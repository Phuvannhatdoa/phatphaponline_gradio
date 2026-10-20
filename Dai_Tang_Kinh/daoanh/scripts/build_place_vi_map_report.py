# -*- coding: utf-8 -*-
"""build_place_vi_map_report.py — [T427] báo cáo trạng thái tab "🗺️ Place" (namevimap.html).

CHỈ ĐỌC DB — không ghi, không sửa dữ liệu.

Tính COUNT theo từng bộ lọc của tab Place (Tất cả / Pass 100% / Cần duyệt /
Thiếu Claude / Thiếu Gemini / Thiếu TTL) trên danh sách gốc `places_dila`
(59.167 địa danh, ID dài PL + 12 số). Đồng thời quét phát hiện 2 nhóm lỗi
dữ liệu đã ghi trong tasks/T427-...: lỗi mã hoá (name_vi chứa ký tự '?' do
mojibake) và cặp lệch name_vi giữa bản ID ngắn (8 ký tự) và ID dài (14 ký tự)
của cùng một địa danh trong namevi_map_places (biết nhưng KHÔNG tự sửa trong
giai đoạn 1 — xem RC note trong file task).

Output: docs/reports/place-vi-map-status.md

Usage:
    python -X utf8 scripts/build_place_vi_map_report.py            # ghi report
    python -X utf8 scripts/build_place_vi_map_report.py --stdout   # chỉ in
"""
import argparse
import io
import os
import sqlite3
import sys
import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
OUT = os.path.join(DAOANH, 'docs', 'reports', 'place-vi-map-status.md')


def pct(n, total):
    if not total:
        return '0.0%'
    return f'{(100.0 * n / total):.1f}%'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stdout', action='store_true', help='Chỉ in ra stdout, không ghi file')
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total_places = conn.execute("SELECT COUNT(*) FROM places_dila").fetchone()[0]

    agg = conn.execute("""
        SELECT
            SUM(CASE WHEN m.id IS NULL OR m.vn_name_status IS NULL OR m.vn_name_status != 'reviewed' THEN 1 ELSE 0 END) AS needs_review_n,
            SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM vn_person_places vp WHERE vp.place_id = pd.id) THEN 1 ELSE 0 END) AS no_ttl_n,
            SUM(CASE WHEN m.id IS NULL THEN 1 ELSE 0 END) AS no_namevi_row_n
        FROM places_dila pd
        LEFT JOIN namevi_map_places m ON m.dila_id = pd.id
    """).fetchone()

    needs_review_n = agg['needs_review_n']
    no_ttl_n = agg['no_ttl_n']
    no_namevi_row_n = agg['no_namevi_row_n']
    pass100_n = 0          # Giai đoạn 1: chưa có Claude/Gemini cho địa danh -> luôn 0
    no_claude_n = total_places  # Chưa có bảng ai_place_name (giai đoạn 2)
    no_gemini_n = total_places  # Chưa có bảng codex_place_name (giai đoạn 2)

    # Lỗi mã hoá: name_vi chứa ký tự '?' literal (mojibake khi import, không phải dấu hỏi thật)
    garble_long = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE length(dila_id) = 14 AND name_vi LIKE '%?%'"
    ).fetchone()[0]
    garble_all = conn.execute(
        "SELECT COUNT(*) FROM namevi_map_places WHERE name_vi LIKE '%?%'"
    ).fetchone()[0]
    garble_rows = conn.execute(
        "SELECT dila_id, name_vi FROM namevi_map_places WHERE length(dila_id) = 14 AND name_vi LIKE '%?%' LIMIT 20"
    ).fetchall()

    # Cặp lệch: cùng name_zh, một bản ID ngắn (<14) và một bản ID dài (=14) trong
    # namevi_map_places có name_vi KHÁC NHAU. (Biết nhưng không tự sửa — xem RC note T427.)
    mismatch_n = conn.execute("""
        SELECT COUNT(*) FROM namevi_map_places ml
        JOIN namevi_map_places ms
            ON ms.name_zh = ml.name_zh AND length(ms.dila_id) < 14 AND length(ml.dila_id) = 14
        WHERE ml.name_vi != ms.name_vi
    """).fetchone()[0]
    mismatch_rows = conn.execute("""
        SELECT ml.dila_id AS long_id, ms.dila_id AS short_id, ml.name_zh AS name_zh,
               ml.name_vi AS long_name_vi, ms.name_vi AS short_name_vi
        FROM namevi_map_places ml
        JOIN namevi_map_places ms
            ON ms.name_zh = ml.name_zh AND length(ms.dila_id) < 14 AND length(ml.dila_id) = 14
        WHERE ml.name_vi != ms.name_vi
        LIMIT 20
    """).fetchall()

    conn.close()

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = []
    lines.append('# Báo cáo trạng thái tab "🗺️ Place" (namevimap.html) — T427')
    lines.append('')
    lines.append(f'Sinh tự động bởi `scripts/build_place_vi_map_report.py` lúc {now}. Chỉ đọc DB, không ghi.')
    lines.append('')
    lines.append('## Tổng quan')
    lines.append('')
    lines.append(f'- Danh sách gốc: `places_dila` — **{total_places:,} địa danh** (ID dài `PL` + 12 số).')
    lines.append(f'- Địa danh chưa có dòng `namevi_map_places` (ID dài) nào: **{no_namevi_row_n:,}** ({pct(no_namevi_row_n, total_places)}) — cột "name_vi hiện tại" hiện "—".')
    lines.append('')
    lines.append('## Số liệu theo 6 bộ lọc (tab Place)')
    lines.append('')
    lines.append('| Bộ lọc | Số dòng | % trên tổng |')
    lines.append('|---|---:|---:|')
    lines.append(f'| 📋 Tất cả | {total_places:,} | 100.0% |')
    lines.append(f'| ✅ Pass 100% | {pass100_n:,} | {pct(pass100_n, total_places)} |')
    lines.append(f'| 🟡 Cần duyệt | {needs_review_n:,} | {pct(needs_review_n, total_places)} |')
    lines.append(f'| ⬜ Thiếu Claude | {no_claude_n:,} | {pct(no_claude_n, total_places)} |')
    lines.append(f'| ⬜ Thiếu Gemini | {no_gemini_n:,} | {pct(no_gemini_n, total_places)} |')
    lines.append(f'| ⬜ Thiếu TTL | {no_ttl_n:,} | {pct(no_ttl_n, total_places)} |')
    lines.append('')
    lines.append('**Ghi chú luật Pass 100%:** giai đoạn 1 chưa có cột Claude/Gemini cho địa danh')
    lines.append('(chưa có bảng `ai_place_name` / `codex_place_name`) nên **không dòng nào có thể đạt')
    lines.append('Pass 100%** cho tới khi chạy AI phiên âm 59K địa danh (giai đoạn 2, ngoài phạm vi T427).')
    lines.append('')
    lines.append('**Ghi chú cột TTL:** `vn_person_places` chỉ có 46 địa danh (slug TTL, chưa map DILA')
    lines.append('Place ID) nên gần như mọi dòng đều "Thiếu TTL" — đây là tình trạng dữ liệu thật,')
    lines.append('không phải lỗi API.')
    lines.append('')
    lines.append('## Lỗi dữ liệu phát hiện khi quét (biết, KHÔNG tự sửa trong T427 giai đoạn 1)')
    lines.append('')
    lines.append(f'### Lỗi mã hoá (mojibake — name_vi chứa ký tự `?` không phải dấu hỏi thật)')
    lines.append('')
    lines.append(f'- Trên bản ID dài (dùng cho tab Place): **{garble_long}** dòng.')
    lines.append(f'- Trên toàn bộ `namevi_map_places` (ID ngắn + ID dài): **{garble_all}** dòng.')
    if garble_rows:
        lines.append('')
        lines.append('| dila_id (dài) | name_vi (lỗi) |')
        lines.append('|---|---|')
        for r in garble_rows:
            lines.append(f"| `{r['dila_id']}` | {r['name_vi']} |")
    lines.append('')
    lines.append('### Cặp lệch name_vi giữa bản ID ngắn và bản ID dài (cùng `name_zh`)')
    lines.append('')
    lines.append(f'- Tổng: **{mismatch_n:,}** cặp (đối chiếu theo `name_zh` trùng khớp giữa 1 dòng ID')
    lines.append('  ngắn và 1 dòng ID dài trong `namevi_map_places` — không phải đối chiếu theo số ID,')
    lines.append('  vì 2 hệ ID ngắn/dài được đánh số độc lập, không suy ra nhau bằng phép toán chuỗi).')
    lines.append('- Admin RC (2026-10-19) từng ghi nhận ước tính "8.440 cặp lệch" bằng phương pháp khác;')
    lines.append('  số liệu ở đây đo lại bằng SQL join theo `name_zh` nên có thể khác do trùng tên')
    lines.append('  (nhiều địa danh có cùng `name_zh` nhưng là 2 nơi khác nhau). Không dọn dữ liệu')
    lines.append('  trong task này — chỉ ghi nhận để Admin quyết định có cần ETL đối soát riêng không.')
    if mismatch_rows:
        lines.append('')
        lines.append('| ID dài | ID ngắn | Hán tự | name_vi (dài) | name_vi (ngắn) |')
        lines.append('|---|---|---|---|---|')
        for r in mismatch_rows:
            lines.append(f"| `{r['long_id']}` | `{r['short_id']}` | {r['name_zh']} | {r['long_name_vi']} | {r['short_name_vi']} |")
    lines.append('')
    lines.append('---')
    lines.append('_Script: `scripts/build_place_vi_map_report.py` — chạy lại bất cứ lúc nào để cập nhật số liệu._')
    lines.append('')

    out_text = '\n'.join(lines)

    if args.stdout:
        print(out_text)
        return

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write(out_text)
    print(f'Đã ghi báo cáo: {OUT}')


if __name__ == '__main__':
    main()
