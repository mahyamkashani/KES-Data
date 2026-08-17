import openai

#client = OpenAI()
#openai.api_key =  "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"


completion = openai.chat.completions.create(
  model="gpt-3.5-turbo",
  
 messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "If Neo4j pattern is Student HAS_REGISTER Course (Student and Course are nodes and HAS_REGISTER is the relationship between the nodes), then, write a sentence using this pattern"},
    {"role": "assistant", "content": "Students can register to a course, then student has registered courses"},
    {"role": "user", "content": "Write simple sentences by considering rice crop only and use these neo4j patterns : Crop HAS_VARIETY Variety, CROP GROW_IN LOCATION, CROP HAS_NUTRITIENT_REQUIREMENT Nutrient Requirements, Crop HAS_BEST_PRACTICE Best Practice, Fertilizer APPLY_FOR Crop, Fertilizer HAS_FERTILIZER_BEST_PRACTICE Best Practice, Crop HAS_GROWING_PROBLEM Growing Problem, Growing Problem HAS_PROBLEM_STAGE Problem Stage, Growing Problem HAS_SYMTOM Symptom, Growing Problem HAS_PREVENTIVE_METHOD Preventive Method, Growing Problem HAS_CONTROL_METHOD Control Method, Pest IS_A Growing Problem, Weed IS_A Growing Problem, Deficiency IS_A Growing Problem, Disease IS_A Growing Problem, Pesticide APPLY_FOR Pest, Disease Control Method APPLY_FOR Disease, Fertilizer Requirement APPLY_FOR Deficiency, Control Method APPLY_IN Stage"}
  ]
)

print(completion.choices[0].message)