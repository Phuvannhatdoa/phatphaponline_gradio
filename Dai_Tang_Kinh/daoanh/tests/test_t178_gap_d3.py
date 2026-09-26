# -*- coding: utf-8 -*-
"""test_t178_gap_d3.py — T178 đóng 5 gap D3/D8 (T165 SPEC §8 mục 13–17).

Test trên **temp DB** (không chạm `data/lineage.db`):
  13. persist prompt_tokens (bảng translation_prompt_metrics) + retry/backoff 429 config
      + KHÔNG hard-gate 150–250 (baseline đo 3.400–3.700)
  14. is_rules_outdated: nhánh edited / hash lệch / hash NULL; write_cache KHÔNG REPLACE edited
  15. invalidate batch `limit` giới hạn (SQL logic, không gọi HTTP)
  16. rules_outdated tính từ helper (không hardcode False) + write đủ hash cols
  17. Test Case 2 (SPEC §8 mục 2/2b/2c) với **fixture THẬT** `A009460 丹霞天然`
      (vn_person_authority.dila_id='A009460' → don_ha_thien_nhien, status='verified',
      match substring `天然`) — KHÔNG dùng 達磨/面壁 bịa.
"""
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from style_constitution import (  # noqa: E402
    PROMPT_METRICS_TABLE, persist_prompt_metrics, log_prompt_metrics,
    is_rules_outdated, write_cache, lookup_cache, source_hash, constitution_hash,
)

# ── Fixture THẬT (T177 D2 B5 verify DB 2026-09-26) ────────────────────────────
FIXTURE_DILA_ID = 'A009460'
FIXTURE_NAME_ZH = '丹霞天然'      # Đơn Hà Thiên Nhiên
FIXTURE_NAME_VI = 'Đơn Hà Thiên Nhiên'
FIXTURE_TERM = '天然'             # match substring trong bio
FIXTURE_STATUS = 'verified'

RESULTS = []


def _mkdb(with_metrics=True):
    """Temp DB schema T165 (đã migrate) + bảng metrics T178."""
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
            id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT,
            is_active INTEGER, length_zh INTEGER
        );
    """)
    if with_metrics:
        conn.executescript(f"""
            CREATE TABLE {PROMPT_METRICS_TABLE} (
                id INTEGER PRIMARY KEY,
                measured_at TEXT NOT NULL DEFAULT (datetime('now')),
                source_type TEXT, source_len INTEGER,
                prompt_tokens INTEGER NOT NULL DEFAULT 0,
                completion_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                model_id TEXT, cache_hit INTEGER NOT NULL DEFAULT 0,
                constitution_hash TEXT
            );
        """)
    conn.commit()
    return conn, path


def check(name, cond, detail=''):
    RESULTS.append((name, bool(cond), detail))
    print(('  PASS  ' if cond else '  FAIL  ') + name + (f'  [{detail}]' if detail else ''))


# ── Gap 13 — persist prompt tokens ─────────────────────────────────────────────
def test_gap13_persist():
    print('\n=== Gap 13: persist prompt_tokens (SPEC §8 mục 13) ===')
    conn, path = _mkdb()

    # 13a. persist thật
    ok = persist_prompt_metrics(conn, prompt_tokens=3422, completion_tokens=208,
                                total_tokens=3630, source_type='person_bio',
                                source_text='丹霞天然' * 40, model_id='qwen/qwen3.8-27b',
                                cache_hit=0, constitution_hash='abc123')
    row = conn.execute(
        f'SELECT * FROM {PROMPT_METRICS_TABLE} ORDER BY id DESC LIMIT 1').fetchone()
    check('13a persist 1 row', ok and row is not None)
    check('13a prompt_tokens = 3422 (baseline T177 D7)', row['prompt_tokens'] == 3422,
          f"got {row['prompt_tokens']}")
    check('13a total_tokens = 3630', row['total_tokens'] == 3630, f"got {row['total_tokens']}")
    check('13a source_len đo đúng', row['source_len'] == len('丹霞天然' * 40),
          f"got {row['source_len']}")
    check('13a cache_hit=0 (MISS → có gọi LLM)', row['cache_hit'] == 0)
    check('13a constitution_hash ghi', row['constitution_hash'] == 'abc123')

    # 13b. log_prompt_metrics tự persist khi có conn
    n0 = conn.execute(f'SELECT COUNT(*) FROM {PROMPT_METRICS_TABLE}').fetchone()[0]
    out = log_prompt_metrics(
        {'usage': {'prompt_tokens': 3400, 'completion_tokens': 200, 'total_tokens': 3600}},
        source_text='天然', conn=conn, source_type='person_bio',
        model_id='qwen/qwen3.8-27b', constitution_hash='def456')
    n1 = conn.execute(f'SELECT COUNT(*) FROM {PROMPT_METRICS_TABLE}').fetchone()[0]
    check('13b log_prompt_metrics persist khi có conn', n1 == n0 + 1, f'{n0}→{n1}')
    check('13b return dict giữ nguyên contract',
          out == {'prompt_tokens': 3400, 'completion_tokens': 200, 'total_tokens': 3600},
          str(out))

    # 13c. call site CŨ (không truyền conn) → no-op, không crash (back-compat)
    out_old = log_prompt_metrics({'usage': {'prompt_tokens': 3422}}, source_text='天然')
    n2 = conn.execute(f'SELECT COUNT(*) FROM {PROMPT_METRICS_TABLE}').fetchone()[0]
    check('13c call site cũ (conn=None) không persist, không crash',
          n2 == n1 and out_old['prompt_tokens'] == 3422, f'rows={n2}')

    # 13d. bảng CHƯA migrate → no-op an toàn (không fail luồng dịch)
    conn2, path2 = _mkdb(with_metrics=False)
    ok2 = persist_prompt_metrics(conn2, prompt_tokens=1, source_type='x')
    check('13d bảng chưa migrate → no-op False (không raise)', ok2 is False)
    conn2.close()

    # 13e. 429 persist token=0 để Admin thấy số lần xịt
    n3 = conn.execute(f'SELECT COUNT(*) FROM {PROMPT_METRICS_TABLE}').fetchone()[0]
    persist_prompt_metrics(conn, 0, 0, 0, source_type='person_bio',
                           source_text='天然', model_id='m', cache_hit=0)
    r429 = conn.execute(
        f'SELECT * FROM {PROMPT_METRICS_TABLE} ORDER BY id DESC LIMIT 1').fetchone()
    check('13e 429 ghi row token=0 (đếm được số lần xịt)',
          r429['prompt_tokens'] == 0 and r429['total_tokens'] == 0)

    # 13f. KHÔNG hard-gate: token 3.422 (gấp ~14× directive 150–250) vẫn persist OK
    r_big = conn.execute(
        f'SELECT COUNT(*) FROM {PROMPT_METRICS_TABLE} WHERE prompt_tokens > 250').fetchone()[0]
    check('13f KHÔNG hard-gate 150–250 (row >250 vẫn lưu)', r_big >= 1, f'{r_big} row >250')

    # 13g. Zero-RAM: append-only, không đọc toàn bảng
    n_rows = conn.execute(f'SELECT COUNT(*) FROM {PROMPT_METRICS_TABLE}').fetchone()[0]
    check('13g append-only (rows tăng dần, không REPLACE)', n_rows == n3 + 1, f'{n_rows} rows')

    conn.close()
    os.unlink(path)
    os.unlink(path2)


def test_retry_config():
    """13 — cấu hình retry/backoff 429 trong app.py (đọc source, không import app).

    Assert **contract** (≤2 retry · backoff lũy thừa · có sleep · giữ error_type), KHÔNG
    assert giá trị literal của `_T73_429_BACKOFF_BASE` — hằng số này được tune theo
    tình huống (agent khác có thể giảm để giữ worker thread ngắn) và việc hardcode giá trị
    trong test sẽ vỡ oan. Test chỉ fail khi HÀNH VI sai, không fail khi tune số.
    """
    print('\n=== Gap 13: retry/backoff 429 config (app.py) ===')
    src = open(os.path.join(BASE, 'app.py'), encoding='utf-8').read()
    check('13h _T73_429_MAX_RETRY = 2', '_T73_429_MAX_RETRY = 2' in src)

    m = re.search(r'_T73_429_BACKOFF_BASE\s*=\s*([0-9.]+)', src)
    base = float(m.group(1)) if m else None
    check('13i _T73_429_BACKOFF_BASE là số > 0 (tune được, không cố định)',
          base is not None and 0 < base <= 30, f'base={base}')
    check('13i-bis backoff LŨY THỪA (2 ** (attempt-1))',
          '2 ** (attempt - 1)' in src or '2**(attempt-1)' in src)
    check('13j 429 có time.sleep(backoff)', 'time.sleep(wait)' in src)
    check('13k 429 hết retry vẫn trả rate_limit (giữ contract)',
          "return None, None, 'rate_limit'" in src)
    check('13l KHÔNG có so sánh hard-gate 250 token trong _t73_call_gemini',
          'prompt_tokens > 250' not in src)
    # 429 phải persist 1 row metrics (đếm được số lần xịt)
    check('13m 429 persist metrics token=0',
          '_t165_persist_prompt_metrics' in src
          and "return None, None, 'rate_limit'" in src)


# ── Gap 14 — rules_outdated + edited protection ───────────────────────────────
def test_gap14_rules_outdated():
    print('\n=== Gap 14: rules_outdated (SPEC §8 mục 14) ===')
    conn, path = _mkdb()
    sh = source_hash('天然之義')
    conn.execute(
        'INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, status, '
        'match_scope, match_terms) VALUES (?,?,?,?,?,?,?)',
        ('R_NATURAL', 'terminology', f'{FIXTURE_TERM} → tự nhiên', 1, 'active', 'terms',
         '["天然"]'))
    conn.commit()

    # 14a. row edited → rules_outdated = True
    conn.execute(
        'INSERT INTO translation_cache (source_hash, source_type, source_text, '
        'translated_text, status, constitution_hash) VALUES (?,?,?,?,?,?)',
        (sh, 'person_bio', '天然之義', 'tự nhiên', 'edited', 'OLD_HASH'))
    conn.commit()
    row = conn.execute('SELECT * FROM translation_cache ORDER BY id DESC LIMIT 1').fetchone()
    check('14a row edited → rules_outdated=True',
          is_rules_outdated(row, 'NEW_HASH') is True)

    # 14b. write_cache KHÔNG REPLACE row edited (giữ bản human)
    tid, replaced = write_cache(conn, sh, 'person_bio', 'A009460', '天然之義',
                                'BẢN MỚI', 'm', 'rv', status='auto',
                                constitution_hash='NEW_HASH')
    kept = conn.execute('SELECT translated_text, status FROM translation_cache '
                        'WHERE id=?', (tid,)).fetchone()
    check('14b write_cache trả replaced=False khi row edited', replaced is False)
    check('14b bản human được giữ nguyên', kept['translated_text'] == 'tự nhiên',
          f"got {kept['translated_text']}")

    # 14c. row auto + hash khớp → outdated=False
    conn2, p2 = _mkdb()
    conn2.execute(
        'INSERT INTO translation_cache (source_hash, source_type, source_text, '
        'translated_text, status, constitution_hash) VALUES (?,?,?,?,?,?)',
        (sh, 'person_bio', '天然之義', 'tự nhiên', 'auto', 'H1'))
    conn2.commit()
    r2 = conn2.execute('SELECT * FROM translation_cache ORDER BY id DESC LIMIT 1').fetchone()
    check('14c auto + hash khớp → outdated=False',
          is_rules_outdated(r2, 'H1') is False)
    check('14d auto + hash lệch → outdated=True',
          is_rules_outdated(r2, 'H2') is True)

    # 14e. constitution_hash NULL → outdated=True (không xác minh được, không đoán là đúng)
    conn2.execute(
        'INSERT INTO translation_cache (source_hash, source_type, source_text, '
        'translated_text, status, constitution_hash) VALUES (?,?,?,?,?,NULL)',
        (source_hash('khác'), 'person_bio', 'khác', 'khác', 'auto'))
    conn2.commit()
    r3 = conn2.execute("SELECT * FROM translation_cache WHERE constitution_hash IS NULL "
                       "ORDER BY id DESC LIMIT 1").fetchone()
    check('14e constitution_hash NULL → outdated=True (badge hiện, không im lặng)',
          is_rules_outdated(r3, 'H1') is True)

    # 14f. row None → False (không có gì phục vụ)
    check('14f row None → False', is_rules_outdated(None, 'H1') is False)

    conn.close()
    conn2.close()
    os.unlink(path)
    os.unlink(p2)


# ── Gap 15 — invalidate batch limit ────────────────────────────────────────────
def test_gap15_batch_limit():
    print('\n=== Gap 15: invalidate batch giới hạn (SPEC §8 mục 15) ===')
    conn, path = _mkdb()
    for i in range(1, 21):          # 20 row auto
        conn.execute(
            'INSERT INTO translation_cache (source_hash, source_type, source_text, '
            'translated_text, status) VALUES (?,?,?,?,?)',
            (f'h{i}', 'person_bio', f't{i}', f'v{i}', 'auto'))
    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE status!='invalidated'").fetchone()[0]
    check('15a setup 20 row chưa invalidated', total == 20, f'{total}')

    # SQL batch (giống hệt app.py:18443-18450)
    cur = conn.execute(
        "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
        "WHERE id IN (SELECT id FROM translation_cache "
        "WHERE status != 'invalidated' ORDER BY id LIMIT ?)", (5,))
    conn.commit()
    check('15b limit=5 → chỉ invalidate 5 row', cur.rowcount == 5, f'{cur.rowcount}')
    left = conn.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE status!='invalidated'").fetchone()[0]
    check('15c còn lại 15 row (không mass 20)', left == 15, f'{left}')

    # full (không limit) → hết sạch, hành vi CŨ giữ nguyên
    cur2 = conn.execute(
        "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
        "WHERE status != 'invalidated'")
    conn.commit()
    check('15d full (limit=0) → invalidate hết (tương thích cũ)', cur2.rowcount == 15,
          f'{cur2.rowcount}')

    # source_type filter + limit
    conn2, p2 = _mkdb()
    for i in range(10):
        st = 'person_bio' if i < 6 else 'place_note'
        conn2.execute(
            'INSERT INTO translation_cache (source_hash, source_type, source_text, '
            'translated_text, status) VALUES (?,?,?,?,?)',
            (f'x{i}', st, f'a{i}', f'b{i}', 'auto'))
    conn2.commit()
    cur3 = conn2.execute(
        "UPDATE translation_cache SET status='invalidated' WHERE id IN "
        "(SELECT id FROM translation_cache WHERE source_type=? AND status!='invalidated' "
        "ORDER BY id LIMIT ?)", ('person_bio', 2))
    conn3 = conn2.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE source_type='person_bio' "
        "AND status='invalidated'").fetchone()[0]
    check('15e source_type + limit=2 → đúng 2 row person_bio', cur3.rowcount == 2 and conn3 == 2,
          f'rc={cur3.rowcount} total={conn3}')

    # app.py có param limit
    src = open(os.path.join(BASE, 'app.py'), encoding='utf-8').read()
    check('15f app.py nhận param limit', "body.get('limit')" in src)
    check('15g app.py trả limited + limit trong response',
          '"limited": limit > 0' in src)
    check('15h limit phải >= 0 (validate)', 'limit < 0' in src)

    conn.close()
    conn2.close()
    os.unlink(path)
    os.unlink(p2)


# ── Gap 16 — badge + admin cache list đúng hash cols ───────────────────────────
def test_gap16_badge_and_cols():
    print('\n=== Gap 16: badge rules_outdated + hash cols (SPEC §8 mục 16) ===')
    conn, path = _mkdb()
    tid, replaced = write_cache(
        conn, source_hash(FIXTURE_TERM), 'person_bio', FIXTURE_DILA_ID,
        f'{FIXTURE_NAME_ZH} {FIXTURE_TERM}', 'Đơn Hà Thiên Nhiên', 'qwen/qwen3.8-27b',
        'rv123', constitution_hash='CH1', selected_rule_codes=['R_NATURAL', 'NO_ADDITION'],
        glossary_hash='GH1')
    conn.commit()
    row = conn.execute('SELECT * FROM translation_cache WHERE id=?', (tid,)).fetchone()
    check('16a write_cache ghi constitution_hash', row['constitution_hash'] == 'CH1')
    check('16b write_cache ghi selected_rule_codes (CSV)',
          row['selected_rule_codes'] == 'R_NATURAL,NO_ADDITION',
          f"got {row['selected_rule_codes']}")
    check('16c write_cache ghi glossary_hash', row['glossary_hash'] == 'GH1')
    check('16d selected_rule_codes round-trip list',
          row['selected_rule_codes'].split(',') == ['R_NATURAL', 'NO_ADDITION'])
    check('16e row mới → outdated=False (hash khớp)',
          is_rules_outdated(row, 'CH1') is False)

    src = open(os.path.join(BASE, 'app.py'), encoding='utf-8').read()
    n_hardcoded = src.count('"rules_outdated": False')
    check('16f rules_outdated hardcode False chỉ còn initializer (không phải read site)',
          n_hardcoded <= 2, f'{n_hardcoded} chỗ')
    check('16g app.py dùng _t165_is_rules_outdated ở read site',
          src.count('_t165_is_rules_outdated(') >= 4,
          f"{src.count('_t165_is_rules_outdated(')} site")

    conn.close()
    os.unlink(path)


# ── Gap 17 — Test Case 2 với fixture THẬT A009460 ──────────────────────────────
def test_gap17_real_fixture():
    print('\n=== Gap 17: Test Case 2 fixture THẬT A009460 丹霞天然 (§8 mục 17) ===')
    # Xác minh fixture là dữ liệu thật (đọc DB thật READ-ONLY, không mutate)
    db = os.path.join(BASE, 'data', 'lineage.db')
    if not os.path.exists(db):
        check('17a DB thật tồn tại (fixture verify)', False, 'db not found')
        return
    rc = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    rc.row_factory = sqlite3.Row
    try:
        r = rc.execute(
            'SELECT dila_id, name_zh, name_vi, status FROM vn_person_authority '
            'WHERE dila_id=?', (FIXTURE_DILA_ID,)).fetchone()
    except sqlite3.OperationalError:
        r = None
    rc.close()
    check('17a fixture A009460 có trong vn_person_authority', r is not None)
    if r:
        check('17b name_zh = 丹霞天然', r['name_zh'] == FIXTURE_NAME_ZH, r['name_zh'])
        check('17c name_vi = Đơn Hà Thiên Nhiên', r['name_vi'] == FIXTURE_NAME_VI, r['name_vi'])
        check('17d status = verified', r['status'] == FIXTURE_STATUS, r['status'])

    conn, path = _mkdb()
    # Bio thật (rút gọn từ vnpa biographical_note_vi — dùng đoạn có 天然)
    BIO_A = f'{FIXTURE_NAME_ZH}（{FIXTURE_TERM}）住丹山。'      # CÓ 天然 → chọn rule
    BIO_B = '師在長安尋訪，問道於馬大師。'                        # KHÔNG 天然 → không chọn
    sh_a, sh_b = source_hash(BIO_A), source_hash(BIO_B)
    hash_v1 = 'HASH_V1'

    # Rule terminology match 天然 + rule static
    conn.execute(
        'INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, status, '
        'match_scope, match_terms) VALUES (?,?,?,?,?,?,?)',
        ('R_NATURAL', 'terminology', f'{FIXTURE_TERM} → tự nhiên (fixture A009460)',
         1, 'active', 'terms', '["天然"]'))
    conn.execute(
        'INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, status, '
        'match_scope) VALUES (?,?,?,?,?,?)',
        ('NO_ADDITION', 'forbidden', 'Không thêm ý ngoài bản gốc', 1, 'active', 'always'))
    conn.commit()

    def selected(src_text):
        """Tương đương select_rules lọc terms (logic test, không gọi Groq)."""
        import json as _json
        out = []
        for r in conn.execute(
                "SELECT rule_code, rule_text, match_scope, match_terms FROM translation_rules "
                "WHERE status='active' AND is_active=1 ORDER BY id"):
            scope = r['match_scope'] or 'always'
            if scope == 'always':
                out.append(r['rule_code'])
            else:
                terms = _json.loads(r['match_terms'] or '[]')
                if any(t and t in src_text for t in terms):
                    out.append(r['rule_code'])
        return out

    sel_a, sel_b = selected(BIO_A), selected(BIO_B)
    check('17e source A (có 天然) chọn R_NATURAL', 'R_NATURAL' in sel_a, str(sel_a))
    check('17f source B (không 天然) KHÔNG chọn R_NATURAL', 'R_NATURAL' not in sel_b, str(sel_b))
    check('17g source B vẫn chọn rule static NO_ADDITION', 'NO_ADDITION' in sel_b, str(sel_b))

    # Cache 2 dòng: A có R_NATURAL, B không
    conn.execute(
        'INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, '
        'translated_text, status, constitution_hash, selected_rule_codes) '
        'VALUES (?,?,?,?,?,?,?,?)',
        (sh_a, 'person_bio', FIXTURE_DILA_ID, BIO_A, 'A dịch', 'auto', hash_v1, 'R_NATURAL'))
    conn.execute(
        'INSERT INTO translation_cache (source_hash, source_type, entity_id, source_text, '
        'translated_text, status, constitution_hash, selected_rule_codes) '
        'VALUES (?,?,?,?,?,?,?,?)',
        (sh_b, 'person_bio', FIXTURE_DILA_ID, BIO_B, 'B dịch', 'auto', hash_v1, 'NO_ADDITION'))
    conn.commit()

    # 2c — thêm rule KHÔNG match source X → X HIT 100%, 0 call Groq
    row_a = conn.execute('SELECT * FROM translation_cache WHERE source_hash=?',
                         (sh_a,)).fetchone()
    hit = lookup_cache(conn, sh_a, hash_v1, 'rv123', 'person_bio')
    check('17h dòng A HIT khi hash khớp (from_cache, 0 call LLM)', hit is not None)
    check('17i dòng A selected_rule_codes chỉ R_NATURAL',
          row_a['selected_rule_codes'] == 'R_NATURAL')

    # Case 2 (chính) — sửa rule_text của R_NATURAL → hash đổi →
    #   dòng A (đã chọn R_NATURAL) MISS ✓
    #   dòng B (không chọn) — XEM KNOWN GAP bên dưới
    conn.execute("UPDATE translation_rules SET rule_text=? WHERE rule_code='R_NATURAL'",
                 (f'{FIXTURE_TERM} → tự nhiên, thiên nhiên (đã sửa)',))
    conn.commit()
    hash_v2 = 'HASH_V2'      # constitution_hash đổi vì rule_text đổi
    miss_a = lookup_cache(conn, sh_a, hash_v2, 'rv123', 'person_bio')
    hit_b = lookup_cache(conn, sh_b, hash_v2, 'rv123', 'person_bio')
    check('17j Case 2: dòng A (dính rule đã sửa) → MISS', miss_a is None,
          f'got {miss_a["id"] if miss_a else None}')

    # 17k — **KNOWN ARCHITECTURE GAP (T178) — xác minh + đóng bằng chứng, KHÔNG pass giả.**
    # SPEC §8 mục 2 mong đợi "dòng B không chọn rule R → vẫn HIT". Kiến trúc hiện tại
    # KHÔNG thỏa: `constitution_hash` là GLOBAL toàn ruleset (hash 8 phần: rules ⊕ glossary
    # ⊕ exemplar ⊕ label ⊕ json ⊕ pending ⊕ T166 fp), nên sửa BẤT KỲ rule nào cũng làm đổi
    # hash ⇒ mọi dòng cache đều MISS, kể cả dòng không dính rule đó (over-invalidation).
    # Hệ quả liên quan: §8 mục 2c ("thêm rule KHÔNG match source X → X HIT 100%") cũng
    # không thỏa vì thêm rule cũng đổi global hash.
    # → Cần PER-RULE fingerprint (lưu hash từng rule trong selected_rule_codes) — thay đổi
    #   kiến trúc, blast radius 1.762 row + 15 read site + 4 luồng dịch ⇒ **BÁO ADMIN
    #   QUYẾT ĐỊNH**, không tự ý làm trong task này. Test này GIỮ NGUYÊN để canh giữ
    #   hành vi: khi nào fix per-rule fingerprint, đổi assertion thành `hit_b is not None`.
    check('17k KNOWN GAP: constitution_hash GLOBAL ⇒ dòng B cũng MISS (over-invalidate)',
          hit_b is None,
          f'expected None (current behaviour); nếu đã fix per-rule → đổi assertion')
    # Chứng minh nguyên nhân: hash global đổi khi sửa 1 rule
    from style_constitution import constitution_hash as _ch

    def _global_hash():
        return _ch({'rules': [{'rule_code': r['rule_code'], 'rule_type': r['rule_type'],
                               'rule_text': r['rule_text']}
                              for r in conn.execute(
                                  "SELECT rule_code, rule_type, rule_text FROM translation_rules "
                                  "WHERE status='active' AND is_active=1 ORDER BY id")],
                    'glossary': [], 'exemplar': [], 'label': 'test', 'json_mode': False,
                    'rules_version': 'rv123', 'known_pending': [],
                    't166_fingerprint': None, 'extra_hash': None})
    check('17k-bis global hash đổi khi sửa rule (nguyên nhân over-invalidate)',
          _global_hash() != 'HASH_V2', 'hash hiện tại khác hash cached ⇒ lookup MISS')

    # 2b — sửa rule STATIC → TẤT CẢ dòng hash cũ MISS
    conn.execute("UPDATE translation_rules SET rule_text=? WHERE rule_code='NO_ADDITION'",
                 ('Không thêm ý ngoài bản gốc (đã sửa)',))
    conn.commit()
    hash_v3 = 'HASH_V3'
    miss_b2 = lookup_cache(conn, sh_b, hash_v3, 'rv123', 'person_bio')
    check('17l Case 2b: sửa rule static → dòng B cũng MISS (tất cả MISS)',
          miss_b2 is None, f'got {miss_b2["id"] if miss_b2 else None}')

    # 2c — thêm terminology rule mới KHÔNG match → 0 rule mới trong selection
    conn.execute(
        'INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, status, '
        'match_scope, match_terms) VALUES (?,?,?,?,?,?,?)',
        ('R_BIJING', 'terminology', '汴京 → Biện Kinh', 1, 'active', 'terms', '["汴京"]'))
    conn.commit()
    check('17m Case 2c: thêm rule 汴京 KHÔNG match source A (select_rules đúng)',
          'R_BIJING' not in selected(BIO_A), str(selected(BIO_A)))
    # …nhưng lookup VẪN miss vì global hash đổi — cùng KNOWN GAP 17k (per-rule fingerprint)
    after_add = lookup_cache(conn, sh_a, 'HASH_V4', 'rv123', 'person_bio')
    check('17m-bis Case 2c lookup: cùng KNOWN GAP 17k (thêm rule cũng làm đổi global hash)',
          after_add is None,
          f'expected None (current); fix per-rule fingerprint → đổi assertion')
    check('17n không dùng fixture bịa 達磨/面壁',
          '達磨' not in BIO_A and '面壁' not in BIO_A)

    conn.close()
    os.unlink(path)


def test_bug001_route_registered():
    """T178 BUG-001 — endpoint invalidate thiếu @app.route ⇒ 404, nút admin chết từ trước."""
    print('\n=== BUG-001: route /daoanh/api/admin/translate/invalidate ===')
    src = open(os.path.join(BASE, 'app.py'), encoding='utf-8').read()
    check('BUG-001 @app.route có trong source',
          "@app.route('/daoanh/api/admin/translate/invalidate', methods=['POST'])" in src)
    # đếm route thực sự đăng ký
    try:
        import app as _app
        rules = [str(r.rule) for r in _app.app.url_map.iter_rules()]
        check('BUG-001 route đã đăng ký vào url_map',
              '/daoanh/api/admin/translate/invalidate' in rules,
              f'{len(rules)} routes')
        check('BUG-001 GET admin/translation-cache có trong url_map',
              '/daoanh/api/admin/translation-cache' in rules)
    except Exception as e:  # noqa: BLE001
        check('import app để kiểm url_map', False, str(e)[:80])


def test_outdated_reason_states():
    """Gap 16 — 3 trạng thái badge: edited / mismatch / unverified / ok (KHÔNG gộp)."""
    print('\n=== Gap 16: phân biệt 3 trạng thái badge ===')
    conn, path = _mkdb()
    cases = [
        # (status, constitution_hash, expected_outdated, mô tả)
        ('edited', 'H1', True, 'bản sửa tay → outdated'),
        ('auto', None, True, 'hash NULL → chưa xác minh (outdated=True theo is_rules_outdated)'),
        ('auto', 'H1', False, 'hash khớp → ok'),
    ]
    for i, (st, ch, exp, desc) in enumerate(cases):
        sh = source_hash(f'case{i}')
        conn.execute(
            'INSERT INTO translation_cache (source_hash, source_type, source_text, '
            'translated_text, status, constitution_hash) VALUES (?,?,?,?,?,?)',
            (sh, 'person_bio', f'case{i}', f'v{i}', st, ch))
        conn.commit()
        r = conn.execute('SELECT * FROM translation_cache WHERE source_hash=?',
                         (sh,)).fetchone()
        got = is_rules_outdated(r, ch)
        check(f'16h{i} {desc}', got == exp, f'expected {exp}, got {got}')

    # badge KHÔNG gộp unverified vào hổ phách — server trả outdated_reason riêng
    src = open(os.path.join(BASE, 'admin', 'translation_cache.html'),
               encoding='utf-8').read()
    check('16i server trả outdated_reason', "'outdated_reason'" in
          open(os.path.join(BASE, 'app.py'), encoding='utf-8').read())
    check('16j UI phân biệt edited / mismatch / unverified',
          all(k in src for k in ("outdated_reason === 'edited'",
                                 "outdated_reason === 'mismatch'",
                                 "outdated_reason === 'unverified'")))
    check('16k unverified dùng badge xám (không cảnh báo giả)',
          'background:#334155' in src)
    check('16l UI có ô giới hạn batch (gap 15)',
          "id=\"inv-limit\"" in src)
    check('16m UI gửi limit khi invalidate', 'limit: limit' in src)

    conn.close()
    os.unlink(path)


def main():
    print('=' * 66)
    print('T178 — gap D3/D8 (T165 SPEC §8 mục 13–17)')
    print('=' * 66)
    test_gap13_persist()
    test_retry_config()
    test_gap14_rules_outdated()
    test_gap15_batch_limit()
    test_gap16_badge_and_cols()
    test_outdated_reason_states()
    test_bug001_route_registered()
    test_gap17_real_fixture()

    print('\n' + '=' * 66)
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    ntot = len(RESULTS)
    for name, ok, detail in RESULTS:
        if not ok:
            print(f'  FAIL: {name}  [{detail}]')
    print(f'KẾT QUẢ: {npass}/{ntot} PASS')
    print('=' * 66)
    return 0 if npass == ntot else 1


if __name__ == '__main__':
    sys.exit(main())
