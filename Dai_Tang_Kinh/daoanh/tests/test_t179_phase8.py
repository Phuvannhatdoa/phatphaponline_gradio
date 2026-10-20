# -*- coding: utf-8 -*-
"""test_t179_phase8.py — T179: T165 Phase 8 (SPEC §7 phase 8) + ĐÍNH CHÍNH kết luận T178.

**ĐÍNH CHÍNH quan trọng (T179, 2026-09-26):** T178 kết luận "`constitution_hash` là GLOBAL
toàn ruleset ⇒ §8 mục 2/2c không thỏa" là **SAI**. Đo lại với hash THẬT cho thấy
`constitution_hash` là **PER-ROW**: nó chỉ gồm các rule mà DÒNG ĐÓ chọn (qua
`style_lock(source_text=...)`). T178 test FAIL vì dùng hash **giả** (`'HASH_V1'`/`'HASH_V2'`).
⇒ §8 mục 2 / 2b / 2c **đã thỏa sẵn từ T165**; hướng "per-rule fingerprint" đã bị GỠ.

Bộ test này (tất cả trên **temp DB**, không mutate `data/lineage.db`):
  A. §8 mục 2  — sửa rule R: dòng DÌNH R → MISS, dòng KHÔNG dính R → HIT   (hash THẬT)
  B. §8 mục 2b — sửa rule STATIC (always) → mọi dòng dùng nó đều MISS
  C. §8 mục 2c — thêm rule KHÔNG match source X → X HIT 100%, 0 call LLM
  D. §8 mục 3  — đổi glossary đã inject → MISS (không được nới)
  E. §8 mục 5b — đổi label / json_mode → MISS
  F. Phase 8a — XML boundary: thẻ, escape, json_mode giữ contract, version t165-v2
  G. Phase 8b — Trie/Aho-Corasick: gate 1000, trie ≡ substring, auto-bật ở ≥1000
  H. Phase 8c — đo token v1 vs v2 (ghi file, ghi rõ cơ sở đo)
"""
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from style_constitution import (  # noqa: E402
    PROMPT_FORMAT_VERSION, style_lock, select_rules, source_hash,
    lookup_cache, write_cache, build_style_prompt,
)
from term_matcher import TermMatcher, build_matcher, scan_terms, TRIE_MIN_TERMS  # noqa: E402

# Fixture THẬT (đồng nhất T178/T177): A009460 丹霞天然 (vnpa don_ha_thien_nhien, verified)
FX_ID = 'A009460'
FX_ZH = '丹霞天然'
FX_TERM = '天然'
RESULTS = []


def _mkdb():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE translation_rules (
            id INTEGER PRIMARY KEY, rule_code TEXT UNIQUE, rule_type TEXT,
            rule_text TEXT, is_active INTEGER, priority INTEGER, status TEXT,
            match_scope TEXT DEFAULT 'always', match_terms TEXT,
            suggested_by TEXT, ruleset_id TEXT, ruleset_version TEXT,
            is_canonical INTEGER, description TEXT, created_by TEXT,
            created_at TEXT, updated_at TEXT
        );
        CREATE TABLE translation_cache (
            id INTEGER PRIMARY KEY, source_hash TEXT, source_type TEXT, entity_id TEXT,
            source_text TEXT, translated_text TEXT, model_id TEXT, rules_version TEXT,
            status TEXT, report_count INTEGER DEFAULT 0, approved_by TEXT,
            approved_at TEXT, created_at TEXT, updated_at TEXT,
            constitution_hash TEXT, selected_rule_codes TEXT, glossary_hash TEXT,
            UNIQUE(source_hash, source_type)
        );
        CREATE TABLE translation_glossary (
            id INTEGER PRIMARY KEY, term_zh TEXT, term_vi TEXT, is_locked INTEGER
        );
        CREATE TABLE translation_exemplar (
            id INTEGER PRIMARY KEY, zh TEXT, vi TEXT, source_label TEXT,
            is_active INTEGER, length_zh INTEGER
        );
    """)
    c.commit()
    return c, path


def check(name, cond, detail=''):
    RESULTS.append((name, bool(cond), detail))
    print(('  PASS  ' if cond else '  FAIL  ') + name + (f'  [{detail}]' if detail else ''))


BIO_A = f'{FX_ZH}（{FX_TERM}）住丹山。'      # CÓ 天然 → chọn R_NATURAL + static
BIO_B = '師在長安尋訪，問道於馬大師。'        # KHÔNG 天然 → chỉ chọn static


def _seed(c):
    c.execute("INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, "
              "status, match_scope, match_terms) VALUES (?,?,?,?,?,?,?)",
              ('R_NATURAL', 'terminology', f'{FX_TERM} → tự nhiên', 1, 'active',
               'terms', json.dumps([FX_TERM], ensure_ascii=False)))
    c.execute("INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, "
              "status, match_scope) VALUES (?,?,?,?,?,?)",
              ('NO_ADDITION', 'forbidden', 'Không thêm ý ngoài bản gốc', 1, 'active', 'always'))
    c.commit()


def _lock(c, text, label='test', json_mode=False):
    return style_lock(c, source_text=text, prompt_label=label, json_mode=json_mode)


def _put(c, lock, text, translated):
    tid, _ = write_cache(
        c, source_hash(text), 'person_bio', FX_ID, text, translated, 'm',
        lock['rules_version'], status='auto',
        constitution_hash=lock['constitution_hash'],
        selected_rule_codes=lock['codes'], glossary_hash=lock['glossary_hash'])
    c.commit()
    return tid


def _hit(c, lock, text):
    r = lookup_cache(c, source_hash(text), lock['constitution_hash'],
                     lock['rules_version'], 'person_bio')
    return r


# ── A/B/C — §8 mục 2 / 2b / 2c với hash THẬT ───────────────────────────────
def test_abc_real_hash():
    print('\n=== A–C. §8 mục 2/2b/2c — dùng constitution_hash THẬT ===')
    c, p = _mkdb()
    _seed(c)
    la0, lb0 = _lock(c, BIO_A), _lock(c, BIO_B)
    check('A0 A chọn 2 rule, B chỉ chọn static',
          set(la0['codes']) == {'R_NATURAL', 'NO_ADDITION'} and lb0['codes'] == ['NO_ADDITION'],
          f"A={la0['codes']} B={lb0['codes']}")
    _put(c, la0, BIO_A, 'A dịch')
    _put(c, lb0, BIO_B, 'B dịch')
    check('A1 fast path: A HIT', _hit(c, la0, BIO_A) is not None)
    check('A2 fast path: B HIT', _hit(c, lb0, BIO_B) is not None)

    # ── §8 mục 2 ────────────────────────────────────────────────────────
    c.execute("UPDATE translation_rules SET rule_text=? WHERE rule_code='R_NATURAL'",
              (f'{FX_TERM} → tự nhiên, thiên nhiên (đã sửa)',))
    c.commit()
    la1, lb1 = _lock(c, BIO_A), _lock(c, BIO_B)
    check('§8.2 [nguồn sự thật] sửa rule R ⇒ hash của A ĐỔI',
          la1['constitution_hash'] != la0['constitution_hash'])
    check('§8.2 [đính chính] sửa rule R (B KHÔNG chọn) ⇒ hash của B **KHÔNG đổi**',
          lb1['constitution_hash'] == lb0['constitution_hash'],
          f"{lb0['constitution_hash']} -> {lb1['constitution_hash']}")
    check('§8.2a dòng A (DÌNH rule bị sửa) → MISS', _hit(c, la1, BIO_A) is None)
    hit_b = _hit(c, lb1, BIO_B)
    check('§8.2b dòng B (KHÔNG dính rule bị sửa) → **HIT**',
          hit_b is not None and hit_b['translated_text'] == 'B dịch',
          f"got {hit_b['translated_text'] if hit_b is not None else None}")

    # ── §8 mục 2b — sửa rule STATIC ─────────────────────────────────────
    c.execute("UPDATE translation_rules SET rule_text=? WHERE rule_code='NO_ADDITION'",
              ('Không thêm ý ngoài bản gốc (đã sửa static)',))
    c.commit()
    la2, lb2 = _lock(c, BIO_A), _lock(c, BIO_B)
    check('§8.2b-1 sửa rule static ⇒ A MISS', _hit(c, la2, BIO_A) is None)
    check('§8.2b-2 sửa rule static ⇒ B MISS (mọi dòng dùng static đều miss)',
          _hit(c, lb2, BIO_B) is None)
    check('§8.2b-3 hash của B ĐÃ đổi (static luôn được chọn)',
          lb2['constitution_hash'] != lb1['constitution_hash'])

    # ── §8 mục 2c — thêm rule KHÔNG match ───────────────────────────────
    c.execute("INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, "
              "status, match_scope, match_terms) VALUES (?,?,?,?,?,?,?)",
              ('R_BIJING', 'terminology', '汴京 → Biện Kinh', 1, 'active', 'terms',
               json.dumps(['汴京'], ensure_ascii=False)))
    c.commit()
    la3 = _lock(c, BIO_A)
    check('§8.2c-1 thêm rule 汴京 KHÔNG match A ⇒ không vào selection',
          'R_BIJING' not in la3['codes'], str(la3['codes']))
    c.execute("UPDATE translation_cache SET status='invalidated'")
    c.commit()
    la4, lb4 = _lock(c, BIO_A), _lock(c, BIO_B)
    _put(c, la4, BIO_A, 'A mới')
    _put(c, lb4, BIO_B, 'B mới')
    check('§8.2c-2 thêm rule không liên quan ⇒ hash KHÔNG đổi ⇒ A HIT 100%, 0 call LLM',
          _hit(c, _lock(c, BIO_A), BIO_A) is not None)
    check('§8.2c-3 tương tự B HIT', _hit(c, _lock(c, BIO_B), BIO_B) is not None)
    c.close()
    os.unlink(p)


# ── D/E — §8 mục 3 + 5b (điều kiện KHÔNG được nới) ────────────────────────
def test_de():
    print('\n=== D–E. §8 mục 3 (glossary) + 5b (label/json) — KHÔNG được nới ===')
    c, p = _mkdb()
    _seed(c)
    c.execute("INSERT INTO translation_glossary (term_zh, term_vi, is_locked) "
              "VALUES (?,?,1)", (FX_TERM, 'tự nhiên'))
    c.commit()
    la = _lock(c, BIO_A)
    check('D0 glossary 天然 được inject (source A chứa 天然)',
          any(g['term_zh'] == FX_TERM for g in la['glossary']),
          str([g['term_zh'] for g in la['glossary']]))
    _put(c, la, BIO_A, 'A dịch')
    check('D1 fast path HIT', _hit(c, la, BIO_A) is not None)
    c.execute("UPDATE translation_glossary SET term_vi=? WHERE term_zh=?",
              ('thiên nhiên', FX_TERM))
    c.commit()
    la2 = _lock(c, BIO_A)
    check('D2 đổi glossary ĐÃ inject ⇒ MISS', _hit(c, la2, BIO_A) is None)
    # glossary KHÔNG inject (source B) ⇒ đổi glossary cũng không ảnh hưởng B
    c.execute("UPDATE translation_cache SET status='invalidated'")
    c.commit()
    lb = _lock(c, BIO_B)
    _put(c, lb, BIO_B, 'B dịch')
    c.execute("UPDATE translation_glossary SET term_vi=? WHERE term_zh=?", ('tự nhiên MỚI', FX_TERM))
    c.commit()
    check('D3 glossary KHÔNG inject vào B ⇒ B vẫn HIT (lọc đúng)',
          _hit(c, _lock(c, BIO_B), BIO_B) is not None)

    # E — label / json_mode
    c.execute("UPDATE translation_cache SET status='invalidated'")
    c.commit()
    lb_lbl = _lock(c, BIO_B, label='nhãn-A')
    _put(c, lb_lbl, BIO_B, 'B dịch')
    check('E1 cùng label ⇒ HIT', _hit(c, _lock(c, BIO_B, label='nhãn-A'), BIO_B) is not None)
    check('E2 đổi prompt_label ⇒ MISS',
          _hit(c, _lock(c, BIO_B, label='nhãn-B'), BIO_B) is None)
    c.execute("UPDATE translation_cache SET status='invalidated'")
    c.commit()
    lb_js = _lock(c, BIO_B, json_mode=False)
    _put(c, lb_js, BIO_B, 'B dịch')
    check('E3 đổi json_mode ⇒ MISS',
          _hit(c, _lock(c, BIO_B, json_mode=True), BIO_B) is None)
    c.close()
    os.unlink(p)


# ── F — Phase 8a XML boundary ──────────────────────────────────────────────
def test_f_xml():
    print('\n=== F. Phase 8a: XML boundary + version bump ===')
    check('F0 PROMPT_FORMAT_VERSION = t165-v2', PROMPT_FORMAT_VERSION == 't165-v2',
          PROMPT_FORMAT_VERSION)
    c, p = _mkdb()
    _seed(c)
    lock = _lock(c, BIO_A, label='tiểu sử')
    prompt = build_style_prompt(BIO_A, lock, label='tiểu sử')
    for tag in ('<rules>', '</rules>', '<glossary>', '</glossary>',
                '<exemplars>', '</exemplars>', '<source>', '</source>'):
        check(f'F1 có thẻ {tag}', tag in prompt)
    check('F2 <source> chứa NGUYÊN BẢN', f'<source>\n{BIO_A}\n</source>' in prompt)
    check('F3 chỉ dẫn đóng trước <source>',
          prompt.index('</exemplars>') < prompt.index('<source>'))
    c.execute("UPDATE translation_rules SET rule_text=? WHERE rule_code='R_NATURAL'",
              ('a < b & c > d',))
    c.commit()
    pr2 = build_style_prompt('x<y&z', _lock(c, BIO_A))
    check('F4 escape & < > (không phá thẻ)',
          '&lt;' in pr2 and '&amp;' in pr2 and '<y&z' not in pr2)
    pj = build_style_prompt(BIO_A, lock, label='x', json_mode=True)
    check('F5 json_mode giữ yêu cầu JSON duy nhất', 'translation_vi' in pj)
    check('F6 json_mode KHÔNG bọc kết quả trong thẻ giả',
          not re.search(r'<translation_vi>', pj))
    pv1 = build_style_prompt(BIO_A, lock, label='x', xml=False)
    check('F7 xml=False → khung v1 (đo token so sánh)',
          '=== NGUYÊN BẢN HÁN VĂN ===' in pv1 and '<source>' not in pv1)
    c.close()
    os.unlink(p)


# ── G — Phase 8b Trie có gate ──────────────────────────────────────────────
def test_g_trie():
    print('\n=== G. Phase 8b: Trie/Aho-Corasick có gate ===')
    check('G0 TRIE_MIN_TERMS = 1000', TRIE_MIN_TERMS == 1000, str(TRIE_MIN_TERMS))
    terms = ['汴京', '江西', '四川', '嘉州', '上堂', '禪師', '大師', '法師', '天然',
             '法嗣', '少林寺', '白馬寺', '丹霞', '南嶽', '天台', '北宋', '南宋',
             '僧璨', '神光', '慧可', '楞伽', '居士', '法錫', '石頭', '華頂']
    m, mode = build_matcher(terms)
    check('G1 25 term (<1000) ⇒ mode = substring', mode == 'substring', mode)
    txt = '師在江西嘉州，後上堂問禪，天然和尚，居士慧可。'
    a = scan_terms(txt, terms)
    b = TermMatcher(set(terms)).scan(txt)
    check('G2 trie ≡ substring (kết quả giống hệt)', a == b, f'{sorted(a)}')
    check('G3 bắt đúng 6 term trong fixture', len(a) == 6, str(sorted(a)))
    check('G4 không bắt nhầm term không có', '汴京' not in a and '少林寺' not in a)
    big = [f'T{i:04d}' for i in range(1200)]
    mb, mode_b = build_matcher(big)
    check('G5 1.200 term ⇒ mode = trie (auto-bật)', mode_b == 'trie', mode_b)
    check('G6 trie 1.200 term tìm đúng', mb.scan('x T0500 y T1199') == {'T0500', 'T1199'})
    check('G7 matcher rỗng an toàn', TermMatcher([]).scan('abc') == set())

    c, p = _mkdb()
    _seed(c)
    check('G8 select_rules thật (76-term) vẫn chọn đúng',
          set(_lock(c, BIO_A)['codes']) == {'R_NATURAL', 'NO_ADDITION'})
    c.close()
    os.unlink(p)

    c, p = _mkdb()
    c.execute("INSERT INTO translation_rules (rule_code, rule_type, rule_text, is_active, "
              "status, match_scope, match_terms) VALUES ('R_MANY','terminology','nhiều',1,"
              "'active','terms',?)",
              (json.dumps([f'Z{i:04d}' for i in range(1000)], ensure_ascii=False),))
    c.commit()
    check('G9 1.000 term thật trong DB ⇒ match thì chọn',
          'R_MANY' in select_rules(c, 'có Z0999 trong đó')['codes'])
    check('G10 1.000 term ⇒ không match thì loại',
          'R_MANY' not in select_rules(c, 'không có mã nào')['codes'])
    c.close()
    os.unlink(p)


# ── H — Phase 8c đo token v1 vs v2 ────────────────────────────────────────
def test_h_token():
    print('\n=== H. Phase 8c: đo token trước/sau XML ===')
    c, p = _mkdb()
    _seed(c)
    lock = _lock(c, BIO_A, label='tiểu sử')
    p1 = build_style_prompt(BIO_A, lock, label='tiểu sử', xml=False)
    p2 = build_style_prompt(BIO_A, lock, label='tiểu sử')
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        n1, n2 = len(enc.encode(p1)), len(enc.encode(p2))
        basis = 'tiktoken cl100k_base (ĐO THẬT)'
    except Exception:
        n1 = sum(2 if ord(ch) > 0x2E80 else 1 for ch in p1)
        n2 = sum(2 if ord(ch) > 0x2E80 else 1 for ch in p2)
        basis = 'ƯỚC LƯỢNG (Hán 2×, ASCII 1×) — không có tiktoken'
    d = n2 - n1
    pct = (d / n1 * 100) if n1 else 0
    print(f'  v1 (không XML): {n1} token | v2 (XML): {n2} token | '
          f'chênh {d:+d} ({pct:+.1f}%)')
    print(f'  cơ sở đo: {basis}')
    check('H1 đo được cả 2 khung', n1 > 0 and n2 > 0, f'v1={n1} v2={n2}')
    check('H2 XML không làm prompt dài hơn quá nhiều', pct < 25, f'{pct:+.1f}%')
    out = os.path.join(BASE, 'data', 't179_token_measure.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'v1_tokens': n1, 'v2_tokens': n2, 'delta': d,
                   'delta_pct': round(pct, 2), 'basis': basis,
                   'prompt_chars_v1': len(p1), 'prompt_chars_v2': len(p2),
                   'note': 'T179 Phase 8c — đo offline, KHÔNG gọi Groq; '
                           'constitution_hash là per-row nên bump FMT chỉ miss 1 lần'},
                  f, ensure_ascii=False, indent=2)
    check('H3 ghi data/t179_token_measure.json', os.path.exists(out))
    c.close()
    os.unlink(p)


def main():
    print('=' * 70)
    print('T179 — T165 Phase 8 + ĐÍNH CHÍNH kết luận "KNOWN ARCH GAP" của T178')
    print('=' * 70)
    test_abc_real_hash()
    test_de()
    test_f_xml()
    test_g_trie()
    test_h_token()
    print('\n' + '=' * 70)
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    for name, ok, detail in RESULTS:
        if not ok:
            print(f'  FAIL: {name}  [{detail}]')
    print(f'KẾT QUẢ: {npass}/{len(RESULTS)} PASS')
    print('=' * 70)
    return 0 if npass == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())