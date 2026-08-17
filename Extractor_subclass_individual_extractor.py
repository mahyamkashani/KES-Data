import Reader_pdf_reader
import AI_gpt_caller
import Reader_spreadsheet_reader
import JSON_validator

def get_subclass_individual(subclasses,docpath,doc_type, pages, sheet_name):
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
    
    if doc_type == "pdf":
        docdata = Reader_pdf_reader.pdfReadModullar(docpath, pages)
        prompt = (
            "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
            "1. **USER_JSON**: This contains a hierarchical pattern; it represents  subclasses and their associated data properties without values. "
            "2. **TEXT_CONTENT**: This contains the text content from which you need to extract information. "
            "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
            
            "Your task is to read the USER_JSON and identify the individuals from the TEXT_CONTENT for the given classes and subclasses. "
            "For each individuals, extract the corresponding values for the data properties. "
            "Return the results formatted as specified in OUTPUT_JSON_FORMAT. "
            
            "Do not include any additional messages or content in your response."
            
            f"\n\nUSER_JSON: {subclasses}"
            f"\nOUTPUT_JSON_FORMAT: {output_format}"
            f"\nTEXT_CONTENT: {docdata}"
        )
    elif doc_type == "excel":
        data = Reader_spreadsheet_reader.get_spreadsheet_data(docpath,sheet_name)
        # Convert DataFrame to JSON
        docdata = data.to_json(orient="records")
       
        prompt = (
            "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
            "1. **USER_JSON**: This contains subclasses and their associated data properties without values. "
            "2. **TEXT_CONTENT**: This contains the text content from which you need to extract information. "
            "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
            
            "Your task is to read the USER_JSON and identify the individuals from the TEXT_CONTENT for the given subclasses. "
            "For each individuals, extract the corresponding values for the data properties. "
            "Return the results formatted as specified in OUTPUT_JSON_FORMAT. "
            
            "Do not include any additional messages or content in your response."
            
            f"\n\nUSER_JSON: {subclasses}"
            f"\nOUTPUT_JSON_FORMAT: {output_format}"
            f"\nTEXT_CONTENT: {docdata}"
        )
    else:
        prompt=""
    
    #print ("Here is the prompt: " + prompt)

    
    output = AI_gpt_caller.get_gpt_response(prompt)
    # Extract the 'content' part
    content_part = output.content

    # Parse the JSON data
    parsed_data = JSON_validator.validate_json(content_part)

    return parsed_data
    

