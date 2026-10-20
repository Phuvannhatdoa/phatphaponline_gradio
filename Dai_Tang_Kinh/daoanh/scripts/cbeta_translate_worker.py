# -*- coding: utf-8 -*-
"""
T95 Phase C — Worker dịch CBETA per-passage (batch Groq + resume + style-lock)

Module độc lập (KHÔNG import app.py) → dùng được cả từ CLI lẫn thread trong app.py.

Luồng xử lý:
  1) `new-job` tạo translation_jobs + translation_job_items (scope mở rộng, UNIQUE job_id+passage_id).
  2) `worker_run` claim từng item atomic (queued→running), gom batch ≤3 theo sequence_no,
     kèm CONTEXT hàng xóm (read-only) → 1 call Groq → JSON contract → validation gate
     (passage_id khớp lệnh, translation_vi rỗng bị từ chối, tỉ lệ ký tự 0.6–8.0, không echo Hán).
  3) Commit per passage: INSERT translation_segments (provider=groq, source_original_hash,
     prompt_version, model, translation_status='completed', quality_status='unreviewed',
     created_by_job_id) + alignment (segment_full) + raw_response audit JSON.
  4) Resume: skip khi đã có translation FINAL (completed/needs_review/reviewed) cùng hash;
     hash ĐỔI → superseded (cũ → 'superseded', bản mới revision_no+1).
  5) Retry/backoff (2/4/8s, max 3), attempt_count++, sau max → item failed + job.last_error.

Style-lock: glossary `data/glossaries/vi-buddhist.json` + PROMPT_VERSION cố định + model khóa
(mặc định llm_config.groq_model trước, rồi env GROQ_MODEL, rồi mặc định `qwen/qwen3.8-27b`).

Key Groq: env GROQ_API_KEY → llm_config.json groq_key (KHÔNG có key literal trong code).

Usage:
  python scripts/cbeta_translate_worker.py new-job  --work-id T50n2060 --scope untranslated
  python scripts/cbeta_translate_worker.py run      --job <job_id> [--mock] [--limit N]
  python scripts/cbeta_translate_worker.py status   [--job <job_id>] [--work-id T50n2060]
  python scripts/cbeta_translate_worker.py check-key
  python scripts/cbeta_translate_worker.py validate-job --job <job_id>   # T167 Phase 4
  python scripts/cbeta_translate_worker.py revert-job <job_id>

Scope: all | untranslated | page:<loc_ref> | legacy:<passage_id> | n:<count> | ids:<csv>

ROLLBACK bản dịch của 1 job: python scripts/cbeta_translate_worker.py revert-job <job_id>
  (xóa job + items + translation_segments/alignment do job tạo ra mà còn là bản hiện hành)
"""
import json
import os
import re
import sqlite3
import sys
import time
import hashlib
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    import requests
except Exception:  # CLI vẫn dùng được trong mock
    requests = None

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(BASE_DIR, 'data', 'lineage.db')
RAW_DIR    = os.path.join(BASE_DIR, 'data', 'raw_responses')
GLOSS_PATH = os.path.join(BASE_DIR, 'data', 'glossaries', 'vi-buddhist.json')
LLM_CFG    = os.path.join(BASE_DIR, 'data', 'llm_config.json')

PROMPT_VERSION = 't95-batch-cbeta-v1'
GROQ_URL       = 'https://api.groq.com/openai/v1/chat/completions'
DEFAULT_MODEL  = 'qwen/qwen3.8-27b'
TEMP           = 0.1
BATCH_SIZE     = 3
MAX_RETRIES    = 3
# Ngưỡng tỉ lệ ký tự Việt/Hán. Bản gốc 4.0 bị false-negative khi live-test
# T50n2060 0-0484c- (2026-09-05): Hán văn cổ rất cô đọng, bản dịch văn học
# chuẩn đo 4.71–5.84 → nới lên 8.0 (gate chỉ chặn "bài luận dài dòng", echo đã
# được chặn riêng bằng zh_norm(vi)==zh).
RATIO_MIN, RATIO_MAX = 0.6, 8.0

FINAL_STATUS = ('completed', 'needs_review', 'reviewed')

# T167 Phase 3 — quota contract: quota_exhausted ≠ translation failure
QUOTA_EXHAUSTED = 'quota_exhausted'

# Default ruleset cho constitution T167 (sẽ seed sau migration)
DEFAULT_RULESET_ID = 't167-constitution-v1'

_VALIDATOR_MOD = None


def _validator():
    """Load translation_validator (chạy được cả CLI lẫn trong app.py qua importlib).

    Tránh phụ thuộc đường dẫn import: load từ đường dẫn tuyệt đối cạnh worker."""
    global _VALIDATOR_MOD
    if _VALIDATOR_MOD is None:
        import importlib.util
        path = os.path.join(BASE_DIR, 'scripts', 'translation_validator.py')
        spec = importlib.util.spec_from_file_location('translation_validator', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _VALIDATOR_MOD = mod
    return _VALIDATOR_MOD


# ---------------------------------------------------------------- helpers
def _con():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def load_glossary():
    try:
        with open(GLOSS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'version': 0, 'terms': {}}


def llm_key_model():
    """Trả (key, model). Key: env GROQ_API_KEY → llm_config groq_key. Không có → (None, model)."""
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
    return (key or None), model


# ---------------------------------------------------------------- API call
def call_groq(system, user, key, model, retries=MAX_RETRIES, timeout=120):
    """Gọi Groq, trả (text, model_id, error_type). error_type: None ok |
    'key_error' | 'rate_limit' | 'api_error' | 'http_error'."""
    if not requests:
        return None, model, 'http_error'
    last = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                json={'model': model,
                      'messages': [
                          {'role': 'system', 'content': system},
                          {'role': 'user', 'content': user},
                      ],
                      'temperature': TEMP, 'max_tokens': 2048},
                timeout=timeout)
        except Exception as e:
            last = ('http_error', str(e)[:120])
            if attempt < retries:
                time.sleep(2 * (2 ** attempt))
            continue
        if resp.status_code in (401, 403):
            return None, model, 'key_error'
        if resp.status_code == 429:
            last = ('rate_limit', f'HTTP {resp.status_code}')
            if attempt < retries:
                time.sleep(4 * (2 ** attempt))
            continue
        if resp.status_code != 200:
            last = ('api_error', f'HTTP {resp.status_code} {resp.text[:120]}')
            if attempt < retries:
                time.sleep(2 * (2 ** attempt))
            continue
        try:
            data = resp.json()
        except Exception:
            last = ('api_error', 'response not json')
            continue
        if data.get('choices'):
            text = data['choices'][0]['message'].get('content') or ''
            return text.strip(), model, None
        last = ('api_error', str(data.get('error', 'unknown'))[:120])
    return None, model, last[0] if last else 'api_error'


# ---------------------------------------------------------------- parse/validate
def parse_batch_response(text):
    """Trích JSON array [{passage_id, translation_vi}] từ text mô hình.
    Trả list dict hoặc None (không parse được)."""
    if not text:
        return None
    text = re.sub(r'```(?:json)?', '', text).strip()
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    # fallback: từng object rời
    out = []
    for obj in re.finditer(r'\{[^{}]*"passage_id"[^{}]*"translation_vi"[^{}]*\}', text, re.DOTALL):
        try:
            item = json.loads(obj.group(0))
            out.append(item)
        except Exception:
            pass
    return out or None


def zh_norm(s):
    return re.sub(r'\s+', '', s or '')


def validate_unit(zh, vi):
    zh = zh_norm(zh)
    vi = (vi or '').strip()
    if not vi:
        return False, 'translation_vi rỗng'
    if not zh:
        return False, 'passage rỗng'
    if zh_norm(vi) == zh:
        return False, 'echo nguyên văn Hán (mô hình chưa dịch)'
    ratio = len(vi) / len(zh)
    if not (RATIO_MIN <= ratio <= RATIO_MAX):
        return False, f'tỉ lệ ký tự {ratio:.2f} ngoài khoảng [{RATIO_MIN}-{RATIO_MAX}]'
    return True, ''


# ---------------------------------------------------------------- DB: scope
def expand_scope(con, work_id, scope='untranslated'):
    scope = (scope or 'untranslated').strip()
    base = 'SELECT passage_id FROM text_passages WHERE work_id=?'
    if scope.startswith('page:'):
        return con.execute(base + " AND loc_ref=?", (work_id, scope[len('page:'):])).fetchall()
    if scope.startswith('legacy:'):
        return con.execute(base + " AND legacy_passage_id=?", (work_id, int(scope[len('legacy:'):]))).fetchall()
    if scope.startswith('ids:'):
        ids = [x.strip() for x in scope[len('ids:'):].split(',') if x.strip()]
        return [{'passage_id': x} for x in ids if any(r['passage_id'] == x for r in
                con.execute(base, (work_id,)).fetchall())]
    if scope.startswith('n:'):
        return con.execute(base + " ORDER BY sequence_no LIMIT ?", (work_id, int(scope[len('n:'):]))).fetchall()
    if scope in ('all', 'untranslated'):
        sql = base
        if scope == 'untranslated':
            sql += (" AND passage_id NOT IN (SELECT DISTINCT ts.passage_id FROM translation_segments ts "
                    "WHERE ts.passage_id IN (SELECT passage_id FROM text_passages WHERE work_id=?) "
                    "AND ts.translation_status IN ('completed','needs_review','reviewed'))")
            return con.execute(sql, (work_id, work_id)).fetchall()
        return con.execute(sql, (work_id,)).fetchall()
    raise ValueError(f'Scope không hợp lệ: {scope}')


# ---------------------------------------------------------------- DB: job
def create_job(work_id, scope='untranslated', provider='groq', model=None, requested_by=None):
    con = _con()
    items = expand_scope(con, work_id, scope)
    if not items:
        con.close()
        print('Không có passage nào khớp scope.'); return None
    job_id = f'job-{work_id}-{datetime.now().strftime("%Y%m%d_%H%M%S%f")}'
    _m = model or llm_key_model()[1]
    con.execute(
        "INSERT INTO translation_jobs (job_id, work_id, requested_scope, requested_by_user_id, "
        "provider, model_name, status, total_passages, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,'queued',?,?,?)",
        (job_id, work_id, scope, requested_by, provider, _m, len(items), _now(), _now()))
    con.executemany(
        "INSERT OR IGNORE INTO translation_job_items "
        "(job_item_id, job_id, passage_id, sequence_no, status, created_at) "
        "SELECT ? || ':' || seq_no, ?, passage_id, seq_no, 'queued', ? "
        "FROM (SELECT passage_id, ROW_NUMBER() OVER (ORDER BY sequence_no) AS seq_no "
        "      FROM (SELECT passage_id, sequence_no FROM text_passages WHERE work_id=?) w "
        "      WHERE passage_id IN (SELECT value FROM json_each(?)))",
        [(job_id, job_id, _now(), work_id, json.dumps([r['passage_id'] for r in items]))])
    con.commit()
    n_items = con.execute('SELECT COUNT(*) FROM translation_job_items WHERE job_id=?', (job_id,)).fetchone()[0]
    con.close()
    print(f'Job tạo: {job_id} — {n_items} item (' + scope + f'), model {_m}')
    return job_id


def _current_translation(con, passage_id, zh_hash):
    """Trả (mode, info): 'skip' nếu đã có bản FINAL cùng hash; 'revise' nếu bản
    FINAL khác hash; 'new' nếu chưa. info=(translation_id, revision_no)."""
    row = con.execute(
        "SELECT translation_id, source_original_hash, revision_no, translation_status "
        "FROM translation_segments WHERE passage_id=? "
        "ORDER BY revision_no DESC, created_at DESC LIMIT 1", (passage_id,)).fetchone()
    if not row:
        return 'new', None
    if row['translation_status'] in FINAL_STATUS:
        if row['source_original_hash'] == zh_hash:
            return 'skip', (row['translation_id'], row['revision_no'])
        return 'revise', (row['translation_id'], row['revision_no'])
    return 'new', None


def commit_translation(con, job_id, work_id, item, passage, vi, model, raw_path, ruleset_id=DEFAULT_RULESET_ID):
    """INSERT translation_segments + alignment. Trả translation_id."""
    src_hash = passage['raw_zh_hash']
    mode, cur = _current_translation(con, item['passage_id'], src_hash)
    if mode == 'skip':
        return None, 'skip'
    rev = (cur[1] if cur else 0) + 1
    if cur:
        con.execute(
            "UPDATE translation_segments SET translation_status='superseded', updated_at=? "
            "WHERE translation_id=?", (_now(), cur[0]))
    seq = passage['sequence_no']
    tid = f'cbeta:{work_id}:t{seq:06d}:r{rev:03d}'
    con.execute(
        "INSERT INTO translation_segments "
        "(translation_id, work_id, language, translation_text, translator_type, model_name, "
        " prompt_version, source_passage_ids, translation_status, review_status, "
        " created_at, updated_at, passage_id, provider, source_original_hash, "
        " quality_status, created_by_job_id, revision_no, supersedes_translation_id, ruleset_id) "
        "VALUES (?,?,'vi',?,?,?,?,?,'completed','pending',?,?,?,'groq',?, 'unreviewed', ?, ?, ?, ?)",
        (tid, work_id, vi, 'ai', model, PROMPT_VERSION, item['passage_id'],
         _now(), _now(), item['passage_id'], src_hash, job_id, rev,
         cur[0] if cur and mode == 'revise' else None, ruleset_id))
    con.execute(
        "INSERT INTO passage_translation_alignment "
        "(passage_id, translation_id, alignment_type, source_start_offset, source_end_offset, "
        " confidence, alignment_method, review_status, created_at, updated_at, note) "
        "VALUES (?,?,'segment_full',NULL,NULL,1.0,'batch_json_match','pending',?,?,'t95')",
        (item['passage_id'], tid, _now(), _now()))
    return tid, 'committed'


# ---------------------------------------------------------------- raw audit
def _raw_safe(name):
    # item_id dạng `job-...:1` chứa `:` — trên Windows/NTFS `:` là cú pháp
    # Alternate Data Stream (ADS): tạo file 0 byte thấy được qua listdir, còn
    # nội dung nằm trong stream vô hình → audit bị đếm sai (latent bug Phase C).
    # Thay `:` → `_` để tạo file thật, đọc được bằng listdir ở mọi OS.
    return (name or '').replace(':', '_')


def save_raw(job_id, item_id, request_data, response_dict):
    d = os.path.join(RAW_DIR, job_id)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f'{_raw_safe(item_id)}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'ts': _now(), 'request': request_data, 'response': response_dict},
                  f, ensure_ascii=False, indent=2)
    return path


# ---------------------------------------------------------------- worker loop
def worker_run(job_id, mock=False, max_items=None, profile=True):
    con = _con()
    job = con.execute("SELECT * FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
    if not job:
        con.close(); print(f'Không tìm thấy job {job_id}'); return
    if job['status'] == 'completed':
        con.close(); print('Job đã hoàn thành trước đó — bỏ qua.'); return
    con.execute("UPDATE translation_jobs SET status='running', started_at=COALESCE(started_at,?), updated_at=? WHERE job_id=?",
                (_now(), _now(), job_id))
    con.commit()
    key, model = llm_key_model()
    if not key and not mock:
        print('❌ Thiếu GROQ_API_KEY (env) hoặc groq_key (data/llm_config.json). Dùng --mock để test khô.')
        con.execute("UPDATE translation_jobs SET status='paused', last_error='key_error: thiếu GROQ key', updated_at=? WHERE job_id=?", (_now(), job_id))
        con.commit(); con.close(); return

    glossary = load_glossary()
    terms = glossary.get('terms', {})
    work_id = job['work_id']
    done = failed = 0
    processed_this_session = 0
    batch_no = 0

    while True:
        if max_items and processed_this_session >= max_items:
            break
        rows = con.execute(
            "SELECT i.job_item_id, i.passage_id, i.sequence_no FROM translation_job_items i "
            "WHERE i.job_id=? AND i.status IN ('queued','running') "
            "ORDER BY i.sequence_no LIMIT ?", (job_id, BATCH_SIZE)).fetchall()
        if not rows:
            break
        # claim atomic
        claimed = []
        for r in rows:
            c = con.execute("UPDATE translation_job_items SET status='running', attempt_count=attempt_count+1, started_at=? "
                            "WHERE job_item_id=? AND status IN ('queued','running')", (_now(), r['job_item_id']))
            if c.rowcount:
                claimed.append(r)
        if not claimed:
            break
        batch_no += 1
        print(f'── Batch {batch_no}: {len(claimed)} item (mock={mock})')

        # lấy nội dung + context hàng xóm
        passages = {}
        for r in claimed:
            p = con.execute(
                "SELECT passage_id, original_zh, raw_zh_hash, sequence_no FROM text_passages WHERE passage_id=?",
                (r['passage_id'],)).fetchone()
            if p:
                passages[r['passage_id']] = dict(p)
        if not passages:
            for r in claimed:
                con.execute("UPDATE translation_job_items SET status='failed', error_message='passage không tồn tại', completed_at=? WHERE job_item_id=?", (_now(), r['job_item_id']))
            con.commit(); continue

        order = [r['passage_id'] for r in claimed if r['passage_id'] in passages]
        payload_lines = [f'BATCH:{len(order)}']
        for pid in order:
            p = passages[pid]
            prev_ = con.execute("SELECT original_zh FROM text_passages WHERE work_id=? AND sequence_no=?",
                                (work_id, p['sequence_no'] - 1)).fetchone()
            next_ = con.execute("SELECT original_zh FROM text_passages WHERE work_id=? AND sequence_no=?",
                                (work_id, p['sequence_no'] + 1)).fetchone()
            payload_lines.append(f'#ITEM {pid} | seq {p["sequence_no"]}')
            payload_lines.append('#PREV_CONTEXT(ReadOnly): ' + (prev_['original_zh'] if prev_ else ''))
            payload_lines.append('#NEXT_CONTEXT(ReadOnly): ' + (next_['original_zh'] if next_ else ''))
            payload_lines.append(p['original_zh'])
        user_payload = '\n'.join(payload_lines)

        system = build_system_prompt(terms)
        req_snapshot = {'system_hash_maxlen': 120, 'model': model, 'prompt_version': PROMPT_VERSION,
                        'payload': user_payload}

        # gọi LLM
        if mock:
            items = []
            for pid in order:
                p = passages[pid]
                seed = p['original_zh']
                items.append({'passage_id': pid,
                              'translation_vi': f'Bản dịch nháp (mock) — {zh_norm(seed)[:40]}…（nháp dịch thử、chưa duyệt）'})
            parsed, err_type = items, None
        else:
            parsed, err_type = None, None
            for _try in range(MAX_RETRIES + 1):
                text, model, err_type = call_groq(system, user_payload, key, model)
                if not text:
                    break
                parsed = parse_batch_response(text)
                if isinstance(parsed, list) and parsed:
                    break
                err_type = 'api_error' if not parsed else 'validation'
                if _try < MAX_RETRIES:
                    time.sleep(2 * (2 ** _try))

        # T167 Phase 3: quota_exhausted handling — rate_limit hết retry ≠ translation failure
        quota_exhausted_this_batch = False
        if not parsed and err_type == 'rate_limit':
            quota_exhausted_this_batch = True
            for r in claimed:
                con.execute("UPDATE translation_job_items SET status=?, error_message=?, completed_at=? WHERE job_item_id=?",
                            (QUOTA_EXHAUSTED, 'rate_limit: quota exhausted after max retries', _now(), r['job_item_id']))
            con.commit()
            print(f'    ⏸ Batch {batch_no}: quota_exhausted (rate_limit), {len(claimed)} items paused')
            # break out of worker loop entirely — job will be paused with quota_exhausted
            break

        out_map = {o.get('passage_id'): o.get('translation_vi', '') for o in (parsed or [])}
        for r in claimed:
            pid = r['passage_id']
            vi = out_map.get(pid, '')
            ok, reason = validate_unit(passages[pid]['original_zh'], vi)
            if not ok:
                fresh = con.execute("SELECT attempt_count FROM translation_job_items WHERE job_item_id=?",
                                    (r['job_item_id'],)).fetchone()
                if fresh and fresh['attempt_count'] <= MAX_RETRIES:
                    con.execute("UPDATE translation_job_items SET status='queued', error_message=? WHERE job_item_id=?",
                                (f'tạm fail: {reason}', r['job_item_id']))
                    continue
                con.execute("UPDATE translation_job_items SET status='failed', error_message=?, completed_at=? WHERE job_item_id=?",
                            (reason, _now(), r['job_item_id']))
                failed += 1
                continue
            raw_path = save_raw(job_id, r['job_item_id'],
                                req_snapshot, {'parsed': parsed})
            # re-check existing (giữa chừng có thể có job khác dịch rồi)
            mode, cur = _current_translation(con, pid, passages[pid]['raw_zh_hash'])
            if mode == 'skip':
                con.execute("UPDATE translation_job_items SET status='completed', completed_at=?, error_message='already_translated' WHERE job_item_id=?", (_now(), r['job_item_id']))
                continue
            tid, status = commit_translation(con, job_id, work_id, {'passage_id': pid}, passages[pid], vi, model, raw_path, ruleset_id=DEFAULT_RULESET_ID)
            con.execute("UPDATE translation_job_items SET status='completed', raw_response_path=?, completed_at=? WHERE job_item_id=?",
                        (raw_path, _now(), r['job_item_id']))
            if status == 'committed':
                done += 1
                print(f'    ✅ {pid} → {tid} ({len(vi)} chữ)')
                # T166 §8.7 — identity guard (post_check) cho passage batch.
                # Worker KHÔNG đụng translation_cache (SPEC thực tế: viết
                # translation_segments) ⇒ identity ghi vào validation_report +
                # hạ translation_status='needs_review' khi có issue → Admin duyệt.
                try:
                    import canonical_lock as _t166_cl
                    ires = _t166_cl.post_check_translation(
                        con, passages[pid]['original_zh'], vi)
                    if ires['identity_status'] != 'pass':
                        con.execute(
                            "UPDATE translation_segments SET translation_status='needs_review', "
                            "validation_status='REVIEW', validation_report=?, updated_at=? "
                            "WHERE translation_id=?",
                            (json.dumps({
                                'identity': ires['identity_issues'],
                                'identity_lock_hash': ires['identity_lock_hash'],
                            }, ensure_ascii=False), _now(), tid))
                    elif ires['identity_issues']:
                        # issue WARN vẫn pass (không chặn) nhưng ghi chú auditable
                        con.execute(
                            "UPDATE translation_segments SET validation_report=?, updated_at=? "
                            "WHERE translation_id=?",
                            (json.dumps({'identity': ires['identity_issues'],
                                         'identity_lock_hash': ires['identity_lock_hash'],
                                         }, ensure_ascii=False), _now(), tid))
                except Exception as ive:
                    print(f'        └ t166 guard skip: {str(ive)[:100]}')
                # T167 Phase 4 — validator deterministic (A–G) → ghi kết quả auditable, KHÔNG rewrite
                try:
                    vres = _validator().validate_translation(tid, con)
                    con.execute(
                        "UPDATE translation_segments SET validation_status=?, validation_report=?, validated_at=? "
                        "WHERE translation_id=?",
                        (vres.get('overall', 'FAIL'), json.dumps(vres, ensure_ascii=False), _now(), tid))
                    print(f'        └ validator: {vres.get("overall", "FAIL")} '
                          f'({len(vres.get("layers", []))} layers)')
                except Exception as ve:
                    con.execute(
                        "UPDATE translation_segments SET validation_status='FAIL', validation_report=?, validated_at=? "
                        "WHERE translation_id=?",
                        (json.dumps({'error': f'validator crash: {str(ve)[:200]}'}, ensure_ascii=False), _now(), tid))
                    print(f'        └ validator: FAIL (crash: {str(ve)[:120]})')
        con.commit()

        processed_this_session += len(claimed)
        time.sleep(0.2)

    # finalize
    remaining = con.execute("SELECT COUNT(*) FROM translation_job_items WHERE job_id=? AND status IN ('queued','running','failed',?)", (job_id, QUOTA_EXHAUSTED)).fetchone()[0]
    failed_n = con.execute("SELECT COUNT(*) FROM translation_job_items WHERE job_id=? AND status='failed'", (job_id,)).fetchone()[0]
    quota_n = con.execute("SELECT COUNT(*) FROM translation_job_items WHERE job_id=? AND status=?", (job_id, QUOTA_EXHAUSTED)).fetchone()[0]
    total = job['total_passages']
    if quota_n > 0:
        final_status = QUOTA_EXHAUSTED
    elif remaining == 0:
        final_status = 'completed'
    else:
        final_status = 'paused'
    con.execute("UPDATE translation_jobs SET status=?, completed_passages=?, failed_passages=?, "
                "finished_at=CASE WHEN ?='completed' THEN ? ELSE finished_at END, updated_at=? WHERE job_id=?",
                (final_status, done, failed_n, final_status, _now(), _now(), job_id))
    con.commit()
    con.close()
    print(f'Kết thúc {job_id}: completed {done}, failed {failed_n}, quota_exhausted {quota_n}, trạng thái {final_status}')


def build_system_prompt(terms):
    gloss_txt = '\n'.join(f'- {k} → {v}' for k, v in terms.items()) if terms else '(trống)'
    return (
        "Bạn là dịch giả Phật học chuyên nghiệp (Hán → Việt, Cao Tăng Truyện / CBETA).\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1) Dịch TỪNG #ITEM (BATCH) sang tiếng Việt văn hoa, đúng nghĩa thuật ngữ Phật học.\n"
        "2) #PREV_CONTEXT / #NEXT_CONTEXT chỉ để THAM KHẢO ngữ cảnh — KHÔNG dịch, KHÔNG đưa vào kết quả.\n"
        "3) Dùng ĐÚNG bản dịch glossary nếu thuật ngữ xuất hiện:\n"
        f"{gloss_txt}\n"
        "4) Chỉ xuất ra ĐÚNG 1 mảng JSON, không giải thích, không markdown:\n"
        "[{\"passage_id\": \"<id gốc y nguyên>\", \"translation_vi\": \"<bản dịch>\"}, ...]\n"
        "5) Mỗi passage_id trong BATCH PHẢI xuất hiện ĐÚNG 1 lần, id giữ Y NGUYÊN."
    )


# ---------------------------------------------------------------- CLI commands
def cmd_new_job(args):
    work_id = args.get('--work-id', 'T50n2060')
    scope = args.get('--scope', 'untranslated')
    return create_job(work_id, scope=scope, model=args.get('--model'))


def cmd_run(args):
    job_id = args.get('--job')
    mock = '--mock' in sys.argv[1:]
    limit = int(args.get('--limit') or 0)
    if not job_id:
        work_id = args.get('--work-id', 'T50n2060')
        scope = args.get('--scope', 'untranslated')
        job_id = create_job(work_id, scope=scope)
    if job_id:
        worker_run(job_id, mock=mock, max_items=limit or None)


def cmd_status(args):
    con = _con()
    job_id = args.get('--job')
    work_id = args.get('--work-id')
    sql = "SELECT * FROM translation_jobs"
    params = ()
    if job_id:
        sql += ' WHERE job_id=?'; params = (job_id,)
    elif work_id:
        sql += ' WHERE work_id=? ORDER BY created_at DESC'; params = (work_id,)
    else:
        sql += ' ORDER BY created_at DESC LIMIT 10'
    for j in con.execute(sql, params).fetchall():
        print(f'{j["job_id"]} | {j["work_id"]} | {j["status"]} | {j["completed_passages"]}/{j["total_passages"]} | fail {j["failed_passages"]} | {j["requested_scope"]}')
    con.close()


def cmd_check_key():
    key, model = llm_key_model()
    if key:
        print(f'✅ Key Groq có sẵn (env hoặc llm_config) — model {model}')
    else:
        print(f'❌ Chưa có GROQ_API_KEY env / groq_key trong data/llm_config.json — model {model}')


def cmd_validate_job(job_id):
    """T167 Phase 4 — validate toàn bộ translation committed của 1 job, ghi kết quả vào DB."""
    con = _con()
    segs = con.execute(
        "SELECT ts.translation_id FROM translation_segments ts "
        "WHERE ts.created_by_job_id=? AND ts.translation_status <> 'superseded'",
        (job_id,)).fetchall()
    if not segs:
        print(f'{job_id}: không có segment nào (chưa dịch).'); con.close(); return
    print(f'Validate {job_id}: {len(segs)} segment...')
    cnt = {'PASS': 0, 'REVIEW': 0, 'FAIL': 0}
    for s in segs:
        tid = s['translation_id']
        try:
            vres = _validator().validate_translation(tid, con)
            v_s = vres.get('overall', 'FAIL')
            cnt[v_s] = cnt.get(v_s, 0) + 1
            con.execute(
                "UPDATE translation_segments SET validation_status=?, validation_report=?, validated_at=? "
                "WHERE translation_id=?",
                (v_s, json.dumps(vres, ensure_ascii=False), _now(), tid))
        except Exception as ve:
            cnt['FAIL'] += 1
            con.execute(
                "UPDATE translation_segments SET validation_status='FAIL', validation_report=?, validated_at=? "
                "WHERE translation_id=?",
                (json.dumps({'error': f'validator crash: {str(ve)[:200]}'}, ensure_ascii=False), _now(), tid))
    con.commit()
    con.close()
    print(f'✅ {job_id}: PASS {cnt["PASS"]} · REVIEW {cnt["REVIEW"]} · FAIL {cnt["FAIL"]}')


def cmd_revert_job(job_id):
    con = _con()
    j = con.execute("SELECT job_id, work_id FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
    if not j:
        print('Không tìm thấy job.'); con.close(); return
    print(f'REVERT {job_id}: xóa job + item + bản dịch do job tạo (chỉ bản còn hiện hành).')
    print('Tiếp tục? [y/N]', end=' ')
    if input().strip().lower() != 'y':
        print('Đã hủy.'); con.close(); return
    # chỉ xóa translation mà job là bản hiện hành (không bị bản sau supersede)
    cur = con.execute(
        "SELECT ts.translation_id FROM translation_segments ts WHERE ts.created_by_job_id=? AND "
        "ts.translation_status NOT IN ('superseded')", (job_id,))
    tids = [r['translation_id'] for r in cur.fetchall()]
    for tid in tids:
        con.execute("DELETE FROM passage_translation_alignment WHERE translation_id=?", (tid,))
    con.executemany("DELETE FROM translation_segments WHERE translation_id=?", [(t,) for t in tids])
    con.execute("DELETE FROM translation_job_items WHERE job_id=?", (job_id,))
    con.execute("DELETE FROM translation_jobs WHERE job_id=?", (job_id,))
    con.commit()
    con.close()
    print(f'✅ Revert {job_id}: xóa {len(tids)} bản dịch.')


def main(argv):
    args = {'--work-id': None, '--scope': None, '--job': None, '--model': None, '--limit': None}
    for i, a in enumerate(argv):
        if a in args and i + 1 < len(argv):
            args[a] = argv[i + 1]
    flags = set(argv)
    if 'new-job' in flags:
        cmd_new_job(args)
    elif 'run' in flags:
        cmd_run(args)
    elif 'status' in flags:
        cmd_status(args)
    elif 'check-key' in flags:
        cmd_check_key()
    elif 'validate-job' in flags:
        cmd_validate_job(args.get('--job'))
    elif 'revert-job' in flags:
        cmd_revert_job(args.get('--job'))
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])