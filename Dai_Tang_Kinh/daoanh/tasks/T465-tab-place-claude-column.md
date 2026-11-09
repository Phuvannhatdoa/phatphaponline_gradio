---
id: T465
title: "Bug verify: cột Claude trên Tab Place hiện '—' dù XML đã dịch ~57K place"
status: done
created: 2026-10-26
updated: 2026-10-26
done_when: "Cột Claude trên Tab Place (namevimap.html) hiển thị giá trị name_vi đúng theo dila_id từ nguồn Claude đã import (hoặc, nếu bảng claude_place_name chưa tồn tại, task dừng ở trạng thái chờ Admin duyệt tạo bảng/apply import, không tự ý CREATE TABLE/ghi DB), có bằng chứng trình duyệt thật (screenshot trước/sau, network log, đối chiếu ID mẫu PL000000000009/PL000000000019/PL000000000168)."
---

## Mô tả

Admin báo: đã dịch xong XML phiên âm Claude (`data/phien_am/vn_place_name_vi.xml`, nhánh
`claude/sleepy-tesla-qsx17b`) cho khoảng 57K địa danh, nhưng cột "Claude" trên Tab Place
tại `http://127.0.0.1:8080/daoanh/admin/namevimap.html` vẫn hiện "—" ở mọi dòng.

### Triệu chứng
- Route/case: `admin/namevimap.html` → Tab Place.
- Mọi dòng cột Claude = "—".

### Nguyên nhân nghi ngờ (đã khảo trước, chưa xác nhận lại)
- `api_places_vi_map_list()` trong `daoanh/app.py` (khoảng dòng 11899–12020) đang gán cứng
  `claude_name_vi=None` (placeholder giai đoạn 2 — xem T440).
- T445 (`tasks/T445-claude-place-name-import.md`) đã dry-run ra
  `docs/sessions/2026-10-21/claude_place_name_dryrun.csv` (59.353 dòng) và đề xuất bảng
  `claude_place_name(dila_id TEXT PRIMARY KEY, name_zh, name_vi, tier, source, imported_at)`
  — CHƯA được Admin duyệt tạo, CHƯA apply vào `data/lineage.db`.

### Phạm vi dự kiến
1. Xác nhận bảng `claude_place_name` có tồn tại trong `lineage.db` chưa (chỉ SELECT
   sqlite_master, không ghi).
2. Nếu CHƯA có bảng/dữ liệu: KHÔNG CREATE TABLE, KHÔNG import — dừng và hỏi Admin duyệt
   quy trình dry-run → duyệt → `--apply` (có backup DB + ghi `docs/ROLLBACK.md`).
3. Nếu ĐÃ có dữ liệu: chỉ sửa `api_places_vi_map_list()` để JOIN đúng theo `dila_id`
   (cùng cách cột Gemini `ai_place_name` đang JOIN), không hard-code giá trị trong UI.
4. Không đụng `district_*` (việc sau), không sửa `dashboard/`, không sửa task khác.

### Không thuộc phạm vi
- Import/transliterate dữ liệu mới.
- Tạo bảng DB khi chưa có duyệt của Admin.
