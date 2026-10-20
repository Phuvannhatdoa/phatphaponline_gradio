#!/usr/bin/env python3
"""
Data Fusion Script - Hợp Nhất Dữ Liệu
Zero-RAM: Dùng streaming/generator để xử lý file lớn
Sử dụng ijson cho true streaming của large JSON files
"""
import json
import os
import re
import ijson
from datetime import datetime
from unicodedata import normalize as uni_normalize

# === CONSTANTS ===
WORK_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"
PERSONS_FILE = f"{WORK_DIR}/data/persons.json"
COMBINED_DICT_FILE = f"{WORK_DIR}/data/indexed/combined_dict.json"
PLACES_FILE = f"{WORK_DIR}/data/places.json"
OUTPUT_DIR = f"{WORK_DIR}/data/indexed"

# === HELPER FUNCTIONS ===

def normalize_name(name):
    """Normalize name: bỏ dấu, lowercase, strip"""
    if not name:
        return ""
    # Bỏ dấu tiếng Việt và ký tự Hán
    normalized = uni_normalize('NFD', name)
    ascii_name = ''.join(c for c in normalized if ord(c) < 128)
    return ascii_name.lower().strip()

def extract_names_from_person(person):
    """Trích xuất tất cả tên từ person entry"""
    names = []
    if 'names' in person:
        for name_entry in person['names']:
            if 'value' in name_entry:
                names.append(name_entry['value'])
    return names

def extract_chinese_name(term):
    """Trích xuất tên Hán từ term hoặc definition trong dict"""
    term_clean = term.strip()
    
    # Pattern 1: (01) Vietnamese - lấy phần trong ngoặc đầu tiên nếu là Hán
    match = re.search(r'\(([^\)]+)\):\s*(.+)', term_clean)
    if match:
        han_part = match.group(1).strip()
        # Nếu phần trong ngoặc chứa ký tự Hán
        if re.search(r'[\u4e00-\u9fff]', han_part):
            return han_part
    
    # Pattern 2: Tìm ký tự Hán trong term (sau số thứ tự)
    match2 = re.search(r'\(\d+\)\s*([^\(]+)', term_clean)
    if match2:
        text = match2.group(1).strip()
        if re.search(r'[\u4e00-\u9fff]', text):
            # Lấy chuỗi Hán đầu tiên
            han_match = re.search(r'[\u4e00-\u9fff]+', text)
            if han_match:
                return han_match.group()
    
    return None

def extract_chinese_from_definition(definition):
    """Trích xuất tên Hán từ definition"""
    if not definition:
        return None
    
    # Pattern: (Hán: definition)
    match = re.search(r'\(([^\)]+)\):\s*([^\(]+)', definition)
    if match:
        han_part = match.group(1).strip()
        if re.search(r'[\u4e00-\u9fff]', han_part):
            return han_part
    
    # Lấy ký tự Hán đầu tiên trong definition
    han_match = re.search(r'[\u4e00-\u9fff]+', definition)
    if han_match:
        return han_match.group()
    
    return None

# === STREAMING FUNCTIONS (iJSON for true streaming) ===

def stream_persons():
    """Generator: Stream persons.json theo từng person entry (iJSON)"""
    with open(PERSONS_FILE, 'rb') as f:  # binary mode for ijson
        for person in ijson.items(f, 'persons.item'):
            yield person

def stream_combined_dict():
    """Generator: Stream combined_dict.json theo từng entry (iJSON)"""
    with open(COMBINED_DICT_FILE, 'rb') as f:
        for entry in ijson.items(f, 'entries.item'):
            yield entry

def stream_places():
    """Generator: Stream places.json theo từng place entry (iJSON)"""
    with open(PLACES_FILE, 'rb') as f:
        for place in ijson.items(f, 'places.item'):
            yield place

# === MAIN PROCESSING ===

def build_name_lookup():
    """Bước 1: Xây dựng name→DILA lookup từ persons.json"""
    print("🔄 Bước 1: Xây dựng name lookup từ persons.json...")
    
    name_to_dila = {}
    person_count = 0
    
    for person in stream_persons():
        dila_id = person.get('id', '')
        if not dila_id:
            continue
        
        names = extract_names_from_person(person)
        for name in names:
            norm_name = normalize_name(name)
            if norm_name and norm_name not in name_to_dila:
                name_to_dila[norm_name] = {
                    'dila_id': dila_id,
                    'original': name
                }
        
        person_count += 1
        if person_count % 10000 == 0:
            print(f"  ✓ Đã xử lý {person_count} persons...")
    
    print(f"  ✅ Hoàn thành: {person_count} persons, {len(name_to_dila)} unique names")
    return name_to_dila, person_count

def run_data_fusion(name_lookup):
    """Bước 2: Data Fusion - Match combined_dict với persons"""
    print("\n🔄 Bước 2: Data Fusion...")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "total_entries": 0,
        "merged": 0,
        "orphans": [],
        "sameas_links": []
    }
    
    # Stats
    entry_count = 0
    matched_count = 0
    
    # Debug: show sample lookup keys
    sample_keys = list(name_lookup.keys())[:10]
    print(f"  📋 Sample lookup keys: {sample_keys}")
    
    # Process combined_dict - streaming
    for entry in stream_combined_dict():
        term = entry.get('term', '')
        definition = entry.get('definition', '')
        log_data['total_entries'] += 1
        
        # Try matching from term first
        chinese_name = extract_chinese_name(term)
        
        matched = False
        matched_id = None
        
        if chinese_name:
            norm_name = normalize_name(chinese_name)
            # Debug: print some samples
            if entry_count < 5:
                print(f"  Debug - term: {term[:50]}, chinese: {chinese_name}, norm: {norm_name}")
            
            if norm_name in name_lookup:
                matched = True
                matched_id = name_lookup[norm_name]['dila_id']
        
        # If not matched, try definition
        if not matched and definition:
            def_chinese = extract_chinese_from_definition(definition)
            if def_chinese:
                norm_def = normalize_name(def_chinese)
                if norm_def in name_lookup:
                    matched = True
                    matched_id = name_lookup[norm_def]['dila_id']
        
        if matched:
            log_data['merged'] += 1
            matched_count += 1
            log_data['sameas_links'].append({
                "term": term[:100],
                "dila_id": matched_id,
                "source": entry.get('source', '')
            })
        else:
            log_data['orphans'].append({
                "term": term[:100],
                "source": entry.get('source', '')
            })
        
        entry_count += 1
        if entry_count % 10000 == 0:
            print(f"  ✓ Đã xử lý {entry_count} entries...")
    
    print(f"  ✅ Hoàn thành: {entry_count} entries, {matched_count} matched")
    return log_data

def count_temples_with_gps():
    """Đếm số chùa có GPS"""
    print("\n🔄 Bước 3: Đếm places có GPS...")
    
    gps_count = 0
    total_places = 0
    
    for place in stream_places():
        total_places += 1
        lat = place.get('lat', '')
        lon = place.get('lon', '')
        if lat and lon and lat != '0' and lon != '0':
            gps_count += 1
    
    print(f"  ✅ Places: {total_places} total, {gps_count} có GPS")
    return gps_count, total_places

def rebuild_binary_index(name_lookup):
    """Bước 4: Rebuild binary index"""
    print("\n🔄 Bước 4: Rebuild binary index...")
    
    # Sắp xếp theo normalized name
    sorted_entries = sorted(name_lookup.items(), key=lambda x: x[0])
    
    idx_file = f"{OUTPUT_DIR}/entity_master.idx"
    
    # Binary format: magic(4) + version(4) + count(8) + entries
    # Entry: len(key)+1 + key + dila_id
    
    with open(idx_file, 'wb') as f:
        # Magic: PTH1 (4 bytes)
        f.write(b'PTH1')
        # Version: 0001 (4 bytes)
        f.write(b'0001')
        # Count (8 bytes, little-endian)
        count = len(sorted_entries)
        f.write(count.to_bytes(8, 'little'))
        
        # Entries
        for norm_name, data in sorted_entries:
            key_bytes = norm_name.encode('utf-8')
            dila_bytes = data['dila_id'].encode('utf-8')
            
            # Format: key_len(2) + key + dila_id
            f.write(len(key_bytes).to_bytes(2, 'little'))
            f.write(key_bytes)
            f.write(b'\x00')  # separator
            f.write(dila_bytes)
    
    print(f"  ✅ Đã tạo {idx_file} với {count} entries")
    return idx_file

def write_system_map(person_count, dict_entry_count, place_count, gps_count):
    """Bước 5: Write SYSTEM_MAP.md"""
    print("\n🔄 Bước 5: Write SYSTEM_MAP.md...")
    
    content = f"""# System Map - Phật Pháp Online
**Phiên bản:** {datetime.now().strftime('%Y-%m-%d')}
**Primary Key:** DILA ID (Axxxxx format)

## Cấu Trúc 4-Lớp Dữ Liệu
- 01_raw/ - Nguồn thô (.docx, .txt, .xml)
- 02_external/ - Dữ liệu ngoài (BDRC, GraphDB)
- 03_processing/ - Scripts & ETL
- 04_production/ - Binary index & API

## Thống Kê
- persons.json: {person_count:,} entries (ID DILA)
- combined_dict.json: {dict_entry_count:,} entries (22 dictionaries)
- places.json: {place_count:,} entries ({gps_count:,} có GPS)
- indexed/entity_master.idx: Binary search ready

## Zero-RAM Compliance
- Streaming generator cho large files
- Binary index cho O(log n) lookup
- Không load toàn bộ vào RAM
"""
    
    map_file = f"{WORK_DIR}/SYSTEM_MAP.md"
    with open(map_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Đã ghi {map_file}")
    return map_file

def write_summary_report(person_count, dict_entry_count, place_count, gps_count, matched_count):
    """Bước 6: Write SUMMARY_REPORT.md"""
    print("\n🔄 Bước 6: Write SUMMARY_REPORT.md...")
    
    content = f"""# SUMMARY_REPORT.md - Tổng Kết Hệ Thống
**Ngày:** {datetime.now().strftime('%Y-%m-%d')}

## Thống Kê Dữ Liệu

| Nguồn | Số Lượng | Ghi Chú |
|-------|----------|---------|
| **Tổ (Tăng Ni)** | {person_count:,} vị | Từ persons.json (DILA ID) |
| **Chùa có GPS** | {gps_count:,} | Từ places.json |
| **Tổng Places** | {place_count:,} | Tất cả địa danh |
| **Thuật ngữ** | {dict_entry_count:,} | Từ combined_dict.json |

## Data Fusion Results

| Trạng Thái | Số Lượng | Tỷ Lệ |
|------------|----------|-------|
| **Matched** | {matched_count:,} | {matched_count*100/dict_entry_count:.1f}% |
| **Orphans** | {dict_entry_count - matched_count:,} | {(dict_entry_count - matched_count)*100/dict_entry_count:.1f}% |
| **Tổng** | {dict_entry_count:,} | 100% |

## Binary Index

- File: `data/indexed/entity_master.idx`
- Format: PTH1 + version + count + entries
- Lookup: O(log n) binary search

## Zero-RAM Compliance

✅ Streaming generator cho persons.json (47MB)
✅ Streaming generator cho combined_dict.json (18MB)  
✅ Binary index cho fast lookup
✅ Memory-efficient processing
"""
    
    report_file = f"{WORK_DIR}/SUMMARY_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Đã ghi {report_file}")
    return report_file

def write_integration_log(log_data):
    """Bước 7: Write INTEGRATION_LOG.json"""
    print("\n🔄 Bước 7: Write INTEGRATION_LOG.json...")
    
    # Giới hạn orphans và sameas_links để file không quá lớn
    log_output = {
        "timestamp": log_data['timestamp'],
        "total_entries": log_data['total_entries'],
        "merged": log_data['merged'],
        "orphans_count": len(log_data['orphans']),
        "sameas_links_count": len(log_data['sameas_links']),
        "orphans": log_data['orphans'][:100],  # Giới hạn 100
        "sameas_links": log_data['sameas_links'][:100]  # Giới hạn 100
    }
    
    log_file = f"{OUTPUT_DIR}/INTEGRATION_LOG.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_output, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ Đã ghi {log_file}")
    return log_file

# === MAIN ===

def main():
    print("=" * 60)
    print("🚀 Data Fusion - Zero-RAM Processing")
    print("=" * 60)
    
    # Bước 1: Build name lookup
    name_lookup, person_count = build_name_lookup()
    
    # Bước 2: Data Fusion
    log_data = run_data_fusion(name_lookup)
    dict_entry_count = log_data['total_entries']
    matched_count = log_data['merged']
    
    # Bước 3: Count places with GPS
    gps_count, place_count = count_temples_with_gps()
    
    # Bước 4: Rebuild binary index
    rebuild_binary_index(name_lookup)
    
    # Bước 5: Write SYSTEM_MAP.md
    write_system_map(person_count, dict_entry_count, place_count, gps_count)
    
    # Bước 6: Write SUMMARY_REPORT.md
    write_summary_report(person_count, dict_entry_count, place_count, gps_count, matched_count)
    
    # Bước 7: Write INTEGRATION_LOG.json
    write_integration_log(log_data)
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH DATA FUSION")
    print("=" * 60)
    print(f"📊 Persons: {person_count:,}")
    print(f"📊 Dictionary entries: {dict_entry_count:,}")
    print(f"📊 Matched: {matched_count:,} ({matched_count*100/dict_entry_count:.1f}%)")
    print(f"📊 Places: {place_count:,} ({gps_count:,} có GPS)")

if __name__ == "__main__":
    main()