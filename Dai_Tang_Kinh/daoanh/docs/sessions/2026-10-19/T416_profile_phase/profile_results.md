# T416 — Profile `/daoanh/api/public/autocomplete` (phase 1-2: profile + đề xuất, chưa sửa code)

Ngày: 2026-10-19
Phạm vi: chỉ đo và đề xuất, KHÔNG sửa `app.py`, KHÔNG tạo index trong phiên này.

## 1. Route thật đang chạy

`app.py:12358-12417` — `@app.route('/daoanh/api/public/autocomplete')` → `public_autocomplete()`.
Xác nhận đây đúng là endpoint frontend gọi: `places.html:1945`
`fetch('/daoanh/api/public/autocomplete?q=' + encodeURIComponent(q), ...)`.

Route chạy tối đa 4 query SQL **tuần tự**, chỉ dừng sớm khi đã đủ 10 kết quả:

| # | Bảng | Cột so khớp | Điều kiện chạy |
|---|------|-------------|-----------------|
| 1 | `namevi_map_places` (118,296 dòng) | `name_vi LIKE '%q%'` | luôn chạy |
| 2 | `places_pending` (176,783 dòng) | `name_zh LIKE '%q%'` | nếu kết quả #1 < 10 |
| 3 | `marcus_reference` (18,127 dòng) | `label_vi LIKE '%q%' OR label LIKE '%q%'` | nếu kết quả < 10 |
| 4 | `lexicon` (166,278 dòng) | `term LIKE '%q%'` | nếu kết quả < 10 |

Không có gọi lồng `/api/monk-resolve` trong route này (nghi vấn trong T404 không đúng với route thật đang
được gọi — đã kiểm tra lại toàn bộ thân hàm, không có `monk-resolve`).

## 2. Đo trực tiếp bằng `sqlite3` qua Python, case "Thiếu L" (case T404 ghi nhận chậm nhất)

DB: `data/lineage.db` (1.5 GB, `PRAGMA page_count` = 390,519 × `page_size` 4096).

### EXPLAIN QUERY PLAN + thời gian thực thi từng query (lần đầu / cache lạnh)

```
==== mapped (namevi_map_places) ====
  SCAN namevi_map_places
  USE TEMP B-TREE FOR DISTINCT
  rows=3  time=175.0ms

==== pending (places_pending) ====
  SCAN places_pending
  USE TEMP B-TREE FOR DISTINCT
  rows=0  time=9620.3ms   <-- nút nghẽn chính

==== marcus (marcus_reference) ====
  SCAN marcus_reference
  rows=4  time=19.0ms

==== lexicon ====
  SCAN lexicon USING COVERING INDEX idx_lex_term
  rows=10  time=113.3ms
```

Tổng cộng lần đầu (cache lạnh): **175 + 9620 + 19 + 113 ≈ 9.9 s** — khớp đúng với báo cáo "1–9 s" của Admin.

### Chạy lại cùng query sau khi cache ấm (3 lần, chỉ riêng `places_pending`)

```
run0: rows=0 time=1096.8ms
run1: rows=0 time=1095.9ms
run2: rows=0 time=1274.5ms
```

→ Khi cache ấm, vẫn mất ~1.1–1.3 s chỉ cho bảng `places_pending`. Biên độ "1 s (ấm) – 9 s (lạnh)" chính là do
cache OS/SQLite bị đẩy ra (DB 1.5 GB, máy dev không đủ RAM giữ nóng toàn bộ) — không phải do tải khác nhau
giữa các lần gõ.

## 3. Root cause xác minh

### 3a. `LIKE '%...%'` có wildcard ở đầu → B-Tree index không thể seek
Cả 4 query đều dùng `LIKE '%q%'` (wildcard hai đầu) nên SQLite **không thể** dùng index để seek theo range —
đây là hạn chế cố hữu của B-Tree index với substring match. Điều này đã được chính codebase ghi nhận ở
`app.py` dòng 12533-2543 (comment T58/T11): cùng kiểu LIKE trên `places_pending`/`namevi_map_places` (118K/118K
dòng) đo được "~2.5 s/query" và đã được thay bằng FTS5 (`places_pending_fts`) cho endpoint `/daoanh/api/search`.
**Route `/daoanh/api/public/autocomplete` chưa áp dụng fix tương tự** — đây là khác biệt chính giữa route đã
tối ưu và route đang chậm.

### 3b. Planner KHÔNG dùng index sẵn có cho `places_pending`, dù index tồn tại
`places_pending` đã có `idx_places_pending_name_zh` (index trên đúng cột đang LIKE), nhưng
`EXPLAIN QUERY PLAN` cho thấy SQLite chọn `SCAN places_pending` (full table scan, đọc cả 21 cột kể cả
`raw_xml`) thay vì scan qua index hẹp hơn.

Test ép buộc dùng index (`INDEXED BY idx_places_pending_name_zh`):
```
forced index-scan time: 224.5 ms   (so với scan bảng ấm cache ~1.1-1.3s, lạnh cache ~9.6s)
```
→ Chỉ riêng việc để planner chọn đúng index đã hẹp hơn, speedup đã **~5x (ấm cache)**, và lớn hơn nhiều ở cache
lạnh (ước tính vì index nhỏ hơn nhiều so với bảng đầy đủ cột — bảng có `raw_xml` trung bình 366 ký tự/dòng,
tổng ~64 MB chỉ riêng cột đó).

Nguyên nhân planner bỏ qua index: `sqlite_stat1` **không tồn tại** — DB chưa từng chạy `ANALYZE`, nên planner
không có thống kê chi phí để ưu tiên index hẹp hơn so với scan bảng đầy đủ.

### 3c. `namevi_map_places` và `marcus_reference` không có index nào trên cột đang LIKE
`namevi_map_places.name_vi` và `marcus_reference.label_vi`/`label` hoàn toàn không có index — chỉ có thể full
table scan. Hai bảng này tương đối nhỏ (118K và 18K dòng) nên hiện tại chưa phải nút nghẽn chính (175ms, 19ms),
nhưng sẽ xấu dần nếu bảng tăng kích thước.

### 3d. Không phải do Python/vòng lặp
Phần xử lý Python sau khi fetchall (dedupe bằng `seen`, cắt chuỗi `value`, gọi `ensure_long_id`) chạy trên tối
đa 10 dòng → chi phí không đáng kể (<1ms), không phải nút nghẽn.

## 4. Trả lời 4 câu hỏi root cause

1. **Data thực tế trong DB:** đúng như kỳ vọng — `places_pending` không có dòng nào khớp "Thiếu L" trên cột
   `name_zh` (Hán), hợp lý vì so khớp Việt-Latin với Hán tự gần như luôn miss → luôn phải scan hết bảng.
2. **API trả về gì:** đúng hợp đồng (`{"success": true, "data": [...]}`) — vấn đề là **thời gian**, không phải
   nội dung.
3. **Resolver/route xử lý sai ở đâu:** route chạy 4 query SQL tuần tự dùng `LIKE '%q%'` không seek được bằng
   index; với `places_pending` cụ thể, planner còn bỏ qua index sẵn có do thiếu `ANALYZE` stats.
4. **UI thiếu/sai gì:** không — UI (đã fix ở T404) chỉ đợi response của route này; vấn đề hoàn toàn ở backend.

## 5. Phân loại lỗi

`mapping` (query pattern không tận dụng index có sẵn) + `data` (thiếu ANALYZE/thiếu index phụ) — không phải
`API contract`, `resolver` (theo nghĩa graph), `renderer`, `layout`, `state`, hay `async`.

## 6. Đề xuất sửa (CHƯA THỰC HIỆN — chờ Admin duyệt)

Thứ tự đề xuất theo rủi ro tăng dần:

### Đề xuất A — Chạy `ANALYZE` trên `data/lineage.db` (rủi ro thấp nhất, không đổi schema)
```sql
ANALYZE places_pending;
ANALYZE namevi_map_places;
ANALYZE marcus_reference;
```
Không sửa dữ liệu, không đổi schema, chỉ ghi `sqlite_stat1`/`sqlite_stat4`. Có thể giúp planner tự chọn
`idx_places_pending_name_zh` mà không cần sửa code. Cần đo lại sau khi chạy để xác nhận planner đổi lựa chọn
hay không — nếu không đổi, chuyển sang đề xuất B.

### Đề xuất B — Ép dùng index có sẵn bằng `INDEXED BY` trong `app.py:12376`
```python
pending = conn.execute(
    "SELECT DISTINCT id, name_zh AS value, name_zh AS name_zh, 'pending' AS source "
    "FROM places_pending INDEXED BY idx_places_pending_name_zh WHERE name_zh LIKE ? LIMIT ?",
    (like, remaining)
).fetchall()
```
Đo thực tế: 224ms (ấm cache) so với 1.1-1.3s hiện tại — giảm ~5x, và giảm mạnh hơn ở cache lạnh. Rủi ro thấp:
chỉ thêm gợi ý index, không đổi logic/kết quả trả về.

### Đề xuất C — Thêm index còn thiếu cho `namevi_map_places.name_vi` và `marcus_reference(label_vi, label)`
```sql
CREATE INDEX idx_namevi_map_places_name_vi ON namevi_map_places(name_vi);
CREATE INDEX idx_marcus_reference_label_vi ON marcus_reference(label_vi);
CREATE INDEX idx_marcus_reference_label ON marcus_reference(label);
```
Hai bảng này hiện chưa phải nút nghẽn chính (175ms/19ms) nhưng không có index nào trên cột LIKE; thêm index
hẹp giúp phòng ngừa khi bảng lớn hơn, và nhất quán với cách `places_pending`/`lexicon` đã được lập index.
Cần backup DB trước khi `CREATE INDEX` theo CLAUDE.md, có `DROP INDEX` revert tương ứng, không mất dữ liệu.

### Đề xuất D — Hướng dài hạn: chuyển `/autocomplete` sang dùng FTS5 như `/api/search` đã làm
Codebase đã có đúng pattern cho vấn đề này ở `app.py:12533-12543` (`ensure_places_pending_fts` +
`places_pending_fts MATCH`) dùng cho `/daoanh/api/search`, với comment ghi rõ lý do: LIKE wildcard hai đầu
trên 118K/118K dòng ~2.5s, chuyển sang FTS5 prefix match giải quyết được. Route `/autocomplete` nên tái dùng
đúng FTS table này (và tạo FTS tương ứng cho `namevi_map_places`/`marcus_reference`/`lexicon` nếu cần) thay vì
viết lại LIKE scan riêng. Đây là hướng bền vững nhất (không phụ thuộc ANALYZE/planner), nhưng phạm vi sửa lớn
hơn A/B/C — nên làm sau khi A/B đã xác nhận không đủ.

## 7. Khuyến nghị thứ tự thực hiện (chờ Admin duyệt riêng bước sửa code)

1. Thử A (ANALYZE) trước — rẻ nhất, không sửa code.
2. Nếu A không đủ, làm B (INDEXED BY hint tại app.py:12376) — đã đo trước, biết chắc hiệu quả ~5x.
3. Làm C song song (thêm 2-3 index nhỏ, có backup+revert) để tránh nút nghẽn tương tự ở 2 bảng còn lại khi dữ
   liệu tăng.
4. D để sau, chỉ làm nếu A+B+C vẫn không đạt mốc <200ms ổn định ở cache lạnh.

Dự kiến nếu làm A+B+C: tổng thời gian còn lại ước tính ~175ms (mapped, chưa tối ưu) + ~100-220ms (pending sau
khi có index) + ~20-50ms (marcus sau khi có index) + ~113ms (lexicon, đã nhanh) ≈ 400-550ms worst case (vẫn
trên mốc <200ms yêu cầu) — nếu cần đạt chắc <200ms thì bước D (FTS5) hoặc giảm số bảng query tuần tự
(parallel hoá hoặc rút ngắn danh sách nguồn) sẽ cần thêm.

## 8. Việc CHƯA làm trong phiên này

- Không sửa `app.py`.
- Không chạy `ANALYZE` hoặc `CREATE INDEX` trên `data/lineage.db` (chỉ test bằng `INDEXED BY` tạm thời trong
  Python script, không ghi gì vào DB).
- Chưa đo lại luồng "mớm từng chữ" T404 trên browser thật (nằm ở bước 3-4 của done_when, sau khi Admin duyệt
  hướng sửa).
