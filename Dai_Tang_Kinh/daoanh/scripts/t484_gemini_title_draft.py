"""
T484 — Gemini free dịch tên Kinh (dila_catalog_works.title_zh) sang tiếng Việt, theo lô nhỏ.

Chỉ ghi file nháp JSONL, KHÔNG ghi DB. Admin đối chiếu rồi mới pass.

Cách chạy
---------
  python -X utf8 scripts/t484_gemini_title_draft.py --dry-run
  python -X utf8 scripts/t484_gemini_title_draft.py --max-requests 20

Quy tắc an toàn
---------------
- Khóa đọc từ GEMINI_API_KEY trong .env (không in ra log).
- Gọi tuần tự, nghỉ SLEEP_OK giây giữa các yêu cầu (hạn mức free rất thấp).
- Gộp BATCH_SIZE tên mỗi yêu cầu. Model trả JSON; thiếu id hoặc id lạ thì
  cả lô không được ghi, để chạy lại sau (không gán nhầm).
- Hết hạn mức theo ngày (429 PerDay) thì dừng sạch; ngày hôm sau chạy lại,
  chương trình tự bỏ qua các id đã có trong file nháp.
- Có giới hạn cứng --max-requests tính cả yêu cầu lỗi.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..")
DB = os.path.join(BASE, "data", "lineage.db")
ENV = os.path.join(BASE, ".env")
OUT = os.path.join(BASE, "docs", "sessions", "2026-10-28", "catalog", "t484_gemini_titles_draft.jsonl")

MODEL = "gemini-3.8-flash"
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
BATCH_SIZE = 5
SLEEP_OK = 6.5
SLEEP_429 = 20.0
RETRY_429 = 3

PROMPT_HEAD = (
    "Bạn là chuyên gia Phật học. Dịch tên các bộ kinh Hán sau sang tiếng Việt, "
    "giữ thuật ngữ Phật học chuẩn; tên riêng giữ theo phiên âm Hán-Việt. "
    "Trả về JSON array dạng [{\"id\": \"...\", \"vi\": \"...\"}], đúng số lượng và "
    "đúng id như đầu vào, không thêm chú thích.\n\nDanh sách:\n"
)


def load_key():
    """Đọc GEMINI_API_KEY từ môi trường hoặc .env. Không in giá trị khóa."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    try:
        with open(ENV, encoding="utf-8") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def load_done(path):
    """Các cbeta_id đã có bản dịch hợp lệ trong file nháp (để chạy lại không dịch trùng)."""
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("gemini_vi"):
                done.add(row["cbeta_id"])
    return done


def load_todo(done):
    """Đọc tên Hán từ DB ở chế độ chỉ đọc, bỏ các id đã dịch."""
    try:
        conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    except sqlite3.Error as e:
        print(f"Không mở được DB chỉ đọc: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        rows = conn.execute(
            "SELECT cbeta_id, title_zh FROM dila_catalog_works "
            "WHERE title_zh IS NOT NULL AND title_zh <> '' ORDER BY cbeta_id"
        ).fetchall()
    finally:
        conn.close()
    return [(cid, zh) for cid, zh in rows if cid not in done]


def build_prompt(batch):
    lines = "\n".join(f"{cid} | {zh}" for cid, zh in batch)
    return PROMPT_HEAD + lines


def parse_response(text, batch):
    """Trả về dict id -> vi nếu đủ và đúng mọi id; ngược lại None (cả lô không ghi)."""
    try:
        data = json.loads(text)
    except ValueError:
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except ValueError:
            return None
    if not isinstance(data, list):
        return None
    got = {}
    for item in data:
        if isinstance(item, dict) and item.get("id") and item.get("vi"):
            got[str(item["id"])] = str(item["vi"]).strip()
    expected = {cid for cid, _ in batch}
    if set(got) != expected:
        return None
    return got


def call_gemini(key, prompt, counter):
    """Gọi một yêu cầu. Trả về (text, lỗi, hết_hạn_mức_ngày)."""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    for attempt in range(RETRY_429 + 1):
        if counter["used"] >= counter["limit"]:
            return None, "đạt giới hạn --max-requests", False
        counter["used"] += 1
        try:
            resp = requests.post(URL.format(model=MODEL), headers=headers, json=body, timeout=120)
        except requests.RequestException as e:
            return None, f"lỗi mạng: {type(e).__name__}", False
        if resp.status_code == 429:
            if "PerDay" in resp.text:
                return None, "hết hạn mức ngày", True
            time.sleep(SLEEP_429 * (attempt + 1))
            continue
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}", False
        try:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError):
            return None, "phản hồi không đúng cấu trúc", False
        return text, None, False
    return None, "vẫn 429 sau khi thử lại", False


def main():
    ap = argparse.ArgumentParser(description="T484 Gemini free dịch tên Kinh (nháp, không ghi DB)")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in số lô, không gọi API")
    ap.add_argument("--max-requests", type=int, default=20, help="giới hạn yêu cầu HTTP thực tế")
    args = ap.parse_args()

    done = load_done(OUT)
    todo = load_todo(done)
    batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    print(f"Đã có {len(done)} tên trong nháp; còn {len(todo)} tên, {len(batches)} lô x {BATCH_SIZE}.")

    if args.dry_run:
        print("Dry-run: không gọi API.")
        return 0

    key = load_key()
    if not key:
        print("Thiếu GEMINI_API_KEY trong .env hoặc môi trường.", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    counter = {"used": 0, "limit": args.max_requests}
    ok_items = bad_batches = 0
    stop_reason = None
    with open(OUT, "a", encoding="utf-8") as out:
        for batch in batches:
            text, err, daily = call_gemini(key, build_prompt(batch), counter)
            if err:
                stop_reason = err
                if daily or "giới hạn" in err:
                    break
                bad_batches += 1
                time.sleep(SLEEP_OK)
                continue
            mapping = parse_response(text, batch)
            if mapping is None:
                bad_batches += 1
                print(f"Lô {batch[0][0]}…{batch[-1][0]}: phản hồi thiếu/lệch id, bỏ qua lô.")
            else:
                ts = datetime.now().isoformat(timespec="seconds")
                for cid, zh in batch:
                    out.write(json.dumps({"cbeta_id": cid, "title_zh": zh, "gemini_vi": mapping[cid],
                                          "model": MODEL, "ts": ts}, ensure_ascii=False) + "\n")
                out.flush()
                ok_items += len(batch)
            time.sleep(SLEEP_OK)

    print(f"Yêu cầu HTTP đã dùng: {counter['used']}. Tên mới ghi: {ok_items}. Lô lỗi: {bad_batches}.")
    if stop_reason:
        print(f"Dừng: {stop_reason}. Chạy lại sau; các id đã ghi sẽ được bỏ qua.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
