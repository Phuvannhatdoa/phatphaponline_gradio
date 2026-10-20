# Đạo Ảnh — Tài Liệu Dự Án

> **Hữu Tự Vô Đạo — Bất Khả Hưng Giáo.**
> Hệ thống tra cứu dữ liệu Đại Tạng Kinh Việt Nam: biến dữ liệu thô thành tri thức có cấu trúc (SSOT).

---

## Giới thiệu nhanh

**Đạo Ảnh** là hệ thống tra cứu địa danh & nhân vật Phật giáo, tích hợp dữ liệu từ nhiều nguồn học thuật (DILA, CBETA, TTL, Marcus, CBDB, Wikipedia) và cung cấp:

- **Đối chiếu Hán → Việt** tự động (NameVi Map, lexicons).
- **Đồ thị dòng phái Thiền tông** (visjs / D3).
- **Trích dẫn Đại Tạng Kinh** (CBETA Han text, dịch tiếng Việt, giải thích LLM).
- **Bản đồ GIS** địa danh Phật giáo với cluster progressive loading.
- **Dashboard tiến độ** đối chiếu docs ↔ code.

## Bắt đầu từ đâu

| Mục đích | Đọc |
|----------|-----|
| Hiểu kiến trúc & module | [Overview](overview.md) |
| Lịch sử + kế hoạch dài hạn | [Roadmap](roadmap.md) · [DEV_HISTORY](DEV_HISTORY.md) |
| Việc cần làm kế tiếp | [TASKTODO](tasktodo.md) · [Task Board](tasks/README.md) |
| Tiến độ hiện tại | [Progress](progress.md) · [Dashboard](../dashboard/README.md) |
| Chạy hệ thống | `python server.py` (port 5001) + `python app.py` (port 5000) |

## Cấu trúc tài liệu

Tài liệu dự án tổ chức theo chuẩn GitBook (mục lục đầy đủ trong [SUMMARY.md](SUMMARY.md)):

- `docs/` — hướng dẫn, kiến trúc, tiến độ, hợp đồng agent.
- `docs/sessions/` — nhật ký phiên build (mỗi task 1 file).
- `docs/bug-reports/` + `docs/fix-logs/` — báo lỗi và log sửa.
- `docs/contracts/` — thỏa thuận làm việc với agent.
- `tasks/` — feature dev board chuẩn Claude Code (1 task = 1 file).
- `dashboard/` — tài liệu vận hành dashboard process tracker.

## Xem GitBook (render website)

Dự án có GitBook thật (Honkit — gitbook-cli mã nguồn mở) tại thư mục gốc `daoanh/`:

```powershell
npm run docs:serve   # http://localhost:4000 — watch + livereload
npm run docs:build   # dựng tĩnh ra _book/
```

- `book.json` — cấu hình (title, theme dark #020617/#d97706, README = `README.md`, SUMMARY = `SUMMARY.md`).
- `SUMMARY.md` — mục lục sách (thêm trang mới → thêm dòng vào đây).
- `.gitignore` — loại trừ `node_modules/ data/ _book/ .opencode/ ontology/ ...` khỏi bản build (giữ `docs/ tasks/ dashboard/ styles/`).
- File `.md` có space trong tên → honkit không build → dùng `_` thay space.
- **Auto-update hàng ngày 12:00:** Task Scheduler `GitBook_DailyUpdate_1200` → `scripts/gitbook_daily_update.ps1` (giữ server sống + restart nếu chết; log `%TEMP%\gitbook_daily_update.log`).
