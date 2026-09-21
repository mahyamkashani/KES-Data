"""Semantic validation of extracted axioms against the T-box, plus the refine loop.

JSON_validator only answers "does this parse?". Everything that actually went
wrong in practice parsed perfectly and was caught much later, by
populate_ontology.py, after the JSON had already been written:

    USBL hasSensor USBL                  a class name in an individual slot
    SO277_OMAX hasVehicle RV SONNE       a name with a space, so the n-ary
                                         triple parser drops the whole axiom
    CTD hasStatus "in the water"         outside the closed hasStatus range
    Vehicle has sensor MBES              a property the ontology does not declare

Each of those is decidable against the T-box the moment the answer comes back,
which is early enough to hand the model a specific reason and ask again. That is
the ontology counterpart of evaluate() + refine_chain in
LLMs-RAG/scenario_generation-sequential_chain.py; the difference is that the
reason here is a checked fact ("USBL is a class, not an individual") rather than
a phrase heuristic, so the retry carries real new information even though the
retrieved context has not changed.

The T-box comes from KES_TBOX, or Ontology/new/marine_report.rdf by default.
Set KES_VALIDATE=0 to turn the whole thing off and get the previous behaviour.
"""
import os
import re
from owlready2 import World, OneOf
import AI_gpt_caller
import JSON_validator
import Reader_vector_retriever

HERE = os.path.dirname(os.path.abspath(__file__))
TBOX_PATH = os.environ.get("KES_TBOX", os.path.join(HERE, "Ontology", "new", "marine_report.rdf"))
MAX_RETRIES = int(os.environ.get("KES_MAX_RETRIES", "2"))
ENABLED = os.environ.get("KES_VALIDATE", "1") != "0"

MAX_REASONS = 6          # how many problems to quote back to the model at once
GROUNDING = os.environ.get("KES_GROUNDING", "1") != "0"

_tbox = None
_pages = {}


# ----------------------------  grounding in the source  ----------------------
#
# The T-box checks say an axiom is well formed; they cannot say it is true.
# ifm-geomar_rep39 produced "DR 4 hasDestination Embryo" and "DR 5 hasDestination
# Axial Seamount": both structurally perfect, both wrong. The report pairs Embryo
# with DR 12 and Axial Seamount with DR 122, and "DR 4" is not a station in it at
# all -- every "DR 4" in the text is the start of DR 40-49, and what the model
# actually saw was the contents line "(DR 1-40, TVG 8+22)".
#
# Two things are decidable against the source text. Does this name occur in the
# document at all, and do the two names of a relation ever occur on the same
# page? Neither proves the axiom true, but either failing is strong evidence it
# is invented, and both failed for those two axioms.

def _normalise(text):
    #the model is asked to write RV_SONNE, the report prints "RV SONNE"
    return " ".join(str(text).replace("_", " ").split()).lower()


def page_texts(docpath, pages=None):
    """{page: normalised text}. Page level, not chunk level: two names printed
    in the same table are related in a way two names from opposite ends of the
    report are not."""
    key = (os.path.abspath(docpath), pages)
    if key not in _pages:
        texts = {}
        for chunk in Reader_vector_retriever._chunks(docpath, pages):
            page = chunk.metadata.get("page", 0) + 1
            texts[page] = texts.get(page, "") + " " + chunk.page_content
        _pages[key] = {p: _normalise(t) for p, t in texts.items()}
    return _pages[key]


def _occurs(term, text):
    """Whole-token match, so 'DR 4' does not quietly match inside 'DR 44'."""
    term = _normalise(term)
    if not term:
        return False
    return re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(term), text) is not None


def _grounded_pages(terms, pages):
    return [p for p, text in pages.items() if all(_occurs(t, text) for t in terms)]


def _check_grounding(names, pages, tbox, problems, where, together=True):
    """`names` must occur in the document, and (when `together`) on one page."""
    checkable = [n for n in names if isinstance(n, str) and n.strip()
                 and n not in tbox.vocabulary]
    if not checkable:
        return
    absent = [n for n in checkable if not any(_occurs(n, t) for t in pages.values())]
    if absent:
        problems.append(
            f"{where}: {', '.join(repr(a) for a in absent)} does not appear anywhere in the "
            f"document - do not invent a name, and do not turn a range like 'DR 1-40' into a "
            f"station; drop the axiom if the report does not name it")
        return
    if together and len(checkable) > 1 and not _grounded_pages(checkable, pages):
        problems.append(
            f"{where}: {' and '.join(repr(c) for c in checkable)} both occur in the document "
            f"but never on the same page, so the report does not state this relation - "
            f"pair each name with the one the report actually puts beside it, or drop the axiom")


class TBox:
    """The names an extraction is allowed to use, read once from the ontology."""

    def __init__(self, path):
        self.path = path
        world = World()
        onto = world.get_ontology("file://" + os.path.abspath(path)).load()
        self.onto = onto
        #populate_ontology.py reaches entities with getattr(onto, name), so a
        #class declared under a foreign namespace (sosa:Sensor, sosa:Platform)
        #is present but unusable; keep the two sets apart so the reason can say
        #which problem it is
        self.classes = {c.name for c in onto.classes()}
        self.reachable = {n for n in self.classes if getattr(onto, n, None) is not None}
        self.object_properties = {p.name for p in onto.object_properties()}
        self.data_properties = {p.name for p in onto.data_properties()}
        #Act_TakePhoto, flat, rocky, sand ... are controlled vocabulary the
        #extraction is told to use; they are deliberately not words of the
        #report, so the grounding check must not ask the document for them
        self.vocabulary = {i.name for i in onto.individuals()}
        self.enums = {}
        for prop in onto.data_properties():
            for constraint in prop.range or []:
                if isinstance(constraint, OneOf):
                    self.enums[prop.name] = [str(v) for v in constraint.instances]


def get_tbox(path=None):
    global _tbox
    path = path or TBOX_PATH
    if _tbox is None or _tbox.path != path:
        _tbox = TBox(path)
    return _tbox


# ----------------------------  per-pattern checks  ---------------------------

def _check_individual(name, tbox, problems, where):
    if not isinstance(name, str) or not name.strip():
        problems.append(f"{where}: an individual slot is empty")
        return
    if name in tbox.classes:
        problems.append(
            f"{where}: {name!r} is a CLASS in the ontology, not an individual - "
            f"use the specific name the report gives, or drop the axiom")


def _check_enum(prop, value, tbox, problems, where):
    members = tbox.enums.get(prop)
    if members and str(value) not in members:
        problems.append(
            f"{where}: {prop}={value!r} is outside its closed value list {members} - "
            f"use exactly one of those words")


def _check_binary(payload, tbox, problems, pages=None):
    axioms = payload.get("ObjectPropertyAxiom")
    if not isinstance(axioms, list) or not axioms:
        problems.append("ObjectPropertyAxiom is missing or empty - return at least one axiom")
        return
    for axiom in axioms:
        if not isinstance(axiom, dict):
            problems.append("every entry of ObjectPropertyAxiom must be an object")
            continue
        label = axiom.get("AXIOM") or axiom.get("OBJECT_PROPERTY") or "?"
        prop = axiom.get("OBJECT_PROPERTY")
        if prop not in tbox.object_properties:
            problems.append(
                f"{label}: OBJECT_PROPERTY {prop!r} is not declared in the ontology - "
                f"use the exact identifier from USER_JSON, e.g. hasSensor not 'has sensor'")
        for slot in ("DOMAIN", "RANGE"):
            name = axiom.get(slot)
            if name not in tbox.classes:
                problems.append(f"{label}: {slot} {name!r} is not a class in the ontology")
            elif name not in tbox.reachable:
                problems.append(
                    f"{label}: {slot} {name!r} cannot be used here - it is declared in a "
                    f"foreign namespace; use one of its subclasses instead")
        pair = axiom.get("INDIVIDUAL")
        if not isinstance(pair, list) or len(pair) != 2:
            problems.append(f"{label}: INDIVIDUAL must be a list of exactly two names")
            continue
        for name in pair:
            _check_individual(name, tbox, problems, label)
        if pages:
            _check_grounding(pair, pages, tbox, problems, label)


def _check_nary(payload, tbox, problems, pages=None):
    blocks = payload.get("NaryPropertyAxiom")
    if not isinstance(blocks, dict) or not blocks:
        problems.append("NaryPropertyAxiom is missing or empty")
        return
    for block in blocks.values():
        lines = block.get("Axioms") if isinstance(block, dict) else block
        for line in lines or []:
            parts = str(line).split()
            if len(parts) != 3:
                #the single biggest source of dropped axioms downstream
                problems.append(
                    f"{line!r}: an axiom must be exactly three whitespace-separated terms - "
                    f"join multi-word names with underscores, e.g. RV_SONNE, Dive_1426")
                continue
            subject, prop, obj = parts
            if prop not in tbox.object_properties:
                problems.append(f"{line!r}: {prop!r} is not an object property of the ontology")
            for name in (subject, obj):
                _check_individual(name, tbox, problems, repr(line))
            if pages:
                _check_grounding([subject, obj], pages, tbox, problems, repr(line))


def _check_attributes(payload, tbox, problems, pages=None):
    individuals = payload.get("Individuals")
    if not isinstance(individuals, dict):
        problems.append("Individuals must be an object keyed by individual name")
        return
    for name, fields in individuals.items():
        if not isinstance(fields, dict):
            problems.append(f"{name}: its value must be an object of class and data properties")
            continue
        _check_individual(name, tbox, problems, name)
        if pages:
            _check_grounding([name], pages, tbox, problems, name, together=False)
        class_name = fields.get("class")
        if class_name not in tbox.classes:
            problems.append(f"{name}: class {class_name!r} is not in the ontology")
        for prop, value in fields.items():
            if prop == "class" or value in (None, ""):
                continue
            if prop not in tbox.data_properties:
                problems.append(f"{name}: data property {prop!r} is not in the ontology")
                continue
            _check_enum(prop, value, tbox, problems, name)


def _check_subclass(payload, tbox, problems, pages=None):
    for parent, subclasses in payload.items():
        if not isinstance(subclasses, dict):
            problems.append(f"{parent}: expected an object of subclasses")
            continue
        for subclass, rows in subclasses.items():
            if subclass not in tbox.classes:
                problems.append(f"{subclass!r} is not a class in the ontology")
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                name = row.get("individual_name")
                if not name:
                    problems.append(f"{subclass}: a row has no individual_name")
                    continue
                _check_individual(name, tbox, problems, str(name))
                if pages:
                    _check_grounding([name], pages, tbox, problems, str(name), together=False)
                for prop, value in row.items():
                    if prop == "individual_name" or value in (None, ""):
                        continue
                    if prop not in tbox.data_properties:
                        problems.append(f"{name}: data property {prop!r} is not in the ontology")
                        continue
                    _check_enum(prop, value, tbox, problems, str(name))


def evaluate(parsed, tbox=None, pages=None):
    """(ok, reason) for one extraction, checked against the T-box.

    The shape decides the checks, the same way populate_ontology.py dispatches
    on the top-level key.
    """
    tbox = tbox or get_tbox()
    problems = []
    if not isinstance(parsed, dict) or not parsed:
        return False, "the answer was not a JSON object with any content"

    if "ObjectPropertyAxiom" in parsed:
        _check_binary(parsed, tbox, problems, pages)
    elif "NaryPropertyAxiom" in parsed:
        _check_nary(parsed, tbox, problems, pages)
    elif "Individuals" in parsed:
        _check_attributes(parsed, tbox, problems, pages)
    else:
        _check_subclass(parsed, tbox, problems, pages)

    if not problems:
        return True, ""
    shown = problems[:MAX_REASONS]
    more = len(problems) - len(shown)
    reason = "; ".join(shown) + (f"; and {more} more like these" if more > 0 else "")
    return False, reason


# ----------------------------  the refine loop  ------------------------------

def extract_with_retries(build_prompt, label="", max_retries=MAX_RETRIES, tbox_path=None,
                         docpath=None, pages_limit=None):
    """Ask, check against the T-box, and re-ask with the reason until it passes.

    `build_prompt(reason, prior)` returns the prompt; on the first attempt both
    arguments are None. Returns (parsed, attempts, ok) and, when every attempt
    fails, still returns the last answer so a partly good extraction is not lost
    -- populate_ontology.py will skip whatever is still wrong.
    """
    if not ENABLED:
        parsed = JSON_validator.validate_json(
            AI_gpt_caller.get_gpt_response(build_prompt(None, None)).content)
        return parsed, 1, True

    tbox = get_tbox(tbox_path)
    #without the source text only the T-box checks run; with it, an invented
    #name is caught too
    pages = page_texts(docpath, pages_limit) if (docpath and GROUNDING) else None
    parsed, reason, prior = None, None, None
    for attempt in range(1, max_retries + 2):
        try:
            output = AI_gpt_caller.get_gpt_response(build_prompt(reason, prior))
            parsed = JSON_validator.validate_json(output.content)
        except ValueError as exc:
            #malformed JSON is just another reason to ask again
            reason, prior = f"the reply was not valid JSON ({exc})", None
            continue
        ok, reason = evaluate(parsed, tbox, pages)
        if ok:
            if attempt > 1:
                print(f"    {label}validated after {attempt} attempts")
            return parsed, attempt, True
        print(f"    {label}attempt {attempt} rejected: {reason[:160]}")
        prior = output.content
    return parsed, max_retries + 1, False


# ----------------------------  whole-ontology check  -------------------------

def check_consistency(rdf_path):
    """(ok, message) from running the OWL reasoner over a populated ontology."""
    from owlready2 import World, sync_reasoner, OwlReadyInconsistentOntologyError
    world = World()
    onto = world.get_ontology("file://" + os.path.abspath(rdf_path)).load()
    try:
        with onto:
            sync_reasoner(world, debug=0)
    except OwlReadyInconsistentOntologyError:
        return False, "the reasoner reports the populated ontology is INCONSISTENT"
    return True, "the reasoner reports the populated ontology is consistent"
