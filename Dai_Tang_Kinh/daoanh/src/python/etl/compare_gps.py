#!/usr/bin/env python3
"""
GPS Compare Tool - Compare DILA quarterly updates with current database
Usage: python compare_gps.py [--download-new] [--approve-all]
"""

import json
import os
import requests
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import math

# Configuration
CURRENT_JSON = "/opt/phatphaponline_gradio/daoanh/data/places.json"
DILA_DOWNLOAD_URL = "https://authority.dila.edu.tw/downloads/authority_place.2026-04.zip"
DILA_OUTPUT_DIR = "/opt/phatphaponline_gradio/daoanh/data/dila_temp"
COMPARE_OUTPUT = "/opt/phatphaponline_gradio/daoanh/data/compare/changes.json"
GPS_THRESHOLD_METERS = 100

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS points in meters"""
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def download_dila():
    """Download latest DILA Place Authority"""
    print("📥 Downloading DILA Place Authority...")
    
    os.makedirs(DILA_OUTPUT_DIR, exist_ok=True)
    
    try:
        response = requests.get(DILA_DOWNLOAD_URL, stream=True)
        response.raise_for_status()
        
        zip_path = os.path.join(DILA_OUTPUT_DIR, "authority_place.zip")
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ Downloaded, extracting...")
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(DILA_OUTPUT_DIR)
        
        # Find XML file
        xml_files = [f for f in os.listdir(DILA_OUTPUT_DIR) if f.endswith('.xml')]
        if xml_files:
            return os.path.join(DILA_OUTPUT_DIR, xml_files[0])
        
        return None
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None

def parse_dila_places(xml_path):
    """Parse DILA XML to extract places with GPS"""
    print("📖 Parsing DILA XML...")
    
    places = {}
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Get namespace from root
        ns = root.tag.strip('{}')
        ns_map = {'': ns} if ns else {}
        
        # Find all place elements
        for place in root.findall('.//{http://www.tei-c.org/ns/1.0}place'):
            place_id = place.get('{http://www.w3.org/XML/1998/namespace}id')
            
            if not place_id:
                continue
            
            # Get name - find first placeName without specific attribute
            name_zh = ""
            for name_elem in place.findall('.//{http://www.tei-c.org/ns/1.0}placeName'):
                text = name_elem.text or ""
                if text and name_elem.get('{http://www.w3.org/XML/1998/namespace}lang') == 'zho-Hant':
                    name_zh = text
                    break
                elif text and not name_zh:
                    name_zh = text
            
            # Get GPS from <geo> element - format: "lon lat"
            lat = ""
            lon = ""
            geo_elem = place.find('.//{http://www.tei-c.org/ns/1.0}geo')
            if geo_elem is not None and geo_elem.text:
                geo_text = geo_elem.text.strip().split()
                if len(geo_text) >= 2:
                    lon = geo_text[0]
                    lat = geo_text[1]
            
            # Get district
            district = ""
            district_elem = place.find('.//{http://www.tei-c.org/ns/1.0}district')
            if district_elem is not None and district_elem.text:
                district = district_elem.text
            
            # Extract country from district
            country = ""
            if district and '-' in district:
                country = district.split('-')[0]
            
            if lat and lon:
                places[place_id] = {
                    "id": place_id,
                    "nameChinese": name_zh,
                    "lat": lat,
                    "lon": lon,
                    "country": country,
                    "district": district,
                    "source": "DILA"
                }
        
        print(f"✅ Found {len(places)} places with GPS")
        return places
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def load_current_places():
    """Load current places from JSON"""
    if not os.path.exists(CURRENT_JSON):
        print(f"⚠️ {CURRENT_JSON} not found")
        return {}
    
    with open(CURRENT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    places = {}
    for place in data.get('places', []):
        place_id = place.get('id')
        if place_id and place.get('lat') and place.get('lon'):
            places[place_id] = place
    
    print(f"📂 Loaded {len(places)} current places")
    return places

def compare_gps(current, new_dila):
    """Compare GPS between current and new DILA data"""
    print("🔄 Comparing GPS...")
    
    results = {
        "checked_at": datetime.now().isoformat(),
        "current_count": len(current),
        "new_count": len(new_dila),
        "summary": {
            "new_places": [],
            "deleted_places": [],
            "gps_changed": [],
            "unchanged": 0
        },
        "details": []
    }
    
    current_ids = set(current.keys())
    new_ids = set(new_dila.keys())
    
    # New places (in DILA but not in current)
    new_place_ids = new_ids - current_ids
    results["summary"]["new_places"] = list(new_place_ids)[:50]  # Limit to 50
    
    # Deleted places (in current but not in DILA)
    deleted_place_ids = current_ids - new_ids
    results["summary"]["deleted_places"] = list(deleted_place_ids)[:50]
    
    # GPS changed
    for place_id in current_ids & new_ids:
        curr = current[place_id]
        new = new_dila[place_id]
        
        try:
            curr_lat = float(curr.get('lat', 0))
            curr_lon = float(curr.get('lon', 0))
            new_lat = float(new.get('lat', 0))
            new_lon = float(new.get('lon', 0))
            
            distance = haversine_distance(curr_lat, curr_lon, new_lat, new_lon)
            
            if distance > GPS_THRESHOLD_METERS:
                change = {
                    "id": place_id,
                    "name": new.get('nameChinese', curr.get('nameChinese', 'Unknown')),
                    "old": {"lat": curr['lat'], "lon": curr['lon']},
                    "new": {"lat": new['lat'], "lon": new['lon']},
                    "distance_m": round(distance, 2),
                    "status": "pending"
                }
                results["summary"]["gps_changed"].append(change)
                results["details"].append(change)
        except (ValueError, TypeError):
            pass
    
    results["summary"]["unchanged"] = len(current_ids & new_ids) - len(results["summary"]["gps_changed"])
    
    # Save results
    os.makedirs(os.path.dirname(COMPARE_OUTPUT), exist_ok=True)
    with open(COMPARE_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Compare Results:")
    print(f"  New places: {len(results['summary']['new_places'])}")
    print(f"  Deleted: {len(results['summary']['deleted_places'])}")
    print(f"  GPS changed (>100m): {len(results['summary']['gps_changed'])}")
    print(f"  Unchanged: {results['summary']['unchanged']}")
    
    if results['summary']['gps_changed']:
        print(f"\n⚠️ ALERT: {len(results['summary']['gps_changed'])} places have GPS changes >{GPS_THRESHOLD_METERS}m")
        print(f"   Review at: {COMPARE_OUTPUT}")
    
    return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GPS Compare Tool')
    parser.add_argument('--download', action='store_true', help='Download latest DILA')
    parser.add_argument('--approve-all', action='store_true', help='Auto-approve all changes')
    
    args = parser.parse_args()
    
    if args.download:
        xml_path = download_dila()
        if xml_path:
            new_places = parse_dila_places(xml_path)
        else:
            print("❌ Cannot proceed without DILA data")
            return
    else:
        # Try to find existing DILA XML
        xml_files = [f for f in os.listdir(DILA_OUTPUT_DIR) if f.endswith('.xml')] if os.path.exists(DILA_OUTPUT_DIR) else []
        if xml_files:
            xml_path = os.path.join(DILA_OUTPUT_DIR, xml_files[0])
            new_places = parse_dila_places(xml_path)
        else:
            print("⚠️ No DILA data found. Run with --download to get latest.")
            return
    
    # Load current data
    current_places = load_current_places()
    
    # Compare
    results = compare_gps(current_places, new_places)
    
    if args.approve_all:
        print("\n⚠️ Auto-approve not implemented yet")
        # TODO: Implement auto-approve workflow

if __name__ == "__main__":
    main()