"""
t44_gen_candidates_tsv.py — T44 Việc 2: sinh danh sách nháp (CHỈ ĐỌC, KHÔNG ghi DB)
====================================================================================
Dùng lại hàm extract_year_from_era() từ scripts/dila_era_name_extract.py (đã sửa
điều kiện bỏ qua ở T44 Việc 1) để liệt kê các chùa trích được năm từ niên hiệu +
số Hán nhưng CHƯA có event_type='founding' trong place_timeline_events.

Mở DB ở mode=ro. Không insert/update/delete bất kỳ dòng nào.

Output: docs/evidence/2026-10-09_T44_candidates.tsv
Cột: dila_id, note_excerpt(80 ky tu), year, era_name, method, has_renovation_flag
Sắp xếp: exact_year không trùng tu lên đầu; midpoint và có cờ trùng tu xuống cuối.
"""
import sqlite3
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dila_era_name_extract import extract_year_from_era, ERA_TABLE  # noqa: E402

DB_PATH = 'data/lineage.db'
OUT_PATH = 'docs/evidence/2026-10-09_T44_candidates.tsv'

RENOVATION_ANY = re.compile(r'重[修建葺]|修繕|修復|新修|重葺|重刊|重塑|敕修|奉修')


def excerpt80(note: str) -> str:
    note = (note or '').replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
    note = note.strip()
    return note[:80]


def main():
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)

    existing_founding = set(r[0] for r in conn.execute(
        "SELECT DISTINCT dila_id FROM place_timeline_events WHERE event_type='founding'"
    ).fetchall())

    places = conn.execute("""
        SELECT id, name_zh, note FROM places_dila
        WHERE note IS NOT NULL AND length(note) > 20
          AND note_category LIKE '%寺廟%'
    """).fetchall()

    rows = []
    for (dila_id, name_zh, note) in places:
        if dila_id in existing_founding:
            continue
        year, era, method = extract_year_from_era(note)
        if year is None:
            continue
        has_renov = bool(RENOVATION_ANY.search(note or ''))
        rows.append({
            'dila_id': dila_id,
            'note_excerpt': excerpt80((name_zh or '') + ' ' + (note or '')),
            'year': year,
            'era_name': era,
            'method': method,
            'has_renovation_flag': 'Y' if has_renov else 'N',
        })

    # Sắp xếp: exact_year không trùng tu lên đầu; midpoint/trùng tu xuống cuối
    def sort_key(r):
        is_exact = r['method'] == 'exact_year'
        is_renov = r['has_renovation_flag'] == 'Y'
        # priority 0 = exact_year + không trùng tu (tốt nhất)
        # priority 3 = midpoint + trùng tu (kém nhất)
        priority = (0 if is_exact else 2) + (0 if not is_renov else 1)
        return (priority, r['dila_id'])

    rows.sort(key=sort_key)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write("dila_id\tnote_excerpt\tyear\tera_name\tmethod\thas_renovation_flag\n")
        for r in rows:
            f.write(f"{r['dila_id']}\t{r['note_excerpt']}\t{r['year']}\t{r['era_name']}\t{r['method']}\t{r['has_renovation_flag']}\n")

    total = len(rows)
    n_exact = sum(1 for r in rows if r['method'] == 'exact_year')
    n_mid = sum(1 for r in rows if r['method'] == 'midpoint')
    n_renov = sum(1 for r in rows if r['has_renovation_flag'] == 'Y')

    print(f"Tong so candidate: {total}")
    print(f"  exact_year: {n_exact}")
    print(f"  midpoint:   {n_mid}")
    print(f"  co co trung tu (has_renovation_flag=Y): {n_renov}")
    print(f"Ghi file: {OUT_PATH}")

    conn.close()


if __name__ == '__main__':
    main()
