#!/usr/bin/env python3
"""
Wiki Buddhist Temple Crawler - Vietnamese Buddhist Temples
Crawls data from Vietnamese Buddhist Wiki and converts to DILA format.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
from urllib.parse import quote, urljoin
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWL_DIR = os.path.join(BASE_DIR, 'data', 'crawl')
os.makedirs(CRAWL_DIR, exist_ok=True)

# Wiki categories to crawl
# NOTE: ONLY Vietnamese Wikipedia (vi.wikipedia.org) - No English
CATEGORIES = {
    'chua': 'Chùa Việt Nam',
    'ton_dinh': 'Tổ đình Việt Nam', 
    'thien_vien': 'Thiền viện Việt Nam',
    'ni_tu': 'Ni viện Việt Nam',
    'hoc_vien': 'Học viện Phật giáo Việt Nam'
}

# Heritage patterns for detection
HERITAGE_PATTERNS = [
    ('UNESCO', re.compile(r'(unesco|di sản liên hợp|world heritage)', re.I)),
    ('Quốc Gia', re.compile(r'(quốc gia|đặc biệt|cấp quốc gia|di tích quốc gia|di tích lịch sử quốc gia)', re.I)),
    ('Tỉnh', re.compile(r'(cấp tỉnh|di tích tỉnh|di tích lịch sử cấp tỉnh)', re.I)),
    (' Huyện', re.compile(r'(cấp huyện)', re.I))
]

# Enhanced Auto-Labels (v2.3) - For Team VN Geographic Audit
ENHANCED_LABELS = [
    ('Tổ Đình', re.compile(r'(sắc phong tổ đình|tổ đình dòng|ngôi tổ đình)', re.I)),
    ('Di Tích', re.compile(r'(di tích (lịch sử|văn hóa) (cấp|xếp hạng) (quốc gia|tỉnh|thành phố)', re.I)),
    ('Cổ Tự', re.compile(r'(danh lam cổ tự|chùa cổ)', re.I))
]

# Label colors for UI display
LABEL_COLORS = {
    'Tổ Đình': {'color': '#ef4444', 'icon': '🔴'},
    'Di Tích': {'color': '#f97316', 'icon': '🟠'},
    'Cổ Tự': {'color': '#92400e', 'icon': '🟤'},
    'UNESCO': {'color': '#ffd700', 'icon': '🏆'},
    'Quốc Gia': {'color': '#f97316', 'icon': '🏛️'},
    'Tỉnh': {'color': '#3b82f6', 'icon': '📜'},
    'Tân Tự': {'color': '#6b7280', 'icon': '🏗️'}
}

# Province mapping
PROVINCE_MAP = {
    'TP. Hồ Chí Minh': ['VN-SG', 'TPHCM'],
    'Hà Nội': ['VN-HN', 'HN'],
    'Đà Nẵng': ['VN-DN', 'DN'],
    'Huế': ['VN-26', 'TTH'],
    'Nha Trang': ['VN-34', 'KH'],
    'Cần Thơ': ['VN-CT', 'CT'],
    'Hải Phòng': ['VN-HP', 'HP'],
    'Biên Hòa': ['VN-37', 'ĐN'],
    'Vũng Tàu': ['VN-43', 'BDA'],
}

def detect_heritage(text):
    """Detect heritage level from text"""
    if not text:
        return 'Tân Tự'
    for level, pattern in HERITAGE_PATTERNS:
        if pattern.search(text):
            return level
    return 'Tân Tự'

def detect_enhanced_labels(text):
    """Detect auto-labels for Team VN audit (v2.3)"""
    if not text:
        return []
    labels = []
    for label, pattern in ENHANCED_LABELS:
        if pattern.search(text):
            labels.append({
                'name': label,
                'color': LABEL_COLORS.get(label, {}).get('color', '#6b7280'),
                'icon': LABEL_COLORS.get(label, {}).get('icon', '🏷️')
            })
    return labels

def extract_year(text):
    """Extract founding year from text"""
    if not text:
        return None
    # Match patterns like "năm 1601", "1601", "năm Mùi 1599" (zodiac)
    year_patterns = [
        r'năm\s*(\d{3,4})',
        r'(\d{3,4})\s*(?:TCN|CN|TL)',
        r'(?:năm|dựng|thành lập|khởi công)\s*(?:Mùi|Tỵ|Sửu|Dần|Mão|Thìn|Tị|Ngọ|Mùi|Dậu|Canh|Tân|Nhâm|Quý)?\s*(\d{3,4})?'
    ]
    for pattern in year_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            year = match.group(1) if match.group(1) else match.group(2)
            if year and 1000 <= int(year) <= 2026:
                return int(year)
    return None

def extract_gps(text):
    """Extract GPS coordinates from text"""
    if not text:
        return None, None
    # Match decimal coordinates
    pattern = r'([\d.]+)[,\s]+([\d.]+)'
    match = re.search(pattern, text)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        if 8 <= lat <= 24 and 102 <= lon <= 110:
            return lat, lon
    return None, None

def get_province_code(province_name):
    """Get ISO 3166-2 province code"""
    for key, codes in PROVINCE_MAP.items():
        if key.lower() in province_name.lower():
            return codes[0]
    # Default - extract from first 2 chars of province
    if province_name:
        return f"VN-{province_name[:2].upper()[:2]}"
    return "VN-00"

def crawl_category(category, max_pages=5):
    """
    Crawl a category from Wiki
    
    NOTE: Only Vietnamese Wikipedia (vi.wikipedia.org) - No English pages.
    """
    results = []
    
    # Wiki categories for Vietnamese Buddhist temples
    # ONLY vi.wikipedia.org - Vietnamese language only
    category_urls = {
        'chua': 'https://vi.wikipedia.org/wiki/Danh_sách_Chùa_theo_Việt_Nam',
        'ton_dinh': 'https://vi.wikipedia.org/wiki/Danh_sách_Chùa_Tổ_đình_tại_Việt_Nam',
        'thien_vien': 'https://vi.wikipedia.org/wiki/Thiền_viện',
        'ni_tu': 'https://vi.wikipedia.org/wiki/Danh_sách_Ni_viện',
    }
    
    url = category_urls.get(category)
    if not url:
        print(f"[Crawler] Unknown category: {category}")
        return results
    
    try:
        print(f"[Crawler] Crawling {category}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all temple items in the page
        # Look for links to temple articles
        links = soup.find_all('a', href=re.compile(r'/wiki/Chùa_'))
        
        print(f"[Crawler] Found {len(links)} links in {category}")
        
        for i, link in enumerate(links[:max_pages * 10]):
            try:
                href = link.get('href')
                if not href:
                    continue
                    
                full_url = urljoin('https://vi.wikipedia.org', href)
                temple_data = crawl_temple_page(full_url)
                
                if temple_data:
                    temple_data['category'] = category
                    temple_data['source'] = 'wiki'
                    temple_data['crawl_date'] = datetime.now().isoformat()
                    results.append(temple_data)
                    
                if (i + 1) % 10 == 0:
                    print(f"[Crawler] Processed {i+1} temples...")
                    
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"[Crawler] Error processing link {i}: {e}")
                continue
                
    except Exception as e:
        print(f"[Crawler] Error crawling {category}: {e}")
    
    return results

def crawl_temple_page(url):
    """Crawl individual temple page"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title_elem = soup.find('h1', {'id': 'firstHeading'})
        name_vi = title_elem.text.strip() if title_elem else ''
        
        if not name_vi or 'Chùa' not in name_vi:
            return None
        
        # Extract info box (infobox)
        infobox = soup.find('table', {'class': 'infobox'})
        
        data = {
            'name_vi': name_vi,
            'source_url': url,
            'wiki_full': '',
            'stardict_full': '',
            'heritage_status': 'Tân Tự',
            'founding_year': None,
            'province': '',
            'lat': None,
            'lon': None,
            'gmaps_address': '',
            'monks': [],
            'lineage': ''
        }
        
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                header = row.find('th')
                value = row.find('td')
                if not header or not value:
                    continue
                    
                header_text = header.get_text(strip=True)
                value_text = value.get_text(strip=True, separator=' ')
                
                # Map fields
                if 'Tỉnh' in header_text or 'Thành phố' in header_text:
                    data['province'] = value_text
                elif 'Vĩ độ' in header_text or 'Kinh độ' in header_text:
                    lat, lon = extract_gps(value_text)
                    data['lat'] = lat
                    data['lon'] = lon
                elif 'Năm thành lập' in header_text or 'Xây dựng' in header_text:
                    data['founding_year'] = extract_year(value_text)
                elif 'Thể loại' in header_text or 'Phong cách' in header_text:
                    data['heritage_status'] = detect_heritage(value_text)
        
        # Get main content for full text
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if content_div:
            # Get paragraphs
            paragraphs = content_div.find_all('p', limit=5)
            full_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            data['wiki_full'] = full_text[:2000]  # Limit to 2000 chars
            data['stardict_full'] = full_text[:2000]
        
        # Detect enhanced labels (v2.3)
        data['auto_labels'] = detect_enhanced_labels(data['wiki_full'])
        
        # If no enhanced labels, use heritage as primary label
        if not data['auto_labels']:
            data['auto_labels'] = [{
                'name': data['heritage_status'],
                'color': LABEL_COLORS.get(data['heritage_status'], {}).get('color', '#6b7280'),
                'icon': LABEL_COLORS.get(data['heritage_status'], {}).get('icon', '🏷️')
            }]
        
        # Detect heritage from text
        data['heritage_status'] = detect_heritage(data['wiki_full'])
        
        # Generate place ID
        province_code = get_province_code(data['province'])
        data['place_id'] = f"pth:{province_code}_{name_vi[:20].replace(' ','_')}"
        
        print(f"[Crawler] {name_vi} - {data.get('heritage_status', 'Tân Tự')}")
        
        return data
        
    except Exception as e:
        print(f"[Crawler] Error crawling {url}: {e}")
        return None

def convert_to_dila_format(temple_data):
    """Convert to DILA-compatible format"""
    return {
        # Basic ID
        'id': temple_data.get('place_id', ''),
        'dila_id': '',
        
        # Names
        'nameVietnamese': temple_data.get('name_vi', ''),
        'nameChinese': temple_data.get('name_zh', ''),
        'namePinyin': '',
        
        # Location
        'country': 'Vietnam',
        'province': temple_data.get('province', ''),
        'district': '',
        'lat': temple_data.get('lat'),
        'lon': temple_data.get('lon'),
        
        # GPS Address
        'gmaps_address': temple_data.get('gmaps_address', ''),
        
        # Time
        'foundingYear': temple_data.get('founding_year'),
        'heritage_status': temple_data.get('heritage_status', 'Tân Tự'),
        
        # Source
        'source': 'wiki',
        'source_url': temple_data.get('source_url', ''),
        
        # Full text
        'stardict_full': temple_data.get('stardict_full', ''),
        'wiki_full': temple_data.get('wiki_full', ''),
        
        # Lineage
        'monks': temple_data.get('monks', []),
        'lineage': temple_data.get('lineage', ''),
        
        # Metadata
        'category': temple_data.get('category', 'chua'),
        'crawl_date': temple_data.get('crawl_date', '')
    }

def main():
    """Main crawl function"""
    print("=" * 60)
    print("Wiki Buddhist Temple Crawler v1.0")
    print("=" * 60)
    
    all_results = []
    
    # Crawl each category
    for category in ['chua', 'ton_dinh']:
        print(f"\n[Crawler] Starting {category}...")
        temples = crawl_category(category, max_pages=3)
        all_results.extend(temples)
        
        # Convert to DILA format
        dila_results = [convert_to_dila_format(t) for t in temples]
        
        # Save to file
        output_file = os.path.join(CRAWL_DIR, f'{category}_wiki_{datetime.now().strftime("%Y%m%d")}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dila_results, f, ensure_ascii=False, indent=2)
        
        print(f"[Crawler] Saved {len(dila_results)} temples to {output_file}")
    
    # Save all results
    all_output = os.path.join(CRAWL_DIR, f'all_temples_{datetime.now().strftime("%Y%m%d")}.json')
    with open(all_output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("CRAWL SUMMARY")
    print("=" * 60)
    print(f"Total temples: {len(all_results)}")
    
    heritage_counts = {}
    for t in all_results:
        level = t.get('heritage_status', 'Tân Tự')
        heritage_counts[level] = heritage_counts.get(level, 0) + 1
    
    print("\nHeritage Level Distribution:")
    for level, count in sorted(heritage_counts.items(), key=lambda x: -x[1]):
        print(f"  {level}: {count}")
    
    print(f"\nOutput: {all_output}")
    print("=" * 60)

if __name__ == '__main__':
    main()