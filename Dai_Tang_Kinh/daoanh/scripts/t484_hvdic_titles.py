"""
T484 — Phiên âm Hán-Việt tên Kinh bằng HVDic (hvdic.thivien.net), mỗi tên một yêu cầu.

Chỉ đọc DB, chỉ ghi file nháp JSONL, KHÔNG ghi DB.
Chạy lại được: các cbeta_id đã có trong file nháp sẽ được bỏ qua.

Cách chạy
---------
  python -X utf8 scripts/t484_hvdic_titles.py --dry-run
  python -X utf8 scripts/t484_hvdic_titles.py            # chạy toàn bộ (~1,5 giờ)
  python -X utf8 scripts/t484_hvdic_titles.py --limit 20  # thử vài dòng
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
from datetime import datetime

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..")
DB = os.path.join(BASE, "data", "lineage.db")
OUT = os.path.join(BASE, "docs", "sessions", "2026-10-28", "catalog", "t484_hvdic_titles.jsonl")

URL = "https://hvdic.thivien.net/transcript-query.json.php"
HEADERS = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
SLEEP_OK = 1.0
RETRY = 3


def base_zh(title):
    """Tên Hán gốc: bỏ phần chú thích quyển và tác giả."""
    return re.split(r"\s*[\(（]", title or "", maxsplit=1)[0].strip()


def load_done(path):
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                done.add(json.loads(line)["cbeta_id"])
            except (ValueError, KeyError):
                continue
    return done


def load_todo(done):
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
    return [(cid, base_zh(zh)) for cid, zh in rows if cid not in done and base_zh(zh)]


def hvdic_reading(text):
    """Trả về (phiên âm, số ký tự không có âm). None nếu lỗi."""
    payload = f"mode=trans&lang=1&input={urllib.parse.quote(text)}"
    for attempt in range(RETRY):
        try:
            resp = requests.post(URL, headers=HEADERS, data=payload.encode("utf-8"), timeout=15)
            resp.raise_for_status()
            result = resp.json().get("result", [])
        except (requests.RequestException, ValueError):
            time.sleep(2 * (attempt + 1))
            continue
        parts, missing = [], 0
        for el in result:
            opts = el.get("o") or []
            if opts:
                parts.append(opts[0])
            else:
                missing += 1
        return " ".join(parts), missing
    return None


def main():
    ap = argparse.ArgumentParser(description="T484 HVDic phiên âm tên Kinh (nháp, không ghi DB)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="0 = không giới hạn")
    args = ap.parse_args()

    done = load_done(OUT)
    todo = load_todo(done)
    if args.limit:
        todo = todo[:args.limit]
    print(f"Đã có {len(done)} tên trong nháp; cần làm {len(todo)} tên.")
    if args.dry_run:
        print("Dry-run: không gọi HVDic.")
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ok = failed = 0
    with open(OUT, "a", encoding="utf-8") as out:
        for cid, zh in todo:
            res = hvdic_reading(zh)
            if res is None:
                failed += 1
                print(f"Lỗi HVDic: {cid}, bỏ qua để chạy lại sau.")
            else:
                reading, missing = res
                out.write(json.dumps({"cbeta_id": cid, "title_zh": zh, "hvdic_vi": reading,
                                      "chars_without_reading": missing,
                                      "ts": datetime.now().isoformat(timespec="seconds")},
                                     ensure_ascii=False) + "\n")
                out.flush()
                ok += 1
            time.sleep(SLEEP_OK)
    print(f"Ghi được: {ok}. Lỗi: {failed}. File: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
