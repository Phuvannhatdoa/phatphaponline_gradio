#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T470 PHASE 1 — dry-run reconcile: DILA extracted JSON vs data/lineage.db.

CHỈ ĐỌC. Không ghi DB dưới mọi hình thức (mở sqlite3 ở mode=ro).
Không có cờ --apply. Đây là script dry-run duy nhất cho PHASE 1.

Đọc từng file `A<dila_id>.json` trong
`daoanh/data/dila_import/extracted/` theo generator (os.scandir), KHÔNG nạp hết
49.487 file vào RAM cùng lúc (Zero-RAM rule — AGENTS.md).

Để tránh hàng trăm nghìn query SQLite rời rạc (1 query/field/file), các bảng
DB liên quan (nhỏ, vài chục nghìn dòng — xem log "DB preload counts") được
nạp một lần thành dict tra cứu theo `dila_id`/`person_id`. Đây KHÔNG phải vi
phạm Zero-RAM: luật đó nói về *raw scripture files* (JSON trích xuất 49.487
file), không phải vài bảng chỉ-mục nhỏ của DB.

Với mỗi trường trong JSON, phân loại:
  - KHỚP            : JSON và DB có giá trị và khớp (so khớp chuỗi/substring)
  - DB_THIEU        : JSON có giá trị nhưng DB không có cột/bảng tương ứng,
                       hoặc có bảng nhưng không có dòng nào cho ID này
  - KHAC_GIA_TRI    : JSON và DB đều có giá trị nhưng khác nhau
  - JSON_TRONG      : JSON không có giá trị cho trường này (không đánh giá DB)

Bảng/cột tương ứng (audit thủ công từ schema thật, xem log):
  dynasty            -> people.dynasty
  concise_bio        -> people.bio
  places_of_origin   -> person_origin_link.place_id JOIN places_dila.name_zh
                        (QUAN TRỌNG: KHÔNG phải bảng `places` — `places.id` dùng
                        numbering khác, 8 ký tự, ví dụ 'PL000000'; còn
                        `person_origin_link.place_id` / `nexus_events.place_dila_id`
                        dùng DILA ID gốc 14 ký tự, ví dụ 'PL000000055425', khớp với
                        `places_dila.id` — đã verify 0 orphan FK khi join đúng bảng
                        này, xem báo cáo mục "Phát hiện bất thường")
  works_in_tripitaka -> dila_catalog_contributors.person_id JOIN
                        dila_catalog_works.cbeta_id (title_zh)
  cbeta_citations    -> cbeta_person_mentions.dila_person_id (định dạng khác
                        hoàn toàn JSON — xem ghi chú trong hàm so sánh)
  wikidata_qid       -> KHÔNG CÓ bảng person-wikidata nào trong DB (đã audit:
                        geo_cross_ref.dila_id chỉ dùng cho PLACE, không dùng
                        cho PERSON) -> luôn DB_THIEU khi JSON có giá trị
  birth_death_dates  -> people.birth_year / people.death_year (chỉ year, JSON
                        có range ngày — so sánh theo year trích từ range)
  active_at_places   -> nexus_events.person_dila_id JOIN
                        places_dila.name_zh (qua place_dila_id, xem ghi chú ở
                        places_of_origin)
  xml_sha256         -> codex_person_name.xml_sha256

`extracted_at` và `source` KHÔNG được đối chiếu — đây là metadata của quá
trình trích xuất JSON (không phải dữ liệu tiểu sử), không có cột DB tương
ứng và không nằm trong phạm vi "DB có đủ thông tin tiểu sử hay chưa" của
T470. Bỏ qua có ghi chú rõ trong log, không âm thầm.

Output:
  docs/sessions/2026-10-26/dila_json_reconcile.csv   (1 dòng / dila_id / field)
  docs/sessions/2026-10-26/dila_json_reconcile.log   (thống kê tổng hợp)
"""

import sys
import io
import os
import re
import csv
import json
import sqlite3
import pathlib
import datetime

# Force utf-8 stdio regardless of Windows codepage.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
DAOANH_ROOT = HERE.parent
EXTRACTED_DIR = DAOANH_ROOT / "data" / "dila_import" / "extracted"
DB_PATH = DAOANH_ROOT / "data" / "lineage.db"
SESSION_DIR = DAOANH_ROOT / "docs" / "sessions" / "2026-10-26"
CSV_PATH = SESSION_DIR / "dila_json_reconcile.csv"
LOG_PATH = SESSION_DIR / "dila_json_reconcile.log"

FIELDS = [
    "dynasty",
    "concise_bio",
    "places_of_origin",
    "works_in_tripitaka",
    "cbeta_citations",
    "wikidata_qid",
    "birth_death_dates",
    "active_at_places",
    "xml_sha256",
]
SKIPPED_FIELDS = ["extracted_at", "source"]

KHOP = "KHOP"
DB_THIEU = "DB_THIEU"
KHAC_GIA_TRI = "KHAC_GIA_TRI"
JSON_TRONG = "JSON_TRONG"


def log(msg, fh=None):
    print(msg)
    if fh:
        fh.write(msg + "\n")


def open_ro(db_path):
    uri = pathlib.Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def preview(v, n=160):
    if v is None:
        return ""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", " ").replace("\r", " ")
    return s[:n]


def norm(s):
    if s is None:
        return ""
    return re.sub(r"\s+", "", str(s)).strip()


def extract_year(range_str):
    """'+1631-01-01 ~ +1631-12-31' -> 1631 ; '-0200-01-01 ~ -0200-12-31' -> -200.
    BUG DA SUA (2026-10-26, vong 2): regex cu (\\d{3,4}) khong bat dau '-' nen
    nam TCN (Truoc Cong Nguyen) bi phan loai nham thanh KHOP khi so sanh voi
    gia tri duong da ghi sai trong DB. Gio bat ca dau +/- ngay truoc chuoi so,
    tra ve so am cho nam TCN — logic phan loai (KHOP/DB_THIEU/KHAC_GIA_TRI)
    khong doi, chi doi cach doc nam tu chuoi JSON."""
    if not range_str:
        return None
    m = re.search(r"([+-]?\d{3,4})", str(range_str))
    return int(m.group(1)) if m else None


def load_db_indexes(con, log_fh):
    """Preload các bảng nhỏ liên quan thành dict tra cứu theo id.
    KHÔNG tải toàn bộ DB — chỉ các cột cần, vài chục nghìn dòng tổng cộng."""
    cur = con.cursor()
    idx = {}

    cur.execute("SELECT id, dynasty, bio, birth_year, death_year FROM people")
    rows = cur.fetchall()
    idx["people"] = {r[0]: {"dynasty": r[1], "bio": r[2],
                             "birth_year": r[3], "death_year": r[4]} for r in rows}
    log(f"  preload people: {len(rows)} dong", log_fh)

    # QUAN TRONG: place_id trong person_origin_link / nexus_events dung DILA ID
    # goc 14 ky tu (vd 'PL000000055425'), KHONG khop voi `places.id` (8 ky tu,
    # numbering khac). Da verify: join dung voi `places_dila.id` -> 0 orphan FK.
    cur.execute("SELECT id, name_zh FROM places_dila")
    place_name = {r[0]: r[1] for r in cur.fetchall()}
    log(f"  preload places_dila (dung id scheme voi person_origin_link/nexus_events): {len(place_name)} dong", log_fh)

    cur.execute("SELECT person_id, place_id FROM person_origin_link")
    origin = {}
    for person_id, place_id in cur.fetchall():
        origin.setdefault(person_id, []).append(place_name.get(place_id) or place_id)
    idx["origin"] = origin
    log(f"  preload person_origin_link: {sum(len(v) for v in origin.values())} dong -> {len(origin)} person_id", log_fh)

    cur.execute("SELECT person_id, cbeta_id FROM dila_catalog_contributors")
    contrib = {}
    for person_id, cbeta_id in cur.fetchall():
        contrib.setdefault(person_id, []).append(cbeta_id)
    idx["contrib"] = contrib
    log(f"  preload dila_catalog_contributors: {len(contrib)} person_id", log_fh)

    cur.execute("SELECT cbeta_id, title_zh FROM dila_catalog_works")
    works_title = {r[0]: r[1] for r in cur.fetchall()}
    idx["works_title"] = works_title
    log(f"  preload dila_catalog_works: {len(works_title)} dong", log_fh)

    cur.execute("SELECT dila_person_id, cbeta_text_sigla FROM cbeta_person_mentions")
    mentions = {}
    for pid, sigla in cur.fetchall():
        if pid:
            mentions.setdefault(pid, set()).add(sigla or "")
    idx["mentions"] = mentions
    log(f"  preload cbeta_person_mentions: {len(mentions)} person_id", log_fh)

    cur.execute("SELECT dila_id, xml_sha256 FROM codex_person_name")
    idx["xml_sha256"] = {r[0]: r[1] for r in cur.fetchall()}
    log(f"  preload codex_person_name: {len(idx['xml_sha256'])} dong", log_fh)

    cur.execute("SELECT person_dila_id, place_dila_id FROM nexus_events")
    active = {}
    for pid, place_id in cur.fetchall():
        if pid:
            active.setdefault(pid, []).append(place_name.get(place_id) or place_id)
    idx["active"] = active
    log(f"  preload nexus_events: {sum(len(v) for v in active.values())} dong -> {len(active)} person_id", log_fh)

    return idx


def classify_dynasty(json_val, idx, pid):
    items = [x for x in (json_val or []) if x]
    if not items:
        return JSON_TRONG, preview(json_val), ""
    person = idx["people"].get(pid)
    db_val = person["dynasty"] if person else None
    if not db_val or not norm(db_val):
        return DB_THIEU, preview(items), preview(db_val)
    db_n = norm(db_val)
    if any(norm(x) and (norm(x) in db_n or db_n in norm(x)) for x in items):
        return KHOP, preview(items), preview(db_val)
    return KHAC_GIA_TRI, preview(items), preview(db_val)


def classify_bio(json_val, idx, pid):
    if not json_val or not norm(json_val):
        return JSON_TRONG, preview(json_val), ""
    person = idx["people"].get(pid)
    db_val = person["bio"] if person else None
    if not db_val or not norm(db_val):
        return DB_THIEU, preview(json_val), preview(db_val)
    jn, dn = norm(json_val), norm(db_val)
    if jn == dn or jn in dn or dn in jn:
        return KHOP, preview(json_val), preview(db_val)
    return KHAC_GIA_TRI, preview(json_val), preview(db_val)


def classify_name_list(json_val, idx, pid, key):
    items = [x for x in (json_val or []) if x]
    if not items:
        return JSON_TRONG, preview(json_val), ""
    db_items = idx[key].get(pid) or []
    if not db_items:
        return DB_THIEU, preview(items), ""
    db_set = {norm(x) for x in db_items if x}
    if any(norm(x) and any(norm(x) in d or d in norm(x) for d in db_set) for x in items):
        return KHOP, preview(items), preview(db_items)
    return KHAC_GIA_TRI, preview(items), preview(db_items)


def classify_works(json_val, idx, pid):
    items = [x for x in (json_val or []) if x]
    if not items:
        return JSON_TRONG, preview(json_val), ""
    cbeta_ids = idx["contrib"].get(pid) or []
    if not cbeta_ids:
        return DB_THIEU, preview(items), ""
    db_titles = {norm(idx["works_title"].get(c)) for c in cbeta_ids if idx["works_title"].get(c)}
    if not db_titles:
        return DB_THIEU, preview(items), preview(cbeta_ids)
    if any(any(t and t in norm(x) for t in db_titles) for x in items):
        return KHOP, preview(items), preview(sorted(db_titles))
    return KHAC_GIA_TRI, preview(items), preview(sorted(db_titles))


def classify_cbeta_citations(json_val, idx, pid):
    """cbeta_citations JSON dùng định dạng '( CBETA X35n0652_p0254a05 ) <tên>'.
    DB cbeta_person_mentions chỉ lưu text_sigla (vd 'X35n0652'), không lưu
    passage locator đầy đủ -> không bao giờ coi là KHỚP đầy đủ; chỉ phân biệt
    DB có dấu vết sigla trùng hay hoàn toàn không có gì."""
    items = [x for x in (json_val or []) if x]
    if not items:
        return JSON_TRONG, preview(json_val), ""
    siglas = idx["mentions"].get(pid) or set()
    if not siglas:
        return DB_THIEU, preview(items), ""
    sigla_n = {norm(s) for s in siglas if s}
    if any(s and any(s in norm(x) for x in items) for s in sigla_n):
        return KHAC_GIA_TRI, preview(items), preview(sorted(siglas))  # co sigla trung nhung format khac -> van khac gia tri
    return DB_THIEU, preview(items), preview(sorted(siglas))


def classify_wikidata_qid(json_val, idx, pid):
    if not json_val:
        return JSON_TRONG, preview(json_val), ""
    # Khong co bang person-wikidata nao trong DB (da audit geo_cross_ref la PLACE-only).
    return DB_THIEU, preview(json_val), "(khong co bang person-wikidata trong DB)"


def classify_birth_death(json_val, idx, pid):
    bd = json_val or {}
    jb, jd = extract_year(bd.get("birth")), extract_year(bd.get("death"))
    if jb is None and jd is None:
        return JSON_TRONG, preview(json_val), ""
    person = idx["people"].get(pid)
    db_b = person["birth_year"] if person else None
    db_d = person["death_year"] if person else None
    missing = (jb is not None and db_b is None) or (jd is not None and db_d is None)
    mismatch = (jb is not None and db_b is not None and jb != db_b) or \
               (jd is not None and db_d is not None and jd != db_d)
    preview_db = preview({"birth_year": db_b, "death_year": db_d})
    if missing:
        return DB_THIEU, preview(json_val), preview_db
    if mismatch:
        return KHAC_GIA_TRI, preview(json_val), preview_db
    return KHOP, preview(json_val), preview_db


def classify_xml_sha256(json_val, idx, pid):
    if not json_val:
        return JSON_TRONG, preview(json_val), ""
    db_val = idx["xml_sha256"].get(pid)
    if not db_val:
        return DB_THIEU, preview(json_val), ""
    if norm(json_val) == norm(db_val):
        return KHOP, preview(json_val), preview(db_val)
    return KHAC_GIA_TRI, preview(json_val), preview(db_val)


def classify_record(data, idx):
    pid = data.get("dila_id")
    out = {}
    out["dynasty"] = classify_dynasty(data.get("dynasty"), idx, pid)
    out["concise_bio"] = classify_bio(data.get("concise_bio"), idx, pid)
    out["places_of_origin"] = classify_name_list(data.get("places_of_origin"), idx, pid, "origin")
    out["works_in_tripitaka"] = classify_works(data.get("works_in_tripitaka"), idx, pid)
    out["cbeta_citations"] = classify_cbeta_citations(data.get("cbeta_citations"), idx, pid)
    out["wikidata_qid"] = classify_wikidata_qid(data.get("wikidata_qid"), idx, pid)
    out["birth_death_dates"] = classify_birth_death(data.get("birth_death_dates"), idx, pid)
    out["active_at_places"] = classify_name_list(data.get("active_at_places"), idx, pid, "active")
    out["xml_sha256"] = classify_xml_sha256(data.get("xml_sha256"), idx, pid)
    return out


def iter_json_files(extracted_dir):
    """Generator — KHONG doc het 49.487 file vao list truoc."""
    with os.scandir(extracted_dir) as it:
        for entry in it:
            if entry.is_file() and entry.name.endswith(".json"):
                yield entry.path


def main():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now()

    with open(LOG_PATH, "w", encoding="utf-8") as log_fh:
        log(f"=== T470 PHASE1 dry-run reconcile — {started.isoformat()} ===", log_fh)
        log(f"EXTRACTED_DIR = {EXTRACTED_DIR}", log_fh)
        log(f"DB_PATH       = {DB_PATH} (mode=ro)", log_fh)
        log(f"CSV_PATH      = {CSV_PATH}", log_fh)
        log(f"Fields compared: {FIELDS}", log_fh)
        log(f"Fields skipped (no DB-mappable biographical meaning): {SKIPPED_FIELDS}", log_fh)

        if not EXTRACTED_DIR.is_dir():
            log(f"LOI: khong tim thay thu muc {EXTRACTED_DIR}", log_fh)
            sys.exit(1)
        if not DB_PATH.is_file():
            log(f"LOI: khong tim thay DB {DB_PATH}", log_fh)
            sys.exit(1)

        con = open_ro(DB_PATH)
        log("Mo DB thanh cong o mode=ro (chi doc).", log_fh)
        idx = load_db_indexes(con, log_fh)

        people_ids = set(idx["people"].keys())

        total_files = 0
        parse_errors = []
        person_not_in_db = 0
        field_stats = {f: {KHOP: 0, DB_THIEU: 0, KHAC_GIA_TRI: 0, JSON_TRONG: 0} for f in FIELDS}

        with open(CSV_PATH, "w", encoding="utf-8", newline="") as csv_fh:
            writer = csv.writer(csv_fh)
            writer.writerow(["dila_id", "field", "classification", "json_value_preview", "db_value_preview"])

            for path in iter_json_files(EXTRACTED_DIR):
                total_files += 1
                try:
                    with open(path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                except Exception as e:
                    parse_errors.append((path, str(e)))
                    continue

                pid = data.get("dila_id") or pathlib.Path(path).stem
                if pid not in people_ids:
                    person_not_in_db += 1

                results = classify_record(data, idx)
                for field, (cls, jprev, dprev) in results.items():
                    field_stats[field][cls] += 1
                    writer.writerow([pid, field, cls, jprev, dprev])

                if total_files % 5000 == 0:
                    log(f"  ... da xu ly {total_files} file", log_fh)

        finished = datetime.datetime.now()
        log("", log_fh)
        log("=== THONG KE TONG HOP ===", log_fh)
        log(f"Tong so file JSON da xu ly: {total_files}", log_fh)
        log(f"So file loi parse: {len(parse_errors)}", log_fh)
        for p, e in parse_errors[:50]:
            log(f"  LOI PARSE: {p} -> {e}", log_fh)
        log(f"So dila_id trong JSON KHONG co trong bang people: {person_not_in_db}", log_fh)
        log("", log_fh)
        log(f"{'FIELD':22} {'KHOP':>8} {'DB_THIEU':>10} {'KHAC_GT':>10} {'JSON_TRONG':>11}", log_fh)
        for f in FIELDS:
            s = field_stats[f]
            log(f"{f:22} {s[KHOP]:>8} {s[DB_THIEU]:>10} {s[KHAC_GIA_TRI]:>10} {s[JSON_TRONG]:>11}", log_fh)
        log("", log_fh)
        log(f"Thoi gian chay: {finished - started}", log_fh)
        log(f"CSV: {CSV_PATH}", log_fh)
        log(f"LOG: {LOG_PATH}", log_fh)
        log("DRY-RUN ONLY — khong co thay doi nao duoc ghi vao lineage.db.", log_fh)

        con.close()


if __name__ == "__main__":
    main()
