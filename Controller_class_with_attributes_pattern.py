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
# ADD island name in waypoint besides lat and lon
# vehicle and sensors in classes
# SWRL rule: if all tasks failed, mission should be considered as failure
# probability of environment knowledge like rocky Terrain, like getting from Ontology (Domain Knowledge): if it is high value, the risk is higher
# Planner: sometimes the plan is successful sometime the plan is failure
classList = {
     "classes": {
            "Mission": {
                "data_properties": [
                    "MissionID",
                    "startTime",
                    "endTime",
                    "maxDepth",
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
                    "locationName",
                    "latitude",
                    "longitude",
                    "seabedDepth"
                ]
            },
            "Task": {
                "note": "A Task is one operation carried out during the cruise - a numbered JAGO dive, a station occupation, a deployment or a test. Name it exactly as the report does, e.g. 'Dive 1426'. Extract EVERY numbered dive you can find, including any dive/station table. hasDuration MUST be a plain decimal number of hours such as 4.5 - never a count of missions, never text, never a time of day. hasStatus must be exactly one of SUCCESSFUL, PartialSUCCESSFUL, PartialFAILURE or FAILED. IMPORTANT: JAGO, ANTON and LUISE are vehicles, not Tasks, Missions or Stations - never emit them as individuals of any class in this USER_JSON.",
                "data_properties": [
                    "hasDuration",
                    "hasStatus"
                ]
            },
            "State": {
                "note": "A State is the environmental condition measured at one place and depth - a CTD cast, a profile reading or a water-column observation. Give each one the name the report uses, e.g. the CTD station or cast number. Temperature is in degrees Celsius, conductivity in S/m and depth in metres, all plain decimal numbers.",
                "data_properties": [
                    "has_Temperature",
                    "has_Conductivity",
                    "has_Depth"
                ]
            }

        }
}

def get_individual_data_from_doc (class_with_attributes=None,docpath='pdfs/geomar_rep_ns_55_2020-highlight.pdf', pages=None):

    if class_with_attributes is None:
        class_with_attributes = classList

    #One class per call. With all four classes in a single USER_JSON the model
    #covers the first ones and silently omits the rest -- Task never came back
    #while Mission and Station were present. Asking per class extracts each one
    #completely, at the cost of one request per class.
    merged = {}
    for class_name, definition in class_with_attributes["classes"].items():
        one_class = {"classes": {class_name: definition}}
        result = Extractor_class_individual_property_value_extractor.get_class_property_value(
            one_class, docpath, pages)
        for name, fields in result.get("Individuals", {}).items():
            #the per-class call cannot know the other classes, so trust its own label
            fields.setdefault("class", class_name)
            merged[name] = fields

    return {"Individuals": merged}