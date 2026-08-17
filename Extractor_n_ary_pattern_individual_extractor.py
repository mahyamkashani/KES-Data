import Reader_pdf_reader
import Reader_spreadsheet_reader
import AI_gpt_caller
import JSON_validator
#import AI_geminiai_caller
#import re

def get_individual_for_nary_relation(nary_relations,docpath,doc_type, pages, sheet_name):
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
    "1. **USER_JSON**: This is the JSON defining my ontology's structure, representing classes with n-ary relationships and their connected range classes."
    "2. **TEXT_CONTENT**: This contains the text content from which you need to extract individuals for ontology follwing the relationships. "
    "3. **OUTPUT_JSON_FORMAT**: This specifies the format in which you should return your response. "
    
    "Your task: Based on the n-ary class and their associated range classes in USER_JSON, generate individuals that adhere to the given relationships from the TEXT_CONTENT"
    "For the n-ary class, assign a primary key by shortening the class name and appending a number"
    "Then, connect each primary key instance with depending individuals of its range classes using their relationships. "
    "Finally, provide the response folwoing the OUTPUT_JSON_FORMAT"
    "Do not include any additional messages or content in your response. List all possible patterns the defined context"
    
    f"\n\nUSER_JSON: {nary_relations}"
    f"\nOUTPUT_JSON_FORMAT: {jsonExample}"
    f"\nTEXT_CONTENT: {docdata}"
    )
    '''
    #output = gpt_caller.get_gpt_response(prompt)
    output = geminiai_caller.get_gemini_response(prompt)
    #print (output)

    # Extract and print the text content
    text_content = output.text
    print(text_content)
    '''

    output = AI_gpt_caller.get_gpt_response(prompt)
    # Extract the 'content' part
    content_part = output.content

    # Parse the JSON data
    parsed_data = JSON_validator.validate_json(content_part)

    return parsed_data
