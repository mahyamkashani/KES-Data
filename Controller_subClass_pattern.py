import Extractor_subclass_individual_extractor
import ontology_importer
import Retriver_ontology_entity
import json

def get_subclass_from_onto(ontology_path):
    ontology = ontology_importer.ontology_reader(ontology_path)
    subclasses = Retriver_ontology_entity.entity_subclass_list(ontology)
    return subclasses

def get_classes_properties(ontology_path, classList):
    ontology = ontology_importer.ontology_reader(ontology_path)
    subclasses = Retriver_ontology_entity.data_property_list_for_classes(ontology, classList)
    return subclasses
    
def get_subclass_pattern_from_doc (user_data,doc='pdfs/geomar_rep_ns_55_2020-highlight.pdf',pages=None):
# Define the ontology structure with classes, subclasses, and data properties
    #agriculture pattern (CropKB_Tbox_KES.rdf / rice_large.pdf)
    #data = {
    #    "classes": {
    #        "Crop": {
    #            "subclasses": {
    #                "variety":{
    #                    "data_properties": [
    #                        "average_yield",
    #                        "average_yield_unit",
    #                        "features",
    #                        "average plant height",
    #                        "average plant height units",
    #                        "maturity period",
    #                        "maturity period units"
    #                    ]
    #                }
    #            }
    #        }
    #    }
    #}

    #marine survey pattern (marine_survey.rdf / geomar_rep_ns_55_2020-highlight.pdf)
    #Adapted to Ontology/new/marine_report.rdf, which declares a different
    #hierarchy: BottomLockSite, NavFixSite, UnconstrainedSite and LongTask are
    #gone, Waypoint has no subclasses any more, and the *_Mission classes are
    #subclasses of Task rather than of Mission. Only the SUBCLASS names have to
    #resolve as onto.<Name> -- populate_ontology.py types each individual by its
    #subclass -- so Platform is fine as a parent label even though sosa:Platform
    #is not reachable that way.
    data = {
        "classes": {
            "Task": {
                "subclasses": {
                    "SurveyMission":{
                        "data_properties": [
                            "hasDuration",
                            "hasStatus"
                        ]
                    },
                    "Bathymetric_Mission":{
                        "data_properties": [
                            "hasDuration",
                            "hasStatus"
                        ]
                    },
                    "CTDMission":{
                        "data_properties": [
                            "hasDuration",
                            "hasStatus"
                        ]
                    },
                    "Data_Sampling_Mission":{
                        "data_properties": [
                            "hasDuration",
                            "hasStatus",
                            "collect_sample"
                        ]
                    },
                    "TrialMission":{
                        "data_properties": [
                            "hasDuration",
                            "hasStatus"
                        ]
                    },
                    "Traversal":{
                        "data_properties": [
                            "hasDuration",
                            "hasStatus"
                        ]
                    }
                }
            },
            "Vehicle": {
                "subclasses": {
                    "AUV":{
                        "data_properties": [
                            "maxDepth"
                        ]
                    },
                    "Remotely_Operated_Vehicle":{
                        "data_properties": [
                            "maxDepth"
                        ]
                    },
                    "Submersible_Vehicle":{
                        "data_properties": [
                            "maxDepth"
                        ]
                    }
                }
            },
            "Platform": {
                "subclasses": {
                    "Ship":{
                        "data_properties": [
                            "maxDepth"
                        ]
                    },
                    "Station":{
                        "data_properties": [
                            "stationID",
                            "stationName",
                            "stationDate",
                            "stationTime"
                        ]
                    }
                }
            }
        }
    }

    # Convert the dictionary to a JSON string
    json_classes = json.dumps(data, indent=4)

    #Testing SubClasses pattern based individual extraction
    #parameters: subclasses: List/JSON, docpath: file path, pages: cap on pages
    #indexed (None = the whole report)
    respones = Extractor_subclass_individual_extractor.get_subclass_individual(json_classes,doc,pages)
    return respones