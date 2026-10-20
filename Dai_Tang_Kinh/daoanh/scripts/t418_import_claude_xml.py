#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T418 PART 1 — Import Claude-translated XML (vn_person_name_vi.xml) vao bang moi
codex_person_name trong lineage.db.

Nguon XML co dinh theo commit SHA (KHONG dung branch):
  https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/0d2ea40/data/phien_am/vn_person_name_vi.xml

Nguyen tac (theo tasks/T418-gemini-translation-incomplete.md, admin da duyet):
  - Zero-RAM: parse bang xml.etree.ElementTree.iterparse (generator), khong load
    ca cay XML vao RAM.
  - Tao bang MOI codex_person_name (CREATE TABLE IF NOT EXISTS). KHONG ALTER
    bat ky bang nao khac (people, name_vi_map, entity_claims, ai_person_name
    deu giu nguyen).
  - Matched (dila_id co trong people.id) -> status='suggested'.
  - Orphan (dila_id KHONG co trong people.id) -> status='orphan-chua co ID Dila'.
  - model = 'claude-xml-import@0d2ea40' cho moi dong.
  - name_zh_mismatch = 1 neu name_zh trong XML khac people.name_zh tuong ung.
  - Idempotent: co the chay lai an toan (kiem tra da ton tai truoc khi insert lai).
  - --dry-run: khong ghi DB, chi in bao cao.
  - --apply: thuc su ghi (ket qua tinh toan truoc, khong backup tu dong trong
    script nay vi backup thu cong da lam truoc khi chay - xem outcome trong
    tasks/T418-gemini-translation-incomplete.md).
  - --revert: DROP TABLE codex_person_name (bang moi, khong anh huong bang khac).

Usage:
    python scripts/t418_import_claude_xml.py --dry-run
    python scripts/t418_import_claude_xml.py --apply
    python scripts/t418_import_claude_xml.py --revert
"""

import os
import sys
import json
import sqlite3
import hashlib
import argparse
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
XML_URL = (
    "https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/"
    "0d2ea40/data/phien_am/vn_person_name_vi.xml"
)
XML_COMMIT = "0d2ea40"
MODEL_TAG = f"claude-xml-import@{XML_COMMIT}"
SESSION_DIR = os.path.join(BASE_DIR, 'docs', 'sessions', '2026-10-19', 'T418')
EXPECTED_PERSON_COUNT = 49335
EXPECTED_MATCHED = 48646
EXPECTED_ORPHAN = 689


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(conn):
    """Tao bang moi codex_person_name neu chua ton tai. Khong dong toi bang nao khac."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS codex_person_name (
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
    """)
    conn.commit()


def download_xml():
    """Tai XML tu commit SHA co dinh, luu vao file tam, tinh SHA-256.
    KHONG load ca noi dung vao RAM mot luc - doc theo chunk de hash + ghi file."""
    log(f"Dang tai XML tu: {XML_URL}")
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.xml', prefix='t418_')
    os.close(tmp_fd)
    sha256 = hashlib.sha256()
    try:
        req = urllib.request.Request(XML_URL, headers={'User-Agent': 'T418-import-script'})
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp_path, 'wb') as f:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                sha256.update(chunk)
                f.write(chunk)
    except Exception as e:
        raise RuntimeError(f"LOI: Khong tai duoc XML tu GitHub: {e}")
    digest = sha256.hexdigest()
    size = os.path.getsize(tmp_path)
    log(f"Da tai xong: {size} bytes, SHA-256={digest}")
    return tmp_path, digest


def iter_persons(xml_path):
    """Generator: duyet XML bang iterparse, yield dict moi <person>, roi clear()
    de giai phong RAM ngay (Zero-RAM principle)."""
    context = ET.iterparse(xml_path, events=('end',))
    for event, elem in context:
        if elem.tag == 'person':
            dila_id = elem.get('dila_id')
            tier = elem.get('tier')
            name_zh = elem.findtext('name_zh')
            name_vi = elem.findtext('name_vi')
            review = elem.findtext('review')
            rule = elem.findtext('rule')
            evidence = elem.findtext('evidence')
            alternatives = elem.findtext('alternatives')
            yield {
                'dila_id': dila_id,
                'tier': tier,
                'name_zh_xml': name_zh,
                'name_vi': name_vi,
                'review': review,
                'rule': rule,
                'evidence': evidence,
                'alternatives': alternatives,
            }
            # Giai phong <person> SAU KHI da doc xong du lieu con cua no
            # (name_zh/name_vi/...) de khong tich luy RAM nhung khong lam mat
            # text truoc khi findtext() doc duoc.
            elem.clear()


def load_people_map(conn):
    """Tra ve dict {dila_id: name_zh} tu bang people (chi doc, khong sua)."""
    cur = conn.execute("SELECT id, name_zh FROM people")
    return {row['id']: row['name_zh'] for row in cur.fetchall()}


def run(dry_run=True, apply_=False):
    if not apply_:
        dry_run = True

    os.makedirs(SESSION_DIR, exist_ok=True)

    conn = get_db()
    try:
        people_map = load_people_map(conn)
        log(f"So nguoi hien co trong bang people: {len(people_map)}")

        if apply_:
            ensure_table(conn)

        # Kiem tra idempotent: neu bang da co du lieu voi dung model tag nay,
        # bao cao va khong insert lai.
        already = set()
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='codex_person_name'"
        )
        table_exists = cur.fetchone() is not None
        if table_exists:
            cur = conn.execute(
                "SELECT dila_id FROM codex_person_name WHERE model = ?", (MODEL_TAG,)
            )
            already = {r['dila_id'] for r in cur.fetchall()}
            log(f"Da co {len(already)} dila_id voi model='{MODEL_TAG}' trong codex_person_name (se bo qua khi insert lai).")

        xml_path, xml_sha256 = download_xml()

        matched_rows = []
        orphan_rows = []
        mismatch_count = 0
        person_count = 0
        now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        try:
            for p in iter_persons(xml_path):
                person_count += 1
                dila_id = p['dila_id']
                if not dila_id:
                    continue
                name_zh_db = people_map.get(dila_id)
                is_matched = dila_id in people_map
                mismatch = 0
                if is_matched and name_zh_db is not None and name_zh_db != p['name_zh_xml']:
                    mismatch = 1
                    mismatch_count += 1
                status = 'suggested' if is_matched else 'orphan-chưa có ID Dila'

                row = (
                    dila_id,
                    p['name_zh_xml'],
                    p['name_vi'],
                    p['tier'],
                    p['review'],
                    p['rule'],
                    p['evidence'],
                    p['alternatives'],
                    MODEL_TAG,
                    status,
                    mismatch,
                    xml_sha256,
                    now_iso,
                )
                if is_matched:
                    matched_rows.append(row)
                else:
                    orphan_rows.append(row)
        finally:
            try:
                os.remove(xml_path)
            except OSError:
                pass

        log(f"Tong so <person> doc duoc: {person_count} (ky vong {EXPECTED_PERSON_COUNT})")
        log(f"Matched (co trong people): {len(matched_rows)} (ky vong {EXPECTED_MATCHED})")
        log(f"Orphan (khong co trong people): {len(orphan_rows)} (ky vong {EXPECTED_ORPHAN})")
        log(f"name_zh_mismatch=1: {mismatch_count}")

        if person_count != EXPECTED_PERSON_COUNT:
            log(f"CANH BAO: so <person> ({person_count}) khac ky vong ({EXPECTED_PERSON_COUNT}).")
        if len(matched_rows) != EXPECTED_MATCHED:
            log(f"CANH BAO: so matched ({len(matched_rows)}) khac ky vong ({EXPECTED_MATCHED}).")
        if len(orphan_rows) != EXPECTED_ORPHAN:
            log(f"CANH BAO: so orphan ({len(orphan_rows)}) khac ky vong ({EXPECTED_ORPHAN}).")

        all_rows = matched_rows + orphan_rows
        to_insert = [r for r in all_rows if r[0] not in already]
        skipped = len(all_rows) - len(to_insert)
        if skipped:
            log(f"Bo qua {skipped} dila_id da co san (idempotent).")

        if not apply_:
            log("DRY-RUN: khong ghi vao DB. Dung --apply de thuc hien insert thuc su.")
            # Van xuat CSV/manifest de admin xem truoc neu muon (preview).
            write_orphan_csv(orphan_rows)
            write_manifest(all_rows, xml_sha256, person_count, len(matched_rows), len(orphan_rows), mismatch_count, dry_run=True)
            return

        if to_insert:
            conn.executemany(
                """INSERT OR IGNORE INTO codex_person_name
                   (dila_id, name_zh_xml, name_vi, tier, review, rule, evidence,
                    alternatives, model, status, name_zh_mismatch, xml_sha256, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                to_insert,
            )
            conn.commit()
            log(f"Da INSERT {len(to_insert)} dong vao codex_person_name.")
        else:
            log("Khong co dong moi can insert (da chay roi - idempotent).")

        cur = conn.execute("SELECT COUNT(*) FROM codex_person_name")
        total_after = cur.fetchone()[0]
        log(f"Tong so dong trong codex_person_name sau khi chay: {total_after}")

        write_orphan_csv(orphan_rows)
        write_manifest(all_rows, xml_sha256, person_count, len(matched_rows), len(orphan_rows), mismatch_count, dry_run=False)

    except Exception as e:
        log(f"LOI: {e}")
        raise
    finally:
        conn.close()


def write_orphan_csv(orphan_rows):
    import csv
    path = os.path.join(SESSION_DIR, 'orphan_ids.csv')
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['dila_id', 'name_zh_xml', 'name_vi', 'tier', 'reason'])
        for row in orphan_rows:
            dila_id, name_zh_xml, name_vi, tier = row[0], row[1], row[2], row[3]
            w.writerow([dila_id, name_zh_xml, name_vi, tier, 'khong_co_trong_bang_people'])
    log(f"Da xuat CSV orphan ({len(orphan_rows)} dong): {path}")


def write_manifest(all_rows, xml_sha256, person_count, matched_count, orphan_count, mismatch_count, dry_run):
    path = os.path.join(SESSION_DIR, 'part1_manifest.json')
    manifest = {
        'task': 'T418',
        'xml_url': XML_URL,
        'xml_commit': XML_COMMIT,
        'xml_sha256': xml_sha256,
        'model_tag': MODEL_TAG,
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'dry_run': dry_run,
        'person_count_xml': person_count,
        'matched_count': matched_count,
        'orphan_count': orphan_count,
        'name_zh_mismatch_count': mismatch_count,
        'dila_ids': [r[0] for r in all_rows],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    log(f"Da ghi manifest ({len(all_rows)} dila_id): {path}")


def revert():
    conn = get_db()
    try:
        conn.execute("DROP TABLE IF EXISTS codex_person_name")
        conn.commit()
        log("Da DROP TABLE codex_person_name (revert hoan tat). Khong anh huong bang nao khac.")
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='T418 Part 1 - Import Claude XML vao codex_person_name')
    parser.add_argument('--dry-run', action='store_true', help='Chi tinh toan va in bao cao, khong ghi DB (mac dinh)')
    parser.add_argument('--apply', action='store_true', help='Thuc su ghi vao DB')
    parser.add_argument('--revert', action='store_true', help='DROP TABLE codex_person_name')
    args = parser.parse_args()

    try:
        if args.revert:
            revert()
        else:
            run(dry_run=not args.apply, apply_=args.apply)
    except Exception as e:
        log(f"DUNG LAI vi loi: {e}")
        sys.exit(1)
