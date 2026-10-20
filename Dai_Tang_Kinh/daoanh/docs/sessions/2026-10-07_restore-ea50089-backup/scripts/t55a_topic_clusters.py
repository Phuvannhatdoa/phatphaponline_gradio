# -*- coding: utf-8 -*-
"""
T55a — Topic Clustering CBETA Texts (additive, Zero-RAM).

Phân cụm cbeta_catalog_vn (3,122 texts) theo chủ đề:
  - Genre keywords lấy từ title_vi (Kinh/Luận/Luật/Đà La Ni/Thiền/Lục/Truyện/...)
  - Dynasty (triều đại dịch)
  - Translator (dịch giả)

Bảng mới: cbeta_topic_clusters(text_id, topic, score)
  0 ALTER bảng nền, 0 migration. CREATE TABLE IF NOT EXISTS.
  Revert = DROP TABLE cbeta_topic_clusters (bảng thuần add, không đụng bảng khác).

Zero-RAM: đọc CATALOG theo page (LIMIT/OFFSET --page_size), chỉ giữ các topic
của page hiện tại rồi bulk-insert, không load toàn bộ texts vào RAM.

Usage:
  python scripts/t55a_topic_clusters.py [--db data/lineage.db] [--limit N] [--offset M]
        [--page_size 200] [--drop] [--dry] [--stats]

  --drop : DROP TABLE cbeta_topic_clusters trước khi tạo lại (thường chỉ dùng --dry trước)
  --dry  : chỉ in kế hoạch + đếm, KHÔNG ghi DB
  --stats: in thống kê cuối (count + sample)
"""

import argparse
import io
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# (keyword, canonical topic) — scan title_vi theo thứ tự, topic chuẩn hoá
TOPIC_KEYWORDS = [
    ("Đà La Ni", "Thần Chú"),
    ("Đà-la-ni", "Thần Chú"),
    ("Thần Chú", "Thần Chú"),
    ("Chú", "Thần Chú"),
    ("Luật", "Luật"),
    ("Luận", "Luận"),
    ("Kinh Ưu Bà Đề Xá", "Luận"),
    ("Ưu Bà Đề Xá", "Luận"),
    ("Kinh", "Kinh"),
    ("Lục", "Ngữ Lục"),
    ("Ngữ Lục", "Ngữ Lục"),
    ("Cảnh Đức Truyền Đăng Lục", "Ngữ Lục"),
    ("Truyện", "Truyện Ký"),
    ("Biệt Truyện", "Truyện Ký"),
    ("Thiền", "Thiền"),
    ("Tông Cảnh", "Thiền"),
    ("Tam Muội", "Thiền"),
    ("Niết Bàn", "Niết Bàn"),
    ("Hoa Nghiêm", "Hoa Nghiêm"),
    ("Pháp Hoa", "Pháp Hoa"),
    ("Bát Nhã", "Bát Nhã"),
    ("Duy Ma", "Duy Ma"),
    ("Lăng Nghiêm", "Lăng Nghiêm"),
    ("Kim Cang", "Kim Cang"),
    ("A Hàm", "A Hàm"),
    ("Bồ Tát", "Bồ Tát"),
    ("Pháp", "Giáo Pháp"),
    ("Giới", "Giới Luật"),
]

DRY = False
DROP = False


def topics_for(catalog_row):
    """Trả list (topic, score) cho 1 text. Deterministic, không bịa."""
    text_id = catalog_row["id"]
    title = (catalog_row["title_vi"] or "").strip()
    dynasty = (catalog_row["dynasty_vi"] or "").strip()
    translator = (catalog_row["translator_vi"] or "").strip()

    topics = {}

    # 1) Genre keywords trong title
    for kw, topic in TOPIC_KEYWORDS:
        if kw in title:
            topics[topic] = topics.get(topic, 0) + 1.0

    # 2) Dynasty — chỉ khi thật (không phải placeholder)
    if dynasty and dynasty not in ("None", "?", "-", "Chưa rõ"):
        topics["Dynasty: " + dynasty] = topics.get("Dynasty: " + dynasty, 0) + 0.8

    # 3) Translator — những dịch giả nổi bật (không phải danh sách dài)
    if translator and translator not in ("None", "?", "-", "Không rõ người", "không rõ người") and len(translator) <= 30:
        topics["Dịch Giả: " + translator] = topics.get("Dịch Giả: " + translator, 0) + 0.5

    if text_id is None:
        return []
    return [(text_id, t, s) for t, s in topics.items()]


def main():
    global DRY, DROP
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/lineage.db")
    ap.add_argument("--limit", type=int, default=None, help="chỉ xử lý N text (để thử)")
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--page_size", type=int, default=200)
    ap.add_argument("--drop", action="store_true", help="DROP bảng cũ trước khi tạo")
    ap.add_argument("--dry", action="store_true", help="không ghi DB, chỉ in kế hoạch")
    ap.add_argument("--stats", action="store_true", help="in thống kê sau khi chạy")
    args = ap.parse_args()
    DRY, DROP = args.dry, args.drop

    if not os.path.exists(args.db):
        print(f"LỖI: không thấy DB {args.db}")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    if DROP:
        conn.execute("DROP TABLE IF EXISTS cbeta_topic_clusters")
        conn.commit()
        print("Đã DROP cbeta_topic_clusters (tạo lại mới).")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cbeta_topic_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            score REAL NOT NULL DEFAULT 1.0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cbeta_topic_clusters_text ON cbeta_topic_clusters(text_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cbeta_topic_clusters_topic ON cbeta_topic_clusters(topic)")
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]
    processed = 0
    inserted = 0
    offset = args.offset
    seen_texts = set()

    while True:
        limit = args.limit - processed if args.limit is not None else args.page_size
        if limit is not None and limit <= 0:
            break
        page = conn.execute(
            "SELECT id, title_vi, dynasty_vi, translator_vi FROM cbeta_catalog_vn"
            " WHERE id IS NOT NULL LIMIT ? OFFSET ?",
            (args.page_size if limit is None else limit, offset),
        ).fetchall()
        if not page:
            break
        batch = []
        for row in page:
            tid = row["id"]
            if tid in seen_texts:
                continue
            seen_texts.add(tid)
            batch.extend(topics_for(row))
            processed += 1
        if not DRY:
            conn.executemany(
                "INSERT INTO cbeta_topic_clusters(text_id, topic, score) VALUES (?,?,?)", batch
            )
            conn.commit()
        inserted += len(batch)
        offset += len(page)

    conn.close()
    print(f"Tổng text catalog (có cbeta_ref): {total}")
    print(f"Processed: {processed} | Topic rows: {inserted}"
          + (" (DRY — không ghi DB)" if DRY else " (đã ghi DB)"))

    if args.stats and not DRY:
        c2 = sqlite3.connect(args.db)
        print("\n=== STATS ===")
        print("rows:", c2.execute("SELECT COUNT(*) FROM cbeta_topic_clusters").fetchone()[0])
        print("distinct text_id:", c2.execute("SELECT COUNT(DISTINCT text_id) FROM cbeta_topic_clusters").fetchone()[0])
        print("distinct topic:", c2.execute("SELECT COUNT(DISTINCT topic) FROM cbeta_topic_clusters").fetchone()[0])
        print("\ntop topics:")
        for r in c2.execute(
            "SELECT topic, COUNT(*) c FROM cbeta_topic_clusters GROUP BY topic ORDER BY c DESC LIMIT 15"
        ):
            print(f"  {r[0]}: {r[1]}")
        c2.close()


if __name__ == "__main__":
    main()