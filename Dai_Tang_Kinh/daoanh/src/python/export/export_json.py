#!/usr/bin/env python3
"""
Export places from GraphDB to JSON file
Usage: python export_json.py
"""

import json
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

# Configuration
GRAPHDB_URL = "http://158.220.106.183:7200/repositories/Dao_Anh"
OUTPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places.json"

# Prefix definitions
PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX schema: <http://schema.org/>
PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
PREFIX dila: <http://www.dila.edu.tw/rdf/entity/>
PREFIX cbeta: <http://www.cbeta.org/rdf/entity/>
"""

def export_places():
    """Export all places from GraphDB to JSON"""
    
    print("📤 Exporting places from GraphDB...")
    
    sparql = SPARQLWrapper(GRAPHDB_URL)
    
    query = PREFIXES + """
    SELECT ?id ?nameZh ?nameVi ?nameEn ?lat ?lon ?country ?province ?desc ?source ?referencedIn
    WHERE {
        ?s a bkg:BuddhistPlace .
        OPTIONAL { ?s bkg:cbetaId ?id }
        OPTIONAL { ?s bkg:nameChinese ?nameZh }
        OPTIONAL { ?s bkg:nameVietnamese ?nameVi }
        OPTIONAL { ?s bkg:nameEnglish ?nameEn }
        OPTIONAL { ?s geo:lat ?lat }
        OPTIONAL { ?s geo:long ?lon }
        OPTIONAL { ?s bkg:countryCode ?country }
        OPTIONAL { ?s bkg:province ?province }
        OPTIONAL { ?s schema:description ?desc }
        OPTIONAL { ?s bkg:source ?source }
        OPTIONAL { ?s bkg:referencedIn ?ref }
    }
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        
        # Process results
        places = []
        place_map = {}
        
        for binding in results.get("results", {}).get("bindings", []):
            place_id = binding.get("id", {}).get("value", "")
            
            if not place_id:
                continue
                
            if place_id not in place_map:
                place_map[place_id] = {
                    "id": place_id,
                    "nameChinese": "",
                    "nameVietnamese": "",
                    "nameEnglish": "",
                    "lat": "",
                    "lon": "",
                    "country": "",
                    "province": "",
                    "description": "",
                    "source": "DILA",
                    "referencedIn": []
                }
            
            # Update fields
            place = place_map[place_id]
            
            if "nameZh" in binding and not place["nameChinese"]:
                place["nameChinese"] = binding["nameZh"]["value"]
            if "nameVi" in binding and not place["nameVietnamese"]:
                place["nameVietnamese"] = binding["nameVi"]["value"]
            if "nameEn" in binding and not place["nameEnglish"]:
                place["nameEnglish"] = binding["nameEn"]["value"]
            if "lat" in binding and not place["lat"]:
                place["lat"] = binding["lat"]["value"]
            if "lon" in binding and not place["lon"]:
                place["lon"] = binding["lon"]["value"]
            if "country" in binding and not place["country"]:
                place["country"] = binding["country"]["value"]
            if "province" in binding and not place["province"]:
                place["province"] = binding["province"]["value"]
            if "desc" in binding and not place["description"]:
                place["description"] = binding["desc"]["value"]
            if "source" in binding and not place["source"]:
                place["source"] = binding["source"]["value"]
                
            # Collect referencedIn
            if "ref" in binding:
                ref = binding["ref"]["value"]
                if ref not in place["referencedIn"]:
                    place["referencedIn"].append(ref)
        
        places = list(place_map.values())
        
        # Save to JSON
        output = {"places": places, "count": len(places)}
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {len(places)} places to {OUTPUT_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    export_places()