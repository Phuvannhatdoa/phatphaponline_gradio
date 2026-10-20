"""
T66 — Place Description VI: DILA Note → place_desc_vi_draft
=============================================================
Copy places_dila.note (Chinese geographic descriptions) vào bảng
place_desc_vi_draft để admin đọc + tóm tắt thành note_vi tiếng Việt.

Pivot từ kế hoạch gốc (lexicon ĐỊA DANH) vì audit 2026-08-28 xác nhận
lexicon ĐỊA DANH là khái niệm Phật học, không phải mô tả địa lý.

Nguồn: places_dila.note — 14,010 mô tả học thuật tiếng Hán từ DILA Authority.
Link: namevi_map_places.dila_id → places_dila.id (lấy name_vi)

Usage:
    python scripts/t66_place_desc_vi_dila_note.py          # dry-run
    python scripts/t66_place_desc_vi_dila_note.py --apply  # insert vào DB
    python scripts/t66_place_desc_vi_dila_note.py --revert # DELETE T66 rows
    python scripts/t66_place_desc_vi_dila_note.py --stats  # thống kê
    python scripts/t66_place_desc_vi_dila_note.py --sample N  # dry-run + N samples
"""

import argparse
import io
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH  = 'data/lineage.db'
LOG_JSON = Path('data/t66_import_log.json')

T66_SOURCES = ('dila_note_zh',)


def ensure_draft_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS place_desc_vi_draft (
            place_id       TEXT PRIMARY KEY,
            name_vi        TEXT,
            name_zh        TEXT,
            note_category  TEXT,
            desc_vi_draft  TEXT,
            desc_source    TEXT,
            char_count     INTEGER,
            admin_approved INTEGER DEFAULT 0,
            admin_note     TEXT,
            created_at     TEXT,
            updated_at     TEXT
        )
    """)
    conn.commit()


def load_candidates(conn: sqlite3.Connection) -> list[dict]:
    """Load all places that have a DILA note and a name_vi in namevi_map_places."""
    rows = conn.execute("""
        SELECT
            p.id          AS place_id,
            m.name_vi,
            p.name_zh,
            p.note_category,
            p.note        AS desc_zh
        FROM places_dila p
        JOIN namevi_map_places m ON m.dila_id = p.id
        WHERE p.note IS NOT NULL
          AND LENGTH(p.note) > 20
          AND m.name_vi IS NOT NULL
          AND LENGTH(m.name_vi) > 1
        GROUP BY p.id          -- one row per place_id (shortest name_vi if multiple)
        ORDER BY LENGTH(p.note) DESC
    """).fetchall()
    return [dict(r) for r in rows]


def load_existing(conn: sqlite3.Connection) -> set:
    return {r[0] for r in conn.execute("SELECT place_id FROM place_desc_vi_draft")}


def print_sample(rows: list[dict], n: int = 20):
    print(f'\n[T66] Sample (first {min(n, len(rows))}):')
    print(f'  {"place_id":<22} {"name_vi":<25} {"cat":<15} {"chars":>5}')
    print('  ' + '-' * 72)
    for r in rows[:n]:
        cat = (r.get('note_category') or '')[:14]
        print(f'  {r["place_id"]:<22} {(r["name_vi"] or "")[:24]:<25} '
              f'{cat:<15} {r["char_count"]:>5}')
        print(f'    {r["desc_vi_draft"][:100]!r}')


def insert_rows(conn: sqlite3.Connection, rows: list[dict]) -> int:
    now = datetime.now().isoformat(timespec='seconds')
    inserted = 0
    for r in rows:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO place_desc_vi_draft
                    (place_id, name_vi, name_zh, note_category,
                     desc_vi_draft, desc_source, char_count,
                     admin_approved, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'dila_note_zh', ?, 0, ?, ?)
            """, (r['place_id'], r['name_vi'], r['name_zh'], r.get('note_category'),
                  r['desc_vi_draft'], r['char_count'], now, now))
            inserted += conn.execute('SELECT changes()').fetchone()[0]
        except sqlite3.Error as e:
            print(f'  [WARN] {r["place_id"]}: {e}')
    conn.commit()
    return inserted


def print_stats(conn: sqlite3.Connection):
    total = conn.execute('SELECT COUNT(*) FROM place_desc_vi_draft').fetchone()[0]
    if total == 0:
        print('[T66] place_desc_vi_draft: (empty)')
        return
    by_src = conn.execute(
        'SELECT desc_source, COUNT(*), AVG(char_count) FROM place_desc_vi_draft GROUP BY desc_source'
    ).fetchall()
    approved = conn.execute(
        'SELECT COUNT(*) FROM place_desc_vi_draft WHERE admin_approved=1'
    ).fetchone()[0]
    cat_dist = conn.execute(
        'SELECT note_category, COUNT(*) FROM place_desc_vi_draft GROUP BY note_category ORDER BY 2 DESC LIMIT 8'
    ).fetchall()
    print(f'\n[T66] place_desc_vi_draft stats:')
    print(f'  Total rows : {total:,}')
    print(f'  Approved   : {approved:,}')
    for src, cnt, avg in by_src:
        print(f'  {(src or "?"):<20} : {cnt:>6,}  avg {int(avg or 0):,} chars')
    print(f'  Category distribution:')
    for cat, cnt in cat_dist:
        print(f'    {(cat or "(none)"):<30} {cnt:>6,}')


def main():
    parser = argparse.ArgumentParser(description='T66 Place Description VI from DILA note')
    parser.add_argument('--apply',  action='store_true', help='Insert vào DB (default: dry-run)')
    parser.add_argument('--revert', action='store_true', help='Xóa tất cả T66 rows')
    parser.add_argument('--stats',  action='store_true', help='In stats và exit')
    parser.add_argument('--sample', type=int, default=20, help='Số rows sample (default 20)')
    parser.add_argument('--min-len', type=int, default=20, help='Min note length (default 20)')
    args = parser.parse_args()

    dry = not args.apply

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_draft_table(conn)

    if args.stats:
        print_stats(conn)
        conn.close()
        return

    if args.revert:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM place_desc_vi_draft WHERE desc_source IN ('dila_note_zh')"
        ).fetchone()[0]
        print(f'[T66] REVERT: xóa {cnt:,} rows (desc_source=dila_note_zh)')
        if cnt == 0:
            print('[T66] Không có gì để revert.')
            conn.close()
            return
        conn.execute("DELETE FROM place_desc_vi_draft WHERE desc_source IN ('dila_note_zh')")
        conn.commit()
        remaining = conn.execute('SELECT COUNT(*) FROM place_desc_vi_draft').fetchone()[0]
        print(f'[T66] Revert xong. Còn lại: {remaining:,} rows.')
        conn.close()
        return

    print(f'[T66] {"DRY RUN" if dry else "APPLY"} — DILA note → place_desc_vi_draft')

    existing = load_existing(conn)
    print(f'[T66] Existing rows: {len(existing):,}')

    candidates = load_candidates(conn)
    print(f'[T66] DILA places with note + name_vi: {len(candidates):,}')

    # Filter: min length, not already in draft
    results = []
    for c in candidates:
        if c['place_id'] in existing:
            continue
        note = (c['desc_zh'] or '').strip()
        if len(note) < args.min_len:
            continue
        results.append({
            'place_id':     c['place_id'],
            'name_vi':      c['name_vi'],
            'name_zh':      c['name_zh'],
            'note_category': c.get('note_category'),
            'desc_vi_draft': note[:2000],
            'char_count':   min(len(note), 2000),
        })

    print(f'[T66] New rows to insert: {len(results):,}')
    print(f'[T66] Projected total: {len(existing) + len(results):,}')

    # Category distribution
    cat_dist: dict[str, int] = {}
    for r in results:
        k = r.get('note_category') or '(none)'
        cat_dist[k] = cat_dist.get(k, 0) + 1
    if cat_dist:
        print('\n[T66] Category distribution:')
        for cat, cnt in sorted(cat_dist.items(), key=lambda x: -x[1])[:10]:
            print(f'  {cat:<35} {cnt:>6,}')

    print_sample(results, args.sample)

    if dry:
        print(f'\n[DRY RUN] {len(results):,} rows sẽ được insert. Chạy --apply để thực thi.')
        conn.close()
        return

    inserted = insert_rows(conn, results)
    print(f'\n[T66] Inserted: {inserted:,}')
    print_stats(conn)

    log = {
        'date':         datetime.now().isoformat(timespec='seconds'),
        'mode':         'apply',
        'candidates':   len(candidates),
        'inserted':     inserted,
        'min_len':      args.min_len,
        'cat_dist':     cat_dist,
    }
    logs = []
    if LOG_JSON.exists():
        try:
            logs = json.loads(LOG_JSON.read_text(encoding='utf-8'))
            if not isinstance(logs, list):
                logs = [logs]
        except Exception:
            logs = []
    logs.append(log)
    LOG_JSON.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[T66] Log → {LOG_JSON}')

    conn.close()


if __name__ == '__main__':
    main()
