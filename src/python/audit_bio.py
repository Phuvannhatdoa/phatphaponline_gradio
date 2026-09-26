#!/usr/bin/env python3
"""
===============================================================================
GraphDB Bio Audit Script - P0-2
===============================================================================
Mục đích: Tìm bất hợp lý trong Bio truyền thừa TTL
Ví dụ:
- Tổ sư Bồ Đề Quang Dụng nhưng bio là Lâm Tế
- Hưng Hóa Tồn Tưởng là có 2 vị (trùng tên)
- Tên không tồn tại trong lịch sử/web/ebook
===============================================================================
"""

import json
import re
import requests
from collections import defaultdict

GRAPHDB_URL = "http://localhost:7200/repositories/buddhist"
OUTPUT_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/data/bio_audit_report.csv"

# Danh sách Tổ sư nổi tiếng để kiểm tra lineage trong bio
FOUNDERS = {
    "Bồ Đề Đạt Ma": "Thiền Tông Trung Hoa",
    "Lâm Tế Nghĩa Huyền": "Lâm Tế",
    "Mã Tổ Đạo Nhất": "Nam Tông",
    "Dương Kỳ Phương Hội": "Dương Kỳ",
    "Thạch Đầu Hy Thiên": "Thạch Đầu",
    "Bồ Đề Quang Dụng": "Liễu Quán",
    "Hưng Hóa Tồn Tưởng": "Liễu Quán",
    "Trần Nhân Tông": "Trúc Lâm",
    "Minh Hải Pháp Bảo": "Lâm Tế Chúc Thánh",
    "Liễu Quán": "Liễu Quán",
}

# Những từ khóa cho thấy bất hợp lý
CONFLICT_KEYWORDS = {
    "Bồ Đề Đạt Ma": ["Lâm Tế", "Thiếu Lâm", "Mã Tổ", "Nam Tông"],
    "Lâm Tế": ["Bồ Đề Đạt Ma", "Thiếu Lâm", "Ngọc Hoa"],
    "Mã Tổ": ["Bồ Đề Đạt Ma", "Lâm Tế", "Trung Quán"],
}

def query_graphdb(sparql):
    """Gọi GraphDB SPARQL endpoint"""
    r = requests.get(
        GRAPHDB_URL,
        params={"query": sparql},
        headers={"Accept": "application/sparql-results+json"},
        timeout=60
    )
    return r.json()

def get_all_monks_with_bios():
    """Lấy tất cả thiền sư có bio"""
    query = """
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?monk ?label ?bio ?lineage WHERE {
        ?monk rdfs:label ?label .
        FILTER(lang(?label) = "vi")
        OPTIONAL { ?monk bkg:biographicalNote ?bio }
        OPTIONAL { ?monk bkg:dharmaLineage ?lineage }
    }
    LIMIT 5000
    """
    data = query_graphdb(query)
    results = []
    for b in data.get("results", {}).get("bindings", []):
        label = b.get("label", {}).get("value", "")
        bio = b.get("bio", {}).get("value", "") if "bio" in b else ""
        lineage = b.get("lineage", {}).get("value", "") if "lineage" in b else ""
        uri = b.get("monk", {}).get("value", "")
        if label:
            results.append({
                "label": label,
                "bio": bio,
                "lineage": lineage,
                "uri": uri
            })
    return results

def check_lineage_conflict(monk_label, bio, lineage):
    """Kiểm tra xem bio có xung đột với lineage không"""
    issues = []
    bio_lower = bio.lower() if bio else ""
    lineage_lower = lineage.lower() if lineage else ""
    
    # Kiểm tra từng founder
    for founder, expected_lineage in FOUNDERS.items():
        if founder in monk_label:
            # Founder này có bio nói về lineage khác?
            for exp_lc in CONFLICT_KEYWORDS.get(founder, []):
                if exp_lc in bio_lower and expected_lineage not in lineage_lower:
                    issues.append(f"Bio nhắc đến '{exp_lc}' nhưng lineage là '{lineage}'")
    
    # Kiểm tra các từ khóa xung đột trong bio
    if "Lâm Tế" in bio and "Thiếu Lâm" in bio:
        issues.append("Bio chứa cả 'Lâm Tế' và 'Thiếu Lâm' - có thể confused")
    
    return issues

def check_duplicate_names(monks):
    """Tìm các trùng tên"""
    name_count = defaultdict(list)
    for m in monks:
        name_count[m["label"]].append(m)
    
    duplicates = {}
    for name, entries in name_count.items():
        if len(entries) > 1:
            duplicates[name] = entries
    
    return duplicates

def check_bio_quality(monk_label, bio):
    """Kiểm tra chất lượng bio"""
    issues = []
    
    if not bio or len(bio) < 20:
        issues.append("Bio quá ngắn hoặc trống")
        return issues
    
    # Kiểm tra các pattern bất thường
    bio_lower = bio.lower()
    
    # Pattern: "tại + số" - có thể là ngày tháng nhầm
    date_pattern = r'tại\s+năm\s+\d{3,4}'
    if re.search(date_pattern, bio):
        # Check năm có hợp lý không
        years = re.findall(r'\d{4}', bio)
        for year in years:
            if int(year) < 500 or int(year) > 2026:
                issues.append(f"Năm không hợp lý: {year}")
    
    return issues

def generate_report():
    """Tạo báo cáo audit"""
    print("=" * 60)
    print("GraphDB Bio Audit - Bắt đầu...")
    print("=" * 60)
    
    # Lấy tất cả monks có bio
    monks = get_all_monks_with_bios()
    print(f"Tìm thấy {len(monks)} thiền sư có trong GraphDB")
    
    # 1. Tìm duplicate names
    print("\n[1] Kiểm tra trùng tên...")
    duplicates = check_duplicate_names(monks)
    print(f"  Tìm thấy {len(duplicates)} tên trùng")
    for name, entries in list(duplicates.items())[:10]:
        print(f"    - {name}: {len(entries)} người")
    
    # 2. Kiểm tra lineage conflicts
    print("\n[2] Kiểm tra lineage conflicts...")
    conflicts = []
    for m in monks:
        issues = check_lineage_conflict(m["label"], m["bio"], m["lineage"])
        if issues:
            conflicts.append({
                "name": m["label"],
                "lineage": m["lineage"],
                "issues": issues
            })
    print(f"  Tìm thấy {len(conflicts)} potential conflicts")
    for c in conflicts[:10]:
        print(f"    - {c['name']}: {c['issues']}")
    
    # 3. Kiểm tra bio quality
    print("\n[3] Kiểm tra chất lượng bio...")
    quality_issues = []
    for m in monks:
        issues = check_bio_quality(m["label"], m["bio"])
        if issues:
            quality_issues.append({
                "name": m["label"],
                "issues": issues
            })
    print(f"  Tìm thấy {len(quality_issues)} bio có vấn đề")
    
    # Xuất CSV
    print(f"\n[4] Xuất báo cáo...")
    with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
        f.write("Tên,Lineage,Issues,URI\n")
        for d in duplicates:
            f.write(f'"{d}","DUPLICATE","{len(duplicates[d])} monks",\n')
        for c in conflicts:
            issues_str = "; ".join(c["issues"])
            f.write(f'"{c["name"]}","{c["lineage"]}","{issues_str}",\n')
        for q in quality_issues:
            issues_str = "; ".join(q["issues"])
            f.write(f'"{q["name"]}","","{issues_str}",\n')
    
    print(f"  Đã xuất: {OUTPUT_CSV}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TỔNG KẾT:")
    print(f"  - Tổng monks: {len(monks)}")
    print(f"  - Trùng tên: {len(duplicates)}")
    print(f"  - Lineage conflicts: {len(conflicts)}")
    print(f"  - Bio issues: {len(quality_issues)}")
    print("=" * 60)

if __name__ == "__main__":
    generate_report()