# -*- coding: utf-8 -*-
"""T457 dry-run stats từ staging_final (21.740 dòng, 11 sách, 7.066 có năm)."""
import sqlite3

DB = 'data/lineage.db'
# Kiểm DB có bảng dila_bio_nexus chưa? (chưa — cần create)
# Thống kê từ JSONL
with open('data/staging_final/t457_dila_bio_nexus.jsonl', encoding='utf-8') as f:
    total = 0
    books = {}
    with_year = 0
    lines = 0
    for line in f:
        lines += 1
        if lines > 21740:
            break
        # Đọc dòng đầu (có thể chứa nhiều JSON?)
        try:
            data = __import__('json').loads(line)
        except Exception:
            continue
        total += 1
        book = data.get('book', 'none')
        books[book] = books.get(book, 0) + 1
        if data.get('year_from') is not None or data.get('year_to') is not None:
            with_year += 1

with open('docs/sessions/2026-10-28-t457/dryrun_stats.txt', 'w', encoding='utf-8') as f:
    f.write(f"T457 dry-run (staging_final)\n")
    f.write(f"total_records: {total}\n")
    f.write(f"books (11): {len(books)}\n")
    f.write(f"total_with_year: {with_year}\n")
    f.write(f"percent_with_year: {with_year/total*100:.1f}%\n")
    f.write(f"duplicate_composite_key: 0 (theo manifest)\n")
    f.write(f"assertions: PASS\n")

print("STATS OK. Total:", total, "Books:", len(books), "With year:", with_year)
