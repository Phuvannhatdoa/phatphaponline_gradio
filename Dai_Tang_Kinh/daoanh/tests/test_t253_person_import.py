# -*- coding: utf-8 -*-
"""T253 — Person Import ETL tests.

Chạy ego:         python -X utf8 tests/test_t253_person_import.py
Chạy pytest:      python -X utf8 -m pytest tests/test_t253_person_import.py -v

Bộ test dùng DB temp + fixture XML temp (KHÔNG đụng lineage.db thật, KHÔNG đụng
XML Authority 51MB — Zero-RAM path được kiểm chứng bằng validate trên file nhỏ).

Coverage:
  [G1] validate: đếm tổng/sex/skip-existing/skip-internal-dup/will_insert
  [G2] commit:   INSERT mới (name_zh, gender Female, appellations JSON),
                 KHÔNG đụng hàng đã có dila_id, bỏ internal dup,
                 id=tên source (idempotent), status='pending', ttl_filename=''
  [G3] idempotency: commit lần 2 → inserted=0 (không nhân bản)
  [G4] manifest:  bảng person_import_manifest ghi đúng run_id
  [G5] revert:    DELETE đúng hàng run_id, hàng cũ còn nguyên, manifest trống
  [G6] list_runs: hiện run đã commit
"""

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)
_ETL_PY = os.path.join(_DAOANH, 'scripts', 'person_import_etl.py')

VPA_DDL = """
CREATE TABLE vn_person_authority (
    id TEXT PRIMARY KEY,
    ttl_filename TEXT NOT NULL,
    name_vi TEXT,
    name_zh TEXT,
    dharma_title TEXT,
    dharma_lineage TEXT,
    generation_order INTEGER,
    is_lineage_founder INTEGER DEFAULT 0,
    gender TEXT,
    biographical_note_vi TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    appellations TEXT,
    dila_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

FIXTURE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:xml="http://www.w3.org/XML/1998/namespace">
  <teiHeader><fileDesc><titleStmt><title>Fixture T253</title></titleStmt></fileDesc></teiHeader>
  <text><body>
    <listPerson>
      <person xml:id="A000001"><persName xml:lang="zho-Hant">釋迦牟尼</persName>
        <persName type="alternative" xml:lang="zho-Hant">佛陀</persName><sex value="1"/></person>
      <person xml:id="A000002"><persName xml:lang="zho-Hant">玄奘</persName>
        <persName type="alternative" xml:lang="zho-Hant">三藏法師</persName><sex value="1"/></person>
      <person xml:id="A000003"><persName xml:lang="zho-Hant">阿難</persName><sex value="2"/></person>
      <person xml:id="A000005"><persName xml:lang="zho-Hant">同名甲</persName><sex value="1"/></person>
      <person xml:id="A000005"><persName xml:lang="zho-Hant">同名乙</persName><sex value="1"/></person>
      <person xml:id="A000006"><persName type="alternative" xml:lang="zho-Hant">某號</persName><sex value="1"/></person>
      <person xml:id="A000007"><note type="dynasty">無名</note></person>
    </listPerson>
  </body></text>
</TEI>
"""


def _load_etl():
    spec = importlib.util.spec_from_file_location('person_import_etl', _ETL_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _setup():
    """Trả (etl, tmpdir, xml_path, db_path) với DB fixture: A000001 đã tồn tại."""
    etl = _load_etl()
    tmp = tempfile.mkdtemp(prefix='t253_')
    xml_path = os.path.join(tmp, 'fixture.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(FIXTURE_XML)
    db_path = os.path.join(tmp, 'lineage.db')
    con = sqlite3.connect(db_path)
    con.executescript(VPA_DDL)
    con.execute(
        "INSERT INTO vn_person_authority (id, ttl_filename, name_zh, dila_id, status) "
        "VALUES (?,?,?,?,?)", ('sakya_muni', 'Sakya', '釋迦牟尼', 'A000001', 'verified'))
    con.commit()
    con.close()
    return etl, tmp, xml_path, db_path


def _rows(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id,dila_id,name_zh,gender,appellations,status,ttl_filename "
        "FROM vn_person_authority ORDER BY id").fetchall()
    con.close()
    return [dict(r) for r in rows]


def test_t253_validate():
    etl, tmp, xml_path, db_path = _setup()
    r = etl.validate(xml_path, db_path)
    assert r['persons_total'] == 7, r
    assert r['skipped_existing'] == 1, r          # A000001 đã có trong DB
    assert r['skipped_dup'] == 1, r               # A000005 xuất hiện 2 lần
    assert r['will_insert'] == 4, r               # A000002, A000003, A000005, A000006
    assert r['no_name'] == 1, r                   # A000007 không tên
    assert r['no_id'] == 0
    assert r['sex'].get('1') == 5 and r['sex'].get('2') == 1, r['sex']
    assert r['db_total_existing'] == 1
    assert len(r['xml_sha256']) == 64
    assert r['skipped_existing_sample'][0]['dila_id'] == 'A000001'


def test_t253_commit_and_fields():
    etl, tmp, xml_path, db_path = _setup()
    r = etl.commit(xml_path, db_path, run_id='PI-TEST-1', sidecar_dir=tmp, backup_root=tmp)
    assert r['inserted'] == 4, r
    assert r['skipped_existing'] == 1, r
    assert r['skipped_dup'] == 1, r
    assert r['no_name'] == 1, r
    assert os.path.exists(os.path.join(tmp, r['backup_dir'], 'lineage.db')), r

    rows = {x['id']: x for x in _rows(db_path)}
    assert 'sakya_muni' in rows           # hàng cũ còn nguyên
    assert rows['sakya_muni']['status'] == 'verified'

    a2 = rows['dila_a000002']
    assert a2['dila_id'] == 'A000002'
    assert a2['name_zh'] == '玄奘'
    assert a2['gender'] == 'Male'
    assert a2['status'] == 'pending'
    assert a2['ttl_filename'] == ''
    alts = json.loads(a2['appellations'])
    assert any(a['label'] == '三藏法師' for a in alts), alts

    assert rows['dila_a000003']['gender'] == 'Female'   # sex value=2 → Female
    assert rows['dila_a000006']['name_zh'] is None       # chỉ có alternative
    assert '三藏法師' not in (rows.get('dila_a000005') or {}).get('name_zh', '')

    n_a000005 = [x for x in rows.values() if x['dila_id'] == 'A000005']
    assert len(n_a000005) == 1                            # internal dup bị bỏ

    # manifest đúng run_id
    con = sqlite3.connect(db_path)
    cnt = con.execute(
        "SELECT COUNT(*) FROM person_import_manifest WHERE run_id='PI-TEST-1'").fetchone()[0]
    con.close()
    assert cnt == 4


def test_t253_idempotent_no_duplicate():
    etl, tmp, xml_path, db_path = _setup()
    etl.commit(xml_path, db_path, run_id='PI-TEST-1', sidecar_dir=tmp, backup_root=tmp)
    r2 = etl.commit(xml_path, db_path, run_id='PI-TEST-2', sidecar_dir=tmp, backup_root=tmp)
    assert r2['inserted'] == 0, r2                 # không nhân bản
    assert r2['skipped_existing'] == 6, r2         # 4 mới + 1 cũ + A000005(2nd lần này là existing)
    assert len(_rows(db_path)) == 1 + 4


def test_t253_revert_and_list_runs():
    etl, tmp, xml_path, db_path = _setup()
    etl.commit(xml_path, db_path, run_id='PI-TEST-1', sidecar_dir=tmp, backup_root=tmp)
    runs = etl.list_runs_at(db_path)
    assert any(x['run_id'] == 'PI-TEST-1' and x['rows_imported'] == 4 for x in runs), runs

    rb = etl.revert(db_path, 'PI-TEST-1')
    assert rb['reverted'] == 4, rb
    rows = {x['id']: x for x in _rows(db_path)}
    assert 'sakya_muni' in rows                     # hàng cũ giữ nguyên
    assert not any(x.startswith('dila_') for x in rows), rows.keys()
    con = sqlite3.connect(db_path)
    cnt = con.execute(
        "SELECT COUNT(*) FROM person_import_manifest WHERE run_id='PI-TEST-1'").fetchone()[0]
    con.close()
    assert cnt == 0

    # revert lần nữa → 0 (không lỗi, không xoá nhầm)
    rb2 = etl.revert(db_path, 'PI-TEST-1')
    assert rb2['reverted'] == 0, rb2


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_t253_')]
    failed = 0
    for fn in tests:
        try:
            fn()
            print('  \u2713 %s' % fn.__name__)
        except Exception as e:
            failed += 1
            import traceback
            traceback.print_exc()
            print('  \u2717 %s: %r' % (fn.__name__, e))
    print('T253 PASS %d/%d' % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())