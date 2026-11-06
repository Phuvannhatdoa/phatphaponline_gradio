# -*- coding: utf-8 -*-
"""
T514 việc 2 — Dịch text_zh của dila_bio_nexus sang tiếng Việt bằng Gemini API
(free tier), ghi staging JSONL, CÓ quota-guard + checkpoint.

NGUYÊN TẮC BẮT BUỘC (xem tasks/T514 + CLAUDE.md daoanh):
- CHỈ ĐỌC DB (SELECT, mode=ro ở mức URI SQLite). KHÔNG UPDATE/INSERT/DELETE
  vào dila_bio_nexus hay bất kỳ bảng nào khác.
- Zero-RAM: dùng generator/cursor streaming qua SELECT, KHÔNG fetchall() toàn
  bộ sách vào RAM.
- GEMINI_API_KEY đọc từ .env (cùng thư mục daoanh/), KHÔNG BAO GIỜ in ra
  log/stdout/stderr/exception message.
- Khi gặp lỗi quota/rate-limit (HTTP 429 hoặc quotaId theo ngày) → DỪNG NGAY,
  ghi checkpoint (offset/nexus_id cuối đã xử lý THÀNH CÔNG) để lần sau chạy
  tiếp đúng từ đó, KHÔNG chạy lại từ đầu, KHÔNG dịch lại nexus đã có trong
  JSONL.
- Output JSONL ghi vào:
    data/dila_import/biographies.2024-01/vn_translate/<book>/batch_<ts>.jsonl
  (tạo thư mục nếu chưa có). Mỗi dòng JSONL tối thiểu gồm:
    {nexus_id, text_vi, model, timestamp}
  (script này ghi thêm text_zh, book để tab UI T514 hiển thị cột Gemini mà
  không phải mở lại DB).

Usage:
    python scripts/t514_gemini_translate_nexus.py --book Mingsengzhuanchao --dry-run
    python scripts/t514_gemini_translate_nexus.py --book Mingsengzhuanchao --limit 50 --max-requests 20
    python scripts/t514_gemini_translate_nexus.py --book Mingsengzhuanchao --self-test
"""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DAOANH_DIR = os.path.join(BASE, '..')
DB_PATH = os.path.join(DAOANH_DIR, 'data', 'lineage.db')
ENV_PATH = os.path.join(DAOANH_DIR, '.env')
VN_TRANSLATE_ROOT = os.path.join(
    DAOANH_DIR, 'data', 'dila_import', 'biographies.2024-01', 'vn_translate'
)

MODEL = 'gemini-3.8-flash'
GEMINI_URL_TMPL = (
    'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
)
BATCH_SIZE_DEFAULT = 5
MAX_RETRIES = 3
MAX_CONSEC_ERRORS = 5
SLEEP_OK = 6.5
SLEEP_AFTER_429 = 20.0
MAX_REQUESTS_HARD_CAP = 50   # việc 5 pilot bị khoá cứng ở 50 nexus — script này
                             # không tự vượt số request tương ứng dù CLI truyền gì lớn hơn.

ID_MARKER_RE = re.compile(r'\[\[ID:([^\]]+)\]\]')
SECRET_KEY_QS_RE = re.compile(r'(key=)[^&\s"\'\\]+', re.IGNORECASE)

try:
    import requests
except Exception:
    requests = None


def mask_secrets(text, key=None):
    """Che giá trị key thực và mọi pattern 'key=...' trước khi ghi ra bất kỳ
    chuỗi lỗi/log nào — KHÔNG BAO GIỜ để lộ GEMINI_API_KEY."""
    if not text:
        return text
    masked = str(text)
    if key:
        masked = masked.replace(key, '***')
    masked = SECRET_KEY_QS_RE.sub(r'\1***', masked)
    return masked


def load_env(path):
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def resolve_gemini_key():
    key = os.environ.get('GEMINI_API_KEY')
    if key:
        return key
    return load_env(ENV_PATH).get('GEMINI_API_KEY', '')


def iter_nexus_rows(book, db_path=DB_PATH):
    """Generator — streaming qua cursor, KHÔNG fetchall(). Mở DB ở mode=ro
    (read-only thật ở mức SQLite URI, không chỉ ở mức ứng dụng)."""
    uri = f'file:{os.path.abspath(db_path)}?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    try:
        cur = conn.execute(
            "SELECT nexus_id, text_zh, seq FROM dila_bio_nexus "
            "WHERE book = ? ORDER BY seq",
            (book,)
        )
        for nexus_id, text_zh, seq in cur:
            yield nexus_id, text_zh, seq
    finally:
        conn.close()


def book_dir(book):
    return os.path.join(VN_TRANSLATE_ROOT, book)


def checkpoint_path(book):
    return os.path.join(book_dir(book), '_checkpoint.json')


def load_checkpoint(book):
    path = checkpoint_path(book)
    if not os.path.isfile(path):
        return {'last_seq_done': 0, 'last_nexus_id': None, 'quota_exhausted': None}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'last_seq_done': 0, 'last_nexus_id': None, 'quota_exhausted': None}


def save_checkpoint(book, data):
    os.makedirs(book_dir(book), exist_ok=True)
    path = checkpoint_path(book)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def existing_done_ids(book):
    """Quét TẤT CẢ batch_*.jsonl đã có của sách này -> set nexus_id đã dịch,
    để KHÔNG dịch lại (resume đúng nghĩa, không chạy lại từ đầu)."""
    done = set()
    bdir = book_dir(book)
    if not os.path.isdir(bdir):
        return done
    for fp in sorted(glob.glob(os.path.join(bdir, 'batch_*.jsonl'))):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    nid = obj.get('nexus_id')
                    if nid:
                        done.add(nid)
        except OSError:
            continue
    return done


PROMPT_HEADER = (
    'Dich cac doan Han van tieu su Phat giao sau sang tieng Viet hoc thuat, '
    'dung phien am Han-Viet chuan cho ten rieng/dia danh, giu nguyen nien hieu, '
    'nam thang, so lieu.\n'
    'QUY TAC TRA LOI BAT BUOC:\n'
    '- Co dung {n} doan duoi day, moi doan bat dau bang mot dong rieng ghi ma '
    'dinh danh dang [[ID:...]], giu nguyen ma nay, khong dich, khong doi ky tu.\n'
    '- Tra loi lai DUNG {n} dong ma dinh danh theo dung thu tu, moi ma theo sau '
    'boi ban dich tuong ung.\n'
    '- Khong gop, khong bo sot, khong them doan nao khac ngoai {n} ma da cho.\n'
    '- Chi tra ve ban dich, khong loi ban, khong dung chu Han, khong dung '
    'markdown/JSON.\n\n'
)


def build_prompt(items):
    """items: list of (nexus_id, text_zh)."""
    parts = [PROMPT_HEADER.format(n=len(items))]
    for nexus_id, text_zh in items:
        parts.append(f'[[ID:{nexus_id}]]\n{text_zh or ""}\n\n')
    return ''.join(parts)


def parse_response(text, expected_ids):
    result = {}
    if not text:
        return result
    expected_set = set(expected_ids)
    matches = list(ID_MARKER_RE.finditer(text))
    for idx, m in enumerate(matches):
        found_id = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if found_id not in expected_set or not content or found_id in result:
            continue
        result[found_id] = content
    return result


class ApiResult:
    def __init__(self, text=None, error=None, daily_quota_exceeded=False,
                 quota_id=None, finish_reason=None):
        self.text = text
        self.error = error
        self.daily_quota_exceeded = daily_quota_exceeded
        self.quota_id = quota_id
        self.finish_reason = finish_reason


def _extract_text(data):
    cands = data.get('candidates')
    if not cands:
        return None
    parts = (cands[0].get('content') or {}).get('parts') or []
    texts = [p.get('text', '') for p in parts if isinstance(p, dict) and p.get('text')]
    return ''.join(texts).strip() if texts else None


def _detect_daily_quota(resp_text):
    if not resp_text:
        return False, None
    m = re.search(r'"quotaId"\s*:\s*"([^"]+)"', resp_text)
    if m and 'PerDay' in m.group(1):
        return True, m.group(1)
    if 'GenerateRequestsPerDayPerProjectPerModel' in resp_text:
        return True, 'GenerateRequestsPerDayPerProjectPerModel'
    return False, None


def call_gemini(key, prompt, model=MODEL):
    if not requests:
        return ApiResult(error='requests_not_available')
    url = GEMINI_URL_TMPL.format(model=model)
    headers = {'x-goog-api-key': key, 'Content-Type': 'application/json'}
    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 4096, 'temperature': 0.1},
    }
    last_err = 'unknown'
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=90)
        except Exception as e:
            last_err = mask_secrets(f'http_error: {e}', key)
            time.sleep(2 * (2 ** attempt))
            continue
        if resp.status_code == 429:
            is_daily, quota_id = _detect_daily_quota(resp.text)
            if is_daily:
                return ApiResult(error='rate_limit_429_daily', daily_quota_exceeded=True,
                                  quota_id=quota_id)
            last_err = 'rate_limit_429'
            time.sleep(SLEEP_AFTER_429 * (attempt + 1))
            continue
        if resp.status_code != 200:
            last_err = mask_secrets(f'HTTP {resp.status_code}: {resp.text[:200]}', key)
            time.sleep(2 * (2 ** attempt))
            continue
        try:
            data = resp.json()
        except Exception:
            last_err = 'not_json'
            continue
        text = _extract_text(data)
        finish_reason = (data.get('candidates') or [{}])[0].get('finishReason')
        if finish_reason and finish_reason != 'STOP':
            return ApiResult(error=f'finish_reason_{finish_reason.lower()}',
                              finish_reason=finish_reason)
        if text:
            return ApiResult(text=text, finish_reason=finish_reason or 'STOP')
        last_err = mask_secrets(f'no_candidates: {str(data)[:200]}', key)
        break
    return ApiResult(error=mask_secrets(last_err, key))


def chunk(it, size):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf


def run(book, limit, batch_size, max_requests, dry_run=False, call_fn=None, verbose=True):
    max_requests = min(max_requests, MAX_REQUESTS_HARD_CAP)
    ckpt = load_checkpoint(book)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if ckpt.get('quota_exhausted') and ckpt['quota_exhausted'].get('date') == today:
        print(f"DỪNG: Gemini đã hết hạn mức THEO NGÀY hôm nay cho sách '{book}' "
              f"({ckpt['quota_exhausted'].get('quota_id')}). Chờ sang hôm sau rồi chạy lại.")
        return {'n_success': 0, 'n_requests': 0, 'stopped_reason': 'daily_quota_already_exhausted_today'}

    done_ids = existing_done_ids(book)
    if verbose:
        print(f"Resume: {len(done_ids)} nexus đã có staging JSONL cho sách '{book}', sẽ skip.")

    def gen_pending():
        n_seen = 0
        for nexus_id, text_zh, seq in iter_nexus_rows(book):
            if nexus_id in done_ids:
                continue
            if limit is not None and n_seen >= limit:
                return
            n_seen += 1
            yield (nexus_id, text_zh, seq)

    if dry_run:
        batches = list(chunk(gen_pending(), batch_size))
        print(f"[DRY-RUN] Sách '{book}': {sum(len(b) for b in batches)} nexus đang chờ dịch, "
              f"{len(batches)} batch (batch_size={batch_size}). KHÔNG gọi API.")
        return {'n_pending': sum(len(b) for b in batches), 'n_batches': len(batches)}

    key = resolve_gemini_key()
    if not key:
        print("LỖI: không tìm thấy GEMINI_API_KEY trong .env hoặc biến môi trường.")
        return {'n_success': 0, 'n_requests': 0, 'stopped_reason': 'no_api_key'}

    if call_fn is None:
        call_fn = lambda prompt: call_gemini(key, prompt)

    ts_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(book_dir(book), exist_ok=True)
    out_path = os.path.join(book_dir(book), f'batch_{ts_tag}.jsonl')

    n_requests = 0
    n_success = 0
    consec_errors = 0
    stopped_reason = None
    last_nexus_id = ckpt.get('last_nexus_id')
    last_seq_done = ckpt.get('last_seq_done', 0)
    t_start = time.time()

    with open(out_path, 'a', encoding='utf-8') as fout:
        for batch in chunk(gen_pending(), batch_size):
            if n_requests >= max_requests:
                stopped_reason = 'max_requests_reached'
                break
            items = [(nid, zh) for nid, zh, seq in batch]
            prompt = build_prompt(items)
            res = call_fn(prompt)
            n_requests += 1

            if res.daily_quota_exceeded:
                ckpt['quota_exhausted'] = {
                    'date': today, 'quota_id': res.quota_id,
                    'ts': datetime.now().isoformat(timespec='seconds'),
                }
                save_checkpoint(book, ckpt)
                stopped_reason = 'daily_quota_exceeded'
                print(f"DỪNG SẠCH: Gemini báo hết hạn mức THEO NGÀY (quotaId={res.quota_id}). "
                      f"Đã lưu checkpoint tại nexus '{last_nexus_id}' (seq={last_seq_done}). "
                      "Chạy lại script sẽ tiếp tục đúng từ đây, KHÔNG dịch lại từ đầu.")
                break

            if res.error:
                consec_errors += 1
                if verbose:
                    print(f"  x batch lỗi: {mask_secrets(res.error[:150])}")
                if consec_errors >= MAX_CONSEC_ERRORS:
                    stopped_reason = 'max_consec_errors'
                    save_checkpoint(book, ckpt)
                    print(f"DỪNG: {MAX_CONSEC_ERRORS} lỗi liên tiếp. Đã lưu checkpoint, "
                          "chạy lại để tiếp tục.")
                    break
                time.sleep(SLEEP_OK)
                continue

            consec_errors = 0
            parsed = parse_response(res.text, [nid for nid, _ in items])
            for nid, zh in items:
                if nid not in parsed:
                    if verbose:
                        print(f"  ! [{nid}] thiếu trong phản hồi, sẽ dịch lại lần chạy sau.")
                    continue
                record = {
                    'nexus_id': nid,
                    'book': book,
                    'text_zh': zh,
                    'text_vi': parsed[nid],
                    'model': MODEL,
                    'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                }
                fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                fout.flush()
                n_success += 1
                last_nexus_id = nid
            # seq của batch cuối (an toàn: lấy seq lớn nhất trong batch đã xử lý)
            last_seq_done = max(last_seq_done, max(seq for _, _, seq in batch))
            ckpt['last_seq_done'] = last_seq_done
            ckpt['last_nexus_id'] = last_nexus_id
            save_checkpoint(book, ckpt)
            time.sleep(SLEEP_OK)

    elapsed = time.time() - t_start
    if verbose:
        print(f"\n=== XONG lần chạy này (sách '{book}') ===")
        print(f"  File output: {out_path}")
        print(f"  Số request: {n_requests} (giới hạn {max_requests})")
        print(f"  Thành công: {n_success}")
        print(f"  Thời gian: {elapsed:.1f}s")
        if stopped_reason:
            print(f"  Lý do dừng: {stopped_reason}")
    return {'n_success': n_success, 'n_requests': n_requests, 'elapsed_sec': elapsed,
            'stopped_reason': stopped_reason, 'out_path': out_path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--batch-size', type=int, default=BATCH_SIZE_DEFAULT)
    ap.add_argument('--max-requests', type=int, default=20)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    run(args.book, args.limit, args.batch_size, args.max_requests, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
