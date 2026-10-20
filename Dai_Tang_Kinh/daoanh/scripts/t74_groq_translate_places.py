# -*- coding: utf-8 -*-
"""
T74 — Place Desc VI: Batch dịch tiếng Việt mô tả địa danh (place_desc_vi_draft)

Bối cảnh (2026-09-28 · BUILD, premise đã audit lại so với T74 SPEC 2026-08-30):
- `place_desc_vi_draft` đã có sẵn (T66): 14.000 rows, `desc_source='dila_note_zh'`,
  `desc_vi_draft` = bản gốc tiếng Hán/Anh từ `places_dila.note`, `admin_approved=0`.
- Script cũ `batch_translate_places.py` dùng **Gemini key chết** (T50: 403/404).
  Project đã chuẩn hoá **Groq qwen/qwen3.8-27b** (T165+ `_t73_call_gemini`).
- => Script này REBUILD: dịch batch 14k row → Việt qua Groq, ghi đè `desc_vi_draft`
  (bản gốc luôn phục hồi được từ `places_dila.note`), đổi `desc_source='t74_groq'`.

Khung directive (tái dùng T169/T170 — đã hardened):
- batch 25 · `:cursor` memory trong 1 run · restart scan từ đầu qua predicate ·
- RPM adaptive (x-ratelimit-remaining-requests ≤5 → 3s, else 2,2s ~27 RPM < 30) ·
- retry 429/5xx/network với backoff · atomic `with con` (Ctrl+C giữ batch đã commit) ·
- mock cho smoke khô · env `T74_DB` override DB (test không đụng DB thật).
- Resume: skip row đã `desc_source='t74_groq'` (không gọi lại API). `--force` bỏ guard này.
- Guard chất lượng: output còn Hán tự (`is_han`) → HUỶ, giữ nguyên bản gốc (api_error 'still_han').

Usage:
    python scripts/t74_groq_translate_places.py --stats                  # trạng thái
    python scripts/t74_groq_translate_places.py --samples=5              # preview mẫu
    python scripts/t74_groq_translate_places.py --dry-run=10             # xem 10 row sẽ xử lý
    python scripts/t74_groq_translate_places.py --mock --limit=5         # smoke khô (temp DB)
    python scripts/t74_groq_translate_places.py --limit=100              # dịch 100 row
    python scripts/t74_groq_translate_places.py                           # dịch toàn bộ (~560 batch)

Revert dữ liệu (khôi phục bản gốc):
    UPDATE place_desc_vi_draft
    SET desc_vi_draft=d.note, desc_source='dila_note_zh', updated_at=datetime('now')
    FROM places_dila d
    WHERE d.id=place_desc_vi_draft.place_id AND place_desc_vi_draft.desc_source='t74_groq';
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

BASE    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('T74_DB') or os.path.join(BASE, '..', 'data', 'lineage.db')
LLM_CFG = os.path.join(BASE, '..', 'data', 'llm_config.json')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
DEFAULT_MODEL = 'qwen/qwen3.8-27b'

try:
    import requests
except Exception:
    requests = None

BATCH_SIZE = 25
MAX_RETRIES = 3
SLEEP_OK = 2.2      # ~27 RPM (dưới trần 30 free tier)
SLEEP_LOW = 3.0     # khi x-ratelimit-remaining-requests <= 5
LOW_WATERMARK = 5
MAX_TOKENS = 2048
MAX_WORDS = 300

TAG_DONE = 't74_groq'
TAG_SRC = 'dila_note_zh'

SYSTEM_PROMPT = (
    'Bạn là chuyên gia Hán-Nôm Phật giáo biên dịch tuyển tập mô tả địa danh '
    'Phật giáo (nguồn DILA). Dịch đoạn mô tả sau sang tiếng Việt học thuật.\n'
    '- Giữ tên riêng địa danh bằng phiên âm Hán-Việt quen thuộc '
    '(vd 少林寺 => "Thiếu Lâm Tự"; 阿育王柱 => "A Dục Vương Trụ").\n'
    '- Giữ nguyên năm tháng, số liệu, đơn vị, tên riêng kinh sách Ấn-Hán.\n'
    '- Bản dịch thuần tiếng Việt: KHÔNG dùng Hán tự, KHÔNG dùng tiếng Anh, '
    'KHÔNG thêm lời bàn, KHÔNG thẻ, KHÔNG JSON.\n'
    '- Ngắn gọn, súc tích, không quá %d từ.' % MAX_WORDS
)

_PROMPT_TMPL = (
    'Tên địa danh: {name_zh} ({name_vi})\n'
    'Loại: {category}\n'
    'Văn bản gốc:\n{note}'
)


def _con():
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


_HAN_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')


def is_han(text):
    """Có chứa Hán tự (CJK) không — dùng guard 'còn Hán = chưa dịch hết'."""
    return bool(_HAN_RE.search(text or ''))


def normalize_vi(text):
    """(vi, ok, note). Bỏ fence ```, bỏ nhãn 'Dịch:'/'Bản dịch:' đầu, dồn khoảng trắng.
    Rỗng → empty; vẫn còn Hán tự → still_han (guard chất lượng)."""
    if not text or not text.strip():
        return None, False, 'empty'
    t = text.strip()
    t = re.sub(r'```(?:text|html|json)?', '', t).strip()
    t = re.sub(r'^\s*(?:Bản dịch|Dịch|Bai dich|Dich)\s*[::]\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+', ' ', t).strip()
    if not t:
        return None, False, 'empty'
    if is_han(t):
        return None, False, 'still_han'
    n_words = len(t.split())
    if n_words > MAX_WORDS + 50:
        return None, False, 'too_long'
    return t, True, 'ok'


def build_prompt(name_zh, name_vi, category, note):
    return _PROMPT_TMPL.format(
        name_zh=name_zh or '', name_vi=name_vi or '',
        category=category or '', note=(note or '')[:4000])


class Result:
    def __init__(self, text=None, usage=None, error=None, remaining_requests=None):
        self.text = text
        self.usage = usage or {}
        self.error = error
        self.remaining_requests = remaining_requests


def call_groq(key, model, prompt, remaining_hint=None):
    """1 request dịch 1 row. Retry 429/5xx/network với backoff (giống T169/T170)."""
    if not requests:
        return Result(error='http_error')
    last_error = 'api_error'
    rem = remaining_hint
    for attempt in range(MAX_RETRIES + 1):
        body = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.1,
            'max_tokens': MAX_TOKENS,
        }
        try:
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                json=body, timeout=120)
        except Exception:
            last_error = 'http_error'
            if attempt < MAX_RETRIES:
                time.sleep(2 * (2 ** attempt))
            continue
        rrl = resp.headers.get('x-ratelimit-remaining-requests')
        rrl_alt = resp.headers.get('x-ratelimit-remaining')
        r = rrl or rrl_alt
        try:
            rem = int(r)
        except Exception:
            pass
        if resp.status_code == 429:
            last_error = 'rate_limit'
            if attempt < MAX_RETRIES:
                time.sleep(4 * (2 ** attempt))
            continue
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
    return Result(error=last_error, remaining_requests=rem)


def sleep_adaptive(remaining_requests):
    if isinstance(remaining_requests, int) and remaining_requests <= LOW_WATERMARK:
        time.sleep(SLEEP_LOW)
    else:
        time.sleep(SLEEP_OK)


# ---------------------------------------------------------------- SQL
SCOPE_SQL = f"""
SELECT pd.place_id, pd.name_zh, pd.name_vi, pd.note_category, pd.desc_vi_draft
FROM place_desc_vi_draft pd
WHERE pd.place_id > :cursor
  AND pd.desc_source = '{TAG_SRC}'
  AND pd.desc_vi_draft IS NOT NULL AND pd.desc_vi_draft != ''
  AND pd.place_id NOT IN (
    SELECT place_id FROM place_desc_vi_draft
    WHERE desc_source = '{TAG_DONE}'
  )
ORDER BY pd.place_id
LIMIT 25
"""

# --force → bỏ guard "đã dịch" (xử lý lại cả t74_groq)
SCOPE_SQL_FORCE = f"""
SELECT pd.place_id, pd.name_zh, pd.name_vi, pd.note_category, pd.desc_vi_draft
FROM place_desc_vi_draft pd
WHERE pd.place_id > :cursor
  AND pd.desc_source != '{TAG_SRC}'
  AND pd.desc_vi_draft IS NOT NULL AND pd.desc_vi_draft != ''
ORDER BY pd.place_id
LIMIT 25
"""

UPDATE_SQL = f"""
UPDATE place_desc_vi_draft
SET desc_vi_draft = ?, desc_source = '{TAG_DONE}', char_count = ?,
    updated_at = ?
WHERE place_id = ? AND desc_source IN ('{TAG_SRC}','{TAG_DONE}')
"""

STATS_SQL = """
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN desc_source='%%' THEN 1 ELSE 0 END) AS done,
  SUM(CASE WHEN desc_source<>'%%' THEN 1 ELSE 0 END) AS pending,
  SUM(CASE WHEN admin_approved=1 THEN 1 ELSE 0 END) AS approved
FROM place_desc_vi_draft
"""


def print_stats(con):
    total, done, pending, approved = con.execute(
        STATS_SQL.replace('%%', TAG_DONE)).fetchone()
    avg_ch = con.execute(
        f"SELECT AVG(char_count) FROM place_desc_vi_draft WHERE desc_source='{TAG_DONE}'"
    ).fetchone()[0]
    print(f'place_desc_vi_draft · total {total:,} · {TAG_SRC} '
          f'(chưa dịch) {pending:,} · {TAG_DONE} (đã dịch) {done:,} · '
          f'admin_approved {approved:,} · avg char {avg_ch:.0f}' if avg_ch is not None
          else f'place_desc_vi_draft · total {total:,} · pending {pending:,} · done {done:,}')
    return int(pending or 0)


def print_samples(con, n=5):
    rows = con.execute(
        f"SELECT place_id, name_vi, name_zh, note_category, desc_vi_draft "
        f"FROM place_desc_vi_draft WHERE desc_source='{TAG_SRC}' "
        f"ORDER BY place_id LIMIT ?", (n,)).fetchall()
    if not rows:
        print('  (không còn row chưa dịch)')
    for r in rows:
        print(f'  [{r["place_id"]}] {r["name_vi"]} ({r["name_zh"]}) · '
              f'{r["note_category"]} · src={str(r["desc_vi_draft"])[:90]}…')


# ---------------------------------------------------------------- main
def parse_args(args):
    opts = {'limit': None, 'mock': False, 'force': False, 'stats': False,
            'samples': 0, 'dry_run': 0}
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--stats':
            opts['stats'] = True
        elif a == '--mock':
            opts['mock'] = True
        elif a == '--force':
            opts['force'] = True
        elif a == '--dry-run':
            opts['dry_run'] = 10
        elif a.startswith('--dry-run='):
            opts['dry_run'] = int(a.split('=', 1)[1])
        elif a.startswith('--samples='):
            opts['samples'] = int(a.split('=', 1)[1])
        elif a == '--samples' and i + 1 < len(args):
            opts['samples'] = int(args[i + 1]); i += 1
        elif a.startswith('--limit='):
            opts['limit'] = int(a.split('=', 1)[1])
        elif a == '--limit' and i + 1 < len(args):
            opts['limit'] = int(args[i + 1]); i += 1
        i += 1
    return opts


def main(argv=None):
    opts = parse_args(sys.argv[1:] if argv is None else argv)

    con = _con()
    has = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='place_desc_vi_draft'"
    ).fetchone()
    if not has:
        con.close()
        print('❌ place_desc_vi_draft chưa tồn tại.')
        sys.exit(1)

    if opts['stats']:
        print_stats(con)
        con.close()
        return 0

    if opts['samples']:
        print_samples(con, opts['samples'])
        con.close()
        return 0

    key, model = resolve_groq_key_model()
    if not opts['mock'] and not key:
        print('❌ Thiếu GROQ_API_KEY (env) hoặc groq_key (data/llm_config.json). '
              'Dùng --mock để test khô.')
        con.close()
        sys.exit(1)

    scope_sql = SCOPE_SQL_FORCE if opts['force'] else SCOPE_SQL

    if opts['dry_run']:
        rows = con.execute(scope_sql.replace('LIMIT 25', f'LIMIT {opts["dry_run"]}'),
                           {'cursor': ''}).fetchall()
        print(f'🚧 DRY-RUN · {len(rows)} row sẽ được dịch '
              f'({"kể cả đã t74_groq" if opts["force"] else "chỉ dila_note_zh"}):')
        for r in rows:
            print(f'  [{r["place_id"]}] {r["name_vi"]} ({r["name_zh"]}) · {r["note_category"]}')
        con.close()
        return 0

    run_ts = _ts()
    if not opts['force']:
        pending = con.execute(
            f"SELECT COUNT(*) FROM place_desc_vi_draft WHERE desc_source='{TAG_SRC}'"
        ).fetchone()[0]
        print(f'ℹ  {TAG_SRC} (chưa dịch): {pending:,} row · {TAG_DONE} luôn skip (chạy --force để lại).')
    print(f'🚀 T74 place-desc VI · model={model} · mock={"ON" if opts["mock"] else "off"} · '
          f'limit={opts["limit"] or "all"} · force={"ON" if opts["force"] else "off"}')
    print(f'   batch_size=25 · rpm-adaptive (≤{LOW_WATERMARK} → {SLEEP_LOW}s, else {SLEEP_OK}s) · '
          f'retries={MAX_RETRIES} · max_tokens={MAX_TOKENS} · guard Hán còn → huỷ')

    cursor = ''
    processed = 0
    stats = {}
    total_pt = total_ct = 0
    t_start = time.time()
    single_pass = opts['force']   # force: 1 vòng duyệt (row vừa update vẫn khớp scope force
                                  #         → cursor-loop sẽ lặp vô hạn, nên chỉ 1 pass + limit)

    while True:
        if opts['limit'] and processed >= opts['limit']:
            break
        with _con() as con:
            rows = con.execute(scope_sql, {'cursor': cursor}).fetchall()
            if not rows:
                break
            for r in rows:
                if opts['limit'] and processed >= opts['limit']:
                    break
                rid = r['place_id']
                name_zh = r['name_zh'] or ''
                name_vi = r['name_vi'] or ''
                category = r['note_category'] or ''
                src = r['desc_vi_draft'] or ''
                prompt = build_prompt(name_zh, name_vi, category, src)

                if opts['mock']:
                    vi = ('Mo ta duoc dich sang tieng Viet tu nguon DILA '
                          '(mock, khong goi API) cho dia danh ' + name_vi).strip()
                    usage = {'prompt_tokens': len(prompt) // 4, 'completion_tokens': len(vi) // 4}
                    rem = None
                else:
                    res = call_groq(key, model, prompt, None)
                    if res.error:
                        print(f'  ✗ [{rid}] api_error: {res.error}')
                        stats['api_error'] = stats.get('api_error', 0) + 1
                        processed += 1
                        sleep_adaptive(res.remaining_requests)
                        continue
                    vi, ok, note = normalize_vi(res.text)
                    if not ok:
                        print(f'  ✗ [{rid}] {name_vi}: {note} (giữ bản gốc)')
                        stats[note] = stats.get(note, 0) + 1
                        processed += 1
                        sleep_adaptive(res.remaining_requests)
                        continue
                    usage = res.usage
                    rem = res.remaining_requests

                con.execute(UPDATE_SQL, (vi, len(vi), _now(), rid))
                stats['translated'] = stats.get('translated', 0) + 1
                total_pt += int(usage.get('prompt_tokens') or 0)
                total_ct += int(usage.get('completion_tokens') or 0)
                processed += 1
                if opts['mock'] or processed <= 5:
                    print(f'  ✓ [{processed}] {rid} {name_vi} → {vi[:90]}')
                if not opts['mock']:
                    sleep_adaptive(rem)
            if single_pass:
                break
            cursor = rows[-1]['place_id']

    elapsed = max(time.time() - t_start, 1e-6)
    print(f'\n=== RUN XONG (T74 · batch {run_ts}) ===')
    print(f'  Processed {processed:,} · {elapsed/60:.1f} phút · '
          f'avg {(processed / (elapsed/60)):.1f} RPM')
    print('  ', ', '.join(f'{k}: {v:,}' for k, v in sorted(stats.items())))
    print(f'  Tokens: prompt {total_pt:,} · completion {total_ct:,}')
    print('  Rerun tiếp: row còn lại tự resume (skip t74_groq). '
          'Revert: UPDATE place_desc_vi_draft SET desc_vi_draft=d.note, '
          'desc_source="dila_note_zh" FROM places_dila d WHERE '
          'd.id=place_desc_vi_draft.place_id AND '
          'place_desc_vi_draft.desc_source="t74_groq".')
    con.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())