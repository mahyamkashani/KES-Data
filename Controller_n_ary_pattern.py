import ontology_importer
import Retriver_nary_pattern_retriver
import Extractor_n_ary_pattern_individual_extractor
 
def get_nary_patterns(ontology_path):
    ontology=ontology_importer.ontology_reader(ontology_path)
    n_ary_entity = Retriver_nary_pattern_retriver.detect_n_ary_relationships(ontology)
    return n_ary_entity

def get_nary_patterns_data_from_doc(n_ary_entity,doc='/home/mahya/Desktop/robotic-cybersecurity/Projects/marineLLM-PDDL/documents/geomar_rep_ns_55_2020-highlight.pdf',doctype='pdf',pages=30, sheet=None):
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

    #marine survey pattern (marine_survey.rdf / geomar_rep_ns_55_2020-highlight.pdf)
    #Mission is the linking (n-ary) node: it ties a vehicle, a goal, a scenario
    #and the tasks of one dive together
    n_ary_entity = '''
    {
    "NaryPropertyAxiom": {
        "ontology structure": [
            "SurveyNavigation hasMission Mission",
            "Mission usesVehicle Vehicle",
            "Mission hasGoal Goal",
            "Mission hasInitialCondition Scenario",
            "Mission hasTask Task",
            "Task realisedByAction Action",
            "Scenario hasScenarioTask Task"
        ]
    }
    }
    '''
    respones = Extractor_n_ary_pattern_individual_extractor.get_individual_for_nary_relation(n_ary_entity,doc,doctype,pages,sheet)
    #respones = Extractor_n_ary_pattern_individual_extractor.get_individual_for_nary_relation(n_ary_entity,'./POPs/homegarden_brinjal_v9.xlsx','excel',None,"PoP - large")
    return respones

#Testing for KES
#get_nary_patterns_data_from_doc('')
