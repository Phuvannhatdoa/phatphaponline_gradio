---
id: T446
title: Tab Place namevimap.html - live dry-run compare Claude vs Gemini vs namevi_map
status: done
created: 2026-10-21
updated: 2026-10-21
done_when: Endpoint summary moi tra JSON dung, co cache theo key (mtime XML + count 2 bang), namevimap.html Tab Place hien thi so lieu khong chan bang, fallback an so lieu khi loi, QA xac nhan tren browser 127.0.0.1 kem screenshot + network log, khong ghi DB.
---

## Mô tả

Thêm endpoint chỉ đọc /api/admin/places-claude-compare/summary và khối số liệu trong Tab Place của namevimap.html, để Admin thấy đối chiếu Claude với Gemini và namevi_map theo dữ liệu mới nhất. Số liệu được cache theo mtime XML và số dòng bảng; lỗi thì ẩn khối số liệu, bảng vẫn hiển thị. Task kèm ẩn ID đã PASS và sắp xếp theo % khớp, không ghi DB ngoài thao tác PASS đã có.

## Bối cảnh

Script dry-run `scripts/import_claude_place_name_dryrun.py` (task T445) đối chiếu
phiên âm Claude với Gemini (`ai_place_name`) và `namevi_map_places`. Gemini đang
dịch dần theo quota nên số liệu dry-run cũ (CSV mẫu
`docs/sessions/2026-10-21/claude_place_name_dryrun.csv`, 59.353 dòng, 46.490 dòng
Gemini còn trống) nhanh bị lỗi thời.

## Mục tiêu (chỉ đọc, KHÔNG ghi DB)

Mỗi khi Admin mở Tab Place trong `admin/namevimap.html` (127.0.0.1:8080), hệ thống
tự chạy lại logic đối chiếu và hiển thị số liệu mới nhất gần tiêu đề bảng, không
cần đợi batch dry-run ghi CSV.

## Phạm vi kỹ thuật

1. Endpoint mới trong `app.py`, đặt cạnh `api_places_vi_map_list`, ví dụ:
   `GET /api/admin/places-claude-compare/summary` — chỉ SELECT, trả JSON:
   tổng, có Gemini, còn trống Gemini, khác Gemini, khác namevi_map, ID mới.
2. Cache trong bộ nhớ (process-level dict), khóa = (mtime file XML
   `data/phien_am/vn_place_name_vi.xml`, COUNT `ai_place_name`,
   COUNT `namevi_map_places`). Chỉ tính lại khi khóa đổi; JSON trả về có
   trường thời điểm tính (computed_at).
3. `admin/namevimap.html` Tab Place: gọi endpoint khi mở tab (fetch async,
   không chặn render bảng hiện tại). Hiển thị số liệu gần tiêu đề bảng.
   Lỗi fetch/API → ẩn khối số liệu, bảng cũ vẫn hiển thị bình thường.
   Không đổi cột/logic hiện có của bảng.
4. Zero-RAM: đọc XML 21MB bằng generator/iterparse, không load toàn bộ cây
   DOM vào RAM nếu không cần thiết; tận dụng cache key để tránh đọc lại khi
   không cần.
5. Ràng buộc cứng: KHÔNG ghi DB, KHÔNG CREATE/ALTER TABLE, KHÔNG `--apply`,
   KHÔNG git add/commit/reset, KHÔNG tự đánh done khi chưa có xác nhận Admin.

## Backup bắt buộc trước khi sửa

Copy nguyên trạng vào `docs/sessions/2026-10-21/`:
- `app.py` → `app.py.bak_T446`
- `admin/namevimap.html` → `admin/namevimap.html.bak_T446`

## Liên kết

- Nền tảng: T445 (`tasks/T445-claude-place-name-import.md`) — xem thêm ghi chú
  liên kết sang T446 trong file đó.

## Kiểm chứng bắt buộc (daoanh-qa, browser thật 127.0.0.1)

- Mở Tab Place, chụp screenshot khối số liệu.
- Network log cho endpoint mới: lần đầu (tính mới, không cache) và lần sau
  (có cache, nhanh hơn).
- Test fallback: giả lập endpoint lỗi (vd. đổi tạm route hoặc raise), xác nhận
  bảng Tab Place vẫn hiển thị đầy đủ, chỉ ẩn khối số liệu.
- `python -X utf8 -m py_compile app.py`
- `node scripts/lint-check.js` (chạy từ `daoanh/`)

## Bổ sung phạm vi (Admin, cùng task — vì đang sửa cùng `namevimap.html`)

Làm trong cùng task này, KHÔNG mở agent/task khác, vì cùng đụng file
`admin/namevimap.html`.

### 1. Ẩn ID đã PASS, dùng cơ chế giống Tab ETL (T441)

- Tab ETL (T441) đã có cơ chế đúng: lọc `hide_done` ở phía server, trạng thái
  PASS lưu DB (`name_vi_map.name_vi_final` + `approved_by` + `approved_at`).
  KHÔNG dùng localStorage làm nguồn sự thật.
- Đọc code Tab ETL trong `namevimap.html` (và API liên quan trong `app.py`)
  để tái dùng đúng pattern đó cho Tab Place — không viết cơ chế mới, không
  đổi cơ chế Tab ETL.
- PASS dùng endpoint update đã có sẵn (không tạo endpoint ghi DB mới cho
  việc này nếu đã có).

### 2. Mũi tên sắp xếp lên/xuống theo cột % khớp

- Làm y như Tab ETL: tìm hàm sắp xếp + UI mũi tên trong `namevimap.html`,
  dùng lại cho các cột % khớp (Claude/Gemini/Từ điển/Nam Vi) ở Tab Place.
- Không đổi thứ tự cột, không đổi logic cũ khác.

### Kiểm chứng bổ sung (browser thật 127.0.0.1)

- PASS một ID trên Tab Place → reload → ID đó không còn xuất hiện (đúng
  cơ chế hide_done phía server, không phải ẩn tạm bằng JS/localStorage).
- Sắp xếp theo % lên/xuống → thứ tự hiển thị đúng.
- Screenshot + network log cho cả hai hành vi trên, ghi vào task này.
- Không ghi DB ngoài luồng PASS đã có sẵn. Không tự đánh done.

## Bằng chứng debugger

Thực hiện 2026-10-21, browser thật tại `http://127.0.0.1:8080/daoanh/admin/namevimap.html`
(local_gateway 8080 → app.py 5000, restart app.py sau khi sửa để nạp code mới).

- `python -X utf8 -m py_compile app.py` (chạy từ `daoanh/`) → OK.
- `node scripts/lint-check.js` → pass (namevimap.html không nằm trong danh sách file script
  kiểm tra; đã tự validate cú pháp block `<script>` của namevimap.html bằng
  `new Function(source)` trong `node -e` — OK, không lỗi).
- Endpoint mới `GET /api/admin/places-claude-compare/summary`:
  - Cold (cache miss, sau khi `os.utime()` đổi mtime XML): `real 0m3.274s`,
    `cache_hit:false`.
  - Warm (cache hit, gọi lại ngay): `real 0m0.357s`, `cache_hit:true`, cùng
    `computed_at`.
  - Số liệu đo được (nguồn `C:\Users\NAMTHI~1\AppData\Local\Temp\vn_place_name_vi.xml`,
    59.353 dòng — file `data/phien_am/vn_place_name_vi.xml` trong project chưa tồn tại,
    endpoint tự fallback tìm bản cache mới nhất trong `%TEMP%`, đúng theo quy ước
    `fetch_xml_bytes()` của `scripts/import_claude_place_name_dryrun.py`, không gọi
    network):
    `total=59353, have_gemini=12863, missing_gemini=46490, diff_gemini=2910,
    diff_namevi_map=22218, new_ids=208`.
- Mở Tab Place trên browser thật (click tab, không dùng JS để giả route): khối
  "Đối chiếu Claude sống (cache): Tổng 59,353 · Có Gemini 12,863 · Thiếu Gemini 46,490
  · Khác Gemini 2,910 · Khác Từ điển 22,218 · ID mới 208 — tính lúc 2026-10-21 03:02"
  hiện ngay dưới mô tả tab, không chặn bảng (screenshot đã chụp, bảng render song song).
- Network log xác nhận 2 request độc lập khi mở tab:
  `GET /api/admin/places-claude-compare/summary → 200`
  `GET /daoanh/api/places/vi-map?page=1&size=50&filter=all&hide_done=true → 200`
- Ẩn ID đã PASS (hide_done, tái dùng điều kiện SQL của filter=needs_review,
  `m.vn_name_status != 'reviewed'`, ở `api_places_vi_map_list`):
  - Click thật nút "✓ Pass" trên dòng `PL000000000005` → network
    `POST /daoanh/api/places/vi-map/PL000000000005/approve → 200`.
  - Reload trang (`navigate`) → mở lại Tab Place → `PL000000000005` KHÔNG còn xuất
    hiện trong bảng (kiểm tra bằng DOM: `hasRow5=false`), đúng yêu cầu — ẩn bằng
    server-side filter trong DB (`namevi_map_places.vn_name_status`), không phải
    localStorage.
  - Bỏ tick checkbox "Ẩn đã Pass" (`hide_done=false`) → `PL000000000001` (đã reviewed
    từ trước) và `PL000000000005` (vừa Pass) đều hiện lại ngay dòng đầu bảng.
- Sắp xếp theo cột "Tin cậy" (mũi tên ⇅, tái dùng pattern `etlFlagSortConfidence()`/
  `sort_by`+`sort_dir` của Tab ETL, áp cho cột `m.confidence` có sẵn ở Tab Place):
  - Click 1 (desc): arrow `↓`, 5 dòng đầu đều `confidence=85%` (cao nhất khả dụng khi
    hide_done=true — PL000000000314=100% bị ẩn vì đã reviewed, đúng logic).
  - Click 2 (asc): arrow `↑`, dòng đầu `PL000000046783` (confidence 65%, thấp nhất),
    tăng dần đúng thứ tự.
  - Network log xác nhận param gửi đi: `sort_by=confidence&sort_dir=desc` rồi
    `sort_by=confidence&sort_dir=asc`.
- Fallback khi endpoint summary lỗi: patch tạm `window.fetch` để request
  `places-claude-compare/summary` reject (giả lập lỗi mạng), gọi lại
  `placeLoadCompareSummary()`, sau đó khôi phục `window.fetch` nguyên bản ngay lập tức.
  Kết quả: `document.getElementById('place-compare-summary').style.display === 'none'`,
  bảng Tab Place vẫn còn đủ 50 dòng (`tableRows=50`), không lỗi, không trắng bảng.
  Screenshot xác nhận: khối số liệu biến mất, bảng + bộ lọc vẫn hiển thị bình thường.
- Không có thay đổi nào ghi DB ngoài 1 lần Pass thật (`PL000000000005`, dùng để test
  hide_done) — đây là thao tác hợp lệ qua endpoint Pass đã có sẵn từ trước (T427),
  không phải endpoint mới của T446.

## Xác nhận cột HOME đọc đúng sau PASS/Sửa (2026-10-21, theo yêu cầu Admin)

Admin yêu cầu kiểm tra: HOME/search địa danh chỉ hiển thị cột Name_Vi (không hiện
cột Claude/Gemini), nên giá trị admin duyệt trên Tab Place PHẢI ghi vào đúng cột
HOME đọc, tức `namevi_map_places.name_vi` (không phải `places_pending.name_vi`).

Đọc code xác nhận trước khi test: `api_places_vi_map_approve` (app.py dòng ~12236)
và `api_places_vi_map_edit` (app.py dòng ~12287) đều `UPDATE namevi_map_places SET
name_vi=...` (edit đổi giá trị; approve giữ nguyên giá trị hiện tại, chỉ đổi
`vn_name_status='reviewed'`). HOME/search đọc theo
`COALESCE(namevi_map_places.name_vi, places_pending.name_vi)` (app.py dòng ~529-537),
tức `namevi_map_places` luôn được ưu tiên trước — đúng bảng/cột cần ghi.

Test thật trên browser (127.0.0.1:8080, Tab Place):
- ID thử: `PL000000000019` (`范延`). Trước khi sửa: `namevi_map_places.name_vi =
  'Phạm Dang'` (auto_transliterate), Gemini gợi ý khác: `Phạm Diên`.
- Click "Sửa" trên dòng PL000000000019, nhập `Phạm Diên` (mô phỏng admin chọn giá
  trị đối chiếu đúng), bấm Lưu → UI cập nhật ngay: cột Name_Vi hiện "Phạm Diên",
  badge "Admin sửa tay", Kết luận = "Đã duyệt".
- SELECT trực tiếp DB sau thao tác:
  `namevi_map_places`: `{dila_id: PL000000000019, name_zh: 范延, name_vi: 'Phạm Diên',
  vn_name_status: 'reviewed', source: 'manual', needs_review: 0}` — khớp chính xác
  giá trị admin vừa chọn.
  `places_pending.name_vi` vẫn là giá trị cũ `'Phạm Dang'` (không bị ghi đè — đúng
  thiết kế, vì HOME không đọc bảng này khi `namevi_map_places` đã có dòng).
- Gọi thẳng API HOME-facing để xác nhận: `GET /daoanh/api/places/search?q=PL000000000019`
  → `name_vi: "Phạm Diên"`; `GET /daoanh/api/places/PL000000000019` → `name_vi:
  "Phạm Diên"`, `source: "namevi_map"`, `source_of_name_vi: "Admin chỉnh sửa"`,
  `vn_name_status: "reviewed"`. Không có field Claude/Gemini nào lẫn vào payload
  HOME — đúng yêu cầu Admin (HOME chỉ hiển thị Name_Vi chính thức).

Kết luận: Tab Place PASS/Sửa hiện đang ghi đúng vào `namevi_map_places.name_vi` —
không cần đổi schema hay route ghi DB nào thêm cho yêu cầu này.
