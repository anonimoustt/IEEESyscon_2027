# Writes the part of the ontology that query Q12 matches for one year and one debt, so Protege can draw it as a chain.
# Usage: python code/make_chain_view.py <failure_path_owl> <year> <debt> <output_owl>
import sys  # arguments

from rdflib import OWL, RDF, Graph, Namespace, URIRef  # RDF API

SRC, YEAR, DEBT, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]  # inputs
C = Namespace("http://example.org/ml_core.owl#")  # core namespace
T = Namespace("http://example.org/ml_trust.owl#")  # extension namespace
g = Graph().parse(SRC, format="xml")  # ontology with the record of the year
rows = list(g.query("""
SELECT ?model ?m ?year ?metric ?attribute ?debt WHERE {
  ?model c:achieves_metric ?m . ?m c:measured_on ?year . ?m t:is_degraded true .
  ?m t:of_metric_kind ?metric . ?metric t:supports_attribute ?attribute . ?debt t:requires_attribute ?attribute .
  FILTER (?year = ?y && ?debt = ?d) }""", initNs={"c": C, "t": T},
    initBindings={"y": T["Weather_Year_%d" % YEAR], "d": T[DEBT]}))  # the pattern of Q12
v = Graph()  # the view
v.bind("c", C); v.bind("t", T)  # prefixes
v.add((URIRef("http://example.org/trustworthiness_debt_chain.owl"), RDF.type, OWL.Ontology))  # header
for p in (C.achieves_metric, C.measured_on, T.of_metric_kind, T.supports_attribute, T.requires_attribute):  # the five links
    v.add((p, RDF.type, OWL.ObjectProperty))  # declared as in the source
for model, m, year, metric, attribute, debt in rows:  # one row is one path
    for node in (model, m, year, metric, attribute, debt):  # every node of the path
        v.add((node, RDF.type, OWL.NamedIndividual))  # an individual
    v.add((model, C.achieves_metric, m)); v.add((m, C.measured_on, year))  # model, measurement, year
    v.add((m, T.of_metric_kind, metric)); v.add((metric, T.supports_attribute, attribute))  # metric and attribute
    v.add((debt, T.requires_attribute, attribute))  # debt
for s, p, o in list(v):  # safety check
    if p != RDF.type: assert (s, p, o) in g, (s, p, o)  # every link exists in the source ontology
v.serialize(OUT, format="xml")  # the view file
print("wrote", OUT, "| paths:", len(rows), "| links:", sum(1 for _, p, _ in v if p != RDF.type))  # summary
