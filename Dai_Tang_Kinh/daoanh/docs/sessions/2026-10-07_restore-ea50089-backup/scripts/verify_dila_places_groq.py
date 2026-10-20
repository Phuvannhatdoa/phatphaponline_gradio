# -*- coding: utf-8 -*-
"""
T169 / T170 — Robust Batch Verification Pipeline: Groq Qwen vs SQLite từ điển

`--entity place`  (mặc định, T169) — ĐỊA DANH places_dila JOIN places_pending → `place_groq_audit`
`--entity person` (T170)        — NHÂN VẬT people (spine) → `person_groq_audit`
    + preprocess R2 bracket-strip · R3 fold_cjk · R4 title strip (t170_classify)
    + classify person: SANSKRIT registry/R2/R3/R4 → TITLE_VARIANT = auto_title_aligned,
      Sanskrit khớp = auto_verified_sanskrit, indicator lạ = SANSKRIT_UNMAPPED →
      needs_lexicon_review (SPEC §3.2/§3.4 + §3bis R2/R3/R4).

Khung directive (giữ nguyên T169, §5):
- batch 25 · RPM adaptive · retry 429 · atomic `with conn` (Ctrl+C giữ batch đã commit, dở rollback)
- P0: DB thật data/lineage.db · resolve key env → data/llm_config.json ·
  model default qwen/qwen3.8-27b
- P1 + T184 G1/G3/G4: `:cursor` memory trong 1 run · restart scan từ đầu qua predicate ·
  skip verified/approved_dict BẤT KỂ --force · conflict/api_error/pending LUÔN retried ·
  --force chỉ bỏ guard "đã có run".

Thay đổi T170 (SPEC §3bis + §5):
- R5: BỎ `PRAGMA journal_mode=WAL` (dòng chủ đoạn ghi), thêm `PRAGMA busy_timeout=10000`
  + `synchronous=NORMAL` cho mọi connection.
- R6: parse response flat/dict `{"trans_vi": "..."}` → `normalize_groq()` = extract trans_vi
  (ưu tiên flat dict, fallback nested, fallback regex từng cặp, pass-through text trơn).
  Empty content → api_error (enum API_EMPTY_RESPONSE). Nếu content chỉ có người dụng → được ghi.
- R7: max_tokens 512 → 2048 · salvage: 1 lần gọi lại khi parse thất bại (retry once).

Chỉ ghi side-car audit — KHÔNG đụng people/places_pending / namevi_map_*.

Usage:
    python scripts/verify_dila_places_groq.py --entity place --limit 25 --mock   # smoke test khô
    python scripts/verify_dila_places_groq.py                       # place full (~2.366 batch)
    python scripts/verify_dila_places_groq.py --entity person --limit 25 --mock # smoke person
    python scripts/verify_dila_places_groq.py --entity person        # person full (~1.947 batch)

Bắt buộc trước khi chạy thật:
    python scripts/t170_entity_groq_audit_migrate.py --apply   (person side-car)
    (place side-car: python scripts/t169_place_groq_audit_migrate.py --apply)
"""
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE     = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.environ.get('T170_DB') or os.environ.get('T169_DB') \
    or os.path.join(BASE, '..', 'data', 'lineage.db')
LLM_CFG  = os.path.join(BASE, '..', 'data', 'llm_config.json')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
DEFAULT_MODEL = 'qwen/qwen3.8-27b'

sys.path.insert(0, BASE)
try:
    import requests
except Exception:
    requests = None

from t169_classify import classify_diff  # noqa: E402
from t170_classify import classify_person_diff, split_brackets, fold_cjk  # noqa: E402

BATCH_SIZE = 25
MAX_RETRIES = 3
SLEEP_OK = 2.2      # ~27 RPM (dưới trần 30 free tier) — G3
SLEEP_LOW = 3.0     # khi x-ratelimit-remaining-requests <= 5
LOW_WATERMARK = 5
TPM_LIMIT = 6000
MAX_TOKENS = 2048   # R7: 512 → 2048

STATUS_VERIFIED = 'verified'
STATUS_CONFLICT = 'conflict'
STATUS_API_ERROR = 'api_error'
# rows đã duyệt — không bao giờ chạy lại (G4, kể cả --force).
# place: verified/approved_dict. person: thêm auto_* (resolved một lần, không gọi lại API).
SKIP_STATUSES = ('verified', 'approved_dict', 'auto_verified', 'auto_verified_sanskrit',
                 'auto_title_aligned', 'auto_taxonomy_aligned')
_SKIP_CLAUSE = "review_status IN ('" + "', '".join(SKIP_STATUSES) + "')"

# auto status from person classify → (status, needs_review)
AUTO_STATUS = {
    'auto_verified':            ('auto_verified', 0),
    'auto_verified_sanskrit':   ('auto_verified_sanskrit', 0),
    'auto_title_aligned':       ('auto_title_aligned', 0),
    'auto_taxonomy_aligned':    ('auto_taxonomy_aligned', 0),
    'needs_lexicon_review':     ('needs_lexicon_review', 1),
}

SYSTEM_PROMPT_TMPL = (
    'Bạn là chuyên gia Hán-Nôm Phật giáo. Nhiệm vụ: phiên âm {word} Hán tự '
    '(name_zh) sang tiếng Việt Hán-Việt học thuật cho bản Việt dịch Đại Tạng Kinh.\n'
    '- Chỉ trả giá trị phiên âm, không thêm lời bàn, không thẻ, không dấu câu.\n'
    '- {example}: giữ Hán-Việt chuẩn (vd 寺 -> "Tự").\n'
    '- Trả JSON duy nhất, đúng schema: {{"trans_vi": "..."}}'
)


def _con():
    # R5: bỏ WAL; busy_timeout 10000 + synchronous=NORMAL
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=10000')
    con.execute('PRAGMA synchronous=NORMAL')
    return con


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _ts():
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def resolve_groq_key_model():
    """Key: env GROQ_API_KEY/GROQ_KEY → llm_config.groq_key → ''. Model tương tự."""
    key = os.environ.get('GROQ_API_KEY') or os.environ.get('GROQ_KEY') or ''
    model = os.environ.get('GROQ_MODEL') or DEFAULT_MODEL
    try:
        with open(LLM_CFG, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        if not key and cfg.get('groq_key'):
            key = cfg.get('groq_key')
        if cfg.get('groq_model'):
            model = cfg.get('groq_model')
    except Exception:
        pass
    return (key or ''), model


# ---------------------------------------------------------------- R6 parse
def safe_parse_json_content(text):
    """Bỏ fence (```json … ```) và trích object JSON đầu tiên."""
    if not text:
        return None
    text = re.sub(r'```(?:json)?', '', text).strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        fm = re.search(r'"trans_vi"\s*:\s*"([^"]*)"', text, re.DOTALL)
        if fm:
            return {'trans_vi': fm.group(1).strip()}
        return None


def find_trans_vi(obj):
    """R6 flat: đệ quy tìm trans_vi/translation/name_vi trong dict (flat hoặc nested)."""
    if isinstance(obj, dict):
        for k in ('trans_vi', 'translation', 'name_vi'):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        for v in obj.values():
            r = find_trans_vi(v)
            if r:
                return r
    return None


def normalize_groq(text):
    """(trans_vi, ok, note). R6: trích giá trị sạch khỏi JSON (fence/flat/nested/regex);
    text trơn → pass-through (mock/model trả thẳng); rỗng/không parse được → ok=False."""
    if not text or not text.strip():
        return None, False, 'empty_response'
    t = text.strip()
    if '{' not in t:
        return t, True, 'plain'
    d = safe_parse_json_content(t)
    if d is not None:
        v = find_trans_vi(d)
        if v:
            return v, True, ('json_flat' if isinstance(d, dict) and 'trans_vi' in d else 'json_nested')
    fm = re.search(r'"trans_vi"\s*:\s*"([^"]*)"', t, re.DOTALL)
    if fm:
        return fm.group(1).strip(), True, 'json_regex'
    return t, False, 'unparseable'


# ---------------------------------------------------------------- Groq call
class Result:
    def __init__(self, text=None, usage=None, error=None, remaining_requests=None):
        self.text = text
        self.usage = usage or {}
        self.error = error
        self.remaining_requests = remaining_requests


def call_groq(key, model, use_json_object, remaining_hint=None):
    """1 request 1 đối tượng. Trả Result. Retry 429/5xx với backoff."""
    if not requests:
        return Result(error='http_error')
    last_error = 'api_error'
    for attempt in range(MAX_RETRIES + 1):
        body = {
            'model': model,
            'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}],
            'temperature': 0.1,
            'max_tokens': MAX_TOKENS,   # R7
        }
        if use_json_object:
            body['response_format'] = {'type': 'json_object'}
        try:
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                json=body, timeout=90)
        except Exception:
            last_error = 'http_error'
            if attempt < MAX_RETRIES:
                time.sleep(2 * (2 ** attempt))
            continue
        rrl = resp.headers.get('x-ratelimit-remaining-requests')
        rrl_alt = resp.headers.get('x-ratelimit-remaining')
        rem = rrl or rrl_alt
        try:
            rem = int(rem)
        except Exception:
            rem = remaining_hint
        if resp.status_code == 429:
            last_error = 'rate_limit'
            if attempt < MAX_RETRIES:
                time.sleep(4 * (2 ** attempt))
            continue
        if resp.status_code in (400, 422):
            return Result(error='schema_400', remaining_requests=rem)
        if resp.status_code != 200:
            last_error = f'HTTP {resp.status_code}'
            if attempt < MAX_RETRIES:
                time.sleep(2 * (2 ** attempt))
            continue
        try:
            data = resp.json()
        except Exception:
            last_error = 'not-json'
            continue
        if data.get('choices'):
            text = (data['choices'][0]['message'].get('content') or '').strip()
            return Result(text=text, usage=(data.get('usage') or {}), remaining_requests=rem)
        last_error = str(data.get('error', 'unknown'))[:120]
    return Result(error=last_error,
                  remaining_requests=rem if 'rem' in dir() else None)


def sleep_adaptive(remaining_requests):
    if isinstance(remaining_requests, int) and remaining_requests <= LOW_WATERMARK:
        time.sleep(SLEEP_LOW)
    else:
        time.sleep(SLEEP_OK)


# ---------------------------------------------------------------- SQL scope / upsert
SCOPE_SQL_PLACE = f"""
SELECT d.id, d.name_zh, p.name_vi AS dict_vi
FROM places_dila d
JOIN places_pending p ON p.id = d.id
WHERE d.id > :cursor
  AND d.name_zh IS NOT NULL AND d.name_zh != ''
  AND d.id NOT IN (
    SELECT id FROM place_groq_audit
    WHERE {_SKIP_CLAUSE}
  )
ORDER BY d.id
LIMIT 25
"""

UPSERT_SQL_PLACE = """
INSERT INTO place_groq_audit
 (id, name_zh, dict_vi, groq_trans_vi, needs_review, review_status, diff_type,
  diff_reason, model_id, batch_id, prompt_tokens, completion_tokens, checked_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  dict_vi=excluded.dict_vi, groq_trans_vi=excluded.groq_trans_vi,
  needs_review=excluded.needs_review, review_status=excluded.review_status,
  diff_type=excluded.diff_type, diff_reason=excluded.diff_reason,
  model_id=excluded.model_id, batch_id=excluded.batch_id,
  prompt_tokens=excluded.prompt_tokens, completion_tokens=excluded.completion_tokens,
  checked_at=excluded.checked_at
"""

SCOPE_SQL_PERSON = f"""
SELECT p.id, p.name_zh, p.name_vi AS dict_vi
FROM people p
WHERE p.id > :cursor
  AND p.name_zh IS NOT NULL AND p.name_zh != ''
  AND p.id NOT IN (
    SELECT id FROM person_groq_audit
    WHERE {_SKIP_CLAUSE}
  )
ORDER BY p.id
LIMIT 25
"""

UPSERT_SQL_PERSON = """
INSERT INTO person_groq_audit
 (id, name_zh, dict_vi, groq_trans_vi, final_vi, clean_zh, meta_note, variant_zh,
  is_uncertain, needs_review, review_status, diff_type, diff_reason, model_id,
  batch_id, prompt_tokens, completion_tokens, retry_count, last_error,
  processing_started_at, checked_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  dict_vi=excluded.dict_vi, groq_trans_vi=excluded.groq_trans_vi,
  final_vi=excluded.final_vi, clean_zh=excluded.clean_zh, meta_note=excluded.meta_note,
  variant_zh=excluded.variant_zh, is_uncertain=excluded.is_uncertain,
  needs_review=excluded.needs_review, review_status=excluded.review_status,
  diff_type=excluded.diff_type, diff_reason=excluded.diff_reason,
  model_id=excluded.model_id, batch_id=excluded.batch_id,
  prompt_tokens=excluded.prompt_tokens, completion_tokens=excluded.completion_tokens,
  retry_count=excluded.retry_count, last_error=excluded.last_error,
  processing_started_at=excluded.processing_started_at, checked_at=excluded.checked_at
"""


def classify_place(name_zh, dict_vi, groq_vi):
    try:
        diff_type, reason = classify_diff(name_zh, dict_vi, groq_vi)
    except ValueError as e:
        diff_type, reason = 'NONE', f'skip-classify: {e}'
    return diff_type, reason, None


def classify_person(name_zh, dict_vi, groq_vi):
    diff_type, reason, hint = classify_person_diff(name_zh, dict_vi, groq_vi)
    return diff_type, reason, hint


def person_pre(name_zh):
    """R2/R3 preprocess cho upsert person (clean_zh/meta/variant/uncertain)."""
    clean_zh, meta_note, uncertain = split_brackets(name_zh)
    folded, changed = fold_cjk(clean_zh or name_zh)
    variant_zh = folded if changed else None
    return clean_zh, meta_note, variant_zh, uncertain


def status_from(diff_type, hint):
    if hint in AUTO_STATUS:
        return AUTO_STATUS[hint]
    if diff_type == 'NONE':
        return STATUS_VERIFIED, 0
    return STATUS_CONFLICT, 1


# ---------------------------------------------------------------- main
def parse_args(args):
    limit = None
    mock = False
    force = False
    entity = 'place'
    for i in range(len(args)):
        a = args[i]
        if a == '--mock':
            mock = True
        elif a == '--force':
            force = True
        elif a == '--entity' and i + 1 < len(args):
            entity = args[i + 1]
        elif a.startswith('--entity='):
            entity = a.split('=', 1)[1]
        elif a.startswith('--limit='):
            limit = int(a.split('=', 1)[1])
        elif a == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
    if entity not in ('place', 'person'):
        print(f'❌ entity không hợp lệ: {entity} (chỉ place|person)')
        sys.exit(1)
    return entity, limit, mock, force


def main():
    entity, limit, mock, force = parse_args(sys.argv[1:])

    if entity == 'person':
        scope_sql, upsert_sql, sidecar = SCOPE_SQL_PERSON, UPSERT_SQL_PERSON, 'person_groq_audit'
        kind, word, example = 'NHÂN VẬT (people)', 'NHÂN VẬT', 'Nhân vật / tăng đoàn'
        batch_tag = 't170'
    else:
        scope_sql, upsert_sql, sidecar = SCOPE_SQL_PLACE, UPSERT_SQL_PLACE, 'place_groq_audit'
        kind, word, example = 'ĐỊA DANH (places_dila)', 'ĐỊA DANH', 'Địa danh chùa'
        batch_tag = 't169'
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = SYSTEM_PROMPT_TMPL.format(word=word, example=example)

    key, model = resolve_groq_key_model()
    if not mock and not key:
        print('❌ Thiếu GROQ_API_KEY (env) hoặc groq_key (data/llm_config.json). Dùng --mock để test khô.')
        sys.exit(1)

    con = _con()
    has_tbl = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sidecar,)).fetchone()
    if not has_tbl:
        con.close()
        print(f'❌ {sidecar} chưa tồn tại.')
        if entity == 'person':
            print('   Chạy trước: python scripts/t170_entity_groq_audit_migrate.py --apply')
        else:
            print('   Chạy trước: python scripts/t169_place_groq_audit_migrate.py --apply')
        sys.exit(1)
    done = con.execute(f"SELECT COUNT(*) FROM {sidecar}").fetchone()[0]
    con.close()
    if done > 0 and not force:
        print(f'ℹ  Đã có {done:,} hàng audit từ run trước — chạy tiếp các hàng '
              f'pending/conflict/api_error còn lại (verified/approved_dict luôn skip). '
              f'Dùng --force để bỏ thông báo này.')

    run_ts = _ts()
    batch_id = f'{batch_tag}-{run_ts}'
    print(f'🚀 T170 verify — entity={entity} ({kind}) · model={model} · mock={"ON" if mock else "off"} · '
          f'limit={limit or "all"}')
    print(f'   batch_size=25 · rpm-adaptive (≤{LOW_WATERMARK} → {SLEEP_LOW}s, else {SLEEP_OK}s) · '
          f'retries={MAX_RETRIES} · max_tokens={MAX_TOKENS} (R7) · parse trans_vi flat (R6)')

    cursor = '0' if entity == 'place' else ''    # cursor='0' an toàn mọi entity (id THẬT là TEXT 'PL…'; bug ''~0 rows chỉ ở test-harness INTEGER) [T189]
    processed = 0
    stats = {}
    total_prompt_tokens = total_completion_tokens = 0
    window_events = []      # (ts, tokens) cho window 60s
    max_window_tpm = 0
    t_start = time.time()
    use_json_object = True

    while True:
        if limit and processed >= limit:
            break
        with _con() as con:
            rows = con.execute(scope_sql, {'cursor': cursor}).fetchall()
            if not rows:
                break
            for r in rows:
                if limit and processed >= limit:
                    break
                rid = r['id']
                name_zh = r['name_zh']
                dict_vi = r['dict_vi'] or ''
                started_at = _now()

                if entity == 'person':
                    clean_zh, meta_note, variant_zh, uncertain = person_pre(name_zh)
                    pre = (clean_zh, meta_note, variant_zh, uncertain)
                else:
                    pre = None

                if mock:
                    groq_vi = dict_vi
                    parse_note = 'plain(mock)'
                    usage = {'prompt_tokens': 10, 'completion_tokens': 5}
                    rem = None
                    parse_ok = True
                else:
                    res = call_groq(key, model, use_json_object, None)
                    if res.error == 'schema_400':
                        print('  [[ P1-6 ]] response_format json_object bị 400/422 — bỏ response_format cho cả run')
                        use_json_object = False
                        res = call_groq(key, model, use_json_object, None)
                    if res.error:
                        last_error = res.error
                        if entity == 'person':
                            upsert_person(con, rid, name_zh, dict_vi, None, None, *pre, 1,
                                          STATUS_API_ERROR, None, last_error, model, batch_id,
                                          None, None, 0, last_error, started_at, _now())
                        else:
                            upsert_place(con, rid, name_zh, dict_vi, None, 1, STATUS_API_ERROR,
                                         None, last_error, model, batch_id, None, None, _now())
                        stats[STATUS_API_ERROR] = stats.get(STATUS_API_ERROR, 0) + 1
                        processed += 1
                        if not mock:
                            sleep_adaptive(res.remaining_requests)
                        continue
                    groq_vi, parse_ok, parse_note = normalize_groq(res.text)
                    if not parse_ok:
                        # R7 salvage: 1 lần gọi lại khi parse thất bại
                        res2 = call_groq(key, model, use_json_object, res.remaining_requests)
                        if not res2.error:
                            groq_vi, parse_ok, parse_note = normalize_groq(res2.text)
                    if not parse_ok:
                        last_error = parse_note
                        if entity == 'person':
                            upsert_person(con, rid, name_zh, dict_vi, None, None, *pre, 1,
                                          STATUS_API_ERROR, None, last_error, model, batch_id,
                                          None, None, 1, last_error, started_at, _now())
                        else:
                            upsert_place(con, rid, name_zh, dict_vi, None, 1, STATUS_API_ERROR,
                                         None, last_error, model, batch_id, None, None, _now())
                        stats[STATUS_API_ERROR] = stats.get(STATUS_API_ERROR, 0) + 1
                        processed += 1
                        if not mock:
                            sleep_adaptive(res.remaining_requests)
                        continue
                    usage = res2.usage if (not parse_ok and res2 and res2.text) else res.usage
                    rem = res.remaining_requests
                    if parse_ok:
                        print(f'  [{processed+1}] {rid} {name_zh} | dict={dict_vi!r} | '
                              f'groq={groq_vi!r} [{parse_note}]')

                prompt_tok = int(usage.get('prompt_tokens') or 0)
                comp_tok = int(usage.get('completion_tokens') or 0)
                total_prompt_tokens += prompt_tok
                total_completion_tokens += comp_tok
                ts = time.time()
                window_events.append((ts, prompt_tok + comp_tok))
                window_events = [e for e in window_events if ts - e[0] <= 60]
                win_tokens = sum(e[1] for e in window_events)
                max_window_tpm = max(max_window_tpm, win_tokens)

                if entity == 'person':
                    diff_type, reason, hint = classify_person(name_zh, dict_vi, groq_vi)
                else:
                    diff_type, reason, hint = classify_place(name_zh, dict_vi, groq_vi)
                status, needs_review = status_from(diff_type, hint)

                if entity == 'person':
                    final_vi = groq_vi if status not in (STATUS_API_ERROR,) else dict_vi
                    upsert_person(con, rid, name_zh, dict_vi, groq_vi, final_vi, *pre,
                                  needs_review, status, diff_type, reason, model, batch_id,
                                  prompt_tok, comp_tok, 0, None, started_at, _now())
                else:
                    upsert_place(con, rid, name_zh, dict_vi, groq_vi, needs_review, status,
                                 diff_type, reason, model, batch_id, prompt_tok, comp_tok, _now())
                stats[diff_type] = stats.get(diff_type, 0) + 1
                stats[status] = stats.get(status, 0) + 1
                processed += 1

                if not mock:
                    sleep_adaptive(rem)
            if not rows:
                break
            cursor = rows[-1]['id']

    elapsed = max(time.time() - t_start, 1e-6)
    rpm = processed / (elapsed / 60)
    print(f'\n=== RUN XONG (entity={entity} · batch_id={batch_id}) ===')
    print(f'  Processed: {processed:,} · thời gian {elapsed/60:.1f} phút · avg RPM {rpm:.1f}')
    print('  diff_type/status:')
    for k in sorted(stats):
        print(f'    {k}: {stats[k]:,}')
    print(f'  Tokens: prompt {total_prompt_tokens:,} · completion {total_completion_tokens:,} · '
          f'total {total_prompt_tokens + total_completion_tokens:,}')
    print(f'  Window max {max_window_tpm}/60s (TPM {TPM_LIMIT}) '
          f'{"✅ dưới" if max_window_tpm <= TPM_LIMIT else "⚠️ VƯỢT"}')
    print('  Chạy típ: --force để xử lý lại conflict/api_error/pending; verified/approved_dict không bao giờ.')


def upsert_place(con, rid, name_zh, dict_vi, groq_vi, needs_review, status,
                 diff_type, reason, model, batch_id, ptok, ctok, now):
    con.execute(UPSERT_SQL_PLACE, (rid, name_zh, dict_vi, groq_vi, needs_review, status,
                                   diff_type, reason, model, batch_id, ptok, ctok, now))


def upsert_person(con, rid, name_zh, dict_vi, groq_vi, final_vi,
                  clean_zh, meta_note, variant_zh, uncertain,
                  needs_review, status, diff_type, reason, model, batch_id,
                  ptok, ctok, retry_count, last_error, started_at, now):
    con.execute(UPSERT_SQL_PERSON, (rid, name_zh, dict_vi, groq_vi, final_vi,
                                    clean_zh, meta_note, variant_zh, uncertain,
                                    needs_review, status, diff_type, reason, model, batch_id,
                                    ptok, ctok, retry_count, last_error, started_at, now))


if __name__ == '__main__':
    main()