"""Harvest GLEIF lei-records for every LEI value in the EIOPA register export.

Batch filter requests (50 LEIs per call) against the public GLEIF API,
throttled for the unauthenticated rate limit, with a resumable JSONL cache.

Outputs:
  data/gleif_records.jsonl   one record per LEI found
  data/gleif_missing.json    LEI values the API returned nothing for
"""
import csv, json, os, time, urllib.request

BATCH = 50


def main():
    rows = list(csv.DictReader(open("data/eiopa_register.csv", encoding="utf-8-sig"), delimiter=";"))
    leis = sorted({r["LEI"].strip().upper() for r in rows if r["LEI"].strip()})
    print("distinct LEIs:", len(leis))

    done = set()
    if os.path.exists("data/gleif_records.jsonl"):
        for line in open("data/gleif_records.jsonl"):
            try:
                done.add(json.loads(line)["lei"])
            except (ValueError, KeyError):
                pass
    todo = [l for l in leis if l not in done]
    print("todo:", len(todo))

    found = set(done)
    with open("data/gleif_records.jsonl", "a") as out:
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            url = ("https://api.gleif.org/api/v1/lei-records?filter%5Blei%5D="
                   + ",".join(chunk) + f"&page%5Bsize%5D={BATCH}")
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={
                        "User-Agent": "insurance-register-ontology (research)",
                        "Accept": "application/vnd.api+json"})
                    d = json.load(urllib.request.urlopen(req, timeout=60))
                    for r in d.get("data", []):
                        a = r["attributes"]; e = a["entity"]; reg = a["registration"]
                        rec = {
                            "lei": r["id"],
                            "legalName": e["legalName"]["name"],
                            "entityStatus": e.get("status"),
                            "entityCategory": e.get("category"),
                            "legalForm": (e.get("legalForm") or {}).get("id"),
                            "jurisdiction": e.get("jurisdiction"),
                            "country": (e.get("legalAddress") or {}).get("country"),
                            "regStatus": reg.get("status"),
                            "lastUpdate": reg.get("lastUpdateDate"),
                            "nextRenewal": reg.get("nextRenewalDate"),
                            "managingLou": reg.get("managingLou"),
                        }
                        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        found.add(r["id"])
                    out.flush()
                    break
                except Exception as ex:
                    print("retry", i, attempt, ex)
                    time.sleep(10 * (attempt + 1))
            time.sleep(1.1)  # unauthenticated rate limit headroom
            if (i // BATCH) % 10 == 0:
                print(f"progress {i + len(chunk)}/{len(todo)}")

    missing = [l for l in leis if l not in found]
    json.dump(missing, open("data/gleif_missing.json", "w"))
    print("DONE. found:", len(found), "not in GLEIF:", len(missing))


if __name__ == "__main__":
    main()
