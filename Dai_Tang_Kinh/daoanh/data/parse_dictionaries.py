#!/usr/bin/env python3
"""
Script để parse từ điển Phật giáo (.docx) và tạo dictionary lookup
cho Phật Tổ Đạo Ảnh project
"""

import os
import re
import json
from docx import Document
from pathlib import Path

BASE_DIR = Path(__file__).parent
DICT_DIR = BASE_DIR / "dictionaries"
OUTPUT_DIR = BASE_DIR / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)

def parse_docx(filepath):
    """Parse .docx file và extract text"""
    doc = Document(filepath)
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())
    return paragraphs

def extract_entries_dao_uuyen(text_lines):
    """Parse Từ Điển Phật Học Đạo Uyển"""
    entries = []
    current_entry = None
    
    for line in text_lines:
        # Pattern: Từ Hán + Nghĩa Việt
        # Ví dụ: "AN CỦU 庵就 - Chùa..."
        match = re.match(r'^([A-Z\s\-]+)\s*[-–]\s*(.+)$', line.strip())
        if match:
            if current_entry:
                entries.append(current_entry)
            han = match.group(1).strip()
            viet = match.group(2).strip()
            current_entry = {
                "term": han,
                "vietnamese": viet,
                "source": "Đạo Uyển"
            }
        elif current_entry:
            current_entry["description"] = current_entry.get("description", "") + " " + line
    
    if current_entry:
        entries.append(current_entry)
    
    return entries

def extract_entries_phat_quang(text_lines):
    """Parse Phật Quang Tự Điển"""
    entries = []
    current_entry = None
    
    for line in text_lines:
        # Phật Quang format: có thể bắt đầu với từ Hán
        if re.match(r'^[\u4e00-\u9fff]+', line):
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "term": line,
                "source": "Phật Quang"
            }
        elif current_entry:
            if not current_entry.get("vietnamese"):
                current_entry["vietnamese"] = line
            else:
                current_entry["description"] = current_entry.get("description", "") + " " + line
    
    if current_entry:
        entries.append(current_entry)
    
    return entries

def extract_thien_tong(text_lines):
    """Parse Từ Điển Thiền Tông Hán Việt"""
    entries = []
    
    for i, line in enumerate(text_lines):
        # Tìm dòng có format: HÁN VIỆT - description
        match = re.match(r'^([\u4e00-\u9fff\s]+)\s*[-–]\s*(.+)$', line)
        if match:
            entries.append({
                "term": match.group(1).strip(),
                "vietnamese": match.group(2).strip(),
                "source": "Thiền Tông"
            })
    
    return entries

def extract_danh_tang(text_lines):
    """Parse Tiểu Sử Danh Tăng Việt Nam"""
    entries = []
    current_entry = None
    
    for line in text_lines:
        # Tìm tên tu sĩ (bắt đầu bằng số hoặc Hán tự)
        match = re.match(r'^(\d+[\.\)]\s*)?([\u4e00-\u9fff\s]+)', line)
        if match:
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "name": match.group(2).strip() if match.group(2) else line,
                "source": "Danh Tăng VN"
            }
            # Try to extract years
            year_match = re.search(r'\((\d{4})[-–](\d{4}|[^)]+)\)', line)
            if year_match:
                current_entry["years"] = year_match.group(0)
        elif current_entry:
            current_entry["bio"] = current_entry.get("bio", "") + " " + line
    
    if current_entry:
        entries.append(current_entry)
    
    return entries

def create_place_lookup(entries):
    """Tạo lookup dict từ entries cho places.json"""
    lookup = {}
    
    for entry in entries:
        term = entry.get("term", "")
        viet = entry.get("vietnamese", "")
        name = entry.get("name", "")
        
        # Normalize key
        key = term.lower().strip() if term else name.lower().strip()
        if not key:
            continue
            
        lookup[key] = {
            "vietnamese": viet or name,
            "description": entry.get("description", "") or entry.get("bio", ""),
            "years": entry.get("years", ""),
            "source": entry.get("source", "")
        }
    
    return lookup

def main():
    print("🔍 Parsing Buddhist Dictionaries...")
    
    all_entries = []
    
    # Parse Đạo Uyển
    dao_uuyen_file = DICT_DIR / "Tu Dien Phat Hoc Dao Uyen.docx"
    if dao_uuyen_file.exists():
        print(f"📖 Parsing: {dao_uuyen_file.name}")
        text = parse_docx(dao_uuyen_file)
        entries = extract_entries_dao_uuyen(text)
        print(f"   → {len(entries)} entries extracted")
        all_entries.extend(entries)
    
    # Parse Phật Quang
    phat_quang_file = DICT_DIR / "Phat Quang Tu Dien - HT Quang Do.docx"
    if phat_quang_file.exists():
        print(f"📖 Parsing: {phat_quang_file.name}")
        text = parse_docx(phat_quang_file)
        entries = extract_entries_phat_quang(text)
        print(f"   → {len(entries)} entries extracted")
        all_entries.extend(entries)
    
    # Parse Thiền Tông
    thien_tong_file = DICT_DIR / "Tu Dien Thien Tong Han Viet - Han Man - Thong Thien.docx"
    if thien_tong_file.exists():
        print(f"📖 Parsing: {thien_tong_file.name}")
        text = parse_docx(thien_tong_file)
        entries = extract_thien_tong(text)
        print(f"   → {len(entries)} entries extracted")
        all_entries.extend(entries)
    
    # Parse Danh Tăng VN
    danh_tang_file = DICT_DIR / "Tieu Su Danh Tang Viet Nam - TK Thich Dong Bon.doc"
    if danh_tang_file.exists():
        print(f"📖 Parsing: {danh_tang_file.name}")
        text = parse_docx(danh_tang_file)
        entries = extract_danh_tang(text)
        print(f"   → {len(entries)} entries extracted")
        all_entries.extend(entries)
    
    # Create lookup
    lookup = create_place_lookup(all_entries)
    
    # Save to JSON
    output_file = OUTPUT_DIR / "dictionary_lookup.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "entries": all_entries,
            "lookup": lookup,
            "stats": {
                "total": len(all_entries),
                "sources": list(set(e.get("source", "") for e in all_entries))
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved {len(lookup)} entries to: {output_file}")
    
    # Also create monk dictionary for search
    monk_dict = [e for e in all_entries if e.get("source") == "Danh Tăng VN"]
    monk_output = OUTPUT_DIR / "monk_bio_lookup.json"
    with open(monk_output, 'w', encoding='utf-8') as f:
        json.dump(monk_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(monk_dict)} monk bios to: {monk_output}")

if __name__ == "__main__":
    main()
