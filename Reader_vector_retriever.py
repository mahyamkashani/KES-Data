import hashlib
import json
import logging
import os
import re


os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
#is disabled, so silence the one logger that emits it (posthog.py:61)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import AI_gpt_caller

logging.getLogger("pypdf").setLevel(logging.ERROR)

HERE = os.path.dirname(os.path.abspath(__file__))
PERSIST_ROOT = os.environ.get("KES_CHROMA_DIR", os.path.join(HERE, ".chroma"))

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
K_PER_QUERY = 6       # chunks fetched per axiom
MAX_CHUNKS = 60       # ceiling on the chunks pasted into one prompt

CONTEXT_TOKENS = int(os.environ.get("KES_CONTEXT_TOKENS", "60000"))
WINDOW_OVERLAP = 2    # chunks repeated between consecutive windows

_embeddings = None
_stores = {}
_encoder = None


def _token_len(text):
    global _encoder
    if _encoder is None:
        try:
            import tiktoken
            _encoder = tiktoken.get_encoding("o200k_base")
        except Exception:
            _encoder = False
    if _encoder is False:
        #no tokeniser: assume the worst plausible density rather than overshoot
        return len(text) // 2
    return len(_encoder.encode(text))


def _embedding_fn():
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=os.environ.get("KES_EMBED_MODEL", "text-embedding-3-small"),
            api_key=AI_gpt_caller._load_key(),
        )
    return _embeddings


# ----------------------------  index  ----------------------------------------

def _collection_name(docpath, pages):
    stem = os.path.splitext(os.path.basename(docpath))[0]
    slug = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower()[:40] or "doc"
    tag = "p%d" % pages if pages else "all"
    digest = hashlib.sha1(
        ("%s|%s|%d|%d" % (os.path.abspath(docpath), tag, CHUNK_SIZE, CHUNK_OVERLAP)).encode()
    ).hexdigest()[:8]
    return "%s-%s-%s" % (slug, tag, digest)


def _chunks(docpath, pages=None):
    documents = PyPDFLoader(docpath).load()
    if pages:
        documents = documents[:pages]
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE,
                                              chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk"] = index
        chunk.metadata["source"] = os.path.basename(docpath)
    return chunks


def _count(store):
    try:
        return store._collection.count()
    except Exception:
        return len(store.get(limit=1).get("ids", []))


def get_store(docpath, pages=None):
    """The Chroma collection for this document, built once and then reused."""
    name = _collection_name(docpath, pages)
    if name in _stores:
        return _stores[name]

    os.makedirs(PERSIST_ROOT, exist_ok=True)
    store = Chroma(collection_name=name, persist_directory=PERSIST_ROOT,
                   embedding_function=_embedding_fn())
    if _count(store) == 0:
        chunks = _chunks(docpath, pages)
        if not chunks:
            raise ValueError("no extractable text in %s" % docpath)
        store.add_documents(chunks)
        print("  indexed %d chunks from %s" % (len(chunks), os.path.basename(docpath)))
    _stores[name] = store
    return store


# ----------------------------  retrieval  ------------------------------------

def _order_key(doc):
    return (doc.metadata.get("chunk", 0), doc.metadata.get("page", 0))


def _format(docs):
    blocks = []
    for doc in docs:
        page = doc.metadata.get("page")
        #PyPDFLoader numbers pages from 0; report them as a reader would count
        marker = "[page %d]" % (page + 1) if isinstance(page, int) else "[page ?]"
        blocks.append("%s\n%s" % (marker, doc.page_content))
    return "\n\n".join(blocks)


def whole_document(docpath, pages=None):
    return _format(sorted(_chunks(docpath, pages), key=_order_key))


def document_windows(docpath, pages=None, budget=CONTEXT_TOKENS, overlap=WINDOW_OVERLAP):
    chunks = sorted(_chunks(docpath, pages), key=_order_key)
    windows, current, used = [], [], 0
    for chunk in chunks:
        cost = _token_len(chunk.page_content) + 8      # allow for the [page N] marker
        if current and used + cost > budget:
            windows.append(_format(current))
            current = current[-overlap:] if overlap else []
            used = sum(_token_len(c.page_content) + 8 for c in current)
        current.append(chunk)
        used += cost
    if current:
        windows.append(_format(current))
    return windows


def retrieve(docpath, queries, pages=None, k=K_PER_QUERY, max_chunks=MAX_CHUNKS):
    """The chunks matching `queries`, merged and returned in reading order."""
    queries = [q for q in queries if q]
    if not queries:
        #nothing to match on: take the head of the report, still within budget
        head = sorted(_chunks(docpath, pages), key=_order_key)[:max_chunks]
        return _format(head)

    store = get_store(docpath, pages)
    #retrieval only earns its keep when the report does not fit the budget;
    #a short report is cheaper and more accurate sent whole
    if _count(store) <= max_chunks:
        return whole_document(docpath, pages)

    #spend the whole budget however many queries there are: the attribute
    #pattern asks one class at a time and would otherwise get k chunks for the
    #entire call, while the binary pattern's eighteen axioms share it evenly
    k = max(k, -(-max_chunks // len(queries)))
    hits = [store.similarity_search(query, k=k) for query in queries]

    #round-robin by rank, so every axiom gets its best chunk before any axiom
    #gets its second: one broad query must not crowd out the other seventeen
    picked = {}
    for rank in range(k):
        for per_query in hits:
            if len(picked) >= max_chunks:
                break
            if rank < len(per_query):
                doc = per_query[rank]
                picked.setdefault(doc.metadata.get("chunk", doc.page_content), doc)
        if len(picked) >= max_chunks:
            break

    return _format(sorted(picked.values(), key=_order_key))


# ----------------------------  spec -> queries  ------------------------------

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _humanise(text):
    #hasSeabedDepth -> has Seabed Depth
    return _CAMEL.sub(" ", str(text).replace("_", " ")).strip()


def _class_query(name, definition, parent=None):
    parts = [_humanise(name)]
    if parent:
        parts.append("a kind of %s" % _humanise(parent))
    properties = definition.get("data_properties") or []
    if properties:
        parts.append(", ".join(_humanise(p) for p in properties))
    if definition.get("note"):
        parts.append(definition["note"])
    return " . ".join(parts)


def queries_from_pattern(spec):

    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except json.JSONDecodeError:
            return [spec]
    if not isinstance(spec, dict):
        return []

    queries = []

    #binary: the Annotation already describes the individual to look for
    #("Multibeam echosounder used for bathymetric mapping ... e.g. EM2040")
    for axiom in spec.get("OntologyAxiom", []):
        parts = [axiom.get("Binary_Relation", ""), axiom.get("Annotation", "")]
        queries.append(" . ".join(_humanise(p) for p in parts if p))

    #n-ary: the triples carry no annotation, so the triple itself is the query
    for block in (spec.get("NaryPropertyAxiom") or {}).values():
        triples = block if isinstance(block, list) else (block.get("Axioms") or [])
        queries.extend(_humanise(triple) for triple in triples)

    #attribute and subclass: the class name plus what we want to know about it
    for class_name, definition in (spec.get("classes") or {}).items():
        subclasses = definition.get("subclasses")
        if subclasses:
            for sub_name, sub_definition in subclasses.items():
                queries.append(_class_query(sub_name, sub_definition, parent=class_name))
        else:
            queries.append(_class_query(class_name, definition))

    #dict.fromkeys keeps the order while dropping repeats
    return [q for q in dict.fromkeys(queries) if q]


def context_for_pattern(spec, docpath, pages=None, exhaustive=False, **kwargs):
    #The TEXT_CONTENT block(s) for one pattern, as a list.

    #exhaustive reads the whole document,for the patterns whose prompt demands every
    #instance of something. Otherwise a single retrieved block is returned, so
    if exhaustive:
        return document_windows(docpath, pages)
    return [retrieve(docpath, queries_from_pattern(spec), pages=pages, **kwargs)]
