#!/usr/bin/env python3
import json
import re
import csv
import unicodedata
import requests
from collections import defaultdict


GRAPHDB_URL = "http://localhost:7200/repositories/buddhist"
MONK_LIST_FILE = "data/monk_list.json"
EXCLUDED_FILE = "data/excluded_monks.csv"
OUTPUT_FILE = "data/potential_links.csv"

def load_excluded():
    excluded = set()
    try:
        with open(EXCLUDED_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Tên Thiền Sư", "").strip()
                if name:
                    excluded.add(name)
    except FileNotFoundError:
        pass
    return excluded

from datetime import date

def save_excluded(excluded):
    with open(EXCLUDED_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Tên Thiền Sư", "Ngày Loại"])
        writer.writeheader()
        for name in sorted(excluded):
            writer.writerow({"Tên Thiền Sư": name, "Ngày Loại": str(date.today())})

def load_monk_list():
    with open(MONK_LIST_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    known_names = set()
    for item in raw:
        label = item.get("label", "")
        if label:
            known_names.add(label.strip())
            known_names.add(label.strip().lower())
    print(f"Loaded {len(known_names)//2} unique monk names from monk_list.json")
    return known_names

def fetch_all_bios():
    query = """PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?s ?label ?note WHERE {
        ?s rdfs:label ?label .
        FILTER(lang(?label) = "vi")
        ?s bkg:biographicalNote ?note .
    }"""
    
    print("Fetching bios from GraphDB...")
    r = requests.get(
        GRAPHDB_URL,
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=60
    )
    data = r.json()
    bios = []
    for b in data.get("results", {}).get("bindings", []):
        label = b.get("label", {}).get("value", "")
        note = b.get("note", {}).get("value", "")
        s_uri = b.get("s", {}).get("value", "")
        if label and note:
            bios.append({"label": label, "note": note, "uri": s_uri})
    print(f"Fetched {len(bios)} bios with notes")
    return bios

def normalize(s):
    return unicodedata.normalize("NFC", s)

NOT_NAME_PARTS = {'ở', 'bảo', 'hỏi', 'thượng', 'đường', 'điện', 'đàm', 'đầu', 'viện', 
                  'bèn', 'đánh', 'đáp', 'quát', 'biết', 'rằng', 'đi', 'nói', 'hỏi',
                  'về', 'ra', 'vào', 'lên', 'xuống', 'đến', 'từ', 'cho', 'được',
                  'các', 'này', 'kia', 'nọ', 'đây', 'kìa', 'hay', 'và', 'hay',
                  'với', 'bởi', 'nên', 'vì', 'nhưng', 'mà', 'hay', 'thì', 'nếu',
                  'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười',
                  'nghĩ', 'muốn', 'cần', 'phải', 'đang', 'đã', 'sẽ', 'vẫn', 'còn',
                  'rất', 'quá', 'lắm', 'hơn', 'kém', 'vừa', 'đang', 'vậy', 'thế',
                  'đặc', 'biệt', 'hết', 'trước', 'sau', 'trong', 'ngoài', 'trên', 'dưới',
                  'giữa', 'giữa', 'bên', 'ngoài', 'trong', 'ngoài', 'tại', 'theo',
                  'cùng', 'với', 'khi', 'lúc', 'nơi', 'nọ', 'kia', 'đây', 'ấy'}

def looks_like_monk_name(name):
    if not name or len(name) < 4 or len(name) > 45:
        return False
    words = name.strip().split()
    if len(words) < 2:
        return False
    
    VERB_PATTERNS = ['nêu cử', 'đem công', 'vui vẻ', 'nắm tay', 'trao truyền', 'thọ trai', 
                     'gửi thư', 'nghiêng mặt', 'nghiêm sắc', 'sao lại', 'căn cứ', 'sai thị',
                     'nêu cử', 'thấy gặp', 'nói đó', 'đến đó', 'vân du', 'nghinh đón',
                     'bảo:', 'hỏi:', 'đáp:', 'nói:', 'dạy:', 'cười:', 'thị tịch', 'viên tịch']
    
    name_lower = name.lower()
    for vp in VERB_PATTERNS:
        if vp in name_lower:
            return False
    
    ACTION_WORDS = {'nêu', 'đem', 'vui', 'tra', 'đưa', 'trô', 'nghiêng', 'sai', 'gửi', 'căn', 'thấy', 'nói', 'đến', 'vân', 'nghinh'}
    
    NAME_CHARS = set('aăâbcdđeêghiklmnoôơpqrstuưvwxyzAĂÂBCDĐEÊGHIKLMNOÔƠPQRSTUƯVWXYZÀÈÌÒÙẰÈÌÒÙÁÉÍÓÚÂÊÍÔÚĀĔĪŌŪǢǤǦǨǪṒṔȘȚẠẸỊỌỤẬẦẾỒỆỈỌỎỦỬỰỲỴŽ')
    
    last_word = words[-1] if words else ""
    for c in last_word:
        if c not in NAME_CHARS and c != ' ':
            return False
    
    for w in words:
        w_lower = w.lower()
        if w_lower in ACTION_WORDS:
            return False
        if w_lower in NOT_NAME_PARTS:
            return False
    
    for w in words:
        if len(w) <= 2:
            return False
    
    return True

def find_mentioned_monks(text):
    found = set()
    
    title_prefixes = ['Thiền sư', 'Trưởng lão']
    
    for title in title_prefixes:
        pattern = rf'{re.escape(title)}\s+([A-ZÀ-Ỹ][a-zà-ỹ]{{1,15}}(?:\s+[A-ZÀ-Ỹ]?[a-zà-ỹ]{{1,15}}){{0,2}})'
        for m in re.finditer(pattern, text):
            name = m.group(1).strip()
            name = re.sub(r'\s+', ' ', name)
            if looks_like_monk_name(name):
                found.add(name)
    
    ngai_pattern = r'Ngài\s+([A-ZÀ-Ỹ][a-zà-ỹ]{{1,15}}(?:\s+[A-ZÀ-Ỹ]?[a-zà-ỹ]{{1,15}}){{0,2}})'
    for m in re.finditer(ngai_pattern, text):
        name = m.group(1).strip()
        name = re.sub(r'\s+', ' ', name)
        if looks_like_monk_name(name):
            found.add(name)
    
    bon_su_pattern = r'Bổn\s*sư\s+([A-ZÀ-Ỹ][a-zà-ỹ]{{1,15}}(?:\s+[A-ZÀ-Ỹ]?[a-zà-ỹ]{{1,15}}){{0,2}})'
    for m in re.finditer(bon_su_pattern, text, re.IGNORECASE):
        name = m.group(1).strip()
        name = re.sub(r'\s+', ' ', name)
        if looks_like_monk_name(name):
            found.add(name)
    
    ho_th_pattern = r'(?:^|[^a-zà-ỹ])Hòa\s*thượng\s+([A-ZÀ-Ỹ][a-zà-ỹ]{{1,15}}(?:\s+[A-ZÀ-Ỹ]?[a-zà-ỹ]{{1,15}}){{0,2}})'
    for m in re.finditer(ho_th_pattern, text):
        name = m.group(1).strip()
        name = re.sub(r'\s+', ' ', name)
        if looks_like_monk_name(name):
            found.add(name)
    
    return list(found)

def find_potential_links():
    known_names = load_monk_list()
    excluded_names = load_excluded()
    bios = fetch_all_bios()
    
    potential = defaultdict(lambda: {"count": 0, "sources": [], "contexts": []})
    
    for bio in bios:
        monk_name = bio["label"]
        note = bio["note"]
        
        mentioned = find_mentioned_monks(note)
        for name in mentioned:
            name_nfc = normalize(name)
            name_lower = name_nfc.lower()
            
            is_known = False
            for known in known_names:
                known_norm = normalize(known).lower()
                if known_norm == name_lower or name_lower in known_norm:
                    is_known = True
                    break
            
            if not is_known and name != monk_name and name not in excluded_names:
                context = ""
                idx = note.find(name)
                if idx >= 0:
                    start = max(0, idx - 30)
                    end = min(len(note), idx + len(name) + 30)
                    context = note[start:end].replace("\n", " ").strip()
                
                key = name_nfc
                potential[key]["count"] += 1
                source = bio["uri"].split("/")[-1].replace("_", "-")
                if source not in [s for s, _ in potential[key]["sources"]]:
                    potential[key]["sources"].append((source, monk_name))
                if context and context not in potential[key]["contexts"]:
                    potential[key]["contexts"].append(context)
    
    results = []
    for name, info in sorted(potential.items(), key=lambda x: -x[1]["count"]):
        source, monk = info["sources"][0] if info["sources"] else ("", "")
        ctx = info["contexts"][0] if info["contexts"] else ""
        results.append({
            "Tên Thiền Sư Mới": name,
            "Số Lần Xuất Hiện": info["count"],
            "Trích Từ (file TTL)": source,
            "Trích Đoạn Bio": ctx
        })
    
    print(f"Found {len(potential)} potential new monks")
    return results

def save_results(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Tên Thiền Sư Mới", "Số Lần Xuất Hiện", "Trích Từ (file TTL)", "Trích Đoạn Bio"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved {len(results)} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    results = find_potential_links()
    save_results(results)
