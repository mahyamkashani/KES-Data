import Reader_vector_retriever
import Validator_axiom_semantics

def get_class_property_value(individuals,docpath, pages=None):
    prompt = None  
    output_format = '''{
    "Individuals": {
        "individual_name_01": {
            "class": "add the corresponding class_name given in the USER_JSON",
            "dataproperty_01": "value",
            "dataproperty_02": "value"
        },
        "individual_name_02": {
            "class": ""add the corresponding class_name given in the USER_JSON"",
            "dataproperty_01": "value",
            "dataproperty_02": "value"
        }
    }
}
'''
    
    #the controller calls this once per class, so the single query built from the
    #class name, its data properties and its note gets the whole chunk budget
    docdata = Reader_vector_retriever.context_for_pattern(
        individuals, docpath, pages)[0]

    def build_prompt(reason, prior):
        retry = ""
        if reason:
            retry = (
                "\n\nYour PREVIOUS answer was rejected. Reason: " + reason +
                "\nPrevious answer: " + (prior or "") +
                "\nFix exactly these problems and return the corrected JSON. "
                "Drop any individual you cannot correct rather than inventing a value.")
        return (
        "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
        "1. **USER_JSON**: This contains an attribute pattern. It contains classes and their associated data properties without values. "
        "2. **TEXT_CONTENT**: This contains excerpts of the source document from which you need to extract information. "
        "Each excerpt is preceded by a [page N] marker giving its page in the report; the markers are provenance, never extract them as individuals. "
        "The excerpts are not contiguous, so do not assume a fact is absent because the surrounding text is missing. "
        "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "

        "Your task is to read the USER_JSON and identify the individuals and their corresponding data properties."
        "Then, extract values for data properties of each individual from the TEXT_CONTENT."
        "Then, return the results formatted as specified in OUTPUT_JSON_FORMAT. "
        "Do not include any additional messages or content in your response."

        f"\n\nUSER_JSON: {individuals}"
        f"\nOUTPUT_JSON_FORMAT: {output_format}"
        f"\nTEXT_CONTENT: {docdata}"
        + retry
        )

    parsed_data, attempts, ok = Validator_axiom_semantics.extract_with_retries(
        build_prompt, label="attributes: ", docpath=docpath, pages_limit=pages)
    return parsed_data


