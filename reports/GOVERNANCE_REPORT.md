# Automated governance report: the EEA insurance register fabric

Generated 2026-08-14 by pipeline/governance_report.py from the EIOPA Register of Insurance Undertakings bulk export and per-LEI GLEIF API records harvested the same day. Every figure is computed; nothing is hand-typed. Both sources are living systems, so a re-fetch will produce different totals.

## 1. Universe

| Object | Count |
|---|---|
| Register rows (entity x operation-country) | 33,924 |
| Distinct undertakings (home country + NCA code) | 5,719 |
| Domestic registration rows | 4,842 |
| Active domestic undertakings (no registration end date) | 3,304 |
| Distinct LEI values filed anywhere in the register | 3,630 |

## 2. Layer-3 rules (set-based execution)

| Rule | Severity | Findings |
|---|---|---|
| R1 Active domestic undertaking with no LEI | Warning | 643 of 3,304 (19.5%) |
| R2 LEI fails ISO 7064 check digits | Violation | 4 |
| R3 Active undertaking, LEI LAPSED in GLEIF | Warning | 118 |
| R4 Active undertaking, GLEIF entity INACTIVE | Warning | 42 |
| R5 LEI shared by >1 register key | Warning | 227 LEIs; 56 with materially different names; 3 hard collapses |
| R6 Open operation row for an ended registration | Violation | 283 |

R1 by home country (top 10): DE 492, SE 81, BE 24, AT 23, DK 5, BG 5, HU 4, NO 4, SK 1, CY 1.

R2, in full, with the undertaking that filed each impossible value:

- `00000000000000000000` — European Risk Insurance Company ehf. (DE)
- `529900TDXS505XDXWZ69` — Forsikringsaktieselskabet K.a.B. International (DK)
- `549300X77HR0ZWZELM25` — Застрахователно акционерно дружество Булстрад Виена Иншурънс Груп (BG)
- `5493O00MN7XN3BBKCE67` — AP Skadesforsikring Aktieselskab (DK)

`5493O00MN7XN3BBKCE67` is a letter O where the real LEI `5493000MN7XN3BBKCE67` (same undertaking, per GLEIF) has a zero: a hand-keyed transposition sitting in the official register. None of the four values exists in GLEIF.

R3 by home country: FR 63, ES 10, BG 7, AT 6, NL 6, DK 4, NO 4, DE 4, SE 2, EE 2.

R5's three hard collapses — materially different names sharing one LEI on domestic registrations only:

- `213800KL7RVEKAJHQO02` — ARNOLD CLARK (MALTA) LIMITED / ARNOLD CLARK LIFE INSURANCE (MALTA) LIMITED
- `529900FQ7DWNLPNRN517` — Lippische Landes-Brandversicherungsanstalt / Lippische Landesbrandversicherung AG
- `549300KCPG3666EE4546` — SCOR GLOBAL REINSURANCE France / SCOR Global Reinsurance Ireland Designated Activity Company

One of the three is a reinsurance pair: SCOR Global Reinsurance France and SCOR Global Reinsurance Ireland Designated Activity Company, two distinct legal entities filed under the same LEI. The remaining 53 different-name shares involve branch rows, where a branch legitimately carries its head office's LEI under a host NCA's identification code — the scope distinction the ontology's scheme registry declares as data.

## 3. GLEIF status of the register's LEIs

On ACTIVE domestic undertakings (2,661 GLEIF-resolvable LEIs): ISSUED 2,500, LAPSED 118, RETIRED 42, PENDING_TRANSFER 1.

Across ALL 3,630 distinct LEI values filed in the register (including ended registrations and cross-border rows): ISSUED 2,590, RETIRED 680, LAPSED 351, NOT_IN_GLEIF 4, DUPLICATE 3, ANNULLED 1, PENDING_TRANSFER 1.

## 4. Name agreement with GLEIF

Of 2,661 active domestic undertakings with a GLEIF-resolvable LEI, 402 (15.1%) have a register name that does not match the GLEIF legal name even after aggressive normalization (case, diacritics, punctuation stripped, substring containment allowed). Some are legal-form spelling variants; some are renames one side has not caught up with (e.g. MAPFRE MIDDLESEA P.L.C. vs MAPFRE MALTA P.L.C.). The normalization is code, not SPARQL, which is why this is a report finding rather than a layer-3 shape.

## 5. The passporting fabric

Open freedom-of-services operations: 13,848 undertaking-x-host-country rows.

Top exporters (home country of the passporting undertaking): DE 2,794, IE 1,658, FR 1,280, LU 1,166, NL 1,140, MT 915, BE 709, SE 551.

Top host markets: FR 618, BE 610, IT 597, ES 592, AT 574, DE 570, NL 555, PT 552.

