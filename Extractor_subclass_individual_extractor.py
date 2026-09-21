import Reader_vector_retriever
import Validator_axiom_semantics

def get_subclass_individual(subclasses,docpath, pages=None):
    prompt = None  
    output_format = '''{
    "ParentClass": {
        "SubClass": [
        {
            "individual_name": "value",
            "dataproperty_01": "value",
            "dataproperty_02": "value"
        },
        {
            "individual_name": "value",
            "dataproperty_01": "value",
            "dataproperty_02": "value"
            "dataproperty_03": "value"
        }
        ]
    }
    }'''
    
    #one query per subclass, built from its name, its parent class and its data
    #properties: "Bottom Lock Site . a kind of Waypoint . seabed Depth"
    docdata = Reader_vector_retriever.context_for_pattern(
        subclasses, docpath, pages)[0]

    def build_prompt(reason, prior):
        retry = ""
        if reason:
            retry = (
                "\n\nYour PREVIOUS answer was rejected. Reason: " + reason +
                "\nPrevious answer: " + (prior or "") +
                "\nFix exactly these problems and return the corrected JSON. "
                "Drop any row you cannot correct rather than inventing a name.")
        return (
        "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
        "1. **USER_JSON**: This contains a hierarchical pattern; it represents  subclasses and their associated data properties without values. "
        "2. **TEXT_CONTENT**: This contains excerpts of the source document from which you need to extract information. "
        "Each excerpt is preceded by a [page N] marker giving its page in the report; the markers are provenance, never extract them as individuals. "
        "The excerpts are not contiguous, so do not assume a fact is absent because the surrounding text is missing. "
        "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "

        "Your task is to read the USER_JSON and identify the individuals from the TEXT_CONTENT for the given classes and subclasses. "
        "For each individuals, extract the corresponding values for the data properties. "
        "Return the results formatted as specified in OUTPUT_JSON_FORMAT. "

        "Do not include any additional messages or content in your response."

        f"\n\nUSER_JSON: {subclasses}"
        f"\nOUTPUT_JSON_FORMAT: {output_format}"
        f"\nTEXT_CONTENT: {docdata}"
        + retry
        )

    parsed_data, attempts, ok = Validator_axiom_semantics.extract_with_retries(
        build_prompt, label="subclass: ", docpath=docpath, pages_limit=pages)
    return parsed_data
    

