# -*- coding: utf-8 -*-
"""
T445 — DRY-RUN đối chiếu phiên âm địa danh "Claude" (vn_place_name_vi.xml)
với các nguồn hiện có trong daoanh/data/lineage.db:

  - Gemini  : bảng ai_place_name (cột name_vi_ai)
  - Từ điển : bảng namevi_map_places (cột name_vi)

KHÔNG GHI DB. Script này chỉ SELECT (kết nối mode=ro thật). Không có
CREATE/ALTER/INSERT/UPDATE/DELETE nào được thực thi. Flag --apply tồn tại
chỉ để khớp UX CLI tương lai — khi truyền, script in cảnh báo và DỪNG,
không làm gì khác.

Nguồn XML:
  https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/
      claude/sleepy-tesla-qsx17b/data/phien_am/vn_place_name_vi.xml

Cấu trúc XML thực tế (đã xác minh bằng xml.etree, 2026-10-21):
  <vn_place_authority_name_vi ...>
    <place dila_id="PL..." tier="1|2|3|4">
      <name_zh>...</name_zh>
      <name_vi>...</name_vi>
      <category_zh>...</category_zh>      (optional)
      <district_zh>...</district_zh>      (optional)
      <district_vi>...</district_vi>      (optional)
      <review>...</review>                (optional, tier 3 thường có)
      <alternatives>...</alternatives>    (optional)
    </place>
    ...
  </vn_place_authority_name_vi>

GHI CHU QUAN TRONG ve ID (xac minh 2026-10-21, doc truoc khi dung lai script):
  - Bang `places.id` dung dang NGAN (8 ky tu, vd "PL000009") — day la ID noi
    bo cua lop hop nhat/curated, KHONG phai dila_id goc.
  - Bang `places_dila.id` dung dang DAY (14 ky tu, vd "PL000000000009") —
    day moi la DILA Place Authority ID goc, khop 1-1 voi `dila_id` trong
    XML cua Claude, voi `ai_place_name.dila_id` (Gemini), voi
    `namevi_map_places.dila_id` (Tu dien) va voi `codex_district_name.dila_id`.
  - Vi vay script nay doi chieu "co trong DB" bang bang `places_dila`
    (59167 dong), KHONG dung bang `places` (59161 dong, ID khac namespace).
    Neu doi chieu nham bang `places.id` se ra 100% "ID moi" (sai).

Schema hiện có trong DB (tham khảo để KHÔNG đụng vào):
  - ai_place_name(dila_id TEXT PRIMARY KEY, name_vi_ai TEXT, model TEXT,
        created_at TEXT)                         -- Gemini, đã có
  - codex_district_name(dila_id TEXT PRIMARY KEY, name_zh TEXT, name_vi TEXT,
        type TEXT, tier TEXT, review TEXT, alternatives TEXT, tier_zh TEXT,
        xml_sha256 TEXT, model TEXT, status TEXT, created_at TEXT)
                                                   -- district, đã có
  - namevi_map_places(id INTEGER PK, name_vi, name_zh, dila_id, confidence,
        source, created_at, needs_review, note_vi, gps_lat, gps_long,
        source_id, district_vi, country_vi, vn_name_status)
                                                   -- Từ điển nội bộ, đã có
  - claude_place_name                              -- CHƯA TỒN TẠI.

Đề xuất schema cho lần import thật sau này (CHƯA tạo, chỉ ghi lại ở đây để
Admin duyệt trước khi áp dụng, theo mẫu codex_district_name):

  CREATE TABLE claude_place_name (
      dila_id      TEXT PRIMARY KEY,
      name_zh      TEXT,
      name_vi      TEXT,
      tier         INTEGER,
      source       TEXT,
      imported_at  TEXT
  );

Rollback dự kiến cho lần --apply thật (CHƯA thực hiện ở đây):
  1. Backup trước khi ghi:
       copy data\\lineage.db data\\lineage.db.bak_<YYYYMMDD_HHMMSS>
  2. Nếu cần hủy sau khi tạo bảng:
       DROP TABLE claude_place_name;
  3. Ghi lại đường dẫn backup + lệnh revert vào daoanh/docs/ROLLBACK.md
     (chưa làm ở dry-run này vì chưa ghi DB thật).

Usage:
    python -X utf8 scripts/import_claude_place_name_dryrun.py
    python -X utf8 scripts/import_claude_place_name_dryrun.py --xml-path <local.xml>
    python -X utf8 scripts/import_claude_place_name_dryrun.py --apply   # sẽ chỉ in cảnh báo, KHÔNG làm gì
"""

import argparse
import csv
import glob
import os
import sqlite3
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

XML_URL = (
    "https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/"
    "claude/sleepy-tesla-qsx17b/data/phien_am/vn_place_name_vi.xml"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAOANH_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(DAOANH_DIR, "data", "lineage.db")
REPORT_DIR = os.path.join(DAOANH_DIR, "docs", "sessions", "2026-10-21")
REPORT_CSV = os.path.join(REPORT_DIR, "claude_place_name_dryrun.csv")

TIER_WARN = {"3", "4"}  # tier 3/4 = độ tin cậy thấp hơn, cần cảnh báo riêng

MUST_SAMPLE_IDS = ["PL000000000009", "PL000000000019"]


def fetch_xml_bytes(explicit_path=None):
    """Lấy nội dung XML: ưu tiên network, fallback %TEMP%, fallback đường dẫn
    local do người dùng chỉ định. KHÔNG ghi gì vào DB ở bước này."""
    if explicit_path:
        if not os.path.isfile(explicit_path):
            raise SystemExit(f"[LOI] Khong tim thay file XML local: {explicit_path}")
        with open(explicit_path, "rb") as f:
            return f.read(), f"local:{explicit_path}"

    try:
        req = urllib.request.Request(XML_URL, headers={"User-Agent": "T445-dryrun"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            if data:
                return data, f"network:{XML_URL}"
    except Exception as exc:  # noqa: BLE001 - muốn fallback cho mọi lỗi mạng
        print(f"[CANH BAO] Khong tai duoc qua network ({type(exc).__name__}: {exc}). "
              f"Thu tim ban da tai trong %TEMP%...", file=sys.stderr)

    temp_dir = tempfile.gettempdir()
    candidates = sorted(
        glob.glob(os.path.join(temp_dir, "**", "vn_place_name_vi.xml"), recursive=True),
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    if candidates:
        chosen = candidates[0]
        with open(chosen, "rb") as f:
            return f.read(), f"temp_cache:{chosen}"

    raise SystemExit(
        "[LOI] Khong tai duoc XML qua network va khong tim thay ban cache trong "
        f"%TEMP% ({temp_dir}). Vui long cung cap duong dan local bang "
        "--xml-path <file.xml>."
    )


def parse_places(xml_bytes):
    root = ET.fromstring(xml_bytes)
    entries = []
    for p in root.findall("place"):
        dila_id = p.get("dila_id")
        tier = p.get("tier")
        name_zh_el = p.find("name_zh")
        name_vi_el = p.find("name_vi")
        review_el = p.find("review")
        alt_el = p.find("alternatives")
        entries.append({
            "dila_id": dila_id,
            "tier": tier,
            "name_zh": name_zh_el.text if name_zh_el is not None else None,
            "name_vi": name_vi_el.text if name_vi_el is not None else None,
            "review": review_el.text if review_el is not None else None,
            "alternatives": alt_el.text if alt_el is not None else None,
        })
    return entries


def open_db_readonly(db_path):
    if not os.path.isfile(db_path):
        raise SystemExit(f"[LOI] Khong tim thay DB: {db_path}")
    uri = f"file:{db_path.replace(os.sep, '/')}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def load_db_maps(con):
    cur = con.cursor()

    # Dung bang places_dila (ID day, dung namespace voi dila_id trong XML),
    # KHONG dung bang places (ID ngan, namespace noi bo khac - xem docstring).
    cur.execute("SELECT id FROM places_dila")
    places_ids = {r["id"] for r in cur.fetchall()}

    cur.execute("SELECT dila_id, name_vi_ai FROM ai_place_name")
    gemini_map = {r["dila_id"]: r["name_vi_ai"] for r in cur.fetchall()}

    # namevi_map_places co the co nhieu dong cho 1 dila_id -> lay dong moi nhat
    cur.execute(
        "SELECT dila_id, name_vi, created_at FROM namevi_map_places "
        "WHERE dila_id IS NOT NULL ORDER BY created_at ASC"
    )
    namevi_map = {}
    for r in cur.fetchall():
        namevi_map[r["dila_id"]] = r["name_vi"]  # dong sau de len dong truoc = moi nhat thang

    return places_ids, gemini_map, namevi_map


def norm(s):
    return (s or "").strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-path", default=None, help="Duong dan XML local (bo qua network/temp cache).")
    parser.add_argument(
        "--apply", action="store_true",
        help="CHUA IMPLEMENT. Truyen co nay se chi in canh bao va dung, khong ghi gi vao DB.",
    )
    args = parser.parse_args()

    if args.apply:
        print(
            "[CANH BAO] --apply chua duoc implement. Day la script DRY-RUN, "
            "khong co flag nao ghi DB thuc su. Dung lai, khong lam gi them.",
            file=sys.stderr,
        )
        return 0

    xml_bytes, xml_source = fetch_xml_bytes(args.xml_path)
    entries = parse_places(xml_bytes)

    con = open_db_readonly(DB_PATH)
    try:
        places_ids, gemini_map, namevi_map = load_db_maps(con)
    finally:
        con.close()

    total = len(entries)
    seen_ids = {}
    duplicate_ids = set()
    missing_dila_id = 0

    for e in entries:
        did = e["dila_id"]
        if not did:
            missing_dila_id += 1
            continue
        if did in seen_ids:
            duplicate_ids.add(did)
        seen_ids[did] = seen_ids.get(did, 0) + 1

    rows = []
    n_in_db_places = 0
    n_new_id = 0
    n_diff_gemini = 0
    n_diff_namevi = 0
    n_tier_warn = 0

    for e in entries:
        did = e["dila_id"]
        name_zh = e["name_zh"]
        name_vi_claude = norm(e["name_vi"])
        tier = e["tier"]

        in_places_db = bool(did and did in places_ids)
        if in_places_db:
            n_in_db_places += 1
        is_new_id = bool(did) and not in_places_db
        if is_new_id:
            n_new_id += 1

        gemini_val = gemini_map.get(did) if did else None
        namevi_val = namevi_map.get(did) if did else None

        diff_gemini = bool(gemini_val) and norm(gemini_val) != name_vi_claude
        diff_namevi = bool(namevi_val) and norm(namevi_val) != name_vi_claude
        if diff_gemini:
            n_diff_gemini += 1
        if diff_namevi:
            n_diff_namevi += 1

        is_dup = did in duplicate_ids
        tier_warn = tier in TIER_WARN
        if tier_warn:
            n_tier_warn += 1

        rows.append({
            "dila_id": did,
            "name_zh": name_zh,
            "name_vi_claude": name_vi_claude,
            "tier": tier,
            "in_db_places_dila": in_places_db,
            "gemini_value": gemini_val,
            "namevi_map_value": namevi_val,
            "flag_duplicate_in_xml": is_dup,
            "flag_new_id_not_in_db": is_new_id,
            "flag_diff_vs_gemini": diff_gemini,
            "flag_diff_vs_namevi_map": diff_namevi,
            "flag_tier_warning": tier_warn,
            "review_note": e["review"],
            "alternatives": e["alternatives"],
        })

    os.makedirs(REPORT_DIR, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "dila_id", "name_zh", "name_vi_claude", "tier", "in_db_places_dila",
        "gemini_value", "namevi_map_value", "flag_duplicate_in_xml",
        "flag_new_id_not_in_db", "flag_diff_vs_gemini", "flag_diff_vs_namevi_map",
        "flag_tier_warning", "review_note", "alternatives",
    ]
    with open(REPORT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print("=" * 70)
    print("T445 DRY-RUN — doi chieu phien am dia danh Claude (KHONG ghi DB)")
    print("=" * 70)
    print(f"Nguon XML          : {xml_source}")
    print(f"DB (read-only)     : {DB_PATH}")
    print(f"Bao cao CSV        : {REPORT_CSV}")
    print("-" * 70)
    print(f"Tong so entry XML            : {total}")
    print(f"Thieu dila_id                : {missing_dila_id}")
    print(f"Duplicate dila_id trong XML  : {len(duplicate_ids)}")
    print(f"Co trong DB places_dila (DILA authority) : {n_in_db_places}")
    print(f"ID hoan toan moi (khong co trong places_dila): {n_new_id}")
    print(f"Khac voi Gemini (ai_place_name)             : {n_diff_gemini}")
    print(f"Khac voi Tu dien (namevi_map_places)        : {n_diff_namevi}")
    print(f"Tier 3/4 (canh bao do tin cay thap)         : {n_tier_warn}")
    print("-" * 70)
    print("Xac nhan schema hien co:")
    print("  - ai_place_name       : CO (Gemini)")
    print("  - codex_district_name : CO (district, nguon Claude truoc day)")
    print("  - claude_place_name   : CHUA CO (chi la de xuat, chua tao)")
    print("-" * 70)

    print("10 dong mau (uu tien PL000000000009, PL000000000019, va vai dong tier 3/4):")
    by_id = {r["dila_id"]: r for r in rows}
    sample = []
    for want in MUST_SAMPLE_IDS:
        if want in by_id:
            sample.append(by_id[want])
    tier34 = [r for r in rows if r["flag_tier_warning"] and r["dila_id"] not in MUST_SAMPLE_IDS]
    sample.extend(tier34[:4])
    for r in rows:
        if len(sample) >= 10:
            break
        if r not in sample:
            sample.append(r)

    for r in sample[:10]:
        print(
            f"  {r['dila_id']} | tier={r['tier']} | name_zh={r['name_zh']} | "
            f"name_vi_claude={r['name_vi_claude']} | gemini={r['gemini_value']} | "
            f"namevi_map={r['namevi_map_value']} | diff_gemini={r['flag_diff_vs_gemini']} | "
            f"diff_namevi={r['flag_diff_vs_namevi_map']} | tier_warn={r['flag_tier_warning']}"
        )

    print("=" * 70)
    print("KHONG co thay doi nao duoc ghi vao lineage.db (chi SELECT, ket noi mode=ro).")
    print("Rollback du kien khi apply thuc su (xem docstring dau file):")
    print(r"  copy data\lineage.db data\lineage.db.bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    print("  DROP TABLE claude_place_name;  -- neu can huy sau khi tao")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
