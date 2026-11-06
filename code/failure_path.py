# Writes the record of one monitored year into a copy of the ontology, so the failure path can be followed in Protege.
# The static ontology is not changed: the record goes into a separate file.
# Usage: python code/failure_path.py <ontology_with_thresholds> <monitor_years_csv> <model> <year> <output_owl>
import csv  # monitor output
import sys  # arguments
from decimal import Decimal  # exact literals

from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, Namespace  # RDF API

ONTO, YEARS, MODEL, YEAR, OUT = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]  # inputs
C = Namespace("http://example.org/ml_core.owl#")  # core namespace
T = Namespace("http://example.org/ml_trust.owl#")  # extension namespace
FAMILY = {"Accuracy": C.Performance_Metric, "F1_Score": C.Performance_Metric, "MMD": T.Shift_Metric,  # measurement classes,
          "KS": T.Shift_Metric, "Attack_Success_Rate": C.Robustness_Metric}  # as for the documented systems

g = Graph().parse(ONTO, format="xml")  # ontology with thresholds
row = next(r for r in csv.DictReader(open(YEARS)) if int(r["year"]) == YEAR)  # the monitored year

g.add((T.has_score, RDF.type, OWL.DatatypeProperty))  # the measured value of a degraded metric
g.add((T.has_score, RDFS.domain, C.ML_Metric)); g.add((T.has_score, RDFS.range, XSD.decimal))  # domain and range
g.add((T.has_score, RDFS.comment, Literal("Measured value, oriented like the thresholds: larger is worse "
                                          "(accuracy and F1 score are stored as 1 minus the value).")))  # meaning

year_ctx = T["Weather_Year_%d" % YEAR]  # the monitored year as a context
g.add((year_ctx, RDF.type, OWL.NamedIndividual)); g.add((year_ctx, RDF.type, C.Operational_Context))  # typed
for m in [k[4:] for k in row if k.startswith("deg_") and row[k] == "1"]:  # each degraded metric of that year
    e = T["%s_Year%d_%s" % (MODEL, YEAR, m)]  # one measurement
    g.add((e, RDF.type, OWL.NamedIndividual)); g.add((e, RDF.type, FAMILY.get(m, C.ML_Metric)))  # typed
    g.add((e, T.of_metric_kind, T[m])); g.add((e, C.measured_on, year_ctx))  # kind and year
    g.add((e, T.is_degraded, Literal(True))); g.add((e, T.reported_in, Literal("monitor, year %d" % YEAR)))  # status
    g.add((e, T.has_score, Literal(format(Decimal(repr(float(row["v_" + m]))), "f"), datatype=XSD.decimal)))  # value
    g.add((T[MODEL], C.achieves_metric, e))  # model to measurement
g.serialize(OUT, format="xml")  # the demo file
print("wrote", OUT, "| degraded metrics in year", YEAR, ":", [k[4:] for k in row if k.startswith("deg_") and row[k] == "1"])
