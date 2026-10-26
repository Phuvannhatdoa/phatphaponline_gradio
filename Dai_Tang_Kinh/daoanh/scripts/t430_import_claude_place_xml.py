#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T443 (Part 1) - Import Claude places + districts tu XML GitHub.

Nguon: nhanh claude/sleepy-tesla-qsx17b
- Places:    data/phien_am/vn_place_name_vi.xml    (~59.353 <place>)
- Districts: data/phien_am/vn_district_name_vi.xml (~16.907 <unit>)

Bang dich (tao moi, KHONG dung vao bang goc):
- codex_place_name    : anh xa 1-1 voi codex_person_name (T418)
- codex_district_name : da ton tai (16.907 dong, T428) -> chi INSERT OR IGNORE

Rang buoc (done_when T443):
- Khong UPDATE/DELETE places, places_dila, namevi_map_places.
- name_zh_mismatch=1 khi name_zh trong XML khac places_dila.name_zh.
- place khong co trong places_dila -> status='orphan-chua co ID Dila' + CSV orphan.
- --dry-run chi doc; --apply phai co backup + PRAGMA quick_check=ok truoc khi ghi.
- Manifest ghi commit/model/xml_sha256 + so lieu de revert/truy vet.

Usage:
  python -X utf8 scripts/t430_import_claude_place_xml.py --dry-run
  python -X utf8 scripts/t430_import_claude_place_xml.py --apply   # can Admin duyet
  python -X utf8 scripts/t430_import_claude_place_xml.py --verify
"""

import argparse
import csv
import hashlib
import io
import os
import sqlite3
import sys
import time
import urllib.request
from xml.etree import ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

RAW_BASE = ('https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/'
            'claude/sleepy-tesla-qsx17b/data/phien_am/')
PLACES_XML_URL = RAW_BASE + 'vn_place_name_vi.xml'
DISTRICTS_XML_URL = RAW_BASE + 'vn_district_name_vi.xml'

MODEL = 'claude-xml-import@sleepy-tesla-qsx17b'
TS = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

PLACES_MODEL = 'CLAUDE'
GUARDED_TABLES = ('places', 'places_dila', 'namevi_map_places')


def now_stamp():
    return time.strftime('%Y%m%d_%H%M%S')


def fetch(url, local_path=None):
    """Tra ve (bytes, sha256, nguon). Uu tien file local neu co."""
    if local_path:
        with open(local_path, 'rb') as fh:
            content = fh.read()
        sha = hashlib.sha256(content).hexdigest()
        print(f'  [local] {local_path} ({len(content):,} bytes, sha256={sha[:16]}...)')
        return content, sha, local_path

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=180) as resp:
        content = resp.read()
    sha = hashlib.sha256(content).hexdigest()
    print(f'  [http] {url} ({len(content):,} bytes, sha256={sha[:16]}...)')
    return content, sha, url


def iter_places(xml_bytes):
    """Generator iterparse: khong nap ca cay vao RAM."""
    stream = io.BytesIO(xml_bytes)
    for _, elem in ET.iterparse(stream, events=('end',)):
        if elem.tag != 'place':
            continue
        dila_id = (elem.get('dila_id') or '').strip()
        name_zh = (elem.findtext('name_zh') or '').strip()
        if not dila_id or not name_zh:
            elem.clear()
            continue
        yield {
            'dila_id': dila_id,
            'name_zh': name_zh,
            'name_vi': (elem.findtext('name_vi') or '').strip(),
            'tier': (elem.get('tier') or '').strip(),
            'review': (elem.findtext('review') or '').strip(),
            'alternatives': (elem.findtext('alternatives') or '').strip(),
            'district_zh': (elem.findtext('district_zh') or '').strip(),
            'district_vi': (elem.findtext('district_vi') or '').strip(),
        }
        elem.clear()


def iter_districts(xml_bytes):
    """Generator iterparse cho <unit> (district XML)."""
    stream = io.BytesIO(xml_bytes)
    for _, elem in ET.iterparse(stream, events=('end',)):
        if elem.tag != 'unit':
            continue
        dila_id = (elem.get('dila_id') or '').strip()
        name_zh = (elem.findtext('name_zh') or '').strip()
        if not dila_id or not name_zh:
            elem.clear()
            continue
        yield {
            'dila_id': dila_id,
            'name_zh': name_zh,
            'name_vi': (elem.findtext('name_vi') or '').strip(),
            'type': (elem.get('type') or '').strip(),
            'tier': (elem.get('tier') or '').strip(),
        }
        elem.clear()


def open_db(readonly=False):
    if readonly:
        uri = 'file:' + DB_PATH.replace(os.sep, '/') + '?mode=ro'
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(DB_PATH)


def create_tables(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS codex_place_name (
            dila_id          TEXT PRIMARY KEY,
            name_zh_xml      TEXT,
            name_vi          TEXT,
            tier             TEXT,
            review           TEXT,
            rule             TEXT,
            evidence         TEXT,
            alternatives     TEXT,
            model            TEXT,
            status           TEXT,
            name_zh_mismatch INTEGER DEFAULT 0,
            xml_sha256       TEXT,
            created_at       TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS codex_district_name (
            dila_id         TEXT PRIMARY KEY,
            name_zh         TEXT,
            name_vi         TEXT,
            type            TEXT,
            tier            TEXT,
            review          TEXT,
            alternatives    TEXT,
            tier_zh         TEXT,
            xml_sha256      TEXT,
            model           TEXT DEFAULT 'claude-xml-import@sleepy-tesla-qsx17b',
            status          TEXT DEFAULT 'suggested',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_codex_place_name_status '
                 'ON codex_place_name(status)')
    conn.commit()


def table_counts(conn, tables):
    out = {}
    for t in tables:
        try:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except sqlite3.Error:
            out[t] = None
    return out


def build_places_index(conn):
    """dila_id -> name_zh tu places_dila (nguon so sanh mismatch)."""
    return {r[0]: (r[1] or '').strip()
            for r in conn.execute('SELECT id, name_zh FROM places_dila')}


def analyse(conn, places, districts):
    db_zh = build_places_index(conn)
    existing_places = {r[0] for r in conn.execute('SELECT dila_id FROM codex_place_name')} \
        if _table_exists(conn, 'codex_place_name') else set()
    existing_districts = {r[0] for r in conn.execute('SELECT dila_id FROM codex_district_name')} \
        if _table_exists(conn, 'codex_district_name') else set()

    stats = {
        'places_xml': len(places),
        'places_matched': 0,
        'places_orphan': 0,
        'places_mismatch': 0,
        'places_dup_id': 0,
        'places_already': 0,
        'places_tier_empty': 0,
        'districts_xml': len(districts),
        'districts_matched': 0,
        'districts_orphan': 0,
        'districts_already': 0,
        'districts_dup_id': 0,
    }

    seen = set()
    orphans = []
    mismatches = []
    for p in places:
        did = p['dila_id']
        if did in seen:
            stats['places_dup_id'] += 1
        seen.add(did)
        if did in existing_places:
            stats['places_already'] += 1
        if not p['tier']:
            stats['places_tier_empty'] += 1

        ref_zh = db_zh.get(did)
        if ref_zh is None:
            stats['places_orphan'] += 1
            orphans.append((did, p['name_zh'], p['name_vi'], p['district_zh'] or ''))
        else:
            stats['places_matched'] += 1
            if ref_zh and ref_zh != p['name_zh']:
                stats['places_mismatch'] += 1
                mismatches.append((did, ref_zh, p['name_zh'], p['name_vi']))

    seen_d = set()
    for d in districts:
        did = d['dila_id']
        if did in seen_d:
            stats['districts_dup_id'] += 1
        seen_d.add(did)
        if did in existing_districts:
            stats['districts_already'] += 1

    # District dung namespace rieng (PLA...), khong so voi places_dila (PL...):
    # "orphan" = chua co trong codex_district_name.
    stats['districts_orphan'] = len(seen_d - existing_districts)
    stats['districts_matched'] = len(seen_d & existing_districts) if existing_districts else 0
    stats['districts_in_places_dila_district'] = len(
        {d['name_zh'] for d in districts} & {r[0] for r in conn.execute(
            'SELECT DISTINCT district FROM places_dila WHERE district IS NOT NULL')})
    return stats, orphans, mismatches


def _table_exists(conn, name):
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return bool(row)


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f'  [csv] {path} ({len(rows)} dong)')


def write_manifest(out_dir, places_sha, districts_sha, stats, orphans, mismatches):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'T443_manifest.txt')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('T443 (T428 Part 1) - Claude places + districts import\n')
        fh.write('=' * 64 + '\n')
        fh.write(f'time         : {TS}\n')
        fh.write(f'model        : {MODEL}\n')
        fh.write(f'places_xml   : {places_sha}\n')
        fh.write(f'districts_xml: {districts_sha}\n')
        fh.write(f'db           : {DB_PATH}\n')
        fh.write('\nStats:\n')
        for k in sorted(stats):
            fh.write(f'  {k}: {stats[k]}\n')
        fh.write(f'\nOrphan places CSV : {os.path.join(out_dir, "T443_orphans.csv")}\n')
        fh.write(f'Mismatch CSV      : {os.path.join(out_dir, "T443_mismatch.csv")}\n')
        fh.write(f'\nOrphans: {len(orphans)} | Mismatch name_zh: {len(mismatches)}\n')
        fh.write('\nRevert (khong mat du lieu goc):\n'
                 '  DROP TABLE codex_place_name;\n'
                 '  -- codex_district_name: chi xoa cac dong cua lan chay nay neu can\n')
    print(f'  [manifest] {path}')
    return path


def backup_db():
    ts = now_stamp()
    bdir = os.path.join(BASE_DIR, 'data', 'backups', f'T443_{ts}')
    os.makedirs(bdir, exist_ok=True)
    bpath = os.path.join(bdir, 'lineage.db')
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(bpath)
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
    qc = src.execute('PRAGMA quick_check').fetchone()[0]
    src.close()
    print(f'[backup] {bpath} (quick_check={qc})')
    if qc != 'ok':
        raise SystemExit('[STOP] quick_check FAIL - khong ghi DB.')
    return bpath, bdir


def import_places(conn, places, matched, sha):
    inserted = skipped = 0
    for p in places:
        did = p['dila_id']
        ref_zh = matched.get(did)
        mismatch = 0 if ref_zh is None else int(bool(ref_zh) and ref_zh != p['name_zh'])
        status = 'suggested' if ref_zh is not None else 'orphan-chua co ID Dila'
        cur = conn.execute('''
            INSERT OR IGNORE INTO codex_place_name
            (dila_id, name_zh_xml, name_vi, tier, review, rule, evidence,
             alternatives, model, status, name_zh_mismatch, xml_sha256, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (did, p['name_zh'], p['name_vi'], p['tier'] or None, p['review'] or None,
              None, None, p['alternatives'] or None, MODEL, status, mismatch, sha, TS))
        if cur.rowcount:
            inserted += 1
        else:
            skipped += 1
    return {'inserted': inserted, 'skipped': skipped}


def import_districts(conn, districts, sha):
    inserted = skipped = 0
    for d in districts:
        cur = conn.execute('''
            INSERT OR IGNORE INTO codex_district_name
            (dila_id, name_zh, name_vi, type, tier, model, status, xml_sha256, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (d['dila_id'], d['name_zh'], d['name_vi'], d['type'] or None,
              d['tier'] or None, MODEL, 'suggested', sha, TS))
        if cur.rowcount:
            inserted += 1
        else:
            skipped += 1
    return {'inserted': inserted, 'skipped': skipped}


def cmd_dry_run(args):
    print('=== T443 DRY-RUN (khong ghi DB) ===')
    places_xml, p_sha, p_src = fetch(PLACES_XML_URL, args.places_xml)
    dist_xml, d_sha, d_src = fetch(DISTRICTS_XML_URL, args.districts_xml)
    print(f'  sources: {p_src} | {d_src}')

    places = list(iter_places(places_xml))
    districts = list(iter_districts(dist_xml))
    print(f'  parsed: {len(places)} places, {len(districts)} districts')

    conn = open_db(readonly=True)
    try:
        before = table_counts(conn, GUARDED_TABLES + ('codex_district_name', 'codex_place_name'))
        print(f'  before: {before}')
        stats, orphans, mismatches = analyse(conn, places, districts)
        after = table_counts(conn, GUARDED_TABLES + ('codex_district_name', 'codex_place_name'))
        assert before == after, 'DRY-RUN da ghi DB - LOI NGHIEM TRONG'
    finally:
        conn.close()

    out_dir = os.path.join(BASE_DIR, 'docs', 'sessions', time.strftime('%Y-%m-%d'),
                           'T443')
    write_csv(os.path.join(out_dir, 'T443_orphans.csv'),
              ['dila_id', 'name_zh', 'name_vi', 'district_zh'], orphans[:args.max_csv])
    write_csv(os.path.join(out_dir, 'T443_mismatch.csv'),
              ['dila_id', 'places_dila_name_zh', 'xml_name_zh', 'xml_name_vi'],
              mismatches[:args.max_csv])
    write_manifest(out_dir, p_sha, d_sha, stats, orphans, mismatches)

    print('\n--- STATS ---')
    for k in sorted(stats):
        print(f'  {k:22s} {stats[k]}')
    print(f'\nDRY-RUN xong. Orphan={len(orphans)}, mismatch={len(mismatches)}')
    if stats['places_orphan'] and not args.max_csv:
        print('  (CSV bi gioi han 0 dong; dung --max-csv de ghi day du)')
    return 0


def cmd_apply(args):
    print('=== T443 APPLY ===')
    if not args.yes:
        print('[STOP] --apply can them --yes sau khi Admin duyet dry-run.', file=sys.stderr)
        return 2

    places_xml, p_sha, _ = fetch(PLACES_XML_URL, args.places_xml)
    dist_xml, d_sha, _ = fetch(DISTRICTS_XML_URL, args.districts_xml)
    places = list(iter_places(places_xml))
    districts = list(iter_districts(dist_xml))

    conn = open_db(readonly=True)
    try:
        before = table_counts(conn, GUARDED_TABLES)
        matched = build_places_index(conn)
    finally:
        conn.close()
    print(f'  guarded tables before: {before}')

    backup_path, backup_dir = backup_db()

    conn = open_db()
    try:
        create_tables(conn)
        conn.execute('BEGIN')
        p_stats = import_places(conn, places, matched, p_sha)
        d_stats = import_districts(conn, districts, d_sha)
        after = table_counts(conn, GUARDED_TABLES)
        if after != before:
            conn.rollback()
            raise SystemExit(f'[STOP] bang goc bi thay doi: {before} -> {after}. Da rollback.')
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f'  codex_place_name    +{p_stats["inserted"]} (skip {p_stats["skipped"]})')
    print(f'  codex_district_name +{d_stats["inserted"]} (skip {d_stats["skipped"]})')

    conn = open_db(readonly=True)
    try:
        stats, orphans, mismatches = analyse(conn, places, districts)
        stats['apply_places_inserted'] = p_stats['inserted']
        stats['apply_districts_inserted'] = d_stats['inserted']
    finally:
        conn.close()

    out_dir = backup_dir
    write_csv(os.path.join(out_dir, 'T443_orphans.csv'),
              ['dila_id', 'name_zh', 'name_vi', 'district_zh'], orphans)
    write_csv(os.path.join(out_dir, 'T443_mismatch.csv'),
              ['dila_id', 'places_dila_name_zh', 'xml_name_zh', 'xml_name_vi'], mismatches)
    write_manifest(out_dir, p_sha, d_sha, stats, orphans, mismatches)

    print(f'\n[backup] giu de revert: {backup_path}')
    print('APPLY xong. Khong UPDATE places/places_dila/namevi_map_places.')
    return 0


def cmd_verify(args):
    print('=== T443 VERIFY ===')
    conn = open_db(readonly=True)
    try:
        for t in ('codex_place_name', 'codex_district_name'):
            if not _table_exists(conn, t):
                print(f'  {t}: MISSING')
                continue
            total = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
            with_vi = conn.execute(
                f"SELECT COUNT(*) FROM {t} WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]
            print(f'  {t}: {total:,} dong, {with_vi:,} co name_vi')
        if _table_exists(conn, 'codex_place_name'):
            print('  theo status/tier:')
            for row in conn.execute('SELECT status, tier, COUNT(*) FROM codex_place_name '
                                    'GROUP BY 1,2 ORDER BY 3 DESC'):
                print(f'    {row[0]} tier={row[1]}: {row[2]}')
            print('  mismatch:', conn.execute(
                'SELECT COUNT(*) FROM codex_place_name WHERE name_zh_mismatch=1').fetchone()[0])
        guarded = table_counts(conn, GUARDED_TABLES)
        print(f'  guarded (khong duoc doi): {guarded}')
    finally:
        conn.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description='T443 - import Claude places + districts (XML)')
    ap.add_argument('--dry-run', action='store_true', help='Chi bao cao, khong ghi DB')
    ap.add_argument('--apply', action='store_true', help='Ghi DB (can --yes)')
    ap.add_argument('--verify', action='store_true', help='Kiem tra sau apply')
    ap.add_argument('--yes', action='store_true', help='Xac nhan da duoc Admin duyet')
    ap.add_argument('--places-xml', default=None, help='Dung file XML places local')
    ap.add_argument('--districts-xml', default=None, help='Dung file XML districts local')
    ap.add_argument('--max-csv', type=int, default=5000, help='Gioi han dong CSV (dry-run)')
    args = ap.parse_args()

    if args.apply:
        return cmd_apply(args)
    if args.verify:
        return cmd_verify(args)
    return cmd_dry_run(args)


if __name__ == '__main__':
    sys.exit(main())
