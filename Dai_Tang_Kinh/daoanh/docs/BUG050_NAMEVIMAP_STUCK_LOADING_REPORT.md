# Audit / Bug Fix Report — BUG-050 namevimap.html stuck on "Đang tải…"

> Template: `docs/templates/audit-report.md`. Task: `tasks/T437-bug050-namevimap-stuck-loading.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Route | `http://127.0.0.1:8080/daoanh/admin/namevimap.html` (local_gateway → app.py:5000) |
| API endpoint bị kẹt | `GET /api/admin/namevi/flag-list?page=1&per_page=50&hide_done=true` (tab ETL, bảng "Bulk Flag Queue") |
| Resolver / init logic | `daoanh/admin/namevimap.html` — `init()` → `setTimeout(..., 800)` → `_etlFullLoad()` → `_etlNewAbortSignal()` + `etlFlagQueueLoad()` |
| Dead include | `daoanh/admin/namevimap.html` — `<link href="codex-namevi.css">`, `<script src="codex-namevi.js">` |
| Servers | `app.py` (5000), `local_gateway.py` (8080) đang chạy; `server.py` (5001, auth gateway) **không chạy** lúc audit bắt đầu — đã khởi động lại |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** async (frontend — thiếu timeout/deadline cho fetch) + vận hành (server.py không chạy).
- **Nguyên nhân chính xác (đã verify bằng browser thật + network log):**
  1. Tab ETL (tab mặc định khi mở trang) tự động gọi 5 hàm nặng 800ms sau khi load: `loadEtlStats`, `loadEtlFlagLiveData` (N fetch `/api/admin/namevi-queue/<id>` chạy song song cho ~12 dòng tĩnh), `etlFlagQueueLoad` (fetch `flag-list`), `loadAiColStatus`, `loadCodexColStatus`. Toàn bộ các hàm này **đã có tham số `signal`** (AbortController, thêm từ T427 round 3) nhưng **chỉ abort khi Admin chuyển tab khác — không có deadline theo thời gian**. Nếu backend xử lý chậm bất thường (ghi nhận thực tế trong phiên audit: backend đang bị một tiến trình khác ghi đồng thời `/daoanh/api/places/vi-map/.../edit` và `/approve`, khiến SQLite bị tranh chấp khoá, mỗi request `namevi-queue/<id>` mất 1–10s, có lúc backend trả `500 INTERNAL SERVER ERROR` do khoá), request `flag-list` phải xếp hàng sau cụm request kia (vượt giới hạn 6 connection/origin của browser) và có thể treo rất lâu — tái hiện được thực tế bảng "Bulk Flag Queue" đứng ở "Đang tải…" **quá 50 giây không tự thoát** trong phiên audit (ảnh chụp màn hình kèm theo).
  2. `etlFlagQueueLoad()` có try/catch, nhưng nhánh catch đang coi `AbortError` là "Admin chủ động rời tab" và **im lặng không ghi đè UI** — nên kể cả khi gắn `signal` có abort, nếu không có ai abort (Admin vẫn đứng nguyên ở tab ETL mặc định), UI không bao giờ tự báo lỗi, chỉ đứng mãi ở placeholder tĩnh `"Đang tải…"` được set sẵn lúc bắt đầu fetch.
  3. **Phụ, không phải nguyên nhân chính nhưng là bug thật**: `codex-namevi.js` (nạp kèm `codex-namevi.css`) vẫn được include trong `namevimap.html`, nhưng toàn bộ DOM mà nó cần (`#codex-prepare`, `#codex-run`, `#codex-pause`, `#codex-refresh`, `#codex-search`, `#codex-search-button`, `#codex-corpus-body`, `#codex-corpus-pages`) đã bị xoá khỏi trang ở commit `a4397c2a cleanup: Remove legacy GPT Sol / Claude dịch session from namevimap.html` — script orphan này ném `Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')` ngay khi trang load, ghi log lỗi console mỗi lần tải trang (dead code, không trực tiếp gây "Đang tải" treo vì cột Claude đã được `etlFlagQueueLoad` tự render từ `item.codex_name_vi` do server trả về, không phụ thuộc script này).
  4. **Vận hành**: `server.py` (port 5001, auth gateway) không chạy lúc bắt đầu audit — vi phạm yêu cầu "3 server phải chạy" trong CLAUDE.md. Đã xác minh: khi 5001 down, `admin_session` hợp lệ trong localStorage vẫn khiến trang redirect về `login.html` (do `/daoanh/api/login/check` trả 502 qua gateway, `d.valid` undefined → coi là invalid). Đây **không phải nguyên nhân của triệu chứng "Đang tải" treo** (nó gây redirect về login, không phải treo loading) nhưng là lỗi vận hành thật, đã khởi động lại server.py để audit đúng BƯỚC 0.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Timeout cho cụm fetch tab ETL | Không có — chỉ abort khi rời tab, có thể treo UI vô thời hạn nếu backend chậm | Deadline cứng 45s; hết giờ → abort toàn bộ fetch của lượt tải đó |
| UI khi backend quá tải | Bảng "Bulk Flag Queue" đứng mãi ở `"Đang tải…"`, không có cách phân biệt đang chạy hay đã chết | Sau 45s không xong → tự ghi `"Lỗi: quá thời gian chờ (45s) — server đang quá tải, thử lại"` vào đúng bảng đang kẹt; nút "Load" vẫn dùng được để thử lại ngay |
| `codex-namevi.js`/`.css` | Vẫn include, ném lỗi console mỗi lần tải trang (dead code từ cleanup dở ở a4397c2a) | Gỡ include; không còn request/lỗi console orphan |

## 4. Files changed

- `daoanh/admin/namevimap.html`
  - Gỡ `<link rel="stylesheet" href="codex-namevi.css">` và `<script src="codex-namevi.js"></script>` (dead code sau cleanup commit `a4397c2a`, không còn DOM target).
  - `_etlNewAbortSignal()`: thêm deadline cứng 45s (`setTimeout` abort + tự ghi thông báo lỗi rõ ràng vào `#etl-flag-queue-body` nếu vẫn đang hiện "Đang tải…" lúc hết giờ). Không đổi chữ ký hàm, không đổi endpoint, không đổi luồng khi backend phản hồi nhanh bình thường.
- Không sửa `app.py`, `local_gateway.py`, DB, schema (dù có backup sẵn ở `docs/sessions/2026-10-20/BUG-050/` theo quy trình — không cần dùng vì không đổi các file đó).
- Vận hành: khởi động lại `server.py` (port 5001) đang tắt — không phải thay đổi code, chỉ là khôi phục đúng trạng thái 3-server theo CLAUDE.md.

## 5. Migration / import / dry-run / rollback

- Không chạm DB/schema — không cần migration/dry-run.
- Rollback: `git diff daoanh/admin/namevimap.html` rồi `git checkout -- daoanh/admin/namevimap.html`, hoặc khôi phục từ backup `daoanh/docs/sessions/2026-10-20/BUG-050/namevimap.html.bak`.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu — mở `/daoanh/admin/namevimap.html`, chờ tải tab ETL | Session hợp lệ, cả 3 server chạy | Trang load xong, bảng FLAG queue hiện dữ liệu, không kẹt "Đang tải…" | Khi backend rảnh: load xong trong vài giây (ảnh chụp: "319 FLAG chưa duyệt" hiện đủ dữ liệu). Khi backend bị tải nặng (ghi nhận thực tế do một tiến trình khác đang ghi DB đồng thời): trước đây treo > 50s không tự thoát; sau fix, đúng 45s tự chuyển sang thông báo lỗi rõ ràng | ✅ |
| Fallback — backend chậm/quá tải (mô phỏng bằng tải thật đo được trong phiên, không hard-code) | Giữ nguyên tab ETL, không thao tác gì | Không được treo vô hạn — phải báo lỗi rõ ràng sau một khoảng thời gian hữu hạn | Sau 45s, bảng tự hiện `"Lỗi: quá thời gian chờ (45s) — server đang quá tải, thử lại"` thay vì "Đang tải…" mãi mãi | ✅ |
| Retry sau lỗi | Bấm nút "Load" sau khi gặp thông báo lỗi timeout | Tải lại thành công, không cần F5 | Bấm "Load" → bảng hiện dữ liệu đầy đủ ngay | ✅ |
| Regression — tab "Danh sách chờ mapping" (Queue) | Chuyển tab sau khi sửa | Tab Queue vẫn load bình thường | Hiện đủ dữ liệu, không lỗi console mới | ✅ |
| Regression — route khác dùng chung app.py/local_gateway (`/daoanh/places`) | Mở route GIS Places | Không bị ảnh hưởng bởi thay đổi trong namevimap.html | Load bình thường | ✅ |
| codex-namevi.js orphan error | Mở lại trang sau fix | Không còn request/exception liên quan codex-namevi | `document.scripts` và `performance.getEntriesByType('resource')` xác nhận không còn request tới `codex-namevi.*` | ✅ |

## 7. Limitation / blocker còn lại

- **Chưa sửa nguyên nhân sâu hơn khiến backend chậm**: trong phiên audit, một tiến trình khác (không phải phiên này) đang đồng thời ghi `POST /daoanh/api/places/vi-map/.../edit` và `/approve` vào cùng `data/lineage.db`, khiến các request đọc `namevi-queue/<id>` và `flag-list` bị chậm 1–10s/request, có lúc trả `500`. Đây là tranh chấp khoá SQLite dưới tải ghi đồng thời — nằm ngoài phạm vi task này (không đổi schema/DB theo ràng buộc) và cũng là nguyên nhân gốc khiến BUG-050 "cảm giác" treo vô hạn trong điều kiện tải cao. Fix trong task này đảm bảo **UI không bao giờ treo vô hạn nữa** (luôn thoát trong ≤45s kèm thông báo lỗi + nút thử lại), nhưng không làm backend nhanh hơn.
- 45 giây là ngưỡng chọn dựa trên comment T427 (đã đo thực tế backend có lúc mất tới ~94s khi tải rất nặng) cân bằng giữa "đủ thời gian cho tải bình thường" và "không bắt Admin chờ quá lâu mới thấy lỗi" — nếu Admin thấy 45s vẫn chưa đủ/quá dài trong thực tế vận hành, có thể điều chỉnh hằng số này (dễ sửa, 1 chỗ).
- `server.py` hiện đang chạy nhờ tôi khởi động lại trong phiên này; đây là tiến trình nền cục bộ (không phải service), nếu máy dev khởi động lại thì cần start lại theo đúng quy trình CLAUDE.md (`python server.py > server_local.log 2>&1`).
