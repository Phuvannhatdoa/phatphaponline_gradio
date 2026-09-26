# Audit / Bug Fix Report — <TASK_OR_BUG_SLUG>

> Template báo cáo bắt buộc khi sửa bug data/UI trong Đạo Ảnh (PTDA).
> Lưu tại `docs/<slug>_REPORT.md`. Quy tắc chi tiết: xem skill `daoanh-data-ui-debug`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `...` (table, column, giới hạn rows test) |
| API endpoint | `GET/POST /daoanh/api/...` |
| Resolver / logic | `app.py:<line>` hoặc JS function |
| Component / renderer | `<file>.html:<line/function>` |
| Schema contract | trước / sau |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** data | mapping | API contract | resolver | renderer | layout | state | async
- **Nguyên nhân chính xác:** <vì sao sai — kèm 1 query/1 response mẫu minh chứng>

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data | `...` | `...` |
| API response | `...` | `...` |

## 4. Files changed

- `daoanh/...` — lý do thay đổi (ngắn, per file)

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Lệnh dry-run: `...`
- Backup: `data/lineage.db.backup_<task>_YYYYMMDD_HHMMSS`
- Revert: `git revert <hash>` (xem `docs/ROLLBACK.md`) — hoặc lệnh script `--revert`

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu | ... | ... | ... | ✅ |
| Fallback (empty/null/duplicate/homonym) | ... | ... | ... | ✅ |

## 7. Limitation / data gap còn lại

- <còn thiếu dữ liệu / chưa cover output / blocker>...