#!/usr/bin/env python3
"""
Import CBETA places via API
Search CBETA for place names in Buddhist texts
"""

import requests
import json
import time
import re

CBETA_API = "https://cbdata.dila.edu.tw/stable/search"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places_cbeta.json"

# Common Buddhist place names to search
PLACE_KEYWORDS = [
    # Indian places
    "印度", "王舍城", "竹林精舍", "祇園精舍", "鹿野苑", "靈山", "伽耶", "菩提場",
    "舍衛國", "羅閱國", "迦毘羅衛", "兜率天", "忉利天", "梵天",
    # Chinese places
    "洛陽", "長安", "杭州", "蘇州", "福州", "泉州", "廣州", "南京", "北京",
    "五台山", "峨眉山", "普陀山", "九華山", "天台山", "廬山", "嵩山", "少室山",
    "金山寺", "靈隱寺", "法門寺", "大慈寺", "大明寺", "南禪寺", "臨濟寺",
    # Vietnamese places
    "順化", "河內", "胡志明", "峴港", "會安", "芽莊", "大勒",
    "美湻", "富國", "歸仁", "平定", "清化", "河靜", "義安", "平順",
    # General
    "佛寺", "伽藍", "精舍", "道場", "禪寺", "律寺", "叢林",
]

def search_cbeta(query):
    """Search CBETA API"""
    try:
        params = {"q": query, "limit": 50}
        r = requests.get(CBETA_API, params=params, timeout=30)
        data = r.json()
        return data.get('results', [])
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def extract_places():
    """Extract unique places from CBETA"""
    print("🔍 Searching CBETA API for Buddhist places...")
    
    all_places = {}
    seen_ids = set()
    
    for keyword in PLACE_KEYWORDS:
        print(f"   Searching: {keyword}")
        results = search_cbeta(keyword)
        
        for r in results:
            # Extract place mentions from title/byline
            title = r.get('title', '')
            byline = r.get('byline', '')
            
            # Simple extraction - just add the keyword if found
            if keyword in title or keyword in byline:
                place_id = f"CBETA_{keyword}"
                if place_id not in seen_ids:
                    seen_ids.add(place_id)
                    all_places[place_id] = {
                        'id': place_id,
                        'nameChinese': keyword,
                        'nameVietnamese': '',  # Will convert later
                        'source': 'CBETA',
                        'referenced_in': []
                    }
                
                if 'work' in r:
                    all_places[place_id]['referenced_in'].append(r['work'])
        
        time.sleep(0.5)  # Rate limit
    
    print(f"✅ Found {len(all_places)} unique place mentions")
    
    # Save JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': list(all_places.values()), 'count': len(all_places)}, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    extract_places()
