"""Binary-relation extraction driven by marine_survey2.ttl.

Derives the binary pattern JSON from the ontology (instead of hardcoding it
like Controller_binary_pattern does), then calls the KES extractor.
Nothing in either repo is modified.
"""
import json
import os
import sys

import rdflib
from rdflib.namespace import OWL

KES = "/home/mahya/Desktop/robotic-cybersecurity/Projects/KES-Data"
MARINE = "/home/mahya/Desktop/robotic-cybersecurity/Projects/marineLLM-PDDL"
TTL = os.path.join(MARINE, "ontology/ontology/marine_survey2.ttl")
PDF = os.path.join(MARINE, "documents/geomar_rep_ns_55_2020-highlight.pdf")

sys.path.insert(0, KES)

PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 15

# --- 1. Convert the Turtle ontology so owlready2 can read it -----------------
# owl:imports ssn: is stripped because owlready2 cannot parse what the W3C
# URL serves; the survey ontology's own axioms are unaffected.
graph = rdflib.Graph()
graph.parse(TTL, format="turtle")
graph.remove((None, OWL.imports, None))
rdf_path = os.path.abspath("marine_survey2.rdf")
graph.serialize(rdf_path, format="xml")

# --- 2. Pull the binary patterns out with the repo's own retriever -----------
import ontology_importer
import Retriver_ontology_entity

onto = ontology_importer.ontology_reader("file://" + rdf_path)
relations = Retriver_ontology_entity.entity_object_protery_List(onto)

axioms = [
    {
        "Binary_Relation": f"{r['domain']} {r['object_property']} {r['range']}",
        "DOMAIN": r["domain"],
        "RANGE": r["range"],
        "OBJECT_PROPERTY": r["object_property"],
    }
    for r in relations
    if r["domain"] != "None" and r["range"] != "None"
]

user_json = json.dumps({"OntologyAxiom": axioms}, indent=2)
print(f"=== {len(axioms)} binary patterns from marine_survey2.ttl ===")

# --- 3. Run the extractor ----------------------------------------------------
import Extractor_binary_relation_individual_extractor as E

response = E.get_individual_for_binary_relation(user_json, PDF, "pdf", PAGES, None)

with open("marine_binary_axioms.json", "w") as fh:
    fh.write(response)
print("\n=== written to marine_binary_axioms.json ===")
