#!/usr/bin/env python3
"""
Phiên âm Hán-Việt tự động cho 176k địa danh DILA
3 tầng ưu tiên: Lexicon exact → Context extraction → Character fallback
Optimized: pre-load lookup tables into memory, batch inserts
"""
import sqlite3
import re

DB = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db"
BATCH_SIZE = 1000

def format_name(s):
    return s.title() if s else s

COMMON_SUFFIXES = [
    ("國", "Quốc"), ("省", "Tỉnh"), ("市", "Thị"), ("縣", "Huyện"),
    ("郡", "Quận"), ("州", "Châu"), ("府", "Phủ"), ("城", "Thành"),
    ("鎮", "Trấn"), ("鄉", "Hương"), ("村", "Thôn"), ("邑", "Ấp"),
    ("山", "Sơn"), ("嶺", "Lĩnh"), ("峰", "Phong"), ("岳", "Nhạc"),
    ("江", "Giang"), ("河", "Hà"), ("湖", "Hồ"), ("海", "Hải"),
    ("溪", "Khê"), ("川", "Xuyên"), ("橋", "Kiều"), ("關", "Quan"),
    ("寺", "Tự"), ("院", "Viện"), ("堂", "Đường"), ("庵", "Am"),
    ("塔", "Tháp"), ("宮", "Cung"), ("殿", "Điện"), ("閣", "Các"),
    ("門", "Môn"), ("洞", "Động"), ("窟", "Quật"), ("園", "Viên"),
    ("林", "Lâm"), ("堡", "Bảo"), ("營", "Doanh"), ("屯", "Truân"),
]
# Sort longest first for greedy matching
COMMON_SUFFIXES.sort(key=lambda x: -len(x[0]))
# Pre-build trie-like structure: map first char → list of (suffix, hv)
SUFFIX_MAP = {}
for ch, hv in COMMON_SUFFIXES:
    SUFFIX_MAP.setdefault(ch[0], []).append((ch, hv))


def load_lookup_tables(cur):
    """Pre-load all lookup data into memory dicts."""
    hv_fallback = {}
    for row in cur.execute("SELECT ch, hv FROM hanviet_fallback"):
        hv_fallback[row[0]] = row[1]
    print(f"  Loaded {len(hv_fallback)} hanviet_fallback entries")

    lexicon_term = {}
    for row in cur.execute("SELECT term, definition FROM lexicon"):
        lexicon_term[row[0]] = row[1]
    print(f"  Loaded {len(lexicon_term)} lexicon terms")

    return hv_fallback, lexicon_term


def to_hanviet(name_zh, hv_fallback, lexicon_term, name_cache):
    if not name_zh:
        return "", 0

    if name_zh in name_cache:
        return name_cache[name_zh]

    # Priority 1: Exact match in lexicon.term
    defn = lexicon_term.get(name_zh)
    if defn:
        hv = defn.split("|")[0].split("(")[0].split(";")[0].strip()
        if len(hv) < 60 and hv and not re.search(r'[\u4e00-\u9fff]', hv):
            hv = format_name(hv)
            name_cache[name_zh] = (hv, 0)
            return hv, 0

    # Priority 3: Character-by-character fallback (no SQL queries!)
    hv_parts = []
    needs_review = 0
    i = 0
    while i < len(name_zh):
        ch = name_zh[i]
        suffix_list = SUFFIX_MAP.get(ch)
        matched = False
        if suffix_list:
            remaining = name_zh[i:]
            for suffix_ch, suffix_hv in suffix_list:
                if remaining.startswith(suffix_ch):
                    hv_parts.append(suffix_hv)
                    i += len(suffix_ch)
                    matched = True
                    break
        if matched:
            continue

        hv = hv_fallback.get(ch)
        if hv:
            hv_parts.append(hv)
        else:
            hv_parts.append(ch)
            needs_review = 1
        i += 1

    if not hv_parts:
        name_cache[name_zh] = ("", 1)
        return "", 1
    joined = " ".join(hv_parts)
    joined = format_name(joined)
    result = joined, needs_review
    name_cache[name_zh] = result
    return result


def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
    already = cur.execute("SELECT COUNT(*) FROM namevi_map_places").fetchone()[0]
    print(f"Total places_pending: {total}")
    print(f"Already in namevi_map_places: {already}")
    remaining = total - already
    if remaining <= 0:
        print("Nothing to do!")
        conn.close()
        return

    hv_fallback, lexicon_term = load_lookup_tables(cur)
    name_cache = {}

    processed = 0
    auto_saved = 0
    errors = 0
    batch_rows = []
    last_print = 0

    offset = already
    while offset < total:
        rows = cur.execute(
            "SELECT id, name_zh FROM places_pending LIMIT ? OFFSET ?",
            (BATCH_SIZE, offset)
        ).fetchall()
        if not rows:
            break

        for pid, name_zh in rows:
            try:
                hv, needs_review = to_hanviet(name_zh, hv_fallback, lexicon_term, name_cache)
                if hv:
                    batch_rows.append((pid, hv, name_zh, needs_review))
                    auto_saved += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  ERROR {pid}: {e}")

            processed += 1

        if batch_rows:
            cur.executemany("""
                INSERT OR REPLACE INTO namevi_map_places
                (dila_id, name_vi, name_zh, source, confidence, needs_review)
                VALUES (?, ?, ?, 'auto_transliterate', 0.7, ?)
            """, batch_rows)
            conn.commit()
            batch_rows = []

        offset += BATCH_SIZE

        if processed - last_print >= 5000:
            pct = processed / total * 100
            print(f"  {processed}/{total} ({pct:.1f}%) — saved {auto_saved}, errors {errors}")
            last_print = processed

    conn.close()
    print(f"\nDone! Processed {processed}, saved {auto_saved}, errors {errors}")


if __name__ == "__main__":
    main()
