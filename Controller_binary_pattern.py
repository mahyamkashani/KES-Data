#import Retriver_ontology_entity
#import ontology_importer
import Extractor_binary_relation_individual_extractor
''' 
def get_binary_patterns(ontology_path):
    ontology=ontology_importer.ontology_reader(ontology_path)
    binary_relations = Retriver_ontology_entity.entity_object_protery_List(ontology)
    return binary_relations
'''
def get_binary_patterns_data_from_doc(user_data,doc='pdfs/geomar_rep_ns_55_2020-highlight.pdf',pages=None):
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
    """
    TODO: each Mission has some Tasks. define domain of Task based on Mission!

    Rule: SWRL rules: 2/ if mission has some photo related task, then the vehicle should have sensor Camera

    Planner: Can you do take picture? using this rule (2): consider them in action in DomainPDDL file: should be the same for all pdfs
     
       consider these in ProblemPDDL file should be different for each pdf: intialCondition and goal: rules if satifistied


       Traversal not only has Destination, name of island, location: by calculation of lat and lon
     
    """
    #Adapted to Ontology/new/marine_report.rdf. Every OBJECT_PROPERTY below is
    #an identifier that ontology actually declares (hasSensor, not "has sensor"),
    #and every DOMAIN/RANGE is a class reachable as onto.<Name>. Sensor and
    #Platform are declared in the sosa namespace inside that graph, so they
    #resolve as sosa:Sensor / sosa:Platform and NOT as onto.Sensor -- use their
    #subclasses (MBES, Camera; Ship, Vehicle, Station) in the slots instead.
    binary_relations = '''
    {
    "OntologyAxiom": [
        {
        "Binary_Relation": "Vehicle hasSensor MBES",
        "DOMAIN": "Vehicle",
        "RANGE": "MBES",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Multibeam echosounder used for bathymetric mapping. Use the instrument name given in the report, e.g. EM2040, EM122"
        },
        {
        "Binary_Relation": "Vehicle hasSensor Sonar",
        "DOMAIN": "Vehicle",
        "RANGE": "Sonar",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Side-scan or imaging sonar, e.g. Edgetech 2200. The ontology has no SSS class; side-scan sonar is a Sonar"
        },
        {
        "Binary_Relation": "Vehicle hasSensor DVL",
        "DOMAIN": "Vehicle",
        "RANGE": "DVL",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Doppler velocity log used for bottom-lock navigation. Use the instrument name, e.g. RDI Workhorse"
        },
        {
        "Binary_Relation": "Vehicle hasSensor USBL",
        "DOMAIN": "Vehicle",
        "RANGE": "USBL",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Ultra-short baseline acoustic positioning system, e.g. Posidonia, Sonardyne Ranger"
        },
        {
        "Binary_Relation": "Vehicle hasSensor Camera",
        "DOMAIN": "Vehicle",
        "RANGE": "Camera",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Still or video camera carried by the vehicle, e.g. OFOS, a downward-looking stills camera. Use Monocular or Stereo instead when the report says which"
        },
        {
        "Binary_Relation": "Vehicle hasSensor CTDSensor",
        "DOMAIN": "Vehicle",
        "RANGE": "CTDSensor",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Conductivity-temperature-depth probe, e.g. SBE 9plus, SBE 19"
        },
        {
        "Binary_Relation": "Vehicle hasSensor Echosounder",
        "DOMAIN": "Vehicle",
        "RANGE": "Echosounder",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Single-beam or sub-bottom echosounder, e.g. EA600, Parasound P70. The ontology has no Parasound class; a sub-bottom profiler is an Echosounder"
        },
        {
        "Binary_Relation": "Vehicle hasSensor Hydrophone",
        "DOMAIN": "Vehicle",
        "RANGE": "Hydrophone",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Passive acoustic hydrophone or hydrophone array"
        },
        {
        "Binary_Relation": "Vehicle hasSensor ADCP",
        "DOMAIN": "Vehicle",
        "RANGE": "ADCP",
        "OBJECT_PROPERTY": "hasSensor",
        "Annotation": "Acoustic Doppler current profiler used to measure water currents"
        },
        {
        "Binary_Relation": "Ship usesVehicle Vehicle",
        "DOMAIN": "Ship",
        "RANGE": "Vehicle",
        "OBJECT_PROPERTY": "usesVehicle",
        "Annotation": "Ship is the surface research vessel or mother ship, e.g. RV ALKOR, RV POSEIDON, RV SONNE. Vehicle is the AUV or submersible launched and recovered from it. Never put the ship itself in a Vehicle slot"
        },
        {
        "Binary_Relation": "Ship hasMission Mission",
        "DOMAIN": "Ship",
        "RANGE": "Mission",
        "OBJECT_PROPERTY": "hasMission",
        "Annotation": "Mission is a cruise leg or expedition identified by a code such as AL533 or SO277. Ship is the research vessel it was run from"
        },
        {
        "Binary_Relation": "Mission hasTask Task",
        "DOMAIN": "Mission",
        "RANGE": "Task",
        "OBJECT_PROPERTY": "hasTask",
        "Annotation": "Mission is a cruise leg or survey run such as AL533. Task is an individual operation carried out during it - a numbered dive, a station, a deployment or a test. Use the identifier the report gives it, e.g. Dive 1426. Emit one axiom for EVERY dive or station the report lists, not just the first"
        },
        {
        "Binary_Relation": "Task hasAction Action",
        "DOMAIN": "Task",
        "RANGE": "Action",
        "OBJECT_PROPERTY": "hasAction",
        "Annotation": "Action must be one of these existing individuals only: Act_TakePhoto, Act_Move, Act_DeepDive, Act_AcquireDVLLock, Act_EstablishUSBLFix. Map on meaning: any photography, imaging, video, camera work, visual survey, photo transect or seafloor imaging -> Act_TakePhoto; transit or traverse -> Act_Move; a dive or descent -> Act_DeepDive; bottom lock -> Act_AcquireDVLLock; positioning or navigation fix -> Act_EstablishUSBLFix. A task usually has SEVERAL actions - emit one axiom per action, so a dive that took photographs yields both Act_DeepDive and Act_TakePhoto"
        },
        {
        "Binary_Relation": "Traversal hasVehicle Vehicle",
        "DOMAIN": "Traversal",
        "RANGE": "Vehicle",
        "OBJECT_PROPERTY": "hasVehicle",
        "Annotation": "Traversal is a transit, track or survey line. Vehicle is the AUV, ROV or submersible that flew it"
        },
        {
        "Binary_Relation": "Traversal hasDestination Waypoint",
        "DOMAIN": "Traversal",
        "RANGE": "Waypoint",
        "OBJECT_PROPERTY": "hasDestination",
        "Annotation": "Traversal is a transit or track flown by a vehicle. Waypoint is the named station, site or target position it ends at"
        },
        {
        "Binary_Relation": "Traversal goes_through Waypoint",
        "DOMAIN": "Traversal",
        "RANGE": "Waypoint",
        "OBJECT_PROPERTY": "goes_through",
        "Annotation": "An intermediate waypoint the track passes through, as opposed to its destination. The FIRST slot must be the traversal - a named track, transect, survey line or profile - and NEVER a waypoint. To say that one waypoint comes before another, use the before relation instead: Traversal and Waypoint are disjoint classes, so putting a waypoint here makes the ontology inconsistent"
        },
        {
        "Binary_Relation": "Waypoint before Waypoint",
        "DOMAIN": "Waypoint",
        "RANGE": "Waypoint",
        "OBJECT_PROPERTY": "before",
        "Annotation": "Orders two waypoints along a track: the first was occupied or passed earlier than the second. Both slots are waypoints - stations, sites or target positions"
        },
        {
        "Binary_Relation": "Terrain requiresNavigation Waypoint",
        "DOMAIN": "Terrain",
        "RANGE": "Waypoint",
        "OBJECT_PROPERTY": "requiresNavigation",
        "Annotation": "Terrain is the seafloor area a waypoint sits on - flat, sand, rocky or steep ground, e.g. pillow lava, soft sediment. Waypoint is the named site on it"
        },
        {
        "Binary_Relation": "State has_Terrain Terrain",
        "DOMAIN": "State",
        "RANGE": "Terrain",
        "OBJECT_PROPERTY": "has_Terrain",
        "Annotation": "State is the environmental condition recorded at a place - the water column and seabed situation. Terrain is the seabed structure it describes"
        }
    ]
    }
    '''
    #Testing binary relation pattern based individual extraction
    #parameters: binary_relations: List/JSON, docpath: file path, pages: cap on
    #pages indexed (None = the whole report)
    respones = Extractor_binary_relation_individual_extractor.get_individual_for_binary_relation(binary_relations,doc,pages)
    return respones