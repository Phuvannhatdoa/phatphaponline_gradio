# Đạo Ảnh — Dashboard Process Tracker (docs ↔ code)

> **File này là entry point.** Nếu bạn (Claude Code / opencode) được yêu cầu "tiếp tục công việc", hãy đọc theo thứ tự: `README.md` → `plan.md` → `tasks.md` → `handoff.md`.

## Dự án này là gì

Hệ thống tra cứu dữ liệu **Đại Tạng Kinh Việt Nam** (mã nội bộ `daoanh`). Backend Flask + SQLite, frontend admin HTML tĩnh. Xem thêm `docs/overview.md`, `docs/roadmap.md`, `docs/tasktodo.md`, `docs/progress.md`.

## Kiến trúc server (3 tiến trình)

| Tiến trình | File | Port | Vai trò |
|-----------|------|------|---------|
| Auth Gateway | `server.py` | 5001 | Login Gmail allowlist, session, admin emails |
| Main Server | `app.py` | 5000 | Toàn bộ business logic (131 route) |
| Local Gateway | `local_gateway.py` | 8080 | Thay nginx khi dev Windows: static + proxy |

- `local_gateway.py:8080` phục vụ static file gốc daoanh (VD `dashboard/`) và proxy `/daoanh/api/login/*` → 5001, còn lại → 5000.
- Route `/daoanh/admin/<path:path>` (app.py) phục vụ static trong `admin/`.

## Dashboard Process Tracker — dự án con trong thư mục này

**Mục tiêu:** trang `dashboard_process.html` hiển thị tiến độ các module bằng cách **đối chiếu tài liệu `docs/*.md` với code Python thật** (không hardcode), tính % tự động theo code.

**Dữ liệu:** `scripts/build_progress_data.py` scan docs + code → `data/progress_data.json` → route `GET /daoanh/api/progress/dashboard` (app.py) → HTML fetch + render.

## Cách chạy / test

```bash
# 1. Sinh dữ liệu progress (chạy ở gốc daoanh)
python scripts/build_progress_data.py

# 2. Chạy main server
python app.py                # port 5000

# 3. (dev Windows) gateway
python local_gateway.py      # port 8080

# 4. Mở dashboard
#    http://localhost:8080/dashboard/dashboard_process.html
#    hoặc http://localhost:8080/daoanh/api/progress/dashboard (JSON)
```

Pipeline test trước review: `npm run pipeline` (lint + test + e2e).

## Danh mục tài liệu

| File | Nội dung | Ai đọc |
|------|----------|--------|
| `README.md` | Tổng quan này | Mọi agent khi bắt đầu |
| `plan.md` | Plan chi tiết, thuật toán, đặc tả, thứ tự triển khai | Agent đang dev |
| `tasks.md` | Checklist task + trạng thái (nguồn sự thật) | Agent dev + review |
| `handoff.md` | Session continuation: đang ở đâu / kế tiếp là gì | Agent tiếp nhận |
| `dashboard_process.html` | Trang UI dashboard (kết quả) | Admin xem |

## Quy ước cập nhật (bắt buộc)

- Sau **mỗi task hoàn thành**: tick `tasks.md` + ghi 5 dòng vào `handoff.md` (đang ở đâu / vừa làm gì / bước kế tiếp / lệnh verify / ghi chú).
- Trước khi kết thúc phiên: chạy `npm run pipeline`, cập nhật `docs/sessions/YYYY-MM-DD_*.md`, `docs/progress.md`.
- Commit theo convention: `feat: <mô tả> + docs` từ git root `visjs-app/`.

## Bối cảnh đã khảo sát (để không phải scan lại)

- `app.py`: 7,780 dòng, 172 def, **131 route** (đầy đủ: `app.py:1` → `@app.route`, xem `plan.md` §6).
- `server.py`: 126 dòng, 8 route (login only).
- `scripts/*.py`: 14 file ETL/SQL (đều nối `data/lineage.db`).
- `src_python/`: 59 file; `src/python/`: 41 file (pipeline 4-pillar cũ).
- `admin/`: 12 HTML (index, placevn, panorama, namevimap, ...).
- Data: `data/lineage.db` 633 MB, `data/cbeta/cbeta.db` 16 MB, `data/cbdb/cbdb_20260516.sqlite3` 148 MB, 16 file `data/ttl/old/*.ttl`.

**Cảnh báo an toàn:** `fix_all.py` là "footgun" (ghi đè app.py thành stub 3 route) — không chạy.
