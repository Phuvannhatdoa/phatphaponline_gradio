# 2026-08-17 — HOME GUI Feature Status Dashboard

## Thay đổi

### `dashboard/dashboard_process.html`
- Thêm section **"HOME GUI — Chức Năng Theo Kế Hoạch Thiết Kế"** giữa directive tracker và module grid
- Hiển thị 8 feature HOME được map theo tab: 地 Thực Thể, ⏱ Niên Đại, 📜 Đại Tạng, 🕸 Đồ Thị, 💬 Hỏi Đáp, Bản đồ GIS
- Đọc từ `directives_progress.json` (completed_task_ids) + `progress_data.json` (task statuses từ .md files)
- Status logic: `done` = task .md file status == done; `partial` = trong completed_task_ids của directives; `pending` = chưa
- Metric note hiển thị cho task done: "94.4% name_vi (45,938/48,673)" cho T01, "117,391 rows" cho T14
- Added CSS: `.hf-grid`, `.hf-tab-group`, `.hf-tab-header`, `.hf-feature-row`, `.hf-status.done/partial/pending`, `.hf-metric`, `.hf-legend`

### `data/progress_data.json`
- Rebuilt bằng `python scripts/build_progress_data.py`
- Kết quả: 17 tasks, done=3 (T01, T09, T14), 64% tổng tiến độ

## Trạng thái features (2026-08-17)
| Tab | Feature | Task | Status |
|-----|---------|------|--------|
| 地 Thực Thể | Tên & Tiểu Sử Nhân Vật | T01 | ✓ DONE (94.4% name_vi) |
| 地 Thực Thể | Nhân Vật Liên Quan + NEXUS Badge | T16 | ◑ Partial (BDRC Adapter done, criteria chưa tick) |
| ⏱ Niên Đại | Time Grid | T14 | ✓ DONE (117,391 rows) |
| 📜 Đại Tạng | CBETA Passages | T02 | ○ Pending |
| 📜 Đại Tạng | Nút Dịch Mượt | T12 | ○ Pending |
| 🕸 Đồ Thị | Knowledge Graph | T17 | ○ Pending |
| 💬 Hỏi Đáp | RAG Chat | T11 | ○ Pending |
| Bản đồ GIS | Cluster Click zoom | T06 | ○ Pending |

## Ghi chú
- T16 task file vẫn `pending` vì acceptance criteria chưa được tick hết. `directives_progress.json` ghi "BDRC Adapter completed" — dashboard hiện là `partial` để phân biệt.
- Admin cần mở T16 popup directive và hoàn tất phần còn lại trước khi mark done.
