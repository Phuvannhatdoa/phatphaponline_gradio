#!/usr/bin/env python3
"""
P4: Scan genealogy places from GraphDB
Trích xuất tên chùa/địa danh từ bio trong .ttl phả hệ
"""

import re
import csv
import json
import requests
from collections import defaultdict

# GraphDB config
GRAPHDB_URL = "http://158.220.106.183:7200"
REPO = "buddhist"

def query_graphdb(sparql):
    """Query GraphDB repository"""
    url = f"{GRAPHDB_URL}/repositories/{REPO}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/sparql-results+json"
    }
    try:
        r = requests.post(url, data={"query": sparql}, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ GraphDB query error: {e}")
        return {"results": {"bindings": []}}

def get_all_monk_bios():
    """Lấy tất cả monk bios từ GraphDB"""
    # Use the correct namespace from GraphDB
    sparql = """
    PREFIX buddhist-kg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?monk ?name ?bio
    WHERE {
        ?monk a buddhist-kg:Monk .
        ?monk rdfs:label ?name .
        OPTIONAL { ?monk buddhist-kg:biographicalNote ?bio }
    }
    LIMIT 5000
    """
    print("📥 Querying monk bios from GraphDB...")
    results = query_graphdb(sparql)
    
    monks = []
    for row in results.get("results", {}).get("bindings", []):
        monk_uri = row.get("monk", {}).get("value", "")
        name = row.get("name", {}).get("value", "")
        bio = row.get("bio", {}).get("value", "")
        if name and bio:
            monks.append({"uri": monk_uri, "name": name, "bio": bio})
    
    print(f"✅ Found {len(monks)} monks with bios")
    return monks

def extract_places_from_bio(bio_text):
    """Trích xuất tên chùa/địa danh từ bio text"""
    if not bio_text:
        return []
    
    places = []
    
    # Vietnamese temple patterns - more precise
    temple_patterns = [
        r'chùa\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)',
        r'Tổ\s+đình\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)',
        r'tịnh\s+xá\s+([A-Za-zÀ-ỹ]+)',
        r'tịnh\s+viện\s+([A-Za-zÀ-ỹ]+)',
    ]
    
    for pattern in temple_patterns:
        matches = re.findall(pattern, bio_text)
        for match in matches:
            place = match.strip()
            if len(place) >= 2:
                places.append(place)
    
    # Vietnamese location - more precise
    location_patterns = [
        r'tại\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)',
        r'ở\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, bio_text)
        for match in matches:
            place = match.strip()
            # Filter common non-place words
            if len(place) >= 2 and place.lower() not in ['năm', 'tháng', 'ngày', 'giờ', 'tuổi', 'đời', 'đường', 'lối', 'nơi', 'đâu', 'này', 'kia', 'đó', 'họ', 'tên', 'mình', 'tao', 'ta', 'đây', 'kia', 'trong', 'ngoài', 'trước', 'sau']:
                places.append(place)
    
    # Chinese characters for places (寺, 院, 堂, 庵, 觀, 塔, 山, 洞, 林, 園)
    chinese_patterns = [
        r'([一-龥]{2,10}(?:寺|院|堂|庵|觀|塔|山|洞|林|園))',
    ]
    
    for pattern in chinese_patterns:
        matches = re.findall(pattern, bio_text)
        for match in matches:
            place = match.strip()
            if len(place) >= 2:
                places.append(place)
    
    return list(set(places))

def scan_genealogy():
    """Main scan function"""
    print("🔍 P4: Scanning genealogy places...")
    
    # Get all monk bios
    monks = get_all_monk_bios()
    
    # Extract places
    place_count = defaultdict(list)
    
    for monk in monks:
        places = extract_places_from_bio(monk["bio"])
        for place in places:
            place_count[place].append({
                "monk": monk["name"],
                "uri": monk["uri"]
            })
    
    # Write CSV
    output_file = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/raw_vietnam_places.csv"
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["place_name_raw", "mentioned_in_monk", "source_monk_uri", "frequency"])
        
        for place, monks_list in sorted(place_count.items(), key=lambda x: -len(x[1])):
            for m in monks_list:
                writer.writerow([place, m["monk"], m["uri"], len(monks_list)])
    
    print(f"✅ Wrote {len(place_count)} unique places to {output_file}")
    
    # Also save as JSON for easier processing
    json_output = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/raw_vietnam_places.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(place_count, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON: {json_output}")
    
    # Top 20 places
    print("\n📊 Top 20 places:")
    for place, monks_list in sorted(place_count.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {place}: {len(monks_list)} lần")

if __name__ == "__main__":
    scan_genealogy()
