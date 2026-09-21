import Reader_vector_retriever
import Validator_axiom_semantics
#import AI_geminiai_caller
import re

def get_individual_for_binary_relation(binary_relations,docpath, pages=None):
    prompt = None  
    jsonExample= '''
    {
    "ObjectPropertyAxiom": [
        {
        "INDIVIDUAL": ["individual_1", "individual_2"],
        "OBJECT_PROPERTY": "relationship",
        "DOMAIN": "domain_of_the_relationship",
        "RANGE": "range_of_the_relationship",
        "AXIOM": "individual_1 relationship individual_2",
        },
        {
        "INDIVIDUAL": ["individual_1", "individual_3"],
        "OBJECT_PROPERTY": "relationship",
        "DOMAIN": "class_type_of_indididual_1",
        "RANGE": "class_type_of_indididual_3",
        "AXIOM": "individual_1 relationship individual_3",
        }
    ]
    }
    '''

    #one retrieval query per axiom, built from its Binary_Relation + Annotation.
    #"Mission has task Task" pulls the dive tables, "Vehicle has sensor MBES"
    #pulls the instrument list, wherever in the report they happen to sit.
    #retrieval returns a single window, so there is one prompt to build
    docdata = Reader_vector_retriever.context_for_pattern(
        binary_relations, docpath, pages)[0]

    def build_prompt(reason, prior):
        #the retry differs from the first ask only by the rejection reason, which
        #is a checked fact about the T-box rather than a guess
        retry = ""
        if reason:
            retry = (
                "\n\nYour PREVIOUS answer was rejected. Reason: " + reason +
                "\nPrevious answer: " + (prior or "") +
                "\nFix exactly these problems and return the corrected JSON. "
                "Drop any axiom you cannot correct rather than inventing a name.")
        return (
    "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
    "1. **USER_JSON**: This contains a binary pattern; it represents OBJECT_PROPERTY relations of the ontology with their DOMAINS and RANGES."
    "2. **TEXT_CONTENT**: This contains excerpts of the source document from which you need to extract individuals for ontology. "
    "Each excerpt is preceded by a [page N] marker giving its page in the report; the markers are provenance, never extract them as individuals. "
    "The excerpts are not contiguous, so do not assume a fact is absent because the surrounding text is missing. "
    "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
    
    "Your task is to read the USER_JSON and identify the object properties with their domains and ranges. Then, identify the individuals those follows the given object properties from the TEXT_CONTENT."
    "Return the results formatted as specified in OUTPUT_JSON_FORMAT. "
    
    "Each name you put in INDIVIDUAL must be a specific entity named in the TEXT_CONTENT - "
    "an instrument model, a vehicle name, a station or dive number. "
    "Never use a class name from the USER_JSON (Vehicle, Ship, Station, Mission, Task, Action, "
    "Waypoint, Traversal, Terrain, State, MBES, Sonar, DVL, USBL, Camera, CTDSensor, "
    "Echosounder, Hydrophone, ADCP) as an individual. "
    "If the TEXT_CONTENT names no specific individual for a relation, omit that axiom entirely "
    "rather than filling the slot with the class name. "
    "Set RANGE to the most specific class from the USER_JSON that the individual belongs to. "

    "Do not include any additional messages or content in your response."
    
    f"\n\nUSER_JSON: {binary_relations}"
    f"\nOUTPUT_JSON_FORMAT: {jsonExample}"
    f"\nTEXT_CONTENT: {docdata}"
    + retry
        )

    parsed_data, attempts, ok = Validator_axiom_semantics.extract_with_retries(
        build_prompt, label="binary: ", docpath=docpath, pages_limit=pages)
    return parsed_data
