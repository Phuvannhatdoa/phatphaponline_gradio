#!/usr/bin/env python3
"""
Export places from TTL file to JSON
Usage: python export_from_ttl.py
"""

import json
import re
import os

TTL_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/ontology/dila_places.ttl"
OUTPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places.json"

def parse_ttl_places():
    """Parse TTL file and extract places"""
    print("📤 Exporting places from TTL...")
    
    if not os.path.exists(TTL_FILE):
        print(f"❌ TTL file not found: {TTL_FILE}")
        return {"places": [], "count": 0}
    
    places = []
    current_place = {}
    current_subject = ""
    
    with open(TTL_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and prefixes
            if not line or line.startswith('#') or line.startswith('@prefix'):
                continue
            
            # New place - detect subject
            if ' a bkg:BuddhistPlace' in line:
                if current_place and current_place.get('id'):
                    places.append(current_place)
                current_place = {}
                continue
            
            # Parse properties - check for subject line
            if line.startswith('bkg:place_'):
                current_subject = line.split(' ')[0]
                continue
            
            # Check for property in current place
            if 'bkg:dilaId' in line:
                match = re.search(r'bkg:dilaId\s+"([^"]+)"', line)
                if match:
                    current_place['id'] = match.group(1)
            
            elif 'bkg:nameChinese' in line:
                match = re.search(r'bkg:nameChinese\s+"([^"]+)"', line)
                if match:
                    current_place['nameChinese'] = match.group(1)
            
            elif 'bkg:nameVietnamese' in line:
                match = re.search(r'bkg:nameVietnamese\s+"([^"]+)"@vi', line)
                if match:
                    current_place['nameVietnamese'] = match.group(1)
            
            elif 'bkg:nameEnglish' in line:
                match = re.search(r'bkg:nameEnglish\s+"([^"]+)"', line)
                if match:
                    current_place['nameEnglish'] = match.group(1)
            
            elif 'geo:lat' in line:
                match = re.search(r'geo:lat\s+"([^"]+)"', line)
                if match:
                    current_place['lat'] = match.group(1)
            
            elif 'geo:long' in line:
                match = re.search(r'geo:long\s+"([^"]+)"', line)
                if match:
                    current_place['lon'] = match.group(1)
            
            elif 'bkg:countryCode' in line:
                match = re.search(r'bkg:countryCode\s+"([^"]+)"', line)
                if match:
                    current_place['country'] = match.group(1)
            
            elif 'bkg:district' in line:
                match = re.search(r'bkg:district\s+"([^"]+)"', line)
                if match:
                    current_place['province'] = match.group(1)
            
            elif 'schema:description' in line:
                match = re.search(r'schema:description\s+"([^"]+)"@vi', line)
                if match:
                    current_place['description'] = match.group(1)
            
            elif 'bkg:source' in line:
                match = re.search(r'bkg:source\s+"([^"]+)"', line)
                if match:
                    current_place['source'] = match.group(1)
    
    # Add last place
    if current_place and current_place.get('id'):
        places.append(current_place)
    
    # Ensure all fields exist
    for p in places:
        p.setdefault('id', '')
        p.setdefault('nameChinese', '')
        p.setdefault('nameVietnamese', '')
        p.setdefault('nameEnglish', '')
        p.setdefault('lat', '')
        p.setdefault('lon', '')
        p.setdefault('country', '')
        p.setdefault('province', '')
        p.setdefault('description', '')
        p.setdefault('source', 'DILA')
        p.setdefault('referencedIn', [])
    
    output = {"places": places, "count": len(places)}
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported {len(places)} places to {OUTPUT_FILE}")
    return output

if __name__ == "__main__":
    parse_ttl_places()
