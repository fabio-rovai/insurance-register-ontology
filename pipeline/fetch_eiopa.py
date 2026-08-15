"""Fetch the EIOPA Register of Insurance Undertakings bulk CSV export.

The register (register.eiopa.europa.eu) is a SharePoint application whose
export is an ASP.NET postback, not a stable URL. This script replays the
postback: fetch the page, lift the __VIEWSTATE/__EVENTVALIDATION fields,
POST the export event, save the CSV.

Output: data/eiopa_register.csv (~11 MB, ~34k rows, semicolon-delimited).
"""
import html, os, re, urllib.request, urllib.parse, http.cookiejar

URL = "https://register.eiopa.europa.eu/registers/register-of-insurance-undertakings"
EXPORT_TARGET = "ctl00$ctl34$g_3217d152_792c_4dd6_9a62_51a782ee2349$lkbtnExport"


def main():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "insurance-register-ontology (research; data-quality study)")]
    page = op.open(URL, timeout=90).read().decode("utf-8", "replace")

    def field(name):
        m = re.search(r'id="%s" value="([^"]*)"' % name, page)
        return html.unescape(m.group(1)) if m else None

    data = {"__EVENTTARGET": EXPORT_TARGET, "__EVENTARGUMENT": ""}
    for f in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", "__REQUESTDIGEST"):
        v = field(f)
        if v is not None:
            data[f] = v

    req = urllib.request.Request(URL, urllib.parse.urlencode(data).encode(), method="POST")
    resp = op.open(req, timeout=300)
    body = resp.read()
    disp = resp.headers.get("Content-Disposition", "")
    if "attachment" not in disp:
        raise SystemExit(f"export postback did not return a file (Content-Disposition: {disp!r}); "
                         "the page structure may have changed, re-derive EXPORT_TARGET from the page source")
    os.makedirs("data", exist_ok=True)
    with open("data/eiopa_register.csv", "wb") as f:
        f.write(body)
    print(f"saved data/eiopa_register.csv ({len(body):,} bytes; {disp})")


if __name__ == "__main__":
    main()
