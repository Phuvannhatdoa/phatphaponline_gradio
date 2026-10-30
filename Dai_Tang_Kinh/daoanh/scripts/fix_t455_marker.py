# -*- coding: utf-8 -*-
"""Sửa marker T455 trong blob tasktodo đã stage (thêm link báo cáo + 3 phương án)."""
import os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
P = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions",
                 "2026-10-30-t455-analysis", "blobs",
                 "Dai_Tang_Kinh__daoanh__docs__tasktodo.md")

t = open(P, encoding="utf-8").read()

old = ("Còn chờ Admin: Q3b (thứ tự lô), Q3c (duyệt bảng lịch sử additive "
       "`people_name_vi_history`), mẫu 20 dòng/lô.")
new = ("**Còn chờ Admin: chọn phương án A/B/C** (báo cáo đầy đủ "
       "`docs/reports/T455-analysis-794-mismatch.md`: **A** = sửa 260 dòng có bằng chứng rõ "
       "(lô A 24 + lô C 236) · **B** = sửa cả 794 theo Cloud · **C** = sửa 260 + tra từ điển "
       "534 dòng lô B theo `so_lan`) + Q3c (duyệt bảng lịch sử additive `people_name_vi_history`).")
assert old in t, "khong khop cum T455"
t = t.replace(old, new, 1)

# thêm dòng giải thích ngắn về bản chất 3 lô (để Admin đọc ngay trên tasktodo)
old2 = "CSV: `docs/sessions/2026-10-28-t455/name_vi_mismatch_{A,B,C}.csv`."
new2 = ("CSV: `docs/sessions/2026-10-28-t455/name_vi_mismatch_{A,B,C}.csv`. "
        "Bản chất từng lô: **A** = ZQ hỏng rõ (để tên Anh / sót chữ Hán hiến, 17/24) · "
        "**B** = khác *quy ước đọc cả từ*, không phải lỗi kỹ thuật (ZQ đọc theo nghĩa chữ `Long Thụ`, "
        "Cloud theo cách gọi VN `Long Thọ`; 478/534 sai ≤ 1 từ, 0/534 sót Hán) · "
        "**C** = ZQ thiếu/sai 1 chữ (thiếu tiền tố `釋`/Thích) — charmap dự án xác nhận Cloud 188/236.")
assert old2 in t, "khong khop cum CSV T455"
t = t.replace(old2, new2, 1)

open(P, "w", encoding="utf-8", newline="").write(t)
print("tasktodo blob T455 updated: %d chars" % len(t))
print("co 'T455-analysis-794':", "T455-analysis-794" in t)
