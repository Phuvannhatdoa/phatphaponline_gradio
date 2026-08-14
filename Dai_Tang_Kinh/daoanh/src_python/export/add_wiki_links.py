#!/usr/bin/env python3
"""
Add Wikipedia Links - Placeholder for future enrichment
Note: Wikipedia links require external API (Wikidata/Wikipedia API)
This script adds placeholder structure for wiki links
"""
import json
import os

OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/ontology/json"

def add_wiki_placeholders():
    """Add wiki placeholder to authority_links"""
    
    # Load enriched data
    input_file = os.path.join(OUTPUT_DIR, "entity_export_enriched.json")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data.get('entities', [])
    
    # Add placeholder note
    # Note: Real wiki links need Wikidata API enrichment
    wiki_added = 0
    
    for entity in entities:
        auth = entity.get('authority_links', {})
        if auth and not auth.get('wiki'):
            # Add placeholder for future enrichment
            # Real implementation would call Wikipedia API here
            entity['authority_links']['wiki'] = None  # Placeholder
            wiki_added += 1
    
    # Add metadata note
    data['metadata']['wiki_enriched'] = False
    data['metadata']['note'] = 'Wikipedia links require Wikidata API enrichment'
    
    # Save
    output_file = os.path.join(OUTPUT_DIR, "entity_export_enriched.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Added wiki placeholders: {wiki_added} entities")
    print("📝 Note: Wikipedia links require Wikidata API enrichment")

if __name__ == "__main__":
    add_wiki_placeholders()