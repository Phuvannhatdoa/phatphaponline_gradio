#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T231 — AI Batch Transliterate Person Names (Hán → Việt)
Dùng Gemini 2.0 Flash phiên âm Hán-Việt chuẩn Phật học cho 48,673 thiền sư.

Lưu kết quả vào bảng ai_person_name trong lineage.db.
Resumable: bỏ qua dila_id đã xử lý.

Usage:
    python scripts/ai_batch_transliterate.py              # chạy toàn bộ
    python scripts/ai_batch_transliterate.py --limit 500  # chỉ 500 records
    python scripts/ai_batch_transliterate.py --reset      # xóa và chạy lại từ đầu
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
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(BASE_DIR, 'data', 'lineage.db')
LOG_FILE  = os.path.join(BASE_DIR, 'logs', 'ai_transliterate.log')
MODEL_ID  = 'gemini-3.1-flash-lite'
BATCH_SIZE    = 50    # tên/request
SLEEP_SECONDS = 5     # giữa các batch (15 RPM free tier)
MAX_RETRIES   = 5

# Đọc API key từ .env hoặc env var
def _load_key():
    env_file = os.path.join(BASE_DIR, '.env')
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

CLIENT = genai.Client(api_key=API_KEY)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# ── Logging ─────────────────────────────────────────────────────────────────
def log(msg, level='INFO'):
    ts   = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}][{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_table():
    """Tạo bảng ai_person_name nếu chưa có."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_person_name (
            dila_id     TEXT PRIMARY KEY,
            name_vi_ai  TEXT,
            model       TEXT DEFAULT 'gemini-3.1-flash-lite',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_pending(limit=None):
    """Lấy tất cả people có name_zh chưa được AI transliterate."""
    conn = get_db()
    q = """
        SELECT p.id AS dila_id, p.name_zh
        FROM people p
        WHERE p.name_zh IS NOT NULL AND p.name_zh != ''
          AND p.id NOT IN (SELECT dila_id FROM ai_person_name WHERE name_vi_ai IS NOT NULL AND name_vi_ai != '')
        ORDER BY p.id
    """
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def count_done():
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) FROM ai_person_name WHERE name_vi_ai IS NOT NULL AND name_vi_ai != ''").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM people WHERE name_zh IS NOT NULL AND name_zh != ''").fetchone()[0]
    conn.close()
    return n, total

def save_batch(results: dict):
    """Lưu {dila_id: name_vi_ai} vào DB."""
    if not results:
        return
    conn = get_db()
    now  = time.strftime('%Y-%m-%d %H:%M:%S')
    conn.executemany(
        "INSERT OR REPLACE INTO ai_person_name (dila_id, name_vi_ai, model, created_at) VALUES (?,?,?,?)",
        [(did, name, MODEL_ID, now) for did, name in results.items()]
    )
    conn.commit()
    conn.close()

def reset_table():
    conn = get_db()
    conn.execute("DELETE FROM ai_person_name")
    conn.commit()
    conn.close()
    log("Đã xóa toàn bộ ai_person_name — bắt đầu lại từ đầu")

# ── Prompt ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là chuyên gia phiên âm Hán-Việt theo chuẩn Phật học hàn lâm Việt Nam.

NHIỆM VỤ: Chuyển đổi tên Hán tự của các thiền sư/tăng nhân sang phiên âm Hán-Việt chuẩn.

QUY TẮC BẮT BUỘC:
1. Dùng âm Hán-Việt truyền thống (sino-Vietnamese), KHÔNG dùng âm Mandarin/Pinyin
2. Viết hoa chữ cái đầu mỗi âm tiết: "Huệ Năng", "Đạo Nhất"
3. KHÔNG thêm tiền tố: Ngài, Thiền Sư, Tổ, Hòa Thượng, Đại Sư, v.v.
4. KHÔNG thêm chú thích, ngoặc đơn hay số năm
5. Chỉ trả về tên phiên âm thuần túy

VÍ DỤ CHUẨN:
- 慧能 → Huệ Năng
- 道一 → Đạo Nhất
- 宗杲 → Tông Cảo
- 法演 → Pháp Diễn
- 馬鳴 → Mã Minh
- 龍樹 → Long Thọ
- 玄奘 → Huyền Trang
- 鑑真 → Giám Chân
- 義玄 → Nghĩa Huyền
- 臨濟 → Lâm Tế

INPUT: JSON array [{\"id\": \"A000001\", \"zh\": \"金總持\"}, ...]
OUTPUT: JSON object {\"A000001\": \"Kim Tổng Trì\", ...}

QUAN TRỌNG: Chỉ trả về JSON object thuần túy, không có markdown, không có giải thích."""

def call_gemini(batch: list) -> dict:
    """
    Gọi Gemini với 1 batch. Trả về {dila_id: name_vi_ai}.
    batch = [{'dila_id': 'A000001', 'name_zh': '金總持'}, ...]
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

            # Trích JSON từ response (bỏ ```json ... ```)
            m = re.search(r'\{[\s\S]*\}', raw)
            if not m:
                raise ValueError(f"Không tìm thấy JSON trong response: {raw[:200]}")
            result = json.loads(m.group())

            # Validate: result phải là dict {str: str}
            cleaned = {}
            for k, v in result.items():
                if isinstance(k, str) and isinstance(v, str) and v.strip():
                    cleaned[k] = v.strip()
            return cleaned

        except Exception as e:
            err_str = str(e)
            log(f"  Lỗi attempt {attempt+1}/{MAX_RETRIES}: {e}", 'WARN')
            if attempt < MAX_RETRIES - 1:
                # 503 UNAVAILABLE: sleep lâu hơn (15s, 30s, 45s, 60s, 90s)
                wait = 15 * (attempt + 1) if '503' in err_str else 5 * (attempt + 1)
                time.sleep(wait)
    return {}

# ── Main ─────────────────────────────────────────────────────────────────────
def run(limit=None):
    ensure_table()

    done_before, total = count_done()
    log(f"=== AI Transliterate bắt đầu ===")
    log(f"Tổng: {total} | Đã xử lý: {done_before} | Còn lại: {total - done_before}")

    pending = get_pending(limit)
    if not pending:
        log("Không có gì để xử lý — tất cả đã được AI phiên âm!")
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
            save_batch(results)
            total_processed += len(results)
            coverage = len(results) / len(batch) * 100
            log(f"  ✓ Đã lưu {len(results)}/{len(batch)} ({coverage:.0f}%) | Tổng: {done_before + total_processed}")
        else:
            errors += 1
            log(f"  ✗ Batch thất bại hoàn toàn (errors={errors})", 'ERROR')

        if i + BATCH_SIZE < len(pending):
            time.sleep(SLEEP_SECONDS)

    log(f"=== HOÀN TẤT ===")
    done_after, _ = count_done()
    log(f"Đã lưu tổng cộng: {done_after}/{total} | Lỗi batch: {errors}")

# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI Batch Transliterate Person Names')
    parser.add_argument('--limit',  type=int, default=None, help='Chỉ xử lý N records đầu tiên')
    parser.add_argument('--reset',  action='store_true',    help='Xóa toàn bộ kết quả cũ và chạy lại')
    args = parser.parse_args()

    if args.reset:
        confirm = input("Xác nhận xóa toàn bộ ai_person_name? (gõ 'yes' để tiếp tục): ")
        if confirm.strip().lower() != 'yes':
            print("Đã hủy.")
            sys.exit(0)
        reset_table()

    run(limit=args.limit)
