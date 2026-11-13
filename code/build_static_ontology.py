# Builds the static trustworthiness ontology of the SysCon paper as one OWL file.
# It holds the core ML ontology, the trustworthiness extension, the model catalog (weather MLP and LR),
# and the three case study systems with their documented degradations. No runtime checks are stored.
# Usage: python build_static_ontology.py OUT_DIR
import os  # paths
import sys  # command line arguments

from owlready2 import AllDisjoint, AnnotationProperty, DataProperty, FunctionalProperty, ObjectProperty, Thing, get_ontology  # OWL API

OUT = sys.argv[1]  # output folder
os.makedirs(OUT, exist_ok=True)  # create it
onto = get_ontology("http://example.org/trustworthiness_debt.owl")  # one ontology file
C = onto.get_namespace("http://example.org/ml_core.owl#")  # core namespace (prefix c:)
T = onto.get_namespace("http://example.org/ml_trust.owl#")  # extension namespace (prefix t:)

# 1. Core ML ontology: classes and object properties of our ML ontology
with C:  # core entities
    class ML_Algorithm(Thing): pass  # learning algorithms
    class Deep_Learning_Algorithm(ML_Algorithm): pass  # family
    class Ensemble_Algorithm(ML_Algorithm): pass  # family
    class Reinforcement_Learning_Algorithm(ML_Algorithm): pass  # family
    class Supervised_Algorithm(ML_Algorithm): pass  # family
    class Unsupervised_Algorithm(ML_Algorithm): pass  # family
    class ML_Configuration(Thing): pass  # configurations
    class Environment_Configuration(ML_Configuration): pass  # environment settings
    class Hyperparameter_Configuration(ML_Configuration): pass  # hyperparameters
    class Training_Configuration(ML_Configuration): pass  # training settings
    class ML_Context(Thing): pass  # contexts
    class Data_Characteristics(ML_Context): pass  # data
    class Operational_Context(ML_Context): pass  # operating conditions
    class Problem_Context(ML_Context): pass  # task
    class ML_Metric(Thing): pass  # measurements
    class Efficiency_Metric(ML_Metric): pass  # family
    class Explainability_Metric(ML_Metric): pass  # family
    class Performance_Metric(ML_Metric): pass  # family
    class Robustness_Metric(ML_Metric): pass  # family
    class ML_Model_Instance(Thing): pass  # trained models
    class High_Accuracy_Model(ML_Model_Instance): pass  # defined in the core ontology
    class Real_Time_Suitable_Model(ML_Model_Instance): pass  # defined in the core ontology
    class achieves_metric(ObjectProperty): domain = [ML_Model_Instance]; range = [ML_Metric]  # model to measurement
    class applicable_to_algorithm_family(ObjectProperty): range = [ML_Algorithm]  # metric kind to algorithm
    class has_configuration(ObjectProperty): domain = [ML_Model_Instance]; range = [ML_Configuration]  # model to configuration
    class implements_algorithm(ObjectProperty): domain = [ML_Model_Instance]; range = [ML_Algorithm]  # model to algorithm
    class measured_on(ObjectProperty): domain = [ML_Metric]; range = [ML_Context]  # measurement to context
    class operates_on_context(ObjectProperty): domain = [ML_Model_Instance]; range = [ML_Context]  # current context
    class suited_for_context(ObjectProperty): domain = [ML_Model_Instance]; range = [ML_Context]  # context it was trained and tested for

# 2. Trustworthiness extension (static knowledge)
with T:  # extension entities
    class Shift_Metric(C.ML_Metric): pass  # input shift measurements
    class Raw_Metric_Kind(Thing): pass  # the 21 raw metric kinds
    class Trustworthiness_Attribute(Thing): pass  # the seven attributes
    class Source_Document(Thing): pass  # the four documents of Step 1
    class Trustworthiness_Debt(Thing): pass  # the six debt types
    class Commissioning_Profile(Thing): pass  # thresholds of one model in one context
    class Threshold_Entry(Thing): pass  # thresholds of one metric kind
    class Fine_Tuning_Configuration(C.Training_Configuration): pass  # sequential fine tuning event
    class Transfer_Configuration(C.Training_Configuration): pass  # domain transfer event
    class of_metric_kind(ObjectProperty, FunctionalProperty): domain = [C.ML_Metric]; range = [Raw_Metric_Kind]  # kind
    class supports_attribute(ObjectProperty): domain = [Raw_Metric_Kind]; range = [Trustworthiness_Attribute]  # A_MTA
    class supports_attribute_if_severe(ObjectProperty): domain = [Raw_Metric_Kind]; range = [Trustworthiness_Attribute]  # severe link
    class requires_attribute(ObjectProperty): domain = [Trustworthiness_Debt]; range = [Trustworthiness_Attribute]  # A_TAD
    class named_in(ObjectProperty): domain = [Trustworthiness_Attribute]; range = [Source_Document]  # Table I, second column
    class monitors_metric_kind(ObjectProperty): domain = [C.ML_Model_Instance]; range = [Raw_Metric_Kind]  # plan
    class has_commissioning_profile(ObjectProperty, FunctionalProperty): domain = [C.ML_Model_Instance]; range = [Commissioning_Profile]  # profile
    class has_threshold_entry(ObjectProperty): domain = [Commissioning_Profile]; range = [Threshold_Entry]  # entries
    class for_metric_kind(ObjectProperty, FunctionalProperty): domain = [Threshold_Entry]; range = [Raw_Metric_Kind]  # entry kind
    class commissioned_on(ObjectProperty): domain = [Commissioning_Profile]; range = [C.ML_Context]  # clean context
    class derived_from(ObjectProperty): domain = [C.ML_Model_Instance]; range = [C.ML_Model_Instance]  # lineage
    class has_tau(DataProperty, FunctionalProperty): domain = [Threshold_Entry]; range = [float]  # threshold
    class has_tau_sev(DataProperty, FunctionalProperty): domain = [Threshold_Entry]; range = [float]  # severe threshold
    class has_percentile(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [int]  # 95
    class has_severe_percentile(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [int]  # 99
    class has_resample_size(DataProperty): domain = [Commissioning_Profile]; range = [int]  # 200, 400, 800, 1600 resampled years
    class has_validation_years(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [int]  # 5000
    class has_attack_epsilon(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [float]  # 0.1
    class has_task(DataProperty, FunctionalProperty): domain = [C.ML_Model_Instance]; range = [str]  # learning task
    class has_trainable_parameters(DataProperty, FunctionalProperty): domain = [C.ML_Model_Instance]; range = [int]  # size
    class has_inference_time_ms(DataProperty, FunctionalProperty): domain = [C.ML_Model_Instance]; range = [float]  # per year
    class has_check_length_days(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [int]  # 360
    class has_noise_sigma(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [float]  # 0.1
    class has_reference_size(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [int]  # 1000
    class has_hidden_units(DataProperty, FunctionalProperty): domain = [C.Hyperparameter_Configuration]; range = [int]  # MLP width
    class has_random_seed(DataProperty, FunctionalProperty): domain = [C.Hyperparameter_Configuration]; range = [int]  # seed
    class has_max_iterations(DataProperty, FunctionalProperty): domain = [C.Hyperparameter_Configuration]; range = [int]  # solver limit
    class has_block_length_days(DataProperty, FunctionalProperty): domain = [Commissioning_Profile]; range = [int]  # 30 day blocks
    class has_start_year(DataProperty, FunctionalProperty): range = [int]  # first year of a period
    class has_end_year(DataProperty, FunctionalProperty): range = [int]  # last year of a period
    class is_degraded(DataProperty, FunctionalProperty): domain = [C.ML_Metric]; range = [bool]  # documented degradation
    class reported_in(DataProperty): domain = [C.ML_Metric]; range = [str]  # source of a documented degradation
    class requires_provenance(AnnotationProperty): pass  # debt to the configuration class that must be on record

    ATTR = {k: Trustworthiness_Attribute(n) for k, n in [("A1", "Correctness"), ("A2", "Reliability"), ("A3", "Safety"),  # attributes
            ("A4", "Security"), ("A5", "Resilience"), ("A6", "Predictability"), ("A7", "Transparency_Interpretability")]}  # attributes
    DOC = {"NIST": Source_Document("NIST_AI_RMF"), "EU": Source_Document("EU_AI_Act"),  # the four documents
           "EASA": Source_Document("EASA_ML_Concept_Paper"), "IEEE": Source_Document("IEEE_7010")}  # the four documents
    DOC["NIST"].comment = ["NIST AI Risk Management Framework, AI RMF 1.0 (nist2023rmf)"]  # citation
    DOC["EU"].comment = ["EU Artificial Intelligence Act, Regulation (EU) 2024/1689 (eu2024aiact)"]  # citation
    DOC["EASA"].comment = ["EASA concept paper, first usable guidance for level 1 machine learning applications (easa2021concept)"]  # citation
    DOC["IEEE"].comment = ["IEEE 7010, assessing the impact of AI on human well being (schiff2020ieee)"]  # citation
    NAMED = {"A1": (["NIST", "EU", "EASA"], "NIST valid; EU AI Act accuracy (Art. 15); EASA trained model performance"),  # Table I
             "A2": (["NIST", "EU"], "NIST reliable; EU AI Act consistent performance (Art. 15)"),  # Table I
             "A3": (["NIST", "EU", "EASA", "IEEE"], "NIST safe; EU AI Act safety risks (Art. 9); EASA safety assessment; IEEE 7010 harm to well being"),  # Table I
             "A4": (["NIST", "EU", "EASA"], "NIST secure; EU AI Act cybersecurity (Art. 15); EASA security assessment"),  # Table I
             "A5": (["NIST", "EU"], "NIST resilient; EU AI Act resilience to errors and faults (Art. 15)"),  # Table I
             "A6": (["EASA"], "EASA stability of the trained model"),  # Table I
             "A7": (["NIST", "EU", "EASA"], "NIST transparent, explainable, interpretable; EU AI Act transparency (Art. 13); EASA explainability")}  # Table I
    for k, (docs, terms) in NAMED.items():  # attribute to the documents that name it
        ATTR[k].named_in = [DOC[d] for d in docs]; ATTR[k].comment = ["Named in: " + terms]  # links and terms
    LINKS = {"Accuracy": (["A1"], []), "F1_Score": (["A1"], []), "Intersection_over_Union": (["A1"], []),  # Table I
             "Accuracy_Variance": (["A1", "A2"], []), "Performance_Drift_Rate": (["A1", "A2"], []),  # Table I
             "Failure_Rate": (["A2"], []), "Availability": (["A2"], []), "Silent_Data_Corruption_Rate": (["A2", "A3"], []),  # Table I
             "Mean_Time_To_Repair": (["A5"], []), "Unsafe_Output_Rate": (["A3"], []), "Fault_Detection_Coverage": (["A3"], []),  # Table I
             "Hazard_Response_Time": (["A3", "A5"], []), "Attack_Success_Rate": (["A4"], []), "Attack_Detection_Rate": (["A4"], []),  # Table I
             "MMD": (["A2"], ["A5"]), "KS": (["A2"], ["A5"]), "Latency_Variance": (["A2", "A6"], []),  # Table I
             "Latency_Jitter": (["A2", "A6"], []), "Prediction_Flip_Rate": (["A6"], []),  # Table I
             "Explanation_Stability": (["A6", "A7"], []), "Explanation_Fidelity": (["A7"], [])}  # Table I
    KIND = {}  # metric kind individuals
    for name, (links, severe) in LINKS.items():  # each kind
        KIND[name] = Raw_Metric_Kind(name, supports_attribute=[ATTR[a] for a in links],  # A_MTA links
                                     supports_attribute_if_severe=[ATTR[a] for a in severe])  # severe links
    KIND["Explanation_Stability"].comment = ["Stability of gradient saliency maps under small input noise."]  # definition
    TDI = {"Source_Target_Mismatch": ["A2", "A6", "A7"], "Capability_Loss": ["A1", "A2"], "Robustness_Debt": ["A1", "A4"],  # Table II
           "Operating_Envelope": ["A2", "A5"], "Harmful_Output": ["A3", "A4"], "Faithfulness": ["A6", "A7"]}  # Table II
    DEBT = {n: Trustworthiness_Debt(n, requires_attribute=[ATTR[a] for a in a_]) for n, a_ in TDI.items()}  # debts
    DEBT["Source_Target_Mismatch"].requires_provenance = [Transfer_Configuration]  # provenance of a transfer
    DEBT["Capability_Loss"].requires_provenance = [Fine_Tuning_Configuration]  # provenance of sequential fine tuning

    # Algorithms of the catalog and of the case study systems
    MLP = C.Deep_Learning_Algorithm("Multilayer_Perceptron"); MLP.is_a.append(C.Supervised_Algorithm)  # neural network
    LOGREG = C.Supervised_Algorithm("Logistic_Regression")  # linear model
    LANE = C.Deep_Learning_Algorithm("Lane_Detector_ResNet18"); LANE.is_a.append(C.Supervised_Algorithm)  # AssistTaxi
    LLM = C.Deep_Learning_Algorithm("Large_Language_Model")  # language model case
    ALINA = C.ML_Algorithm("ALINA_Line_Labeling")  # color thresholds and pixel traversal
    ALINA.comment = ["Rule based line labeling with color thresholds and pixel traversal (Khan et al., 2024)."]  # note
    ALGS = [MLP, LOGREG, LANE, LLM, ALINA]  # all algorithms
    GRAD = [MLP, LANE, LLM]  # algorithms with input dependent gradients
    for name, k in KIND.items():  # applicability
        k.applicable_to_algorithm_family = GRAD if name in ("Explanation_Stability", "Explanation_Fidelity") else ALGS  # both are constant for a linear model

with onto:  # axioms stored in the ontology itself
    AllDisjoint([T.Raw_Metric_Kind, T.Trustworthiness_Attribute, T.Source_Document, T.Trustworthiness_Debt, T.Commissioning_Profile,  # disjoint
                 T.Threshold_Entry, C.ML_Algorithm, C.ML_Configuration, C.ML_Context, C.ML_Metric,  # classes
                 C.ML_Model_Instance])  # end of the list

# 3. Model catalog: the two weather classifiers of Section IV
with T:  # catalog individuals
    wdata = C.Data_Characteristics("NOAA_Daily_Weather_Records")  # 18,159 days, eight features
    wtask = C.Problem_Context("Rain_Prediction")  # binary task
    wtrain = C.Operational_Context("Weather_Years_1_to_5", has_start_year=1, has_end_year=5)  # training years
    wcomm = C.Operational_Context("Weather_Years_6_to_10", has_start_year=6, has_end_year=10)  # normal operation years
    wmon = C.Operational_Context("Weather_Years_11_to_50", has_start_year=11, has_end_year=50)  # monitored years
    plan = [KIND[k] for k in ("Accuracy", "F1_Score", "Accuracy_Variance", "MMD", "KS", "Unsafe_Output_Rate",  # ten metric kinds
                              "Attack_Success_Rate", "Prediction_Flip_Rate", "Explanation_Stability", "Explanation_Fidelity")]  # plan
    for tag, alg, units, iters, nparam in (("MLP", MLP, 16, 3000, 8 * 16 + 16 + 16 + 1), ("LR", LOGREG, None, 2000, 8 + 1)):  # models
        hyp = C.Hyperparameter_Configuration("%s_Weather_Hyperparameters" % tag, has_random_seed=0,  # hyperparameters
                                             has_max_iterations=iters)  # solver iteration limit
        if units:  # network width
            hyp.has_hidden_units = units  # one hidden layer of 16 units
        trn = C.Training_Configuration("%s_Weather_Training" % tag, has_start_year=1, has_end_year=5)  # training period
        prof = Commissioning_Profile("%s_Weather_Profile" % tag, commissioned_on=[wcomm], has_percentile=95,  # profile
                                     has_severe_percentile=99, has_resample_size=[200, 400, 800, 1600],  # threshold runs
                                     has_validation_years=5000, has_attack_epsilon=0.1, has_check_length_days=360,  # settings
                                     has_block_length_days=30,  # clean checks are built from 30 day blocks
                                     has_noise_sigma=0.1, has_reference_size=1000)  # settings
        C.ML_Model_Instance("%s_Weather" % tag, implements_algorithm=[alg], has_configuration=[hyp, trn],  # instance
                            suited_for_context=[wdata, wtask, wcomm], operates_on_context=[wmon],  # contexts
                            monitors_metric_kind=plan, has_commissioning_profile=prof,  # plan and profile
                            has_task="binary classification: rain or no rain", has_trainable_parameters=nparam)  # task and size

# 4. Case study systems with their documented degradations (no scores are reported, so none is severe)
with T:  # case individuals
    def documented(model, name, kind, family, ctx, source):  # one documented degradation
        m = family(name, of_metric_kind=KIND[kind], measured_on=[ctx], is_degraded=True, reported_in=[source])  # measurement
        model.achieves_metric.append(m)  # core property
    taxi = C.Operational_Context("Taxiway_Imagery"); runway = C.Operational_Context("Runway_Imagery")  # ALINA contexts
    alina = C.ML_Model_Instance("ALINA_on_Runways", implements_algorithm=[ALINA], suited_for_context=[taxi],  # instance
                                operates_on_context=[runway],  # moved to runways
                                has_configuration=[Transfer_Configuration("ALINA_Taxiway_to_Runway_Transfer"),  # documented transfer
                                                   C.Hyperparameter_Configuration("ALINA_Adjusted_Color_Sensitivity")])  # adjusted
    documented(alina, "ALINA_Runway_Mislabeling", "Accuracy", C.Performance_Metric, runway, "ganeriwala2025runway")  # horizon mislabeled
    documented(alina, "ALINA_Runway_Missed_Line", "Unsafe_Output_Rate", C.ML_Metric, runway, "ganeriwala2025runway")  # missed line
    documented(alina, "ALINA_Taxiway_Runway_Shift", "MMD", Shift_Metric, runway, "ganeriwala2025runway")  # reported shift
    road = C.Operational_Context("Road_Imagery_CULane"); assist = C.Operational_Context("Taxiway_Imagery_AssistTaxi")  # contexts
    at = C.ML_Model_Instance("AssistTaxi_Lane_Detector", implements_algorithm=[LANE], suited_for_context=[road],  # instance
                             operates_on_context=[assist, road],  # road capability still required
                             has_configuration=[Transfer_Configuration("Road_to_Taxiway_Transfer"),  # documented transfer
                                                Fine_Tuning_Configuration("Head_Only_Fine_Tuning")])  # documented fine tuning
    documented(at, "AssistTaxi_Road_F1_Collapse", "F1_Score", C.Performance_Metric, road, "khan2025adapt")  # road F1 80.4 to 5.1
    documented(at, "AssistTaxi_Road_Taxiway_Shift", "MMD", Shift_Metric, assist, "khan2025adapt")  # reported shift
    harmful = C.Problem_Context("Harmful_Instruction_Prompts"); retrieved = C.Operational_Context("Retrieved_Web_Content")  # contexts
    tasks = C.Problem_Context("Fixed_Benchmark_Tasks")  # tasks for drift
    llm = C.ML_Model_Instance("Language_Model_Composite", implements_algorithm=[LLM], operates_on_context=[retrieved, tasks],  # instance
                              has_configuration=[Fine_Tuning_Configuration("Benign_Fine_Tuning")])  # documented fine tuning
    documented(llm, "LLM_Harmful_Responses", "Unsafe_Output_Rate", C.ML_Metric, harmful, "qi2024fine")  # alignment eroded
    documented(llm, "LLM_Prompt_Injection", "Attack_Success_Rate", C.Robustness_Metric, retrieved, "greshake2023not")  # injection
    documented(llm, "LLM_Version_Drift", "Performance_Drift_Rate", C.Performance_Metric, tasks, "chen2024chatgpt")  # drift
onto.save(file=os.path.join(OUT, "trustworthiness_debt.owl"), format="rdfxml")  # write the file
print("classes", len(list(onto.classes())), "| object properties", len(list(onto.object_properties())),  # summary
      "| data properties", len(list(onto.data_properties())), "| individuals", len(list(onto.individuals())))  # summary
