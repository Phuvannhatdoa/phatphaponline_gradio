#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T132 P5 — Seed conflict_pending từ namevi_map_places (spec §9)
==============================================================
Seed NHỎ data THẬT (không fake): sample place-mapping đang chờ duyệt
(`namevi_map_places.needs_review=1`) ghi vào `conflict_pending` cho
human-in-the-loop review.

- Ánh xạ mỗi dòng:
    entity_ref = dila_id (PL…)
    field      = 'name_vi'
    value_a    = name_zh  (chữ Hán từ bản ghi DILA)      source_a = source_code (JOIN data_sources theo source_id, fallback 'DILA')
    value_b    = name_vi  ( ứng viên tiếng Việt auto-transliterate)  source_b = 'ZQLOCAL'  (dữ liệu sinh tại chỗ, staging namevi_map_places)
    notes      = 'namevi_map_places id=<id> confidence=<c> method=auto_transliterate needs_review=1 (T132 P5 seed)'
- Cột `notes` được ADD COLUMN nullable (idempotent) nếu thiếu — additive, 0 destructive.
  (gate/conflict_recorder.py đã kiểm tra 'notes' in cols trước khi INSERT.)
- Idempotent: chạy lại → ConflictRecorder bỏ qua duplicate (SELECT-first).
- Rollback: --revert xóa đúng các dòng seed qua marker '(T132 P5 seed)' trong notes.

Usage (từ thư mục daoanh/):
  python -X utf8 scripts/seed_t132_conflict_pending.py --stats
  python -X utf8 scripts/seed_t132_conflict_pending.py --apply [--limit 20]
  python -X utf8 scripts/seed_t132_conflict_pending.py --revert
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gate.conflict_recorder import ConflictRecorder  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "lineage.db")
SEED_MARKER = "(T132 P5 seed)"
DEFAULT_LIMIT = 20

CANDIDATE_SQL = """
    SELECT id, dila_id, name_zh, name_vi, source_id, confidence
    FROM namevi_map_places
    WHERE needs_review = 1
      AND dila_id IS NOT NULL AND TRIM(dila_id) <> ''
      AND name_vi  IS NOT NULL AND TRIM(name_vi)  <> ''
      AND name_zh  IS NOT NULL AND TRIM(name_zh)  <> ''
    ORDER BY id
    LIMIT ?
"""


def ensure_notes_col(conn: sqlite3.Connection) -> bool:
    """ADD COLUMN notes TEXT nếu chưa có (additive, idempotent). Trả True nếu vừa thêm."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(conflict_pending)")}
    if "notes" in cols:
        return False
    conn.execute("ALTER TABLE conflict_pending ADD COLUMN notes TEXT")
    conn.commit()
    return True


def resolve_source_codes(conn: sqlite3.Connection) -> dict:
    """Map data_sources.source_id -> source_code (fallback: {})."""
    return dict(conn.execute("SELECT source_id, source_code FROM data_sources"))


def build_conflicts(conn: sqlite3.Connection, limit: int) -> list:
    codes = resolve_source_codes(conn)
    out = []
    for row_id, dila_id, name_zh, name_vi, source_id, confidence in conn.execute(
            CANDIDATE_SQL, (limit,)):
        source_a = codes.get(source_id, "DILA")
        notes = (
            f"namevi_map_places id={row_id} "
            f"confidence={confidence if confidence is not None else 'NULL'} "
            f"method=auto_transliterate needs_review=1 {SEED_MARKER}"
        )
        out.append({
            "entity_ref": dila_id,
            "field": "name_vi",
            "value_a": name_zh,
            "value_b": name_vi,
            "source_a": source_a,
            "source_b": "ZQLOCAL",
            "notes": notes,
        })
    return out


def cmd_stats(conn: sqlite3.Connection) -> None:
    total = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE needs_review=1"
    ).fetchone()[0]
    cand = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE needs_review=1 "
        "AND dila_id IS NOT NULL AND TRIM(dila_id)<>'' "
        "AND name_vi IS NOT NULL AND TRIM(name_vi)<>'' "
        "AND name_zh IS NOT NULL AND TRIM(name_zh)<>''"
    ).fetchone()[0]
    cols = {r[1] for r in conn.execute("PRAGMA table_info(conflict_pending)")}
    has_notes = "notes" in cols
    seeded = conn.execute(
        f"SELECT COUNT(*) FROM conflict_pending WHERE "
        + ("notes LIKE ?" if has_notes else "1=0"),
        (f"%{SEED_MARKER}%",),
    ).fetchone()[0]
    all_rows = conn.execute("SELECT COUNT(*) FROM conflict_pending").fetchone()[0]
    print(f"namevi_map_places.needs_review=1 : {total}")
    print(f"ứng viên seed (đủ PL+zh+vi)     : {cand}")
    print(f"conflict_pending tổng / đã seed  : {all_rows} / {seeded}")
    print(f"cột notes có sẵn                 : {'yes' if has_notes else 'no (sẽ ADD khi --apply)'}")


def cmd_apply(conn: sqlite3.Connection, limit: int) -> int:
    added = ensure_notes_col(conn)
    if added:
        print("Đã ADD COLUMN notes TEXT vào conflict_pending (additive, nullable).")
    conflicts = build_conflicts(conn, limit)
    if not conflicts:
        print("Không có ứng viên seed — không làm gì.")
        return 0
    print(f"Ứng viên seed (limit={limit}): {len(conflicts)} dòng")
    rec = ConflictRecorder(db_path=DB_PATH)
    inserted = rec.record_many(conflicts)
    print(f"INSERT mới: {inserted} · đã tồn tại (bỏ qua): {len(conflicts) - inserted}")
    after = conn.execute(
        "SELECT COUNT(*) FROM conflict_pending WHERE notes LIKE ?",
        (f"%{SEED_MARKER}%",),
    ).fetchone()[0]
    print(f"Tổng seed hiện tại trong conflict_pending: {after}")
    print("OK — human-in-loop: status='pending', needs_review=1, resolved_*=NULL.")
    return inserted


def cmd_revert(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        "DELETE FROM conflict_pending WHERE notes LIKE ?", (f"%{SEED_MARKER}%",)
    )
    conn.commit()
    print(f"Đã xóa {cur.rowcount} dòng seed (marker {SEED_MARKER}).")
    print("Lưu ý: cột notes (additive) giữ nguyên — không DROP (0 destructive).")
    return cur.rowcount


def main() -> int:
    ap = argparse.ArgumentParser(description="T132 P5 seed conflict_pending từ namevi_map_places")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stats", action="store_true", help="chỉ in thống kê, không ghi")
    g.add_argument("--apply", action="store_true", help="seed (idempotent)")
    g.add_argument("--revert", action="store_true", help="xóa đúng dòng seed qua marker")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help=f"số dòng seed tối đa (mặc định {DEFAULT_LIMIT})")
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"LỖI: không tìm thấy DB: {DB_PATH}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        if args.stats:
            cmd_stats(conn)
        elif args.apply:
            cmd_apply(conn, args.limit)
        else:
            cmd_revert(conn)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
