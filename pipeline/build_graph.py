"""Build the IRO knowledge graph from the EIOPA register export + GLEIF harvest.

Inputs:
  data/eiopa_register.csv    EIOPA Register of Insurance Undertakings bulk CSV export
  data/gleif_records.jsonl   one GLEIF lei-record per line (pipeline/harvest_gleif.py)
  data/gleif_missing.json    LEI values the GLEIF API returned no record for

Output:
  data/build/iro_graph.ttl
  data/build/build_stats.json

Entity identity. A HOME-REGISTERED undertaking is keyed by (home country, NCA
identification code) taken from its "Domestic undertaking" row, the
register's own primary key. Branch rows frequently carry the HOST NCA's
registration code instead (measured: 171 of 298 LEIs with domestic+branch
rows use a different code on the branch row), so non-domestic rows are
joined to their home undertaking by key first, then by unambiguous LEI;
rows that still match nothing (for example third-country branches, which
have no home row in this register at all) become iro:RegisteredPresence
nodes rather than being silently merged or dropped. A branch's own host
code is recorded as one more authority-scoped identifier assertion on the
home undertaking. LEIs are never used as entity keys: their quality is
what this graph measures.
"""
import csv, json, os, re, sys, time, unicodedata
from collections import defaultdict
from rdflib import Graph, Namespace, Literal, URIRef, RDF, XSD
from checksums import lei_checksum_valid

IRO = Namespace("https://gov.tesseract.academy/def/insurance#")
IROSCH = Namespace("https://gov.tesseract.academy/def/insurance/scheme#")
BASE = "https://gov.tesseract.academy/id/insurance/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

MODE_CONCEPT = {
    "EEA FPS": IROSCH.EEAFreedomOfServices,
    "EEA branch": IROSCH.EEABranch,
    "3rd country branch": IROSCH.ThirdCountryBranch,
    "FPS for EEA Branches": IROSCH.FPSForEEABranch,
}


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")
    return s[:80] or "x"


def parse_date(s):
    s = s.strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return time.strftime("%Y-%m-%d", time.strptime(s, fmt))
        except ValueError:
            continue
    return None


def key_of(r):
    code = r["Identification code"].strip()
    if not code:
        code = "unkeyed-" + slug(r["Official name of the entity"])[:40]
    return (r["Home Country"].strip(), code)


def main():
    t0 = time.time()
    rows = list(csv.DictReader(open("data/eiopa_register.csv", encoding="utf-8-sig"), delimiter=";"))
    gleif = {}
    with open("data/gleif_records.jsonl") as f:
        for line in f:
            r = json.loads(line)
            gleif[r["lei"]] = r
    missing = set(json.load(open("data/gleif_missing.json")))

    g = Graph()
    g.bind("iro", IRO); g.bind("irosch", IROSCH); g.bind("skos", SKOS)

    lei_nodes = {}

    def lei_node(lei):
        if lei not in lei_nodes:
            ln = URIRef(BASE + "identifier/lei/" + slug(lei))
            lei_nodes[lei] = ln
            g.add((ln, RDF.type, IRO.Identifier))
            g.add((ln, RDF.type, IRO.LEI))
            g.add((ln, IRO.identifierScheme, IROSCH.LEI))
            g.add((ln, IRO.identifierValue, Literal(lei)))
            g.add((ln, IRO.sourceSystem, IROSCH["EIOPA-DATINS"]))
            g.add((ln, IRO.checksumValid, Literal(lei_checksum_valid(lei))))
            g.add((ln, IRO.inGleif, Literal(lei not in missing)))
            gr = gleif.get(lei)
            if gr:
                g.add((ln, IRO.gleifEntityStatus, Literal(gr["entityStatus"] or "")))
                g.add((ln, IRO.gleifRegistrationStatus, Literal(gr["regStatus"] or "")))
                g.add((ln, IRO.gleifLegalName, Literal(gr["legalName"])))
        return lei_nodes[lei]

    def add_nca_code(subject, home, code):
        nid = URIRef(BASE + f"identifier/nca-code/{home}/{slug(code)}")
        g.add((nid, RDF.type, IRO.Identifier))
        g.add((nid, RDF.type, IRO.NationalIdentificationCode))
        g.add((nid, IRO.identifierScheme, IROSCH.NationalIdentificationCode))
        g.add((nid, IRO.identifierValue, Literal(code)))
        g.add((nid, IRO.sourceSystem, IROSCH["EIOPA-DATINS"]))
        g.add((nid, IRO.identifies, subject))
        g.add((subject, IRO.identifiedBy, nid))

    # ── Pass 1: domestic rows → undertakings + home registrations ──
    undertakings = {}          # key -> URIRef
    lei_to_domestic = defaultdict(set)
    for r in rows:
        if r["Cross border status"].strip() != "Domestic undertaking":
            continue
        key = key_of(r)
        home, code = key
        if key not in undertakings:
            u = URIRef(BASE + f"undertaking/{home}/{slug(code)}")
            undertakings[key] = u
            g.add((u, RDF.type, IRO.InsuranceUndertaking))
            g.add((u, IRO.legalName, Literal(r["Official name of the entity"].strip())))
            if r["International Name"].strip():
                g.add((u, IRO.internationalName, Literal(r["International Name"].strip())))
            g.add((u, IRO.homeCountry, URIRef(BASE + "country/" + home)))
            g.add((URIRef(BASE + "country/" + home), RDF.type, IRO.Country))

            nca = URIRef(BASE + "nca/" + slug(r["Name of NCA"].strip() or home))
            g.add((nca, RDF.type, IRO.SupervisoryAuthority))
            g.add((nca, IRO.legalName, Literal(r["Name of NCA"].strip())))

            reg = URIRef(str(u) + "/registration")
            g.add((reg, RDF.type, IRO.Registration))
            g.add((reg, IRO.registrationOf, u))
            g.add((reg, IRO.registeredBy, nca))
            for field, prop in (("Registration start date", IRO.registrationStart),
                                ("Registration end date", IRO.registrationEnd)):
                d = parse_date(r[field])
                if d:
                    g.add((reg, prop, Literal(d, datatype=XSD.date)))
            add_nca_code(u, home, code)

        u = undertakings[key]
        lei = r["LEI"].strip().upper()
        if lei:
            ln = lei_node(lei)
            g.add((ln, IRO.identifies, u))
            g.add((u, IRO.identifiedBy, ln))
            lei_to_domestic[lei].add(key)

    # ── Pass 2: non-domestic rows → operations, joined home-first ──
    n_ops = 0
    presences = {}
    unmatched = 0
    for i, r in enumerate(rows):
        status = r["Cross border status"].strip()
        if status == "Domestic undertaking":
            continue
        key = key_of(r)
        home, code = key
        lei = r["LEI"].strip().upper()

        subject = undertakings.get(key)
        joined_via_lei = False
        if subject is None and lei and len(lei_to_domestic[lei]) == 1:
            subject = undertakings[next(iter(lei_to_domestic[lei]))]
            joined_via_lei = True
        if subject is None:
            # A presence with no home row in this register (third-country
            # branches by construction; otherwise an unjoinable branch row).
            if key not in presences:
                p = URIRef(BASE + f"presence/{home}/{slug(code)}")
                presences[key] = p
                g.add((p, RDF.type, IRO.RegisteredPresence))
                g.add((p, IRO.legalName, Literal(r["Official name of the entity"].strip())))
                g.add((p, IRO.homeCountry, URIRef(BASE + "country/" + home)))
                add_nca_code(p, home, code)
                if lei:
                    ln = lei_node(lei)
                    g.add((ln, IRO.identifies, p))
                    g.add((p, IRO.identifiedBy, ln))
            subject = presences[key]
            unmatched += 1
        else:
            if joined_via_lei:
                # The branch's host-side code is one more authority-scoped
                # identifier assertion on the home undertaking.
                add_nca_code(subject, home, code)
            if lei:
                # The row's LEI is asserted for this subject too. Usually a
                # no-op; where a branch row files a DIFFERENT LEI than the
                # domestic row, this creates the second assertion the
                # conflict rules exist to see.
                ln = lei_node(lei)
                g.add((ln, IRO.identifies, subject))
                g.add((subject, IRO.identifiedBy, ln))

        mode = MODE_CONCEPT.get(status)
        host = r["EU Country where the entity operates"].strip()
        if mode is not None and host:
            op = URIRef(str(subject) + f"/op/{slug(host)}/{slug(status)}/{i}")
            g.add((op, RDF.type, IRO.CrossBorderOperation))
            g.add((op, IRO.operationOf, subject))
            g.add((op, IRO.hostCountry, URIRef(BASE + "country/" + slug(host))))
            g.add((op, IRO.operationMode, mode))
            for field, prop in (("Operation Start Date", IRO.operationStart),
                                ("Operation End Date", IRO.operationEnd)):
                d = parse_date(r[field])
                if d:
                    g.add((op, prop, Literal(d, datatype=XSD.date)))
            n_ops += 1

    os.makedirs("data/build", exist_ok=True)
    g.serialize("data/build/iro_graph.ttl", format="turtle")
    stats = {
        "rows": len(rows),
        "undertakings": len(undertakings),
        "registered_presences": len(presences),
        "non_domestic_rows_unjoined_to_home": unmatched,
        "lei_assertions": len(lei_nodes),
        "cross_border_operations": n_ops,
        "triples": len(g),
        "build_seconds": round(time.time() - t0, 1),
    }
    json.dump(stats, open("data/build/build_stats.json", "w"), indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    main()
