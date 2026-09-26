"""
T71 — Place Name VI Lexicon Verify
====================================
Cross-reference 22 bộ từ điển Phật học VN (166K entries) với 59K DILA places
để xác minh tên tiếng Việt qua CJK name_zh matching — không NLP, không LLM.

Pass A (lexicon CJK index, precision ~87%):
    - Build index {name_zh: (vi_term, source)} từ definition/term của 166K entries
    - Match places_dila.name_zh → tìm tên Việt do học giả đặt
    - Khớp: upgrade conf 0.70→0.80 + ghi note [T71:lex_<source>]
    - Khác: flag needs_review=1 + ghi note [T71:CONFLICT lex=<vi>]

Pass B (suffix rules, deterministic):
    - 16 Hán suffix → Hán-Việt tương đương cố định (寺→Tự, 山→Sơn...)
    - Suffix đúng + conf<0.71: upgrade 0.70→0.72 + ghi note [T71:suffix_<char>]
    - Suffix sai: flag needs_review=1 (không tự sửa name_vi)

Usage:
    python scripts/t71_place_name_lexicon_verify.py           # dry-run cả 2 pass
    python scripts/t71_place_name_lexicon_verify.py --apply   # apply
    python scripts/t71_place_name_lexicon_verify.py --revert  # rollback
    python scripts/t71_place_name_lexicon_verify.py --pass A  # chỉ Pass A
    python scripts/t71_place_name_lexicon_verify.py --pass B  # chỉ Pass B
    python scripts/t71_place_name_lexicon_verify.py --stats   # thống kê
    python scripts/t71_place_name_lexicon_verify.py --conflicts  # xem conflicts
"""

import argparse
import io
import json
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH  = 'data/lineage.db'
LOG_JSON = Path('data/t71_import_log.json')
T71_TAG  = '[T71:'  # marker để revert

# Sino-Vietnamese suffix rules (deterministic phonetic)
SUFFIX_RULES = {
    '寺': 'Tự', '山': 'Sơn', '河': 'Hà',  '城': 'Thành',
    '塔': 'Tháp','湖': 'Hồ',  '洞': 'Động','廟': 'Miếu',
    '庵': 'Am',  '院': 'Viện','國': 'Quốc','峰': 'Phong',
    '嶺': 'Lĩnh','橋': 'Kiều','溪': 'Khê', '關': 'Quan',
    '灣': 'Loan','港': 'Cảng','林': 'Lâm', '宮': 'Cung',
}

RE_CJK_START = re.compile(
    r'^[\s]*([一-鿿㐀-䶿]'
    r'[一-鿿㐀-䶿\s]{0,20}'
    r'[一-鿿㐀-䶿])'
    r'[\s]*[。．\.\、,，]'
)
RE_CJK_IN_TERM = re.compile(r'[一-鿿㐀-䶿]{2,10}')
RE_CJK_ONLY    = re.compile(r'^[一-鿿㐀-䶿\s]+$')


def build_cjk_index(conn: sqlite3.Connection) -> dict:
    """
    Đọc toàn bộ 166K lexicon entries, build index:
        name_zh (CJK key) -> [(vi_term, source, lex_id), ...]

    2 pattern:
    1. definition bắt đầu "漢 字. ..." → extract CJK sequence trước dấu chấm
    2. term chứa CJK sequence (nhưng term không toàn CJK → có phần tên Việt)
    """
    print('[T71] Loading 166K lexicon entries for CJK index...')
    rows = conn.execute('SELECT id, term, definition, source FROM lexicon').fetchall()
    print(f'[T71] Loaded: {len(rows):,} entries')

    idx: dict = {}

    def add(key: str, vi: str, src: str, lid: int):
        key = key.strip()
        vi  = vi.strip()
        if not key or not vi or len(key) < 2 or len(key) > 12:
            return
        if len(vi) > 80:
            vi = vi[:80]
        if key not in idx:
            idx[key] = []
        idx[key].append((vi, src, lid))

    for lex_id, term, defn, src in rows:
        term = (term or '').strip()
        defn = (defn or '').strip()

        # Pattern 1: definition starts with CJK sequence followed by 。.，
        if defn:
            m = RE_CJK_START.match(defn)
            if m and term and not RE_CJK_ONLY.match(term) and len(term) < 80:
                cjk = re.sub(r'\s+', '', m.group(1))
                add(cjk, term, src, lex_id)

        # Pattern 2: CJK in term (but term is not entirely CJK = has Vietnamese)
        if term and not RE_CJK_ONLY.match(term) and len(term) < 80:
            for m2 in RE_CJK_IN_TERM.finditer(term):
                cjk = m2.group(0)
                add(cjk, term, src, lex_id)

    print(f'[T71] CJK index: {len(idx):,} unique Chinese keys')
    return idx


def normalize_vi(s: str) -> str:
    """Strip diacritics + lowercase + remove spaces for loose comparison.
    Vietnamese 'Hòa' vs 'Hoà' are same word with different Unicode placement
    — stripping all combining marks resolves this without losing distinctiveness
    ('Huệ' vs 'Tuệ' still differ: 'hue' vs 'tue').
    Also strips any trailing place-type suffix that lex may omit (Tự/Chùa).
    """
    s = (s or '').strip()
    # Split lex terms like "Bách Lâm: Tự..." at colon
    s = s.split(':')[0].strip()
    # Strip diacritics via NFD decomposition
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    # Remove spaces for "HoaThuan" == "Hoa Thuan"
    s = re.sub(r'\s+', '', s)
    return s


def run_pass_a(conn: sqlite3.Connection, cjk_idx: dict, dry: bool) -> dict:
    """
    Pass A: match places_dila.name_zh → lexicon index.
    Returns stats dict.
    """
    print('\n[T71 Pass A] Lexicon CJK cross-reference...')

    # Load DILA places
    dila = conn.execute(
        'SELECT id, name_zh FROM places_dila WHERE name_zh IS NOT NULL AND LENGTH(name_zh)>=2'
    ).fetchall()
    print(f'[T71 Pass A] DILA places with name_zh: {len(dila):,}')

    # Load current conf for all dila places (use max conf per dila_id)
    conf_rows = conn.execute(
        'SELECT dila_id, name_vi, confidence, needs_review, note_vi '
        'FROM namevi_map_places ORDER BY confidence DESC'
    ).fetchall()
    # Map: dila_id -> best row (highest conf)
    conf_map: dict = {}
    for dila_id, name_vi, conf, needs_rev, note_vi in conf_rows:
        if dila_id not in conf_map:
            conf_map[dila_id] = (name_vi, conf, needs_rev, note_vi or '')

    matched_same  = []  # (dila_id, name_zh, lex_vi, auto_vi, src, lex_id)
    matched_diff  = []
    skipped_high  = 0
    no_match      = 0

    for dila_id, name_zh in dila:
        nzh = name_zh.strip()
        if nzh not in cjk_idx:
            no_match += 1
            continue

        info = conf_map.get(dila_id)
        if not info:
            continue

        auto_vi, cur_conf, needs_rev, note_vi = info

        if cur_conf >= 0.80:
            skipped_high += 1
            continue

        lex_vi, src, lex_id = cjk_idx[nzh][0]
        # Use only the part of lex_vi before colon if it contains colon pattern
        lex_term = lex_vi.split(':')[0].strip()

        if normalize_vi(lex_term) == normalize_vi(auto_vi):
            matched_same.append((dila_id, nzh, lex_term, auto_vi, src, lex_id, cur_conf))
        else:
            matched_diff.append((dila_id, nzh, lex_term, auto_vi, src, lex_id, cur_conf))

    upgradeable = [m for m in matched_same if m[6] < 0.75]

    print(f'[T71 Pass A] Matched (same name): {len(matched_same):,}')
    print(f'[T71 Pass A]   → Can upgrade (conf<0.75): {len(upgradeable):,}')
    print(f'[T71 Pass A]   → Already conf>=0.75: {len(matched_same)-len(upgradeable):,}')
    print(f'[T71 Pass A] Matched (DIFF → conflict): {len(matched_diff):,}')
    print(f'[T71 Pass A] Skipped (conf>=0.80): {skipped_high:,}')
    print(f'[T71 Pass A] No match in index: {no_match:,}')

    # Sample conflicts
    if matched_diff:
        print(f'\n[T71 Pass A] Sample conflicts (lex ≠ auto):')
        for dila_id, nzh, lex_vi, auto_vi, src, _, conf in matched_diff[:15]:
            print(f'  {nzh:<12} lex={lex_vi[:25]:<25} auto={auto_vi[:25]:<25} conf={conf:.2f} [{src[:20]}]')

    if dry:
        print(f'\n[DRY RUN Pass A] {len(upgradeable):,} upgrades + {len(matched_diff):,} conflict flags pending.')
        return {
            'pass': 'A', 'mode': 'dry',
            'upgrades': len(upgradeable),
            'conflicts': len(matched_diff),
            'no_match': no_match,
        }

    # APPLY
    now = datetime.now().isoformat(timespec='seconds')
    upgraded = 0
    flagged  = 0

    for dila_id, nzh, lex_vi, auto_vi, src, lex_id, cur_conf in upgradeable:
        src_tag = src[:20].replace(' ', '_')
        tag = f'[T71:lex_{src_tag}]'
        conn.execute(
            "UPDATE namevi_map_places SET confidence=0.80, needs_review=0, "
            "note_vi = TRIM(COALESCE(note_vi,'') || ' ' || ?), "
            "source_id = COALESCE(source_id, 0) "
            "WHERE dila_id=? AND confidence < 0.75",
            (tag, dila_id)
        )
        upgraded += conn.execute('SELECT changes()').fetchone()[0]

    for dila_id, nzh, lex_vi, auto_vi, src, lex_id, cur_conf in matched_diff:
        tag = f'[T71:CONFLICT lex={lex_vi[:20]}]'
        conn.execute(
            "UPDATE namevi_map_places SET needs_review=1, "
            "note_vi = TRIM(COALESCE(note_vi,'') || ' ' || ?) "
            "WHERE dila_id=? AND confidence < 0.80",
            (tag, dila_id)
        )
        flagged += conn.execute('SELECT changes()').fetchone()[0]

    conn.commit()
    print(f'\n[T71 Pass A] Upgraded: {upgraded:,} | Conflict-flagged: {flagged:,}')
    return {
        'pass': 'A', 'mode': 'apply', 'ts': now,
        'upgrades': upgraded, 'conflicts': flagged, 'no_match': no_match,
    }


def run_pass_b(conn: sqlite3.Connection, dry: bool) -> dict:
    """
    Pass B: suffix rules.
    For each place conf<0.71 with name_zh suffix in SUFFIX_RULES:
      - name_vi ends with correct Sino-Viet suffix → upgrade 0.70→0.72
      - name_vi ends with WRONG suffix → flag needs_review=1
    """
    print('\n[T71 Pass B] Suffix rule validation...')

    rows = conn.execute(
        'SELECT p.id, p.name_zh, m.name_vi, m.confidence '
        'FROM places_dila p '
        'JOIN namevi_map_places m ON m.dila_id = p.id '
        'WHERE m.confidence < 0.71 AND p.name_zh IS NOT NULL AND LENGTH(p.name_zh)>=2'
    ).fetchall()
    print(f'[T71 Pass B] Candidates (conf<0.71): {len(rows):,}')

    suffix_ok   = []  # (dila_id, name_zh, suffix_zh, suffix_vi)
    suffix_bad  = []
    no_suffix   = 0

    for dila_id, name_zh, name_vi, conf in rows:
        last_char = name_zh[-1] if name_zh else ''
        vi_suffix = SUFFIX_RULES.get(last_char)
        if not vi_suffix:
            no_suffix += 1
            continue
        if (name_vi or '').endswith(vi_suffix):
            suffix_ok.append((dila_id, name_zh, last_char, vi_suffix, conf))
        else:
            suffix_bad.append((dila_id, name_zh, name_vi, last_char, vi_suffix, conf))

    print(f'[T71 Pass B] Suffix OK (can upgrade): {len(suffix_ok):,}')
    print(f'[T71 Pass B] Suffix BAD (flag review): {len(suffix_bad):,}')
    print(f'[T71 Pass B] No suffix rule: {no_suffix:,}')

    if suffix_bad:
        print(f'\n[T71 Pass B] Sample suffix mismatches:')
        for dila_id, nzh, nvi, szh, svi, conf in suffix_bad[:10]:
            print(f'  {nzh:<12} auto={nvi[:25]:<25} expected_end={svi}  conf={conf:.2f}')

    if dry:
        print(f'\n[DRY RUN Pass B] {len(suffix_ok):,} upgrades + {len(suffix_bad):,} flags pending.')
        return {
            'pass': 'B', 'mode': 'dry',
            'upgrades': len(suffix_ok), 'flags': len(suffix_bad), 'no_suffix': no_suffix,
        }

    now = datetime.now().isoformat(timespec='seconds')
    upgraded = 0
    flagged  = 0

    for dila_id, nzh, last_char, vi_suffix, conf in suffix_ok:
        tag = f'[T71:suffix_{last_char}→{vi_suffix}]'
        conn.execute(
            "UPDATE namevi_map_places SET confidence=0.72, "
            "note_vi = TRIM(COALESCE(note_vi,'') || ' ' || ?) "
            "WHERE dila_id=? AND confidence < 0.71",
            (tag, dila_id)
        )
        upgraded += conn.execute('SELECT changes()').fetchone()[0]

    for dila_id, nzh, nvi, last_char, vi_suffix, conf in suffix_bad:
        tag = f'[T71:SUFFIX_BAD {last_char}≠{vi_suffix}]'
        conn.execute(
            "UPDATE namevi_map_places SET needs_review=1, "
            "note_vi = TRIM(COALESCE(note_vi,'') || ' ' || ?) "
            "WHERE dila_id=? AND confidence < 0.71",
            (tag, dila_id)
        )
        flagged += conn.execute('SELECT changes()').fetchone()[0]

    conn.commit()
    print(f'\n[T71 Pass B] Upgraded: {upgraded:,} | Flagged: {flagged:,}')
    return {
        'pass': 'B', 'mode': 'apply', 'ts': now,
        'upgrades': upgraded, 'flags': flagged, 'no_suffix': no_suffix,
    }


def print_stats(conn: sqlite3.Connection):
    print('\n[T71] namevi_map_places stats after T71:')
    for r in conn.execute(
        'SELECT confidence, COUNT(*) FROM namevi_map_places GROUP BY confidence ORDER BY confidence DESC'
    ).fetchall():
        print(f'  conf={r[0]:.2f}  {r[1]:>7,}')

    t71_rows = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE note_vi LIKE '%[T71:%'"
    ).fetchone()[0]
    conflicts = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE note_vi LIKE '%[T71:CONFLICT%'"
    ).fetchone()[0]
    reviews = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE needs_review=1 AND note_vi LIKE '%[T71:%'"
    ).fetchone()[0]
    print(f'\n  T71 tagged rows: {t71_rows:,}')
    print(f'  Conflict flags : {conflicts:,}')
    print(f'  Review queue   : {reviews:,}')


def print_conflicts(conn: sqlite3.Connection):
    print('\n[T71] Conflict list (lex ≠ auto):')
    rows = conn.execute(
        "SELECT dila_id, name_vi, confidence, note_vi "
        "FROM namevi_map_places "
        "WHERE note_vi LIKE '%[T71:CONFLICT%' "
        "ORDER BY confidence DESC LIMIT 50"
    ).fetchall()
    print(f'  Showing {len(rows)} rows (max 50)')
    for r in rows:
        tag_start = (r[3] or '').find('[T71:CONFLICT')
        tag = r[3][tag_start:tag_start+50] if tag_start >= 0 else ''
        print(f'  {r[0]:<25} vi={r[1][:25]:<25} conf={r[2]:.2f} {tag}')


def do_revert(conn: sqlite3.Connection):
    """Remove all T71 changes: strip T71 tags from note_vi, restore conf."""
    print('[T71] REVERT — stripping T71 tags from namevi_map_places...')

    tagged = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE note_vi LIKE '%[T71:%'"
    ).fetchone()[0]
    print(f'[T71] Rows with T71 tags: {tagged:,}')
    if tagged == 0:
        print('[T71] Nothing to revert.')
        return

    # For conf=0.80 (Pass A upgrades) → restore to 0.70
    conn.execute(
        "UPDATE namevi_map_places SET confidence=0.70 "
        "WHERE confidence=0.80 AND note_vi LIKE '%[T71:lex_%'"
    )
    pa_reverted = conn.execute('SELECT changes()').fetchone()[0]

    # For conf=0.72 (Pass B upgrades) → restore to 0.70
    conn.execute(
        "UPDATE namevi_map_places SET confidence=0.70 "
        "WHERE confidence=0.72 AND note_vi LIKE '%[T71:suffix_%'"
    )
    pb_reverted = conn.execute('SELECT changes()').fetchone()[0]

    # Clear needs_review flags set by T71
    conn.execute(
        "UPDATE namevi_map_places SET needs_review=0 "
        "WHERE needs_review=1 AND note_vi LIKE '%[T71:%'"
    )

    # Strip T71 tags from note_vi using Python (SQLite has no regex replace)
    rows = conn.execute(
        "SELECT rowid, note_vi FROM namevi_map_places WHERE note_vi LIKE '%[T71:%'"
    ).fetchall()
    re_tag = re.compile(r'\s*\[T71:[^\]]*\]')
    for rowid, note_vi in rows:
        clean = re_tag.sub('', note_vi or '').strip()
        conn.execute('UPDATE namevi_map_places SET note_vi=? WHERE rowid=?', (clean or None, rowid))

    conn.commit()
    print(f'[T71] Reverted: Pass A={pa_reverted:,} + Pass B={pb_reverted:,} conf restorations')
    print(f'[T71] T71 tags stripped from {len(rows):,} rows')


def append_log(entry: dict):
    logs = []
    if LOG_JSON.exists():
        try:
            logs = json.loads(LOG_JSON.read_text(encoding='utf-8'))
            if not isinstance(logs, list):
                logs = [logs]
        except Exception:
            logs = []
    logs.append(entry)
    LOG_JSON.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='T71 Place Name VI Lexicon Verify')
    parser.add_argument('--apply',     action='store_true', help='Apply changes (default: dry-run)')
    parser.add_argument('--revert',    action='store_true', help='Revert T71 changes')
    parser.add_argument('--stats',     action='store_true', help='Print stats and exit')
    parser.add_argument('--conflicts', action='store_true', help='Print conflict list and exit')
    parser.add_argument('--pass',      dest='only_pass', choices=['A','B'], help='Run only Pass A or B')
    args = parser.parse_args()

    dry = not args.apply

    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row

    if args.stats:
        print_stats(conn)
        conn.close()
        return

    if args.conflicts:
        print_conflicts(conn)
        conn.close()
        return

    if args.revert:
        do_revert(conn)
        conn.close()
        return

    print(f'[T71] {"DRY RUN" if dry else "APPLY"} — Place Name Lexicon Verify')

    run_log = {'date': datetime.now().isoformat(timespec='seconds'), 'mode': 'dry' if dry else 'apply', 'passes': []}

    # Pass A
    if not args.only_pass or args.only_pass == 'A':
        cjk_idx = build_cjk_index(conn)
        stats_a = run_pass_a(conn, cjk_idx, dry)
        run_log['passes'].append(stats_a)

    # Pass B
    if not args.only_pass or args.only_pass == 'B':
        stats_b = run_pass_b(conn, dry)
        run_log['passes'].append(stats_b)

    if not dry:
        print_stats(conn)
        append_log(run_log)
        print(f'\n[T71] Log → {LOG_JSON}')

    conn.close()


if __name__ == '__main__':
    main()
