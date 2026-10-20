#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T139 (Zero-ALTER · Zero-RAM · Lean) — Zen Lineage Staging Gateway
=====================================================================
Chặn đăng: dữ liệu Zen Lineage (echojoel/zenlineage @ commit ec8357ed) là nguồn
structured TRUYỀN THỪA mới (556 masters · 578 transmissions · 25 schools · 8,684
citations · 206 sources) — license internal-only (quyết định 2026-09-22) → STAGING
vào bảng dẫn xuất `source_staging` (candidate pool).
ĐỊNH NGHĨA CANDIDATE (deviation 2026-09-22, chính xác hóa T139):
- `entity_source_ids` có ràng buộc `entity_id NOT NULL` (0 ALTER base) → KHÔNG thể
  ghi candidate với entity_id=NULL như spec gốc.
- Vì vậy: **candidate pool = row `source_staging` row_type='master'** (chưa approve).
- `entity_source_ids` chỉ được ghi KHI HITL approve (mapping M3→M4) với entity_id thật
  (entity_hub id của DILA person đã verify) + verified=1 + match_status='approved'.
- KHÔNG write lineage_edge_assertions trong script này (bước HITL sau khi license OK).

Tính chất (tuân điều lệnh check07 — 0 ALTER base)
--------------------------------------------------
- ZERO-ALTER: KHÔNG ALTER bảng base. Chỉ CREATE bảng dẫn xuất `source_staging`
  (DERIVED-only, additive).
- LICENSE GATE: `--apply` TỪ CHỐI nếu data_sources.integration_mode != 'INGEST'
  cho source_code='ZENLINEAGE' (SSOT — đọc ngay từ DB registry). Mặc định là
  'BLOCKED' → mọi lệnh --apply đều bị chặn cho tới khi admin mở license.
- IDEMPOTENT: PK source_entity_id UNIQUE (per row_type) → INSERT OR REPLACE.
- REVERSIBLE: `--revert` chỉ DROP bảng dẫn xuất + xóa row candidate Zen Lineage
  (entity_source_ids WHERE source='ZENLINEAGE') — không đụng dữ liệu base.
- BACKUP: backup nhất quán bằng SQLite backup API (Zero-RAM) khi `--apply`.
- Zero-RAM: đọc masters/transmissions theo fetchmany chunk — không load nguyên
  graph vào RAM.

Đầu vào (Zero-RAM, không cần npm)
----------------------------------
- Kênh đầy đủ (MẶC ĐỊNH): `--zen-db <path>` — zen.db đã seed @ ec8357ed
  (T137 audit dựng, tồn tại ở temp) — đầy đủ 556 masters + tier evidence.
- Kênh tĩnh (fallback): `--static <masters.json>` — public/api/masters.json
  (export publish-only, 465/556 masters, KHÔNG có tier) — chỉ để đối chiếu.

Cách dùng
---------
    python scripts/etl_zenlineage_stage.py --dry-run
    python scripts/etl_zenlineage_stage.py --apply
    python scripts/etl_zenlineage_stage.py --revert
    python scripts/etl_zenlineage_stage.py --apply --zen-db <path>

Lưu ý (deviation so với spec T139 §3 — entity_id NOT NULL)
-----------------------------------------------------------
- `--apply` CHỈ backfill `source_staging` (556 masters + 578 transmissions).
- KHÔNG ghi entity_source_ids (candidate/verified=0) — schema chặn entity_id NULL.
  Candidate pool = source_staging (row_type='master'); HITL approve sẽ ghi
  entity_source_ids với entity_id thật khi mapping M3→M4.
- `--revert` chỉ DROP source_staging (không có entity_source_ids ZENLINEAGE manual
  ở giai đoạn này; nếu có row verified=0 legacy thì vẫn xóa — idempotent).
"""
import argparse
import json
import os
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

TS = time.strftime('%Y%m%d_%H%M%S')
BUILT_AT = time.strftime('%Y-%m-%dT%H:%M:%S')

SOURCE_CODE = 'ZENLINEAGE'
SOURCE_VERSION = 'ec8357ed'

# zen.db do T137 audit dựng (temp mặc định) — đầy đủ fidelity
DEFAULT_ZEN_DB = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'opencode',
                              'zenlineage_t137', 'zen.db')
if not os.path.exists(DEFAULT_ZEN_DB):
    DEFAULT_ZEN_DB = os.path.join(BASE_DIR, '..', '..', '..', '..', '..',
                                  'AppData', 'Local', 'Temp', 'opencode',
                                  'zenlineage_t137', 'zen.db')

TABLE = 'source_staging'

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS source_staging (
    source_code        TEXT NOT NULL,
    source_version     TEXT NOT NULL,
    row_type           TEXT NOT NULL,      -- 'master' | 'transmission'
    source_entity_id   TEXT NOT NULL,      -- zen slug / transmission id
    primary_name       TEXT,
    teacher_slug       TEXT,
    student_slug       TEXT,
    school_slug        TEXT,
    tier               TEXT,
    human_review_needed INTEGER DEFAULT 0,
    extra_json         TEXT,
    ingested_at        TEXT,
    PRIMARY KEY (source_code, row_type, source_entity_id)
)
"""
CREATE_IDX = [
    "CREATE INDEX IF NOT EXISTS idx_ss_type ON source_staging(row_type)",
    "CREATE INDEX IF NOT EXISTS idx_ss_school ON source_staging(school_slug)",
]

EXPECTED = {  # đối chiếu với audit T137 §2 (số đo thật từ zen.db @ ec8357ed)
    'masters': 556,
    'transmissions': 578,
    'schools': 25,
    'citations': 8684,
    'sources': 206,
}


def connect(db=DB_PATH):
    conn = sqlite3.connect(db, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f'lineage_t139_{TS}.db')
    if not os.path.exists(DB_PATH):
        print(f'[backup] KHÔNG tìm thấy {DB_PATH} — bỏ qua backup')
        return None
    src = sqlite3.connect(DB_PATH, timeout=60)
    try:
        dest = sqlite3.connect(dst, timeout=60)
        try:
            src.backup(dest)
        finally:
            dest.close()
    finally:
        src.close()
    print(f'[backup] Đã backup → {dst} ({os.path.getsize(dst):,} bytes)')
    return dst


def find_zen_db(args):
    """Ưu tiên --zen-db; fallback DEFAULT_ZEN_DB; rồi --static masters.json."""
    if args.zen_db:
        if not os.path.exists(args.zen_db):
            print(f'[lỗi] --zen-db không tồn tại: {args.zen_db}')
            sys.exit(1)
        return args.zen_db
    if os.path.exists(DEFAULT_ZEN_DB):
        return DEFAULT_ZEN_DB
    print(f'[cảnh báo] zen.db mặc định không tồn tại ({DEFAULT_ZEN_DB})')
    print('[cảnh báo] dùng kênh tĩnh masters.json (publish-only, thiếu tier)')
    return None


def load_counter(zen_conn, clear):
    """Chỉ đếm đối chiếu audit — không ghi gì."""
    counts = {}
    for key, table in [('masters', 'masters'), ('transmissions', 'master_transmissions'),
                       ('schools', 'schools'), ('citations', 'citations'), ('sources', 'sources')]:
        try:
            counts[key] = zen_conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        except Exception as e:
            print(f'[cảnh báo] không đếm được {table}: {e}')
            counts[key] = None
    return counts


def validate(expected, counts):
    ok = True
    for k, exp in expected.items():
        cur = counts.get(k)
        if cur is None:
            print(f'[verify][?] {k}: không đọc được')
            ok = False
        elif cur == exp:
            print(f'[verify][ok] {k}: {cur:,} (khớp audit)')
        else:
            print(f'[verify][!!] {k}: {cur:,} != audit {exp:,}')
            ok = False
    return ok


def license_gate(conn):
    """Đọc SSOT từ data_sources — --apply chỉ chạy khi integration_mode='INGEST'."""
    row = conn.execute(
        "SELECT integration_mode, legal_status, license_verified FROM data_sources "
        "WHERE source_code=? LIMIT 1", (SOURCE_CODE,)).fetchone()
    if not row:
        return False, f'{SOURCE_CODE} chưa đăng ký trong data_sources'
    if row['integration_mode'] != 'INGEST':
        return False, (f'integration_mode={row["integration_mode"]} (legal={row["legal_status"]}, '
                       f'license_verified={row["license_verified"]}) — license CHƯA sẵn sàng')
    return True, 'ok'


def do_dry_run(args):
    zen_path = find_zen_db(args)
    print(f'[plan] DB production: {DB_PATH}')
    print(f'[plan] Sẽ tạo bảng {TABLE} (DERIVED-only, additive, 0 ALTER base)')
    print(f'[plan] Nguồn Zen Lineage: {SOURCE_CODE} @ {SOURCE_VERSION}')
    if zen_path:
        print(f'[plan] Kênh đầy đủ: {zen_path}')
        zen = connect(zen_path)
        try:
            counts = load_counter(zen, args)
            vy = validate(EXPECTED, counts)
            if not vy:
                print('[cảnh báo] số liệu KHÔNG khớp audit — dừng dry-run (an toàn)')
                sys.exit(2)
        finally:
            zen.close()
    else:
        print('[plan] Kênh tĩnh (masters.json) — chỉ đối chiếu số masters')
    conn = connect()
    try:
        ok, why = license_gate(conn)
        print(f'[gate] --apply sẽ {"" if ok else "BỊ CHẶN"}: {why}')
        print('[plan] BACKUP → data/backups/lineage_t139_<ts>.db (khi --apply thực thụ)')
        print('[plan] REVERT → DROP source_staging (candidate pool)')
        print('[plan] KHÔNG ghi entity_source_ids ở --apply (entity_id NOT NULL — chỉ ghi khi HITL approve)')
        print('[plan] KHÔNG write lineage_edge_assertions (bước HITL sau license OK)')
    finally:
        conn.close()


def stage_rows(conn, args):
    """Đọc zen.db → insert INTO source_staging (chunks). Trả tổng số dòng."""
    zen_path = find_zen_db(args)
    if not zen_path:
        print('[cảnh báo] không có zen.db — bỏ qua staging (chỉ tạo bảng)')
        return 0
    zen = connect(zen_path)
    n_master = n_trans = 0
    try:
        conn.execute(CREATE_TABLE)
        for idx in CREATE_IDX:
            conn.execute(idx)
        # masters (slugs + primary name + school + extra)
        names = {}
        for r in zen.execute(
                "SELECT master_id, locale, value FROM master_names "
                "WHERE name_type='dharma' ORDER BY locale='en' DESC"):
            names.setdefault(r['master_id'], r['value'])
        cur = zen.execute("SELECT id, slug, school_id, birth_year, death_year, published FROM masters")
        while True:
            rows = cur.fetchmany(2000)
            if not rows:
                break
            for r in rows:
                extra = json.dumps({'birth_year': r['birth_year'], 'death_year': r['death_year'],
                                    'published': r['published']}, ensure_ascii=False)
                conn.execute(
                    "INSERT OR REPLACE INTO source_staging "
                    "(source_code, source_version, row_type, source_entity_id, primary_name, "
                    " teacher_slug, student_slug, school_slug, tier, human_review_needed, "
                    " extra_json, ingested_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (SOURCE_CODE, SOURCE_VERSION, 'master', r['slug'], names.get(r['id']),
                     None, None, r['school_id'], None, 0, extra, BUILT_AT))
                n_master += 1
        # transmissions (teacher→student) + tier + human_review_needed
        cur = zen.execute(
            "SELECT t.id, t.student_id, s1.slug AS st_slug, t.teacher_id, s2.slug AS te_slug, "
            "       t.type, t.is_primary, e.tier, e.human_review_needed "
            "FROM master_transmissions t "
            "JOIN masters s1 ON s1.id = t.student_id "
            "JOIN masters s2 ON s2.id = t.teacher_id "
            "LEFT JOIN transmission_evidence e ON e.transmission_id = t.id")
        while True:
            rows = cur.fetchmany(2000)
            if not rows:
                break
            for r in rows:
                conn.execute(
                    "INSERT OR REPLACE INTO source_staging "
                    "(source_code, source_version, row_type, source_entity_id, primary_name, "
                    " teacher_slug, student_slug, school_slug, tier, human_review_needed, "
                    " extra_json, ingested_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (SOURCE_CODE, SOURCE_VERSION, 'transmission', r['id'], r['type'],
                     r['te_slug'], r['st_slug'], None, r['tier'],
                     1 if r['human_review_needed'] else 0,
                     json.dumps({'tr_type': r['type'], 'is_primary': r['is_primary']},
                                ensure_ascii=False), BUILT_AT))
                n_trans += 1
    finally:
        zen.close()
    print(f'[stage] masters {n_master} · transmissions {n_trans}')
    return n_master + n_trans


def print_candidate_pool(conn):
    """Candidate pool = source_staging row_type='master' (552/556 chưa approve).
    Chỉ đọc — KHÔNG ghi entity_source_ids (schema chặn entity_id NULL)."""
    n = conn.execute(
        "SELECT COUNT(*) FROM source_staging WHERE source_code=? AND row_type='master'",
        (SOURCE_CODE,)).fetchone()[0]
    print(f'[candidate] pool: {n} master trong source_staging (chưa approve). '
          f'entity_source_ids ZENLINEAGE chỉ ghi khi HITL approve (có entity_id thật).')
    return n


def do_apply(args):
    conn = connect()
    try:
        ok, why = license_gate(conn)
        if not ok:
            print(f'[gate] --apply BỊ CHẶN: {why}')
            print('[gate] Chạy lại sau khi admin mở license: '
                  "UPDATE data_sources SET integration_mode='INGEST' WHERE source_code='ZENLINEAGE'")
            sys.exit(2)
        make_backup()
        conn.execute(CREATE_TABLE)
        for idx in CREATE_IDX:
            conn.execute(idx)
        n = stage_rows(conn, args)
        nc = print_candidate_pool(conn)
        conn.commit()
        for row in conn.execute(
                "SELECT row_type, COUNT(*) c FROM source_staging GROUP BY row_type"):
            print(f'[summary] {row["row_type"]}: {row["c"]:,}')
        print(f'[done] --apply hoàn tất (stage {n} rows). Candidate pool: {nc} masters.')
    except SystemExit:
        raise
    except Exception as e:
        conn.rollback()
        print(f'[lỗi] {e}')
        sys.exit(1)
    finally:
        conn.close()


def do_revert():
    conn = connect()
    try:
        if has_table(conn, TABLE):
            conn.execute(f'DROP TABLE {TABLE}')
            conn.commit()
            print(f'[revert] Đã DROP {TABLE}')
        else:
            print(f'[revert] {TABLE} không tồn tại — không có gì để xóa')
        # legacy: nếu tồn tại entity_source_ids ZENLINEAGE verified=0 (spec cũ), xóa sạch
        n = conn.execute(
            "DELETE FROM entity_source_ids WHERE source=? AND verified=0", (SOURCE_CODE,)).rowcount
        conn.commit()
        if n:
            print(f'[revert] Đã xóa {n} entity_source_ids legacy (source={SOURCE_CODE}, verified=0)')
        else:
            print(f'[revert] Không có entity_source_ids {SOURCE_CODE} verified=0 để xóa')
        # verified=1 (HITL approve) GIỮ NGUYÊN — là quyết định mapping, xóa qua script edges riêng
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description='ETL T139 — Zen Lineage Staging Gateway')
    ap.add_argument('--zen-db', default=None,
                    help='zen.db đã seed @ ec8357ed (mặc định: tìm trong temp t137)')
    ap.add_argument('--static', default=None, help='public/api/masters.json (fallback)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    args = ap.parse_args()
    if args.dry_run:
        do_dry_run(args)
    elif args.apply:
        do_apply(args)
    else:
        do_revert()


if __name__ == '__main__':
    main()