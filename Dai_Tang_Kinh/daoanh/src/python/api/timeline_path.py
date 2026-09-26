#!/usr/bin/env python3
"""
A2: Timeline-Path Engine API
Filter places by character + time range, create path visualization
"""

from flask import Flask, jsonify, request
import json
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Character-date mappings (expanded - 30+ important Buddhist figures)
CHARACTER_DATES = {
    # Early Indian Buddhist masters
    '摩訶迦葉': {'birth': -1000, 'death': -900, 'role': 'Kāśyapa Buddha', 'region': 'India'},
    '阿難': {'birth': -500, 'death': -400, 'role': 'Ananda', 'region': 'India'},
    '舍利弗': {'birth': -560, 'death': -480, 'role': 'Śāriputra', 'region': 'India'},
    '目犍連': {'birth': -560, 'death': -480, 'role': 'Maudgalyāyana', 'region': 'India'},
    
    # Indian patriarchs (28 Patriarchs)
    '迦葉': {'birth': -1000, 'death': -900, 'role': 'Nguyệt Xương', 'region': 'India'},
    '阿難': {'birth': -500, 'death': -400, 'role': 'Thiện Hiền', 'region': 'India'},
    '商那和修': {'birth': -400, 'death': -300, 'role': 'Na-Tiềm Tử', 'region': 'India'},
    '優波毱多': {'birth': -300, 'death': -200, 'role': 'Vô Đức Tử', 'region': 'India'},
    '提多迦': {'birth': -200, 'death': -100, 'role': 'Đề-các Tử', 'region': 'India'},
    '彌遮迦': {'birth': -100, 'death': 0, 'role': 'Di-võ Tử', 'region': 'India'},
    '佛陀難提': {'birth': 0, 'death': 100, 'role': 'Phật-đà Nam Đề', 'region': 'India'},
    '富那夜提': {'birth': 100, 'death': 200, 'role': 'Phú-na Diệt', 'region': 'India'},
    '馬鳴': {'birth': 150, 'death': 250, 'role': 'Ma Minh', 'region': 'India'},
    '迦葉摩騰': {'birth': 200, 'death': 300, 'role': 'Ca-da-mẫu', 'region': 'India'},
    '羅睺羅': {'birth': 250, 'death': 350, 'role': 'La-hầu-la', 'region': 'India'},
    
    # Chinese Zen patriarchs
    '達摩': {'birth': 470, 'death': 543, 'role': 'Tổ sư Trung Hoa', 'region': 'China'},
    '慧可': {'birth': 487, 'death': 593, 'role': 'Nhị Tổ', 'region': 'China'},
    '僧璨': {'birth': 536, 'death': 606, 'role': 'Tam Tổ', 'region': 'China'},
    '道信': {'birth': 580, 'death': 651, 'role': 'Tứ Tổ', 'region': 'China'},
    '弘忍': {'birth': 601, 'death': 675, 'role': 'Ngũ Tổ', 'region': 'China'},
    '慧能': {'birth': 638, 'death': 713, 'role': 'Lục Tổ', 'region': 'China'},
    '神秀': {'birth': 606, 'death': 706, 'role': 'Tổ sư Bắc Tông', 'region': 'China'},
    
    # Vietnamese Zen masters
    '法海': {'birth': 746, 'death': 816, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '慧忠': {'birth': 680, 'death': 755, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '無言通': {'birth': 810, 'death': 890, 'role': 'Tổ sư Vô Ngôn Thông', 'region': 'Vietnam'},
    '雲嶽': {'birth': 980, 'death': 1051, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '了悟': {'birth': 1050, 'death': 1110, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '慧讓': {'birth': 1100, 'death': 1170, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '法眼': {'birth': 1150, 'death': 1220, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '竹林派': {'birth': 1300, 'death': 1400, 'role': 'Trúc Lâm phái', 'region': 'Vietnam'},
    '了庵': {'birth': 1350, 'death': 1430, 'role': 'Thiền sư', 'region': 'Vietnam'},
    '醉禪': {'birth': 1400, 'death': 1490, 'role': 'Thiền sư', 'region': 'Vietnam'},
    
    # Modern Vietnamese monks
    '一行': {'birth': 1923, 'death': 1997, 'role': 'Hòa thượng Nhất Hạnh', 'region': 'Vietnam'},
    '法臘': {'birth': 1913, 'death': 2023, 'role': 'Hòa thượng', 'region': 'Vietnam'},
}

# Load places data
def load_places():
    places_path = os.path.join(DATA_DIR, 'processed', 'places_final.json')
    if os.path.exists(places_path):
        with open(places_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('places', [])
    return []

@app.route('/api/timeline-path', methods=['GET'])
def timeline_path():
    """
    A2: Timeline-Path Engine
    Filter places by character + time range
    
    Parameters:
    - char: Character name (e.g., "慧能")
    - start_year: Start year (e.g., 600)
    - end_year: End year (e.g., 750)
    - include_monks: Include related monks (default: true)
    """
    char = request.args.get('char', '')
    start_year = int(request.args.get('start_year', -500))
    end_year = int(request.args.get('end_year', 2026))
    include_monks = request.args.get('include_monks', 'true').lower() == 'true'
    
    # Get character info
    char_info = CHARACTER_DATES.get(char, {})
    char_birth = char_info.get('birth', start_year)
    char_death = char_info.get('death', end_year)
    
    # Adjust time range based on character lifespan
    if char and char_info:
        start_year = min(start_year, char_birth - 50) if char_birth else start_year
        end_year = max(end_year, char_death + 50) if char_death else end_year
    
    # Load all places
    all_places = load_places()
    
    # Filter places within time range
    filtered = []
    for place in all_places:
        # Check if place has any date info
        place_year = place.get('year') or place.get('active_period', {}).get('start')
        
        if place_year:
            try:
                place_year = int(place_year)
                if start_year <= place_year <= end_year:
                    filtered.append(place)
            except:
                pass
        # If no date info, include based on region/period
        else:
            # Add places without explicit dates that match character region
            if char and 'region' in char_info:
                if place.get('country') == get_country_code(char_info['region']):
                    filtered.append(place)
    
    # Build path data (ordered by time)
    path_data = sorted(filtered, key=lambda x: x.get('year') or 0)
    
    return jsonify({
        'character': char,
        'character_info': char_info,
        'time_range': {'start': start_year, 'end': end_year},
        'places_count': len(path_data),
        'path': path_data,
        'bounds': calculate_bounds(path_data)
    })

def get_country_code(region):
    """Map region name to country code"""
    mapping = {
        'India': 'IN',
        'China': 'CN',
        'Vietnam': 'VN',
        'Japan': 'JP',
        'Korea': 'KR'
    }
    return mapping.get(region, 'UN')

def calculate_bounds(places):
    """Calculate map bounds for path"""
    lats = [p.get('lat') for p in places if p.get('lat')]
    lons = [p.get('lon') for p in places if p.get('lon')]
    
    if not lats or not lons:
        return None
    
    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons),
        'center': [sum(lats)/len(lats), sum(lons)/len(lons)]
    }

@app.route('/api/timeline-path/characters', methods=['GET'])
def list_characters():
    """List known characters with dates"""
    return jsonify({
        'count': len(CHARACTER_DATES),
        'characters': CHARACTER_DATES
    })

@app.route('/api/timeline-path/animate', methods=['GET'])
def timeline_animate():
    """
    Get animation data for timeline playback
    Returns places in order with timestamps
    """
    char = request.args.get('char', '')
    char_info = CHARACTER_DATES.get(char, {})
    
    if not char_info:
        return jsonify({'error': 'Character not found'}), 404
    
    all_places = load_places()
    birth = char_info.get('birth', 0)
    death = char_info.get('death', 2026)
    
    # Group places by year
    timeline = []
    for place in all_places:
        year = place.get('year')
        if year:
            try:
                year = int(year)
                if birth <= year <= death:
                    timeline.append({
                        'year': year,
                        'place': place,
                        'event': f"Visit {place.get('nameVietnamese') or place.get('nameChinese')}"
                    })
            except:
                pass
    
    # Sort by year
    timeline.sort(key=lambda x: x['year'])
    
    return jsonify({
        'character': char,
        'birth': birth,
        'death': death,
        'events': timeline
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002)
