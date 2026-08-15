# Cross-register test: Germany, EIOPA against BaFin

Generated 2026-08-15 by pipeline/cross_register_de.py. Strict matching only (EIOPA identification code against BaFin REG NR / BAFIN-ID / BAK NR, or exact normalised legal name). Fuzzy prefix matching was tested and rejected after it collapsed two distinct Saarland insurers onto a single LEI.

## 1. What BaFin's own register carries

| Measure | Count |
|---|---|
| BaFin insurance register rows | 5,400 |
| Rows carrying an LEI | 1,074 (19.9%) |
| German-supervised rows (excluding EEA inbound service providers) | 4,824 |
| German-supervised rows carrying an LEI | 505 (10.5%) |
| BaFin-listed reinsurers | 76 |
| Reinsurers carrying an LEI | 29 (38.2%) |
| BaFin LEI values failing ISO 7064 | 5 |

BaFin's own impossible LEI values, in full:

- `5493000DB4L2GMHE8F8` (19 characters): Foyer Assurances S.A.
- `5967007LIEEXZXC3000` (19 characters): Industriforsikring AS
- `64883H3D597L117RRQ04` (20 characters): Westfield Specialty International (Europe) S.A.
- `9695006OKWFLRW8V318` (19 characters): AXA Health Insurance
- `98450081062CA8590G30` (20 characters): Mutual Insurance and Reinsurance for Information Systems (MIRIS)

## 2. Is the EIOPA gap a transmission failure?

Active domestic German undertakings in the EIOPA register: **862**, of which **492** carry no LEI.

| Result | Count |
|---|---|
| Matched into BaFin by identification code | 33 |
| Matched by exact normalised name | 11 |
| Not matched by either strict method | 448 |
| **Of the 44 matched, BaFin holds an LEI EIOPA does not** | **14** |

Every recovered LEI below passes ISO 7064: these are real, valid identifiers sitting in the national regulator's public file while the European register records nothing.

| Undertaking | EIOPA code | LEI held by BaFin | Valid | BaFin category | Match |
|---|---|---|---|---|---|
| Vorsorgekasse Hoesch Dortmund Sterbegeldversicherung | 3107 | `3912000QMJ4HQKUZJO16` | yes | Sterbekasse unter Bundesaufsicht | code |
| GGG Kraftfahrzeug-Reparaturkosten-Versicherungs-Akti | 5589 | `391200HKIGKAN65IXL88` | yes | Schaden- und Unfallversicherer unter Bun | code |
| Bayer Beistandskasse | 3019 | `5299007MSP5P150C8573` | yes | Sterbekasse unter Bundesaufsicht | code |
| Gothaer Lebensversicherung auf Gegenseitigkeit | 1037 | `529900N11WB8X1CESJ42` | yes | Lebensversicherer unter Bundesaufsicht | name |
| Nürnberger Lebensversicherung Aktiengesellschaft | 1071 | `529900Y3FTZAVPEYUI80` | yes | Lebensversicherer unter Bundesaufsicht | name |
| INTER Lebensversicherung aG | 1097 | `5299004Q6B6J1RWLZG45` | yes | Lebensversicherer unter Bundesaufsicht | name |
| HDI Lebensversicherung Aktiengesellschaft | 1142 | `5299004Y9OOH1UB9EH77` | yes | Lebensversicherer unter Bundesaufsicht | name |
| HDI Lebensversicherung Aktiengesellschaft | 1155 | `5299004Y9OOH1UB9EH77` | yes | Lebensversicherer unter Bundesaufsicht | name |
| Gothaer Krankenversicherung Aktiengesellschaft | 4110 | `529900EPT5BJG6RFEI05` | yes | Krankenversicherer unter Bundesaufsicht | name |
| Gothaer Allgemeine Versicherung Aktiengesellschaft | 5371 | `5299003C59ODEKQIR849` | yes | Schaden- und Unfallversicherer unter Bun | name |
| Rheinland Versicherungs-Aktiengesellschaft | 5439 | `529900Z5DS3MK8G49604` | yes | Schaden- und Unfallversicherer unter Bun | name |
| GENERALI Versicherung Aktiengesellschaft | 5456 | `5299004SL2CE7OOL8A43` | yes | Eur. EWR-Dienstleister, Versicherer unte | name |
| Gothaer Allgemeine Versicherung Aktiengesellschaft | 5597 | `5299003C59ODEKQIR849` | yes | Schaden- und Unfallversicherer unter Bun | name |
| Tryg Forsikring A/S | 5611 | `213800BIA5L8OPBER229` | yes | Eur. EWR-Dienstleister, Versicherer unte | name |

## 3. Where both registers hold an LEI, do they agree?

Strictly matched undertakings holding an LEI in both registers: **344**. Values disagreeing: **0**.

## 4. Reading

The German LEI gap is not primarily a broken pipe between BaFin and EIOPA. BaFin's own register carries an LEI for only 10.5% of the German-supervised entities it lists, so most of the missing identifiers are missing at source. But the pipe leaks too: 14 undertakings that EIOPA records as having no LEI demonstrably have a valid one in their own regulator's public file. Both readings matter operationally. If you screen counterparties against EIOPA, you are missing identifiers that exist and are free to obtain. If you assume a national register is the cleaner source, note that BaFin publishes 5 LEI values that cannot exist, three of them 19 characters long, which is a truncation defect rather than a typo.

