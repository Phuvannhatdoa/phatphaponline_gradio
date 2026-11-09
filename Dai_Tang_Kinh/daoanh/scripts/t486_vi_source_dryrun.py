"""
T486 — Dry-run phân loại chênh lệch tên Việt giữa DB và file vn_dila_authority_catalog/*.vi.json.

Chỉ ĐỌC DB (mode=ro), chỉ GHI file CSV báo cáo. KHÔNG ghi DB.

Phân loại (áp dụng cho title_vi, byline_vi, contributor name_vi):
  A_format   : khác dấu gạch, khoảng trắng hoặc chữ hoa/thường, nội dung giống nhau.
  B_untrans  : bản DB chưa dịch (chỉ có chữ Latinh không dấu hoặc còn chữ Hán).
  C_review   : khác nội dung, Admin cần đọc chữ Hán để quyết định.

Cách chạy
---------
  python -X utf8 scripts/t486_vi_source_dryrun.py
"""

import csv
import glob
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..")
DB = os.path.join(BASE, "data", "lineage.db")
VI_DIR = os.path.join(BASE, "data", "dila_import", "authority_catalog.2026-10", "vn_dila_authority_catalog")
OUT_DIR = os.path.join(BASE, "docs", "sessions", "2026-10-29", "work-metadata")
OUT = os.path.join(OUT_DIR, "t486_dryrun.csv")

RE_CJK = re.compile(r"[㐀-鿿豈-﫿]")
RE_PUNCT = re.compile(r"[\s\-‐-―_.,;:()（）\[\]'\"]+")


def strip_marks(s):
    """Bỏ dấu tiếng Việt để so khớp không dấu."""
    nfd = unicodedata.normalize("NFD", s or "")
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn").replace("đ", "d").replace("Đ", "D")


def fmt_key(s):
    """Khoá so khớp định dạng: bỏ dấu, dấu gạch, khoảng trắng, chữ hoa/thường."""
    return RE_PUNCT.sub("", strip_marks(s or "")).lower()


def has_vi_diacritics(s):
    """Có dấu tiếng Việt hay không (dấu thanh hoặc đ/ơ/ư/â/ê/ô/ă)."""
    return any(ch != strip_marks(ch) for ch in (s or "")) or "đ" in (s or "").lower()


def classify(db_val, file_val):
    """Trả về nhóm A/B/C cho một cặp giá trị DB và file."""
    d = db_val or ""
    f = file_val or ""
    if d == f:
        return "same"
    if fmt_key(d) == fmt_key(f):
        return "A_format"
    if RE_CJK.search(d) or (not has_vi_diacritics(d) and re.fullmatch(r"[A-Za-z\s\-']+", d or "x")):
        return "B_untrans"
    return "C_review"


def walk(o, k=None):
    """Duyệt đệ quy để lấy mọi bản ghi có authorityID, kèm khoá cbeta_id (key của dict cha)."""
    if isinstance(o, dict):
        if "authorityID" in o:
            yield k, o
            return
        for kk, vv in o.items():
            yield from walk(vv, kk)
    elif isinstance(o, list):
        for x in o:
            yield from walk(x, k)


def load_db(conn):
    works = {}
    for cid, auth, t, bv, dv, cv in conn.execute(
            "SELECT cbeta_id, authority_id, title_vi, byline_vi, dynasty_vi, category_vi FROM dila_catalog_works"):
        works[auth] = {"cbeta_id": cid, "title_vi": t, "byline_vi": bv}
    contribs = {}
    for cid, pid, nv in conn.execute(
            "SELECT cbeta_id, person_id, name_vi FROM dila_catalog_contributors WHERE person_id IS NOT NULL"):
        contribs[(cid, pid)] = nv
    return works, contribs


def load_vi():
    vi_works = {}
    for path in glob.glob(os.path.join(VI_DIR, "*.vi.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for _, rec in walk(data):
            vi_works[rec["authorityID"]] = rec
    return vi_works


def main():
    try:
        conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    except sqlite3.Error as e:
        print(f"Không mở được DB chỉ đọc: {e}", file=sys.stderr)
        return 1

    works, contribs = load_db(conn)
    conn.close()
    vi = load_vi()

    rows = []
    counts = defaultdict(Counter)
    for auth, rec in vi.items():
        db = works.get(auth)
        if not db:
            continue
        cid = db["cbeta_id"]
        for field, file_key in (("title_vi", "title_vi"), ("byline_vi", "byline_vi")):
            cls = classify(db[field], rec.get(file_key))
            counts[field][cls] += 1
            if cls not in ("same",):
                rows.append([field, cid, auth, "", db[field], rec.get(file_key), cls])
        for ct in rec.get("contributors") or []:
            pid = ct.get("id")
            key = (cid, pid)
            if key not in contribs:
                continue
            cls = classify(contribs[key], ct.get("name_vi"))
            counts["contributor"][cls] += 1
            if cls != "same":
                rows.append(["contributor", cid, auth, pid, contribs[key], ct.get("name_vi"), cls])

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["field", "cbeta_id", "authority_id", "person_id", "db_value", "file_value", "group"])
        w.writerows(rows)

    print(f"Đã đọc {len(vi)} bản ghi file, {len(works)} bản ghi DB. Ghi CSV: {OUT}")
    for field, c in counts.items():
        total = sum(c.values())
        print(f"  {field}: tổng {total} | " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
