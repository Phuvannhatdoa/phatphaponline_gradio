#!/usr/bin/env python3
"""
ETL Script: Populate FTS5 index places_search_fts
Bảng FTS5 places_search_fts (cột name_vi, name_zh, dila_id) đã tạo sẵn trong lineage.db
nhưng index đang RỖNG — khiến ô tìm kiếm ID phải dùng LIKE full-scan (~2-11s) gây
"Máy chủ phản hồi chậm (Timeout)".

Script này populate index 1 lần từ namevi_map_places (~4-5s cho 118K dòng).
Idempotent: nếu index đã có dữ liệu thì không chạy lại (trừ khi dùng --force).

Cách chạy:
    python scripts/build_places_search_fts.py
    python scripts/build_places_search_fts.py --force   # build lại dù đã có
"""

import sqlite3
import os
import time
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

def build_pending_fts(conn, force):
    """Populate places_pending_fts (FTS thường, lưu nội dung) từ places_pending."""
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='places_pending_fts'"
    ).fetchone()
    if not exists:
        conn.execute("CREATE VIRTUAL TABLE places_pending_fts USING fts5(id, name_vi, name_zh, name_vi_norm)")
        conn.commit()
    doc_count = conn.execute("SELECT COUNT(*) FROM places_pending_fts").fetchone()[0]
    src_count = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]
    if not force and doc_count >= max(1, src_count // 100):
        print(f"✅ places_pending_fts đã có dữ liệu (docs={doc_count}, nguồn={src_count}).")
        return
    print(f"🔄 Populate places_pending_fts từ places_pending ({src_count} dòng)...")
    t0 = time.time()
    # Bảng FTS thường (lưu nội dung) KHÔNG dùng được 'delete-all' — phải DELETE FROM trước khi nạp lại.
    conn.execute("DELETE FROM places_pending_fts")
    conn.commit()
    conn.execute(
        "INSERT INTO places_pending_fts(id, name_vi, name_zh, name_vi_norm) "
        "SELECT id, COALESCE(name_vi, ''), COALESCE(name_zh, ''), COALESCE(name_vi_norm, '') "
        "FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != ''"
    )
    conn.commit()
    new_count = conn.execute("SELECT COUNT(*) FROM places_pending_fts").fetchone()[0]
    print(f"✅ Done trong {time.time()-t0:.1f}s. docs={new_count} dòng.")

def build(force=False):
    """Populate places_search_fts + places_pending_fts nếu rỗng (hoặc force)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places_search_fts'"
        ).fetchone()
        if not exists:
            print("❌ Chưa có bảng places_search_fts trong lineage.db.")
            return 1

        src_count = conn.execute("SELECT COUNT(*) FROM namevi_map_places").fetchone()[0]
        idx_count = conn.execute("SELECT COUNT(*) FROM places_search_fts_docsize").fetchone()[0]

        if not force and idx_count >= max(1, src_count // 100):
            print(f"✅ places_search_fts đã có dữ liệu (idx={idx_count}, nguồn={src_count}).")
        else:
            print(f"🔄 Populate places_search_fts từ namevi_map_places ({src_count} dòng)...")
            t0 = time.time()
            if force:
                # Rebuild sạch: xoá toàn bộ index cũ rồi nạp lại (rowid cố định nên không được INSERT trùng)
                try:
                    conn.execute("INSERT INTO places_search_fts(places_search_fts) VALUES('delete-all')")
                    conn.commit()
                except Exception as e:
                    print(f"⚠️ delete-all bỏ qua: {e}")
            conn.execute(
                "INSERT INTO places_search_fts(places_search_fts, rowid, name_vi, name_zh, dila_id) "
                "SELECT NULL, id, name_vi, name_zh, dila_id FROM namevi_map_places WHERE name_vi IS NOT NULL"
            )
            conn.commit()
            new_idx = conn.execute("SELECT COUNT(*) FROM places_search_fts_idx").fetchone()[0]
            print(f"✅ Done trong {time.time()-t0:.1f}s. idx={new_idx} dòng.")

        build_pending_fts(conn, force)
        return 0
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    force = "--force" in sys.argv
    sys.exit(build(force))
