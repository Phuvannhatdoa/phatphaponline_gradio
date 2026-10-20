import sqlite3
import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

dotenv_path = os.path.join(BASE_DIR, '..', '..', '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
RAG_MODEL_NAME = os.getenv('RAG_MODEL_NAME', 'gemini-2.5-flash')
GEMINI_MODEL = genai.GenerativeModel(RAG_MODEL_NAME)

BATCH_SIZE = 50
SLEEP_SECONDS = 6
RATE_LIMIT_BACKOFF = 60

LOG_FILE = os.path.join(BASE_DIR, 'rag_worker.log')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_batch():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id, p.name_zh, d.district, d.raw_xml,
               m.district_vi, m.country_vi, m.id AS map_id
        FROM places_pending p
        LEFT JOIN places_dila d ON p.id = d.id
        LEFT JOIN namevi_map_places m ON p.id = m.dila_id
        WHERE (m.district_vi IS NULL OR m.district_vi = '' OR m.id IS NULL)
          AND (d.district IS NOT NULL AND d.district != '')
        LIMIT ?
    """, (BATCH_SIZE,))
    batch = [dict(r) for r in rows]
    conn.close()
    return batch

def build_prompt(batch):
    items = []
    for r in batch:
        raw = r['raw_xml'] or ''
        country = ''
        if raw:
            m = raw.replace('\n', ' ').replace('\r', ' ')
        else:
            m = ''
        items.append({
            "id": r['id'],
            "name_zh": r['name_zh'] or '',
            "district_raw": r['district'] or '',
        })
    prompt = f"""Bạn là chuyên gia địa lý học Phật giáo. Dịch các địa danh Hán văn dưới đây sang tiếng Việt.

Quy tắc:
- 中國 -> Trung Quốc, 阿富汗 -> Afghanistan, Ấn Độ -> Ấn Độ
- 雲南省 -> Tỉnh Vân Nam, 大理古城 -> Khu phố cổ Đại Lý
- Giữ nguyên tên quốc tế trong ngoặc đơn: (Balkh) -> (Balkh)
- Dấu phân cách: - hoặc | giữ nguyên

Input JSON:
{json.dumps(items, ensure_ascii=False, indent=2)}

Output JSON (mảng, không markdown, chỉ JSON thuần):
{{"results": [
  {{"id": "PL...", "district_vi": "bản dịch địa giới", "country_vi": "tên quốc gia"}},
]}}"""
    return prompt

def parse_response(text):
    text = text.strip()
    text = text.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return parsed
    return parsed.get('results', [])

def save_batch(results):
    conn = get_db()
    saved = 0
    for r in results:
        pid = r.get('id')
        district_vi = (r.get('district_vi') or '').strip()
        country_vi = (r.get('country_vi') or '').strip()
        if not pid:
            continue
        try:
            conn.execute("""
                INSERT INTO namevi_map_places (dila_id, district_vi, country_vi, source)
                VALUES (?, ?, ?, 'rag_auto')
                ON CONFLICT(dila_id) DO UPDATE SET
                    district_vi = COALESCE(NULLIF(?, ''), district_vi),
                    country_vi = COALESCE(NULLIF(?, ''), country_vi),
                    source = 'rag_auto'
            """, (pid, district_vi, country_vi, district_vi, country_vi))
            saved += 1
        except Exception as e:
            log(f'  Lỗi lưu {pid}: {e}')
    conn.commit()
    conn.close()
    return saved

def main():
    log('=== RAG WORKER KHỞI ĐỘNG ===')
    log(f'Batch size: {BATCH_SIZE}, Sleep: {SLEEP_SECONDS}s, Backoff: {RATE_LIMIT_BACKOFF}s')

    total_processed = 0
    consecutive_errors = 0
    empty_loops = 0

    while True:
        try:
            batch = fetch_batch()
            if not batch:
                empty_loops += 1
                log(f'Không còn dữ liệu. Empty loops: {empty_loops}')
                if empty_loops >= 3:
                    log('=== TẤT CẢ ĐÃ XỬ LÝ XONG. KẾT THÚC. ===')
                    break
                time.sleep(SLEEP_SECONDS)
                continue

            empty_loops = 0
            log(f'Đang xử lý batch {len(batch)} địa danh (processed: {total_processed})')

            prompt = build_prompt(batch)
            response = GEMINI_MODEL.generate_content(prompt)
            raw = response.text

            results = parse_response(raw)
            log(f'  Gemini trả về {len(results)} kết quả')

            saved = save_batch(results)
            total_processed += saved
            log(f'  Đã lưu {saved}/{len(batch)} địa danh')

            consecutive_errors = 0
            log(f'Nghỉ {SLEEP_SECONDS}s...')
            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            err_str = str(e)
            log(f'LỖI: {err_str}')
            if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str or 'quota' in err_str.lower():
                backoff = RATE_LIMIT_BACKOFF * (1 + consecutive_errors)
                log(f'Rate limit! Nghỉ {backoff}s (lần {consecutive_errors + 1})...')
                time.sleep(backoff)
            else:
                consecutive_errors += 1
                if consecutive_errors >= 10:
                    log('Quá nhiều lỗi liên tiếp. Dừng.')
                    break
                time.sleep(SLEEP_SECONDS)

    log(f'=== KẾT THÚC. Tổng số: {total_processed} ===')

if __name__ == '__main__':
    main()
