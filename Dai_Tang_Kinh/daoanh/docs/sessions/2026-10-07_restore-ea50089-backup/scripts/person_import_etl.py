"""
T253 — Person Import ETL (DILA Authority XML → vn_person_authority)
====================================================================
Phase 1 (T253): nhập khối 48.803 nhân vật từ
data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml
vào bảng vn_person_authority (data/lineage.db) theo 4 nguyên tắc:

1. ADDITIVE: chỉ INSERT hàng MỚI (dila_id chưa tồn tại trong DB). Không UPDATE,
   không merge, không đè bản ghi đã có — merge/gộp alias là phạm vi T223
   (báo cáo CSV các dila_id bị skip để T223 xử lý).
2. KHÔNG BỊA: chỉ map cột 1:1 từ XML (dila_id, name_zh, appellations, gender).
   name_vi / birth_year / death_year / dharma_title / dharma_lineage / dynasty
   KHÔNG được phỏng đoán (bài học T252: tự suy dynasty sai). ttl_filename = ''
   vì chưa có file TTL tương ứng; status = 'pending' (chưa kiểm chứng).
3. ZERO-RAM: đọc XML bằng ET.iterparse(events=('end',)) + el.clear() liên tục —
   chỉ giữ set dila_id (~48k string) chứ không bao giờ dựng cây XML.
4. REVERT ĐƯỢC: mỗi lần commit chạy trong 1 transaction ghi NHẤT QUÁN
   vn_person_authority + person_import_manifest, đồng thời chép backup DB file
   vào data/backups/person-import-<run_id>/. Revert = DELETE theo manifest
   (chỉ xoá đúng hàng mình thêm, addditve nên mất 0 dữ liệu cũ). Dựng lại
   backup DB đầy đủ = --restore-db <run_id> (ký rõ: sẽ EDLỌN mọi thay đổi DB sau run_id).

Cách dùng (CLI, chạy từ thư mục daoanh):
  python -X utf8 scripts/person_import_etl.py --action validate
  python -X utf8 scripts/person_import_etl.py --action commit
  python -X utf8 scripts/person_import_etl.py --action runs
  python -X utf8 scripts/person_import_etl.py --action revert --run-id <id>
  python -X utf8 scripts/person_import_etl.py --action revert --run-id <id> --restore-db

Tích hợp API: app.py route /daoanh/api/admin/person/import-xml gọi nhẹ các hàm
run_validate() / run_commit() / run_revert() / list_runs(). Module import-safe
(import thuần không có side effect — chỉ khởi tạo hằng số).
"""

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

# ----------------------------------------------------------------------------
# Namespace & thiết lập đường dẫn mặc định
# ----------------------------------------------------------------------------
TEI = '{http://www.tei-c.org/ns/1.0}'
XMLNS = '{http://www.w3.org/XML/1998/namespace}'
PERSON = TEI + 'person'
PERSNAME = TEI + 'persName'
SEX = TEI + 'sex'
NOTE = TEI + 'note'
BIBL = TEI + 'bibl'

_HERE = os.path.dirname(os.path.abspath(__file__))      # daoanh/scripts
DAONH = os.path.dirname(_HERE)                           # daoanh
DATA_ROOT = os.path.join(DAONH, 'data')                  # daoanh/data (lineage.db ở đây)
DEFAULT_XML = os.path.join(
    DATA_ROOT, 'dila_import', 'Authority-Databases', 'authority_person',
    'Buddhist_Studies_Person_Authority.xml')
DEFAULT_DB = os.path.join(DATA_ROOT, 'lineage.db')
DEFAULT_BACKUP_ROOT = os.path.join(DATA_ROOT, 'backups')

# Bản đồ giới tính DILA → format vn_person_authority (đo thực tế trên XML:
# value '1'=46348, '2'=1600, '0'=575, '9'=280). Không rõ → NULL, không tự đoán.
SEX_MAP = {'1': 'Male', '2': 'Female', '0': None, '9': None}

STATUS_IMPORT = 'pending'          # chưa kiểm chứng, để UI/admin duyệt sau
TTL_FILENAME_EMPTY = ''            # chưa có TTL — KHÔNG bịa tên file
MANIFEST_DDL = """
CREATE TABLE IF NOT EXISTS person_import_manifest (
    run_id      TEXT NOT NULL,
    dila_id     TEXT NOT NULL,
    vnpa_id     TEXT NOT NULL,
    name_zh     TEXT,
    xml_hash    TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    PRIMARY KEY (run_id, dila_id)
)
"""
MANIFEST_TABLE = 'person_import_manifest'


# ----------------------------------------------------------------------------
# Util
# ----------------------------------------------------------------------------
def compute_xml_sha256(xml_path, chunk=1 << 20):
    """SHA-256 streaming của file XML (không nạp toàn bộ vào RAM)."""
    h = hashlib.sha256()
    with open(xml_path, 'rb') as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def vnpa_id(dila_id):
    """Sinh id (slug) mặc định cho hàng nhân vật mới: dila_<idlower>.

    Khớp URI mặc định 'dila_aNNNNNN' dùng trong TTL. Không dùng tên Hán để
    tránh trùng slug — id là bất biến của nguồn dila_id.
    """
    return 'dila_' + (dila_id or '').lower()


def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ----------------------------------------------------------------------------
# Parse XML (Zero-RAM)
# ----------------------------------------------------------------------------
def iter_persons(xml_path):
    """Generator duyệt từng <person> — luôn el.clear() để giữ bộ nhớ phẳng."""
    for _ev, el in ET.iterparse(xml_path, events=('end',)):
        if el.tag != PERSON:
            continue
        try:
            dila_id = (el.get(XMLNS + 'id') or '').strip()
            primary = None
            alts = []
            for pn in el.iter(PERSNAME):
                label = (pn.text or '').strip()
                if not label:
                    continue
                if (pn.get('type') or '') == 'alternative':
                    alts.append({
                        'label': label,
                        'lang': pn.get(XMLNS + 'lang') or '',
                        'type': 'AlternativeName',
                    })
                elif primary is None:
                    primary = label
            sex_raw = None
            for s in el.iter(SEX):
                sex_raw = s.get('value')
                break
            # Trích xuất RAW (không vào DB — chỉ phục vụ manifest/kiểm chứng)
            dynasty = ''
            concise = ''
            origin = []
            works = []
            bibl = []
            for n in el.iter(NOTE):
                t = n.get('type') or ''
                txt = (n.text or '').strip()
                if t == 'dynasty':
                    dynasty = txt
                elif t == 'concise':
                    concise = txt
                elif t == 'placeOfOrigin' and txt:
                    origin.append(txt)
                elif t in ('worksInTripitaka', 'worksBy') and txt:
                    works.append(txt)
            for b in el.iter(BIBL):
                txt = (b.text or '').strip()
                if txt:
                    bibl.append(txt)
            yield {
                'dila_id': dila_id,
                'name_zh': primary,
                'alts': alts,
                'gender': SEX_MAP.get(sex_raw),
                'sex_raw': sex_raw,
                'dynasty': dynasty,
                'concise': concise,
                'origin': origin,
                'works': works,
                'bibl': bibl,
            }
        finally:
            el.clear()


def _appellations_json(alts):
    """Format appellations theo chuẩn có sẵn trong DB (JSON array string)."""
    if not alts:
        return None
    clean = [a for a in alts if a.get('label')]
    return json.dumps(clean, ensure_ascii=False) if clean else None


# ----------------------------------------------------------------------------
# DB helpers
# ----------------------------------------------------------------------------
def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _existing_dila_map(conn):
    """{dila_id → row} của mọi hàng đã có dila_id (không trùng để tránh đè)."""
    rows = conn.execute(
        "SELECT id, dila_id, status, name_zh FROM vn_person_authority "
        "WHERE dila_id IS NOT NULL AND dila_id != ''").fetchall()
    return {r['dila_id']: r for r in rows}


def _backup_dir(backup_root, run_id):
    d = os.path.join(backup_root, 'person-import-' + run_id)
    os.makedirs(d, exist_ok=True)
    return d


# ----------------------------------------------------------------------------
# VALIDATE — đọc-only, hai lượt nhẹ (báo cáo, không ghi DB)
# ----------------------------------------------------------------------------
def validate(xml_path, db_path):
    """Quét XML + DB, trả số liệu để UI hiển thị trước khi commit.

    Trả dict: xml_sha256, xml_size, persons_total, no_id, no_name,
               sex (Counter), skipped_existing(+samples), skipped_dup(+samples),
               will_insert, db_total_existing.
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError('XML nguồn không tồn tại: %s' % xml_path)
    sha = compute_xml_sha256(xml_path)
    xml_size = os.path.getsize(xml_path)

    conn = _connect(db_path)
    try:
        existing = _existing_dila_map(conn)
        db_total_existing = len(existing)
    finally:
        conn.close()

    total = no_id = no_name = will_insert = 0
    skipped_existing = skipped_dup = 0
    sex_count = {}
    seen = set()
    skip_existing_sample = []
    skip_dup_sample = []
    for p in iter_persons(xml_path):
        total += 1
        sex_count[p['sex_raw']] = sex_count.get(p['sex_raw'], 0) + 1
        if not p['dila_id']:
            no_id += 1
            continue
        if p['dila_id'] in existing:
            skipped_existing += 1
            if len(skip_existing_sample) < 10:
                row = existing[p['dila_id']]
                skip_existing_sample.append({
                    'dila_id': p['dila_id'],
                    'id': row['id'],
                    'status': row['status'],
                    'name_zh': row['name_zh'],
                })
            continue
        if p['dila_id'] in seen:
            skipped_dup += 1
            if len(skip_dup_sample) < 5:
                skip_dup_sample.append({'dila_id': p['dila_id']})
            continue
        seen.add(p['dila_id'])
        if not p['name_zh'] and not p['alts']:
            no_name += 1
            continue
        will_insert += 1

    return {
        'xml': os.path.basename(xml_path),
        'xml_size': xml_size,
        'xml_sha256': sha,
        'persons_total': total,
        'no_id': no_id,
        'no_name': no_name,
        'sex': sex_count,
        'db_total_existing': db_total_existing,
        'skipped_existing': skipped_existing,
        'skipped_existing_sample': skip_existing_sample,
        'skipped_dup': skipped_dup,
        'skipped_dup_sample': skip_dup_sample,
        'will_insert': will_insert,
    }


# ----------------------------------------------------------------------------
# COMMIT — 1 transaction: insert vn_person_authority + manifest, rồi chép backup
# ----------------------------------------------------------------------------
def commit(xml_path, db_path, run_id=None, limit=None,
           backup_root=DEFAULT_BACKUP_ROOT):
    """Nhập người mới vào vn_person_authority (additive, idempotent).

    - Skip mọi dila_id đã có trong DB (hoặc trùng trong chính XML).
    - Ghi backup DB file trước khi ghi (restore an toàn).
    - Ghi artifact manifest.json + summary.json vào data/backups/person-import-<run_id>/
    Trả dict {run_id, inserted, skipped_existing, skipped_dup, no_id, no_name,
              xml_sha256, backup, backup_db}
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError('XML nguồn không tồn tại: %s' % xml_path)
    sha = compute_xml_sha256(xml_path)
    if not run_id:
        run_id = 'PI-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')

    bdir = _backup_dir(backup_root, run_id)
    backup_db = os.path.join(bdir, 'lineage.db')
    shutil.copy2(db_path, backup_db)

    conn = _connect(db_path)
    try:
        conn.execute(MANIFEST_DDL)
        existing = _existing_dila_map(conn)
        inserted = skipped_existing = skipped_dup = no_id = no_name = 0
        seen = set()
        manifest_rows = []          # chỉ giữ tối thiểu cho manifest.json artifact
        inserted_ids = []
        with conn:
            for p in iter_persons(xml_path):
                if limit is not None and (inserted + skipped_existing + skipped_dup) >= limit:
                    break
                dila_id = p['dila_id']
                if not dila_id:
                    no_id += 1
                    continue
                if dila_id in existing:
                    skipped_existing += 1
                    continue
                if dila_id in seen:
                    skipped_dup += 1
                    continue
                seen.add(dila_id)
                if not p['name_zh'] and not p['alts']:
                    no_name += 1
                    continue
                vid = vnpa_id(dila_id)
                now = _now_iso()
                before = conn.total_changes
                conn.execute(
                    "INSERT OR IGNORE INTO vn_person_authority "
                    "(id, ttl_filename, name_vi, name_zh, dharma_title, dharma_lineage, "
                    " generation_order, is_lineage_founder, gender, biographical_note_vi, "
                    " birth_year, death_year, appellations, dila_id, status, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (vid, TTL_FILENAME_EMPTY, None, p['name_zh'], None, None, None, 0,
                     p['gender'], None, None, None,
                     _appellations_json(p['alts']), dila_id, STATUS_IMPORT, now))
                if conn.total_changes == before:   # id đã tồn tại khác dila_id → không ghi
                    skipped_dup += 1
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO " + MANIFEST_TABLE +
                    " (run_id, dila_id, vnpa_id, name_zh, xml_hash, imported_at) "
                    "VALUES (?,?,?,?,?,?)",
                    (run_id, dila_id, vid, p['name_zh'], sha, now))
                inserted += 1
                inserted_ids.append({'dila_id': dila_id, 'vnpa_id': vid,
                                     'name_zh': p['name_zh'], 'gender': p['gender']})
        # artifact (ngoài transaction — chỉ là tư liệu kiểm chứng, không sao nếu hỏng)
        try:
            with open(os.path.join(bdir, 'manifest.json'), 'w', encoding='utf-8') as f:
                json.dump({'run_id': run_id, 'rows': inserted_ids}, f,
                          ensure_ascii=False, indent=1)
            with open(os.path.join(bdir, 'summary.json'), 'w', encoding='utf-8') as f:
                json.dump({
                    'run_id': run_id, 'xml': os.path.basename(xml_path),
                    'xml_sha256': sha, 'xml_size': os.path.getsize(xml_path),
                    'inserted': inserted, 'skipped_existing': skipped_existing,
                    'skipped_dup': skipped_dup, 'no_id': no_id, 'no_name': no_name,
                    'backup_db': os.path.basename(backup_db),
                }, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
    finally:
        conn.close()

    return {
        'ok': True, 'run_id': run_id, 'inserted': inserted,
        'skipped_existing': skipped_existing, 'skipped_dup': skipped_dup,
        'no_id': no_id, 'no_name': no_name, 'xml_sha256': sha,
        'backup_dir': os.path.relpath(bdir, DAONH),
        'backup_db': os.path.basename(backup_db),
        'message': 'Import thành công: %d người mới (bỏ qua %d dila_id đã có, '
                   '%d trùng trong XML).' % (inserted, skipped_existing, skipped_dup),
    }


# ----------------------------------------------------------------------------
# REVERT — xoá đúng hàng do run_id thêm (additive: mất 0 dữ liệu cũ)
# ----------------------------------------------------------------------------
def revert(db_path, run_id, restore_db=False, backup_root=DEFAULT_BACKUP_ROOT):
    """Xoá hàng vn_person_authority theo manifest của run_id.

    restore_db=True: chép đè DB từ bản backup (cảnh báo: EDLỌN mọi thay đổi
    DB diễn ra sau run_id — chỉ dùng khi muốn về trạng thái trước import nguyên vẹn).
    Trả dict {ok, run_id, reverted, manifest_cleared, backup_restored}
    """
    if not run_id:
        raise ValueError('Thiếu run_id để revert.')
    conn = _connect(db_path)
    try:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (MANIFEST_TABLE,)).fetchone()
        if not table_exists:
            raise ValueError('Bảng %s chưa tồn tại — chưa import gì cả.' % MANIFEST_TABLE)
        rows = conn.execute(
            "SELECT vnpa_id, dila_id FROM " + MANIFEST_TABLE +
            " WHERE run_id=?", (run_id,)).fetchall()
        reverted = 0
        with conn:
            for r in rows:
                cur = conn.execute(
                    "DELETE FROM vn_person_authority WHERE id=? AND dila_id=?",
                    (r['vnpa_id'], r['dila_id']))
                reverted += cur.rowcount
            if rows:
                conn.execute("DELETE FROM " + MANIFEST_TABLE + " WHERE run_id=?", (run_id,))
    finally:
        conn.close()

    backup_restored = False
    if restore_db:
        bdir = _backup_dir(backup_root, run_id)
        src = os.path.join(bdir, 'lineage.db')
        if os.path.exists(src):
            shutil.copy2(src, db_path)
            backup_restored = True

    return {
        'ok': True, 'run_id': run_id, 'reverted': reverted,
        'manifest_cleared': bool(rows),
        'backup_restored': backup_restored,
        'message': 'Revert run %s: xoá %d hàng nhân vật (từ manifest).'
                   % (run_id, reverted),
    }


# ----------------------------------------------------------------------------
# QUERY — lịch sử import
# ----------------------------------------------------------------------------
def list_runs_at(db_path):
    try:
        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT run_id, MIN(imported_at) AS imported_at, COUNT(*) AS rows_imported "
                "FROM " + MANIFEST_TABLE + " GROUP BY run_id ORDER BY imported_at DESC"
            ).fetchall()
        finally:
            conn.close()
        return [{'run_id': r['run_id'], 'imported_at': r['imported_at'],
                 'rows_imported': r['rows_imported']} for r in rows]
    except sqlite3.Error:
        return []


# ----------------------------------------------------------------------------
# Wrapper dùng mặc định cho route API (app.py import qua importlib)
# ----------------------------------------------------------------------------
def run_validate():
    return validate(DEFAULT_XML, DEFAULT_DB)


def run_commit(limit=None):
    return commit(DEFAULT_XML, DEFAULT_DB, limit=limit)


def run_revert(run_id, restore_db=False):
    return revert(DEFAULT_DB, run_id, restore_db=restore_db)


def list_runs():
    return list_runs_at(DEFAULT_DB)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='person_import_etl', description='T253 ETL: DILA XML → vn_person_authority')
    ap.add_argument('--action', choices=['validate', 'commit', 'runs', 'revert'],
                    required=True)
    ap.add_argument('--xml', default=DEFAULT_XML)
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--run-id', default=None)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--restore-db', action='store_true')
    args = ap.parse_args(argv)

    try:
        if args.action == 'validate':
            print(json.dumps(validate(args.xml, args.db), ensure_ascii=False, indent=1))
        elif args.action == 'commit':
            res = commit(args.xml, args.db, run_id=args.run_id, limit=args.limit)
            print(json.dumps(res, ensure_ascii=False, indent=1))
        elif args.action == 'runs':
            print(json.dumps(list_runs_at(args.db), ensure_ascii=False, indent=1))
        elif args.action == 'revert':
            print(json.dumps(revert(args.db, args.run_id, restore_db=args.restore_db),
                             ensure_ascii=False, indent=1))
    except Exception as e:
        print('T253 person_import_etl ERROR: %s' % e, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())