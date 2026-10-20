#!/usr/bin/env python3
"""
Export TTL - Generate Turtle files from master_db.json
Each entity = 1 TTL file for GraphDB import

Usage: python export_ttl.py
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
MASTER_DB = BASE_DIR / "data" / "master_db.json"
TTL_DIR = BASE_DIR / "ontology" / "monks"

PREFIXES = """@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://www.phatphaponline.org/ex/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix geo: <http://www.w3.org/2003/11/geo#> .

"""


def escape_ttl(s):
    if not s:
        return ""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', '')


def generate_ttl(person_id, record):
    display = record.get('display', {})
    bio = record.get('bio', {})
    lineage = record.get('lineage', {})
    ontology = record.get('ontology', {})

    lines = [PREFIXES]
    lines.append(f"<ex:monk/{person_id}> a bkg:Monk ;")

    labels = []
    if display.get('name_vi'):
        labels.append(f'rdfs:label "{escape_ttl(display["name_vi"])}"@vi')
    if display.get('name_han'):
        labels.append(f'rdfs:label "{escape_ttl(display["name_han"])}"@zh')
    if labels:
        lines.append('    ' + ' ;\n    '.join(labels) + ' ;')

    if bio.get('content'):
        lines.append(f'    bkg:biographicalNote """{escape_ttl(bio["content"])}"""@vi ;')

    if display.get('dynasty'):
        lines.append(f'    bkg:dynasty "{escape_ttl(display["dynasty"])}" ;')

    lines.append('    bkg:gender <bkg:Male> ;')

    if lineage.get('teacher_id'):
        lines.append(f'    bkg:hasTeacher <ex:monk/{lineage["teacher_id"]}> ;')

    for disciple in lineage.get('disciples', []):
        if isinstance(disciple, dict) and disciple.get('id'):
            lines.append(f'    bkg:hasDisciple <ex:monk/{disciple["id"]}> ;')
        elif isinstance(disciple, str):
            lines.append(f'    bkg:hasDisciple <ex:monk/{disciple}> ;')

    if ontology.get('same_as'):
        lines.append(f'    owl:sameAs <{ontology["same_as"]}> .')
    else:
        lines[-1] = lines[-1].rstrip(' ;') + ' .'

    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("🪷 EXPORT TTL FILES")
    print("=" * 60)

    TTL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n📂 Loading {MASTER_DB}...")
    with open(MASTER_DB, 'r', encoding='utf-8') as f:
        master_db = json.load(f)

    print(f"   Loaded {len(master_db)} records")

    print(f"\n🔄 Generating TTL files to {TTL_DIR}...")

    exported = 0
    errors = 0

    for person_id, record in master_db.items():
        try:
            ttl_content = generate_ttl(person_id, record)
            ttl_file = TTL_DIR / f"{person_id}.ttl"
            with open(ttl_file, 'w', encoding='utf-8') as f:
                f.write(ttl_content)
            exported += 1

            if exported % 5000 == 0:
                print(f"   Exported {exported} TTL files...")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"   ⚠️ Error {person_id}: {e}")

    print(f"\n✅ Done: {exported} TTL files created")
    if errors > 0:
        print(f"   ⚠️ {errors} errors")


if __name__ == "__main__":
    main()