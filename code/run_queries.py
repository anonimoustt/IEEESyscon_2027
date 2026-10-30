# Runs every SPARQL query file on the ontology with rdflib, the same text that is pasted into the Protégé SPARQL Query tab,
# and writes each result table as CSV and as one Markdown file for the paper and the README.
# Usage: python run_queries.py ONTOLOGY_FILE QUERY_DIR OUT_DIR
import csv  # result tables
import glob  # query files
import os  # paths
import sys  # command line arguments

import rdflib  # SPARQL engine

OWL, QDIR, OUT = sys.argv[1:4]  # inputs and output folder
os.makedirs(OUT, exist_ok=True)  # create it
g = rdflib.Graph().parse(OWL, format="xml")  # load the RDF/XML file as asserted triples, as Protégé's SPARQL tab does

def short(v):  # readable value
    if isinstance(v, rdflib.URIRef):  # entity
        return v.split("#")[-1]  # local name
    return str(v) if v is not None else ""  # literal or empty

md = []  # Markdown report
for path in sorted(glob.glob(os.path.join(QDIR, "*.rq")), key=lambda p: int(os.path.basename(p)[1:].split("_")[0])):  # each query in number order
    text = open(path).read()  # query text
    res = g.query(text)  # run it
    cols = [str(v) for v in res.vars]  # column names
    rows = [[short(r[v]) for v in res.vars] for r in res]  # rows
    name = os.path.splitext(os.path.basename(path))[0]  # query name
    with open(os.path.join(OUT, name + ".csv"), "w", newline="") as f:  # save CSV
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)  # header and rows
    md.append("### %s (%d rows)\n\n| %s |\n|%s\n" % (name, len(rows), " | ".join(cols), "---|" * len(cols)))  # header
    md.extend("| %s |\n" % " | ".join(r) for r in rows)  # rows
    md.append("\n")  # spacing
    print(name, len(rows), "rows")  # progress
open(os.path.join(OUT, "query_results.md"), "w").write("".join(md))  # save the report
