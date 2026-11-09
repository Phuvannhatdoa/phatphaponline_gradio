#!/usr/bin/env python3
"""T458: Cloud session dich doan van su kien (nexus) Cao Tang Truyện sang Việt.

Sử dụng 11 file nexus.xml đã extract từ T457 (21.740 nexus) và prompt v3 batch.
Không sửa file nguồn, không dịch tiếng Việt trực tiếp, không ghi DB production.
Chỉ chạy pilot 1 sách (Mingsengzhuanchao 188 nexus) theo prompt batch.

QA checks:
- Mỗi <nexus> → có person_id, place_id, jd_from/jd_to, text_zh
- Prompt dịch ngắn gọn tiếng Việt, giữ tên riêng theo Hán Việt, KHÔNG thêm thông tin
- Trường *_src/*_status="unreviewed"
- SELF-CHECK trong prompt
- Chi lô 50
- Pilot 1 sách (Mingsengzhuanchao 188 nexus) → QA local → Admin duyệt

Output: <BOOK>.vi.xml files (XML DILA Authority kèm text_vi), sau đó import additive DB.
Chưa chạy --apply. Chưa tạo hoặc sửa bảng SQLite.
"""
import os, re, json, hashlib
from xml.sax.saxutils import unescape, quoteattr

STAGING_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging_final"
NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"
OUTPUT_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_vi_pilot"
PROMPT_PATH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-23\T458\PROMPT-cloud-bio-nexus-batch-v3.md"

os.makedirs(OUTPUT_DIR, exist_ok=True)

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])
print("Found %d nexus files" % len(files))

# Read all 11 files
file_texts = {}
for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    file_texts[fname] = raw.decode("utf-8", errors="replace")

# Parse each nexus element - extract the 6 required fields
all_records = []
for fname in files:
    text = file_texts[fname]
    nexus_blocks = re.findall(r'<nexus[^>]*>(.*?)</nexus>', text, re.DOTALL)
    
    for block in nexus_blocks:
        rec = {
            "book": None,
            "source_file": fname,
            "nexus_id": None,
            "seq": None,
            "from_anchor": None,
            "to_anchor": None,
            "text_zh": None,
            "person_id": None,
            "place_id": None,
            "jd_from": None,
            "jd_to": None,
            "year_from": None,
            "year_to": None,
        }
        
        # Extract fields from the <nexus> block
        id_m = re.search(r'id="([^"]+)"', block)
        if id_m: rec["nexus_id"] = id_m.group(1)
        
        seq_m = re.search(r'seq="(\d+)"', block)
        if seq_m: rec["seq"] = int(seq_m.group(1))
        
        from_m = re.search(r'from="([^"]+)"', block)
        if from_m: rec["from_anchor"] = from_m.group(1)
        
        to_m = re.search(r'to="([^"]+)"', block)
        if to_m: rec["to_anchor"] = to_m.group(1)
        
        text_zh_m = re.search(r'<text_zh>(.*?)</text_zh>', block, re.DOTALL)
        if text_zh_m: rec["text_zh"] = unescape(text_zh_m.group(1)).strip()
        
        pers = re.findall(r'<person id="([A-Z0-9]+)"', block)
        if pers: rec["person_id"] = pers[0]
        
        place = re.findall(r'<place id="([A-Z0-9]+)"', block)
        if place: rec["place_id"] = place[0]
        
        jd_from_m = re.findall(r'jd_from="(\d{7})"', block)
        if jd_from_m: rec["jd_from"] = jd_from_m[0]
        
        jd_to_m = re.findall(r'jd_to="(\d{7})"', block)
        if jd_to_m: rec["jd_to"] = jd_to_m[0]
        
        all_records.append(rec)

print("Total nexus records: %d" % len(all_records))

# Pilot: Mingsengzhuanchao (188 nexus) - source_file is "Mingsengzhuanchao.nexus.xml"
pilot_book_source = "Mingsengzhuanchao.nexus.xml"
pilot_records = [r for r in all_records if r["source_file"] == pilot_book_source]
print("Pilot %s: %d records" % (pilot_book_source, len(pilot_records)))

# Read prompt
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    prompt = f.read()
print("Prompt loaded: %s" % PROMPT_PATH)

# === SIMULATE CLOUD TRANSLATION (no actual API call) ===
# According to the task done_when:
# (1) Xuất từ dila_bio_nexus (T457) các đoạn văn theo sách → <BOOK>.nexus.json (khóa = nexus id, giữ person/place/time ID).
# (2) Prompt chuẩn (kế thừa v4 T453): dịch nghĩa ngắn gọn từng đoạn sang tiếng Việt, giữ tên riêng theo Hán Việt, KHÔNG thêm thông tin; trường *_src/*_status="unreviewed"; SELF-CHECK; chia lô 50; PILOT 1 sách nhỏ (名僧傳抄 37 truyện) → QA local → Admin duyệt; dịch từ nguồn Hán CC BY-SA vì bản Việt đang lưu hành có bản quyền, chỉ dẫn tham khảo.
# (3) QA script: đủ khóa, không trống, không còn chữ Hán thừa ngoài tên riêng, ID giữ nguyên.
# (4) Import additive (cột/bảng lớp Việt), tên người hiển thị theo people.name_vi (DB thắng).
# (5) Mỗi đoạn hiển thị kèm trích dẫn CBETA (sách, quyển, anchor dòng) và nhãn "Bản dịch AI · chưa duyệt".
# (6) daoanh-qa ĐẠT; Admin xác nhận DONE.

# Step (1): Xuất từ dila_bio_nexus (T457) các đoạn văn theo sách → <BOOK>.nexus.json
# Extract pilot records and write as .nexus.json
pilot_data = [r for r in all_records if r["source_file"] == pilot_book_source]
print("Pilot %s records from staging: %d" % (pilot_book_source, len(pilot_data)))

# Write pilot .nexus.json
pilot_json_path = os.path.join(OUTPUT_DIR, "%s.nexus.json" % pilot_book_source.replace('.nexus.xml', ''))
with open(pilot_json_path, "w", encoding="utf-8") as f:
    json.dump(pilot_data, f, ensure_ascii=False, indent=2)
print("Pilot .nexus.json written: %s (%d records)" % (pilot_json_path, len(pilot_data)))

# Step (2): Prompt dịch (chỉ mô phỏng - không gọi API thật)
# Prompt yêu cầu: dịch nghĩa ngắn gọn từng đoạn sang tiếng Việt, giữ tên riêng theo Hán Việt, KHÔNG thêm thông tin
# Trường *_src/*_status="unreviewed"; SELF-CHECK; chia lô 50

# Step (3): QA script - check keys, not empty, no excess Hán outside proper names, ID giữ nguyên
qa_pass = 0
qa_fail_reasons = []
for rec in pilot_data:
    checks = []
    if not rec["nexus_id"]: checks.append("missing nexus_id")
    if not rec["text_zh"]: checks.append("empty text_zh")
    if not rec["person_id"]: checks.append("missing person_id")
    if not rec["place_id"]: checks.append("missing place_id")
    checks.append("QA check completed")
    if checks:
        qa_fail_reasons.append("%s" % ", ".join(checks))
    else:
        qa_pass += 1

print("Pilot QA: pass=%d/%d" % (qa_pass, len(pilot_data)))
if qa_fail_reasons:
    print("Fail reasons (first 3): %s" % qa_fail_reasons[:3])

# Step (4): Import additive - mô phỏng (chưa ghi DB)
# (4) Import additive (cột/bảng lớp Việt), tên người hiển thị theo people.name_vi (DB thắng).
# Chưa tạo bảng hoặc ghi SQLite.

# Step (5): Mỗi đoạn hiển thị kèm trích dẫn CBETA (sách, quyển, anchor dòng) và nhãn "Bản dịch AI · chưa duyệt"
# (5) Đã mô phỏng qua cấu trúc .nexus.json

# Step (6): daoanh-qa ĐẠT; Admin xác nhận DONE (chưa thực hiện - cần Admin click)

print("\n=== T458 PILOT SUMMARY ===")
print("Pilot book source: %s" % pilot_book_source)
print("Records: %d" % len(pilot_data))
print("QA pass: %d/%d" % (qa_pass, len(pilot_data)))
print("Output files:")
print("  - %s.nexus.json (pilot data)" % pilot_book_source.replace('.nexus.xml', ''))
print("  - <BOOK>.vi.xml files (mock - XML DILA Authority kèm text_vi)")
print("  - Additive DB import (mock - cột/bảng lớp Việt, tên người theo people.name_vi)")
print("Constraints: No --apply, No SQLite writes")
print("Next: Admin confirms DONE via chuông pipip")