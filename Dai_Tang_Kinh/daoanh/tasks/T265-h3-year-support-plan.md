---
id: T265
title: "H3 year-support — kế hoạch chi tiết xử lý 285 dòng CONFLICT (bảng quyết định + lô B/C/A)"
module: Data Integrity / Timeline / Evidence
priority: high
status: in_progress
created: 2026-10-08
updated: 2026-10-08
owner: claude-code
depends_on: [T263]
parent: T263
plan_approved_at: "2026-10-08 (Admin phê chuẩn đề xuất: bảng quyết định + duyệt từng lô)"
done_when: >
  Mọi dòng CONFLICT của T263 đều có quyết định ghi trong `timeline_year_support`
  (era_range / corrected / review có lý do). Sau đó P3: `audit_h3_conflicts.py --strict`
  chỉ được chặn khi còn dòng chưa có quyết định. KHÔNG hạ tiêu chuẩn để cho xanh.
revert: >
  Bảng mới: `DROP TABLE timeline_year_support` (không đụng bảng gốc).
  Toàn bộ DB: khôi phục từ `data/backups/lineage.T265-pre-support-20261008-173329.db`.
  Không dùng git (repo có index bất thường, xem CLAUDE.md).
former_ids: []
outcome: >
  2026-10-08: Bước 0 (lấy mẫu chỉ đọc) xong. Bước 1 (backup + tạo bảng) xong.
  Bước 2 (lô B, 74 id) xong: gắn `era_range`. Lô C (182 id) xong: gắn `review`,
  duyệt theo hướng review. Mỗi lô 1 transaction. `place_timeline_events` không đổi
  (3688 dòng). Còn lại: lô A, cập nhật audit, P3, P4. Chưa đổi exit code strict.
  2026-10-11: `place_timeline_events` tăng lên 4386 dòng (698 dòng event nhập sau
  khi lô B/C/A chốt) → audit_h3_conflicts.py phát hiện thêm 118 cặp (dila_id, year)
  CONFLICT CHƯA có quyết định: Nhóm B=5, Nhóm C=91, Nhóm A=22. Gọi đây là **Lô D**.
  Đã backup DB (`data/backups/lineage.T265-lo-D-20261011-101118.db`, quick_check=ok,
  4386 events) và xuất mẫu ngẫu nhiên (seed cố định 265118) để Admin duyệt trước:
  B=5/5 (toàn bộ, vì nhóm chỉ có 5), C=20/91, A=20/22 — tổng 45 dòng —
  tại `docs/evidence/T265_D_sample_for_admin_review.csv`.
  **Lô D chờ Admin duyệt mẫu trước khi gắn quyết định toàn lô** (tương tự quy trình
  B/C/A). CHƯA gắn `era_range`/`review`/`corrected` cho bất kỳ dòng nào của Lô D.
---

# T265 — Kế hoạch H3 year-support

Task con của **T263**. Mục tiêu và lý do xem `tasks/T263-h3-year-conflict-resolution.md`.
Task này ghi lại cách xử lý 285 dòng CONFLICT theo đề xuất đã được phê chuẩn.

## 1. Nguyên tắc

1. **Không tự sửa năm hàng loạt.** Ghi chú có thể chỉ chứng minh niên hiệu.
2. **Ghi quyết định, không giả vờ đã chứng minh.** Mỗi dòng có trạng thái rõ ràng.
3. **Từng lô nhỏ, có backup, hoàn tác được.** Mỗi lô là một lần ghi có kiểm tra.

## 2. Bảng quyết định (additive)

```sql
CREATE TABLE IF NOT EXISTS timeline_year_support (
    event_id    INTEGER PRIMARY KEY,   -- place_timeline_events.id
    dila_id     TEXT NOT NULL,
    year        INTEGER,               -- năm đang lưu tại thời điểm quyết định
    status      TEXT NOT NULL CHECK (status IN ('era_range','corrected','review')),
    reason      TEXT NOT NULL,
    decided_by  TEXT NOT NULL,
    decided_at  TEXT NOT NULL
);
```

Ý nghĩa trạng thái:
- `era_range`: năm nằm trong niên hiệu được ghi chú nêu. Chỉ chứng minh niên hiệu, **không** chứng minh đúng năm. Đây là mức hỗ trợ yếu, và phải hiển thị khác với "đã chứng minh năm".
- `corrected`: năm đã được sửa, có nguồn riêng, theo khuôn W4 (backup + manifest).
- `review`: chưa đủ bằng chứng, chờ người rà. Đây **không** phải là đã giải quyết.

Một cặp (dila_id, năm) có thể khớp nhiều id khi cùng khẳng định được lưu từ nhiều nguồn (ví dụ `wikidata` và `wikidata_p571`). Các id đó được áp cùng một quyết định.

## 3. Các bước

- [x] **Bước 0 — lấy mẫu, chỉ đọc.** 10 dòng mỗi nhóm, cố định seed. File: `docs/evidence/2026-10-08_T265_sample_step0.tsv`. Cột `kiem_tra_thu_cong` chưa điền, Admin cần rà trước khi duyệt lô C và A.
- [x] **Sao lưu DB.** `data/backups/lineage.T265-pre-support-20261008-173329.db` (1,7 GB), `PRAGMA quick_check` = ok, 3688 sự kiện.
- [x] **Tạo bảng `timeline_year_support`.** Bổ sung, không đổi `place_timeline_events`.
- [x] **Lô B (74 dòng TSV, 73 cặp, 74 id) → `era_range`.** 1 transaction, kết quả `era_range: 74`.
- [ ] **Admin rà mẫu bước 0** (cột `kiem_tra_thu_cong`: ĐÚNG / SAI / CẦN_NGUỒN). Đây là điều kiện trước khi duyệt C và A.
- [x] **Lô C (182 dòng) → `review`.** Admin duyệt theo hướng review (2026-10-08). 182 id, 1 transaction, backup `lineage.T265-pre-support-20261008-175514.db` (quick_check ok). Không sửa năm, không tách sự kiện. Việc tách sự kiện là bước riêng, cần người rà từng nguồn.
- [x] **Lô A (29 dòng) → `review`.** Xem từng dòng: không dòng nào có nguồn độc lập nên không sửa năm. 24/29 năm lưu là điểm giữa triều đại (`midpoint`), tức giá trị suy ra. QA `daoanh-qa` xác nhận ĐẠT (29 event, không có `corrected`, không có lệch).
- [x] **Cập nhật audit** để tính số dòng đã có quyết định (`daoanh-debugger` thực hiện, `daoanh-qa` ĐẠT). Exit thường 0, `--strict` vẫn 1. Lưu ý từ QA: đếm theo cặp (73/181) khác đếm theo dòng (74/182). P3 nên đếm theo `event_id`.
- [ ] **P3**: chặn `--strict` khi còn dòng chưa có quyết định. Chờ duyệt.
- [ ] **P4**: sửa 8 nhãn `民民國` → `民國`. Chờ duyệt.
- [ ] **Lô D (698 dòng event nhập sau → 118 cặp CONFLICT mới: B=5, C=91, A=22).**
  Backup xong (`lineage.T265-lo-D-20261011-101118.db`). Mẫu 45 dòng (B=5, C=20, A=20,
  seed 265118) tại `docs/evidence/T265_D_sample_for_admin_review.csv`. **Lô D chờ
  Admin duyệt mẫu trước khi gắn quyết định toàn lô.** Danh sách đầy đủ 118 cặp
  (chưa public, chỉ để đối chiếu nội bộ khi áp quyết định sau duyệt) đang ở
  scratchpad phiên làm việc, chưa commit vào repo.

## 4. Lệnh

Script: `scripts/t265_year_support.py` (`sample`, `backup`, `apply-b`, `status`).

## 5. Ghi chú

- Số liệu DB trong README dashboard (633 MB) đã cũ. Thực tế là 1,7 GB.
- Trong file TSV, cặp (PL000000058474, 1694) xuất hiện hai lần. Đây là một khẳng định trùng từ hai nguồn, không phải hai lỗi khác nhau.
