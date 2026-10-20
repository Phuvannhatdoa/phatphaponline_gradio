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
import re
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
PLACENAME = TEI + 'placeName'      # T366: <note type="placeOfOrigin"><placeName>...
BIRTH = TEI + 'birth'              # T366: <birth>+YYYY-MM-DD ~ +YYYY-MM-DD<note>...
DEATH = TEI + 'death'               # T366: <death>...
IDNO = TEI + 'idno'                 # T366: <idno type="Wikidata">QNNNN</idno>

_HERE = os.path.dirname(os.path.abspath(__file__))      # daoanh/scripts
DAONH = os.path.dirname(_HERE)                           # daoanh
DATA_ROOT = os.path.join(DAONH, 'data')                  # daoanh/data (lineage.db ở đây)
DEFAULT_XML = os.path.join(
    DATA_ROOT, 'dila_import', 'Authority-Databases', 'authority_person',
    'Buddhist_Studies_Person_Authority.xml')
DEFAULT_DB = os.path.join(DATA_ROOT, 'lineage.db')
DEFAULT_BACKUP_ROOT = os.path.join(DATA_ROOT, 'backups')
# T366: sidecar JSON (STAGING layer) — lưu các phần tử XML đã trích xuất
# nhưng KHÔNG đưa vào DB (dynasty/works/CBETA/places/wikidata/dates), để
# không mất dữ liệu nếu script chạy lại và để T365 tái nhập sau không cần
# parse lại XML. Ephemeral — gitignore, không phải nguồn FINAL.
DEFAULT_SIDECAR_DIR = os.path.join(DATA_ROOT, 'dila_import', 'extracted')

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


def _safe_relpath(path, start):
    """Tính relative path, fallback sang absolute path nếu khác ổ đĩa (Windows).

    Trên Windows, os.path.relpath() raise ValueError nếu path & start trên
    khác ổ đĩa (ví dụ E: vs C:). Fallback sang absolute path để tránh crash.
    """
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return os.path.abspath(path)


def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ----------------------------------------------------------------------------
# T366 — Sidecar JSON (STAGING layer): lưu phần tử XML đã trích xuất nhưng
# không vào DB, để có audit trail + nguồn cho T365 tái nhập.
# ----------------------------------------------------------------------------
def save_sidecar_json(dila_id, dynasty, concise, places, works, bibl,
                       wikidata, dates, sidecar_dir, active_at_places=None,
                       xml_sha256=None):
    """Ghi 1 file JSON sidecar cho dila_id (overwrite — idempotent).

    Không đọc/không ghi DB. An toàn chạy nhiều lần (ghi đè bằng đúng dữ liệu
    trích xuất lại từ XML, không tích lũy rác).

    T366 fix (code review): thêm active_at_places (note type="activeAt",
    tách riêng khỏi works) và xml_sha256 (để biết sidecar sinh ra từ phiên
    bản XML nào — audit trail khi XML nguồn thay đổi).
    """
    sidecar = {
        'dila_id': dila_id,
        'dynasty': dynasty,
        'concise_bio': concise,
        'places_of_origin': places,
        'works_in_tripitaka': works,
        'active_at_places': active_at_places or [],
        'cbeta_citations': bibl,
        'wikidata_qid': wikidata,
        'birth_death_dates': dates,
        'xml_sha256': xml_sha256,
        'extracted_at': _now_iso(),
        'source': 'Buddhist_Studies_Person_Authority.xml',
    }
    sidecar_path = os.path.join(sidecar_dir, '%s.json' % dila_id)
    with open(sidecar_path, 'w', encoding='utf-8') as f:
        json.dump(sidecar, f, ensure_ascii=False, indent=2)
    return sidecar_path


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
            # Trích xuất RAW (không vào DB — chỉ phục vụ manifest/kiểm chứng
            # + sidecar JSON T366, xem save_sidecar_json())
            dynasty = []
            concise = ''
            origin = []
            works = []
            active_at = []
            bibl = []
            for n in el.iter(NOTE):
                t = n.get('type') or ''
                txt = (n.text or '').strip()
                if t == 'dynasty':
                    # T366 fix (code review #4): nhiều triều đại cách nhau
                    # bằng \n (ví dụ "北宋\n    南宋") — tách thành list,
                    # không giữ 1 string nối \n.
                    dynasty = [d.strip() for d in txt.split('\n') if d.strip()]
                elif t == 'concise':
                    # T366 fix (code review #2): n.text chỉ lấy text TRỰC
                    # TIẾP của <note>, bị cắt mất phần nằm trong <ref> con
                    # và tail sau <ref> (ví dụ URL nguồn + ngày trích dẫn).
                    # itertext() duyệt toàn bộ text con + tail để lấy đủ câu.
                    concise = ''.join(n.itertext()).strip()
                elif t == 'placeOfOrigin':
                    # T366 fix: text thật nằm trong <placeName> con, không phải
                    # text trực tiếp của <note> (vốn chỉ là khoảng trắng) —
                    # lấy .text của <placeName> (bỏ qua <ref> id con để không
                    # lẫn DILA place-id vào tên địa danh).
                    for pname in n.iter(PLACENAME):
                        place_txt = (pname.text or '').strip()
                        if place_txt:
                            origin.append(place_txt)
                elif t in ('worksInTripitaka', 'worksBy'):
                    # T366 fix (code review #3,#4): mỗi note có thể chứa NHIỀU
                    # tác phẩm cách nhau bằng \n (ví dụ 4-6 dòng) — tách
                    # thành từng phần tử riêng. Dùng itertext() để không mất
                    # nội dung trong <ref> con (29 notes toàn bộ nội dung nằm
                    # trong <ref>).
                    full_txt = ''.join(n.itertext()).strip()
                    if full_txt:
                        works.extend(line.strip() for line in full_txt.split('\n')
                                     if line.strip())
                elif t == 'activeAt':
                    # T366 fix (code review #3,#5): note activeAt (nơi hoạt
                    # động) chưa được trích xuất — tách theo dấu '；、，,;'
                    # (có thể là ideographic semicolon, CJK, Western comma, hoặc
                    # dấu phẩy) và '\n' (phòng trường hợp nhiều dòng). Dùng
                    # itertext() để không mất nội dung trong <ref> con.
                    full_txt = ''.join(n.itertext()).strip()
                    if full_txt:
                        for chunk in re.split(u'[；、，,;\\n]', full_txt):
                            place = chunk.strip()
                            if place:
                                active_at.append(place)
            # T366 fix (code review #1): chỉ lấy <bibl> trong <listBibl>
            # (CBETA citation thật) — KHÔNG lấy <bibl> trong
            # listRelation/.../desc/bibl (đó là nguồn trích dẫn cho quan hệ
            # thầy-trò, không phải CBETA citation của chính nhân vật này).
            # itertext() để không mất text nằm trong <ref> con (2 entry
            # listBibl/bibl/ref bị bỏ sót khi chỉ đọc b.text).
            list_bibl = el.find(TEI + 'listBibl')
            if list_bibl is not None:
                for b in list_bibl.findall(TEI + 'bibl'):
                    txt = ''.join(b.itertext()).strip()
                    if txt:
                        bibl.append(txt)
            # T366: Wikidata QID (lấy giá trị đầu tiên nếu có nhiều <idno>)
            wikidata = None
            for idno in el.iter(IDNO):
                if (idno.get('type') or '') == 'Wikidata':
                    qid = (idno.text or '').strip()
                    if qid:
                        wikidata = qid
                        break
            # T366: birth/death — chỉ lấy text trực tiếp của <birth>/<death>
            # (span ngày DILA), KHÔNG lấy text của <note> con bên trong.
            dates = {}
            for b in el.iter(BIRTH):
                btxt = (b.text or '').strip()
                if btxt:
                    dates['birth'] = btxt
                break
            for d in el.iter(DEATH):
                dtxt = (d.text or '').strip()
                if dtxt:
                    dates['death'] = dtxt
                break
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
                'active_at': active_at,
                'bibl': bibl,
                'wikidata': wikidata,
                'dates': dates,
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


def _clean_sidecar_dir(sidecar_dir):
    """T366 fix #7: xoá sạch *.json trong thư mục sidecar STAGING.

    Chỉ xoá file .json do chính script này sinh ra (không đụng thư mục nếu
    không tồn tại, không đụng file khác loại). Dùng trước khi chạy đợt mới
    để tránh 100 file "mixed" từ các lượt chạy code cũ/mới lẫn trong cùng
    thư mục (vấn đề daoanh-qa phát hiện).
    """
    if not os.path.isdir(sidecar_dir):
        return 0
    removed = 0
    for fname in os.listdir(sidecar_dir):
        if fname.endswith('.json'):
            try:
                os.remove(os.path.join(sidecar_dir, fname))
                removed += 1
            except OSError:
                pass
    print('T366 --clean-extracted: da xoa %d sidecar JSON cu trong %s' %
          (removed, sidecar_dir), file=sys.stderr)
    return removed


# ----------------------------------------------------------------------------
# VALIDATE — đọc-only, hai lượt nhẹ (báo cáo, không ghi DB)
# ----------------------------------------------------------------------------
def validate(xml_path, db_path, limit=None, preserve_sidecars=False,
             sidecar_dir=DEFAULT_SIDECAR_DIR):
    """Quét XML + DB, trả số liệu để UI hiển thị trước khi commit.

    Trả dict: xml_sha256, xml_size, persons_total, no_id, no_name,
               sex (Counter), skipped_existing(+samples), skipped_dup(+samples),
               will_insert, db_total_existing, sidecars_written (T366).

    T366 fix (code review #5): preserve_sidecars mặc định là False — validate
    là bước đọc-only/dry-run, KHÔNG được tự ý ghi 49k file sidecar ra đĩa.
    Phải truyền preserve_sidecars=True rõ ràng mới ghi (dùng khi muốn kiểm
    tra trích xuất song song với validate, không phải hành vi mặc định).
    limit (nếu có) chỉ giới hạn số người xử lý — để test nhanh (--limit 10)
    không phải quét hết 48k.
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

    if preserve_sidecars:
        os.makedirs(sidecar_dir, exist_ok=True)

    total = no_id = no_name = will_insert = sidecars_written = 0
    skipped_existing = skipped_dup = 0
    sex_count = {}
    seen = set()
    skip_existing_sample = []
    skip_dup_sample = []
    for p in iter_persons(xml_path):
        if limit is not None and total >= limit:
            break
        total += 1
        sex_count[p['sex_raw']] = sex_count.get(p['sex_raw'], 0) + 1
        if preserve_sidecars and p['dila_id']:
            save_sidecar_json(
                p['dila_id'], p['dynasty'], p['concise'], p['origin'],
                p['works'], p['bibl'], p['wikidata'], p['dates'], sidecar_dir,
                active_at_places=p['active_at'], xml_sha256=sha)
            sidecars_written += 1
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
        'sidecars_written': sidecars_written,
        'sidecar_dir': _safe_relpath(sidecar_dir, DAONH) if preserve_sidecars else None,
    }


# ----------------------------------------------------------------------------
# COMMIT — 1 transaction: insert vn_person_authority + manifest, rồi chép backup
# ----------------------------------------------------------------------------
def commit(xml_path, db_path, run_id=None, limit=None,
           backup_root=DEFAULT_BACKUP_ROOT, preserve_sidecars=True,
           sidecar_dir=DEFAULT_SIDECAR_DIR):
    """Nhập người mới vào vn_person_authority (additive, idempotent).

    - Skip mọi dila_id đã có trong DB (hoặc trùng trong chính XML).
    - Ghi backup DB file trước khi ghi (restore an toàn).
    - Ghi artifact manifest.json + summary.json vào data/backups/person-import-<run_id>/
    - T366: nếu preserve_sidecars=True (mặc định), ghi JSON sidecar (STAGING
      layer) cho MỌI người xử lý trong lượt chạy này (kể cả người bị skip vì
      đã có trong DB) — sidecar không phụ thuộc việc insert có xảy ra hay
      không, vì mục đích là giữ audit trail các phần tử trích xuất từ XML.
    Trả dict {run_id, inserted, skipped_existing, skipped_dup, no_id, no_name,
              xml_sha256, backup, backup_db, sidecars_written}
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError('XML nguồn không tồn tại: %s' % xml_path)
    sha = compute_xml_sha256(xml_path)
    if not run_id:
        run_id = 'PI-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')

    bdir = _backup_dir(backup_root, run_id)
    backup_db = os.path.join(bdir, 'lineage.db')
    shutil.copy2(db_path, backup_db)

    if preserve_sidecars:
        os.makedirs(sidecar_dir, exist_ok=True)
    sidecars_written = 0

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
                if preserve_sidecars and dila_id:
                    save_sidecar_json(
                        dila_id, p['dynasty'], p['concise'], p['origin'],
                        p['works'], p['bibl'], p['wikidata'], p['dates'],
                        sidecar_dir, active_at_places=p['active_at'],
                        xml_sha256=sha)
                    sidecars_written += 1
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
                    'sidecars_written': sidecars_written,
                }, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
    finally:
        conn.close()

    return {
        'ok': True, 'run_id': run_id, 'inserted': inserted,
        'skipped_existing': skipped_existing, 'skipped_dup': skipped_dup,
        'no_id': no_id, 'no_name': no_name, 'xml_sha256': sha,
        'backup_dir': _safe_relpath(bdir, DAONH),
        'backup_db': os.path.basename(backup_db),
        'sidecars_written': sidecars_written,
        'sidecar_dir': _safe_relpath(sidecar_dir, DAONH) if preserve_sidecars else None,
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
def run_validate(limit=None, preserve_sidecars=False):
    return validate(DEFAULT_XML, DEFAULT_DB, limit=limit,
                     preserve_sidecars=preserve_sidecars)


def run_commit(limit=None, preserve_sidecars=True):
    return commit(DEFAULT_XML, DEFAULT_DB, limit=limit,
                   preserve_sidecars=preserve_sidecars)


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
    # T366 fix (code review #5): mặc định preserve_sidecars=False cho CẢ CLI
    # — validate là bước đọc-only/dry-run, không được tự ý ghi 49k file ra
    # đĩa. commit (ghi DB thật) vẫn muốn sidecar mặc định để giữ audit trail
    # đầy đủ, nên action=commit sẽ tự bật True nếu user không chỉ định gì
    # (xem default=None + xử lý theo action ngay dưới).
    ap.add_argument('--preserve-sidecars', dest='preserve_sidecars',
                     action='store_true', default=None,
                     help='Ghi JSON sidecar STAGING cho mỗi người '
                          '(mặc định: validate=KHÔNG, commit=CÓ).')
    ap.add_argument('--no-preserve-sidecars', dest='preserve_sidecars',
                     action='store_false',
                     help='Tắt ghi sidecar.')
    ap.add_argument('--clean-extracted', action='store_true',
                     help='T366 fix #7: xoá sạch data/dila_import/extracted/ '
                          '(sidecar STAGING cũ) trước khi chạy, để tránh file '
                          'từ các lượt chạy trộn code cũ/mới lẫn trong cùng '
                          'thư mục. Chỉ xoá *.json sidecar, không đụng DB.')
    ap.add_argument('--sidecar-dir', default=DEFAULT_SIDECAR_DIR)
    args = ap.parse_args(argv)

    if args.clean_extracted:
        _clean_sidecar_dir(args.sidecar_dir)

    try:
        if args.action == 'validate':
            preserve = args.preserve_sidecars
            if preserve is None:
                preserve = False   # validate: mặc định đọc-only
            res = validate(args.xml, args.db, limit=args.limit,
                            preserve_sidecars=preserve,
                            sidecar_dir=args.sidecar_dir)
            print(json.dumps(res, ensure_ascii=False, indent=1))
        elif args.action == 'commit':
            preserve = args.preserve_sidecars
            if preserve is None:
                preserve = True    # commit: mặc định có sidecar (audit trail)
            res = commit(args.xml, args.db, run_id=args.run_id, limit=args.limit,
                          preserve_sidecars=preserve,
                          sidecar_dir=args.sidecar_dir)
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