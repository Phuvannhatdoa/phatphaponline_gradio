# Đạo Ảnh — Claude Code Project Context

## Dự án
Buddhist GIS & Dictionary System cho Phật học Việt Nam.  
Production: `phatphaponline.org/daoanh/`  
Local dev: `http://localhost:8080/daoanh/`

---

## Kiến trúc 2-server

| Server | File | Port | Vai trò |
|--------|------|------|---------|
| Main app | `app.py` | 5000 | 131 routes, toàn bộ business logic |
| Auth gateway | `server.py` | 5001 | Login, admin whitelist |
| Local nginx | `local_gateway.py` | 8080 | Static files + reverse proxy (local only) |

VPS dùng nginx thật. `local_gateway.py` là bản thay thế nginx để dev local.

---

## Khởi động local

```powershell
# Chạy từ thư mục daoanh/  — cần 3 cửa sổ riêng hoặc background
python server.py > server_local.log 2>&1
python app.py    > app_local.log    2>&1
python local_gateway.py > gateway_local.log 2>&1
```

Kiểm tra server đang chạy:
```powershell
Get-NetTCPConnection -LocalPort 5000,5001,8080 -State Listen | Select LocalPort
```

---

## Database

`data/lineage.db` — SQLite, 664MB, 67 tables.  
Đây là nguồn dữ liệu duy nhất đáng tin. Không có ORM — query trực tiếp SQLite.

---

## Trạng thái dự án (audit 2026-08-11)

| Module | Thực tế | Ghi chú |
|--------|---------|---------|
| Place Authority (DILA) | ~85% | 59,167 rows, 67% mapped tiếng Việt |
| Person Authority | ~40% | 48,673 rows — `name_vi`/`bio` = 0% |
| Person curated | ~0.004% | 2/48,673 rows đã duyệt |
| GIS Map | ~70% | places.html + marker clustering |
| Time Authority | 0% | `time_periods` table = 0 rows |
| Nexus Points | 0% | Không có route trong code |
| RAG | 0% | Không có vector index, không có `/api/rag/*` |

> **Lưu ý:** README.md cũ ghi "~99%" — đó là thông tin sai. Tin vào bảng trên.

---

## Tài liệu — thứ tự tin cậy

1. `docs/claudecode-report.md` — audit thực tế 2026-08-11, **tin nhất**
2. Grep trực tiếp `app.py` / query trực tiếp `lineage.db`
3. `docs/progress.md`, `docs/tasktodo.md` — tự báo cáo, khá cập nhật
4. `docs/roadmap.md` — kế hoạch dài hạn, chưa thực hiện
5. `docs/DEV_HISTORY.md` — lưu trữ lịch sử, nhiều claim đã bị bác bỏ

---

## Quy tắc trước khi sửa code

1. **Backup** file sắp sửa vào `docs/sessions/YYYY-MM-DD/` (copy nguyên file)
2. **Verify** trạng thái thực tế bằng grep hoặc DB query trước khi claim "đã xong"
3. **Log** thay đổi vào `docs/sessions/YYYY-MM-DD/changes.md` sau khi xong

---

## Task tracking (bắt buộc — dashboard đọc từ đây)

Mỗi chức năng cần dev có **1 file task** trong `tasks/T<id>-<slug>.md`
(format: frontmatter YAML `id/title/module/priority/status/depends_on/created/updated/done_when` + acceptance criteria checklist).
Quy tắc đầy đủ: `tasks/README.md`. Dashboard `dashboard_process.html` hiển thị qua
`build_progress_data.py` → `data/progress_data.json` (`tasks[]` + `task_meta`).

Quy ước:
1. Bắt đầu task → `status: in_progress` + `updated: hôm nay`.
2. Gặp chặn → `status: blocked` + ghi lý do phần `## Blockers`.
3. Xong → tick hết acceptance criteria, `status: done`.
4. `docs/tasktodo.md` là registry tổng quan — cập nhật dấu ✅/⏳ tương ứng.
5. Sau thay đổi, chạy `python scripts/build_progress_data.py` để dashboard cập nhật.

Status chỉ dùng 4 giá trị: `pending | in_progress | blocked | done`.

---

## Git — KHÔNG tự ý chạy

Repo root là `visjs-app` (2 cấp trên `daoanh/`), không phải `daoanh/` riêng.  
Git index đang có anomaly (mass staged-deletion). Không chạy `git add/commit/reset` khi chưa có lệnh rõ ràng từ user.

---

## Permissions

- Được phép chạy command trong project mà không hỏi từng lần
- **Vẫn cần xác nhận** cho: force push, xóa data lớn, thay đổi schema DB, deploy lên VPS

---

## Gemini API key

Hardcoded trong `app.py` lines 1065 và 1105. Chưa chuyển sang `.env`.  
Không commit key này lên git.

---

## VPS info

IP: `158.220.106.183`  
Path: `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/`
