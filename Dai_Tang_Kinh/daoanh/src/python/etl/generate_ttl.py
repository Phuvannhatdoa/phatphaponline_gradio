#!/usr/bin/env python3
"""
Generate TTL from DILA data
Usage: python generate_ttl.py
"""

import json
import os
import xml.etree.ElementTree as ET

# Configuration
DILA_XML = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dila_temp/Buddhist_Studies_Place_Authority.xml"
OUTPUT_TTL = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/ontology/dila_places.ttl"

PREFIX = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .
@prefix schema: <http://schema.org/> .
@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix dila: <http://www.dila.edu.tw/rdf/entity/> .
@prefix cb: <http://www.cbeta.org/rdf/entity/> .

"""

def generate_ttl():
    """Generate TTL file from DILA XML"""
    print("📝 Generating TTL from DILA XML...")
    
    ttl_lines = [PREFIX]
    ttl_lines.append("# Buddhist Places from DILA Authority")
    ttl_lines.append(f"# Generated: 2026-04-01")
    ttl_lines.append("")
    
    try:
        tree = ET.parse(DILA_XML)
        root = tree.getroot()
        
        # Extract namespace properly
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0].strip('{')
        
        print(f"   Using namespace: {ns}")
        
        count = 0
        for place in root.findall(f'.//{{{ns}}}place'):
            place_id = place.get('{http://www.w3.org/XML/1998/namespace}id')
            
            if not place_id:
                continue
            
            # Get all names
            names = {}
            for name_elem in place.findall(f'.//{{{ns}}}placeName'):
                lang = name_elem.get('{http://www.w3.org/XML/1998/namespace}lang', '')
                text = name_elem.text or ""
                if text:
                    if lang == 'zho-Hant':
                        names['zh'] = text
                    elif lang == 'eng-Latn':
                        names['en'] = text
                    elif lang == 'jpn':
                        names['ja'] = text
                    elif lang not in names:
                        names['other'] = text
            
            # Get GPS
            lat = ""
            lon = ""
            geo_elem = place.find(f'.//{{{ns}}}geo')
            if geo_elem is not None and geo_elem.text:
                geo_text = geo_elem.text.strip().split()
                if len(geo_text) >= 2:
                    lon = geo_text[0]
                    lat = geo_text[1]
            
            # Get district/country
            district = ""
            country = ""
            district_elem = place.find(f'.//{{{ns}}}district')
            if district_elem is not None and district_elem.text:
                district = district_elem.text
                if '-' in district:
                    parts = district.split('-')
                    country = parts[0]
            
            # Get note/description - skip for now due to special chars
            desc = ""
            
            # Only include places with GPS
            if lat and lon:
                ttl_lines.append(f"bkg:place_{place_id} a bkg:BuddhistPlace ;")
                ttl_lines.append(f"    bkg:dilaId \"{place_id}\" ;")
                
                if 'zh' in names:
                    ttl_lines.append(f'    bkg:nameChinese "{names["zh"]}" ;')
                if 'en' in names:
                    ttl_lines.append(f'    bkg:nameEnglish "{names["en"]}" ;')
                if 'ja' in names:
                    ttl_lines.append(f'    bkg:nameJapanese "{names["ja"]}" ;')
                
                ttl_lines.append(f'    geo:lat "{lat}" ;')
                ttl_lines.append(f'    geo:long "{lon}" ;')
                
                if country:
                    ttl_lines.append(f'    bkg:countryCode "{country}" ;')
                if district:
                    ttl_lines.append(f'    bkg:district "{district}" ;')
                
                ttl_lines.append(f'    bkg:source "DILA" .')
                ttl_lines.append("")
                
                count += 1
                
                # Progress
                if count % 5000 == 0:
                    print(f"   Processed {count} places...")
                    
                # Limit for demo (full file would be too large)
                if count >= 5000:
                    print(f"   Limited to 5000 places (full: 58,480)")
                    break
        
        # Write to file
        os.makedirs(os.path.dirname(OUTPUT_TTL), exist_ok=True)
        with open(OUTPUT_TTL, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ttl_lines))
        
        print(f"✅ Generated TTL with {count} places")
        print(f"   Output: {OUTPUT_TTL}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_ttl()