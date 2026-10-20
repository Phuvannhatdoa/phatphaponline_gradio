# Audit Report — So sánh "Đơn Hà Thiên Nhiên" Local vs VPS

> Lưu tại `docs/DONHA_THIEN_NHIEN_LOCAL_VPS_COMPARE_REPORT.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db` → bảng `people` (48,673 rows), cột `name_vi`/`name_zh` |
| API endpoint | `GET /daoanh/api/search?q=...` |
| Resolver / logic | `app.py:11965-12049` (`api_global_search`) |
| Component / renderer | N/A — chưa tới UI, API đã trả kết quả rỗng ở cả 2 môi trường |
| Schema contract | Không đổi |

## 2. Root cause (đã xác minh)

**Lớp gây lỗi:** không phải bug data/API của PTDA — **local networking (port collision)**.

### Phát hiện chính

`http://localhost:8080/daoanh/...` trên máy local **không** luôn tới `local_gateway.py`.
`Get-NetTCPConnection -State Listen` cho port 8080 trả về **2 process khác nhau**:

| Bind address | Port | PID | Process |
|---|---|---|---|
| `127.0.0.1` | 8080 | 7404 | `python.exe local_gateway.py` (đúng — Đạo Ảnh) |
| `::` (IPv6 wildcard, mọi interface) | 8080 | 27260 | Node.js server của dự án **khác** — `ZenQian/ZQ-Claude` (`server.js`, khởi động từ một bash session riêng, project "ZenQ Premium") |

Trên Windows, `localhost` thường resolve `::1` (IPv6) trước `127.0.0.1` (IPv4). Vì process Node bind `::` (wildcard, bắt cả IPv6 loopback), request `curl http://localhost:8080/...` bị route vào **server Node.js của dự án ZenQ Premium** — một trang thương mại/hàng không hoàn toàn không liên quan — thay vì vào Flask gateway của Đạo Ảnh. Đây chính là nguồn gốc "kết quả khác nhau" admin quan sát: không phải do data PTDA sai, mà do **một server dev khác của session trước đã chiếm port 8080 trên toàn bộ interface**.

Khi ép IPv4 rõ ràng (`curl -4 http://127.0.0.1:8080/...` hoặc gọi thẳng Flask port 5000), response đúng là của Đạo Ảnh.

### Sau khi loại trừ nhiễu port, so sánh thực sự local vs VPS

| | Local (`127.0.0.1:8080` và `127.0.0.1:5000`) | VPS (`https://158.220.106.183/daoanh/...`) |
|---|---|---|
| HTTP status | 200 | 301 (http→https) → 200 sau redirect |
| Response | `{"monks":[],"places":[],"works":[]}` | `{"monks":[],"places":[],"works":[]}` |

**Giống hệt nhau** — cả 2 môi trường đều trả rỗng cho `q=Đơn Hà Thiên Nhiên`. Không có khác biệt data/API thật giữa local và VPS.

### Vì sao query rỗng ở cả 2 nơi (data gap thật, nhưng không phải bug môi trường)

Tra trực tiếp `people` table:
- `name_vi LIKE '%Đơn Hà%'` → 0 rows
- `name_vi LIKE '%Đan Hà%'` → 1 row không liên quan (`Đan Hàm Thắng`)
- `name_zh LIKE '%丹霞%'` → 0 rows (tên Hán gốc của tổ sư Đan Hà Thiên Nhiên — 丹霞天然 — không tồn tại trong DB dưới dạng ghép họ+pháp danh)
- `name_vi LIKE '%Thiên Nhiên%'` → 10 rows, **đồng danh** (`Thiên Nhiên`, `Thiên Nhiên Tuệ`, `Thiên Nhiên Nhân`...), không row nào ghép "Đan/Đơn Hà + Thiên Nhiên"

→ Thiền sư Đan Hà Thiên Nhiên (丹霞天然, đời Đường) trong DB hiện chỉ tồn tại rời rạc dưới pháp danh "Thiên Nhiên" (nhiều đồng danh, chưa rõ ID nào đúng), **không có bản ghi nào mang tên núi "Đan Hà/丹霞"** ghép kèm. Đây là data gap ở nguồn DILA gốc hoặc ở bước import — cần audit riêng (không thuộc phạm vi "local vs VPS khác nhau" của task này).

## 3. Data/API contract trước → sau

Không có thay đổi — không phát hiện lỗi API/resolver cần sửa. `lineage.db` trên local và VPS xác nhận giống hệt (đúng như `sync_to_vps.log` ghi "unchanged" lần sync 12:35).

## 4. Files changed

- Không có file nào được sửa. Đây là audit/so sánh, không phải bug fix code.

## 5. Migration / import / dry-run / rollback

- Không áp dụng (không chạm DB, không migration).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| So sánh API local vs VPS | `q=Đơn Hà Thiên Nhiên` qua `127.0.0.1:8080`, `127.0.0.1:5000`, và VPS https | Cùng response | Cả 2 đều `{"monks":[],"places":[],"works":[]}` | ✅ giống nhau |
| Fallback — `localhost` (không ép IPv4) | `q=Đơn Hà Thiên Nhiên` qua `http://localhost:8080/...` | Nên = Đạo Ảnh gateway | Trả về trang HTML của dự án khác ("ZenQ Premium", port collision IPv6) | ⚠️ xác nhận nguyên nhân gây hiểu nhầm "khác nhau" |
| Data gap check | `people.name_vi/name_zh LIKE '%Thiên Nhiên%' / '%丹霞%' / '%Đơn/Đan Hà%'` | Tìm thấy entity ghép đủ tên | Chỉ có "Thiên Nhiên" rời rạc (10 đồng danh), không có "Đan Hà" ghép | data gap xác nhận, tồn tại ở cả 2 môi trường như nhau |

## 7. Limitation / data gap còn lại

1. **Không phải bug môi trường** — kết luận: local và VPS **cùng data, cùng API response** cho entity này. "Khác nhau" admin thấy nhiều khả năng do port 8080 bị một Node.js server khác (dự án ZenQian/ZQ-Claude, PID 27260, bind `::` wildcard) chiếm chung, khiến `http://localhost:8080` route nhầm sang server đó trên máy local. Cần đóng/dừng server Node đó hoặc luôn dùng `127.0.0.1:8080` (ép IPv4) khi test Đạo Ảnh local, hoặc đổi port server kia.
2. **Data gap thật (riêng, không thuộc nguyên nhân local≠VPS):** DB `people` chưa có bản ghi ghép "Đan Hà Thiên Nhiên" (丹霞天然) — chỉ có "Thiên Nhiên" rời rạc với 10 đồng danh, id nào đúng với vị tổ sư nổi tiếng đời Đường chưa xác định. Việc này cần audit nguồn DILA/import riêng, ngoài phạm vi task so sánh local/VPS.
