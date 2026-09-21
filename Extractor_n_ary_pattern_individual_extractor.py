import Reader_vector_retriever
import Validator_axiom_semantics
#import AI_geminiai_caller
#import re

def get_individual_for_nary_relation(nary_relations,docpath, pages=None):
    prompt = None  
    jsonExample= '''
    {
    "NaryPropertyAxiom": {
        "pattern01": { 
            "Axioms":  [
                    "<crop_intance> hasGrowingProblemEvent <growing_problem_event_id>"
                    "<growing_problem_event_id> hasGrowingProblem <GrowingProblem_name>",
                    "<growing_problem_event_id> hasSymptom <Symptom_description>",
                    "<growing_problem_event_id> hasCausalAgent <CausalAgent_name>",
                    "<growing_problem_event_id> hasAvailablePeriod <Season_name>",
                    "<growing_problem_event_id>hasControlMethod <ControlMethod_description>",
                    "<growing_problem_event_id> hasPreventionMethod <PreventionMethod_description>",
                ],
            "Individuals": [
            "crop_intance","growing_problem_event_id","GrowingProblem_name", "Symptom_description","CausalAgent_name","Season_name","ControlMethod_description","PreventionMethod_description"]
        },
        "pattern02": {
            "Axioms":    [
                    "<crop_intance> hasGrowingProblemEvent <growing_problem_event_id>"
                    "<growing_problem_event_id> hasGrowingProblem <GrowingProblem_name>",
                    "<growing_problem_event_id> hasSymptom <Symptom_description>",
                    "<growing_problem_event_id> hasCausalAgent <CausalAgent_name>",
                    "<growing_problem_event_id> hasAvailablePeriod <Season_name>",
                    "<growing_problem_event_id>hasControlMethod <ControlMethod_description>",
                    "<growing_problem_event_id> hasPreventionMethod <PreventionMethod_description>",
                ],
            "Individuals": [
            "crop_intance","growing_problem_event_id","GrowingProblem_name", "Symptom_description","CausalAgent_name","Season_name","ControlMethod_description","PreventionMethod_description"]
        }
    }
    }
    '''

    #the n-ary pattern has to link a whole dive together -- vehicle, goal,
    #scenario and every task of it -- so it reads the document exhaustively
    #rather than top-k, which would drop the tail of the task list. A cruise
    #report is larger than one request, so that means map-reduce: one call per
    #window, then merge.
    windows = Reader_vector_retriever.context_for_pattern(
        nary_relations, docpath, pages, exhaustive=True)

    results = []
    for number, docdata in enumerate(windows, start=1):
        if len(windows) > 1:
            print(f"  n-ary window {number}/{len(windows)}")
        def build_prompt(reason, prior, docdata=docdata):
            retry = ""
            if reason:
                retry = (
                    "\n\nYour PREVIOUS answer was rejected. Reason: " + reason +
                    "\nPrevious answer: " + (prior or "") +
                    "\nFix exactly these problems and return the corrected JSON. "
                    "Drop any axiom you cannot correct rather than inventing a name.")
            return (
        "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
        "1. **USER_JSON**: This is the JSON defining my ontology's structure, representing classes with n-ary relationships and their connected range classes."
        "2. **TEXT_CONTENT**: This contains the source document from which you need to extract individuals for ontology follwing the relationships. "
        "Each excerpt is preceded by a [page N] marker giving its page in the report; the markers are provenance, never extract them as individuals. "
        "It may be one section of a longer report, so extract what it supports and omit the rest rather than guessing. "
        "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "

        "Your task: Based on the n-ary class and their associated range classes in USER_JSON, generate individuals that adhere to the given relationships from the TEXT_CONTENT"
        "For the n-ary class, assign a primary key by shortening the class name and appending a number"
        "Then, connect each primary key instance with depending individuals of its range classes using their relationships. "
        "Name the linking individual after the identifier the report gives it, e.g. the cruise or dive code, so that the same mission found in two sections merges instead of duplicating. "
        "Every name in an axiom must be a specific entity the TEXT_CONTENT names - a cruise code, a dive or station number, a vehicle name, a named site. "
        "NEVER put a class name from the USER_JSON (Mission, Task, Action, Traversal, Waypoint, Terrain, State, Vehicle) in a subject or object slot: those are classes, and asserting a relation onto one makes the ontology inconsistent. "
        "If the text names no specific entity for a relation, omit that axiom entirely rather than filling the slot with the class name. "
        "Keep every name to a single token with no spaces - write Dive_1426 or RV_SONNE, not 'Dive 1426' or 'RV SONNE' - because each axiom is parsed as exactly three whitespace-separated terms. "
        "Finally, provide the response folwoing the OUTPUT_JSON_FORMAT"
        "Do not include any additional messages or content in your response. List all possible patterns the defined context"

        f"\n\nUSER_JSON: {nary_relations}"
        f"\nOUTPUT_JSON_FORMAT: {jsonExample}"
        f"\nTEXT_CONTENT: {docdata}"
            + retry
            )

        parsed, attempts, ok = Validator_axiom_semantics.extract_with_retries(
            build_prompt, label=f"n-ary window {number}: ", docpath=docpath, pages_limit=pages)
        results.append(parsed)

    return merge_nary_results(results)


def merge_nary_results(results):
    """One NaryPropertyAxiom block set out of the per-window ones.

    Windows overlap, so the same pattern comes back more than once; blocks with
    an identical axiom list are kept once and the survivors are renumbered, since
    populate_ontology.py reads the blocks by value and every key must be distinct.
    """
    merged, seen = {}, set()
    for payload in results:
        blocks = (payload or {}).get("NaryPropertyAxiom") or {}
        if isinstance(blocks, list):
            blocks = {str(index): block for index, block in enumerate(blocks)}
        for block in blocks.values():
            if not isinstance(block, dict):
                continue
            axioms = tuple(block.get("Axioms") or [])
            if not axioms or axioms in seen:
                continue
            seen.add(axioms)
            merged["pattern%02d" % (len(merged) + 1)] = block
    return {"NaryPropertyAxiom": merged}
