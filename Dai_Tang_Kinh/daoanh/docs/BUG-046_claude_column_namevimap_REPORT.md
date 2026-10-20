# Audit / Bug Fix Report — BUG-046 (T428) Cột "Claude" trong namevimap.html trùng data TTL name_vi

## 1. Vị trí audit (thực tế)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | bảng `codex_person_name` (49.335 dòng, cột `dila_id`, `name_vi`, `model='claude-xml-import@0d2ea40'`) — NGUỒN THẬT của cột Claude; khác hẳn `vn_person_authority` (nguồn của `ttl_name_vi`) |
| API endpoint | `GET /daoanh/api/admin/namevi/flag-list` (và `/api/admin/namevi/flag-list`) |
| Resolver / logic | `daoanh/app.py:15696-15792` — hàm `admin_namevi_flag_list()` |
| Component / renderer | `daoanh/admin/namevimap.html:1718, 2073` — `td.codex-name-cell` bind `item.codex_name_vi` |
| Schema contract | `codex_name_vi` trước = alias trùng `ttl_name_vi` → sau = giá trị riêng từ `codex_person_name` |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** resolver (SQL trong route backend `app.py`), không phải frontend, không phải data thô.
- **Nguyên nhân chính xác:** route `admin_namevi_flag_list()` xây SQL với:
  ```python
  codex_select = "va.name_vi AS codex_name_vi"   # BUG: va = subquery vn_person_authority
  codex_join   = ""
  ```
  trong khi cùng câu SQL cũng chọn `va.name_vi AS ttl_name_vi` (dòng 15719) cho cột "TTL
  name_vi". Vì cả hai alias cùng đọc một cột `va.name_vi`, hai cột trên UI luôn giống
  hệt nhau cho mọi dòng — bất kể dữ liệu Claude thật sự có khác hay không.
  Trong khi đó dữ liệu Claude thật (từ job import XML, model
  `claude-xml-import@0d2ea40`, 49.335 dòng) đã nằm sẵn trong bảng riêng
  `codex_person_name` nhưng route chưa bao giờ JOIN tới bảng này.
  (Ghi chú: file `app.py` tại thời điểm agent này khởi động đã có patch chưa
  commit sửa đúng root cause trên — agent xác minh patch đúng, chạy thử nghiệm
  trực tiếp qua DB + API sống, không chỉnh sửa gì thêm vì bản vá đã đúng lớp.)

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| SQL | `va.name_vi AS codex_name_vi` (không JOIN bảng Claude) | `cx.name_vi AS codex_name_vi` với `LEFT JOIN codex_person_name cx ON cx.dila_id = p.id` |
| API response (`A000443`) | `codex_name_vi` = `"Tôn Giả Phật Đà Mật Đa"` (=ttl_name_vi, SAI) | `codex_name_vi` = `"Phật Đà Mật Đa"` (nguồn Claude thật, KHÁC ttl_name_vi) |
| ID không có dòng trong `codex_person_name` | (chưa áp dụng — cột luôn có giá trị giả từ va) | `codex_name_vi` = `''` → UI hiện `—` (fallback đúng, không lỗi) |

## 4. Files changed

- `daoanh/app.py` (dòng ~15696-15700) — sửa `codex_select`/`codex_join` để JOIN đúng
  bảng `codex_person_name` thay vì đọc lại `va.name_vi`. (Thay đổi đã có sẵn trong
  working tree khi agent bắt đầu phiên — agent xác minh đúng và không sửa lại.)
- Backup trước khi audit: `daoanh/docs/sessions/2026-10-19/BUG-046/app.py.bak`
  (bản app.py tại thời điểm agent bắt đầu, đã chứa patch).

## 5. Migration / import / dry-run / rollback

- Không chạm schema/DB — chỉ sửa 1 câu SQL SELECT/JOIN trong route đọc (read-only).
- Không cần migration. Revert nếu cần: khôi phục khối code dòng 15696-15700 trong
  `app.py` về bản backup `docs/sessions/2026-10-19/BUG-046/app.py.bak`.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu — Claude khác TTL | `GET /daoanh/api/admin/namevi/flag-list?page=1&per_page=5&hide_done=false` | `codex_name_vi` != `ttl_name_vi` cho các dòng có data Claude khác biệt | `A000443`: ttl=`Tôn Giả Phật Đà Mật Đa`, claude=`Phật Đà Mật Đa` (khác); `A000470`: ttl=`Đoạn Kiều Diệu Luân`, claude=`Diệu Luân` (khác) | ✅ |
| Fallback — ID không có trong `codex_person_name` | SQL `LEFT JOIN ... WHERE cx.dila_id IS NULL` | `codex_name_vi` rỗng, UI hiện `—`, không lỗi 500 | Xác nhận 3 ID mẫu (`A015792`, `A016555`, `A016745`) có `people.id` nhưng không có dòng `codex_person_name` tương ứng → LEFT JOIN trả NULL an toàn (Python `r['codex_name_vi'] or ''`) | ✅ |
| Trùng khóa `dila_id` trong `codex_person_name` | `SELECT dila_id, COUNT(*) FROM codex_person_name GROUP BY dila_id HAVING COUNT(*)>1` | 0 dòng trùng (tránh nhân bản row khi JOIN) | 0 dòng trùng | ✅ |
| py_compile | `python -m py_compile daoanh/app.py` | Không lỗi cú pháp | COMPILE OK | ✅ |
| Regression — route/API khác | `GET /daoanh/api/admin/namevi/flag-list` trả đủ field cũ (`ai_name_vi`, `ttl_name_vi`, `dila_name_vi`, `name_vi_final`, `confidence`, `confidence_cross`, `lexicon_source`) | Không mất field nào | Response mẫu có đủ tất cả field cũ | ✅ |

## 7. Limitation / blocker còn lại

- **Chưa chụp screenshot UI trực tiếp trên `namevimap.html`** theo quy tắc
  "Bug verify protocol" (bắt buộc click UI thật + screenshot before/after) vì
  trang admin yêu cầu đăng nhập Google OAuth
  (`http://127.0.0.1:8080/daoanh/login.html` → "Đăng nhập với Google"). Agent
  không được phép tự đăng nhập qua provider sản xuất thật (accounts.google.com)
  theo ràng buộc an toàn của phiên làm việc. Đã xác minh đầy đủ bằng API trực
  tiếp (curl/PowerShell) phản ánh đúng dữ liệu `.codex-name-cell` mà
  `namevimap.html` render (dòng 1718/2073 bind thẳng `item.codex_name_vi` từ
  đúng API này, không qua xử lý trung gian nào khác) — nhưng Admin cần tự đăng
  nhập và xác nhận bằng mắt trước khi đánh dấu T428 là DONE.
- Server local (`app.py`, cổng 5000) mất khoảng 60-90s để bind cổng sau khi
  khởi động (do nạp 166K dòng lexicon + build cache) — lúc đầu gateway 8080 báo
  "backend on port 5000 is not running"; sau khi đợi, cổng 5000 đã listen và
  API trả dữ liệu đúng.
