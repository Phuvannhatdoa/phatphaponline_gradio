#!/usr/bin/env python3
"""
Fuzzy Matching Engine: TTL → StarDict → DILA (Optimized)
Purpose: Match OLD TTL names with DILA IDs via StarDict bridge

Usage: python fuzzy_matcher.py
"""

import json
import os
import re
from pathlib import Path
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
OLD_TTL_DIR = BASE_DIR / "data" / "ttl" / "old"
STAR_DICT_FILE = BASE_DIR / "data" / "dict" / "merged.json"
DILA_PERSON_FILE = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_person" / "Buddhist_Studies_Person_Authority.xml"
OUTPUT_FILE = BASE_DIR / "data" / "indexed" / "fuzzy_matches.json"


def remove_diacritics(text):
    if not text:
        return ""
    replacements = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
    }
    result = []
    for c in text.lower():
        result.append(replacements.get(c, c))
    return ''.join(result)


def fuzzy_ratio(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, remove_diacritics(a), remove_diacritics(b)).ratio()


def parse_ttl_names(ttl_content):
    """Extract all names from TTL file"""
    names = {'vi': [], 'zh': [], 'ja': [], 'en': [], 'all': []}
    
    label_pattern = r'rdfs:label\s+"([^"]+)"@(\w+)'
    for match in re.finditer(label_pattern, ttl_content):
        name = match.group(1).strip()
        lang = match.group(2).strip()
        
        if lang == 'vi':
            names['vi'].append(name)
        elif lang == 'zh':
            names['zh'].append(name)
        elif lang == 'ja':
            names['ja'].append(name)
        elif lang == 'en':
            names['en'].append(name)
        
        names['all'].append({'name': name, 'lang': lang})
    
    return names


def build_dila_index():
    """Build optimized DILA index for fast lookup"""
    print("📋 Building DILA index (optimized)...")
    
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    tree = ET.parse(DILA_PERSON_FILE)
    root = tree.getroot()
    
    persons = root.findall('.//tei:person', ns)
    
    # Index by: exact_zh, fuzzy_zh_lookup
    exact_zh = {}
    fuzzy_zh_lookup = {}  # first char -> [(name, id), ...]
    
    for person in persons[:10000]:  # Limit for speed - first 10K
        person_id = person.get('{http://www.w3.org/XML/1998/namespace}id')
        if not person_id:
            continue
        
        for persName in person.findall('tei:persName', ns):
            lang = persName.get('{http://www.w3.org/XML/1998/namespace}lang', '')
            if persName.text:
                name = persName.text.strip()
                
                if 'zho' in lang or 'zh' in lang:
                    # Exact index
                    if name not in exact_zh:
                        exact_zh[name] = person_id
                    
                    # Fuzzy index - first char
                    if name and len(name) >= 2:
                        first_char = name[0]
                        if first_char not in fuzzy_zh_lookup:
                            fuzzy_zh_lookup[first_char] = []
                        fuzzy_zh_lookup[first_char].append((name, person_id))
    
    print(f"   Indexed {len(exact_zh)} exact + {len(fuzzy_zh_lookup)} fuzzy entries")
    return exact_zh, fuzzy_zh_lookup


def match_ttl_to_dila(ttl_names, exact_zh, fuzzy_zh_lookup):
    """Match TTL names with DILA using index"""
    matches = []
    
    for ttl_name in ttl_names.get('all', []):
        name = ttl_name['name']
        
        # Try exact match first
        if name in exact_zh:
            return {
                'dila_id': exact_zh[name],
                'confidence': 100,
                'method': 'exact_zh',
                'ttl_name': name
            }
        
        # Try fuzzy match
        if name and len(name) >= 2:
            first_char = name[0]
            candidates = fuzzy_zh_lookup.get(first_char, [])
            
            best_score = 0
            best_id = None
            
            for cand_name, dila_id in candidates[:50]:  # Limit candidates
                score = fuzzy_ratio(name, cand_name)
                if score > best_score and score > 0.85:
                    best_score = score
                    best_id = dila_id
            
            if best_id:
                return {
                    'dila_id': best_id,
                    'confidence': int(best_score * 100),
                    'method': 'fuzzy_zh',
                    'ttl_name': name
                }
    
    return None


def process_old_ttls():
    """Process all OLD TTL files"""
    print("=" * 60)
    print("🔍 FUZZY MATCHING: TTL → DILA (Optimized)")
    print("=" * 60)
    
    # Build DILA index
    exact_zh, fuzzy_zh_lookup = build_dila_index()
    
    # Get list of OLD TTL files
    ttl_files = list(OLD_TTL_DIR.glob("*.ttl"))
    print(f"\n📁 Found {len(ttl_files)} OLD TTL files")
    
    results = []
    
    for ttl_file in ttl_files:
        print(f"\n🔄 Processing: {ttl_file.name}")
        
        with open(ttl_file, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
        
        ttl_names = parse_ttl_names(ttl_content)
        print(f"   Names: vi={len(ttl_names['vi'])}, zh={len(ttl_names['zh'])}")
        
        match = match_ttl_to_dila(ttl_names, exact_zh, fuzzy_zh_lookup)
        
        if match:
            print(f"   ✅ Match: DILA {match['dila_id']} ({match['confidence']}%)")
            results.append({
                'filename': ttl_file.name,
                'dila_id': match['dila_id'],
                'confidence': match['confidence'],
                'method': match['method'],
                'names': ttl_names,
                'status': 'matched'
            })
        else:
            print(f"   ❌ No match")
            results.append({
                'filename': ttl_file.name,
                'dila_id': None,
                'confidence': 0,
                'method': None,
                'names': ttl_names,
                'status': 'unmatched'
            })
    
    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved to {OUTPUT_FILE}")
    
    matched = sum(1 for r in results if r['status'] == 'matched')
    print(f"\n📊 Summary: {matched}/{len(results)} matched")


if __name__ == "__main__":
    process_old_ttls()