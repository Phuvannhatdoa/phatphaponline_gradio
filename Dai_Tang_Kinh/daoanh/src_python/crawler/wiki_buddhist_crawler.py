#!/usr/bin/env python3
"""
Wiki Buddhist Crawler - Fetches Buddhist temple data from Wikipedia
Usage: python wiki_buddhist_crawler.py
"""

import os
import json
import requests
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'crawl', 'wiki_temples.json')

# Vietnamese Buddhist temple categories to crawl
CATEGORIES = [
    'Danh sách chùa Việt Nam',
    'Chùa Việt Nam',
    'Danh sách chùa theo tỉnh thành Việt Nam'
]

def crawl_wikipedia(category, limit=50):
    """Crawl Wikipedia for Buddhist temples"""
    url = f"https://vi.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'categorymembers',
        'cmtitle': f'Category:{category}',
        'cmlimit': limit,
        'cmtype': 'page'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        pages = data.get('query', {}).get('categorymembers', [])
        return [{'title': p['title'], 'pageid': p['pageid']} for p in pages]
    except Exception as e:
        print(f"Error crawling {category}: {e}")
        return []

def main():
    """Main crawler function"""
    print("🚀 Wiki Buddhist Crawler")
    print(f"Started: {datetime.now().isoformat()}")
    
    all_temples = []
    
    for category in CATEGORIES:
        print(f"📥 Crawling: {category}")
        temples = crawl_wikipedia(category)
        all_temples.extend(temples)
        print(f"   Found: {len(temples)} pages")
    
    # Save to output
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({'temples': all_temples, 'count': len(all_temples)}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Complete: {len(all_temples)} temples saved to {OUTPUT_FILE}")
    return len(all_temples)

if __name__ == '__main__':
    main()

# END