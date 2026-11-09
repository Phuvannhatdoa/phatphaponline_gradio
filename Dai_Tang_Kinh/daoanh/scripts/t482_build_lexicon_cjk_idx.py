#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T482 perf fix (QA đo thực tế curl: trang chưa truy cập 7.9-13.9s/trang, 2026-10-28).

Root cause THẬT (đã xác minh bằng curl + EXPLAIN QUERY PLAN, không phải benchmark
hàm cô lập): JOIN SQL của /daoanh/api/places/catalog đã có index đủ (dila_id là PK
ở namevi_map_places/codex_place_name/ai_place_name) nên bản thân query rất nhanh
(COUNT ~0.6s, SELECT 1 trang ~0.04s — đo bằng EXPLAIN QUERY PLAN + time.time() trực
tiếp trên data/lineage.db). Bottleneck THẬT nằm ở `_t482_dictionary_lookup`
(routes_places.py, bản T482 trước): hàm này nạp TOÀN BỘ 166.278 dòng `lexicon` vào
1 list Python + build 2 dict Python (_T482_EXACT_IDX, _T482_BIGRAM_IDX) **trong RAM
của tiến trình Flask**, chỉ 1 lần/đời tiến trình — nhưng chi phí build đó (~10-37s
đo thực tế, tuỳ máy) cộng với chi phí query (~0.5-1s) khớp đúng khoảng QA đo được
mỗi khi admin/QA RESTART server rồi test "trang chưa truy cập" (môi trường dev này
restart app.py rất thường xuyên khi đang sửa file khác — xem AGENTS.md §17). Vi
phạm Zero-RAM Principle (AGENTS.md §2): không được nạp toàn bộ dữ liệu lớn vào RAM
mỗi lần tiến trình khởi động lại; phải dùng index SQL bền (persist trong DB, không
mất khi restart).

Fix: thêm 2 cột `term_ns`/`def_ns` (CJK đã bỏ khoảng trắng OCR) vào `lexicon` +
1 bảng phụ `lexicon_cjk_bigram` (bigram Hán liên tục trong def_ns -> lexicon_id),
build 1 LẦN DUY NHẤT qua migration này (không build lại mỗi lần server start).
routes_places.py sau đó tra bằng SQL (WHERE term_ns IN (...) / bigram IN (...)),
KHÔNG còn nạp 166K dòng vào RAM Python nữa — tốc độ không phụ thuộc restart.

Idempotent: --dry-run (mặc định an toàn, không ghi) / --apply (build, bỏ qua dòng
đã có term_ns nếu không --force) / --revert (DROP cột + bảng phụ, KHÔNG đổi dữ liệu
gốc term/definition/source). Tự backup DB trước --apply/--revert (sqlite backup API).

Usage:
    python -X utf8 scripts/t482_build_lexicon_cjk_idx.py --dry-run
    python -X utf8 scripts/t482_build_lexicon_cjk_idx.py --apply
    python -X utf8 scripts/t482_build_lexicon_cjk_idx.py --apply --force   # rebuild lại từ đầu
    python -X utf8 scripts/t482_build_lexicon_cjk_idx.py --revert
"""
import argparse
import os
import re
import sqlite3
import sys
import time
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "lineage.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backups")

_WS_RE = re.compile(r"\s+")
_CJK_RUN_RE = re.compile(r"[㐀-䶿一-鿿]+")

BATCH_COMMIT_EVERY = 2000  # Zero-RAM: commit theo lô, không giữ hết thay đổi trong 1 transaction khổng lồ


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def backup_db(label):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"lineage_{ts}_{label}.db")
    src_conn = sqlite3.connect(DB_PATH)
    dst_conn = sqlite3.connect(dest)
    with dst_conn:
        src_conn.backup(dst_conn)
    src_conn.close()
    dst_conn.close()
    print(f"Backup: {dest}")
    return dest


def _has_column(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def _has_table(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def dry_run(conn):
    n_lexicon = conn.execute("SELECT COUNT(*) FROM lexicon").fetchone()[0]
    has_term_ns = _has_column(conn, "lexicon", "term_ns")
    has_bigram_tbl = _has_table(conn, "lexicon_cjk_bigram")
    n_done = conn.execute("SELECT COUNT(*) FROM lexicon WHERE term_ns IS NOT NULL").fetchone()[0] if has_term_ns else 0
    n_bigram_rows = conn.execute("SELECT COUNT(*) FROM lexicon_cjk_bigram").fetchone()[0] if has_bigram_tbl else 0
    print("=== DRY-RUN T482 lexicon CJK index ===")
    print(f"lexicon: {n_lexicon:,} dòng")
    print(f"Cột term_ns/def_ns đã tồn tại: {has_term_ns}")
    print(f"Bảng lexicon_cjk_bigram đã tồn tại: {has_bigram_tbl}")
    print(f"Dòng đã có term_ns (đã index hoá): {n_done:,} / {n_lexicon:,}")
    print(f"Số dòng bigram hiện có: {n_bigram_rows:,}")
    if n_done < n_lexicon:
        print(f"Cần build thêm cho {n_lexicon - n_done:,} dòng (--apply).")
    else:
        print("Đã build đủ — --apply (không --force) sẽ không làm gì thêm.")


def apply(conn, force=False):
    cur = conn.cursor()
    if not _has_column(conn, "lexicon", "term_ns"):
        cur.execute("ALTER TABLE lexicon ADD COLUMN term_ns TEXT")
    if not _has_column(conn, "lexicon", "def_ns"):
        cur.execute("ALTER TABLE lexicon ADD COLUMN def_ns TEXT")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_term_ns ON lexicon(term_ns)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS lexicon_cjk_bigram (bigram TEXT NOT NULL, lexicon_id INTEGER NOT NULL)"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_cjk_bigram ON lexicon_cjk_bigram(bigram)")
    conn.commit()

    if force:
        cur.execute("UPDATE lexicon SET term_ns = NULL, def_ns = NULL")
        cur.execute("DELETE FROM lexicon_cjk_bigram")
        conn.commit()

    # Generator: đọc từng dòng qua cursor, KHÔNG fetchall() toàn bảng vào list (Zero-RAM).
    t0 = time.time()
    n_updated = 0
    n_bigram_inserted = 0
    read_cur = conn.execute(
        "SELECT id, term, definition FROM lexicon WHERE term_ns IS NULL"
    )
    while True:
        rows = read_cur.fetchmany(BATCH_COMMIT_EVERY)
        if not rows:
            break
        for r in rows:
            lid = r["id"]
            term_ns = _WS_RE.sub("", r["term"] or "")
            def_ns = _WS_RE.sub("", r["definition"] or "")
            cur.execute(
                "UPDATE lexicon SET term_ns = ?, def_ns = ? WHERE id = ?",
                (term_ns, def_ns, lid),
            )
            seen_bg = set()
            for run in _CJK_RUN_RE.findall(def_ns):
                for j in range(len(run) - 1):
                    seen_bg.add(run[j : j + 2])
            if seen_bg:
                cur.executemany(
                    "INSERT INTO lexicon_cjk_bigram (bigram, lexicon_id) VALUES (?, ?)",
                    [(bg, lid) for bg in seen_bg],
                )
                n_bigram_inserted += len(seen_bg)
            n_updated += 1
        conn.commit()
        print(f"  ...{n_updated:,} dòng, {n_bigram_inserted:,} bigram ({time.time()-t0:.1f}s)")

    print("=== APPLY T482 lexicon CJK index ===")
    print(f"Đã index {n_updated:,} dòng mới, {n_bigram_inserted:,} bigram, {time.time()-t0:.1f}s")
    n_total_done = conn.execute("SELECT COUNT(*) FROM lexicon WHERE term_ns IS NOT NULL").fetchone()[0]
    print(f"Tổng đã index: {n_total_done:,} / {conn.execute('SELECT COUNT(*) FROM lexicon').fetchone()[0]:,}")


def revert(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS lexicon_cjk_bigram")
    cur.execute("DROP INDEX IF EXISTS idx_lexicon_cjk_bigram")
    cur.execute("DROP INDEX IF EXISTS idx_lexicon_term_ns")
    if _has_column(conn, "lexicon", "term_ns"):
        cur.execute("ALTER TABLE lexicon DROP COLUMN term_ns")
    if _has_column(conn, "lexicon", "def_ns"):
        cur.execute("ALTER TABLE lexicon DROP COLUMN def_ns")
    conn.commit()
    print("Đã revert: DROP bảng lexicon_cjk_bigram + cột term_ns/def_ns (term/definition/source gốc KHÔNG đổi).")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--revert", action="store_true")
    ap.add_argument("--force", action="store_true", help="Xoá term_ns/def_ns/bigram cũ, build lại từ đầu")
    args = ap.parse_args()

    conn = connect()
    try:
        if args.dry_run:
            dry_run(conn)
        elif args.apply:
            backup_db("lexicon_cjk_idx")
            apply(conn, force=args.force)
        elif args.revert:
            backup_db("lexicon_cjk_idx_revert")
            revert(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
