import Reader_pdf_reader
import AI_gpt_caller
import Reader_spreadsheet_reader
import JSON_validator

def get_class_property_value(individuals,docpath,doc_type, pages, sheet_name):
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
    
    if doc_type == "pdf":
        docdata = Reader_pdf_reader.pdfReadModullar(docpath, pages)
        prompt = (
            "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
            "1. **USER_JSON**: This contains an attribute pattern. It contains classes and their associated data properties without values. "
            "2. **TEXT_CONTENT**: This contains the text content from which you need to extract information. "
            "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
            
            "Your task is to read the USER_JSON and identify the individuals and their corresponding data properties."
            "Then, extract values for data properties of each individual from the TEXT_CONTENT."
            "Then, return the results formatted as specified in OUTPUT_JSON_FORMAT. "
            "Do not include any additional messages or content in your response."
            
            f"\n\nUSER_JSON: {individuals}"
            f"\nOUTPUT_JSON_FORMAT: {output_format}"
            f"\nTEXT_CONTENT: {docdata}"
        )
    elif doc_type == "excel":
        data = Reader_spreadsheet_reader.get_spreadsheet_data(docpath,sheet_name)
        # Convert DataFrame to JSON
        docdata = data.to_json(orient="records")
       # docdata =''
        prompt = (
            "You will be provided with three components: USER_JSON, TEXT_CONTENT, and OUTPUT_JSON_FORMAT. "
            "1. **USER_JSON**: This contains class name, data properties of the class and individuals. "
            "2. **TEXT_CONTENT**: This contains the text content from which you need to extract information. "
            "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
            
            "Your task is to read the USER_JSON and identify the individuals and data properties."
            "Then, extract values for data properties of each individuals from the TEXT_CONTENT."
            "Then, return the results formatted as specified in OUTPUT_JSON_FORMAT. "
            "Do not include any additional messages or content in your response."
            
            f"\n\nUSER_JSON: {individuals}"
            f"\nOUTPUT_JSON_FORMAT: {output_format}"
            f"\nTEXT_CONTENT: {docdata}"
        )
    else:
        raise ValueError(f"Unsupported doc_type: {doc_type}")

    output = AI_gpt_caller.get_gpt_response(prompt)
    # Extract the 'content' part
    content_part = output.content

    # Parse the JSON data
    parsed_data = JSON_validator.validate_json(content_part)

    return parsed_data


