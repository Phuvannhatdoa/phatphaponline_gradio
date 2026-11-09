"""
T483 — Dry-run đối chiếu Mục Lục Đại Tạng Kinh (Nguyễn Minh Tiến, cbeta_catalog_vn)
với danh mục tác phẩm DILA (dila_catalog_works) để chuẩn hóa tên Việt khâu Catalog.

Chỉ đọc, KHÔNG ghi DB. Kết quả là một CSV để Admin duyệt từng nhóm.

Logic phân loại (theo thứ tự ưu tiên):
  1. NO_MATCH        — tên Hán gốc không có trong DILA.
  2. MULTI_T         — nhiều ứng viên DILA nhưng đúng 1 ứng viên thuộc tạng T → lấy ứng viên T.
  3. MULTI_AMBIG     — nhiều ứng viên, không chọn được → Admin quyết.
  4. SAME            — 1 ứng viên, tên Việt giống sau chuẩn hóa (bỏ dấu, gạch, khoảng trắng).
  5. STYLE           — 1 ứng viên, khác nhau nhưng độ giống chữ cao (≥ 0,80), khả năng chỉ khác cách viết.
  6. DIFF            — 1 ứng viên, khác rõ ràng → Admin duyệt.
  7. SUSPECT_MISALIGN — DIFF và độ giống chữ rất thấp (< 0,30): nghi dòng Mục Lục bị lệch.

Usage
-----
  python -X utf8 scripts/t483_mlk_dila_dryrun.py
"""

import csv
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "data", "lineage.db")
OUT = os.path.join(HERE, "..", "docs", "sessions", "2026-10-28", "catalog", "t483_mlk_dila_dryrun.csv")


def base_zh(title):
    """Bỏ phần chú thích quyển và tác giả, chỉ giữ tên Hán gốc."""
    return re.split(r"\s*[\(（]", title, maxsplit=1)[0].strip()


def clean_vi(title):
    """Bỏ đuôi cắt dở kiểu '(1' hoặc '(30' do Mục Lục bị tách sai."""
    return re.sub(r"\s*\(\d*$", "", title or "").strip()


def norm_vi(title):
    """Chuẩn hóa để so sánh: bỏ dấu, gạch nối, khoảng trắng, đưa về chữ thường."""
    t = unicodedata.normalize("NFD", (title or "").lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return re.sub(r"[\s\-]+", "", t)


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def load_rows(conn):
    """Đọc Mục Lục và danh mục DILA, mỗi bảng một lần (generator-free vì dữ liệu nhỏ, ~6K dòng)."""
    mlk = conn.execute(
        "SELECT id, title_vi, title_zh, translator_vi, dynasty_vi "
        "FROM cbeta_catalog_vn WHERE title_zh IS NOT NULL AND title_zh <> ''"
    ).fetchall()
    dila = conn.execute(
        "SELECT cbeta_id, title_zh, title_vi, vol FROM dila_catalog_works "
        "WHERE title_zh IS NOT NULL AND title_zh <> ''"
    ).fetchall()
    return mlk, dila


def classify(zh_base, mlk_vi_clean, candidates):
    """Trả về (nhóm, cbeta_id được chọn, title_vi DILA được chọn, ghi chú)."""
    if not candidates:
        return "NO_MATCH", "", "", ""
    if len(candidates) > 1:
        t_only = [c for c in candidates if (c[3] or "").upper().startswith("T")]
        if len(t_only) == 1:
            chosen = t_only[0]
            return _compare(mlk_vi_clean, chosen, "MULTI_T", f"{len(candidates)} ứng viên, chọn tạng T")
        ids = ";".join(c[0] for c in candidates)
        return "MULTI_AMBIG", "", "", f"ứng viên: {ids}"
    return _compare(mlk_vi_clean, candidates[0], "", "")


def _compare(mlk_vi_clean, chosen, prefix, note):
    cid, _zh, dila_vi, _vol = chosen
    dila_vi = dila_vi or ""
    if norm_vi(mlk_vi_clean) == norm_vi(dila_vi):
        group = "SAME"
    else:
        score = similarity(norm_vi(mlk_vi_clean), norm_vi(dila_vi))
        if score >= 0.80:
            group = "STYLE"
        elif score < 0.30:
            group = "SUSPECT_MISALIGN"
        else:
            group = "DIFF"
        note = (note + f"; độ giống {score:.2f}").strip("; ")
    if prefix:
        group = f"{prefix}->{group}"
    return group, cid, dila_vi, note


def main():
    try:
        conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    except sqlite3.Error as e:
        print(f"Không mở được DB ở chế độ chỉ đọc: {e}", file=sys.stderr)
        return 1

    try:
        mlk, dila = load_rows(conn)
    except sqlite3.Error as e:
        print(f"Lỗi đọc bảng (kiểm tra schema): {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    by_zh = defaultdict(list)
    for cid, zh, vi, vol in dila:
        by_zh[zh].append((cid, zh, vi, vol))

    rows = []
    for mid, mlk_vi_raw, mlk_zh, translator, dynasty in mlk:
        zh_b = base_zh(mlk_zh)
        vi_clean = clean_vi(mlk_vi_raw)
        truncated = "có" if vi_clean != (mlk_vi_raw or "").strip() else ""
        group, cid, dila_vi, note = classify(zh_b, vi_clean, by_zh.get(zh_b, []))
        rows.append({
            "mlk_id": mid,
            "zh_goc": zh_b,
            "mlk_vi": vi_clean,
            "mlk_cat_bi_cat_cuoi": truncated,
            "nhom": group,
            "dila_cbeta_id": cid,
            "dila_vi_hien_tai": dila_vi,
            "dich_gia_mlk": translator or "",
            "trieu_dai_mlk": dynasty or "",
            "ghi_chu": note,
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    try:
        with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    except OSError as e:
        print(f"Không ghi được CSV: {e}", file=sys.stderr)
        return 1

    counts = Counter(r["nhom"] for r in rows)
    print(f"Đã xử lý {len(rows)} dòng Mục Lục → {OUT}")
    for g, n in counts.most_common():
        print(f"  {g:<24} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
