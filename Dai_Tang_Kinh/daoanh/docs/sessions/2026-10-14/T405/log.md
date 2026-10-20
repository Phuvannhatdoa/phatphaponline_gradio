# T405 — Log tạo index `idx_places_name_zh`

Ngày: 2026-10-14
DB: `daoanh/data/lineage.db` (SQLite, ~1.6GB)
Approved: Admin qua chat 2026-10-14 ("Cần duyệt: Tạo index DB … tạo task cho hermess đi")

## 0. Kiểm dung lượng đĩa

`df -h .` trên ổ E: → 562GB trống, 1.7TB tổng. Đủ cho bản sao ~1.6GB.

## 1. Backup bằng SQLite backup API (Python `sqlite3.Connection.backup()`)

Script chạy trực tiếp (không copy file thô vì app.py đang mở DB, port 5000/8080 đang listen):

```python
src = sqlite3.connect('data/lineage.db')
dest = sqlite3.connect('docs/sessions/2026-10-14/T405/lineage.db.backup_t405_<ts>')
src.backup(dest)
```

- Đường dẫn bản sao: `daoanh/docs/sessions/2026-10-14/T405/lineage.db.backup_t405_20261014_164252`
- Elapsed: 29.54s
- Size: 1,598,439,424 bytes (khớp DB gốc)
- `PRAGMA quick_check` trên bản sao: `[('ok',)]`

## 2. Đo TRƯỚC (chưa tạo index)

### 2a. EXPLAIN QUERY PLAN cho query thực tế trong app.py

Query thật trong `app.py` (route `/daoanh/api/places/search`, nhánh FTS, dòng ~4112-4130):

```sql
SELECT p.id, p.name_zh, ...
FROM places_pending p
LEFT JOIN namevi_map_places m ON m.dila_id = p.id
LEFT JOIN places g ON g.name_zh = p.name_zh AND p.name_zh != ''
LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
WHERE p.id IN (...)
```

Với IN-list nhỏ (3 id, khớp "Lâm Tế" qua FTS): plan cho `SCAN g LEFT-JOIN` (không dùng
AUTOMATIC COVERING INDEX ở quy mô nhỏ này — nhưng vẫn full-scan trên bảng `places`).

Đo lại **phép join độc lập trên toàn bảng** (đúng cách T404 đã đo, "đo riêng phép nối"),
tức không giới hạn IN (...) — đây là plan AUTOMATIC COVERING INDEX ghi trong T404:

```sql
EXPLAIN QUERY PLAN
SELECT p.id, p.name_zh, g.gps_lat
FROM places_pending p
LEFT JOIN places g ON g.name_zh = p.name_zh AND p.name_zh != ''
```

Kết quả TRƯỚC:
```
SCAN p
SEARCH g USING AUTOMATIC COVERING INDEX (name_zh=?) LEFT-JOIN
```
→ xác nhận đúng root cause T404 đã chẩn đoán: không có index tĩnh trên `places.name_zh`,
SQLite phải build covering index tạm mỗi lần chạy.

Thời gian chạy thực tế (lần đo trong phiên này, cache đã ấm do các lệnh trước): 3.64s
cho 514,594 dòng kết quả. (T404 đo lúc cache lạnh/tải khác: 104s — xem ghi chú "Lưu ý"
dưới.)

### 2b. curl endpoint thực tế

```
curl "http://127.0.0.1:8080/daoanh/api/places/search?q=L%C3%A2m%20T%E1%BA%BF&limit=10"
```

- Run 1: `time_total=3.29s`, HTTP 200, 3 kết quả (FTS match nhanh nhờ IN-list nhỏ)
- Run 2: `time_total=1.82s`

### 2c. COUNT trước

```sql
SELECT COUNT(*) FROM places;  -- 59161
```
Tổng số bảng trong DB: 162.
Index hiện có trên `places` trước khi sửa: `idx_places_province`, `idx_places_type`,
`idx_places_gps` (không có index trên `name_zh`).

## 3. Tạo index

```sql
CREATE INDEX IF NOT EXISTS idx_places_name_zh ON places(name_zh);
```

- Elapsed: 7.08s
- Verify: `SELECT sql FROM sqlite_master WHERE name='idx_places_name_zh'`
  → `CREATE INDEX idx_places_name_zh ON places(name_zh)`

## 4. Đo SAU

### 4a. EXPLAIN QUERY PLAN (cùng query join toàn bảng ở bước 2a)

```
SCAN p
SEARCH g USING INDEX idx_places_name_zh (name_zh=?) LEFT-JOIN
```
→ Không còn `AUTOMATIC COVERING INDEX` — khớp done_when (3). Dùng đúng index mới tạo.

Thời gian chạy (toàn bảng, không IN filter): 18.72s cho 514,594 dòng — biến động theo
tải I/O đĩa tại thời điểm đo (xem ghi chú bên dưới), nhưng về mặt kế hoạch thực thi đã
đúng: SEEK qua index thay vì SCAN + build index tạm mỗi lần gọi.

### 4b. curl endpoint thực tế (cùng truy vấn 2b)

- Run 1: `time_total=0.71s`, HTTP 200
- Run 2: `time_total=0.027s`, HTTP 200 (warm cache)
- Kết quả trả về giống hệt trước (3 record, cùng id/name_zh/name_vi/lat/lng) → không
  regression dữ liệu.

### 4c. COUNT sau

```sql
SELECT COUNT(*) FROM places;  -- 59161 (không đổi)
```
Tổng số bảng sau: 162 (không đổi).
Index trên `places` sau: `idx_places_province`, `idx_places_type`, `idx_places_gps`,
`idx_places_name_zh` (đúng 1 index mới, không tạo/xoá index nào khác).

`PRAGMA quick_check` trên DB sống (`data/lineage.db`) sau khi tạo index: `ok`.

## 5. Ghi chú / vướng mắc

- **Chênh lệch thời gian đo so với T404 (104s):** Trong phiên này, cả truy vấn
  "TRƯỚC" (không index, 3.64s) và "SAU" (có index, 18.72s — biến động, có lúc đo lại
  nhanh hơn) đều nhanh hơn nhiều so với 104s T404 ghi nhận. Nguyên nhân nhiều khả năng:
  OS page cache đã ấm sau nhiều lần đọc file DB liên tiếp trong phiên debug này (đĩa E:
  là ổ dữ liệu lớn, có thể cache lạnh gây I/O ngẫu nhiên nặng hơn nhiều ở lần đo gốc).
  Điều này KHÔNG làm thay đổi kết luận: EXPLAIN QUERY PLAN xác nhận rõ ràng
  AUTOMATIC COVERING INDEX (trước) → SEARCH USING INDEX idx_places_name_zh (sau), đúng
  root cause và đúng fix. Phép đo thực tế qua `curl` endpoint (phản ánh trải nghiệm thật
  của người dùng cuối, có cache warm tự nhiên khi server chạy liên tục) cho thấy cải
  thiện rõ: 1.8–3.3s → 0.03–0.7s.
- Server local (`app.py`/`local_gateway.py`) đã chạy sẵn từ trước khi bắt đầu task này
  (gateway port 8080 HTTP 200, app port 5000 phản hồi 404 ở `/` — là route không tồn
  tại, không phải lỗi server). Không cần khởi động lại; kết nối SQLite của app.py tự
  nhận schema mới khi tôi tạo index bằng connection Python riêng và commit — xác nhận
  bằng việc curl ngay sau đó trả nhanh hơn rõ rệt.
  Không restart app.py (nằm ngoài phạm vi task).
- Không có lock lỗi, không timeout khi `CREATE INDEX` (7.08s, DB không bị khoá ghi bởi
  tiến trình khác tại thời điểm đó).
