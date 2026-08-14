# Build report

Build date: 14 August 2026. Machine: Apple silicon laptop, Python 3.11, rdflib 7.6.0, pyshacl 0.40.1. Everything below states exactly what was fetched, what was computed, and what could not be obtained. Nothing is estimated.

## What was fetched

| Source | File | Fetched | Contents |
|---|---|---|---|
| EIOPA Register of Insurance Undertakings | `DATINS_Export_*.csv` (11,264,975 bytes) | 2026-08-14, via ASP.NET postback replay (`pipeline/fetch_eiopa.py`) — the register has no stable export URL | 33,924 rows: 4,842 domestic registration rows, 18,730 EEA FPS, 9,174 FPS-for-EEA-branch, 1,141 EEA branch, 37 third-country branch rows; 29,461 rows carry an LEI (3,630 distinct values); 4,463 rows carry none |
| GLEIF lei-records API | `gleif_records.jsonl` (3,626 records) | 2026-08-14, batched 50 LEIs/request at unauthenticated rate limits (`pipeline/harvest_gleif.py`) | legal name, entity status, registration status, jurisdiction, managing LOU per LEI |

## What was computed

- **Two-pass entity resolution.** Domestic rows mint undertakings keyed by (home country, NCA identification code) — the register's own key. Non-domestic rows join to their home undertaking by key first, then by unambiguous LEI; measured necessity: of 298 LEIs appearing on both domestic and EEA-branch rows, **171 use a different identification code on the branch row** (the host NCA's). 1,839 rows (185 keys) joined nothing and became `iro:RegisteredPresence` — third-country branches by construction, plus branch rows the register itself does not key back to a head office. The join failure is retained as data.
- **ISO 7064 MOD 97-10** over every LEI value, with embedded test vectors including the register's own four defects. Result asserted per assertion node; pyshacl independently re-finds exactly these 4 from the recorded state (`data/build/shacl_summary.json`).
- **Cross-source status join**: GLEIF entity status + registration status attached to every resolvable LEI assertion.
- **Six set-based rules** (R1-R6, identical SPARQL semantics to `shapes/iro-rules.ttl`) plus the name-agreement comparison (normalization is code, not SPARQL). All counts in `reports/GOVERNANCE_REPORT.md`; the five committed queries in `queries/` reproduce the rule counts against the Turtle graph exactly (118 / 42 / 4 / shared-LEI decomposition / exporter table).

## Verified engineering gotchas

- Every date in the export is `DD/MM/YYYY HH:MM:SS`. A parser expecting bare `DD/MM/YYYY` silently drops **all 41,920 date values**, which makes every registration look active and inflates the LAPSED/INACTIVE rules threefold (348 vs the true 118; 680 vs the true 42). Caught by cross-checking graph queries against the set-based report; the two now agree exactly.
- The export is reachable only by replaying a SharePoint postback (`__VIEWSTATE`/`__EVENTVALIDATION` + `lkbtnExport` event target). The control GUID is scraped per run; it is not stable by contract.
- The GLEIF API accepts ~50 LEIs per `filter[lei]` request; the unauthenticated limit is 60 requests/minute. The 3,630-LEI harvest takes ~10 minutes with 1.1 s spacing.

## What could NOT be obtained

- **Undertaking type.** The public export does not distinguish direct insurers from pure reinsurers, nor life from non-life. `iro:InsuranceUndertaking` deliberately spans Solvency II Article 13(1)-(4); subclassing would require evidence the export does not carry.
- **Lines of business.** Not in the export. A SKOS registry of Solvency II lines of business (Annex I, Delegated Regulation (EU) 2015/35) is the natural v0.2 addition, sourced from EUR-Lex.
- **Authorisation class detail per undertaking** (which classes of insurance each authorization covers): visible in some NCA registers (e.g. BaFin's export carries category and authorisation dates) but not in the EIOPA bulk export.
- **A licence statement on the EIOPA register data.** EIOPA's site legal notice governs; EU-institution reuse policy generally permits reuse with attribution. Stated confidence: moderate. GLEIF data is CC0 1.0 (high confidence, stated in GLEIF's terms).
- **Whether findings 3/4 are register errors.** A LAPSED LEI or INACTIVE entity status can reflect GLEIF-side staleness rather than register-side error; the graph records the disagreement, not a verdict on who is wrong. Finding 2 (check-digit failures) is different: those values are arithmetically impossible, so the register side is wrong by construction.

## Data currency

Both sources are living systems fetched as "current": the register postback returns today's state; the GLEIF API returns today's records. None of the headline numbers are evergreen. The pipeline is fully reproducible; the specific totals are timestamped to 14 August 2026.
