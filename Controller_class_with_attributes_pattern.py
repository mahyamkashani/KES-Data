import Retriver_ontology_entity
import ontology_importer
import Extractor_class_individual_property_value_extractor

def get_individuals_attributes_patterns(ontology_path):
    ontology=ontology_importer.ontology_reader(ontology_path)
    #should get attrubutes for general classes
    class_with_attributes = Retriver_ontology_entity.individual_attributes(ontology)
    return class_with_attributes

#the attribute-value pattern used for KES
#agriculture pattern (CropKB_Tbox_KES.rdf / rice_large.pdf)
#classList = {
#     "classes": {
#            "SoilType": {
#                "data_properties": [
#                    "hasmaxphvalue",
#                    "hasminphvalue"
#                ]
#            },
#            "Crop": {
#                "data_properties": [
#                    "scientific_name"
#                ]
#            }
#
#        }
#}

#marine survey pattern (marine_survey.rdf / geomar_rep_ns_55_2020-highlight.pdf)
classList = {
     "classes": {
            "Mission": {
                "data_properties": [
                    "MissionID",
                    "startTime",
                    "endTime",
                    "maxDepth",
                    "imageCount",
                    "dataVolume",
                    "hasStatus",
                    "remark"
                ]
            },
            "Station": {
                "data_properties": [
                    "stationID",
                    "stationDate",
                    "stationTime"
                ]
            },
            "Waypoint": {
                "data_properties": [
                    "latitude",
                    "longitude",
                    "seabedDepth"
                ]
            },
            "Task": {
                "data_properties": [
                    "hasDuration",
                    "hasStatus"
                ]
            }

        }
}

def get_individual_data_from_doc (class_with_attributes=None,docpath='/home/mahya/Desktop/robotic-cybersecurity/Projects/marineLLM-PDDL/documents/geomar_rep_ns_55_2020-highlight.pdf',doc_type='pdf', pages=30, sheet_name=None):

    if class_with_attributes is None:
        class_with_attributes = classList
    individual_attributes_data = Extractor_class_individual_property_value_extractor.get_class_property_value(class_with_attributes,docpath,doc_type, pages, sheet_name)
    return individual_attributes_data