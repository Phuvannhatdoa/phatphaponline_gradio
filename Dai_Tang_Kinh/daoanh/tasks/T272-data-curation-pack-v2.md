---
id: T272
title: "Data curation pack v2 — làm lại tài liệu T203 theo quy tắc mới trên dữ liệu hiện tại"
module: Data Curation / People & Places
priority: high
status: in_progress
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
supersedes: docs/Mimo-Flash/T203-ADMIN-DATA-CURATION-PACK-01.md
plan_approved_at: "2026-10-10 (Admin phê chuẩn đề xuất: làm lại T203 theo quy tắc mới, trên dữ liệu hiện tại)"
done_when: >
  (1) Có tài liệu v2 chạy trên DB hiện tại (không dùng số liệu 2026-10-01).
  (2) Mọi nhóm trùng dila_id có bằng chứng DILA; không gộp chỉ vì trùng tên.
  (3) Không xóa dòng nào; gộp bằng đánh dấu merged_into, có sao lưu và cách hoàn tác.
  (4) Tên lỗi mã hóa khôi phục từ nhật ký quyết định gốc của Admin; bản dịch máy chỉ là gợi ý, cần Admin duyệt.
  (5) Mỗi lô có Admin duyệt riêng, QA độc lập bằng daoanh-qa.
  Không đánh DONE khi chưa có xác nhận Admin.
revert: >
  Gộp mềm: khôi phục bằng cách xóa trạng thái merged_into của các dòng trong lô (có sao lưu trước).
  Mọi lô có bản sao DB trong data/backups/ trước khi ghi.
outcome: >
  2026-10-10: lập kế hoạch thay thế T203 (dữ liệu 2026-10-01 đã cũ; quy tắc gộp theo tên bị bỏ).
---

# T272 — Data curation pack v2

Thay thế `docs/Mimo-Flash/T203-ADMIN-DATA-CURATION-PACK-01.md`. Tài liệu T203 giữ nguyên làm lịch sử, đánh dấu đã thay thế.

## 1. Vì sao làm lại

- T203 dựa trên dữ liệu ngày 2026-10-01 (33 nhóm). Hiện nay T223 ghi 29 nhóm / 61 dòng, và các quyết định T218, T223, T265 đã thay đổi trạng thái.
- T203 coi trùng tên là cùng người và đề xuất xóa dòng. Trái với nguyên tắc T223 (cần bằng chứng DILA) và chính sách T198 (xóa mềm, giữ lịch sử).
- T203 dùng bản dịch máy làm nguồn tên "chính thống" và tie-break kỹ thuật (trạng thái, id) để chọn dòng giữ.

## 2. Quy tắc mới

1. **Danh tính** chỉ dựa trên bằng chứng DILA (cùng dila_id có nguồn xác nhận, hoặc TTL/Marcus). Trùng tên không đủ.
2. **Chọn dòng chính** theo nguồn bằng chứng đã ghi, không theo tie-break kỹ thuật.
3. **Không xóa dòng.** Gộp mềm: dòng trùng được đánh dấu `merged_into = <dòng chính>`, giữ nguyên dữ liệu.
4. **Tên lỗi mã hóa** (ký tự `?` thay dấu): khôi phục từ nhật ký quyết định gốc (`en_audit_log`, `canonical_decision` có tên đúng). Không lấy từ `place_desc_vi_draft` làm quyết định.
5. **Mỗi lô có Admin duyệt riêng.** Lô nhỏ, có sao lưu DB trước khi ghi.

## 3. Các bước

- [ ] **Bước 1 — Kiểm trạng thái hiện tại (chỉ đọc):** đếm nhóm trùng dila_id, đếm dòng tên lỗi mã hóa, xác nhận số liệu so với T223 (29 nhóm).
- [ ] **Bước 2 — Phân loại nhóm theo bằng chứng DILA:** mỗi nhóm ghi nguồn xác nhận (cùng người / khác người / chưa rõ). Không dùng trùng tên làm bằng chứng.
- [ ] **Bước 3 — Rà tên lỗi mã hóa:** tìm tên gốc trong nhật ký quyết định. Ghi nguồn cho từng dòng.
- [ ] **Bước 4 — Tài liệu v2:** `docs/Mimo-Flash/T272-DATA-CURATION-PACK-v2.md` với số liệu hiện tại, bảng quyết định cho Admin, và ghi T203 là đã thay thế.
- [ ] **Bước 5 — Thực hiện theo lô đã duyệt:** gộp mềm, sao lưu DB trước mỗi lô, kiểm số đếm sau ghi.
- [ ] **Bước 6 — QA** bằng `daoanh-qa`.
- [ ] **Admin xác nhận DONE.**

## 4. Ràng buộc

- Không xóa dòng. Không đổi schema.
- Không git. Không deploy VPS.
- Không dùng bản dịch máy làm quyết định tên.
- Mọi ghi DB có sao lưu và có cách hoàn tác.

## 5. Liên quan

- T203 (đã thay thế), T200, T218, T223, T265, T198 (chính sách xóa mềm).
