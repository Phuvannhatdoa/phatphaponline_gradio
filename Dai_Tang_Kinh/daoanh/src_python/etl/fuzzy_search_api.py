#!/usr/bin/env python3
"""
Fuzzy Search API
Sử dụng rapidfuzz để tìm kiếm gợi ý từ dictionary
"""

import sqlite3
import json
from pathlib import Path
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("⚠️ rapidfuzz not available, using difflib fallback")

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
CACHE_FILE = BASE_DIR / "data" / "indexed" / "fuzzy_cache.json"


def remove_accents(s):
    """Remove Vietnamese accents"""
    if not s:
        return ""
    import unicodedata
    nfd = unicodedata.normalize('NFD', s)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def load_lexicon_cache():
    """Load lexicon vào memory cache"""
    if CACHE_FILE.exists():
        print("📂 Loading fuzzy cache...")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print("📂 Building fuzzy cache from SQLite...")
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, normalized, entity_type, source, priority
        FROM lexicon
        WHERE term IS NOT NULL AND term != ''
        ORDER BY priority, term
    """)
    rows = cursor.fetchall()
    
    cache = {
        'terms': [],
        'by_normalized': {},
        'by_entity': {'ĐỊA DANH': [], 'TU SĨ': [], 'OTHER': []}
    }
    
    for term, normalized, etype, source, priority in rows:
        entry = {
            'term': term,
            'normalized': normalized or remove_accents(term),
            'entity_type': etype or 'OTHER',
            'source': source,
            'priority': priority
        }
        cache['terms'].append(entry)
        
        norm_key = normalized or remove_accents(term)
        if norm_key not in cache['by_normalized']:
            cache['by_normalized'][norm_key] = []
        cache['by_normalized'][norm_key].append(entry)
        
        entity_bucket = etype if etype in ['ĐỊA DANH', 'TU SĨ'] else 'OTHER'
        cache['by_entity'][entity_bucket].append(entry)
    
    conn.close()
    
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    
    print(f"   ✅ Loaded {len(cache['terms'])} terms")
    return cache


def find_best_match(query, entity_type=None, top_n=5, threshold=60):
    """
    Tìm best match sử dụng rapidfuzz
    
    Args:
        query: Input từ user/admin
        entity_type: Lọc theo entity type (ĐỊA DANH, TU SĨ, hoặc None)
        top_n: Số lượng kết quả trả về
        threshold: Ngưỡng match tối thiểu (0-100)
    
    Returns:
        List of matches với score
    """
    if not query:
        return []
    
    cache = load_lexicon_cache()
    
    query_norm = remove_accents(query).lower()
    candidates = cache['terms']
    
    if entity_type and entity_type in cache['by_entity']:
        candidates = cache['by_entity'][entity_type]
    
    results = []
    
    if RAPIDFUZZ_AVAILABLE:
        terms = [c['term'] for c in candidates]
        matches = process.extract(
            query,
            terms,
            limit=top_n,
            scorer=fuzz.WRatio
        )
        
        for match, score, _ in matches:
            if score >= threshold:
                entry = next(c for c in candidates if c['term'] == match)
                results.append({
                    'term': match,
                    'normalized': entry['normalized'],
                    'entity_type': entry['entity_type'],
                    'source': entry['source'],
                    'priority': entry['priority'],
                    'score': round(score, 1)
                })
    else:
        for entry in candidates:
            ratio = SequenceMatcher(None, query_norm, entry['normalized'].lower()).ratio() * 100
            if ratio >= threshold:
                results.append({
                    'term': entry['term'],
                    'normalized': entry['normalized'],
                    'entity_type': entry['entity_type'],
                    'source': entry['source'],
                    'priority': entry['priority'],
                    'score': round(ratio, 1)
                })
        
        results.sort(key=lambda x: (-x['score'], x['priority']))
        results = results[:top_n]
    
    return results


def search_by_entity(query, entity_type, top_n=3):
    """Tìm kiếm theo entity type cụ thể"""
    return find_best_match(query, entity_type=entity_type, top_n=top_n)


def get_suggestions(query, mode='auto'):
    """
    API chính cho admin interface
    
    Args:
        query: Input từ admin
        mode: 'auto' (tất cả), 'place' (ĐỊA DANH), 'monk' (TU SĨ)
    
    Returns:
        JSON response với suggestions
    """
    if mode == 'place':
        results = find_best_match(query, entity_type='ĐỊA DANH', top_n=5)
    elif mode == 'monk':
        results = find_best_match(query, entity_type='TU SĨ', top_n=5)
    else:
        results = find_best_match(query, top_n=5)
    
    return {
        'query': query,
        'mode': mode,
        'results': results,
        'count': len(results)
    }


def init_fuzzy_api():
    """Initialize API - build cache"""
    cache = load_lexicon_cache()
    return {
        'status': 'ready',
        'total_terms': len(cache['terms']),
        'entity_counts': {
            'ĐỊA DANH': len(cache['by_entity']['ĐỊA DANH']),
            'TU SĨ': len(cache['by_entity']['TU SĨ']),
            'OTHER': len(cache['by_entity']['OTHER'])
        }
    }


if __name__ == "__main__":
    print("🚀 Fuzzy Search API")
    print("=" * 40)
    
    status = init_fuzzy_api()
    print(f"\n✅ API Ready")
    print(f"   Total terms: {status['total_terms']}")
    print(f"   ĐỊA DANH: {status['entity_counts']['ĐỊA DANH']}")
    print(f"   TU SĨ: {status['entity_counts']['TU SĨ']}")
    
    test_queries = [
        ('Quảng Đức', 'monk'),
        ('Chùa Thiếu', 'place'),
    ]
    
    print("\n🧪 Test queries:")
    for query, mode in test_queries:
        result = get_suggestions(query, mode=mode)
        print(f"\n   Query: {query} (mode={mode})")
        for r in result['results'][:3]:
            print(f"      → {r['term']} ({r['score']}%)")


_CACHE = None

def get_cache():
    """Get cached lexicon (singleton)"""
    global _CACHE
    if _CACHE is None:
        _CACHE = load_lexicon_cache()
    return _CACHE


class FuzzySearchAPI:
    """Flask API wrapper"""
    
    def __init__(self):
        pass
    
    def init_app(self, app):
        """Init với Flask app"""
        self.cache = load_lexicon_cache()
        
        @app.route('/api/fuzzy/search')
        def fuzzy_search():
            from flask import request
            query = request.args.get('q', '')
            mode = request.args.get('mode', 'auto')
            return json.dumps(get_suggestions(query, mode))
        
        @app.route('/api/fuzzy/status')
        def fuzzy_status():
            return json.dumps(status)
        
        print("✅ Fuzzy Search API registered")