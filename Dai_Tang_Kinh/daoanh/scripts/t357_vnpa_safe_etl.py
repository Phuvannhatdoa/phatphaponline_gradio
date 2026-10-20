"""T357: staged VNPA ETL, fail-closed preflight, atomic apply and scoped CAS rollback.

Mặc định chỉ tạo plan/artifacts; không mở production connection writable.
Control schema được chuẩn bị riêng, không tự migration trong apply.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'T357-v1'
GENERATION_SAFETY_RANGE = (1, 200)  # numeric safety only; không xác nhận hệ đếm/số đời.
TABLES = ('vn_person_authority', 'vn_person_relations', 'vn_person_places',
          'vn_person_works', 'vn_person_events')
KEYS = {
    'vn_person_authority': ('id',),
    'vn_person_relations': ('person_id', 'relation_type', 'target_id'),
    'vn_person_places': ('person_id', 'place_id'),
    'vn_person_works': ('person_id', 'work_id'),
    'vn_person_events': ('person_id', 'event_type', 'event_id'),
}
CONTROL_SCHEMA = (
    'CREATE TABLE vnpa_etl_runs (run_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, '
    'state TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL)',
    'CREATE TABLE vnpa_etl_changes (run_id TEXT NOT NULL, seq INTEGER NOT NULL, '
    'table_name TEXT NOT NULL, row_id_json TEXT NOT NULL, before_json TEXT, '
    'after_json TEXT, PRIMARY KEY(run_id,seq), '
    'FOREIGN KEY(run_id) REFERENCES vnpa_etl_runs(run_id))',
)


class SafetyError(RuntimeError):
    """Lỗi contract: dừng trước ghi hoặc rollback toàn transaction."""


class RollbackBlocked(SafetyError):
    state = "rollback_blocked"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pack(row):
    # SQLite types được giữ: NULL/TEXT/INTEGER/REAL/BLOB không bị gộp lẫn.
    return {k: {'blob_hex': v.hex()} if isinstance(v, bytes) else v
            for k, v in dict(row).items()}


def unpack(row):
    return {k: bytes.fromhex(v['blob_hex']) if isinstance(v, dict) else v
            for k, v in row.items()}


def quote(name):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name):
        raise SafetyError('Tên SQL không hợp lệ: ' + name)
    return '"' + name + '"'


def connect(db_path, mode='ro'):
    path = Path(db_path).resolve(strict=True)
    if not path.is_file():
        raise SafetyError('DB phải là file đã tồn tại')
    conn = sqlite3.connect(path.as_uri() + '?mode=' + mode, uri=True,
                           isolation_level=None, timeout=2)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    if mode == 'ro':
        conn.execute('PRAGMA query_only=ON')
    return conn


def schema(conn):
    return [dict(r) for r in conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")]


def require_schema(conn):
    for table in TABLES:
        columns = {r['name']: r for r in conn.execute('PRAGMA table_info(' + quote(table) + ')')}
        if 'id' not in columns or not columns['id']['pk'] or 'ttl_filename' not in columns:
            raise SafetyError('Schema không hỗ trợ stable PK/scope: ' + table)
        if columns['id']['type'].upper() != ('TEXT' if table == TABLES[0] else 'INTEGER'):
            raise SafetyError('PK type chưa hỗ trợ: ' + table)
        if not set(KEYS[table]).issubset(columns):
            raise SafetyError('Thiếu key nghiệp vụ: ' + table)
    for table, columns in (
        ('vnpa_etl_runs', {'run_id', 'plan_hash', 'state', 'result_json', 'created_at'}),
        ('vnpa_etl_changes', {'run_id', 'seq', 'table_name', 'row_id_json', 'before_json', 'after_json'}),
        ('ttl_mapping', {'ttl_filename', 'dila_id'}),
    ):
        actual = {r['name'] for r in conn.execute('PRAGMA table_info(' + quote(table) + ')')}
        if not columns.issubset(actual):
            raise SafetyError('Thiếu control/schema: ' + table + '; chuẩn bị riêng, không auto-migrate')


def initialize_controls(db_path):
    """Explicit additive preparation; không gọi từ plan/apply và không nhận DB mặc định."""
    production = Path(__file__).resolve().parents[1] / 'data' / 'lineage.db'
    target = Path(db_path).resolve(strict=True)
    if target == production.resolve() or (production.exists() and os.path.samefile(target, production)):
        raise SafetyError('T357 build không được migration DB production')
    conn = connect(target, 'rw')
    try:
        conn.execute('BEGIN IMMEDIATE')
        existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if {'vnpa_etl_runs', 'vnpa_etl_changes'} & existing:
            raise SafetyError('Control schema đã có hoặc chưa đầy đủ; không ghi đè')
        for statement in CONTROL_SCHEMA:
            conn.execute(statement)
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def managed_sql(table, keys):
    placeholders = ','.join('?' for _ in keys)
    where = 'ttl_filename IN (' + placeholders + ')'
    if table == 'vn_person_authority':
        where += " AND substr(id,1,6) <> 'alias_'"
    return where


def snapshot(conn, keys):
    result = {}
    for table in TABLES:
        all_hash, protected_hash = hashlib.sha256(), hashlib.sha256()
        total = protected = managed = 0
        managed_sum = 0
        for row in conn.execute('SELECT * FROM ' + quote(table) + ' ORDER BY id'):
            encoded = (canonical(pack(row)) + '\n').encode('utf-8')
            all_hash.update(encoded)
            total += 1
            is_managed = row['ttl_filename'] in keys
            if table == 'vn_person_authority' and str(row['id']).startswith('alias_'):
                is_managed = False
            if is_managed:
                managed += 1
                managed_sum = (managed_sum + int.from_bytes(hashlib.sha256(encoded).digest(), 'big')) % (1 << 256)
            else:
                protected_hash.update(encoded)
                protected += 1
        result[table] = {'count': total, 'hash': all_hash.hexdigest(),
                         'protected_count': protected, 'protected_hash': protected_hash.hexdigest(),
                         'managed_count': managed, 'managed_hash': '%064x' % managed_sum}
    return result


def scripts_manifest():
    root = Path(__file__).resolve().parent
    return {str(root / name): file_hash(root / name) for name in
            ('t357_vnpa_safe_etl.py', 'etl_ttl_person_authority.py', 't204_ttl_preflight.py', 't203_quarantine_ttl.py')}


def inputs_manifest(ttl_dir):
    root = Path(ttl_dir).resolve(strict=True)
    files = sorted(p for p in root.iterdir() if p.is_file() and p.suffix == '.ttl')
    if not files or len(files) > 64:
        raise SafetyError('Scope TTL phải có 1..64 file; không chạy full corpus')
    result = []
    for path in files:
        if path.stat().st_size > 4 * 1024 * 1024:
            raise SafetyError('TTL quá lớn cho parser một-file: ' + str(path))
        result.append({'path': str(path.resolve()), 'key': path.stem,
                       'sha256': file_hash(path), 'bytes': path.stat().st_size})
    return result


def load_reference(path, inputs):
    if not path:
        raise SafetyError('Thiếu frozen label reference; không scan corpus để dựng index')
    source = Path(path).resolve(strict=True)
    if source.stat().st_size > 1024 * 1024:
        raise SafetyError('Frozen reference quá lớn cho scope tối đa 64 files')
    with open(source, encoding='utf-8') as stream:
        value = json.load(stream)
    if (value.get('definition_version') != 'T357-label-reference-v1' or
            value.get('reviewed') is not True or not value.get('issuer') or not value.get('source_locators')):
        raise SafetyError('Frozen reference thiếu version/review/issuer/locator')
    required = {re.sub(r'^(TS|Cs|Bo-Tat)-', '', i['key'], flags=re.I).replace('-', '_').lower() for i in inputs}
    index = value.get('index', {})
    if set(index) != required or any(not labels or any(not isinstance(k, str) or not k or
            type(v) is not int or v <= 0 for k, v in labels.items()) for labels in index.values()):
        raise SafetyError('Frozen reference không đúng toàn bộ scope/key/label')
    return value


def default_preflight(ttl_dir, conn, label_reference):
    # T203 classifier giữ nguyên semantics, nhưng index là frozen artifact được review.
    # Clone function globals: không patch globals module, không gọi authoritative_index corpus.
    from types import FunctionType
    inputs = inputs_manifest(ttl_dir)
    reference = load_reference(label_reference, inputs)
    allowed = {str(Path(i['path']).resolve()) for i in inputs}
    def scoped_read(path):
        resolved = str(Path(path).resolve(strict=True))
        if resolved not in allowed:
            raise SafetyError('Preflight đọc ngoài scope: ' + resolved)
        with open(resolved, encoding='utf-8', errors='strict') as stream:
            return stream.read()
    pf = importlib.import_module('t204_ttl_preflight')
    q = importlib.import_module('t203_quarantine_ttl')
    qglobals = dict(q.classify.__globals__)
    qglobals.update(authoritative_index=lambda: reference['index'], read=scoped_read)
    classify = FunctionType(q.classify.__code__, qglobals, q.classify.__name__, q.classify.__defaults__)
    t1, t2, _ = classify(ttl_dir=ttl_dir)
    blocking = [{'code': code, 'file': r['file'], 'current': r['cur'], 'expected': r['corr'],
                 'evidence': r['evidence'], 'msg': r['why']}
                for records, code in ((t1, 'L1'), (t2, 'L2')) for r in records]
    for name in ('check_parse', 'check_empty', 'check_subject_collision'):
        original = getattr(pf, name)
        globals_scoped = dict(original.__globals__)
        globals_scoped['_read'] = scoped_read
        check = FunctionType(original.__code__, globals_scoped, original.__name__, original.__defaults__)
        findings = check(ttl_dir)
        if findings is None:
            raise SafetyError('Preflight parser dependency thiếu: ' + name)
        blocking.extend(findings)
    original = pf.check_mojibake
    globals_scoped = dict(original.__globals__)
    globals_scoped['_read'] = scoped_read
    warnings = FunctionType(original.__code__, globals_scoped, original.__name__, original.__defaults__)(ttl_dir)
    for row in conn.execute("SELECT dila_id,COUNT(*) AS n FROM vn_person_authority "
                            "WHERE dila_id IS NOT NULL AND dila_id<>'' "
                            "AND substr(id,1,6)<>'alias_' GROUP BY dila_id HAVING COUNT(*)>1"):
        warnings.append({'code': 'L5', 'dila_id': row[0], 'count': row[1]})
    return blocking, warnings


def check_ack(ack, bindings):
    if not ack or not ack.get('issuer'):
        raise SafetyError('Thiếu acknowledgment có issuer')
    for key, value in bindings.items():
        if ack.get(key) != value:
            raise SafetyError('Acknowledgment lệch ' + key)
    try:
        expires = datetime.fromisoformat(ack['expires_at'].replace('Z', '+00:00'))
        if expires.tzinfo is None or expires <= datetime.now(timezone.utc):
            raise ValueError('expired')
    except (KeyError, ValueError, TypeError) as exc:
        raise SafetyError('Acknowledgment thiếu/hết hạn') from exc


def stage_put(stage, kind, table, row):
    try:
        if kind == 'after':
            stage.execute('INSERT INTO business_keys VALUES (?,?)',
                          (table, canonical([row[k] for k in KEYS[table]])))
        stage.execute('INSERT INTO rows VALUES (?,?,?,?)',
                      (kind, table, canonical(row['id']), canonical(pack(row))))
    except sqlite3.IntegrityError as exc:
        raise SafetyError('Duplicate stable key trong staging: ' + table) from exc


def materialize(conn, table, incoming, existing=None, new_id=None):
    row = dict(existing) if existing is not None else {}
    for column in conn.execute('PRAGMA table_info(' + quote(table) + ')'):
        name = column['name']
        if name not in row:
            # Chỉ constant/default đã biết; unknown expression không tự đánh giá/đoán.
            default = column['dflt_value']
            if name in incoming:
                row[name] = incoming[name]
            elif default == 'CURRENT_TIMESTAMP':
                row[name] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            elif default is None or default.upper() == 'NULL':
                row[name] = None
            elif re.fullmatch(r'-?\d+', default):
                row[name] = int(default)
            elif len(default) >= 2 and default[0] == default[-1] == "'":
                row[name] = default[1:-1].replace("''", "'")
            else:
                raise SafetyError('Default schema chưa hỗ trợ: ' + table + '.' + name)
    row.update(incoming)
    for column in conn.execute('PRAGMA table_info(' + quote(table) + ')'):
        if column['notnull'] and row.get(column['name']) is None:
            raise SafetyError('NULL trong cột bắt buộc: ' + table + '.' + column['name'])
    if new_id is not None:
        row['id'] = new_id
    return row


def find_business_row(conn, table, row):
    predicate = ' AND '.join(quote(k) + ' IS ?' for k in KEYS[table])
    cursor = conn.execute('SELECT * FROM ' + quote(table) + ' WHERE ' + predicate,
                          tuple(row[k] for k in KEYS[table]))
    first = cursor.fetchone()
    if cursor.fetchone() is not None:
        raise SafetyError('DB duplicate business key: ' + table)
    return first


def iter_diff(stage):
    cursor = stage.execute("SELECT table_name,row_key FROM rows GROUP BY table_name,row_key "
                           "ORDER BY table_name,row_key")
    for table, key in cursor:
        pair = {}
        for kind, text in stage.execute('SELECT kind,row_json FROM rows WHERE table_name=? AND row_key=?',
                                       (table, key)):
            pair[kind] = text
        if pair.get('before') != pair.get('after'):
            yield table, key, pair.get('before'), pair.get('after')




def diff_digest(stage):
    h = hashlib.sha256()
    for item in iter_diff(stage):
        h.update((canonical(item) + '\n').encode('utf-8'))
    return h.hexdigest()


def ledger_diff_digest(conn, run_id):
    h = hashlib.sha256()
    for row in conn.execute('SELECT table_name,row_id_json,before_json,after_json FROM vnpa_etl_changes '
                            'WHERE run_id=? ORDER BY seq', (run_id,)):
        h.update((canonical(list(row)) + '\n').encode('utf-8'))
    return h.hexdigest()


def execute_one(conn, statement, args):
    cursor = conn.execute(statement, args)
    if cursor.rowcount != 1:
        raise SafetyError('Control affected rowcount phải bằng 1')
    return cursor


def mapping_digest(conn):
    h = hashlib.sha256()
    for row in conn.execute('SELECT * FROM ttl_mapping ORDER BY ttl_filename,dila_id'):
        h.update((canonical(pack(row)) + '\n').encode('utf-8'))
    return h.hexdigest()


def write_authorizer(action, first, second, database, trigger):
    if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE):
        # Trigger-origin DML không được hỗ trợ, kể cả final ledger write.
        if trigger:
            return sqlite3.SQLITE_DENY
        if first not in set(TABLES) | {'vnpa_etl_runs', 'vnpa_etl_changes', 'sqlite_sequence'}:
            return sqlite3.SQLITE_DENY
    if action in (sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE,
                  sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def make_plan(db_path, ttl_dir, out_dir, run_id=None, waiver=None, preflight=None, label_reference=None):
    run_id = run_id or 'VNPA-' + uuid.uuid4().hex
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', run_id):
        raise SafetyError('run_id không hợp lệ')
    inputs = inputs_manifest(ttl_dir)
    keys = [item['key'] for item in inputs]
    load_reference(label_reference, inputs)
    reference_info = {'path': str(Path(label_reference).resolve()), 'sha256': file_hash(label_reference)}
    db = str(Path(db_path).resolve(strict=True))
    scripts = scripts_manifest()
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    stage = sqlite3.connect(out / 'stage.sqlite')
    stage.execute('CREATE TABLE rows(kind TEXT,table_name TEXT,row_key TEXT,row_json TEXT, '
                  'PRIMARY KEY(kind,table_name,row_key))')
    stage.execute('CREATE TABLE provenance(file_key TEXT PRIMARY KEY,subject TEXT,sha256 TEXT)')
    stage.execute('CREATE TABLE business_keys(table_name TEXT, business_key TEXT, PRIMARY KEY(table_name,business_key))')
    candidates = open(out / 'date-candidates.jsonl', 'x', encoding='utf-8')
    conn = connect(db)
    try:
        conn.execute('BEGIN')
        require_schema(conn)
        before = snapshot(conn, keys)
        schema_hash = digest(schema(conn))
        mapping_hash = mapping_digest(conn)
        blocking, warnings = (preflight or default_preflight)(str(Path(ttl_dir).resolve()), conn, label_reference)
        findings = sorted(blocking + warnings, key=canonical)
        if findings:
            if any(item.get('code') not in ('L1', 'L2', 'L4', 'L5') for item in findings):
                raise SafetyError('Parse/empty/subject collision không được waiver')
            check_ack(waiver, {'run_id': run_id, 'db_path': db, 'input_hash': digest(inputs),
                              'script_hash': digest(scripts), 'findings_hash': digest(findings)})
        for table in TABLES:
            for row in conn.execute('SELECT * FROM ' + quote(table) + ' WHERE ' + managed_sql(table, keys), keys):
                stage_put(stage, 'before', table, dict(row))
        parser_mod = importlib.import_module('etl_ttl_person_authority')
        next_ids = {t: conn.execute('SELECT COALESCE(MAX(id),0) FROM ' + quote(t)).fetchone()[0]
                    for t in TABLES[1:]}
        seen_subjects = set()  # bounded by 64 input files, not corpus triples.
        for item in inputs:
            graph = parser_mod.rdflib.Graph()
            graph.parse(item['path'], format='turtle')
            parser = parser_mod.TTLMonkParser(graph, item['key'])
            parser.parse()
            if not parser.person or not parser.person['name_vi']:
                raise SafetyError('Không có person/label: ' + item['path'])
            person = parser.person
            generation = person.get('generation_order')
            if generation is not None and (type(generation) is not int or not GENERATION_SAFETY_RANGE[0] <= generation <= GENERATION_SAFETY_RANGE[1]):
                raise SafetyError('generationOrder ngoài policy safety 1..200; cần quarantine/review')
            if any(c in person['id'] for c in ('\"', '\\')) or any(ord(c)<32 for c in person['id']):
                raise SafetyError('Person key chứa ký tự không hỗ trợ')
            if person['id'].startswith('alias_') or person['id'] in seen_subjects:
                raise SafetyError('Alias/subject collision: ' + person['id'])
            seen_subjects.add(person['id'])
            mapping = conn.execute('SELECT dila_id FROM ttl_mapping WHERE ttl_filename=? AND dila_id IS NOT NULL',
                                   (item['key'],))
            match = mapping.fetchone()
            if mapping.fetchone() is not None:
                raise SafetyError('ttl_mapping không duy nhất: ' + item['key'])
            person['dila_id'] = match[0] if match else ''
            person['appellations'] = canonical(person['appellations'])
            existing = find_business_row(conn, TABLES[0], person)
            if existing is not None and existing['ttl_filename'] != item['key']:
                raise SafetyError('Person ID chạm row ngoài scope')
            if existing is not None:
                for name in ('dila_id', 'status', 'name_vi', 'name_zh', 'birth_year', 'death_year',
                             'generation_order', 'is_lineage_founder', 'dharma_lineage'):
                    if existing[name] not in (None, '') and not (name == 'status' and existing[name] == 'pending'):
                        if person.get(name) != existing[name]:
                            candidates.write(canonical({'person_id': person['id'], 'field': name,
                                'incoming': person.get(name), 'preserved': existing[name],
                                'reason': 'protected-field-conflict', 'source': item}) + '\n')
                        person[name] = existing[name]
            stage_put(stage, 'after', TABLES[0], materialize(conn, TABLES[0], person, existing))
            stage.execute('INSERT INTO provenance VALUES (?,?,?)',
                          (item['key'], getattr(parser, 'subject_uri', person['id']), item['sha256']))
            note = person.get('biographical_note_vi') or ''
            for match in re.finditer(r'(?<!\d)\d{3,4}(?!\d)', note):
                candidates.write(canonical({'person_id': person['id'], 'year_candidate': match.group(),
                    'reason': 'biography-year-not-canonical', 'source': item,
                    'locator': 'biographicalNote chars %s:%s' % match.span(),
                    'excerpt': note[max(0,match.start()-50):match.end()+50]}) + '\n')
            for table, rows in zip(TABLES[1:], (parser.relations, parser.places, parser.works, parser.events)):
                for incoming in rows:
                    if table == 'vn_person_relations' and incoming['relation_type'] in ('hasTeacher', 'hasDisciple') and incoming['person_id'] == incoming['target_id']:
                        raise SafetyError('Self teacher/disciple bị chặn trước writable')
                    old = find_business_row(conn, table, incoming)
                    if old is not None and old['ttl_filename'] != item['key']:
                        raise SafetyError('Child business key chạm row ngoài scope: ' + table)
                    if old is None:
                        next_ids[table] += 1
                    stage_put(stage, 'after', table,
                              materialize(conn, table, incoming, old, old['id'] if old else next_ids[table]))
            del parser, graph
        if inputs_manifest(ttl_dir) != inputs or scripts_manifest() != scripts:
            raise SafetyError('Input/code drift trong staging')
        counts = {'accepted': 0, 'inserted': 0, 'updated': 0, 'deleted': 0, 'skipped': 0, 'failed': 0}
        for table, key, b, a in iter_diff(stage):
            counts['deleted' if a is None else 'inserted' if b is None else 'updated'] += 1
        counts['accepted'] = stage.execute("SELECT COUNT(*) FROM rows WHERE kind='after'").fetchone()[0]
        counts['skipped'] = counts['accepted'] - counts['inserted'] - counts['updated']
        stage.commit()
        changes_hash = diff_digest(stage)
        stage.close()
        candidates.close()
        plan = {'version': VERSION, 'run_id': run_id, 'db_path': db, 'ttl_dir': str(Path(ttl_dir).resolve()),
                'inputs': inputs, 'scripts': scripts, 'schema_hash': schema_hash, 'before': before,
                'mapping_hash': mapping_hash, 'label_reference': reference_info,
                'physical_db_hash_provenance_only': file_hash(db), 'waiver': waiver,
                'findings': findings, 'counts': counts, 'stage_hash': file_hash(out / 'stage.sqlite'),
                'diff_hash': changes_hash,
                'candidate_hash': file_hash(out / 'date-candidates.jsonl'),
                'created_at': datetime.now(timezone.utc).isoformat()}
        plan['plan_hash'] = digest(plan)
        with open(out / 'plan.json', 'x', encoding='utf-8') as stream:
            stream.write(canonical(plan) + '\n')
        return plan
    except BaseException:
        stage.close()
        candidates.close()
        raise
    finally:
        conn.close()


def load_plan(out_dir):
    out = Path(out_dir).resolve(strict=True)
    with open(out / 'plan.json', encoding='utf-8') as stream:
        plan = json.load(stream)
    expected = plan.pop('plan_hash')
    if digest(plan) != expected:
        raise SafetyError('Plan manifest hash lệch')
    plan['plan_hash'] = expected
    if plan['version'] != VERSION or file_hash(out / 'stage.sqlite') != plan['stage_hash']:
        raise SafetyError('Version/staging drift')
    if file_hash(out / 'date-candidates.jsonl') != plan['candidate_hash']:
        raise SafetyError('Candidate artifact drift')
    return out, plan


@contextmanager
def writer_gate(db_path):
    # Cooperative lock cho ETL; các app writers vẫn phải quiesce theo acknowledgment.
    lock = Path(str(db_path) + '.t357-writer.lock')
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise SafetyError('Writer lock tồn tại; không tự xóa stale lock') from exc
    try:
        os.write(descriptor, ('pid=' + str(os.getpid())).encode())
        os.close(descriptor)
        yield
    finally:
        lock.unlink()


def current_row(conn, table, key):
    row = conn.execute('SELECT * FROM ' + quote(table) + ' WHERE id IS ?', (json.loads(key),)).fetchone()
    return canonical(pack(row)) if row is not None else None


def mutate(conn, table, key, before, after):
    if table not in TABLES or current_row(conn, table, key) != before:
        raise SafetyError('Row drift/CAS: ' + table + ' ' + key)
    if after is None:
        cursor = conn.execute('DELETE FROM ' + quote(table) + ' WHERE id IS ?', (json.loads(key),))
    else:
        row = unpack(json.loads(after))
        if before is None:
            cols = list(row)
            cursor = conn.execute('INSERT INTO ' + quote(table) + ' (' + ','.join(map(quote, cols)) +
                                  ') VALUES (' + ','.join('?' for _ in cols) + ')', tuple(row[c] for c in cols))
        else:
            cols = [c for c in row if c != 'id']
            cursor = conn.execute('UPDATE ' + quote(table) + ' SET ' + ','.join(quote(c) + '=?' for c in cols) +
                                  ' WHERE id IS ?', tuple(row[c] for c in cols) + (row['id'],))
    if cursor.rowcount != 1 or current_row(conn, table, key) != after:
        raise SafetyError('Affected rowcount/values mismatch: ' + table)


def apply_plan(out_dir, authorization, fault=None, trace=None):
    out, plan = load_plan(out_dir)
    check_ack(authorization, {'run_id': plan['run_id'], 'db_path': plan['db_path'],
                              'plan_hash': plan['plan_hash'], 'external_writers_quiesced': True})
    stage = sqlite3.connect((out / 'stage.sqlite').as_uri() + '?mode=ro', uri=True)
    conn = None
    committed = False
    hook = fault or (lambda _: None)
    try:
        with writer_gate(plan['db_path']):
            # RO gate có trước RW; missing module/preflight error không được bỏ qua.
            ro = connect(plan['db_path'])
            try:
                require_schema(ro)
                prior = ro.execute('SELECT * FROM vnpa_etl_runs WHERE run_id=?', (plan['run_id'],)).fetchone()
                if prior:
                    if prior['plan_hash'] != plan['plan_hash'] or prior['state'] != 'committed':
                        raise SafetyError('run_id collision/state conflict')
                    return {'state': 'committed', 'replayed': True,
                            'counts': {'accepted': 0, 'inserted': 0, 'updated': 0, 'deleted': 0,
                                       'skipped': plan['counts']['accepted'], 'failed': 0}}
                if inputs_manifest(plan['ttl_dir']) != plan['inputs'] or scripts_manifest() != plan['scripts']:
                    raise SafetyError('Input/code drift trước apply')
                if file_hash(plan['label_reference']['path']) != plan['label_reference']['sha256']:
                    raise SafetyError('Frozen reference drift')
                blocking, warnings = default_preflight(plan['ttl_dir'], ro, plan['label_reference']['path'])
                findings = sorted(blocking + warnings, key=canonical)
                if findings != plan['findings']:
                    raise SafetyError('Preflight findings drift')
                if findings:
                    check_ack(plan['waiver'], {'run_id': plan['run_id'], 'db_path': plan['db_path'],
                              'input_hash': digest(plan['inputs']), 'script_hash': digest(plan['scripts']),
                              'findings_hash': digest(findings)})
            finally:
                ro.close()
            conn = connect(plan['db_path'], 'rw')
            conn.set_authorizer(write_authorizer)
            if trace:
                conn.set_trace_callback(trace)
            conn.execute('BEGIN IMMEDIATE')
            require_schema(conn)
            live_mapping_hash = mapping_digest(conn)
            if live_mapping_hash != plan['mapping_hash']:
                raise SafetyError('ttl_mapping drift trước apply')
            keys = [i['key'] for i in plan['inputs']]
            if digest(schema(conn)) != plan['schema_hash'] or snapshot(conn, keys) != plan['before']:
                raise SafetyError('Schema/logical baseline drift trước mutation')
            hook('after_begin')
            # Reserved write lock giữ baseline; ro backup chứa cùng before snapshot.
            backup = out / 'before.sqlite'
            if backup.exists():
                raise SafetyError('Backup artifact đã tồn tại; reconcile run thay vì overwrite')
            source = connect(plan['db_path'])
            destination = sqlite3.connect(backup)
            try:
                source.backup(destination)
                destination.row_factory = sqlite3.Row
                if snapshot(destination, keys) != plan['before']:
                    raise SafetyError('Logical backup mismatch')
            finally:
                source.close()
                destination.close()
            result = {'state': 'committed', 'run_id': plan['run_id'], 'replayed': False,
                      'counts': dict(plan['counts']), 'plan_hash': plan['plan_hash'],
                      'backup_hash': file_hash(backup), 'diff_hash': plan['diff_hash']}
            execute_one(conn, 'INSERT INTO vnpa_etl_runs VALUES (?,?,?,?,?)',
                         (plan['run_id'], plan['plan_hash'], 'committed', canonical(result),
                          datetime.now(timezone.utc).isoformat()))
            actual = {'inserted': 0, 'updated': 0, 'deleted': 0}
            for seq, (table, key, before, after) in enumerate(iter_diff(stage), 1):
                mutate(conn, table, key, before, after)
                kind = 'deleted' if after is None else 'inserted' if before is None else 'updated'
                actual[kind] += 1
                execute_one(conn, 'INSERT INTO vnpa_etl_changes VALUES (?,?,?,?,?,?)',
                             (plan['run_id'], seq, table, key, before, after))
                hook('after_' + kind + ':' + table)
            if ledger_diff_digest(conn, plan['run_id']) != plan['diff_hash']:
                raise SafetyError('Durable inverse diff mismatch')
            if any(actual[k] != plan['counts'][k] for k in actual):
                raise SafetyError('Total affected rowcount mismatch')
            for table, key, before, after in iter_diff(stage):
                if current_row(conn, table, key) != after:
                    raise SafetyError('Postcondition row drift')
            after_snapshot = snapshot(conn, keys)
            for table in TABLES:
                expected_sum = expected_count = 0
                for (text,) in stage.execute("SELECT row_json FROM rows WHERE kind='after' AND table_name=?", (table,)):
                    encoded = (text + '\n').encode('utf-8')
                    expected_sum = (expected_sum + int.from_bytes(hashlib.sha256(encoded).digest(), 'big')) % (1 << 256)
                    expected_count += 1
                if after_snapshot[table]['managed_count'] != expected_count or after_snapshot[table]['managed_hash'] != '%064x' % expected_sum:
                    raise SafetyError('Expected managed rowset mismatch: ' + table)
                for field in ('protected_count', 'protected_hash'):
                    if after_snapshot[table][field] != plan['before'][table][field]:
                        raise SafetyError('Protected rowset changed')
            result['after'] = after_snapshot
            execute_one(conn, 'UPDATE vnpa_etl_runs SET result_json=? WHERE run_id=?',
                         (canonical(result), plan['run_id']))
            hook('before_commit')
            conn.commit()  # chỉ một COMMIT cho business rows + durable ledger.
            committed = True
            hook('after_commit')
            with open(out / 'result.json', 'x', encoding='utf-8') as stream:
                stream.write(canonical(result) + '\n')
            return result
    except BaseException as exc:
        if conn is not None and not committed:
            conn.rollback()
        if isinstance(exc, sqlite3.Error):
            raise SafetyError('SQL/unsupported trigger write blocked: ' + str(exc)) from exc
        raise
    finally:
        if conn is not None:
            conn.close()
        stage.close()



def untouched_fingerprints(conn, run_id):
    """Full untouched rows across all tables, including outside scope, streamed by PK."""
    result = {}
    for table in TABLES:
        h, count = hashlib.sha256(), 0
        cursor = conn.execute('SELECT t.* FROM ' + quote(table) + ' t WHERE NOT EXISTS '
            '(SELECT 1 FROM vnpa_etl_changes c WHERE c.run_id=? AND c.table_name=? '
            'AND c.row_id_json=json_quote(t.id)) ORDER BY t.id', (run_id, table))
        for row in cursor:
            h.update((canonical(pack(row)) + '\n').encode('utf-8'))
            count += 1
        result[table] = {'count': count, 'hash': h.hexdigest()}
    return result


def rollback_run(db_path, run_id, authorization, fault=None):
    db = str(Path(db_path).resolve(strict=True))
    hook = fault or (lambda _: None)
    with writer_gate(db):
        ro = connect(db)
        try:
            require_schema(ro)
            run = ro.execute('SELECT * FROM vnpa_etl_runs WHERE run_id=?', (run_id,)).fetchone()
            if not run or run['state'] != 'committed':
                raise SafetyError('Không có committed run để rollback')
            check_ack(authorization, {'run_id': run_id, 'db_path': db,
                                      'plan_hash': run['plan_hash'], 'external_writers_quiesced': True,
                                      'diff_hash': json.loads(run['result_json'])['diff_hash']})
        finally:
            ro.close()
        conn = connect(db, 'rw')
        conn.set_authorizer(write_authorizer)
        try:
            conn.execute('BEGIN IMMEDIATE')
            live = conn.execute('SELECT * FROM vnpa_etl_runs WHERE run_id=?', (run_id,)).fetchone()
            if not live or live['state'] != 'committed' or live['plan_hash'] != run['plan_hash']:
                raise SafetyError('Run ledger drift')
            if ledger_diff_digest(conn, run_id) != authorization['diff_hash']:
                raise SafetyError('Inverse ledger hash drift')
            # Kiểm toàn CAS trước mutation; không đè app updates ngoài/ trong phạm vi.
            for row in conn.execute('SELECT * FROM vnpa_etl_changes WHERE run_id=? ORDER BY seq', (run_id,)):
                if current_row(conn, row['table_name'], row['row_id_json']) != row['after_json']:
                    raise SafetyError('Rollback drift: ' + row['table_name'])
            untouched_before = untouched_fingerprints(conn, run_id)
            restored = 0
            for row in conn.execute('SELECT * FROM vnpa_etl_changes WHERE run_id=? ORDER BY seq DESC', (run_id,)):
                mutate(conn, row['table_name'], row['row_id_json'], row['after_json'], row['before_json'])
                restored += 1
                hook('after_inverse')
            if untouched_fingerprints(conn, run_id) != untouched_before:
                raise RollbackBlocked('Rollback protected/outside rowset drift (trigger effects)')
            for row in conn.execute('SELECT * FROM vnpa_etl_changes WHERE run_id=? ORDER BY seq', (run_id,)):
                if current_row(conn, row['table_name'], row['row_id_json']) != row['before_json']:
                    raise RollbackBlocked('Rollback inverse expected rowset drift')
            execute_one(conn, "UPDATE vnpa_etl_runs SET state='rolled_back' WHERE run_id=?", (run_id,))
            conn.commit()
            return {'state': 'rolled_back', 'run_id': run_id, 'restored': restored}
        except BaseException as exc:
            conn.rollback()
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise RollbackBlocked('rollback_blocked: ' + str(exc)) from exc
        finally:
            conn.close()


def read_json(path):
    if path is None:
        return None
    with open(path, encoding='utf-8') as stream:
        return json.load(stream)


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('plan', 'apply', 'rollback', 'initialize-controls'), default='plan')
    parser.add_argument('--db', required=True, help='DB tồn tại; tuyệt đối không tự tạo')
    parser.add_argument('--ttl-dir')
    parser.add_argument('--out-dir')
    parser.add_argument('--run-id')
    parser.add_argument('--waiver')
    parser.add_argument('--label-reference', help='Frozen scoped label index đã được review, bắt buộc cho plan')
    parser.add_argument('--authorization')
    parser.add_argument('--skip-preflight', action='store_true', help='Bị cấm; fail-closed')
    args = parser.parse_args(argv)
    try:
        if args.skip_preflight:
            raise SafetyError('--skip-preflight bị cấm; dùng exact scoped waiver đã duyệt')
        if args.mode == 'initialize-controls':
            initialize_controls(args.db)
            result = {'state': 'controls_initialized', 'db_path': str(Path(args.db).resolve())}
        elif args.mode == 'plan':
            if not args.ttl_dir or not args.out_dir:
                raise SafetyError('Plan cần --ttl-dir và --out-dir explicit')
            result = make_plan(args.db, args.ttl_dir, args.out_dir, args.run_id, read_json(args.waiver), label_reference=args.label_reference)
        elif args.mode == 'apply':
            if not args.out_dir:
                raise SafetyError('Apply cần --out-dir plan đã review')
            _, plan = load_plan(args.out_dir)
            if str(Path(args.db).resolve(strict=True)) != plan['db_path']:
                raise SafetyError('--db khác DB bind trong plan')
            result = apply_plan(args.out_dir, read_json(args.authorization))
        else:
            if not args.run_id:
                raise SafetyError('Rollback cần --run-id')
            result = rollback_run(args.db, args.run_id, read_json(args.authorization))
        print(canonical(result))
        return 0
    except Exception as exc:
        if args.mode == 'apply' and args.out_dir:
            try:
                _, p = load_plan(args.out_dir)
                recovery = connect(p['db_path'])
                try:
                    recorded = recovery.execute('SELECT * FROM vnpa_etl_runs WHERE run_id=?', (p['run_id'],)).fetchone()
                    if recorded and recorded['state'] == 'committed' and recorded['plan_hash'] == p['plan_hash']:
                        result = json.loads(recorded['result_json'])
                        result.update(state='committed_artifact_failed', artifact_error=str(exc))
                        print(canonical(result))
                        return 2
                finally:
                    recovery.close()
            except Exception:
                pass
        print(canonical({'state': 'rollback_blocked' if args.mode == 'rollback' else 'failed', 'counts': {'accepted': 0, 'inserted': 0, 'updated': 0,
              'deleted': 0, 'skipped': 0, 'failed': 1}, 'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(cli())
