#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T428 Part 1 — Import Claude phiên âm Places + Districts từ XML GitHub.

Nguồn: GitHub nhánh claude/sleepy-tesla-qsx17b
- Places: https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/claude/sleepy-tesla-qsx17b/data/phien_am/vn_place_name_vi.xml (59.353)
- Districts: https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/claude/sleepy-tesla-qsx17b/data/phien_am/vn_district_name_vi.xml (16.907)

Chiến lược:
- Places: cập nhật namevi_map_places.name_vi (chỉ fill ô trống, không overwrite)
- Districts: tạo bảng codex_district_name (mới) để lưu Claude phiên âm districts (tương tự codex_person_name của T418)
- Ghi manifest + CSV để rollback.
- Không overwrite: chỉ UPDATE/INSERT khi trường đích NULL/rỗng.

Usage:
  python scripts/t428_import_claude_xml.py --dry-run    # chỉ báo cáo
  python scripts/t428_import_claude_xml.py --apply      # chạy thật
  python scripts/t428_import_claude_xml.py --verify     # verify sau apply
"""

import argparse
import hashlib
import os
import sqlite3
import sys
import time
import urllib.request
from xml.etree import ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
OUT_DIR = os.path.join(BASE_DIR, 'docs', 'sessions', '2026-10-20', 'T428')

# GitHub URLs (nhánh claude/sleepy-tesla-qsx17b)
PLACES_XML_URL = 'https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/claude/sleepy-tesla-qsx17b/data/phien_am/vn_place_name_vi.xml'
DISTRICTS_XML_URL = 'https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/claude/sleepy-tesla-qsx17b/data/phien_am/vn_district_name_vi.xml'

TS = time.strftime('%Y-%m-%d %H:%M:%S')


def now_stamp():
    return time.strftime('%Y%m%d_%H%M%S')


def download_xml(url):
    print(f'  Downloading: {url}')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
    sha256 = hashlib.sha256(content).hexdigest()
    print(f'  Size: {len(content):,} bytes, SHA256: {sha256}')
    return content, sha256


def parse_places_xml(xml_bytes):
    """Parse places XML, yield dict for each <place>."""
    root = ET.fromstring(xml_bytes)
    for place in root.findall('place'):
        dila_id = place.get('dila_id')
        tier = place.get('tier')
        name_zh = place.findtext('name_zh', '').strip()
        name_vi = place.findtext('name_vi', '').strip()
        category_zh = place.findtext('category_zh', '').strip()
        district_zh = place.findtext('district_zh', '').strip()
        district_vi = place.findtext('district_vi', '').strip()
        review = place.findtext('review', '').strip()
        alternatives = place.findtext('alternatives', '').strip()
        if dila_id and name_zh:
            yield {
                'dila_id': dila_id,
                'tier': tier,
                'name_zh': name_zh,
                'name_vi': name_vi,
                'category_zh': category_zh,
                'district_zh': district_zh,
                'district_vi': district_vi,
                'review': review,
                'alternatives': alternatives,
            }


def parse_districts_xml(xml_bytes):
    """Parse districts XML, yield dict for each <unit>."""
    root = ET.fromstring(xml_bytes)
    for unit in root.findall('unit'):
        dila_id = unit.get('dila_id')
        utype = unit.get('type')
        tier = unit.get('tier')
        name_zh = unit.findtext('name_zh', '').strip()
        name_vi = unit.findtext('name_vi', '').strip()
        if dila_id and name_zh:
            yield {
                'dila_id': dila_id,
                'type': utype,
                'tier': tier,
                'name_zh': name_zh,
                'name_vi': name_vi,
            }


def open_db():
    return sqlite3.connect(DB_PATH)


def backup_db():
    ts = time.strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join('data', 'backups', f'T428_{ts}')
    os.makedirs(bdir, exist_ok=True)
    bpath = os.path.join(bdir, 'lineage.db')
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(bpath)
    with dst:
        src.backup(dst)
    dst.close()
    qc = src.execute('PRAGMA quick_check').fetchone()[0]
    src.close()
    print(f'[backup] {bpath} (quick_check={qc})')
    if qc != 'ok':
        raise SystemExit('quick_check FAIL — dừng, không ghi DB.')
    return bpath


def create_district_table(conn):
    """Tạo bảng codex_district_name nếu chưa có (tương tự codex_person_name của T418)."""
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
    conn.commit()


def import_places(conn, places, dry_run):
    """Import places: update namevi_map_places.name_vi where NULL/empty."""
    updated = 0
    inserted = 0
    skipped = 0
    mismatched = 0

    # Build lookup: dila_id -> existing name_vi
    cur = conn.cursor()
    for p in places:
        dila_id = p['dila_id']
        name_vi = p['name_vi']
        name_zh = p['name_zh']
        district_zh = p['district_zh']
        district_vi = p['district_vi']
        tier = p['tier']
        review = p['review']
        alternatives = p['alternatives']

        # Check existing in namevi_map_places
        row = cur.execute('SELECT name_vi, name_zh FROM namevi_map_places WHERE dila_id=?', (dila_id,)).fetchone()

        if row:
            existing_vi, existing_zh = row
            if existing_vi and existing_vi.strip():
                # Already has name_vi - skip (no overwrite)
                skipped += 1
                if existing_zh != name_zh:
                    mismatched += 1
                continue
            # Existing row but name_vi is empty - UPDATE
            if not dry_run:
                cur.execute(
                    'UPDATE namevi_map_places SET name_vi=?, note_vi=?, source=? WHERE dila_id=?',
                    (name_vi, f'Claude tier={tier}', 'claude_xml_import', dila_id)
                )
            updated += 1
        else:
            # No existing row - INSERT new (use short ID format?)
            # Try to match with places_dila
            short_id = dila_id
            if dila_id.startswith('PL') and len(dila_id) > 8:
                short_id = dila_id[-8:]  # Last 8 chars
            if not dry_run:
                cur.execute('''
                    INSERT OR IGNORE INTO namevi_map_places
                    (id, name_vi, name_zh, dila_id, confidence, source, created_at, needs_review, note_vi, district_vi, vn_name_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    short_id, name_vi, name_zh, dila_id, 0.95, 'claude_xml_import', TS, 0,
                    f'Claude tier={tier}', district_vi, 'pending'
                ))
            inserted += 1

    if not dry_run:
        conn.commit()
    return {'updated': updated, 'inserted': inserted, 'skipped': skipped, 'mismatched': mismatched}


def import_districts(conn, districts, dry_run):
    """Import districts: create codex_district_name table and insert."""
    create_district_table(conn)
    cur = conn.cursor()

    inserted = 0
    updated = 0
    skipped = 0

    for d in districts:
        dila_id = d['dila_id']
        name_zh = d['name_zh']
        name_vi = d['name_vi']
        utype = d['type']
        tier = d['tier']

        row = cur.execute('SELECT name_vi FROM codex_district_name WHERE dila_id=?', (dila_id,)).fetchone()
        if row:
            if row[0] and row[0].strip():
                skipped += 1
                continue
            if not dry_run:
                cur.execute('UPDATE codex_district_name SET name_vi=?, type=?, tier=? WHERE dila_id=?',
                           (name_vi, d['type'], d['tier'], dila_id))
            updated += 1
        else:
            if not dry_run:
                cur.execute('''
                    INSERT INTO codex_district_name
                    (dila_id, name_zh, name_vi, type, tier, model, status, created_at)
                    VALUES (?,?,?,?,?,?,?,?)
                ''', (dila_id, name_zh, name_vi, utype, tier,
                      'claude-xml-import@sleepy-tesla-qsx17b', 'suggested', TS))
            inserted += 1

    if not dry_run:
        conn.commit()
    return {'inserted': inserted, 'updated': updated, 'skipped': skipped}


def write_manifest(places_sha, districts_sha, places_stats, districts_stats, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = os.path.join(out_dir, f't428_manifest_{time.strftime("%Y%m%d_%H%M%S")}.txt')
    with open(manifest, 'w', encoding='utf-8') as f:
        f.write(f'T428 Manifest - {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('=' * 60 + '\n')
        f.write(f'Places XML SHA256: {places_sha}\n')
        f.write(f'Districts XML SHA256: {districts_sha}\n')
        f.write('\nPlaces stats:\n')
        for k, v in places_stats.items():
            f.write(f'  {k}: {v}\n')
        f.write('\nDistricts stats:\n')
        for k, v in districts_stats.items():
            f.write(f'  {k}: {v}\n')
    print(f'[manifest] {manifest}')
    return manifest


def run_dry_run():
    print('=== T428 DRY-RUN ===')
    places_xml, places_sha = download_xml(PLACES_XML_URL)
    districts_xml, districts_sha = download_xml(DISTRICTS_XML_URL)

    places = list(parse_places_xml(places_xml))
    districts = list(parse_districts_xml(districts_xml))

    print(f'Places parsed: {len(places)}')
    print(f'Districts parsed: {len(districts)}')

    conn = open_db()
    # Test queries
    cur = conn.cursor()

    # Check how many places have matching dila_id in namevi_map_places
    places_with_dila = [p for p in places if p['dila_id'].startswith('PL')]
    matched = 0
    for p in places_with_dila[:100]:
        row = conn.execute('SELECT 1 FROM namevi_map_places WHERE dila_id=?', (p['dila_id'],)).fetchone()
        if row:
            matched += 1
    print(f'Sample 100 places: {matched} have existing row in namevi_map_places')

    # Check districts
    print(f'Districts will go to codex_district_name (new table)')
    for d in districts[:5]:
        print(f'  {d["dila_id"]} {d["name_zh"]} -> {d["name_vi"]} (type={d["type"]})')

    conn.close()
    print('\nDRY-RUN hoàn tất. Chạy --apply để ghi DB.')


def run_apply():
    print('=== T428 APPLY ===')
    places_xml, places_sha = download_xml(PLACES_XML_URL)
    districts_xml, districts_sha = download_xml(DISTRICTS_XML_URL)

    places = list(parse_places_xml(places_xml))
    districts = list(parse_districts_xml(districts_xml))

    print(f'Places: {len(places)}, Districts: {len(districts)}')

    # Backup
    backup_path = backup_db()

    conn = open_db()
    try:
        # Import places
        print('[1/2] Importing places...')
        places_stats = import_places(conn, places, dry_run=False)
        print(f'  Updated: {places_stats["updated"]}, Inserted: {places_stats["inserted"]}, Skipped: {places_stats["skipped"]}, Mismatched: {places_stats["mismatched"]}')

        # Import districts
        print('[2/2] Importing districts...')
        districts_stats = import_districts(conn, districts, dry_run=False)
        print(f'  Inserted: {districts_stats["inserted"]}, Updated: {districts_stats["updated"]}, Skipped: {districts_stats["skipped"]}')

        # Write manifest
        write_manifest(places_sha, districts_sha, places_stats, districts_stats, OUT_DIR)

    finally:
        conn.close()

    print(f'\n[backup] Giữ cho revert: {backup_path}')
    print('APPLY hoàn tất.')


def run_verify():
    print('=== T428 VERIFY ===')
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Places verify
    total_places = cur.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
    with_vi = cur.execute('SELECT COUNT(*) FROM namevi_map_places WHERE name_vi IS NOT NULL AND name_vi != ""').fetchone()[0]
    print(f'namevi_map_places có name_vi: {with_vi:,} / {total_places:,}')

    # Districts verify
    try:
        total_districts = cur.execute('SELECT COUNT(*) FROM codex_district_name').fetchone()[0]
        with_vi = cur.execute('SELECT COUNT(*) FROM codex_district_name WHERE name_vi IS NOT NULL AND name_vi != ""').fetchone()[0]
        print(f'codex_district_name: {with_vi:,} / {total_districts:,} có name_vi')
    except Exception as e:
        print(f'codex_district_name: ERR - {e}')

    conn.close()


def main():
    ap = argparse.ArgumentParser(description='T428 Part 1 — Import Claude XML Places + Districts')
    ap.add_argument('--dry-run', action='store_true', help='Chỉ báo cáo, không ghi DB')
    ap.add_argument('--apply', action='store_true', help='GHI DB (chỉ khi Admin duyệt)')
    ap.add_argument('--verify', action='store_true', help='Verify sau apply')
    args = ap.parse_args()

    if args.verify:
        run_verify()
    elif args.apply:
        run_apply()
    else:
        run_dry_run()


if __name__ == '__main__':
    main()