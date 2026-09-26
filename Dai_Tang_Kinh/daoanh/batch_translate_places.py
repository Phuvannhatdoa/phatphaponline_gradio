#!/usr/bin/env python3
"""
Batch Translation Engine for DILA Place Names
Dịch hàng loạt địa danh Hán văn từ places_pending + places_dila
sang tiếng Việt hành chính bằng Gemini 1.5 Flash (Free Tier).

Luồng xử lý:
1. Query các dòng CHƯA có district_vi trong namevi_map_places
2. Gom batch 50 ID/Prompt
3. Gửi Gemini Flash, parse JSON kết quả
4. UPSERT vào namevi_map_places (không ghi đè dòng đã biên tập thủ công)
5. Sleep 4 giây giữa các request (15 RPM)
6. Lặp lại cho đến khi hết dữ liệu

Usage: nohup python3 batch_translate_places.py > translate.log 2>&1 &
"""

import os
import sqlite3
import json
import time
import re
import google.generativeai as genai

# Đường dẫn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

# Gemini config
genai.configure(api_key="AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE")
MODEL = genai.GenerativeModel('gemini-2.0-flash')

# Batch config
BATCH_SIZE = 50
SLEEP_SECONDS = 4
MAX_RETRIES = 3

LOG_FILE = os.path.join(BASE_DIR, 'translate.log')


def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_pending_batch(offset):
    """Lấy BATCH_SIZE dòng places_pending chưa có district_vi trong namevi_map_places."""
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id, p.name_zh, p.country,
               d.district, d.geo_lat, d.geo_long
        FROM places_pending p
        LEFT JOIN places_dila d ON p.id = d.id
        WHERE (p.id NOT IN (SELECT dila_id FROM namevi_map_places WHERE district_vi IS NOT NULL AND district_vi != ''))
          AND p.name_zh IS NOT NULL AND p.name_zh != ''
          AND d.district IS NOT NULL AND d.district != ''
        LIMIT ? OFFSET ?
    """, (BATCH_SIZE, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_pending():
    """Đếm tổng số dòng cần xử lý."""
    conn = get_db()
    row = conn.execute("""
        SELECT COUNT(*) as cnt FROM places_pending p
        LEFT JOIN places_dila d ON p.id = d.id
        WHERE (p.id NOT IN (SELECT dila_id FROM namevi_map_places WHERE district_vi IS NOT NULL AND district_vi != ''))
          AND p.name_zh IS NOT NULL AND p.name_zh != ''
          AND d.district IS NOT NULL AND d.district != ''
    """).fetchone()
    conn.close()
    return row['cnt'] if row else 0


def build_prompt(batch):
    """Xây dựng prompt Gemini cho một batch 50 địa danh."""
    items_str = "\n".join([
        f"{i+1}. ID: {r['id']}, Hán văn: {r['district']}, Quốc gia: {r['country'] or 'N/A'}"
        for i, r in enumerate(batch)
    ])
    prompt = f"""Bạn là chuyên gia địa lý học Phật giáo. Dịch danh sách {len(batch)} địa danh Hán văn sau sang tiếng Việt hành chính hiện đại.

Quy tắc:
- 中國 -> Trung Quốc, 阿富汗 -> Afghanistan, 雲南省 -> Tỉnh Vân Nam
- 廣南省 -> Tỉnh Quảng Nam, 承天順化省 -> Tỉnh Thừa Thiên Huế
- Đảm bảo giữ nguyên cấp độ hành chính (Tỉnh, Huyện, Xã, Thôn)
- Nếu không xác định được, trả về chuỗi gốc

Trả về JSON array, mỗi phần tử có dạng:
{{"id": "PL...", "translated_district": "kết quả dịch", "translated_country": "tên quốc gia tiếng Việt"}}

DANH SÁCH:
{items_str}

Yêu cầu: Chỉ trả về JSON array hợp lệ, không markdown, không giải thích thêm."""
    return prompt


def translate_batch(batch):
    """Gửi một batch lên Gemini và parse kết quả."""
    prompt = build_prompt(batch)
    for attempt in range(MAX_RETRIES):
        try:
            response = MODEL.generate_content(prompt)
            clean = response.text.strip().replace('```json', '').replace('```', '').strip()
            results = json.loads(clean)
            if isinstance(results, list):
                return results
            log(f" Lần {attempt+1}: Response không phải array, thử lại...")
        except Exception as e:
            log(f" Lần {attempt+1} thất bại: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(SLEEP_SECONDS * 2)
    return None


def save_results(results):
    """UPSERT kết quả vào namevi_map_places. Chỉ cập nhật district_vi, country_vi, không ghi đè các cột khác."""
    if not results:
        return 0
    conn = get_db()
    saved = 0
    for r in results:
        dila_id = r.get('id', '')
        district_vi = (r.get('translated_district') or '').strip()
        country_vi = (r.get('translated_country') or '').strip()
        if not dila_id or not district_vi:
            continue
        try:
            # UPSERT: insert nếu chưa có, chỉ update district_vi + country_vi nếu đã tồn tại
            conn.execute("""
                INSERT INTO namevi_map_places (dila_id, name_zh, district_vi, country_vi, source, needs_review)
                VALUES (?, ?, ?, ?, 'ai_translate', 0)
                ON CONFLICT(dila_id) DO UPDATE SET
                    district_vi = excluded.district_vi,
                    country_vi = excluded.country_vi
            """, (dila_id, '', district_vi, country_vi))
            saved += 1
        except Exception as e:
            log(f"  Lỗi lưu {dila_id}: {e}")
    conn.commit()
    conn.close()
    return saved


def main():
    log("=" * 60)
    log("BATCH TRANSLATE ENGINE KHỞI ĐỘNG")
    log(f"DB: {DB_PATH}")
    log(f"Batch size: {BATCH_SIZE}, Sleep: {SLEEP_SECONDS}s")
    log("=" * 60)

    total = get_total_pending()
    log(f"Tổng số dòng cần xử lý: {total}")

    processed = 0
    saved_total = 0
    errors = 0
    offset = 0
    start_time = time.time()

    while offset < total:
        batch = get_pending_batch(offset)
        if not batch:
            log(f"Không còn dữ liệu tại offset {offset}. Kết thúc.")
            break

        log(f"Batch {offset//BATCH_SIZE + 1}: offset={offset}, size={len(batch)}")
        results = translate_batch(batch)

        if results:
            saved = save_results(results)
            saved_total += saved
            log(f"  -> Đã lưu {saved}/{len(batch)} dòng")
        else:
            errors += 1
            log(f"  -> THẤT BẠI sau {MAX_RETRIES} lần thử")

        processed += len(batch)
        elapsed = time.time() - start_time
        rate = processed / elapsed * 3600 if elapsed > 0 else 0
        pct = processed / total * 100 if total > 0 else 0
        log(f"  Tiến độ: {processed}/{total} ({pct:.1f}%) | "
            f"Đã lưu: {saved_total} | Lỗi batch: {errors} | "
            f"Tốc độ: {rate:.0f} dòng/giờ | Thời gian: {elapsed/60:.1f} phút")

        offset += len(batch)
        if offset < total:
            log(f"  Đợi {SLEEP_SECONDS}s trước batch tiếp theo...")
            time.sleep(SLEEP_SECONDS)

    elapsed_total = time.time() - start_time
    log("=" * 60)
    log(f"HOÀN TẤT! Tổng: {processed} dòng, Đã lưu: {saved_total}, Lỗi: {errors}")
    log(f"Thời gian: {elapsed_total/60:.1f} phút ({elapsed_total/3600:.2f} giờ)")
    log("=" * 60)


if __name__ == '__main__':
    main()
