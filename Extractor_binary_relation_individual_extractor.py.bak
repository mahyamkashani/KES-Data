import  Reader_pdf_reader
import Reader_spreadsheet_reader
import AI_gpt_caller
import JSON_validator
#import AI_geminiai_caller
import re

def get_individual_for_binary_relation(binary_relations,docpath,doc_type, pages, sheet_name):
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

    if doc_type == "pdf":
        docdata = Reader_pdf_reader.pdfReadModullar(docpath, pages)
    elif doc_type == "excel":
        data = Reader_spreadsheet_reader.get_spreadsheet_data(docpath,sheet_name)
        # Convert DataFrame to JSON
        docdata = data.to_json(orient="records")
    else:
        raise ValueError(f"Unsupported doc_type: {doc_type}")

    prompt = (
    "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
    "1. **USER_JSON**: This contains a binary pattern; it represents OBJECT_PROPERTY relations of the ontology with their DOMAINS and RANGES."
    "2. **TEXT_CONTENT**: This contains the text content from which you need to extract individuals for ontology. "
    "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
    
    "Your task is to read the USER_JSON and identify the object properties with their domains and ranges. Then, identify the individuals those follows the given object properties from the TEXT_CONTENT."
    "Return the results formatted as specified in OUTPUT_JSON_FORMAT. "
    
    "Do not include any additional messages or content in your response."
    
    f"\n\nUSER_JSON: {binary_relations}"
    f"\nOUTPUT_JSON_FORMAT: {jsonExample}"
    f"\nTEXT_CONTENT: {docdata}"
    )

    #print ("Here is the prompt: " + prompt)

    """ 
    #output = gpt_caller.get_gpt_response(prompt)
    output = geminiai_caller.get_gemini_response(prompt)
    #print (output)
   
    # Extract and print the text content
    text_content = output.text
    print(text_content)

    """
    output = AI_gpt_caller.get_gpt_response(prompt)
    # Extract the 'content' part
    content_part = output.content

    # Parse the JSON data
    parsed_data = JSON_validator.validate_json(content_part)

    return parsed_data
