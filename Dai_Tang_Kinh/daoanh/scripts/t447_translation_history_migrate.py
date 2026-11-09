# -*- coding: utf-8 -*-
"""
T447 — Minimal migration: thêm cột history_json vào translation_cache.

Mục đích: nút "Dịch lại" của admin cần giữ bản dịch cũ lại trong lịch sử
(không xoá) trước khi ghi đè. Vì translation_cache có UNIQUE(source_hash,
source_type), không thể giữ nhiều row cho cùng khoá — history_json (TEXT,
JSON array) lưu các bản dịch đã bị "Dịch lại" thay thế, append-only.

Additive-only (ADD COLUMN, nullable) — KHÔNG đổi dữ liệu hiện có.
Backup tự động trước khi ALTER. Rollback: DROP COLUMN history_json
(SQLite >= 3.35 hỗ trợ trực tiếp) hoặc revert từ file backup.

Dùng:
    python -X utf8 scripts/t447_translation_history_migrate.py --dry-run
    python -X utf8 scripts/t447_translation_history_migrate.py --apply
    python -X utf8 scripts/t447_translation_history_migrate.py --revert
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'lineage.db')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'docs', 'sessions', datetime.now().strftime('%Y-%m-%d'), 'T447')


def _has_col(conn, table, col):
    return any(r[1] == col for r in conn.execute(f'PRAGMA table_info({table})').fetchall())


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    has = _has_col(conn, 'translation_cache', 'history_json')

    if args.dry_run:
        print(f"[DRY-RUN] translation_cache.history_json đã tồn tại: {has}")
        if not has:
            print("[DRY-RUN] Sẽ chạy: ALTER TABLE translation_cache ADD COLUMN history_json TEXT")
        conn.close()
        return

    if args.revert:
        if not has:
            print("[REVERT] Cột history_json không tồn tại — không cần revert.")
            conn.close()
            return
        try:
            conn.execute('ALTER TABLE translation_cache DROP COLUMN history_json')
            conn.commit()
            print("[REVERT] Đã DROP COLUMN history_json (SQLite >= 3.35).")
        except sqlite3.OperationalError as e:
            print(f"[REVERT] DROP COLUMN thất bại ({e}). Khôi phục từ bản backup DB thủ công thay vào đó.")
            sys.exit(1)
        conn.close()
        return

    # --apply
    if has:
        print("[APPLY] Cột history_json đã tồn tại — không cần migrate (idempotent).")
        conn.close()
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, 'lineage.db.bak-T447-history_json')
    conn.close()  # đóng trước khi copy file để tránh đọc nửa WAL
    shutil.copy2(DB_PATH, backup_path)
    print(f"[APPLY] Backup DB: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute('ALTER TABLE translation_cache ADD COLUMN history_json TEXT')
    conn.commit()
    conn.close()
    print("[APPLY] Đã ALTER TABLE translation_cache ADD COLUMN history_json TEXT.")
    print(f"[APPLY] Rollback: python -X utf8 scripts/t447_translation_history_migrate.py --revert")
    print(f"[APPLY] Hoặc khôi phục file backup: {backup_path}")


if __name__ == '__main__':
    main()
