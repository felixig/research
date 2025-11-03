#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

BASE_URL = "https://repositum.tuwien.at/oai/request"
OUTPUT_MD = "publications.md"
AUTHOR_SET = "crisrp09116"  # Tu ID en ReposiTUM

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/"
}

# Configuración de intervalos de fechas (ejemplo: 2 años por bloque)
START_YEAR = 2000
END_YEAR = datetime.utcnow().year
INTERVAL = 2  # años

def fetch_records(from_date, until_date, resumptionToken=None):
    if resumptionToken:
        params = {"verb": "ListRecords", "resumptionToken": resumptionToken}
    else:
        params = {
            "verb": "ListRecords",
            "metadataPrefix": "oai_dc",
            "set": AUTHOR_SET,
            "from": from_date,
            "until": until_date
        }

    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    records = root.findall(".//oai:record", NS)

    token_el = root.find(".//oai:resumptionToken", NS)
    next_token = token_el.text if token_el is not None and token_el.text else None
    return records, next_token

def parse_record(record):
    metadata = record.find("oai:metadata", NS)
    if metadata is None:
        return None
    dc = metadata.find("dc:dc", NS)
    if dc is None:
        return None

    def get_text(tag):
        el = dc.find(f"dc:{tag}", NS)
        return el.text.strip() if el is not None else ""

    return {
        "title": get_text("title"),
        "authors": get_text("creator"),
        "date": get_text("date"),
        "type": get_text("type"),
        "link": get_text("identifier")
    }

def fetch_all():
    all_records = []
    for start in range(START_YEAR, END_YEAR + 1, INTERVAL):
        from_date = f"{start}-01-01"
        until_year = min(start + INTERVAL - 1, END_YEAR)
        until_date = f"{until_year}-12-31"

        print(f"Fetching records from {from_date} to {until_date} ...")
        token = None
        while True:
            records, token = fetch_records(from_date, until_date, token)
            all_records.extend(records)
            print(f"  Fetched {len(records)} records, next_token={token}")
            if not token:
                break
    return all_records

def main():
    records = fetch_all()
    print(f"Total records fetched: {len(records)}")

    publications = [parse_record(r) for r in records if parse_record(r)]
    # Ordenar por fecha descendente
    publications.sort(key=lambda x: x['date'], reverse=True)

    # Generar Markdown
    lines = []
    lines.append(f"# Publications\n")
    lines.append(f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_\n")

    for pub in publications:
        line = f"- **{pub['title']}**. {pub['authors']} ({pub['date']}) - {pub['type']}"
        if pub['link']:
            line += f" [link]({pub['link']})"
        lines.append(line)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Wrote {OUTPUT_MD}")

if __name__ == "__main__":
    main()

