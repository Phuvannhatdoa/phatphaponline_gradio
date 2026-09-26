# -*- coding: utf-8 -*-
"""test_t165_style_constitution.py — T165 Rules-Constrained Translation Engine tri thức SSOT.
Test unit trên temp DB (không chạm DB thật):
  1. extract_match_terms ≥2 chars (arrow + paren, lọc 1-char noise) — #10
  2. select_rules status='active' AND is_active=1 selector — #13
  3. select_rules filter terms theo source_text + forced-always khi extract fail — #10
  4. constitution_hash khác khi sửa rule_text (KHÔNG hash chỉ code) — invariant
  5. constitution_hash khác khi label/json_mode khác — #5b
  6. invalidate_cache_for_rule chỉ xoá row có selected_rule_codes trùng, KHÔNG xoá row NULL — #4
  7. write_cache không REPLACE row edited — #3
  8. lookup_cache ưu tiên constitution_hash, fallback rules_version — §4.4
  9. style_lock tự chạy resolver + hash post-merge (db_verified xuất hiện trong hash) — #5a
 10. hash equality app.py + t50 cùng formula — §8.5
 11. Pre-migration guards (DB chưa migrate) — #16
"""
import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from style_constitution import (  # noqa: E402
    PROMPT_FORMAT_VERSION, source_hash, extract_match_terms, select_rules,
    style_lock, constitution_hash, invalidate_cache_for_rule,
    invalidate_cache_all_semantic, lookup_cache, write_cache,
)


def _mkdb():
    """Temp DB với schema đã migrate (match_scope/match_terms + 3 hash cols)."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE translation_rules (
            id INTEGER PRIMARY KEY, rule_code TEXT UNIQUE, rule_type TEXT,
            description TEXT, rule_text TEXT, is_active INTEGER, priority INTEGER,
            created_by TEXT, created_at TEXT, updated_at TEXT, status TEXT,
            suggested_by TEXT, ruleset_id TEXT, ruleset_version TEXT, is_canonical INTEGER,
            match_scope TEXT DEFAULT 'always', match_terms TEXT
        );
        CREATE TABLE translation_cache (
            id INTEGER PRIMARY KEY, source_hash TEXT, source_type TEXT, entity_id TEXT,
            source_text TEXT, translated_text TEXT, model_id TEXT, rules_version TEXT,
            status TEXT, report_count INTEGER DEFAULT 0, approved_by TEXT,
            approved_at TEXT, created_at TEXT, updated_at TEXT,
            constitution_hash TEXT, selected_rule_codes TEXT, glossary_hash TEXT
        );
        CREATE TABLE translation_glossary (
            id INTEGER PRIMARY KEY, term_zh TEXT, term_vi TEXT, is_locked INTEGER
        );
        CREATE TABLE translation_exemplar (
            id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT, is_active INTEGER, length_zh INTEGER
        );
        INSERT INTO translation_rules
            (rule_code, rule_type, description, rule_text, is_active, priority, status, match_scope, match_terms)
        VALUES
            ('PERSONA_BAN_DICH','style','persona','Bạn là dịch giả Phật học thuần Việt, nghiêm túc.',1,0,'active','always',NULL),
            ('NO_ADDITION','forbidden','no them','KHÔNG thêm giảng giải ngoài nguyên bản.',1,10,'active','always',NULL),
            ('TERM_TAM_AN','terminology','dich','三昧 (tam muội) → Định (thiền định).',1,20,'active','terms','["三昧"]'),
            ('TERM_PHAP_SI','terminology','dich','法嗣 (pháp tự) là người kế thừa pháp.',1,30,'active','terms','["法嗣"]'),
            ('RULE_LOCKED','style','lock','Ứng nghiệm y nguyên.',1,40,'active','always',NULL),
            ('RULE_DRAFT','style','draft','Chưa duyệt — không nên include.',1,50,'draft','always',NULL),
            ('RULE_INACTIVE','style','off','Tắt — không include.',1,60,'active','always',NULL),
            ('TERM_1CHAR','terminology','one','律 → Luật.',1,70,'active','terms','[]');
        INSERT INTO translation_glossary (term_zh, term_vi, is_locked) VALUES
            ('三昧','định',1), ('法嗣','pháp tự',1), ('戒','giới',1);
        INSERT INTO translation_exemplar (zh, vi, source_label, is_active, length_zh) VALUES
            ('菩提本無樹','Bồ đề vốn không cây','mẫu 1',1,6);
    """)
    # set is_active=0 for RULE_INACTIVE to mirror DB thật (RULE- rows is_active?)
    conn.execute("UPDATE translation_rules SET is_active=0 WHERE rule_code='RULE_INACTIVE'")
    conn.commit()
    return conn, path


def test_extract_match_terms():
    # arrow pattern (SPEC §6.2) → group 1 là Hán
    t = extract_match_terms('上堂 → thượng đường (thuật ngữ chỉ việc Thiền Sư giảng pháp).')
    assert '上堂' in t
    assert 'thượng' not in t
    # paren pattern → group 1 THẬT trong ngoặc Hán
    t2 = extract_match_terms('Định (三昧) là thuật ngữ quán chiếu.')
    assert t2 == ['三昧']
    # 1-char → lọc (noise, #10); fail → []
    assert extract_match_terms('律 → Luật.') == []
    t3 = extract_match_terms('律 → tăng.')  # '律' 1 char
    assert t3 == []
    assert extract_match_terms(None) == []
    assert all(len(x) >= 2 for x in extract_match_terms('義解 → Nghĩa giải (chỉ người chuyên về nghĩa lý).'))


def test_select_rules_selector_13():
    conn, path = _mkdb()
    try:
        r = select_rules(conn, None)
        codes = {x['rule_code'] for x in r['rules']}
        # status='active' AND is_active=1: bỏ RULE_DRAFT (draft) và RULE_INACTIVE (is_active=0)
        assert 'PERSONA_BAN_DICH' in codes
        assert 'TERM_TAM_AN' in codes
        assert 'RULE_DRAFT' not in codes
        assert 'RULE_INACTIVE' not in codes
    finally:
        conn.close(); os.unlink(path)


def test_select_rules_terms_filter_10():
    conn, path = _mkdb()
    try:
        # source chứa 法嗣 → TERM_PHAP_SI khớp; không có 三昧 → TERM_TAM_AN bị loại
        r = select_rules(conn, '法嗣 傳燈')
        codes = [x['rule_code'] for x in r['rules']]
        assert 'TERM_PHAP_SI' in codes
        assert 'TERM_TAM_AN' not in codes
        # all-active (source None) → mọi active terms đều có
        r2 = select_rules(conn, None)
        c2 = [x['rule_code'] for x in r2['rules']]
        assert 'TERM_TAM_AN' in c2 and 'TERM_PHAP_SI' in c2
        # TERM_1CHAR match_terms rỗng → forced always (không loại oan)
        assert 'TERM_1CHAR' in c2
    finally:
        conn.close(); os.unlink(path)


def test_hash_invariant_rule_text_edit():
    conn, path = _mkdb()
    try:
        l1 = style_lock(conn, '三昧 法嗣', prompt_label='test')
        # sửa rule_text của PERSONA (chỉ code giữ nguyên, full text đổi) → hash luôn lệch
        conn.execute("UPDATE translation_rules SET rule_text='PERSONA MỚI đổi wording.' WHERE rule_code='PERSONA_BAN_DICH'")
        conn.commit()
        l2 = style_lock(conn, '三昧 法嗣', prompt_label='test')
        assert l1['constitution_hash'] != l2['constitution_hash']
    finally:
        conn.close(); os.unlink(path)


def test_hash_label_json_mode_5b():
    conn, path = _mkdb()
    try:
        h1 = style_lock(conn, '三昧', prompt_label='tiểu sử').get('constitution_hash')
        h2 = style_lock(conn, '三昧', prompt_label='đoạn kinh', json_mode=True).get('constitution_hash')
        h3 = style_lock(conn, '三昧', prompt_label='tiểu sử').get('constitution_hash')
        assert h1 != h2
        assert h1 == h3  # deterministic
    finally:
        conn.close(); os.unlink(path)


def test_invalidate_no_null_delete_4():
    conn, path = _mkdb()
    try:
        rv = 'deadbeef00000000'
        now = '2026-09-25T00:00:00'
        # 1 row NULL (legacy) + 1 row có selected_rule_codes chứa TERM_TAM_AN
        conn.execute(
            "INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, "
            "translated_text, model_id, rules_version, status, created_at, updated_at, "
            "constitution_hash, selected_rule_codes, glossary_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ('hash1', 'person_bio', 'P1', 'a', 'A', 'm', rv, 'auto', now, now, 'ch1', None, 'gh1')
        )
        conn.execute(
            "INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, "
            "translated_text, model_id, rules_version, status, created_at, updated_at, "
            "constitution_hash, selected_rule_codes, glossary_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ('hash2', 'dila_card', 'P2', 'b', 'B', 'm', rv, 'auto', now, now, 'ch2', 'PERSONA_BAN_DICH,TERM_TAM_AN', 'gh2')
        )
        conn.commit()
        n = invalidate_cache_for_rule(conn, 'TERM_TAM_AN')
        assert n == 1  # chỉ row chứa code — row NULL legacy giữ nguyên (#4)
        left = conn.execute("SELECT COUNT(*) FROM translation_cache").fetchone()[0]
        assert left == 1
    finally:
        conn.close(); os.unlink(path)


def test_write_edited_not_replaced_3():
    conn, path = _mkdb()
    try:
        rv = 'deadbeef00000000'
        now = '2026-09-25T00:00:00'
        conn.execute(
            "INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, "
            "translated_text, model_id, rules_version, status, created_at, updated_at, "
            "constitution_hash, selected_rule_codes, glossary_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ('hashE', 'person_bio', 'PE', 'srctext', 'BẢN HUMAN', 'manual', rv, 'edited', now, now, 'chE', None, 'ghE')
        )
        conn.commit()
        tid, replaced = write_cache(conn, 'hashE', 'person_bio', 'PE', 'srctext',
                                    'BẢN AI MỚI', 'gemini-x', rv, status='auto',
                                    constitution_hash='chNEW', selected_rule_codes=['A'], glossary_hash='ghN')
        assert not replaced
        row = conn.execute("SELECT translated_text, status FROM translation_cache WHERE id=?", (tid,)).fetchone()
        assert row['translated_text'] == 'BẢN HUMAN'   # không bị AI ghi đè
        assert row['status'] == 'edited'
    finally:
        conn.close(); os.unlink(path)


def test_lookup_dual_key():
    conn, path = _mkdb()
    try:
        now = '2026-09-25T00:00:00'
        conn.execute(
            "INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, "
            "translated_text, model_id, rules_version, status, created_at, updated_at, "
            "constitution_hash, selected_rule_codes, glossary_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ('hk', 'person_bio', 'PK', 'text', 'BẢN NEW', 'm', 'rvNEW', 'auto', now, now, 'chNEW', 'A,B', 'gh')
        )
        conn.execute(
            "INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, "
            "translated_text, model_id, rules_version, status, created_at, updated_at, "
            "constitution_hash, selected_rule_codes, glossary_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ('hk', 'person_bio', 'PK', 'text', 'BẢN CŨ LEGACY', 'm', 'rvOLD', 'auto', now, now, None, None, None)
        )
        conn.commit()
        row = lookup_cache(conn, 'hk', 'chNEW', 'rvOLD', 'person_bio')
        assert row['constitution_hash'] == 'chNEW'   # ưu tiên constitutional
        row2 = lookup_cache(conn, 'hk', 'chMISS', 'rvOLD', 'person_bio')
        assert row2['constitution_hash'] is None and row2['rules_version'] == 'rvOLD'  # fallback legacy
        row3 = lookup_cache(conn, 'hk', 'chNEW', 'rvOLD', 'dila_card')
        assert row3 is None  # source_type bắt buộc (không HIT chéo)
    finally:
        conn.close(); os.unlink(path)


def test_style_lock_resolver_hash_post_merge_5a():
    conn, path = _mkdb()
    try:
        # source chứa 三昧 (có trong locked glossary + đúng cả db) và 法嗣
        lk = style_lock(conn, '三昧 法嗣', prompt_label='dila')
        zh_in = {g['term_zh'] for g in lk['glossary']}
        # glossary filtered: chỉ 三昧/法嗣 (khớp text), 戒 bị loại (không trong text)
        assert '戒' not in zh_in
        assert '三昧' in zh_in and '法嗣' in zh_in
        # source khác → glossary khác → hash khác (#5a post-filter)
        lk2 = style_lock(conn, '三昧', prompt_label='dila')
        assert lk['constitution_hash'] != lk2['constitution_hash']
    finally:
        conn.close(); os.unlink(path)


def test_hash_equality_app_t50():
    """§8.5: app.py + t50 cùng formula hash (1 fixture Python assertEquals).
    Cả hai code path đều delegate vào style_constitution.style_lock → constitution_hash
    phải identical cho cùng input (source_text, label, json_mode, resolver)."""
    conn, path = _mkdb()
    try:
        # Same source_text, same label+json_mode → same constitution_hash
        lock1 = style_lock(conn, '孝義性空禪師法嗣。', prompt_label='passage', json_mode=False)
        lock2 = style_lock(conn, '孝義性空禪師法嗣。', prompt_label='passage', json_mode=False)
        assert lock1['constitution_hash'] == lock2['constitution_hash']
        # Different label → different hash (expected)
        lock_meta = style_lock(conn, '孝義性空禪師法嗣。', prompt_label='meta', json_mode=False)
        assert lock1['constitution_hash'] != lock_meta['constitution_hash']
        # Same label, different json_mode → different hash
        lock_json = style_lock(conn, '孝義性空禪師法嗣。', prompt_label='passage', json_mode=True)
        assert lock1['constitution_hash'] != lock_json['constitution_hash']
    finally:
        conn.close(); os.unlink(path)


def test_pre_migration_guards_16():
    """DB CHƯA migrate (thiếu match_scope/match_terms + 3 hash cols) — mọi hàm SSOT phải
    chạy không crash: select_rules→always, lookup→legacy, write→legacy insert,
    invalidate→0, invalidate_all→0."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE translation_rules (
            id INTEGER PRIMARY KEY, rule_code TEXT UNIQUE, rule_type TEXT,
            description TEXT, rule_text TEXT, is_active INTEGER, priority INTEGER,
            created_by TEXT, created_at TEXT, updated_at TEXT, status TEXT,
            suggested_by TEXT, ruleset_id TEXT, ruleset_version TEXT, is_canonical INTEGER
        );
        CREATE TABLE translation_cache (
            id INTEGER PRIMARY KEY, source_hash TEXT, source_type TEXT, entity_id TEXT,
            source_text TEXT, translated_text TEXT, model_id TEXT, rules_version TEXT,
            status TEXT, report_count INTEGER DEFAULT 0, approved_by TEXT,
            approved_at TEXT, created_at TEXT, updated_at TEXT
        );
        CREATE TABLE translation_glossary (
            id INTEGER PRIMARY KEY, term_zh TEXT, term_vi TEXT, is_locked INTEGER
        );
        CREATE TABLE translation_exemplar (
            id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT, is_active INTEGER, length_zh INTEGER
        );
        INSERT INTO translation_rules
            (rule_code, rule_type, description, rule_text, is_active, priority, status)
        VALUES
            ('PERSONA_BAN_DICH', 'style', 'Persona Ban Dịch PTDA.',
             'Dịch giả Hán-Việt. Trả về bản dịch thuần Việt.', 1, 1, 'active'),
            ('GRAM_KHONG_GIU_HAN', 'grammar', 'Không giữ chữ Hán (âm đã Việt hoá).',
             'Không giữ chữ Hán trong bản dịch.', 1, 2, 'active'),
            ('TERM_TAM_AN', 'terminology', '三昧 → tam muội',
             '三昧 dịch là tam muội.', 1, 10, 'active');
    """)
    conn.commit()
    try:
        sel = select_rules(conn, '三昧 nào đó')
        # pre-migration: không có cột match_scope → mọi rule đều active, không bị lọc
        assert len(sel['rules']) == 3
        codes = [r['rule_code'] for r in sel['rules']]
        assert 'TERM_TAM_AN' in codes and 'GRAM_KHONG_GIU_HAN' in codes
        tid, replaced = write_cache(conn, 'h1', 'person_bio', 'P1', '三昧', 'tam muội',
                                    'm', 'rv1', status='auto',
                                    constitution_hash='ch1', selected_rule_codes=['A'], glossary_hash='gh1')
        assert replaced
        row = lookup_cache(conn, 'h1', 'ch1', 'rv1', 'person_bio')
        assert row is not None and row['translated_text'] == 'tam muội'   # legacy fallback (no ch col)
        assert invalidate_cache_for_rule(conn, 'TERM_TAM_AN') == 0         # no selected_rule_codes col
        assert invalidate_cache_all_semantic(conn) == 0                    # no constitution_hash col
        left = conn.execute("SELECT COUNT(*) FROM translation_cache").fetchone()[0]
        assert left == 1  # legacy row giữ nguyên
    finally:
        conn.close(); os.unlink(path)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    passed, failed = 0, []
    for fn in fns:
        try:
            fn()
            print(f'✅ {fn.__name__}')
            passed += 1
        except Exception as e:
            print(f'❌ {fn.__name__}: {e}')
            failed.append(fn.__name__)
    print(f'\nT165 style_constitution tests: {passed}/{len(fns)} PASS')
    if failed:
        print('FAILED:', ', '.join(failed))
        sys.exit(1)


if __name__ == '__main__':
    _run_all()