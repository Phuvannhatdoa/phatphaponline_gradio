"""
style_constitution.py — T165 Rules-Constrained Translation Engine — SSOT (single source of truth)
=====================================================================================================
Module độc lập (cùng cấp app.py) import được từ app, admin, scripts. KHÔNG import app.py
(tránh circular). Chủ trương: thông báo lỗi tiếng Việt; try-except thân thiện; Zero-RAM
(không nạp 248k glossary vào RAM — mọi truy vấn đều SQL + generator).

Đây là nơi duy nhất nắm:
  - select_rules            — lọc rules theo source_text (match_scope='terms' → match substring)
  - constitution_hash       — hash prompt THẬT đã inject (FULL rule_text + filtered glossary +
                              exemplar + PROMPT_FORMAT_VERSION + t166 fingerprint + label/json_mode)
  - style_lock              — lock đầy đủ, tự chạy resolver và tính hash SAU khi merge (#5a)
  - build_style_prompt      — khung prompt thống nhất (dán nguyên cấu trúc _t73_build_style_prompt)
  - invalidate_cache_for_rule — invalidate có chọn lọc theo selected_rule_codes (bỏ DELETE NULL — #4)

Tham chiếu: docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md §3/§5 (SPEC v2).
Số issue #N tương ứng verdict §14.2 đã ACCEPTED (T168).
"""
import hashlib
import json
import re
import sqlite3

PROMPT_FORMAT_VERSION = 't165-v1'   # bump nếu đổi khung prompt phase 2

_RE_HAN_RUN = re.compile(r'[一-鿿㐀-䶿]+')
_RE_ARROW = re.compile(r'([一-鿿㐀-䶿]{1,8})\s*(?:→|->|➞|⟶)\s*\S+')
_RE_PAREN = re.compile(r'[（(]([一-鿿㐀-䶿]{2,8})[）)]')
_RE_HAN_OK = re.compile(r'^[一-鿿㐀-䶿]{2,8}$')


# ── úp tiện: nhận diện cột tồn tại (chạy được cả khi migration chưa apply) ─────────────
def _has_col(conn, table, col):
    try:
        return any(r[1] == col for r in conn.execute(f'PRAGMA table_info({table})').fetchall())
    except Exception:
        return False


def source_hash(text):
    """SHA256 hexdigest[:24] — GIỮ format _t73_source_hash (callers phụ thuộc)."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:24]


def extract_match_terms(rule_text):
    """Trích danh sách thuật ngữ Hán 2-8 chars từ rule_text (SPEC §5, lọc ≥2 chars — #10).
    union các regex (arrow + paren), dedup giữ thứ tự. Fail/rỗng → [] → gọi match_scope='always'."""
    if not rule_text:
        return []
    terms = []
    for m in _RE_ARROW.finditer(rule_text):
        t = (m.group(1) or '').strip()
        if _RE_HAN_OK.match(t):
            terms.append(t)
    for m in _RE_PAREN.finditer(rule_text):
        terms.append(m.group(1))
    seen, out = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _parse_match_terms(raw):
    """match_terms cột DB (JSON string) → list[str]. Fail → []."""
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return [t for t in v if isinstance(t, str)] if isinstance(v, list) else []
    except Exception:
        return []


# ── 1. Select rules ──────────────────────────────────────────────────────────────────────
def select_rules(conn, source_text=None, max_rules=200):
    """Chọn rules áp cho source_text.
    Selector CHỐT: status='active' AND is_active=1 (#13).
    key DB: rule_code/rule_type/rule_text (KHÔNG code/type/content).
    include iff match_scope != 'terms' OR any(match_terms ⊆ source_text).
    - source_text=None → trả TẤT CẢ active (hành vi legacy lúc chưa có text) — a.k.a all-active.
    - extract/matched terms rỗng → coi như always (an toàn, không mất rule oan — #10).
    - match_scope cột chưa tồn tại (pre-migration) → mọi rule như 'always'.
    Trả dict {rules, codes, rule_block, rules_version_global}.
    """
    col_match = _has_col(conn, 'translation_rules', 'match_scope') and \
        _has_col(conn, 'translation_rules', 'match_terms')
    sel = ("SELECT rule_code, rule_type, rule_text, priority"
           + (", match_scope, match_terms" if col_match else "")
           + " FROM translation_rules "
           + "WHERE status='active' AND is_active=1 ORDER BY priority ASC, id ASC")
    try:
        rows = conn.execute(sel).fetchall()
    except Exception as e:
        # fallback an toàn pre-migration (cột chưa tồn tại thì sel không tham chiếu)
        import logging
        logging.getLogger(__name__).warning(f"select_rules query fail (db chưa migrate?): {e}")
        rows = []
    rules = []
    for r in rows:
        scope = (r['match_scope'] or 'always') if col_match else 'always'
        terms = (_parse_match_terms(r['match_terms']) if col_match else [])
        if source_text is not None and scope == 'terms':
            if not terms:
                # extract fail → forced always (an toàn)
                rules.append(dict(r))
                continue
            if not any(t and t in source_text for t in terms):
                continue  # không khớp → loại rule này khỏi prompt
        rules.append(dict(r))
        if len(rules) >= max_rules:
            break
    codes = sorted({r['rule_code'] for r in rules})
    rule_block = "\n".join(
        f"{i+1}. [{r['rule_type'].upper()}] {r['rule_text']}" for i, r in enumerate(rules)
    )
    return {
        'rules': rules,
        'codes': codes,
        'rule_block': rule_block,
        'rules_version_global': _rules_version_global(conn),
    }


def _rules_version_global(conn):
    """Rules_version semantic GLOBAL như cũ (hash mọi active rule_text theo priority) —
    panel admin + fallback legacy lookup dựa vào. KHÔNG filter theo source_text."""
    try:
        rows = conn.execute(
            "SELECT rule_text FROM translation_rules "
            "WHERE status='active' AND is_active=1 ORDER BY priority ASC, id ASC"
        ).fetchall()
        combined = "\n---\n".join((r['rule_text'] or '') for r in rows)
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    except Exception:
        return ''


# ── 2. Glossary filter ───────────────────────────────────────────────────────────────────
def filter_glossary_for_text(locked_rows, source_text, resolver_verified=None, max_glossary=120):
    """Giữ row locked glossary nếu term_zh xuất hiện trong source_text HOẶC đã db_verified.
    (#15: term 1-char gần như luôn match → noise cho T166, không chặn T165).
    source_text=None → trả nguyên (legacy). Sorted stable. Limit max_glossary."""
    resolver_verified = resolver_verified or {}
    out = []
    for g in locked_rows:
        zh = (g.get('term_zh') or '').strip()
        vi = g.get('term_vi') or ''
        if not zh:
            continue
        if source_text is None or zh in source_text or zh in resolver_verified:
            out.append({'term_zh': zh, 'term_vi': vi})
            if len(out) >= max_glossary:
                break
    return out


# ── 3. Hash functions ────────────────────────────────────────────────────────────────────
def glossary_hash(glossary, exemplar=None):
    """sha16[:16] của filtered glossary pairs + exemplar ids (bắt buộc — Admin #3)."""
    parts = sorted(f"{g.get('term_zh','')}→{g.get('term_vi','')}" for g in (glossary or []))
    for ex in (exemplar or []):
        parts.append(f"ex:{ex.get('zh','')}:{ex.get('vi','')}")
    return hashlib.sha256(('\n'.join(parts)).encode('utf-8')).hexdigest()[:16]


def constitution_hash(lock):
    """Hash prompt THẬT đã inject (SPEC §3, post-resolver + label/json_mode/known_pending — #5a/#5b/#5c).
    CẤM hash chỉ rule_code (static_sig bug directive). Các phần:
      - SORT("rule_code\nrule_text" FULL text) cho mọi selected rule (cả static+terms)
      - SORT("zh→vi") filtered glossary + db_verified
      - SORT("zh:vi") exemplar
      - PROMPT_FORMAT_VERSION
      - prompt_label + json_mode (inject khác nhau → hash khác — #5b)
      - known_pending sorted (nếu block được inject — #5c)
      - t166_lock_fingerprint (NULL skip khi T166 chưa build — #12)
      - extra_hash (vd person_name_lock dila_card)
    """
    parts = []
    for r in sorted(lock.get('rules') or [], key=lambda x: (x.get('rule_code') or '', x.get('rule_text') or '')):
        parts.append(f"{r.get('rule_code','')}\n{r.get('rule_text','')}")
    for g in sorted(lock.get('glossary') or [], key=lambda x: (x.get('term_zh',''), x.get('term_vi',''))):
        parts.append(f"{g.get('term_zh','')}→{g.get('term_vi','')}")
    for ex in sorted(lock.get('exemplar') or [], key=lambda x: (x.get('zh',''), x.get('vi',''))):
        parts.append(f"ex:{ex.get('zh','')}:{ex.get('vi','')}")
    parts.append(f"FMT:{PROMPT_FORMAT_VERSION}")
    parts.append(f"label:{lock.get('prompt_label') or ''}")
    parts.append(f"json:{bool(lock.get('json_mode'))}")
    # known_pending nếu caller inject (dila_card — #5c)
    if lock.get('known_pending'):
        kp = sorted(str(p.get('rule_code') or '') for p in lock['known_pending'])
        parts.append(f"known:{','.join(kp)}")
    fp = lock.get('t166_lock_fingerprint')
    if fp:
        parts.append(f"fp:{fp}")
    for ex in (lock.get('extra_hash') or []):
        parts.append(str(ex))
    return hashlib.sha256(('\n'.join(parts)).encode('utf-8')).hexdigest()[:16]


# ── 4. style_lock — lock đầy đủ (tự chạy resolver + hash post-merge) ────────────────────
def style_lock(conn, source_text=None, labels=None, max_glossary=120, max_exemplar=3,
               resolver=None, max_ngrams=400, prompt_label='', json_mode=False,
               extra_hash=None):
    """Build Style Constitution lock. Trả dict:
    {rules, codes, rules_version, constitution_hash, glossary_hash, glossary[], exemplar[],
     known_pending[], resolver, t166_lock_fingerprint, t166_identity_lock}.
    - source_text cung cấp → select_rules lọc + filter_glossary + tự chạy glossary resolver để
      merge db_verified và SAU ĐÓ tính hash (#5a). source_text=None → all-active (hành vi cũ).
    - resolver truyền sẵn (đã chạy ở caller) → dùng, không chạy lại.
    - T166: t166_lock_fingerprint = sha16 của CanonicalLock LOCKED (rỗng nếu không có
      Hán / không có LOCKED ⇒ constitution_hash không đổi ⇒ cache cũ KHÔNG mass-miss).
    """
    sel = select_rules(conn, source_text)
    rules = sel['rules']
    rv = sel['rules_version_global']

    # Glossary locked rows (is_locked=1)
    try:
        locked = [dict(r) for r in conn.execute(
            "SELECT term_zh, term_vi FROM translation_glossary WHERE is_locked=1 "
            "ORDER BY id LIMIT ?", (max_glossary * 3,)
        ).fetchall()]
    except Exception:
        locked = []

    # Empty resolver init
    resolved = {}
    if resolver is None and source_text:
        resolver = glossary_resolver(conn, source_text, max_ngrams=max_ngrams)
    if resolver:
        resolved = resolver.get('resolved') or {}

    # Filter theo text ⊕ db_verified (Admin #3)
    db_verified_keys = {
        k for k, v in (resolved or {}).items() if isinstance(v, dict) and v.get('status') == 'db_verified'
    }
    glossary = filter_glossary_for_text(locked, source_text, db_verified_keys, max_glossary=max_glossary)
    existing_zh = {g['term_zh'] for g in glossary}
    for zh in sorted(db_verified_keys):
        if zh not in existing_zh:
            glossary.append({'term_zh': zh, 'term_vi': (resolved[zh] or {}).get('term_vi', '')})
            if len(glossary) >= max_glossary:
                break

    # Exemplar
    try:
        exemplar = [dict(r) for r in conn.execute(
            "SELECT zh, vi, source_label FROM translation_exemplar "
            "WHERE is_active=1 ORDER BY length_zh LIMIT ?", (max_exemplar,)
        ).fetchall()]
    except Exception:
        exemplar = []

    # known_pending (GIỮ hành vi T158 — dila_card inject)
    known_pending = []
    try:
        pending_rows = conn.execute(
            "SELECT rule_code, rule_text FROM translation_rules WHERE status='pending' LIMIT 100"
        ).fetchall()
        for row in pending_rows:
            zh_terms = _RE_HAN_RUN.findall(row[1] or '')
            if zh_terms:
                known_pending.append({'rule_code': row[0], 'zh': zh_terms[0]})
    except Exception:
        known_pending = []

    lock = {
        'rules': rules,
        'codes': sel['codes'],
        'rules_version': rv,
        'rules_version_global': rv,
        'glossary': glossary,
        'exemplar': exemplar,
        'known_pending': known_pending,
        'resolver': resolver,
        't166_lock_fingerprint': _t166_fingerprint(conn, source_text),
        't166_identity_lock': _t166_identity_lock(conn, source_text),
        'prompt_label': prompt_label,
        'json_mode': json_mode,
        'extra_hash': extra_hash or [],
    }
    lock['glossary_hash'] = glossary_hash(glossary, exemplar)
    lock['constitution_hash'] = constitution_hash(lock)
    return lock


# ── 3b. T166 CanonicalLock bridge (SPEC T166 §9) ──────────────────────────────
def _t166_identity_lock(conn, source_text):
    """Build CanonicalLock từ authority thật (T166). Trả [] nếu không có Hán / lỗi.
    Zero-RAM: SQL batch theo ≤40 maximal Han run."""
    if not source_text:
        return []
    try:
        from canonical_lock import build_canonical_lock
        return build_canonical_lock(conn, source_text)
    except Exception:
        # T166 chưa sẵn sàng / DB thiếu bảng → KHÔNG làm hỏng T165
        return []


def _t166_fingerprint(conn, source_text):
    """t166_lock_fingerprint (sha16) để nhét vào constitution_hash.
    Rỗng ('') khi không có Hán hoặc không có entry LOCKED ⇒ constitution_hash
    KHÔNG đổi ⇒ cache cũ vẫn hit (tránh mass-miss 1762 row — SPEC §9 / §20.2 #18)."""
    entries = _t166_identity_lock(conn, source_text)
    if not entries:
        return ''
    try:
        from canonical_lock import t166_lock_fingerprint
        return t166_lock_fingerprint(entries)
    except Exception:
        return ''


def glossary_resolver(conn, source_text, max_ngrams=400):
    """14-priority pre-translation lookup (SPEC §2 — 14 authority tables; #14 docstring).
    Trả {resolved, unresolved} — shape khớp _glossary_resolver (app.py)."""
    if not source_text:
        return {'resolved': {}, 'unresolved': []}
    runs = _RE_HAN_RUN.findall(source_text)
    seen, ngrams = set(), []
    for run in runs:
        for n in (2, 3, 4, 5):
            for i in range(len(run) - n + 1):
                g = run[i:i + n]
                if g not in seen:
                    seen.add(g)
                    ngrams.append(g)
        if len(ngrams) >= max_ngrams:
            break
    if not ngrams:
        return {'resolved': {}, 'unresolved': []}
    resolved = {}
    ng_set = set(ngrams)
    ph = ','.join('?' * len(ngrams))

    def _bulk(sql, args, src, status):
        try:
            for row in conn.execute(sql, args).fetchall():
                zh, vi = row[0], row[1]
                if zh in ng_set and vi and zh not in resolved:
                    resolved[zh] = {'term_vi': vi, 'source': src, 'status': status}
        except Exception:
            pass

    _bulk("SELECT term_zh, term_vi FROM translation_glossary WHERE term_zh IN (%s) AND is_locked=1" % ph,
          ngrams, 'translation_glossary', 'db_verified')
    _bulk("SELECT display_name_zh, display_name_vi FROM person_display_names "
          "WHERE display_name_zh IN (%s) AND display_name_vi IS NOT NULL AND display_name_vi!=''" % ph,
          ngrams, 'person_display_names', 'db_verified')
    _bulk("SELECT name_zh, name_vi FROM vn_person_authority "
          "WHERE name_zh IN (%s) AND status='verified' AND name_vi IS NOT NULL AND name_vi!=''" % ph,
          ngrams, 'vn_person_authority', 'db_verified')
    _bulk("SELECT entity_ref, canonical_name_vi FROM canonical_decision "
          "WHERE entity_ref IN (%s) AND canonical_name_vi IS NOT NULL AND canonical_name_vi!=''" % ph,
          ngrams, 'canonical_decision', 'db_verified')
    _bulk("SELECT name_zh, name_vi_final FROM name_vi_map "
          "WHERE name_zh IN (%s) AND name_vi_final IS NOT NULL AND name_vi_final!=''" % ph,
          ngrams, 'name_vi_map', 'db_verified')
    _bulk("SELECT name_zh, proposed_vi FROM person_name_correction "
          "WHERE name_zh IN (%s) AND status='approved' AND proposed_vi IS NOT NULL AND proposed_vi!=''" % ph,
          ngrams, 'person_name_correction', 'db_verified')
    _bulk("SELECT term_zh, term_vi FROM term_glossaries "
          "WHERE term_zh IN (%s) AND term_vi IS NOT NULL AND term_vi!='' AND term_vi!=term_zh" % ph,
          ngrams, 'term_glossaries', 'db_verified')
    _bulk("SELECT label, label_vi FROM marcus_reference "
          "WHERE label IN (%s) AND label_vi IS NOT NULL AND label_vi!='' AND label_vi!=label" % ph,
          ngrams, 'marcus_reference', 'db_verified')
    _bulk("SELECT name_zh, name_vi FROM namevi_map_places "
          "WHERE name_zh IN (%s) AND (vn_name_status='reviewed' OR confidence>=0.8) "
          "AND name_vi IS NOT NULL AND name_vi!=''" % ph,
          ngrams, 'namevi_map_places_hq', 'db_verified')
    _bulk("SELECT title_zh, title_vi FROM cbeta_catalog_vn "
          "WHERE title_zh IN (%s) AND title_vi IS NOT NULL AND title_vi!=''" % ph,
          ngrams, 'cbeta_catalog_vn', 'db_verified')
    _bulk("SELECT name_zh, name_vi FROM doctrine_concept "
          "WHERE name_zh IN (%s) AND name_vi IS NOT NULL AND name_vi!=''" % ph,
          ngrams, 'doctrine_concept', 'db_verified')
    _bulk("SELECT han_name, vn_name FROM monk_dict "
          "WHERE han_name IN (%s) AND vn_name IS NOT NULL AND vn_name!=''" % ph,
          ngrams, 'monk_dict', 'db_verified')
    # Priority 13: translation_rules active → "Vi (漢字) là..."
    try:
        tr_rows = conn.execute(
            "SELECT rule_text FROM translation_rules WHERE status='active'"
        ).fetchall()
        for row in tr_rows:
            rtext = (row[0] or '').strip()
            m = re.search(r'^([^（(一-鿿]+?)\s*[（(]([一-鿿㐀-䶿]{2,})[）)]', rtext)
            if m:
                vi_part, zh_part = m.group(1).strip(), m.group(2)
                if zh_part in ng_set and vi_part and zh_part not in resolved:
                    resolved[zh_part] = {'term_vi': vi_part, 'source': 'translation_rules_active',
                                         'status': 'db_verified'}
    except Exception:
        pass
    # Priority 14: namevi_map_places (all — ambiguous)
    _bulk("SELECT name_zh, name_vi FROM namevi_map_places "
          "WHERE name_zh IN (%s) AND name_vi IS NOT NULL AND name_vi!=''" % ph,
          ngrams, 'namevi_map_places', 'db_ambiguous')
    unresolved = [zh for zh in ngrams if zh not in resolved]
    return {'resolved': resolved, 'unresolved': unresolved}


# ── 5. Invalidate ────────────────────────────────────────────────────────────────────────
def invalidate_cache_for_rule(conn, rule_code):
    """DELETE cache có selected_rule_codes chứa rule_code (SPEC §3, BỎ WHERE NULL — #4).
    Codes không chứa `,` (chỉ [A-Z0-9_]) → delimiter `,` an toàn. commit; return rowcount.
    Pre-migration DB (chưa có cột selected_rule_codes) → 0 (không có row gắn rule nào)."""
    if not _has_col(conn, 'translation_cache', 'selected_rule_codes'):
        return 0
    cur = conn.execute(
        "DELETE FROM translation_cache "
        "WHERE selected_rule_codes IS NOT NULL "
        "  AND instr(',' || selected_rule_codes || ',', ',' || ? || ',') > 0",
        (rule_code,)
    )
    conn.commit()
    return cur.rowcount


def invalidate_cache_all_semantic(conn):
    """Fallback admin nút 'Dịch lại hàng loạt' (T123): DELETE mọi row semantic
    (constitution_hash != NULL). Legacy NULL giữ nguyên (tự miss theo rules_version).
    Pre-migration DB (chưa có cột) → 0 (ghi nhận là chưa có gì để xoá)."""
    if not _has_col(conn, 'translation_cache', 'constitution_hash'):
        return 0
    cur = conn.execute("DELETE FROM translation_cache WHERE constitution_hash IS NOT NULL")
    conn.commit()
    return cur.rowcount


# ── 6. log_prompt_metrics ────────────────────────────────────────────────────────────────
PROMPT_METRICS_TABLE = 'translation_prompt_metrics'


def persist_prompt_metrics(conn, prompt_tokens=0, completion_tokens=0, total_tokens=0,
                           source_type=None, source_text=None, model_id=None,
                           cache_hit=0, constitution_hash=None, logger=None):
    """T178 gap 13 — PERSIST usage.prompt_tokens vào bảng additive append-only.

    Ngân sách: KHÔNG hard-gate (baseline đo được 3.400–3.700 prompt_tokens/lần — T177 D7;
    directive's 150–250 không khả thi, gấp ~14×). Chỉ đo + lưu để Admin đối chiếu.

    - `conn=None` ⇒ no-op (call site cũ giữ nguyên hành vi).
    - Bảng chưa migrate ⇒ no-op (guard sqlite3.OperationalError, KHÔNG fail luồng dịch).
    - Zero-RAM: INSERT 1 row/bạn gọi, KHÔNG đọc/quét bảng.
    """
    if conn is None:
        return False
    try:
        conn.execute(
            f"INSERT INTO {PROMPT_METRICS_TABLE} "
            "(source_type, source_len, prompt_tokens, completion_tokens, total_tokens, "
            " model_id, cache_hit, constitution_hash) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (source_type, len(source_text or ''), int(prompt_tokens or 0),
             int(completion_tokens or 0), int(total_tokens or 0),
             model_id, 1 if cache_hit else 0, constitution_hash)
        )
        return True
    except Exception as e:  # noqa: BLE001 — metrics KHÔNG được làm hỏng luồng dịch
        if logger is not None:
            logger.warning(f"[T178 persist_prompt_metrics] bỏ qua: {e}")
        return False


def log_prompt_metrics(response_json, source_text=None, logger=None, conn=None,
                       source_type=None, model_id=None, cache_hit=0,
                       constitution_hash=None):
    """Đọc usage.prompt_tokens/completion_tokens/total_tokens → logger INFO tiếng Việt
    + (T178) PERSIST vào `translation_prompt_metrics` khi truyền `conn`.
    KHÔNG hard-fail theo ngưỡng 150–250 (không khả thi — baseline đo 3.422); chỉ measure + lưu.
    Tham số mới đều OPTIONAL ⇒ call site cũ không đổi hành vi.
    """
    usage = (response_json or {}).get('usage') or {}
    pt = usage.get('prompt_tokens') or 0
    ct = usage.get('completion_tokens') or 0
    tt = usage.get('total_tokens') or 0
    sample = ''
    if source_text:
        sample = (source_text[:40].replace('\n', ' ')
                  + ('…' if len(source_text) > 40 else ''))
    msg = (f"[T165 log_prompt_metrics] source={len(source_text or '')} chars"
           f" | prompt_tokens={pt} completion_tokens={ct} total_tokens={tt}")
    if sample:
        msg += f" | sample='{sample}'"
    if logger is not None:
        logger.info(msg)
    if conn is not None:
        persist_prompt_metrics(conn, pt, ct, tt, source_type=source_type,
                               source_text=source_text, model_id=model_id,
                               cache_hit=cache_hit,
                               constitution_hash=constitution_hash, logger=logger)
    return {'prompt_tokens': pt, 'completion_tokens': ct, 'total_tokens': tt}


# ── 7. build_style_prompt — khung prompt thống nhất (GIỮ nguyên wording T123) ─────────────
def build_style_prompt(content, lock, label='văn bản', json_mode=False):
    """T123 — Unified Style-Lock prompt cho MỌI luồng dịch Groq. Dán Y cấu trúc
    _t73_build_style_prompt hiện tại (KHÔNG đổi wording / KHÔNG XML trong phase 1 — Admin #2 phase 2).
    Chỉ đổi nguồn rule_block + glossary_block (đã filter theo source_text)."""
    rule_block = "\n".join(f"{i+1}. [{r['rule_type'].upper()}] {r['rule_text']}"
                           for i, r in enumerate(lock.get('rules') or []))
    glossary_block = "\n".join(f"  - {g['term_zh']} → {g['term_vi']}"
                               for g in lock.get('glossary') or []) or "  (không có)"
    exemplar_block = ""
    for i, ex in enumerate(lock.get('exemplar') or [], 1):
        exemplar_block += (
            f"\n--- MẪU {i} (theo {ex['source_label']}) ---\n"
            f"Hán: {ex['zh']}\nViệt: {ex['vi']}\n"
        )
    persona = (
        "Bạn là thành viên Ban Dịch PTDA — dịch giả Hán-Việt chuyên ngành Phật học, "
        "kế thừa tinh thần các dịch giả và từ điển Phật học danh tiếng. "
        "Dịch đoạn {label} Hán văn dưới đây sang tiếng Việt theo ĐÚNG mọi quy tắc bắt buộc."
    ).format(label=label)
    how = ("Trả về JSON duy nhất: {\"translation_vi\": \"...\"}, không kèm nội dung khác."
           if json_mode else
           "Chỉ trả về bản dịch thuần tiếng Việt, không giải thích, không ghi chú trong ngoặc, "
           "không lặp lại chữ Hán. Giữ cấu trúc đoạn văn của bản gốc.")
    # T166 §5 — LOCKED CANONICAL CONTEXT là CONSTRAINT, đặt TRƯỚC glossary để
    # ưu tiên cao nhất (identity > thuật ngữ > phong cách).
    identity_block = _t166_identity_block(lock)
    return (
        f"{persona}\n\n"
        f"{identity_block}"
        f"=== QUY TẮC DỊCH BẮT BUỘC (Style Constitution) ===\n{rule_block}\n\n"
        f"=== GLOSSARY LOCK (thuật ngữ bắt buộc, ưu tiên cao nhất) ===\n{glossary_block}\n"
        f"=== FEW-SHOT MẪU PHONG CÁCH (học theo tiền bối danh tác) ===\n{exemplar_block or '  (không có'}\n"
        f"=== NGUYÊN BẢN HÁN VĂN ===\n{content}\n\n"
        f"=== BẢN DỊCH TIẾNG VIỆT / YÊU CẦU ===\n{how}"
    )


def _t166_identity_block(lock):
    """Render CanonicalLock (T166 §5) thành prompt section. Rỗng nếu không có lock."""
    entries = (lock or {}).get('t166_identity_lock') or []
    if not entries:
        return ''
    try:
        from canonical_lock import build_lock_prompt_section
        section = build_lock_prompt_section(entries)
    except Exception:
        return ''
    return section + '\n\n' if section else ''


# ── 8. cache helpers (dual-key transition — chạy khi cột tồn tại) ────────────────────────
def is_rules_outdated(row, constitution_hash):
    """T178 gap 14/16 — bản dịch đang phục vụ có LỆCH rules không?

    True khi:
      (a) row phục vụ từ nhánh `status='edited'` (hash lệch) — bản human giữ nguyên theo
          SPEC §4.4 #3, nhưng rules đã đổi ⇒ Admin/user cần biết để bấm "Dịch lại";
      (b) `constitution_hash` NULL (chưa backfill / pre-migration) — KHÔNG xác minh được
          ⇒ coi là outdated để hiển thị badge, KHÔNG đoán là "đúng".
    KHÔNG đổi logic chọn dòng (chỉ báo cáo trạng thái).
    """
    if not row:
        return False
    try:
        if (row['status'] or '') == 'edited':
            return True
        ch = row['constitution_hash']
    except (IndexError, KeyError):
        return False
    if not ch:
        return True
    return bool(constitution_hash) and ch != constitution_hash


def lookup_cache(conn, src_hash, constitution_hash, rules_version, source_type):
    """Dual-key lookup (SPEC §4.4 v2):
      1) constitution_hash khớp (status!='invalidated') — ưu tiên status='edited'
      2) fallback legacy rules_version khớp
    Trả row(sqlite3.Row) hoặc None. Bảo vệ edited (#3): query nhánh ưu tiên edited trước."""
    if _has_col(conn, 'translation_cache', 'constitution_hash'):
        # edited priority (#3): bản human giữ nguyên bất kể hash lệch
        edited = conn.execute(
            "SELECT * FROM translation_cache "
            "WHERE source_hash=? AND source_type=? AND status='edited' AND status!='invalidated' "
            "ORDER BY id DESC LIMIT 1",
            (src_hash, source_type)
        ).fetchone()
        if edited:
            return edited
        row = conn.execute(
            "SELECT * FROM translation_cache "
            "WHERE source_hash=? AND source_type=? AND status!='invalidated' "
            "  AND constitution_hash IS NOT NULL AND constitution_hash=? "
            "ORDER BY id DESC LIMIT 1",
            (src_hash, source_type, constitution_hash)
        ).fetchone()
        if row:
            return row
    # legacy fallback
    return conn.execute(
        "SELECT * FROM translation_cache "
        "WHERE source_hash=? AND source_type=? AND status!='invalidated' AND rules_version=? "
        "ORDER BY id DESC LIMIT 1",
        (src_hash, source_type, rules_version)
    ).fetchone()


def write_cache(conn, src_hash, source_type, entity_id, source_text, translated_text,
                model_id, rules_version, status='auto',
                constitution_hash=None, selected_rule_codes=None, glossary_hash=None,
                identity_status=None, identity_issues=None, identity_lock_hash=None):
    """Ghi cache dual-key (SPEC §4.3): luôn ghi constitution_hash + selected_rule_codes(CSV)
    + glossary_hash + rules_version (giữ compat panel). KHÔNG bao giờ REPLACE row status='edited' (#3):
    trả (id_existing_edited, replaced:False) nếu row edited tồn tại — caller phải dùng UPDATE.

    T166 (SPEC §8.5): thêm identity_status / identity_issues (JSON) / identity_lock_hash.
    - `identity_status=None` ⇒ để NULL = legacy pass (KHÔNG đoán lịch sử).
    - Cột identity_* chỉ ghi khi DB đã migrate (guard `_has_col`) → pre-migration
      vẫn chạy như T165.
    """
    if _has_col(conn, 'translation_cache', 'constitution_hash'):
        edited = conn.execute(
            "SELECT id FROM translation_cache "
            "WHERE source_hash=? AND source_type=? AND status='edited' AND status!='invalidated' "
            "ORDER BY id DESC LIMIT 1",
            (src_hash, source_type)
        ).fetchone()
        if edited:
            return edited['id'], False
    now = __import__('datetime').datetime.now().isoformat()
    csv_codes = ",".join(selected_rule_codes or []) or None
    issues_json = None
    if identity_issues:
        try:
            import json as _json
            issues_json = _json.dumps(identity_issues, ensure_ascii=False)
        except Exception:
            issues_json = None

    if _has_col(conn, 'translation_cache', 'identity_status'):
        # T166 đã migrate — ghi đủ 3 cột identity
        cur = conn.execute(
            "INSERT INTO translation_cache "
            "(source_hash, source_type, entity_id, source_text, translated_text, "
            " model_id, rules_version, status, created_at, updated_at, "
            " constitution_hash, selected_rule_codes, glossary_hash, "
            " identity_status, identity_issues, identity_lock_hash) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (src_hash, source_type, entity_id, source_text, translated_text,
             model_id, rules_version, status, now, now,
             constitution_hash, csv_codes, glossary_hash,
             identity_status, issues_json, identity_lock_hash)
        )
    elif _has_col(conn, 'translation_cache', 'constitution_hash'):
        # T165 đã migrate, T166 chưa → bỏ cột identity
        cur = conn.execute(
            "INSERT INTO translation_cache "
            "(source_hash, source_type, entity_id, source_text, translated_text, "
            " model_id, rules_version, status, created_at, updated_at, "
            " constitution_hash, selected_rule_codes, glossary_hash) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (src_hash, source_type, entity_id, source_text, translated_text,
             model_id, rules_version, status, now, now,
             constitution_hash, csv_codes, glossary_hash)
        )
    else:
        # pre-migration DB (chưa có cột T165) → legacy insert, bỏ các cột mới
        cur = conn.execute(
            "INSERT INTO translation_cache "
            "(source_hash, source_type, entity_id, source_text, translated_text, "
            " model_id, rules_version, status, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (src_hash, source_type, entity_id, source_text, translated_text,
             model_id, rules_version, status, now, now)
        )
    return cur.lastrowid, True


# ── 8b. T166 cache safety (SPEC §8.1–§8.4) ─────────────────────────────────
# Trusted read = identity_status IS NULL OR 'pass'  (NULL = legacy, không đoán lịch sử)
TRUSTED_IDENTITY = (None, '', 'pass')
# Row failed/conflict/review_required VẪN serve như DRAFT (không trusted) và
# KHÔNG tự re-LLM mỗi request (tránh lặp vô hạn + chi phí TPM) — chỉ re-run
# khi Admin bấm "Dịch lại" (force) — SPEC §8.3.
DRAFT_IDENTITY = ('failed', 'conflict', 'review_required')


def is_trusted_translation(row):
    """True nếu row cache được coi là 'đã duyệt chuẩn' cho UI (SPEC §8.1)."""
    if row is None:
        return False
    try:
        val = row['identity_status'] if not isinstance(row, dict) else row.get('identity_status')
    except (IndexError, KeyError, TypeError):
        return False
    return val in TRUSTED_IDENTITY


def is_draft_translation(row):
    """True nếu row cache phải serve như DRAFT kèm cờ 'chưa duyệt' (SPEC §8.3)."""
    if row is None:
        return False
    try:
        val = row['identity_status'] if not isinstance(row, dict) else row.get('identity_status')
    except (IndexError, KeyError, TypeError):
        return False
    return val in DRAFT_IDENTITY


def identity_lock_policy(conn, default='P-PARTIAL'):
    """Đọc `translation_rules.identity_lock_policy` (Admin đổi được — SPEC §4).
    Fallback về `default` khi cột chưa migrate / không có row."""
    if not _has_col(conn, 'translation_rules', 'identity_lock_policy'):
        return default
    try:
        row = conn.execute(
            "SELECT identity_lock_policy FROM translation_rules "
            "WHERE identity_lock_policy IS NOT NULL AND identity_lock_policy!='' "
            "ORDER BY id LIMIT 1"
        ).fetchone()
        val = row['identity_lock_policy'] if row else None
    except sqlite3.Error:
        return default
    return val if val in ('P-PARTIAL', 'P-STOP') else default