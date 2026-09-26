#!/usr/bin/env python3
"""
Bulk Import - Import entities enrichment data vào verification system
Input: entity_export_enriched.json
Output: verification.json format cho Admin UI
"""
import json
import os
from datetime import datetime

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/ontology/json"

def load_enriched():
    """Load enriched entity data"""
    input_file = os.path.join(OUTPUT_DIR, "entity_export_enriched.json")
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_to_verification(entities):
    """Convert entities to verification format"""
    items = []
    
    for e in entities:
        # Only include entities with meaningful data
        if not e.get('biography') and not e.get('authority_links'):
            continue
        
        item = {
            "id": e.get('id'),
            "name": e.get('name'),
            "han_name": e.get('han_name'),
            "dynasty": e.get('dynasty'),
            "biography": e.get('biography', ''),
            "authority_links": e.get('authority_links'),
            "status": "approved",
            "enriched_at": datetime.utcnow().isoformat() + "Z",
            "graph_connections": e.get('graph_connections', [])
        }
        
        # Add spatial if available
        if e.get('spatial_timeline'):
            item['spatial_timeline'] = e['spatial_timeline']
        
        items.append(item)
    
    return items

def main():
    print("📦 Loading enriched data...")
    data = load_enriched()
    entities = data.get('entities', [])
    print(f"   Loaded {len(entities)} entities")
    
    # Convert to verification format
    print("🔄 Converting to verification format...")
    items = convert_to_verification(entities)
    print(f"   Converted {len(items)} items")
    
    # Save verification file
    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_items": len(items),
            "source": "entity_export_enriched.json"
        },
        "items": items
    }
    
    output_file = os.path.join(DATA_DIR, "verification.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved to: {output_file}")
    print(f"   Total: {len(items)} verified entities")
    
    # Sample
    if items:
        sample = items[0]
        print(f"\n📋 Sample:")
        print(f"   ID: {sample.get('id')}")
        print(f"   Name: {sample.get('name')}")
        print(f"   Biography: {len(sample.get('biography', ''))} chars")

if __name__ == "__main__":
    main()