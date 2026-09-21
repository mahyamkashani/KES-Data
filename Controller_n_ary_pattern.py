import ontology_importer
import Retriver_nary_pattern_retriver
import Extractor_n_ary_pattern_individual_extractor
 
def get_nary_patterns(ontology_path):
    ontology=ontology_importer.ontology_reader(ontology_path)
    n_ary_entity = Retriver_nary_pattern_retriver.detect_n_ary_relationships(ontology)
    return n_ary_entity

def get_nary_patterns_data_from_doc(n_ary_entity,doc='pdfs/geomar_rep_ns_55_2020-highlight.pdf',pages=None):
    #agriculture pattern (CropKB_Tbox_KES.rdf / rice_large.pdf)
    #n_ary_entity = '''
    #{
    #"NaryPropertyAxiom": {
    #    "ontology structure": [
    #        "Crop hasGrowingProblemEvent GrowingProblemEvent"
    #        "GrowingProblemEvent hasGrowingProblem GrowingProblem",
    #        "GrowingProblemEvent hasSymptom Symptom",
    #        "GrowingProblemEvent hasCausalAgent CausalAgent",
    #        "GrowingProblemEvent hasVailablePeriod Season",
    #        "GrowingProblemEvent hasControlMethod ControlMethod",
    #        "GrowingProblemEvent hasPreventionMethod PreventionMethod"
    #    ]
    #}
    #}
    #'''

    #Adapted to Ontology/new/marine_report.rdf. populate_ontology.py types the
    #individuals of an n-ary triple from the PROPERTY's declared domain and range,
    #not from the JSON, so a triple is only usable here when the property declares
    #both AND both are reachable as onto.<Name>. That rules out hasMission,
    #hasGoal, hasInitialCondition, hasScenarioTask and realisedByAction (no
    #declared domain) and usesVehicle/usesDevice/hasSensor (domain or range is
    #sosa:Platform / sosa:Sensor). Goal and Scenario are not classes in this
    #ontology at all; Mission links to its work through hasTask.
    n_ary_entity = '''
    {
    "NaryPropertyAxiom": {
        "ontology structure": [
            "Mission hasTask Task",
            "Task hasAction Action",
            "Traversal hasVehicle Vehicle",
            "Traversal hasDestination Waypoint",
            "Traversal goes_through Waypoint",
            "Terrain requiresNavigation Waypoint",
            "State has_Terrain Terrain"
        ]
    }
    }
    '''
    respones = Extractor_n_ary_pattern_individual_extractor.get_individual_for_nary_relation(n_ary_entity,doc,pages)
    return respones

#Testing for KES
#get_nary_patterns_data_from_doc('')
