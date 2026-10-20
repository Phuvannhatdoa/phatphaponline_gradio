"""
T65 — Person Bio VI Phase 2: Chinese Name Pattern Matching
============================================================
Mở rộng T63 từ 845 rows lên ≥2,345 rows qua matching name_zh
trong body text của lexicon definitions.

Pass 1 (bracket):  definition LIKE '%(name_zh)%'  → conf 0.80
Pass 2 (body+val): definition LIKE '%name_zh%'    → conf 0.65 + similarity validate

Strategy: build in-memory index từ lexicon (O(n_lex)), lookup O(1) per person.
Tránh n×m SQLite LIKE query (từng timeout với 48K×166K).

Usage:
    python scripts/t65_bio_vi_lexicon_p2.py              # dry-run cả 2 pass
    python scripts/t65_bio_vi_lexicon_p2.py --apply      # insert vào DB
    python scripts/t65_bio_vi_lexicon_p2.py --pass 1     # Pass 1 only
    python scripts/t65_bio_vi_lexicon_p2.py --pass 2     # Pass 2 only
    python scripts/t65_bio_vi_lexicon_p2.py --revert     # xóa tất cả T65 rows
    python scripts/t65_bio_vi_lexicon_p2.py --stats      # thống kê hiện tại
"""

import argparse
import io
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH  = 'data/lineage.db'
LOG_JSON = Path('data/t65_import_log.json')

# Regex: bracket patterns  (慧能)  or  （慧能）
_RE_BRACKET_HALF  = re.compile(r'\(([^\)]{2,10})\)')
_RE_BRACKET_FULL  = re.compile(r'（([^）]{2,10})）')
# Vietnamese title-case word sequence
_RE_VN_NAME       = re.compile(
    r'[A-ZĐÀÁẢÃẠĂẮẶẰẴẪÂẤẦẨẪẬÊẾỀỆÊÔƠƯ]'
    r'[a-zđàáảãạăắặằẵẫâấầẩẫậêếềệôơư]+'
    r'(?:\s+[A-ZĐÀÁẢÃẠĂẮẶẰẴẪÂẤẦẨẪẬÊẾỀỆÊÔƠƯ][a-zđàáảãạăắặằẵẫâấầẩẫậêếềệôơư]+)+'
)


def is_cjk(s: str) -> bool:
    return bool(s) and all('一' <= c <= '鿿' for c in s)


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a, b = a.strip().lower(), b.strip().lower()
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def extract_vn_near(definition: str, name_zh: str, window: int = 60) -> str | None:
    idx = definition.find(name_zh)
    if idx == -1:
        return None
    ctx = definition[max(0, idx - window): idx + len(name_zh) + window]
    names = _RE_VN_NAME.findall(ctx)
    return names[0] if names else None


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def build_indexes(conn: sqlite3.Connection) -> tuple[dict, dict]:
    """
    Returns:
        bracket_idx : name_zh → [(lex_id, term, source, definition)]
        body_idx    : name_zh → [(lex_id, term, source, definition)]
    """
    print('[T65] Đang load lexicon definitions vào RAM...')
    rows = conn.execute("""
        SELECT id, term, definition, source
        FROM lexicon
        WHERE LENGTH(definition) > 100
    """).fetchall()
    print(f'[T65] Lexicon entries loaded: {len(rows):,}')

    bracket_idx: dict[str, list] = defaultdict(list)
    body_seen: dict[str, set]   = defaultdict(set)  # name_zh → set of lex_ids (dedup)
    body_idx: dict[str, list]   = defaultdict(list)

    for lex_id, term, definition, source in rows:
        if not definition:
            continue

        # --- Pass 1 index: extract (X) and （X） patterns ---
        for m in _RE_BRACKET_HALF.finditer(definition):
            cand = m.group(1).strip()
            if is_cjk(cand) and len(cand) >= 2:  # allow 2-char dharma names
                bracket_idx[cand].append((lex_id, term, source, definition))

        for m in _RE_BRACKET_FULL.finditer(definition):
            cand = m.group(1).strip()
            if is_cjk(cand) and len(cand) >= 2:
                bracket_idx[cand].append((lex_id, term, source, definition))

        # --- Pass 2 index: scan for any CJK sequence ≥3 chars ---
        # Extract all CJK runs from definition
        for cjk_run in re.finditer(r'[一-鿿]{3,10}', definition):
            nz = cjk_run.group()
            if lex_id not in body_seen[nz]:
                body_seen[nz].add(lex_id)
                body_idx[nz].append((lex_id, term, source, definition))

    print(f'[T65] Bracket index: {len(bracket_idx):,} unique name_zh keys')
    print(f'[T65] Body index   : {len(body_idx):,} unique name_zh keys')
    return dict(bracket_idx), dict(body_idx)


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def run_pass1(persons: list, bracket_idx: dict,
              existing_pids: set) -> list[dict]:
    """Pass 1: name_zh in bracket pattern (慧能) → match_type='name_zh_bracket'"""
    results = []
    for pid, name_zh, name_vi in persons:
        if pid in existing_pids or not name_zh or len(name_zh) < 2:
            continue
        if not is_cjk(name_zh):
            continue
        matches = bracket_idx.get(name_zh)
        if not matches:
            continue
        # Keep longest definition
        best = max(matches, key=lambda x: len(x[3]))
        lex_id, term, source, definition = best
        bio = definition[:2000]
        results.append({
            'person_id':    pid,
            'name_vi':      name_vi,
            'name_zh':      name_zh,
            'bio_vi_draft': bio,
            'source_lex_id': lex_id,
            'source_term':  term,
            'source_name':  source,
            'match_type':   'name_zh_bracket',
            'char_count':   len(bio),
        })
    return results


def run_pass2(persons: list, body_idx: dict, existing_pids: set,
              p1_pids: set, sim_threshold: float = 0.50) -> list[dict]:
    """Pass 2: name_zh anywhere in definition + similarity validate."""
    results = []
    for pid, name_zh, name_vi in persons:
        if pid in existing_pids or pid in p1_pids:
            continue
        if not name_zh or len(name_zh) < 3 or not is_cjk(name_zh):
            continue
        matches = body_idx.get(name_zh)
        if not matches:
            continue
        # Try each match, validate via extracted VN name
        best_sim = 0.0
        best_match = None
        for lex_id, term, source, definition in matches:
            # Quick check: term similarity
            hw_sim = similarity(term, name_vi) if name_vi else 0
            # Extract VN name near name_zh
            vn_near = extract_vn_near(definition, name_zh)
            near_sim = similarity(vn_near, name_vi) if vn_near else 0
            score = max(hw_sim, near_sim)
            if score > best_sim:
                best_sim = score
                best_match = (lex_id, term, source, definition, score)

        if best_match and best_sim >= sim_threshold:
            lex_id, term, source, definition, score = best_match
            bio = definition[:2000]
            results.append({
                'person_id':    pid,
                'name_vi':      name_vi,
                'name_zh':      name_zh,
                'bio_vi_draft': bio,
                'source_lex_id': lex_id,
                'source_term':  term,
                'source_name':  source,
                'match_type':   'name_zh_body',
                'char_count':   len(bio),
                'sim_score':    round(best_sim, 3),
            })
    return results


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------

CONF = {'name_zh_bracket': '0.80', 'name_zh_body': '0.65'}

T65_MATCH_TYPES = ('name_zh_bracket', 'name_zh_body')


def ensure_draft_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS person_bio_vi_draft (
            person_id      TEXT PRIMARY KEY,
            name_vi        TEXT,
            name_zh        TEXT,
            bio_vi_draft   TEXT,
            source_lex_id  INTEGER,
            source_term    TEXT,
            source_name    TEXT,
            match_type     TEXT,
            char_count     INTEGER,
            admin_approved INTEGER DEFAULT 0,
            admin_note     TEXT,
            created_at     TEXT,
            updated_at     TEXT
        )
    """)
    conn.commit()


def insert_results(conn: sqlite3.Connection, results: list[dict]) -> int:
    now = datetime.now().isoformat(timespec='seconds')
    inserted = 0
    for r in results:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO person_bio_vi_draft
                    (person_id, name_vi, name_zh, bio_vi_draft,
                     source_lex_id, source_term, source_name,
                     match_type, char_count, admin_approved, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (r['person_id'], r['name_vi'], r['name_zh'], r['bio_vi_draft'],
                  r['source_lex_id'], r['source_term'], r['source_name'],
                  r['match_type'], r['char_count'], now, now))
            inserted += conn.execute('SELECT changes()').fetchone()[0]
        except sqlite3.Error as e:
            print(f'  [WARN] {r["person_id"]}: {e}')
    conn.commit()
    return inserted


def print_sample(results: list[dict], n: int = 20, label: str = ''):
    if not results:
        print(f'  (no results)')
        return
    print(f'\n[T65] Sample {label} (first {min(n, len(results))}):')
    print(f'  {"person_id":<16} {"name_zh":<10} {"name_vi":<20} {"source_term":<18} {"chars":>5}')
    print('  ' + '-' * 75)
    for r in results[:n]:
        sim = f' sim={r.get("sim_score",""):.2f}' if 'sim_score' in r else ''
        print(f'  {r["person_id"]:<16} {(r["name_zh"] or "")[:9]:<10} '
              f'{(r["name_vi"] or "")[:19]:<20} {(r["source_term"] or "")[:17]:<18} '
              f'{r["char_count"]:>5}{sim}')


def print_stats(conn: sqlite3.Connection):
    total = conn.execute('SELECT COUNT(*) FROM person_bio_vi_draft').fetchone()[0]
    by_type = conn.execute(
        'SELECT match_type, COUNT(*), AVG(char_count) FROM person_bio_vi_draft GROUP BY match_type'
    ).fetchall()
    approved = conn.execute(
        'SELECT COUNT(*) FROM person_bio_vi_draft WHERE admin_approved=1'
    ).fetchone()[0]
    print(f'\n[T65] person_bio_vi_draft stats:')
    print(f'  Total rows : {total:,}')
    print(f'  Approved   : {approved:,}')
    for mt, cnt, avg in by_type:
        print(f'  {mt:<22} : {cnt:>5,}  avg {int(avg or 0):,} chars')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='T65 Person Bio VI Phase 2')
    parser.add_argument('--apply',   action='store_true', help='Insert vào DB (default: dry-run)')
    parser.add_argument('--pass',    dest='only_pass', type=int, choices=[1, 2],
                        help='Chỉ chạy pass 1 hoặc pass 2')
    parser.add_argument('--revert',  action='store_true',
                        help='Xóa tất cả rows có match_type IN (name_zh_bracket, name_zh_body)')
    parser.add_argument('--stats',   action='store_true', help='In stats và exit')
    parser.add_argument('--sim',     type=float, default=0.50,
                        help='Similarity threshold cho Pass 2 (default 0.50)')
    parser.add_argument('--sample',  type=int, default=20,
                        help='Số rows sample in ra (default 20)')
    args = parser.parse_args()

    dry = not args.apply

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_draft_table(conn)

    # --stats
    if args.stats:
        print_stats(conn)
        conn.close()
        return

    # --revert: xóa T65 rows, revert về trạng thái trước T65
    if args.revert:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM person_bio_vi_draft WHERE match_type IN (?,?)",
            T65_MATCH_TYPES
        ).fetchone()[0]
        print(f'[T65] REVERT: sẽ xóa {cnt:,} rows (match_type: name_zh_bracket, name_zh_body)')
        if cnt == 0:
            print('[T65] Không có gì để revert.')
            conn.close()
            return
        conn.execute(
            "DELETE FROM person_bio_vi_draft WHERE match_type IN (?,?)",
            T65_MATCH_TYPES
        )
        conn.commit()
        remaining = conn.execute('SELECT COUNT(*) FROM person_bio_vi_draft').fetchone()[0]
        print(f'[T65] Revert xong. Còn lại: {remaining:,} rows (T63 intact).')
        conn.close()
        return

    mode = 'DRY RUN' if dry else 'APPLY'
    pass_label = f'Pass {args.only_pass} only' if args.only_pass else 'Pass 1 + Pass 2'
    print(f'[T65] {mode} — {pass_label} (sim_threshold={args.sim})')

    # Existing pids
    existing_pids = {r[0] for r in conn.execute('SELECT person_id FROM person_bio_vi_draft')}
    print(f'[T65] Existing drafts: {len(existing_pids):,}')

    # Load persons (name_zh ≥ 2 chars — bracket pass handles 2-char names)
    persons = conn.execute("""
        SELECT id, name_zh, name_vi
        FROM people
        WHERE name_zh IS NOT NULL AND LENGTH(name_zh) >= 2
    """).fetchall()
    persons = [(r[0], r[1], r[2]) for r in persons]
    print(f'[T65] People with name_zh ≥2: {len(persons):,}')

    results_p1: list[dict] = []
    results_p2: list[dict] = []

    # Build indexes (only if needed)
    need_p1 = args.only_pass in (None, 1)
    need_p2 = args.only_pass in (None, 2)

    bracket_idx, body_idx = build_indexes(conn)

    # Pass 1
    if need_p1:
        print('\n[T65] === Pass 1: Bracket Match ===')
        results_p1 = run_pass1(persons, bracket_idx, existing_pids)
        print(f'[T65] Pass 1 matches: {len(results_p1):,}')
        print_sample(results_p1, args.sample, 'Pass 1 (bracket)')

    # Pass 2
    if need_p2:
        p1_pids = {r['person_id'] for r in results_p1}
        print(f'\n[T65] === Pass 2: Body Match (sim ≥ {args.sim}) ===')
        results_p2 = run_pass2(persons, body_idx, existing_pids, p1_pids, args.sim)
        print(f'[T65] Pass 2 matches: {len(results_p2):,}')
        print_sample(results_p2, args.sample, 'Pass 2 (body+validation)')

    all_results = results_p1 + results_p2
    print(f'\n[T65] Total new matches: {len(all_results):,}  '
          f'(P1={len(results_p1):,} + P2={len(results_p2):,})')
    print(f'[T65] Projected total drafts: {len(existing_pids) + len(all_results):,}')

    # Source distribution
    src_dist: dict[str, int] = {}
    for r in all_results:
        src_dist[r['source_name']] = src_dist.get(r['source_name'], 0) + 1
    if src_dist:
        print('\n[T65] Source distribution:')
        for src, cnt in sorted(src_dist.items(), key=lambda x: -x[1])[:10]:
            print(f'  {src or "(none)":<30} {cnt:>6,}')

    if dry:
        print(f'\n[DRY RUN] {len(all_results):,} rows sẽ được insert. Chạy --apply để thực thi.')
        conn.close()
        return

    # Apply
    inserted_p1 = insert_results(conn, results_p1) if results_p1 else 0
    inserted_p2 = insert_results(conn, results_p2) if results_p2 else 0
    total_inserted = inserted_p1 + inserted_p2

    print(f'\n[T65] Inserted Pass 1: {inserted_p1:,}')
    print(f'[T65] Inserted Pass 2: {inserted_p2:,}')
    print(f'[T65] Total inserted : {total_inserted:,}')
    print_stats(conn)

    # Write log
    log = {
        'date':            datetime.now().isoformat(timespec='seconds'),
        'mode':            'apply',
        'pass1_matches':   len(results_p1),
        'pass2_matches':   len(results_p2),
        'inserted_p1':     inserted_p1,
        'inserted_p2':     inserted_p2,
        'total_inserted':  total_inserted,
        'sim_threshold':   args.sim,
        'source_dist':     src_dist,
    }
    # Append to log (keep history)
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
    print(f'[T65] Log → {LOG_JSON}')

    conn.close()


if __name__ == '__main__':
    main()
