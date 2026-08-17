#import Retriver_ontology_entity
#import ontology_importer
import Extractor_binary_relation_individual_extractor
''' 
def get_binary_patterns(ontology_path):
    ontology=ontology_importer.ontology_reader(ontology_path)
    binary_relations = Retriver_ontology_entity.entity_object_protery_List(ontology)
    return binary_relations
'''
def get_binary_patterns_data_from_doc(user_data,doc='/home/mahya/Desktop/robotic-cybersecurity/Projects/marineLLM-PDDL/documents/geomar_rep_ns_55_2020-highlight.pdf',doctype='pdf',pages=30, sheet=None):
    #agriculture pattern (CropKB_Tbox_KES.rdf / rice_large.pdf)
    #binary_relations = '''
    #{
    #"OntologyAxiom": [
    #    {
    #    "Binary_Relation": "Crop IsaffectedBy GrowingProblem"
    #    "DOMAIN": "Crop",
    #    "RANGE": "GrowingProblem",
    #    "OBJECT_PROPERTY": "IsaffectedBy"
    #    "Annotation": "Crop can be a rice considered in the doc. Growing Problme can be a pest or disease"
    #    }
    #]
    #}
    #'''

    #marine survey pattern (marine_survey.rdf / geomar_rep_ns_55_2020-highlight.pdf)
    binary_relations = '''
    {
    "OntologyAxiom": [
        {
        "Binary_Relation": "Vehicle hasSensor Sensor",
        "DOMAIN": "Vehicle",
        "RANGE": "Sensor",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Vehicle can be an AUV or a manned submersible described in the report. Sensor can be a CTD, camera, DVL, USBL, echosounder, MBES or hydrophone"
        },
        {
        "Binary_Relation": "Mission usesVehicle Vehicle",
        "DOMAIN": "Mission",
        "RANGE": "Vehicle",
        "OBJECT_PROPERTY": "usesVehicle",
        "Annotation": "Mission is a dive or a survey run reported in the cruise report. Vehicle is the AUV or submersible deployed for it"
        },
        {
        "Binary_Relation": "Traversal hasDestination Waypoint",
        "DOMAIN": "Traversal",
        "RANGE": "Waypoint",
        "OBJECT_PROPERTY": "hasDestination",
        "Annotation": "Traversal is a transit or track flown by a vehicle. Waypoint is a named station, site or target position"
        },
        {
        "Binary_Relation": "Waypoint onTerrain TerrainArea",
        "DOMAIN": "Waypoint",
        "RANGE": "TerrainArea",
        "OBJECT_PROPERTY": "onTerrain",
        "Annotation": "TerrainArea is the seafloor area a waypoint sits on"
        }
    ]
    }
    '''
    #Testing binary relation pattern based individual extraction
    #parameters: binary_relation_individual_extractor: List/JSON ,docpath: file path ,doc_type: pdf or excel, pages: if pdf, sheet_name: if excel
    respones = Extractor_binary_relation_individual_extractor.get_individual_for_binary_relation(binary_relations,doc,doctype,pages,sheet)
    #respones = Extractor_binary_relation_individual_extractor.get_individual_for_binary_relation(binary_relations,'./POPs/homegarden_brinjal_v9.xlsx','excel',None,"Variety - small")
    return respones