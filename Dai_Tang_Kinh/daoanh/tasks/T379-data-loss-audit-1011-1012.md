---
id: T379
title: "Điều tra sự cố mất dữ liệu 11/10–12/10 (ai_person_name, vn_person_authority, passage, 22 bảng)"
status: in_progress
created: 2026-10-13
updated: 2026-10-13
owner: claude-code (điều phối, giao daoanh-debugger)
parent: null
plan_approved_at: "2026-10-13 (Admin yêu cầu trực tiếp qua chat)"
dispatch: approved
done_when: >
  (1) Bảng so sánh chi tiết 3 bản DB: data/lineage.db (hiện tại, 159 bảng),
  data/backups/lineage.T265-lo-D-20261011-101118.db (11/10 10:11, 165 bảng),
  data/backups/lineage_2026-10-12.db (11/10 20:39, 148 bảng) — danh sách bảng mất,
  số dòng mất cho tối thiểu 20 bảng quan trọng (ai_person_name, vn_person_authority,
  passage, vn_person_relations, lineage_*, person_gen_*, codex_*, ...).
  (2) Kết quả PRAGMA quick_check trên bản 11/10 10:11 — ghi rõ pass/fail và chi tiết lỗi
  nếu có.
  (3) Truy nguyên docs/sessions/2026-10-11_T274_COMPLETION.md và
  docs/sessions/2026-10-11_T274-Option-A2-BUILD-REPORT.md: xác định lệnh backup/restore
  T274 đã chạy, có phải T274 restore lại bản cũ không, file
  lineage-T274-opt-a2-20261011_195516.db có mở được không (report ghi malformed).
  (4) Phân tích: 22 bảng mất là bảng nào, 39.269 dòng ai_person_name mất từ mốc nào,
  37K dòng passage mất từ mốc nào, có pattern lặp lại không.
  (5) Khuyến nghị khôi phục: bản nào dùng an toàn cho từng bảng, có thể khôi phục chọn
  lọc theo bảng hay phải restore toàn bộ, rủi ro schema mismatch.
  (6) Report lưu tại docs/sessions/2026-10-13/T379_DATA_LOSS_AUDIT.md.
  (7) Admin xác nhận DONE.
scope: >
  CHỈ ĐỌC — KHÔNG ghi/sửa bất kỳ file DB nào (lineage.db, các bản backup).
  Không restore, không migrate, không xóa trong task này. Chỉ phân tích và báo cáo.
revert: >
  Không áp dụng — task chỉ đọc, không có thay đổi để revert.
---

## Triệu chứng

- DB hiện tại (`data/lineage.db`): 159 bảng, `ai_person_name`=0 dòng, `vn_person_authority`=1.074 dòng.
- Bản backup 11/10 10:11 (`data/backups/lineage.T265-lo-D-20261011-101118.db`): 165 bảng,
  `ai_person_name`=39.269 dòng, `vn_person_authority`=1.507 dòng.
- Bản backup 11/10 20:39 (`data/backups/lineage_2026-10-12.db`): 148 bảng, `ai_person_name`=0,
  `vn_person_authority`=1.074 — giống DB hiện tại, không giống bản 10:11.
- Khoảng mất dữ liệu nằm giữa 10:11 AM và 20:39 PM ngày 11/10 — đúng khung giờ task T274 chạy.
- Report T274 (`docs/sessions/2026-10-11_T274_COMPLETION.md`) có dòng "Backup Used: Oct 10 restored"
  — nghi vấn T274 đã restore nhầm một bản DB cũ hơn, đè lên dữ liệu mới hơn (39.269 ai_person_name,
  ~37K passage records).

## Case tái hiện

So sánh trực tiếp 3 file `.db` bằng sqlite3 (table list, row count từng bảng), đối chiếu với
nội dung 2 file report T274 trong `docs/sessions/`. Không cần route/API — đây là audit dữ liệu
offline trên file DB, không phải bug UI.

## Nguyên nhân nghi ngờ

T274 (chạy ngày 11/10, khung giờ chiều/tối) có thể đã thực hiện restore DB từ một bản backup cũ
(trước 10:11 AM) thay vì backup mới nhất, làm mất các bảng/dòng được tạo ra trong khoảng 10:11–20:39
(ví dụ: kết quả transliterate Gemini 39.269 người, ~37K passage, 22 bảng khác).

## Phạm vi dự kiến

- Đọc 3 file DB bằng sqlite3 CLI (read-only, không mở ở mode ghi).
- Đọc 2 file report T274 trong `docs/sessions/2026-10-11*`.
- Đọc log `logs/ai_transliterate.log` nếu cần mốc thời gian.
- Không chạy UPDATE/DELETE/VACUUM/restore trên bất kỳ file DB nào.
- Output: 1 file report duy nhất tại `docs/sessions/2026-10-13/T379_DATA_LOSS_AUDIT.md`.
