#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T444 (T428 Part 2) — Gemini batch phien am places + districts (Han -> Viet).

KHONG sua script cu (ai_batch_transliterate.py, ai_batch_transliterate_places_districts.py).

Nguon Han tu:
- place    : codex_place_name.name_zh_xml    (59.353 dong, T443)
- district : codex_district_name.name_zh     (16.907 dong, T428)

Dich:
- ai_place_name(dila_id, name_vi_ai, model, created_at)
- ai_district_name(dila_id, name_vi_ai, model, created_at)

Uu tien (T444): review_needed_places.tsv (3.047) + review_needed_districts.tsv (305)
truoc, sau do phan con lai. Resumable: bo qua id da co name_vi_ai.

Rang buoc:
- KHONG dung vao codex_place_name / places / places_dila / namevi_map_places
  (snapshot truoc/sau moi lan chay, lech -> exit 3).
- Retry MAX_RETRIES=5; 429 -> sleep 70s; 503 -> backoff.
- Tran 3 ngay (--max-hours 72).
- Log rieng: logs/ai_transliterate_place.log

Usage:
  python -X utf8 scripts/ai_batch_transliterate_place.py --dry-run
  python -X utf8 scripts/ai_batch_transliterate_place.py --limit 500
  python -X utf8 scripts/ai_batch_transliterate_place.py            # resume het
  python -X utf8 scripts/ai_batch_transliterate_place.py --reset --yes
"""

import argparse
import csv
import io
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'ai_transliterate_place.log')
CACHE_DIR = os.path.join(BASE_DIR, 'data', 'phien_am')

RAW_BASE = ('https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/'
            'claude/sleepy-tesla-qsx17b/data/phien_am/')
REVIEW_TSV = {
    'place': RAW_BASE + 'review_needed_places.tsv',
    'district': RAW_BASE + 'review_needed_districts.tsv',
}

MODEL_ID = 'gemini-3.1-flash-lite'
BATCH_SIZE = 50
SLEEP_SECONDS = 5
MAX_RETRIES = 5
MAX_HOURS = 72.0

ELEMENTS = {
    'place': {
        'source': 'codex_place_name',
        'zh_col': 'name_zh_xml',
        'ai_table': 'ai_place_name',
    },
    'district': {
        'source': 'codex_district_name',
        'zh_col': 'name_zh',
        'ai_table': 'ai_district_name',
    },
}

GUARDED = ('codex_place_name', 'codex_district_name', 'places', 'places_dila',
           'namevi_map_places')

SYSTEM_PROMPT = """Bạn là chuyên gia phiên âm Hán-Việt theo chuẩn Phật học hàn lâm Việt Nam.

NHIỆM VỤ: Chuyển đổi tên Hán tự của các địa danh/địa phương sang phiên âm Hán-Việt chuẩn.

QUY TẮC BẮT BUỘC:
1. Dùng âm Hán-Việt truyền thống (sino-Vietnamese), KHÔNG dùng âm Mandarin/Pinyin
2. Viết hoa chữ cái đầu mỗi âm tiết: "Trung Quốc", "A Phú Hãn", "Vân Nam"
3. KHÔNG thêm tiền tố, hậu tố không cần thiết
4. KHÔNG thêm chú thích, ngoặc đơn hay số năm
5. Chỉ trả về tên phiên âm thuần túy
6. Tên quốc gia/khu vực: dùng tên gọi phổ biến tại Việt Nam (VD: "Trung Quốc", "Nhật Bản", "Hàn Quốc")

VÍ DỤ CHUẨN:
- 中國 → Trung Quốc
- 阿富汗 → A Phú Hãn
- 雲南省 → Vân Nam Tỉnh
- 曲靖市 → Khúc Tĩnh Thị
- 富源縣 → Phú Nguyên Huyện
- 巴爾赫省 → Ba Nhĩ Hách Tỉnh

INPUT: JSON array [{"id": "PL000000000001", "zh": "闊悉多國"}, ...]
OUTPUT: JSON object {"PL000000000001": "Khoát Tất Đa Quốc", ...}

QUAN TRỌNG: Chỉ trả về JSON object thuần túy, không có markdown, không có giải thích."""


def log(msg, level='INFO'):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}][{level}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    except OSError:
        pass


def load_key():
    env_file = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_file):
        with open(env_file, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('GEMINI_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    return os.environ.get('GEMINI_API_KEY', '')


def get_db(readonly=False):
    if readonly:
        return sqlite3.connect('file:' + DB_PATH.replace(os.sep, '/') + '?mode=ro', uri=True)
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS ai_place_name (
        dila_id TEXT PRIMARY KEY, name_vi_ai TEXT,
        model TEXT DEFAULT 'gemini-3.1-flash-lite', created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS ai_district_name (
        dila_id TEXT PRIMARY KEY, name_vi_ai TEXT,
        model TEXT DEFAULT 'gemini-3.1-flash-lite', created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()


def counts(conn, tables):
    out = {}
    for t in tables:
        try:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except sqlite3.Error:
            out[t] = None
    return out


def fetch_review_ids(element):
    """dila_id trong TSV review (uu tien). Tra ve list theo thu tu file."""
    url = REVIEW_TSV[element]
    name = os.path.basename(url)
    path = os.path.join(CACHE_DIR, name)
    raw = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        raw = io.open(path, 'rb').read()
        log(f'  review TSV: cache {path}')
    else:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(raw)
        log(f'  review TSV: http {url} ({len(raw):,} bytes)')

    text = raw.decode('utf-8-sig')
    ids = []
    for row in csv.DictReader(io.StringIO(text), delimiter='\t'):
        did = (row.get('dila_id') or '').strip()
        if did:
            ids.append(did)
    return ids


def pending_ids(conn, element, review_ids):
    """Uu tien review_ids roi den phan con lai, bo qua da co name_vi_ai."""
    cfg = ELEMENTS[element]
    done = {r[0] for r in conn.execute(
        f"SELECT dila_id FROM {cfg['ai_table']} "
        "WHERE name_vi_ai IS NOT NULL AND name_vi_ai != ''")}
    order = ['cn.rowid']
    rows = conn.execute(
        f"SELECT c.dila_id FROM {cfg['source']} c "
        f"WHERE c.{cfg['zh_col']} IS NOT NULL AND c.{cfg['zh_col']} != '' "
        "ORDER BY c.dila_id").fetchall()
    all_ids = [r[0] for r in rows]

    prio = [i for i in review_ids if i not in done]
    prio_set = set(prio)
    rest = [i for i in all_ids if i not in done and i not in prio_set]
    return prio + rest, len(prio), len(rest), len(done)


def norm_zh(text):
    """Bo ngoac Latin (vd: "卡納塔克邦(Karnataka)") + khoang trang thua.

    Giu nguyen ngoac neu ben trong co chu Han (co the la ten thay the can dich).
    """
    s = (text or '').strip()
    if not s:
        return ''
    has_han = re.compile(r'[\u3400-\u9fff]')

    def _drop(m):
        inner = m.group(1)
        return '' if inner and not has_han.search(inner) else m.group(0)

    s = re.sub(r'[\(（]([^\)）]*)[\)）]', _drop, s)
    return re.sub(r'\s+', ' ', s).strip()


def load_names(conn, element, ids):
    cfg = ELEMENTS[element]
    out = {}
    chunk = 500
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        q = (f"SELECT dila_id, {cfg['zh_col']} AS zh FROM {cfg['source']} "
             f"WHERE dila_id IN ({','.join('?' * len(part))})")
        for did, zh in conn.execute(q, part):
            clean = norm_zh(zh)
            if clean:
                out[did] = clean
    missing = len(ids) - len(out)
    if missing:
        log(f'  {element}: {missing} id khong co name_zh hop le -> bo qua (lan sau xu ly)',
            'WARN')
    return out


def call_gemini(client, types_mod, batch):
    payload = [{'id': d, 'zh': z} for d, z in batch]
    prompt = SYSTEM_PROMPT + '\n\nINPUT:\n' + json.dumps(payload, ensure_ascii=False)

    for attempt in range(MAX_RETRIES):
        try:
            resp = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types_mod.GenerateContentConfig(
                    temperature=0.1, max_output_tokens=4000,
                    response_mime_type='application/json'))
            raw = (resp.text or '').strip()
            m = re.search(r'\{[\s\S]*\}', raw)
            if not m:
                raise ValueError(f'khong thay JSON: {raw[:160]}')
            body = m.group()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                body = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', body)
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    data = dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', body))
            return {k: v.strip() for k, v in data.items()
                    if isinstance(k, str) and isinstance(v, str) and v.strip()}
        except Exception as exc:  # noqa: BLE001 - API tra nhieu loai loi
            err = str(exc)
            log(f'  loi attempt {attempt + 1}/{MAX_RETRIES}: {err[:200]}', 'WARN')
            if attempt == MAX_RETRIES - 1:
                break
            if '429' in err or 'RESOURCE_EXHAUSTED' in err:
                wait = 70
            elif '503' in err or 'UNAVAILABLE' in err:
                wait = 15 * (attempt + 1)
            else:
                wait = 3
            log(f'  sleep {wait}s', 'WARN')
            time.sleep(wait)
    return {}


def save_batch(conn, element, results):
    cfg = ELEMENTS[element]
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    conn.executemany(
        f'INSERT OR REPLACE INTO {cfg["ai_table"]} '
        '(dila_id, name_vi_ai, model, created_at) VALUES (?,?,?,?)',
        [(did, name, MODEL_ID, now) for did, name in results.items()])
    conn.commit()


def checkpoint(conn):
    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    except sqlite3.Error as exc:
        log(f'  checkpoint loi: {exc}', 'WARN')


def backup_db():
    ts = time.strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join(BASE_DIR, 'data', 'backups', f'T444_{ts}')
    os.makedirs(bdir, exist_ok=True)
    bpath = os.path.join(bdir, 'lineage.db')
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(bpath)
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
    qc = src.execute('PRAGMA quick_check').fetchone()[0]
    src.close()
    log(f'[backup] {bpath} (quick_check={qc})')
    if qc != 'ok':
        raise SystemExit('[STOP] quick_check FAIL - khong ghi DB.')
    return bpath


def plan(conn, elements):
    info = {}
    for el in elements:
        review_ids = fetch_review_ids(el)
        ids, n_prio, n_rest, n_done = pending_ids(conn, el, review_ids)
        info[el] = {'ids': ids, 'prio': n_prio, 'rest': n_rest, 'done': n_done,
                    'review_total': len(review_ids)}
        log(f'  {el:9s}: da xong {n_done:,} | con lai {len(ids):,} '
            f'(uu tien review {n_prio:,} + con lai {n_rest:,}) | review TSV {len(review_ids):,}')
    return info


def main():
    ap = argparse.ArgumentParser(description='T444 - Gemini batch phien am places + districts')
    ap.add_argument('--element', choices=['place', 'district', 'both'], default='both')
    ap.add_argument('--limit', type=int, default=None, help='Chi xu ly N ten (doc lap cho tung element)')
    ap.add_argument('--reset', action='store_true', help='Xoa ai_*_name truoc khi chay')
    ap.add_argument('--yes', action='store_true', help='Xac nhan cho --reset')
    ap.add_argument('--dry-run', action='store_true', help='Chi bao cao so luong, khong goi API')
    ap.add_argument('--sleep', type=float, default=SLEEP_SECONDS, help='Giay nghi giua batch')
    ap.add_argument('--max-hours', type=float, default=MAX_HOURS, help='Tran thoi gian chay')
    ap.add_argument('--no-backup', action='store_true', help='Bo qua backup (khong khuyen nghi)')
    args = ap.parse_args()

    elements = ['place', 'district'] if args.element == 'both' else [args.element]

    conn = get_db(readonly=True)
    try:
        ensure_needed = False
        for t in ('ai_place_name', 'ai_district_name'):
            if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                                (t,)).fetchone():
                ensure_needed = True
        before = counts(conn, GUARDED)
        info = plan(conn, elements)
    finally:
        conn.close()

    total = sum(len(info[e]['ids']) for e in elements)
    log(f'=== T444 {"DRY-RUN" if args.dry_run else "RUN"} | pending {total:,} | model {MODEL_ID} ===')
    if args.dry_run:
        for el in elements:
            log(f'  {el}: {info[el]["ids"][:3]} ...')
        log('DRY-RUN xong, khong goi API.')
        return 0
    if not total:
        log('Khong con gi de xu ly.')
        return 0

    api_key = load_key()
    if not api_key:
        log('Thieu GEMINI_API_KEY trong .env', 'ERROR')
        return 2
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        log('Thieu thu vien google-genai (pip install google-genai)', 'ERROR')
        return 2
    client = genai.Client(api_key=api_key)

    if args.reset:
        if not args.yes:
            log('--reset can --yes', 'ERROR')
            return 2
        conn = get_db()
        for el in elements:
            conn.execute(f'DELETE FROM {ELEMENTS[el]["ai_table"]}')
            log(f'reset {ELEMENTS[el]["ai_table"]}')
        conn.commit()
        conn.close()
        conn = get_db(readonly=True)
        info = plan(conn, elements)
        conn.close()
        total = sum(len(info[e]['ids']) for e in elements)

    backup_path = None if args.no_backup else backup_db()

    started = time.time()
    deadline = started + args.max_hours * 3600
    stats = {el: {'saved': 0, 'failed': 0, 'batches': 0} for el in elements}

    conn = get_db()
    ensure_tables(conn)
    for el in elements:
        ids = info[el]['ids']
        if args.limit:
            ids = ids[:args.limit]
        if not ids:
            continue
        names = load_names(conn, el, ids)
        batch_total = (len(ids) + BATCH_SIZE - 1) // BATCH_SIZE
        log(f'--- {el}: {len(ids)} ten / {batch_total} batch ---')
        for bi in range(0, len(ids), BATCH_SIZE):
            if time.time() > deadline:
                log(f'Cham tran {args.max_hours}h - dung (resume sau).', 'WARN')
                break
            part = [i for i in ids[bi:bi + BATCH_SIZE] if i in names]
            if not part:
                continue
            batch = [(i, names[i]) for i in part]
            got = call_gemini(client, genai_types, batch)
            if got:
                save_batch(conn, el, got)
                stats[el]['saved'] += len(got)
                stats[el]['batches'] += 1
                log(f'  batch {bi // BATCH_SIZE + 1}/{batch_total}: {len(got)}/{len(batch)} '
                    f'| tong {stats[el]["saved"]}')
            else:
                stats[el]['failed'] += 1
                log(f'  batch {bi // BATCH_SIZE + 1}/{batch_total}: THAT BAI', 'ERROR')
            if (bi // BATCH_SIZE + 1) % 20 == 0:
                checkpoint(conn)
            if bi + BATCH_SIZE < len(ids):
                time.sleep(args.sleep)
        checkpoint(conn)

    conn.close()

    conn = get_db(readonly=True)
    try:
        after = counts(conn, GUARDED)
        ai_now = counts(conn, ('ai_place_name', 'ai_district_name'))
    finally:
        conn.close()

    log(f'=== KET QUA ({time.time() - started:.0f}s) ===')
    for el in elements:
        log(f'  {el}: saved {stats[el]["saved"]:,} | failed_batch {stats[el]["failed"]} '
            f'| batch_ok {stats[el]["batches"]}')
    log(f'  ai_place_name={ai_now["ai_place_name"]:,} ai_district_name={ai_now["ai_district_name"]:,}')
    if after != before:
        log(f'[FATAL] bang duoc bao ve bi doi: {before} -> {after}', 'ERROR')
        return 3
    log(f'  guarded OK (khong doi): {after}')
    if backup_path:
        log(f'  backup: {backup_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
