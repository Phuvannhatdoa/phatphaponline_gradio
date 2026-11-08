# -*- coding: utf-8 -*-
"""T380 — kiểm thử số đời nhập tay: migration (additive), API (upsert/history/delete), ETL không xóa."""
import os
import sqlite3
import sys

import pytest
from flask import Flask

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import api_manual_generation as agm  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    't380_mig', os.path.join(ROOT, 'scripts', 't380_manual_generation_tables.py'))
t380 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(t380)

FOUNDER = 'A001984'   # Quy Sơn Linh Hựu (locked trong anchors_khai_to_dong.json)


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / 'lineage.db'
    c = sqlite3.connect(p)
    c.executescript("""
        CREATE TABLE vn_person_authority (id TEXT PRIMARY KEY, name_vi TEXT, name_zh TEXT, dila_id TEXT);
        CREATE TABLE person_gen_computed (person_id TEXT, lineage_key TEXT, lineage_name TEXT,
            gen_sect INTEGER, gen_lamte INTEGER, gen_thientong INTEGER, PRIMARY KEY(person_id, lineage_key));
        INSERT INTO vn_person_authority VALUES ('p_computed','Đã Tính','已',  'A100');
        INSERT INTO vn_person_authority VALUES ('p_free','Chưa Tính','未', 'A200');
        INSERT INTO person_gen_computed VALUES ('p_computed','k','Tông',1,2,33);
    """)
    c.commit(); c.close()
    return str(p)


@pytest.fixture
def client(db_path):
    app = Flask(__name__)
    app.config['TESTING'] = True
    base = ROOT

    def get_conn():
        import sqlite3 as s
        conn = s.connect(db_path, timeout=10)
        conn.row_factory = s.Row
        return conn

    app.register_blueprint(agm.create_manual_generation_blueprint(base, get_conn))
    return app.test_client()


def test_migration_apply_is_additive_and_idempotent(tmp_path, db_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    import shutil
    shutil.copy(db_path, tmp_path / 'data' / 'lineage.db')
    target = str(tmp_path / 'data' / 'lineage.db')
    assert t380.apply(target) == 0
    assert t380.apply(target) == 0  # chạy lại không lỗi
    c = sqlite3.connect(target)
    names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'person_generation_manual', 'person_generation_manual_history'} <= names
    assert c.execute("SELECT COUNT(*) FROM vn_person_authority").fetchone()[0] == 2
    c.close()


def test_migration_revert_refuses_when_rows_exist(tmp_path, db_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    import shutil
    target = str(tmp_path / 'data' / 'lineage.db')
    shutil.copy(db_path, target)
    t380.apply(target)
    c = sqlite3.connect(target)
    c.execute("INSERT INTO person_generation_manual VALUES ('p_free',?,30,NULL,'admin','2026-11-08')", (FOUNDER,))
    c.commit(); c.close()
    assert t380.revert(target) == 1


def test_founders_only_locked_with_dila_id():
    founders = agm._load_founders(ROOT)
    assert founders, 'phải có khai tổ đã khóa'
    assert all(f['dila_id'] for f in founders)
    assert FOUNDER in {f['dila_id'] for f in founders}


def test_unresolved_excludes_computed_person(client):
    j = client.get('/daoanh/api/admin/manual-gen/unresolved').get_json()
    ids = [i['person_id'] for i in j['items']]
    assert 'p_free' in ids and 'p_computed' not in ids
    assert j['total'] == 1


def test_upsert_writes_history_and_updates(client, db_path):
    r = client.post('/daoanh/api/admin/manual-gen/entry', json={
        'person_id': 'p_free', 'lineage_founder_dila_id': FOUNDER, 'generation': 40,
        'note': 'nguồn A', 'editor': 'admin'}).get_json()
    assert r['ok'] and r['old_generation'] is None
    r2 = client.post('/daoanh/api/admin/manual-gen/entry', json={
        'person_id': 'p_free', 'lineage_founder_dila_id': FOUNDER, 'generation': 41}).get_json()
    assert r2['ok'] and r2['old_generation'] == 40
    h = client.get('/daoanh/api/admin/manual-gen/history?person_id=p_free').get_json()['items']
    assert [x['action'] for x in h] == ['update', 'insert']
    j = client.get('/daoanh/api/admin/manual-gen/unresolved').get_json()
    row = [i for i in j['items'] if i['person_id'] == 'p_free'][0]
    assert row['manual'][0]['generation'] == 41


def test_rejects_bad_input(client):
    base = {'person_id': 'p_free', 'lineage_founder_dila_id': FOUNDER}
    assert client.post('/daoanh/api/admin/manual-gen/entry', json={**base, 'generation': 'x'}).status_code == 400
    assert client.post('/daoanh/api/admin/manual-gen/entry', json={**base, 'generation': 999}).status_code == 400
    assert client.post('/daoanh/api/admin/manual-gen/entry', json={
        'person_id': 'p_free', 'lineage_founder_dila_id': 'A999999', 'generation': 5}).status_code == 400
    assert client.post('/daoanh/api/admin/manual-gen/entry', json={
        'person_id': 'nobody', 'lineage_founder_dila_id': FOUNDER, 'generation': 5}).status_code == 404


def test_delete_writes_history(client):
    client.post('/daoanh/api/admin/manual-gen/entry', json={
        'person_id': 'p_free', 'lineage_founder_dila_id': FOUNDER, 'generation': 40})
    r = client.post('/daoanh/api/admin/manual-gen/entry/delete', json={
        'person_id': 'p_free', 'lineage_founder_dila_id': FOUNDER}).get_json()
    assert r['ok']
    h = client.get('/daoanh/api/admin/manual-gen/history?person_id=p_free').get_json()['items']
    assert h[0]['action'] == 'delete' and h[0]['old_generation'] == 40
    again = client.post('/daoanh/api/admin/manual-gen/entry/delete', json={
        'person_id': 'p_free', 'lineage_founder_dila_id': FOUNDER})
    assert again.status_code == 404


def test_etl_does_not_drop_manual_tables():
    src = open(os.path.join(ROOT, 'scripts', 'etl_gen_compute.py'), encoding='utf-8').read()
    drops = [l for l in src.splitlines() if 'DROP TABLE' in l]
    assert not any('person_generation_manual' in l for l in drops)
