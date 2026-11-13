# Runs one SPARQL query file on the ontology for a chosen model and prints the answer as a table.
# Usage: python code/ask.py QUERY_NAME [MODEL] [ONTOLOGY_FILE]
# Example: python code/ask.py Q1_model_information LR_Weather
import os  # paths
import sys  # command line arguments

import pandas as pd  # result table
import rdflib  # RDF graph and SPARQL engine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository folder
DEFAULT_OWL = os.path.join(ROOT, "ontology", "trustworthiness_debt.owl")  # the static ontology
_GRAPHS = {}  # loaded ontologies, one per file

def local(v):  # readable value of one cell
    if isinstance(v, rdflib.URIRef):  # an ontology entity
        return v.split("#")[-1]  # its local name
    return None if v is None else v.toPython()  # a literal as a Python value

def run_query(name, model="MLP_Weather", owl=DEFAULT_OWL):  # one query for one model
    if owl not in _GRAPHS:  # first use of this file
        _GRAPHS[owl] = rdflib.Graph().parse(owl, format="xml")  # load it once
    text = open(os.path.join(ROOT, "queries", name + ".rq")).read()  # the query exactly as used in Protégé
    text = text.replace("t:MLP_Weather", "t:" + model)  # the example model becomes the chosen model
    res = _GRAPHS[owl].query(text)  # run it
    cols = [str(c) for c in res.vars]  # column names
    return pd.DataFrame([[local(r[c]) for c in res.vars] for r in res], columns=cols)  # answer as a table

if __name__ == "__main__":  # command line use
    q = sys.argv[1]  # query name, for example Q1_model_information
    m = sys.argv[2] if len(sys.argv) > 2 else "MLP_Weather"  # model name
    o = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OWL  # ontology file
    print(run_query(q, m, o).to_string(index=False))  # print the table
