# Session: Hoàn chỉnh GitBook dự án (Honkit)

**Ngày:** 2026-08-13
**Module:** Hạ tầng / Docs
**Task liên quan:** docs chuẩn GitBook (SUMMARY.md + README) → GitBook thật render được

---

## Mục tiêu

Thay vì đọc file `.md` thô, dựng **GitBook thật** (website điều hướng sidebar theo chuẩn GitBook) hiển thị tại localhost.

## Đã làm

1. **Chọn giải pháp:** Honkit (gitbook-cli mã nguồn mở, đọc thẳng `SUMMARY.md`) — cài `npm install --save-dev honkit` (v6.2.2).
2. **Book root = thư mục `daoanh/`** để SUMMARY.md link được cả `docs/`, `tasks/`, `dashboard/`:
   - `book.json` — title, language `vi`, theme default + custom `styles/website.css` (dark #020617, amber #d97706).
   - `README.md` (root) — landing page (vì `structure.readme` không nhận path có `/`).
   - `SUMMARY.md` (root) — mục lục GitBook đầy đủ.
3. **`.gitignore` bổ sung:** loại trừ `node_modules/ data/(3GB) _book/ .opencode/(48MB) ontology/ logs/ admin/ ...` — honkit copy toàn bộ cây trừ file trong `.gitignore`; thiếu ignore → build chậm/hết timeout (180s+). Giữ `docs/ tasks/ dashboard/ styles/` (SUMMARY.md cần).
4. **Fix file tên có space:** `docs/update contract_opencode.md` → `update_contract_opencode.md` (honkit không build file có space trong tên). Cập nhật link trong `docs/SUMMARY.md` + root `SUMMARY.md`.
5. **npm scripts:** `docs:serve` (port 4000, watch+livereload) + `docs:build`.

## Verify

```powershell
npm run docs:build   # generation finished with success in 30.7s, 20 pages, 112 assets
npm run docs:serve   # Serving book on http://localhost:4000
```

- `http://localhost:4000/` → 200 (landing)
- `http://localhost:4000/docs/roadmap.html`, `/docs/`, `/tasks/`, `/dashboard/`, `/docs/update_contract_opencode.html` → tất cả 200
- Crawl 19 link trong SUMMARY → không còn 404

## Lưu ý / Bước kế tiếp

- Honkit serve có watch → mỗi lần sửa .md tự rebuild (vài chục giây). Muốn build nhanh hơn nữa có thể loại thêm thư mục vào `.gitignore`.
- Thêm trang mới → thêm dòng vào root `SUMMARY.md`.
- **Auto-update hàng ngày 12:00:** Windows Task Scheduler `GitBook_DailyUpdate_1200` chạy `scripts/gitbook_daily_update.ps1`:
  - Port 4000 còn sống → honkit watch tự rebuild khi .md đổi (log `%TEMP%\gitbook_daily_update.log`).
  - Port 4000 chết → rebuild `_book/` + restart honkit serve.
  - Kiểm tra: `Get-ScheduledTask GitBook_DailyUpdate_1200` · `Start-ScheduledTask` để chạy thử · LastTaskResult=0 là OK.
- Kế tiếp: commit (chờ admin), hoặc nếu muốn public → push GitHub + GitBook.com import.
