#!/usr/bin/env python3
"""
A1: Spiritual Geocoder API
Extract places mentioned in CBETA sutras and map to GPS coordinates
"""

from flask import Flask, jsonify, request
import json
import re
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# CBETA Sutra place patterns (expanded - 50+ sacred sites)
SUTRA_PLACE_PATTERNS = {
    # India (ancient Buddhist sites) - 20 sites
    '王舍城': {'lat': 25.0300, 'lon': 85.4436, 'region': 'India', 'name': 'Rājagṛha'},
    '靈鷲山': {'lat': 25.0283, 'lon': 85.4367, 'region': 'India', 'name': 'Gridhrakūṭa'},
    '舍衛國': {'lat': 27.3097, 'lon': 83.9850, 'region': 'India', 'name': 'Śrāvastī'},
    '祇樹給孤獨園': {'lat': 27.3097, 'lon': 83.9850, 'region': 'India', 'name': 'Jetavana'},
    '拘薩羅': {'lat': 27.3097, 'lon': 83.9850, 'region': 'India', 'name': 'Kosala'},
    '迦毘羅衛': {'lat': 27.4369, 'lon': 85.9842, 'region': 'India', 'name': 'Kapilavastu'},
    '鹿野苑': {'lat': 25.1389, 'lon': 83.0261, 'region': 'India', 'name': 'Mṛgadāva'},
    '波羅奈': {'lat': 25.1389, 'lon': 83.0261, 'region': 'India', 'name': 'Bārāṇasī'},
    '毘舍離': {'lat': 26.0000, 'lon': 85.5000, 'region': 'India', 'name': 'Vaiśālī'},
    '拘尸那': {'lat': 27.1939, 'lon': 83.8864, 'region': 'India', 'name': 'Kuśinagar'},
    '娑羅雙樹': {'lat': 27.1939, 'lon': 83.8864, 'region': 'India', 'name': 'Śāla grove'},
    '拘薩羅國': {'lat': 27.3097, 'lon': 83.9850, 'region': 'India', 'name': 'Kosala Kingdom'},
    '摩竭陀國': {'lat': 25.0300, 'lon': 85.4436, 'region': 'India', 'name': 'Magadha'},
    '僧伽施': {'lat': 28.4158, 'lon': 77.6101, 'region': 'India', 'name': 'Sankassa'},
    '沙羅雙樹': {'lat': 27.1939, 'lon': 83.8864, 'region': 'India', 'name': 'Sal grove'},
    '竹林精舍': {'lat': 25.0300, 'lon': 85.4436, 'region': 'India', 'name': 'Veluvana'},
    '祇園': {'lat': 27.3097, 'lon': 83.9850, 'region': 'India', 'name': 'Jetavana'},
    '阿耨達池': {'lat': 34.8333, 'lon': 76.2333, 'region': 'India', 'name': 'Lake Anavatapta'},
    '香雪山': {'lat': 25.0283, 'lon': 85.4367, 'region': 'India', 'name': 'Gandhamādana'},
    '廣嚴城': {'lat': 25.0283, 'lon': 85.4367, 'region': 'India', 'name': 'Vejayanta'},
    
    # China - 20 sites
    '洛陽': {'lat': 34.6237, 'lon': 112.4540, 'region': 'China', 'name': 'Luoyang'},
    '長安': {'lat': 34.3416, 'lon': 108.9398, 'region': 'China', 'name': "Chang'an"},
    '大理': {'lat': 25.6065, 'lon': 100.2679, 'region': 'China', 'name': 'Dali'},
    '台山': {'lat': 38.9784, 'lon': 112.5321, 'region': 'China', 'name': 'Mount Tai'},
    '峨眉山': {'lat': 29.5526, 'lon': 103.4858, 'region': 'China', 'name': 'Mount Emei'},
    '普陀山': {'lat': 30.0107, 'lon': 122.3921, 'region': 'China', 'name': 'Mount Putuo'},
    '五台山': {'lat': 39.1855, 'lon': 113.5657, 'region': 'China', 'name': 'Mount Wutai'},
    '金山': {'lat': 32.1290, 'lon': 118.9585, 'region': 'China', 'name': 'Mount Jin'},
    '廬山': {'lat': 29.4500, 'lon': 115.9500, 'region': 'China', 'name': 'Mount Lu'},
    '衡山': {'lat': 27.3000, 'lon': 112.9500, 'region': 'China', 'name': 'Mount Heng'},
    '華山': {'lat': 34.0500, 'lon': 110.0833, 'region': 'China', 'name': 'Mount Hua'},
    '嵩山': {'lat': 34.4500, 'lon': 113.0500, 'region': 'China', 'name': 'Mount Song'},
    '終南山': {'lat': 34.0500, 'lon': 109.9833, 'region': 'China', 'name': 'Zhongnan Mountain'},
    '南嶽': {'lat': 27.3000, 'lon': 112.9500, 'region': 'China', 'name': 'Southern Mountain'},
    '北嶽': {'lat': 40.0167, 'lon': 115.7000, 'region': 'China', 'name': 'Northern Mountain'},
    '慧日山': {'lat': 34.4500, 'lon': 113.0500, 'region': 'China', 'name': 'Mount Huiri'},
    '香嚴山': {'lat': 34.4500, 'lon': 113.0500, 'region': 'China', 'name': 'Mount Xiangyan'},
    '清涼山': {'lat': 39.1855, 'lon': 113.5657, 'region': 'China', 'name': 'Qingliang Mountain'},
    '靈隱山': {'lat': 30.2397, 'lon': 120.1417, 'region': 'China', 'name': 'Lingyin Mountain'},
    '天台山': {'lat': 29.2500, 'lon': 121.0667, 'region': 'China', 'name': 'Mount Tiantai'},
    
    # Vietnam - 15 sites
    '順化': {'lat': 16.0623, 'lon': 107.5906, 'region': 'Vietnam', 'name': 'Huế'},
    '河內': {'lat': 21.0285, 'lon': 105.8342, 'region': 'Vietnam', 'name': 'Hà Nội'},
    '西湖': {'lat': 21.0635, 'lon': 105.8230, 'region': 'Vietnam', 'name': 'Hồ Tây'},
    '金龍': {'lat': 21.0285, 'lon': 105.8342, 'region': 'Vietnam', 'name': 'Kim Long'},
    '的一天': {'lat': 21.0285, 'lon': 105.8342, 'region': 'Vietnam', 'name': 'Nhất Thiên'},
    '香嚴': {'lat': 16.0623, 'lon': 107.5906, 'region': 'Vietnam', 'name': 'Hương Nhàn'},
    '竹林': {'lat': 21.0285, 'lon': 105.8342, 'region': 'Vietnam', 'name': 'Trúc Lâm'},
    '仙山': {'lat': 22.4922, 'lon': 103.9783, 'region': 'Vietnam', 'name': 'Tiên Sơn'},
    '清化': {'lat': 19.8072, 'lon': 105.3373, 'region': 'Vietnam', 'name': 'Thanh Hóa'},
    '義安': {'lat': 18.6731, 'lon': 105.6934, 'region': 'Vietnam', 'name': 'Nghệ An'},
    '河靜': {'lat': 18.6731, 'lon': 105.6934, 'region': 'Vietnam', 'name': 'Hà Tĩnh'},
    '清涼': {'lat': 20.3789, 'lon': 105.9184, 'region': 'Vietnam', 'name': 'Thanh Lương'},
    '金山': {'lat': 21.0389, 'lon': 105.7937, 'region': 'Vietnam', 'name': 'Kim Sơn'},
    '雙樹': {'lat': 16.0623, 'lon': 107.5906, 'region': 'Vietnam', 'name': 'Song Thụ'},
    '大羅': {'lat': 21.0285, 'lon': 105.8342, 'region': 'Vietnam', 'name': 'Đại La'},
}

def extract_places_from_sutra(sutra_text):
    """Extract place names from sutra text"""
    found_places = []
    for place_cn, info in SUTRA_PLACE_PATTERNS.items():
        if place_cn in sutra_text:
            found_places.append({
                'nameChinese': place_cn,
                'nameEnglish': info['name'],
                'lat': info['lat'],
                'lon': info['lon'],
                'region': info['region']
            })
    return found_places

@app.route('/api/spiritual-geocoder', methods=['GET', 'POST'])
def spiritual_geocoder():
    """
    A1: Spiritual Geocoder API
    GET  - ?text=...  or ?sutra_id=...
    POST - {"text": "..."} or {"sutra_id": "Y0001"}
    """
    data = request.get_json() or {}
    
    # Get text from query or body
    text = data.get('text', '') or request.args.get('text', '')
    sutra_id = data.get('sutra_id', '') or request.args.get('sutra_id', '')
    
    # If sutra_id provided, load from CBETA
    if sutra_id:
        # Try to find sutra text (placeholder - would integrate with CBETA API)
        text = f"[Sutra {sutra_id} content would be loaded here]"
    
    if not text:
        return jsonify({'error': 'text or sutra_id required'}), 400
    
    # Extract places
    places = extract_places_from_sutra(text)
    
    return jsonify({
        'sutra_id': sutra_id,
        'text_length': len(text),
        'places_found': len(places),
        'places': places
    })

@app.route('/api/spiritual-geocoder/places', methods=['GET'])
def list_spiritual_places():
    """List all known spiritual places with GPS"""
    return jsonify({
        'count': len(SUTRA_PLACE_PATTERNS),
        'places': [
            {'nameChinese': k, 'lat': v['lat'], 'lon': v['lon'], 'region': v['region'], 'name': v['name']}
            for k, v in SUTRA_PLACE_PATTERNS.items()
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
