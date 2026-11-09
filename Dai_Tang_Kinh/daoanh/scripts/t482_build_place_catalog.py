#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T482 — Tạo bảng additive `place_catalog` (danh mục địa danh DILA đầy đủ, 59.373 dòng)
và nạp dữ liệu, dùng cho Tab "Catalog" trong admin/namevimap.html.

Nguồn canonical (12 chữ số, theo T477):
  - places_dila.id              (59.167 dòng)
  - dila_place_authority.place_id (206 dòng — bộ mới nạp thêm, KHÔNG trùng places_dila)

KHÔNG đổi/xoá bất kỳ dòng nào trong places_dila / namevi_map_places / dila_place_authority.
place_catalog CHỈ là bảng tổng hợp khoá canonical, phục vụ liệt kê — mọi dữ liệu Claude/
Gemini/Từ điển/name_vi hiện tại vẫn JOIN SỐNG từ bảng gốc khi trả API (không denormalize,
tránh lệch dữ liệu khi admin Pass/Sửa ở Tab Place).

Usage:
    python -X utf8 scripts/t482_build_place_catalog.py --dry-run
    python -X utf8 scripts/t482_build_place_catalog.py --apply
    python -X utf8 scripts/t482_build_place_catalog.py --revert
"""
import argparse
import sqlite3
import sys
import datetime

DB_PATH = "data/lineage.db"

DDL = """
CREATE TABLE IF NOT EXISTS place_catalog (
    place_id      TEXT PRIMARY KEY,   -- canonical 12-digit: 'PL' + 12 số
    name_zh       TEXT,
    source_table  TEXT NOT NULL,      -- 'places_dila' | 'dila_place_authority'
    created_at    TEXT NOT NULL
);
"""

DDL_INDEX = """
CREATE INDEX IF NOT EXISTS idx_place_catalog_source ON place_catalog(source_table);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dry_run(conn):
    n_pd = conn.execute("SELECT COUNT(*) FROM places_dila").fetchone()[0]
    n_auth = conn.execute("SELECT COUNT(*) FROM dila_place_authority").fetchone()[0]
    overlap = conn.execute("""
        SELECT COUNT(*) FROM dila_place_authority a
        JOIN places_dila p ON p.id = a.place_id
    """).fetchone()[0]
    total_expected = n_pd + n_auth - overlap

    has_catalog = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='place_catalog'"
    ).fetchone() is not None
    existing = conn.execute("SELECT COUNT(*) FROM place_catalog").fetchone()[0] if has_catalog else 0

    # Phân bổ Claude/Gemini/Dictionary coverage (chỉ đếm, không ghi)
    n_claude = conn.execute("SELECT COUNT(*) FROM codex_place_name").fetchone()[0]
    n_gemini = conn.execute("SELECT COUNT(*) FROM ai_place_name").fetchone()[0]
    n_namevi = conn.execute("SELECT COUNT(*) FROM namevi_map_places").fetchone()[0]

    print("=== DRY-RUN place_catalog (T482) ===")
    print(f"places_dila:            {n_pd:,}")
    print(f"dila_place_authority:    {n_auth:,}")
    print(f"overlap (trùng id):      {overlap:,}")
    print(f"TỔNG DỰ KIẾN place_catalog: {total_expected:,}  (mục tiêu đề bài: 59.373)")
    print(f"place_catalog đã có sẵn: {existing:,} (bảng {'đã tồn tại' if has_catalog else 'chưa tạo'})")
    print(f"codex_place_name (Claude, toàn DB): {n_claude:,}")
    print(f"ai_place_name (Gemini, toàn DB):     {n_gemini:,}")
    print(f"namevi_map_places (name_vi hiện tại, toàn DB): {n_namevi:,}")
    if total_expected != 59373:
        print(f"*** CHÚ Ý: tổng dự kiến {total_expected} KHÁC 59.373 — xem report để biết nguyên nhân.")
    return total_expected


def apply(conn):
    cur = conn.cursor()
    cur.execute(DDL)
    cur.execute(DDL_INDEX)

    before = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='place_catalog'"
    ).fetchone()
    n_before = cur.execute("SELECT COUNT(*) FROM place_catalog").fetchone()[0]

    now = datetime.datetime.now().isoformat(timespec="seconds")

    cur.execute("BEGIN")
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO place_catalog (place_id, name_zh, source_table, created_at)
            SELECT id, name_zh, 'places_dila', ?
            FROM places_dila
            """,
            (now,),
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO place_catalog (place_id, name_zh, source_table, created_at)
            SELECT place_id, name_zh, 'dila_place_authority', ?
            FROM dila_place_authority
            WHERE place_id NOT IN (SELECT id FROM places_dila)
            """,
            (now,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    n_after = cur.execute("SELECT COUNT(*) FROM place_catalog").fetchone()[0]
    by_source = cur.execute(
        "SELECT source_table, COUNT(*) c FROM place_catalog GROUP BY source_table"
    ).fetchall()

    print("=== APPLY place_catalog (T482) ===")
    print(f"Trước: {n_before:,} dòng")
    print(f"Sau:   {n_after:,} dòng")
    for r in by_source:
        print(f"  {r['source_table']}: {r['c']:,}")
    if n_after != 59373:
        print(f"*** CHÚ Ý: n_after={n_after} KHÁC 59.373 — ghi rõ nguyên nhân vào report.")
    return n_after


def revert(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS place_catalog")
    conn.commit()
    print("Đã DROP TABLE place_catalog (revert).")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    conn = connect()
    try:
        if args.dry_run:
            dry_run(conn)
        elif args.apply:
            apply(conn)
        elif args.revert:
            revert(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
