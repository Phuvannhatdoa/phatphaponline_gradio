# PLAN — Dashboard Process Tracker (docs ↔ code)

> **Trạng thái plan:** ĐÃ CHỐT bởi admin (2026-08-13). Không phá vỡ các quyết định dưới đây trừ khi admin yêu cầu.

## 1. Mục tiêu

Trang admin `dashboard/dashboard_process.html` hiển thị tiến độ từng module của dự án bằng cách **tự động đối chiếu** tài liệu trong `docs/*.md` với **code Python thật** (routes/functions/scripts) → tính `% hoàn thành` theo code. Admin thấy ngay: docs nói gì, code làm được gì, chỗ nào lệch.

## 2. Quyết định đã chốt (KHÔNG THAY ĐỔI)

1. **Vị trí:** file UI nằm ở `dashboard/dashboard_process.html` (thư mục mới gốc daoanh), local_gateway/nginx phục vụ trực tiếp. Không dùng `admin/`.
2. **Cách tính %:** **TỰ ĐỘNG theo code** — đếm route/func/script thật khớp với tên task/module trong docs: `progress = code_found / code_claimed`.
3. **Nguồn dữ liệu:** chỉ từ `docs/*.md` + scan code. KHÔNG hardcode task list trong HTML.
4. **Theme:** Amber `#d97706` trên Dark Slate `#020617`, font Inter (UI) + Noto Serif TC (Hán). Theo `admin/index.html`.

## 3. Kiến trúc & luồng dữ liệu

```
docs/*.md  ─┐
app.py/scripts/*.py/src_python/*.py/src/python/*.py  ─┤
                                                      ▼
                          scripts/build_progress_data.py
                                                      ▼
                                      data/progress_data.json
                                                      ▼
              route GET /daoanh/api/progress/dashboard (app.py)
                                                      ▼
                       dashboard/dashboard_process.html (fetch + render)
```

- Script chạy **theo yêu cầu** (nút Refresh trên UI → `?regenerate=1`; hoặc CLI).
- Route app.py serve JSON; nếu file chưa tồn tại → tự gọi script sinh.
- Zero-RAM: chỉ đọc metadata (regex headers/routes/defs), không nạp data file lớn.

## 4. Thuật toán tính % (`build_progress_data.py`)

1. **Parse docs:** đọc `docs/*.md` (`tasktodo.md`, `progress.md`, `roadmap.md`, `pipelines.md`, `db_schema.md`, `DEV_HISTORY.md`).
   - Trích section headers `##`/`###` (tên module), bảng Markdown, trạng thái `✅/⏳/❌`.
   - Thu thập "claim": mỗi API/route/func/script được docs nhắc tới (regex `\`?`?`/api/...`?`?`, `/daoanh/...`, `scripts/*.py`, tên hàm).
2. **Scan code:**
   - `app.py`, `server.py`, `api_ttl_rebuild.py`, `conflict_server.py` → regex `@app.route` → (method, path, function).
   - `scripts/*.py`, `src_python/**/*.py`, `src/python/**/*.py` → count `def`, đọc 2 dòng đầu docstring.
3. **Đối chiếu:** với mỗi module/claim → kiểm tra tồn tại trong code (chuẩn hóa path, bỏ prefix `/daoanh` khi so sánh).
   - `code_claimed` = số claim từ docs; `code_found` = số claim tìm thấy.
   - `progress% = round(code_found / code_claimed * 100)`.
   - Trạng thái: `100%` → `done`, `>0` → `in_progress`, `0` → `pending`.
4. **Bảng endpoints:** list route thật (từ scan) so với route docs claim → đánh dấu ✓/✗ (phát hiện 404 như `/daoanh/api/admin/dashboard/stats`).
5. **Output JSON:** `{generated_at, modules:[{name, doc_status, progress, code_found, code_claimed, routes[], warnings[]}], endpoints_compare:[...]}`.

## 5. Đặc tả từng file

### 5.1 `scripts/build_progress_data.py`
- Python chuẩn (`os`, `re`, `json`, `pathlib`, `sys`), không thư viện mới.
- `ROOT` = thư mục gốc daoanh; `OUT` = `data/progress_data.json`.
- Khi chạy: in tóm tắt (`Generated N modules, M endpoints`) + ghi JSON; có `try/except` với thông báo tiếng Việt.
- Argument tùy chọn: `--verbose`.

### 5.2 Route trong `app.py`
- `GET /daoanh/api/progress/dashboard` → `api_progress_dashboard()`:
  - Nếu `request.args.get('regenerate')` hoặc JSON chưa tồn tại → chạy script (subprocess python, timeout 60s).
  - Trả về JSON từ file (or `{"error": ...}` 500).
- Đặt gần nhóm dashboard route hiện có (`api_dashboard_stats`, ~line 6044).

### 5.3 `dashboard/dashboard_process.html`
- Tĩnh, gọi `fetch('/daoanh/api/progress/dashboard')`.
- **Header:** tiêu đề "Dashboard Process Tracker", nút Refresh (gọi `?regenerate=1`), timestamp `generated_at`, tổng progress TB.
- **Module cards:** tên module, progress bar (màu: done=green `#22c55e`, in_progress=amber, pending=slate), badge `routes: found/claimed`, trạng thái docs, warnings đỏ.
- **Bảng endpoints:** path, method, docs claim ✓/✗, route thật.
- **Footer:** "Xem plan: dashboard/plan.md" + hướng dẫn refresh.
- Auto-refresh mỗi 60 phút (setInterval). Không cần thư viện ngoài (CDN fallback như các trang khác).

## 6. Thứ tự triển khai & tiêu chí done

| # | Bước | File | Done khi |
|---|------|------|----------|
| 1 | Tạo tài liệu plan | `dashboard/README.md`, `plan.md`, `tasks.md`, `handoff.md` | 4 file tồn tại, nội dung như §7 |
| 2 | Script generator | `scripts/build_progress_data.py` | Chạy CLI ra JSON hợp lệ, in summary |
| 3 | Route API | `app.py` | `curl :5000/daoanh/api/progress/dashboard` trả JSON 200 |
| 4 | UI | `dashboard/dashboard_process.html` | Mở qua :8080, render cards + bảng, nút Refresh hoạt động |
| 5 | Verify thực | — | Mỗi module có % khớp đối chiếu thật |
| 6 | Docs + commit | `docs/sessions/`, `docs/progress.md`, git | `npm run pipeline` PASS, commit thành công |

## 7. Files sẽ tạo/sửa

| File | Loại | Ghi chú |
|------|------|---------|
| `dashboard/README.md` | mới | Entry point cho agent tiếp nhận |
| `dashboard/plan.md` | mới | Plan này |
| `dashboard/tasks.md` | mới | Checklist task (nguồn sự thật) |
| `dashboard/handoff.md` | mới | Session continuation |
| `scripts/build_progress_data.py` | mới | Generator |
| `data/progress_data.json` | auto-gen | Output |
| `app.py` | sửa | +1 route |
| `dashboard/dashboard_process.html` | mới | UI |
| `docs/sessions/2026-08-13_progress_dashboard.md` | mới | Session log |
| `docs/progress.md` | sửa | Thêm section Dashboard |

## 8. Rủi ro / lưu ý

- `fix_all.py` ghi đè app.py → **tuyệt đối không chạy**.
- Route trùng giữa `app.py` và `api_ttl_rebuild.py`/`conflict_server.py` (cùng path) — chỉ chạy 1 app trên port 5000.
- Một số script có hardcode `/opt/...` (Linux/VPS) — không chạy trên Windows, nhưng dashboard chỉ scan metadata nên vẫn đếm được.
- Secrets: `batch_translate_places.py:30` chứa Gemini key — không lộ ra dashboard.
