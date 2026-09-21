"""Multi-mission RAG extraction over cruise-report PDFs.

A cruise report usually contains SEVERAL distinct missions (AL533 alone has
four), matching the ontology axiom  SurveyNavigation ⊑ ≥1 hasMission.Mission.
This script therefore runs in two stages per PDF:

  Q0  mission split   "which distinct missions does this report contain?"
                      -> list of mission names (capped at MAX_MISSIONS)
  Q1..Qn per mission  every question is asked once PER MISSION, with the
                      mission name injected into the query (it also steers
                      retrieval, since the query string reaches the retriever)

Output: one CSV per question with schema
    filename, mission, question, result, feedback
plus scenario_extractionQ0.csv holding the raw mission-split answers.
⚠ The `mission` column and the several-rows-per-filename layout are NEW --
ontology/csv2onto.py still assumes one mission per report and must be updated
before consuming these CSVs (Mission_<rep> -> Mission_<rep>_<mission>).

Model selection (--model or SCENGEN_MODEL env var):
    gpt-4o | gpt-5 | gpt-5-mini | o3         OpenAI (OPENAI_API_KEY)
    qwen3 | qwq                              Qwen reasoning via DashScope
                                             (DASHSCOPE_API_KEY, OpenAI-compatible)
    qwen-local                               Qwen through a local Ollama server
Any unlisted name is passed through as a raw OpenAI model id.
Embeddings are always OpenAIEmbeddings, so OPENAI_API_KEY is needed even for
Qwen runs.

Run:
    python src/scenario_generation-sequential_chain.py --model gpt-5 --limit 1 --questions Q5
    python src/scenario_generation-sequential_chain.py                      # all PDFs, all questions
"""
import argparse
import os
import re
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyMuPDFLoader

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

absolute_path = os.getcwd()
# absolute_path = "/home/mahya/Desktop/ARC/Projects/marineLLM-PDDL"
folder_path = absolute_path + "/documents" + "/Kiel/geomar/"

MAX_RETRIES = 2
MAX_MISSIONS = 6

# ----------------------------  model registry  -------------------------------

DASHSCOPE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

MODELS = {
    # OpenAI
    "gpt-4o":     dict(model="gpt-4o"),
    "gpt-5":      dict(model="gpt-5"),
    "gpt-5-mini": dict(model="gpt-5-mini"),
    "o3":         dict(model="o3"),
    # Qwen reasoning models via Alibaba DashScope (OpenAI-compatible endpoint)
    "qwen3":      dict(model="qwen3-235b-a22b", base_url=DASHSCOPE_URL, key_env="DASHSCOPE_API_KEY"),
    "qwq":        dict(model="qwq-plus",        base_url=DASHSCOPE_URL, key_env="DASHSCOPE_API_KEY"),
    # Qwen locally through Ollama's OpenAI-compatible server
    "qwen-local": dict(model="qwen3:32b", base_url="http://localhost:11434/v1", key_env=None),
}


def get_llm(name):
    cfg = MODELS.get(name, dict(model=name))          # raw model ids pass through
    kwargs = {"model": cfg["model"]}
    if cfg.get("base_url"):
        kwargs["base_url"] = cfg["base_url"]
        env = cfg.get("key_env")
        if env:
            if env not in os.environ:
                raise SystemExit(f"--model {name} needs {env} set in .env")
            kwargs["api_key"] = os.environ[env]
        else:
            kwargs["api_key"] = "ollama"              # Ollama ignores the key
    return ChatOpenAI(**kwargs)


llm = None  # set by run_narrative / main


# ----------------------------  answer quality gate  --------------------------

DONT_KNOW_PHRASES = [
    "i don't know",
    "i do not know",
    "i'm not sure",
    "not sure",
    "the context does not",
    "the context doesn't",
    "no information",
    "not provided",
    "not specified",
    "unclear",
    "cannot determine",
]


def is_dont_know(answer: str) -> bool:
    a = answer.lower()
    return any(p in a for p in DONT_KNOW_PHRASES)


def has_expected_format(answer: str) -> bool:
    return re.search(r'\*[^*]+\*', answer) is not None


def evaluate(answer: str):
    if is_dont_know(answer):
        return False, "the previous answer said you do not know — re-read the context more carefully and extract any partial information available"
    if not has_expected_format(answer):
        return False, "the previous answer did not follow the required format (each bullet wrapped in asterisks, e.g. *item one*)"
    return True, ""


# ----------------------------  prompts  --------------------------------------

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you genuinely cannot find the answer in the context, say 'I don't know'. "
    "Format every bullet of your answer wrapped in like  three double-asterisk groups per line: - **Name**: **Duration** - **Outcome**. "
    "ONLY when the question asks for a task status, the Outcome MUST be exactly "
    "one of the three keywords SUCCESSFUL, PartialSUCCESSFUL, or FAILED (same "
    "closed vocabulary as the ontology); never invent a fourth value, and never "
    "add these keywords to answers about anything other than task status. "
    "Keep each bullet to a few words.\n\n"
    "{context}"
)

refine_system_prompt = (
    "You are refining a previous answer that was unsatisfactory. "
    "Use the retrieved context below to produce a better answer to the original question. "
    "Reason it was rejected: {reason}\n"
    "Previous answer: {prior_answer}\n\n"
    "Format every bullet wrapped in like  three double-asterisk groups per line: - **Name**: **Duration** - **Outcome**. "
    "ONLY when the question asks for a task status, the Outcome MUST be exactly "
    "one of the three keywords SUCCESSFUL, PartialSUCCESSFUL, or FAILED (same "
    "closed vocabulary as the ontology); never invent a fourth value, and never "
    "add these keywords to answers about anything other than task status. "
    "Keep each bullet to a few words.\n\n"
    "{context}"
)

initial_prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", "{input}")]
)

refine_prompt = ChatPromptTemplate.from_messages(
    [("system", refine_system_prompt), ("human", "{input}")]
)

# ----------------------------  mission split (Q0)  ---------------------------

MISSION_SPLIT_QUESTION = (
    "A research cruise report usually contains SEVERAL distinct missions, e.g. "
    "one per system under test or per science package: a submersible trial, an "
    "AUV camera survey, a mooring or seabed-transponder deployment, a CTD/water "
    "sampling programme. List EVERY distinct mission in THIS cruise report, one "
    "bullet per mission: - **Mission name**: **vehicle(s)/system used** - **objective**. "
    "If the report truly describes a single campaign, return exactly one bullet."
)

MISSION_RE = re.compile(r"^\s*[-*]\s*\*\*(.+?)\*\*", re.M)


def parse_missions(answer: str):
    names, seen = [], set()
    for m in MISSION_RE.finditer(answer):
        name = m.group(1).strip(" :;.,-*")
        key = name.lower()
        if 3 <= len(name) <= 80 and key not in seen:
            seen.add(key)
            names.append(name)
    return names[:MAX_MISSIONS]


# ----------------------------  chains  ---------------------------------------

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def build_chains(retriever):
    initial_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | initial_prompt
        | llm
        | StrOutputParser()
    )

    refine_chain = (
        {
            "context": (lambda x: x["input"]) | retriever | format_docs,
            "input": lambda x: x["input"],
            "prior_answer": lambda x: x["prior_answer"],
            "reason": lambda x: x["reason"],
        }
        | refine_prompt
        | llm
        | StrOutputParser()
    )

    return initial_chain, refine_chain


def answer_with_retries(initial_chain, refine_chain, question):
    answer = initial_chain.invoke(question)
    ok, reason = evaluate(answer)
    attempts = 1

    while not ok and attempts <= MAX_RETRIES:
        answer = refine_chain.invoke(
            {"input": question, "prior_answer": answer, "reason": reason}
        )
        ok, reason = evaluate(answer)
        attempts += 1

    return answer, attempts, ok


# ----------------------------  per-PDF processing  ---------------------------

# Q6 and Q8 removed: already addressed by categorising the cruise reports in
# categorize_reports.py. Q12+Q13 merged into one depth-profile question (old
# surface-only temperature question dropped). Q14 added for terrain structure.
questions = {
    "Q1": "What is vehicle vessel name?",
    "Q2": "What is vehicle or vessel type?",
    "Q3": "What is the main purpose of the cruise report?",
    "Q4": "What is the duration of the mission?",
    "Q5": "What are the existing tasks in this mission, the duration of each "
          "task, and the status of each task? Status must be exactly one of: "
          "SUCCESSFUL, PartialSUCCESSFUL, or FAILED.",
    "Q7": "What components/devices/sensors were used in this mission and for "
          "how long?",
    "Q9": "What is the mission (scenario) location? Give the NAMED location -- "
          "a place name we can look up in a DEM (Digital Elevation Model) or "
          "bathymetric gazetteer -- and its latitude and longitude, formatted "
          "as - **Location name**: **Latitude** - **Longitude**.",
    "Q10": "What is the visibility of the environment, and how can we measure "
           "it?",
    "Q11": "What is the signal acoustic condition/ multibeam?",
    "Q12": "Categorise the water temperature together with the salinity of the "
           "water by depth: report the temperature and salinity at the surface "
           "and at the different measured depths, formatted as "
           "- **Depth**: **Temperature** - **Salinity**.",
    "Q14": "What is the terrain / seabed structure at the mission location? "
           "Classify the surface as exactly one of the four ontology keywords: "
           "flat (level soft sediment), sand (sandy or overgrown sediment), "
           "rocky (stony or hard ground, e.g. pillow lava), or steep (slope or "
           "scarp), formatted as - **Location**: **Surface keyword** - "
           "**Evidence**.",
}


def process_pdf(pdf_path, filename, q_keys):
    """Embed one PDF once, split it into missions, then answer every question
    once per mission. Returns {q_label: [row_dict, ...]} including 'Q0'."""
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    initial_chain, refine_chain = build_chains(retriever)

    # ---- Q0: which missions does this report contain? ----
    split_answer, attempts, ok = answer_with_retries(
        initial_chain, refine_chain, MISSION_SPLIT_QUESTION
    )
    missions = parse_missions(split_answer) or ["MAIN"]
    print(f"  missions ({len(missions)}): {missions}")

    rows = {"Q0": [dict(filename=filename, mission="; ".join(missions),
                        question=MISSION_SPLIT_QUESTION, result=split_answer,
                        feedback=attempts if ok else 0)]}

    # ---- every question, once per mission ----
    for q_label in q_keys:
        rows[q_label] = []
        for mission in missions:
            mission_q = (
                f'Regarding ONLY the mission "{mission}" in this cruise report: '
                f"{questions[q_label]}"
            )
            answer, attempts, ok = answer_with_retries(
                initial_chain, refine_chain, mission_q
            )
            rows[q_label].append(dict(filename=filename, mission=mission,
                                      question=questions[q_label], result=answer,
                                      feedback=attempts if ok else 0))

    vectorstore.delete_collection()
    return rows


COLUMNS = ["filename", "mission", "question", "result", "feedback"]


def run_narrative(source_folder, q_keys, out_dir, limit=0, model=None):
    """Multi-mission pipeline: one embedding pass per PDF, mission split (Q0),
    then per-mission answers for `q_keys`. Writes one CSV per question (plus
    Q0) to `out_dir`, re-written after every PDF for crash safety."""
    global llm
    llm = get_llm(model or os.environ.get("SCENGEN_MODEL", "gpt-4o"))

    out_dir = str(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    pdf_names = sorted(f for f in os.listdir(str(source_folder)) if f.endswith(".pdf"))
    if limit:
        pdf_names = pdf_names[:limit]

    collected = {q: [] for q in ["Q0"] + list(q_keys)}
    for filename in pdf_names:
        print(filename)
        rows = process_pdf(os.path.join(str(source_folder), filename), filename, q_keys)
        for q_label, q_rows in rows.items():
            collected[q_label].extend(q_rows)
        for q_label, q_rows in collected.items():          # crash-safe rewrite
            if q_rows:
                pd.DataFrame(q_rows, columns=COLUMNS).to_csv(
                    os.path.join(out_dir, f"scenario_extraction{q_label}.csv"),
                    index=False,
                )

    return collected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("SCENGEN_MODEL", "gpt-4o"),
                        help=f"one of {list(MODELS)} or a raw model id")
    parser.add_argument("--questions", default=",".join(questions),
                        help="comma-separated question keys (default: all)")
    parser.add_argument("--limit", type=int, default=0, help="process only N PDFs (0 = all)")
    parser.add_argument("--out", default=None,
                        help="output dir (default: datasets/CuratedQAs/Geomar-Kiel-multimission)")
    parser.add_argument("--source", default=folder_path,
                        help="folder of cruise-report PDFs (default: documents/Kiel/geomar)")
    args = parser.parse_args()

    if args.questions.strip().lower() == "all":
        q_keys = list(questions)
    else:
        q_keys = [q.strip() for q in args.questions.split(",") if q.strip()]
        unknown = set(q_keys) - set(questions)
        if unknown:
            raise SystemExit(f"unknown question keys: {unknown}; valid: {list(questions)} or 'all'")

    # separate output folder: the mission column changes the CSV schema, so do
    # not overwrite the single-mission CuratedQAs consumed by csv2onto.py
    out_dir = args.out or (absolute_path + "/datasets/CuratedQAs/Geomar-Kiel-multimission/")
    run_narrative(args.source, q_keys, out_dir, limit=args.limit, model=args.model)


if __name__ == "__main__":
    main()
