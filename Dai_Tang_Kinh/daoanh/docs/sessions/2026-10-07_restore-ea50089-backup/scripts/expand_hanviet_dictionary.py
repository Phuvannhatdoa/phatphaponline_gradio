"""T29 — Bulk-expand custom_hanviet_override via hvdic.thivien.net's transcript-query
API (Thieu Chuu / Tran Van Chanh / Nguyen Quoc Hung compiled dictionaries — the same
source already used to manually verify 13 characters on 2026-08-20, cross-checked
against this API and confirmed identical readings before running at scale).

Self-contained: derives the list of characters needing a reading directly from the DB
(any Han character still appearing raw in people.name_vi or the places name_vi chain)
rather than a precomputed file, so it can be safely re-run later as more names are
added or as name_vi gets refreshed — INSERT OR IGNORE means it only ever adds new
entries, never overwrites an existing override (including ones a human verified by
hand, which take priority over this bulk pass).

Usage:
    python scripts/expand_hanviet_dictionary.py
"""
import sys, os, sqlite3, requests, time, re

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)
DB_PATH = os.path.join(PROJECT_ROOT, "data", "lineage.db")

HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': 'DaoAnhBuddhistGIS/1.0 (https://phatphaponline.org/daoanh/; contact admin) python-requests'
}
CHUNK_SIZE = 200
HAN = re.compile(r'[一-鿿]')


def collect_missing_chars(conn):
    missing = set()
    for (vi,) in conn.execute("SELECT name_vi FROM people WHERE name_vi IS NOT NULL AND name_vi != ''").fetchall():
        missing.update(HAN.findall(vi))
    for (vi,) in conn.execute("""
        SELECT COALESCE(m.name_vi, p.name_vi) FROM places_pending p
        LEFT JOIN namevi_map_places m ON m.dila_id = p.id
        WHERE p.id IS NOT NULL AND p.id != '' AND p.name_zh IS NOT NULL AND p.name_zh != ''
          AND p.note IS NOT NULL AND p.note != ''
    """).fetchall():
        if vi:
            missing.update(HAN.findall(vi))
    return missing


def fetch_chunk(chars):
    data = {'mode': 'trans', 'lang': '1', 'input': chars}
    r = requests.post('https://hvdic.thivien.net/transcript-query.json.php', headers=HEADERS, data=data, timeout=20)
    r.raise_for_status()
    return r.json()


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_hanviet_override (
            char TEXT PRIMARY KEY, hanviet TEXT NOT NULL,
            added_by TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    already = {r[0] for r in conn.execute("SELECT char FROM custom_hanviet_override").fetchall()}
    missing = collect_missing_chars(conn) - already
    chars = ''.join(sorted(missing))
    print(f"Chars needing a reading: {len(chars)} (already have {len(already)} overrides)")

    found = 0
    not_found = []
    for i in range(0, len(chars), CHUNK_SIZE):
        chunk = chars[i:i + CHUNK_SIZE]
        try:
            result = fetch_chunk(chunk)
        except Exception as e:
            print(f"  chunk {i}-{i+CHUNK_SIZE} FAILED: {e}")
            time.sleep(3)
            continue
        for item in result.get('result', []):
            ch = item.get('i')
            outs = item.get('o') or []
            if not ch:
                continue
            if outs and outs[0].strip():
                hv = outs[0].strip()
                conn.execute("""
                    INSERT OR IGNORE INTO custom_hanviet_override (char, hanviet, added_by, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (ch, hv[0].upper() + hv[1:], 'bulk-verified-hvdic.thivien.net-transcript-api-2026-08-20'))
                found += 1
            else:
                not_found.append(ch)
        print(f"  chunk {i}-{i + len(chunk)}: processed, cumulative found={found}")
        time.sleep(0.5)  # polite delay between requests

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM custom_hanviet_override").fetchone()[0]
    print(f"\nNewly added: {found}")
    print(f"Not found by dictionary (no known reading): {len(not_found)}")
    if not_found:
        print("Chars with no reading:", ''.join(not_found))
    print(f"Total custom_hanviet_override rows now: {total}")
    conn.close()


if __name__ == "__main__":
    main()
