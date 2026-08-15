# Insurance Register Ontology (IRO)

An open OWL 2 ontology, SKOS registries, and SHACL governance layer for the **authorization, cross-border operation, and identifier fabric of insurance and reinsurance undertakings**, built and validated against the entire EEA register:

- **33,924 register rows** from the EIOPA Register of Insurance Undertakings bulk export (every EU/EEA-authorised insurance and reinsurance undertaking, with every cross-border operation row),
- **4,842 home-registered undertakings** (3,304 with live registrations), **185 registered presences** (third-country branches and unjoinable branch rows), **29,082 cross-border operation rows**, the full EU passporting fabric as a graph,
- **3,630 distinct LEI values**, every one check-digit validated and cross-checked against a same-day **GLEIF API harvest** (3,626 resolved; the 4 that do not exist in GLEIF are precisely the 4 that fail ISO 7064 arithmetic),
- joined into a **276,683-triple knowledge graph**, gated by SHACL, and reported on automatically.

This is not a toy schema. It is the EU's own register of (re)insurers, joined against the global LEI system, with the disagreements between them computed, graded, and queryable, which is the actual problem insurance data teams live with.

## Findings from the first full build (14 August 2026)

All figures from the 14 Aug 2026 EIOPA export and same-day GLEIF harvest. Both are living systems; a re-fetch changes the totals.

| # | Finding | Number |
|---|---|---|
| 1 | Active domestic (re)insurance undertakings carrying **no LEI at all** in the EU's own register, despite EIOPA's Guidelines on the use of the LEI (EIOPA-BoS-14-026). 492 of the 643 are German | **643 of 3,304 (19.5%)** |
| 2 | LEI values in the register that **fail ISO 7064 check digits**, values that cannot exist in the global LEI system. One is all zeros; one (`5493O00MN7XN3BBKCE67`, AP Skadesforsikring, DK) is a letter **O** where the real LEI has a zero, a hand-keyed transposition sitting in an official register, silently severing the undertaking from GLEIF | **4** (all four also absent from GLEIF) |
| 3 | Active undertakings whose LEI registration has **LAPSED** in GLEIF: authorised to write business, not maintaining the global identifier. 63 of the 118 are French | **118** |
| 4 | Active undertakings whose LEI's **entity status is INACTIVE** in GLEIF, the register says authorised, GLEIF says the legal entity has ceased. A cluster of Spanish mutuals dominates | **42** |
| 5 | LEIs filed for more than one register key: **227**, of which **56** carry materially different names, of which **3 are hard entity collapses**, including `549300KCPG3666EE4546` filed for both **SCOR Global Reinsurance France** and **SCOR Global Reinsurance Ireland DAC**, two distinct reinsurance legal entities on one identifier | **227 / 56 / 3** |
| 6 | Open cross-border operation rows belonging to undertakings whose home registration has **ended**, passports outliving the authorization they derive from | **283** |
| 7 | Register names that disagree with the GLEIF legal name even after aggressive normalization (e.g. MAPFRE MIDDLESEA vs MAPFRE MALTA, a rename one side has not caught up with) | **402 of 2,661 (15.1%)** |
| 8 | Across ALL 3,630 distinct LEIs filed anywhere in the register: ISSUED 2,590, RETIRED 680, LAPSED 351, DUPLICATE 3, **ANNULLED 1**, not in GLEIF 4 |, |

The passporting fabric itself: **13,848 open freedom-of-services operations**; top exporters DE (2,794), IE (1,658), FR (1,280), LU (1,166), NL (1,140), MT (915), Ireland, Luxembourg and Malta passport far above their domestic weight, which is the single-market working as designed and measurable from the graph in one query.

Full numbers, method, caveats: [BUILD_REPORT.md](BUILD_REPORT.md) and [reports/GOVERNANCE_REPORT.md](reports/GOVERNANCE_REPORT.md).

## Why this exists

Insurance is the least-served major financial vertical in open semantics, and the gap is verifiable:

- **FIBO** (EDM Council, MIT-licensed) contains, in its entirety, four insurance-related classes in a *guaranty* module plus two entity classes. The string "reinsur" occurs **once** in the whole ontology, inside a free-text definition. There is no Reinsurer, no Treaty, no Cession, nothing.
- **ACORD**'s Reference Architecture and data standards (including the reinsurance GRLC/EBOT/ECOT families) are membership-gated. **Lloyd's Core Data Record** (v3.3, extended to treaty reinsurance in May 2026) is published only through interactive portals. The one genuinely open standard, **OED** (CC0, Oasis LMF), is a flat-file schema for cat-model exposure, not an ontology.
- Lloyd's sunset **Blueprint Two** in March 2026 and repositioned around "setting standards and organising data". The reinsurers advertising ontology-engineer roles build their semantic models privately.

So the definitive open artifact starts where the data actually is: the public register fabric. IRO's design commitments, shared with its sibling, the [Investment Fund Ontology](https://github.com/fabio-rovai/investment-fund-ontology):

1. **Identifiers as first-class assertion nodes**, scheme, source system, computed validation state. Cross-system disagreement is a query, not an audit project.
2. **Scope as data**, the SKOS registry declares the LEI entity-scoped and the NCA code authority-scoped; a branch legitimately carrying its head office's LEI under a host NCA's code is *modelled*, not special-cased.
3. **Authorization and operation reified**, registrations and passports have their own lifecycles, so "a passport outliving its authorization" is a shape violation, not a spreadsheet reconciliation.
4. **Arithmetic in code, policy in shapes**, ISO 7064 runs in the pipeline and asserts `checksumValid`; SHACL requires the recorded result. pyshacl independently re-finds exactly the 4 impossible LEIs from the recorded state.

## Repository layout

```
ontology/iro-core.ttl            Core OWL: undertakings, registrations, operations,
                                 reified identifier fabric, GLEIF reconciliation facets
skos/operation-modes.ttl         SKOS: 5 operation modes (grounded in Directive 2009/138/EC),
                                 identifier schemes with scope levels, source systems
shapes/iro-shapes.ttl            Layers 1-2 SHACL: syntax, checksum policy, structure
shapes/iro-rules.ttl             Layer 3 SHACL-SPARQL: six cross-source business rules (R1-R6)
pipeline/fetch_eiopa.py          EIOPA register bulk export (ASP.NET postback replay)
pipeline/harvest_gleif.py        GLEIF API harvest, batched + resumable
pipeline/checksums.py            ISO 7064 MOD 97-10 with embedded test vectors
pipeline/build_graph.py          Two-pass join -> Turtle (home-registered vs presences)
pipeline/validate.py             pyshacl gate over the full graph
pipeline/governance_report.py    Set-based rules + automated governance report
queries/                         5 verified SPARQL queries (counts match the report exactly)
reports/GOVERNANCE_REPORT.md     The generated findings report
```

## Reproduce

```bash
pip install rdflib pyshacl
python pipeline/fetch_eiopa.py        # ~11 MB CSV via postback replay
python pipeline/harvest_gleif.py      # ~3,630 LEIs, ~10 min at unauthenticated rate limits
python pipeline/build_graph.py        # 276k triples in ~15 s
python pipeline/validate.py           # SHACL gate, ~8 s
python pipeline/governance_report.py  # reports/GOVERNANCE_REPORT.md
```

Layer-3 rules ship as standard SHACL-SPARQL and are executed set-based by the reference pipeline; on an Oxigraph-backed engine they run as written (see the [rdflib scale measurement](https://github.com/fabio-rovai/open-ontologies/tree/main/case-studies/investment-fund-ontology) from the sibling project: rdflib's failure mode at register scale is the multi-way self-join, not the anti-join).

## Licence

Code MIT; ontology, SKOS registries, shapes and reports CC BY 4.0. Source data: EIOPA Register of Insurance Undertakings (EU public register data, attribution given), GLEIF API records (CC0 1.0).

## Working with this

If your organisation runs on insurance entity data, register reconciliation, counterparty graphs, Solvency II reporting plumbing, treaty party resolution, this repo is the open baseline of exactly that discipline. For the applied version on your data: **fabio@thetesseractacademy.com**.
