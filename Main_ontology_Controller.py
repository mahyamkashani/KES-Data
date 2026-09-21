#import Extractor_individual_property_value_extractor
#import Controller_binary_pattern
#import Controller_n_ary_pattern
import Controller_subClass_pattern
import json

import argparse
import os

import Controller_binary_pattern
import Controller_n_ary_pattern
import Controller_class_with_attributes_pattern


#read a given ontology
#path="./OntoRepo/CropKB_tbox_original.rdf"
#binary_rel = Controller_binary_pattern.get_binary_patterns(path)
#Controller_binary_pattern.get_binary_patterns_data_from_doc(None,'./PDF/rice india part1.pdf','pdf',3,None)
#print (binary_rel)

#nary_patterns = Controller_n_ary_pattern.get_nary_patterns(path)
#print (nary_patterns)
#Controller_n_ary_pattern.get_nary_patterns_data_from_doc(None)

# mediator of openai extractor and the ontology
#subClasses = Controller_subClass_pattern.get_subclass_pattern_from_doc(None,None, None, None)
#subClasses = Controller_subClass_pattern.get_subclass_pattern_from_doc(None,None, None, None)
#print (subClasses)
#subclassList = Controller_subClass_pattern.get_subclass_from_onto(path)
""" 
for subclassess in subclassList:
    
    class_data_properties = Controller_subClass_pattern.get_classes_properties (path, subclassess)
# Convert the dictionary to a JSON string
    json_output = json.dumps(class_data_properties, indent=4)
    print (json_output)
"""
"""
#read a given ontology
path="./OntoRepo/CropKB_tbox_original.rdf"
#get_nary_patterns()

#respones = n_ary_pattern_individual_extractor.get_individual_for_nary_relation(n_ary_entity,'./PDF/RICE.pdf','pdf',2,None)
respones = n_ary_pattern_individual_extractor.get_individual_for_nary_relation(n_ary_entity,'./POPs/homegarden_brinjal_v9.xlsx','excel',None,"PoP - large")

""" 
"""
# calling to openai lib for extract individuals - pdf file can be passed
#outputContent = OntoIndividualExtractor.textToOntologyIndividual()
#parsed_data = json.loads(outputContent)
# Accessing information
#JSONtoOntologyPasser.createEntitiesFromJSON (outputContent)
"""

""" 
individuals= '''
{
    "Individuals": [
        {
            "name": "PR 131",
            "class": "rice crop",
            "dataProperties": [
                "plant_height",
                "maturity_days"
            ]
        },
        {
            "name": "PR 129",
            "class": "rice crop",
            "dataProperties": [
                "average_yeild",
                "version"
            ]
        }
    ]
}
'''


#Testing SubClasses pattern based individual extraction
#parameters: subclasses: List/JSON ,docpath: file path ,doc_type: pdf or excel, pages: if pdf, sheet_name: if excel
respones = Extractor_individual_property_value_extractor.get_class_property_value(individuals,'./PDF/rice india.pdf','pdf',2,None)
#respones = subclass_individual_extractor.get_subclass_individual(json_classes,'./POPs/homegarden_brinjal_v9.xlsx','excel',None,"Variety - small")
print (respones)
"""


#source document matching marine_survey.rdf
#MARINE_DOC = "pdfs/geomar_rep_ns_57_2021_compressed.pdf" #ifm-geomar_rep40.pdf"
# MARINE_DOC = "AL374 CR ifm-geomar_rep51-1.pdf"
MARINE_DOC = "pdfs/geomar_rep_ns_57_2021_compressed.pdf"#"pdfs/ifm_geomar_rep5.pdf"

#pattern name -> extraction function
PATTERNS = {
    "subclass": Controller_subClass_pattern.get_subclass_pattern_from_doc,
    "binary": Controller_binary_pattern.get_binary_patterns_data_from_doc,
    "nary": Controller_n_ary_pattern.get_nary_patterns_data_from_doc,
    "attributes": Controller_class_with_attributes_pattern.get_individual_data_from_doc,
}

def run_pattern(name, doc, pages, outdir):
    #run one pattern and write its validated JSON
    print(f"\n=== {name} pattern ===")
    respones = PATTERNS[name](None, doc, pages)

    docstem = os.path.splitext(os.path.basename(doc))[0]
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"output_{name}_{docstem}.json")
    with open(outpath, "w") as fh:
        json.dump(respones, fh, indent=4)
    print(f"wrote {outpath}")
    return respones


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="*", metavar="PATTERN",
                        help="patterns to run, any of %s (default: all)" % ", ".join(PATTERNS))
    parser.add_argument("--doc", default=MARINE_DOC)
    parser.add_argument("--pages", type=int, default=None,
                        help="index only the first N pages (default: the whole "
                             "report; retrieval, not a page cap, is what keeps "
                             "the prompt small)")
    parser.add_argument("--outdir", default="outputs",
                        help="directory for the JSON files (created if missing)")
    parser.add_argument("--tbox", default=None,
                        help="ontology the extractions are validated against "
                             "(default: Ontology/new/marine_report.rdf)")
    parser.add_argument("--no-validate", action="store_true",
                        help="skip the T-box check and the refine loop: one LLM "
                             "call per pattern, as before")
    args = parser.parse_args()

    #the extractors reach the validator through the environment, so the four
    #controller signatures stay as they are
    if args.tbox:
        os.environ["KES_TBOX"] = os.path.abspath(args.tbox)
    if args.no_validate:
        os.environ["KES_VALIDATE"] = "0"

    #argparse cannot validate a list default against choices, so check by hand
    if not args.patterns:
        args.patterns = list(PATTERNS)
    unknown = [p for p in args.patterns if p not in PATTERNS]
    if unknown:
        parser.error("unknown pattern(s): %s (choose from %s)"
                     % (", ".join(unknown), ", ".join(PATTERNS)))

    failures = []
    for name in args.patterns:
        try:
            run_pattern(name, args.doc, args.pages, args.outdir)
        except Exception as exc:
            #one bad pattern should not lose the results of the others
            print(f"FAILED {name}: {type(exc).__name__}: {exc}")
            failures.append(name)

    print(f"\ndone: {len(args.patterns) - len(failures)}/{len(args.patterns)} patterns succeeded")
    if failures:
        print("failed: " + ", ".join(failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()