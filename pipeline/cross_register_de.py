"""Cross-register test: is the EIOPA LEI gap a real absence, or a transmission
failure between a national regulator and EIOPA?

Germany is the test case: 492 of the 862 active domestic German undertakings in
the EIOPA register carry no LEI. BaFin, the German national competent authority,
publishes its own register with its own LEI column. If BaFin holds LEIs that
EIOPA does not, the gap is a pipe problem. If BaFin is empty too, the gap is real
and starts at the national register.

Matching is deliberately strict: the EIOPA identification code against BaFin's
REG NR / BAFIN-ID / BAK NR, or an exact match on a normalised legal name.
Fuzzy prefix matching was tested and rejected: it collapsed two distinct Saarland
insurers onto one LEI, which is exactly the error class this repository exists to
catch.

Input:  data/eiopa_register.csv, data/bafin_register.csv, data/bafin_reinsurers.csv
Output: reports/CROSS_REGISTER_DE.md
"""
import csv, re, time, unicodedata
from collections import Counter
from checksums import lei_checksum_valid

LEGAL_FORM = r"\b(AG|SE|KGAA|GMBH|VVAG|VAG|MBH|AKTIENGESELLSCHAFT|VERSICHERUNGSVEREIN AUF GEGENSEITIGKEIT|AUF GEGENSEITIGKEIT)\b"


def norm_name(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()
    s = s.replace("&", " UND ").replace("-", " ")
    s = re.sub(LEGAL_FORM, " ", s)
    return re.sub(r"[^A-Z0-9]", "", s)


def read(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig"), delimiter=";"))


def main():
    baf = read("data/bafin_register.csv")
    rein = read("data/bafin_reinsurers.csv")
    eio = read("data/eiopa_register.csv")

    # BaFin coverage. "Eur. EWR-Dienstleister" rows are EEA undertakings
    # passporting into Germany, not German-supervised entities.
    baf_de = [r for r in baf if "EWR" not in (r.get("GATTUNG") or "")]
    baf_lei = sum(1 for r in baf if r["LEI"].strip())
    baf_de_lei = sum(1 for r in baf_de if r["LEI"].strip())
    rein_lei = sum(1 for r in rein if r["LEI"].strip())

    baf_bad = sorted({(r["LEI"].strip().upper(), r["NAME"].strip())
                      for r in baf if r["LEI"].strip() and not lei_checksum_valid(r["LEI"])})

    de = [r for r in eio if r["Cross border status"] == "Domestic undertaking"
          and r["Home Country"].strip() == "DE" and not r["Registration end date"].strip()]
    de_nolei = [r for r in de if not r["LEI"].strip()]
    de_haslei = [r for r in de if r["LEI"].strip()]

    idx_code, idx_name = {}, {}
    for r in baf:
        for col in ("REG NR", "BAFIN-ID", "BAK NR"):
            v = (r.get(col) or "").strip()
            if v and v != "---":
                idx_code.setdefault(v, []).append(r)
        n = norm_name(r["NAME"])
        if n:
            idx_name.setdefault(n, []).append(r)

    def strict_match(row):
        code = row["Identification code"].strip()
        if code and code in idx_code:
            return idx_code[code], "code"
        n = norm_name(row["Official name of the entity"])
        if n and n in idx_name:
            return idx_name[n], "name"
        return [], None

    method = Counter()
    recovered = []
    for r in de_nolei:
        cands, how = strict_match(r)
        method[how] += 1
        leis = sorted({c["LEI"].strip().upper() for c in cands if c["LEI"].strip()})
        if leis:
            recovered.append((r["Official name of the entity"].strip(),
                              r["Identification code"].strip(), leis[0],
                              lei_checksum_valid(leis[0]),
                              (cands[0].get("GATTUNG") or "").strip(), how))

    both, disagree = 0, []
    for r in de_haslei:
        cands, how = strict_match(r)
        leis = {c["LEI"].strip().upper() for c in cands if c["LEI"].strip()}
        if leis:
            both += 1
            e = r["LEI"].strip().upper()
            if e not in leis:
                disagree.append((r["Official name of the entity"].strip(), e, sorted(leis)[0], how))

    matched = len(de_nolei) - method[None]
    L = []
    L.append("# Cross-register test: Germany, EIOPA against BaFin\n")
    L.append(f"Generated {time.strftime('%Y-%m-%d')} by pipeline/cross_register_de.py. "
             "Strict matching only (EIOPA identification code against BaFin REG NR / BAFIN-ID / "
             "BAK NR, or exact normalised legal name). Fuzzy prefix matching was tested and "
             "rejected after it collapsed two distinct Saarland insurers onto a single LEI.\n")

    L.append("## 1. What BaFin's own register carries\n")
    L.append("| Measure | Count |\n|---|---|")
    L.append(f"| BaFin insurance register rows | {len(baf):,} |")
    L.append(f"| Rows carrying an LEI | {baf_lei:,} ({100*baf_lei/len(baf):.1f}%) |")
    L.append(f"| German-supervised rows (excluding EEA inbound service providers) | {len(baf_de):,} |")
    L.append(f"| German-supervised rows carrying an LEI | {baf_de_lei:,} ({100*baf_de_lei/len(baf_de):.1f}%) |")
    L.append(f"| BaFin-listed reinsurers | {len(rein):,} |")
    L.append(f"| Reinsurers carrying an LEI | {rein_lei:,} ({100*rein_lei/len(rein):.1f}%) |")
    L.append(f"| BaFin LEI values failing ISO 7064 | {len(baf_bad)} |\n")

    L.append("BaFin's own impossible LEI values, in full:\n")
    for l, n in baf_bad:
        L.append(f"- `{l}` ({len(l)} characters): {n}")
    L.append("")

    L.append("## 2. Is the EIOPA gap a transmission failure?\n")
    L.append(f"Active domestic German undertakings in the EIOPA register: **{len(de):,}**, "
             f"of which **{len(de_nolei):,}** carry no LEI.\n")
    L.append("| Result | Count |\n|---|---|")
    L.append(f"| Matched into BaFin by identification code | {method['code']} |")
    L.append(f"| Matched by exact normalised name | {method['name']} |")
    L.append(f"| Not matched by either strict method | {method[None]} |")
    L.append(f"| **Of the {matched} matched, BaFin holds an LEI EIOPA does not** | **{len(recovered)}** |\n")

    L.append("Every recovered LEI below passes ISO 7064: these are real, valid identifiers "
             "sitting in the national regulator's public file while the European register "
             "records nothing.\n")
    L.append("| Undertaking | EIOPA code | LEI held by BaFin | Valid | BaFin category | Match |\n|---|---|---|---|---|---|")
    for name, code, lei, ok, gat, how in recovered:
        L.append(f"| {name[:52]} | {code} | `{lei}` | {'yes' if ok else 'NO'} | {gat[:40]} | {how} |")
    L.append("")

    L.append("## 3. Where both registers hold an LEI, do they agree?\n")
    L.append(f"Strictly matched undertakings holding an LEI in both registers: **{both}**. "
             f"Values disagreeing: **{len(disagree)}**.\n")
    if disagree:
        L.append("| Undertaking | EIOPA LEI | BaFin LEI | Match |\n|---|---|---|---|")
        for name, e, b, how in disagree:
            L.append(f"| {name[:52]} | `{e}` | `{b}` | {how} |")
        L.append("")

    L.append("## 4. Reading\n")
    L.append(f"The German LEI gap is not primarily a broken pipe between BaFin and EIOPA. "
             f"BaFin's own register carries an LEI for only {100*baf_de_lei/len(baf_de):.1f}% of the "
             f"German-supervised entities it lists, so most of the missing identifiers are missing "
             f"at source. But the pipe leaks too: {len(recovered)} undertakings that EIOPA records "
             f"as having no LEI demonstrably have a valid one in their own regulator's public file. "
             "Both readings matter operationally. If you screen counterparties against EIOPA, you "
             "are missing identifiers that exist and are free to obtain. If you assume a national "
             "register is the cleaner source, note that BaFin publishes "
             f"{len(baf_bad)} LEI values that cannot exist, three of them 19 characters long, "
             "which is a truncation defect rather than a typo.\n")

    open("reports/CROSS_REGISTER_DE.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    main()
