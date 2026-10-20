#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T428 Part 2 — AI Batch Transliterate Places + Districts (Hán → Việt).

Dùng Gemini 2.0 Flash phiên âm Hán-Việt chuẩn Phật học cho:
- Places: 59,353 (từ places_dila)
- Districts: 16,907 (từ codex_district_name)

Lưu kết quả vào bảng ai_place_name và ai_district_name.
Resumable: bỏ qua dila_id đã xử lý.

Usage:
    python scripts/ai_batch_transliterate_places_districts.py --element place --limit 500
    python scripts/ai_batch_transliterate_places_districts.py --element district --limit 500
    python scripts/ai_batch_transliterate_places_districts.py --element place --reset
"""

import os
import sys
import sqlite3
import json
import time
import re
import argparse

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("LỖI: Thiếu thư viện google-genai. Chạy: pip install google-genai")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(BASE_DIR, 'data', 'lineage.db')
LOG_FILE   = os.path.join(BASE_DIR, 'logs', 'ai_transliterate.log')
MODEL_ID   = 'gemini-3.1-flash-lite'
BATCH_SIZE = 50
SLEEP_SECONDS = 5
MAX_RETRIES = 5

# Element configs
ELEMENT_CONFIG = {
    'place': {
        'source_table': 'places_dila',
        'id_col': 'id',
        'zh_col': 'name_zh',
        'ai_table': 'ai_place_name',
        'name_zh_filter': 'name_zh IS NOT NULL AND name_zh != \'\'',
        'total_query': 'SELECT COUNT(*) FROM places_dila WHERE name_zh IS NOT NULL AND name_zh != \'\'',
    },
    'district': {
        'source_table': 'codex_district_name',
        'id_col': 'dila_id',
        'zh_col': 'name_zh',
        'ai_table': 'ai_district_name',
        'name_zh_filter': 'name_zh IS NOT NULL AND name_zh != \'\'',
        'total_query': 'SELECT COUNT(*) FROM codex_district_name WHERE name_zh IS NOT NULL AND name_zh != \'\'',
    },
}

MODEL_ID     = 'gemini-3.1-flash-lite'
BATCH_SIZE   = 50
SLEEP_SECONDS = 5
MAX_RETRIES  = 5


def _load_key():
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_file):
        for line in open(env_file, encoding='utf-8'):
            line = line.strip()
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"\'')
    return os.environ.get('GEMINI_API_KEY', '')


API_KEY = _load_key()
if not API_KEY:
    print("LỖI: Không tìm thấy GEMINI_API_KEY trong .env")
    sys.exit(1)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("LỖI: Thiếu thư viện google-genai. Chạy: pip install google-genai")
    sys.exit(1)

CLIENT = genai.Client(api_key=API_KEY)

os.makedirs(os.path.dirname('logs/ai_transliterate.log'), exist_ok=True)


def log(msg, level='INFO'):
    ts   = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}][{level}] {msg}"
    print(line)
    try:
        with open('logs/ai_transliterate.log', 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_place_name (
            dila_id     TEXT PRIMARY KEY,
            name_vi_ai  TEXT,
            model       TEXT DEFAULT 'gemini-3.1-flash-lite',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_district_name (
            dila_id     TEXT PRIMARY KEY,
            name_vi_ai  TEXT,
            model       TEXT DEFAULT 'gemini-3.1-flash-lite',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_config(element):
    return ELEMENT_CONFIG.get(element)


def get_pending(element, limit=None):
    """Lấy records chưa được AI transliterate."""
    cfg = get_config(element)
    conn = get_db()
    q = f"""
        SELECT s.{cfg['id_col']} AS dila_id, s.{cfg['zh_col']} AS name_zh
        FROM {cfg['source_table']} s
        WHERE s.{cfg['name_zh_filter']}
          AND s.{cfg['id_col']} NOT IN (
              SELECT dila_id FROM {cfg['ai_table']}
              WHERE name_vi_ai IS NOT NULL AND name_vi_ai != ''
          )
        ORDER BY s.{cfg['id_col']}
    """
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_done(element):
    cfg = get_config(element)
    conn = get_db()
    n = conn.execute(
        f"SELECT COUNT(*) FROM {cfg['ai_table']} WHERE name_vi_ai IS NOT NULL AND name_vi_ai != ''"
    ).fetchone()[0]
    total = conn.execute(cfg['total_query']).fetchone()[0]
    conn.close()
    return n, total


def save_batch(element, results: dict):
    if not results:
        return
    cfg = get_config(element)
    conn = get_db()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    conn.executemany(
        f"INSERT OR REPLACE INTO {cfg['ai_table']} (dila_id, name_vi_ai, model, created_at) VALUES (?,?,?,?)",
        [(did, name, MODEL_ID, now) for did, name in results.items()]
    )
    conn.commit()
    conn.close()


def reset_table(element):
    cfg = get_config(element)
    conn = get_db()
    conn.execute(f"DELETE FROM {cfg['ai_table']}")
    conn.commit()
    conn.close()
    log(f"Đã xóa toàn bộ {cfg['ai_table']} — bắt đầu lại từ đầu")


# ── Prompt ───────────────────────────────────────────────────────────────────
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
- 巴黎 → Ba Lí
- 東京 → Đông Kinh
- 首爾 → Seo Ul

INPUT: JSON array [{"id": "PL000000000001", "zh": "闊悉多國"}, ...]
OUTPUT: JSON object {"PL000000000001": "Khoát Tất Đa Quốc", ...}

QUAN TRỌNG: Chỉ trả về JSON object thuần túy, không có markdown, không có giải thích."""


def call_gemini(batch: list) -> dict:
    """
    Gọi Gemini với 1 batch. Trả về {dila_id: name_vi_ai}.
    batch = [{'dila_id': 'PL000000000001', 'name_zh': '闊悉多國'}, ...]
    """
    payload = [{"id": r['dila_id'], "zh": r['name_zh']} for r in batch]
    prompt  = SYSTEM_PROMPT + "\n\nINPUT:\n" + json.dumps(payload, ensure_ascii=False)

    for attempt in range(MAX_RETRIES):
        try:
            response = CLIENT.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4000,
                    response_mime_type="application/json"
                )
            )
            raw = response.text.strip()

            # Trích JSON từ response
            m = re.search(r'\{[\s\S]*\}', raw)
            if not m:
                raise ValueError(f"Không tìm thấy JSON trong response: {raw[:200]}")

            json_str = m.group()
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError:
                json_str2 = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
                try:
                    result = json.loads(json_str2)
                except json.JSONDecodeError:
                    pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', json_str2)
                    if not pairs:
                        raise ValueError(f"Không parse được JSON: {json_str2[:200]}")
                    result = {k: v for k, v in pairs}

            cleaned = {}
            for k, v in result.items():
                if isinstance(k, str) and isinstance(v, str) and v.strip():
                    cleaned[k] = v.strip()
            return cleaned

        except Exception as e:
            err_str = str(e)
            log(f"  Lỗi attempt {attempt+1}/{MAX_RETRIES}: {e}", 'WARN')
            if attempt < MAX_RETRIES - 1:
                if '429' in err_str:
                    wait = 70
                elif '503' in err_str:
                    wait = 15 * (attempt + 1)
                else:
                    wait = 3
                time.sleep(wait)
    return {}


def run(element, limit=None):
    cfg = get_config(element)
    ensure_tables()

    done_before, total = count_done(element)
    log(f"=== AI Transliterate {element.upper()} bắt đầu ===")
    log(f"Tổng: {total} | Đã xử lý: {done_before} | Còn lại: {total - done_before}")

    pending = get_pending(element, limit)
    if not pending:
        log(f"Không có gì để xử lý {element} — tất cả đã được AI phiên âm!")
        return

    log(f"Sẽ xử lý {len(pending)} records trong batch {BATCH_SIZE}")

    total_processed = 0
    errors = 0

    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE

        log(f"Batch {batch_num}/{total_batches}: {batch[0]['dila_id']} → {batch[-1]['dila_id']} ({len(batch)} tên)")

        results = call_gemini(batch)

        if results:
            save_batch(element, results)
            total_processed += len(results)
            coverage = len(results) / len(batch) * 100
            log(f"  ✓ Đã lưu {len(results)}/{len(batch)} ({coverage:.0f}%) | Tổng: {done_before + total_processed}")
        else:
            errors += 1
            log(f"  ✗ Batch thất bại hoàn toàn (errors={errors})", 'ERROR')

        if i + BATCH_SIZE < len(pending):
            time.sleep(SLEEP_SECONDS)

    log(f"=== HOÀN TẤT {element.upper()} ===")
    done_after, _ = count_done(element)
    log(f"Đã lưu tổng cộng: {done_after}/{total} | Lỗi batch: {errors}")


def count_done(element):
    cfg = get_config(element)
    conn = get_db()
    n = conn.execute(
        f"SELECT COUNT(*) FROM {cfg['ai_table']} WHERE name_vi_ai IS NOT NULL AND name_vi_ai != ''"
    ).fetchone()[0]
    total = conn.execute(cfg['total_query']).fetchone()[0]
    conn.close()
    return n, total


def save_batch(element, results: dict):
    if not results:
        return
    cfg = get_config(element)
    conn = get_db()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    conn.executemany(
        f"INSERT OR REPLACE INTO {cfg['ai_table']} (dila_id, name_vi_ai, model, created_at) VALUES (?,?,?,?)",
        [(did, name, MODEL_ID, now) for did, name in results.items()]
    )
    conn.commit()
    conn.close()


def reset_table(element):
    cfg = get_config(element)
    conn = get_db()
    conn.execute(f"DELETE FROM {cfg['ai_table']}")
    conn.commit()
    conn.close()
    log(f"Đã xóa toàn bộ {cfg['ai_table']} — bắt đầu lại từ đầu")


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='AI Batch Transliterate Places + Districts')
    ap.add_argument('--element', choices=['place', 'district'], required=True,
                    help='Loại element: place hoặc district')
    ap.add_argument('--limit', type=int, default=None, help='Chỉ xử lý N records đầu tiên')
    ap.add_argument('--reset', action='store_true', help='Xóa toàn bộ kết quả cũ và chạy lại')
    args = ap.parse_args()

    if args.reset:
        confirm = input(f"Xác nhận xóa toàn bộ ai_{args.element}_name? (gõ 'yes' để tiếp tục): ")
        if confirm.strip().lower() != 'yes':
            print("Đã hủy.")
            sys.exit(0)
        reset_table(args.element)

    run(args.element, limit=args.limit)