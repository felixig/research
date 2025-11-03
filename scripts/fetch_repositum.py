#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://repositum.tuwien.at/oai/request"
OUTPUT_MD = "publications.md"
# Tu identificador de investigador en ReposiTUM
AUTHOR_SET = "crisrp09116"

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/"
}

def fetch_records(resumptionToken=None):
    """
    Hace la petición OAI-PMH y devuelve la lista de registros y el siguiente token.
    """
    if resumptionToken:
        params = {"verb": "ListRecords", "resumptionToken": resumptionToken}
    else:
        params = {"verb": "ListRecords", "metadataPrefix": "oai_dc", "set": AUTHOR_SET}

    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()

    root = ET.fromstring(r.content)
    records = root.findall(".//oai:record", NS)

    # Extraer resumptionToken para siguiente llamada
    token_el = root.find(".//oai:resumptionToken", NS)
    next_token = token_el.text if token_el is not None and token_el.text else None

    return records, next_token

def parse_record(record):
    """
    Convierte un registro XML en un diccionario con campos básicos
    """
    metadata = record.find("oai:metadata", NS)
    if metadata is None:
        return None

    dc = metadata.find("dc:dc", NS)
    if dc is None:
        return None

    title_el = dc.find("dc:title", NS)
    creator_el = dc.find("dc:creator", NS)
    date_el = dc.find("dc:date", NS)
    identifier_el = dc.find("dc:identifier", NS)

    title = title_el.text if title_el is not None else "No title"
    authors = creator_el.text if creator_el is not None else ""
    date = date_el.text if date_el is not None else ""
    link = identifier_el.text if identifier_el is not None else ""

    return {
        "title": title,
        "authors": authors,
        "date": date,
        "link": link
    }

def main():
    print("Fetching records from ReposiTUM OAI-PMH...")
    records_all = []
    token = None

    while True:
        records, token = fetch_records(token)
        print(f"Fetched {len(records)} records, next_token={token}")
        if not records:
            break
        records_all.extend(records)
        if not token:
            break

    print(f"Total records fetched: {len(records_all)}")

    # Parsear los registros
    publications = []
    for rec in records_all:
        pub = parse_record(rec)
        if pub:
            publications.append(pub)

    # Generar Markdown
    lines = []
    lines.append(f"# Publications\n")
    lines.append(f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_\n")

    for pub in sorted(publications, key=lambda x: x['date'], reverse=True):
        line = f"- **{pub['title']}**. {pub['authors']} ({pub['date']})"
        if pub['link']:
            line += f" [link]({pub['link']})"
        lines.append(line)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Wrote {OUTPUT_MD}")

if __name__ == "__main__":
    main()

