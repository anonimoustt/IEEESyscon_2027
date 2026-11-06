# Checks the DL queries of the paper. Each query is the Manchester syntax text typed into the Protégé DL Query tab.
# The same class expression is built with Owlready2, HermiT classifies the ontology, and the instances are printed.
# Usage: python run_dl_queries.py ONTOLOGY_FILE OUT_FILE
import json  # results file
import os  # paths
import sys  # command line arguments

from owlready2 import Inverse, Thing, get_ontology, sync_reasoner  # OWL API and reasoner

OWL, OUT = sys.argv[1:3]  # input ontology and output file
onto = get_ontology("file://" + os.path.abspath(OWL)).load()  # load the ontology from an absolute path
C = onto.get_namespace("http://example.org/ml_core.owl#")  # core namespace
T = onto.get_namespace("http://example.org/ml_trust.owl#")  # extension namespace
MLP, LR = T.MLP_Weather, T.LR_Weather  # the two catalog instances

QUERIES = [  # (Manchester syntax text, equivalent Owlready2 expression)
    ("Raw_Metric_Kind and inverse (monitors_metric_kind) value MLP_Weather",  # D1 monitoring plan of a model
     T.Raw_Metric_Kind & Inverse(T.monitors_metric_kind).value(MLP)),  # expression
    ("Trustworthiness_Attribute and inverse (supports_attribute) some (Raw_Metric_Kind and "  # D2 observable attributes
     "inverse (monitors_metric_kind) value LR_Weather and applicable_to_algorithm_family value Logistic_Regression)",  # text
     T.Trustworthiness_Attribute & Inverse(T.supports_attribute).some(  # expression
         T.Raw_Metric_Kind & Inverse(T.monitors_metric_kind).value(LR) &  # monitored by LR_Weather
         C.applicable_to_algorithm_family.value(T.Logistic_Regression))),  # and applicable to its algorithm
    ("ML_Model_Instance and implements_algorithm some Deep_Learning_Algorithm",  # D3 models by algorithm family
     C.ML_Model_Instance & C.implements_algorithm.some(C.Deep_Learning_Algorithm)),  # expression
    ("ML_Model_Instance and has_configuration some Fine_Tuning_Configuration",  # D4 provenance of Capability Loss
     C.ML_Model_Instance & C.has_configuration.some(T.Fine_Tuning_Configuration)),  # expression
    ("ML_Model_Instance and has_configuration some Transfer_Configuration",  # D5 provenance of Source Target Mismatch
     C.ML_Model_Instance & C.has_configuration.some(T.Transfer_Configuration)),  # expression
    ("Trustworthiness_Debt and requires_attribute value Correctness",  # D6 debts that need Correctness
     T.Trustworthiness_Debt & T.requires_attribute.value(T.Correctness)),  # expression
    ("ML_Model_Instance and achieves_metric some (is_degraded value true and of_metric_kind value MMD)",  # D7 shifted models
     C.ML_Model_Instance & C.achieves_metric.some(T.is_degraded.value(True) & T.of_metric_kind.value(T.MMD))),  # expression
]  # end of the query list

probe = get_ontology("http://example.org/dl_probe.owl")  # scratch ontology for the query classes
with probe:  # define one named class per query
    named = []  # query classes
    for i, (_, expr) in enumerate(QUERIES, 1):  # each query
        q = type("D%d" % i, (Thing,), {"namespace": probe})  # new class D1, D2, ...
        q.equivalent_to.append(expr)  # defined by the query expression
        named.append(q)  # keep it
with probe:  # inferred facts go to the scratch ontology
    sync_reasoner(debug=0)  # HermiT classification and realization

out = []  # results
for (text, _), q in zip(QUERIES, named):  # each query
    inst = sorted(i.name for i in q.instances())  # inferred instances
    out.append({"query": q.name, "manchester": text, "instances": inst})  # record
    print(q.name, "|", text, "\n   ->", ", ".join(inst))  # report
json.dump(out, open(OUT, "w"), indent=1)  # save
