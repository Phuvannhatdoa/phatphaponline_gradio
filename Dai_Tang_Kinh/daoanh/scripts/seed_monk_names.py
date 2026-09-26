#!/usr/bin/env python3
"""
seed_monk_names.py
Bulk Hán-Việt transliteration cho 48K people records trong `people` table.

Chiến lược 3 tầng (giống bulk_transliterate.py cho places):
  1. Lexicon exact match (tên người có trong từ điển)
  2. Hanviet fallback (character-by-character lookup)
  3. Giữ nguyên Hán nếu không tra được (đánh dấu needs_review)

Chạy:
  python scripts/seed_monk_names.py

Có thể chạy lại nhiều lần (idempotent).
Output: name_vi_map được seed ~48K records với source='auto_transliterate'
"""

import sqlite3
import os
import re
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BATCH_SIZE = 1000

COMMON_PATTERNS = [
    ("大師", "Đại Sư"), ("禪師", "Thiền Sư"), ("法師", "Pháp Sư"),
    ("和尚", "Hòa Thượng"), ("長老", "Trưởng Lão"), ("國師", "Quốc Sư"),
    ("尊者", "Tôn Giả"), ("菩薩", "Bồ Tát"), ("羅漢", "La Hán"),
    ("比丘", "Tỳ Kheo"), ("沙門", "Sa Môn"), ("居士", "Cư Sĩ"),
    ("祖师", "Tổ Sư"), ("僧", "Tăng"), ("尼", "Ni"),
]
COMMON_PATTERNS.sort(key=lambda x: -len(x[0]))

PATTERN_MAP = {}
for ch, hv in COMMON_PATTERNS:
    PATTERN_MAP.setdefault(ch[0], []).append((ch, hv))


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def load_lookups(cur):
    hv_fallback = {}
    for row in cur.execute("SELECT ch, hv FROM hanviet_fallback"):
        hv_fallback[row[0]] = row[1]
    log(f"  Loaded {len(hv_fallback)} hanviet_fallback entries")

    lexicon_term = {}
    for row in cur.execute("SELECT term, definition FROM lexicon"):
        lexicon_term[row[0]] = row[1]
    log(f"  Loaded {len(lexicon_term)} lexicon terms")

    return hv_fallback, lexicon_term


def to_hanviet(name_zh, hv_fallback, lexicon_term, cache):
    if not name_zh or not name_zh.strip():
        return "", 1
    name_zh = name_zh.strip()
    if name_zh in cache:
        return cache[name_zh]

    defn = lexicon_term.get(name_zh)
    if defn:
        hv = defn.split("|")[0].split("(")[0].split(";")[0].strip()
        if hv and len(hv) < 80 and not re.search(r'[\u4e00-\u9fff]', hv):
            result = (hv.title(), 0)
            cache[name_zh] = result
            return result

    parts = []
    needs_review = 0
    i = 0
    while i < len(name_zh):
        ch = name_zh[i]
        plist = PATTERN_MAP.get(ch)
        matched = False
        if plist:
            remaining = name_zh[i:]
            for pch, phv in plist:
                if remaining.startswith(pch):
                    parts.append(phv)
                    i += len(pch)
                    matched = True
                    break
        if matched:
            continue
        hv = hv_fallback.get(ch)
        if hv:
            parts.append(hv)
        else:
            parts.append(ch)
            needs_review = 1
        i += 1

    if not parts:
        result = ("", 1)
    else:
        joined = " ".join(parts).title()
        result = (joined, needs_review)
    cache[name_zh] = result
    return result


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    cur = conn.cursor()

    total_people = cur.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    already = cur.execute(
        "SELECT COUNT(*) FROM name_vi_map n JOIN people p ON p.id = n.dila_id"
    ).fetchone()[0]
    log(f"Total people: {total_people}")
    log(f"Already in name_vi_map (with dila_id): {already}")
    remaining = total_people - already
    if remaining <= 0:
        log("Nothing to do!")
        conn.close()
        return
    log(f"Remaining to seed: {remaining}")

    hv_fallback, lexicon_term = load_lookups(cur)
    cache = {}

    processed = 0
    saved = 0
    errors = 0
    batch_rows = []
    offset = 0

    while offset < total_people:
        rows = cur.execute("""
            SELECT p.id as pid, p.name_zh
            FROM people p
            LEFT JOIN name_vi_map n ON p.id = n.dila_id
            WHERE n.dila_id IS NULL
              AND p.name_zh IS NOT NULL AND p.name_zh != ''
            LIMIT ? OFFSET ?
        """, (BATCH_SIZE, offset)).fetchall()
        if not rows:
            break

        for row in rows:
            pid = row['pid']
            name_zh = row['name_zh']
            try:
                hv, nr = to_hanviet(name_zh, hv_fallback, lexicon_term, cache)
                if hv:
                    batch_rows.append((hv, hv, name_zh, pid, 'auto_transliterate', 0.7))
                    saved += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    log(f"  ERROR {pid}: {e}")
            processed += 1

        if batch_rows:
            cur.executemany("""
                INSERT OR IGNORE INTO name_vi_map
                (name_vi, name_vi_auto, name_zh, dila_id, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, batch_rows)
            conn.commit()
            log(f"  Batch committed: {len(batch_rows)} rows (total saved: {saved})")
            batch_rows = []

        offset += BATCH_SIZE

    conn.close()
    log(f"\nDone! Processed {processed}, saved {saved}, errors {errors}")


if __name__ == "__main__":
    main()
