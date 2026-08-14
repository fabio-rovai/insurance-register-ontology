"""pyshacl gate: layers 1-2 over the full graph.

Writes data/build/shacl_summary.json. Layer-3 rules run set-based in
governance_report.py (and as written on Oxigraph; see README).
"""
import json, time
from collections import Counter
from pyshacl import validate
from rdflib import Graph

t0 = time.time()
data = Graph()
data.parse("data/build/iro_graph.ttl", format="turtle")
data.parse("ontology/iro-core.ttl", format="turtle")
data.parse("skos/operation-modes.ttl", format="turtle")
shapes = Graph()
shapes.parse("shapes/iro-shapes.ttl", format="turtle")

conforms, report_graph, _ = validate(data, shacl_graph=shapes, advanced=False)
SH = "http://www.w3.org/ns/shacl#"
by_msg = Counter()
by_sev = Counter()
for res in report_graph.subjects(predicate=None):
    pass
from rdflib import URIRef
for res, _, msg in report_graph.triples((None, URIRef(SH + "resultMessage"), None)):
    by_msg[str(msg)[:120]] += 1
for res, _, sev in report_graph.triples((None, URIRef(SH + "resultSeverity"), None)):
    by_sev[str(sev).rsplit("#", 1)[-1]] += 1

summary = {
    "conforms": bool(conforms),
    "seconds": round(time.time() - t0, 1),
    "by_severity": dict(by_sev),
    "by_message": dict(by_msg.most_common()),
}
json.dump(summary, open("data/build/shacl_summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
