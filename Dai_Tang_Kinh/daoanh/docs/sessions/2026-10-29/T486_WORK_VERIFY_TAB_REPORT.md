# Audit / Build Report — T486 Tab "Xác minh tác giả"

> Task: `daoanh/tasks/T486-catalog-work-metadata-relations.md`, mục
> "Phần việc đang làm (2026-10-29) — Tab Xác minh tác giả".

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source (đo sẵn) | `docs/sessions/2026-10-29/work-metadata/t486_dryrun.csv` — 3.557 dòng, lọc `field='contributor'` còn 1.870 dòng / 794 `person_id` |
| Data source (DB) | `dila_catalog_contributors` (cbeta_id, person_id, name_zh, name_vi), `dila_catalog_works` (cbeta_id, title_zh), `people` (id, name_zh, name_vi) |
| Khóa join | `dila_catalog_contributors.person_id` = `people.id` = `name_vi_map.dila_id` (đã kiểm bằng DB: `person_id='A000457'` ↔ `people.id='A000457'`, name_zh=呂夷簡) |
| API GET | `GET /daoanh/api/admin/work-verify?group=&page=&size=&q=` (chỉ đọc, mode='ro') |
| API POST | `POST /daoanh/api/admin/work-verify/<person_id>/pass` body `{name_vi}` |
| UI | `admin/namevimap.html` — tab mới `tab-workverify`, nút tabbar `#workverify-tab-btn` |
| Backup trước sửa | `docs/sessions/2026-10-29/namevimap.html.before-t486-verify`, `docs/sessions/2026-10-29/routes_namevi.py.before-t486-verify` (đã có sẵn trước khi bắt đầu, không tạo lại) |

## 2. Root cause / lý do thiết kế

- **Lớp triển khai:** API mới (đọc CSV + DB) + ghi theo cơ chế hiện có, không phải sửa lỗi 1 lớp cụ thể — đây là tính năng mới cho task T486.
- **Vì sao dùng `name_vi_map` keyed theo `dila_id` để ghi, không tạo bảng/cột mới:**
  Đã đọc `routes_namevi.py:515-592` (`admin_namevi_map_update`), có chú thích ngay trong code:
  > "Endpoint này ghi `name_vi_map.name_vi_final` + `approved_by='admin'` + `people.name_vi` ⇒ đây chính là nguồn tạo LOCKED authority (`SOURCE_LEVELS['name_vi_map.final+approved']=1.0`)."
  Cơ chế: `UPDATE/INSERT name_vi_map WHERE dila_id=?` (ưu tiên row `confidence DESC`), sau đó `UPDATE people SET name_vi=? WHERE id=?` (bỏ qua nếu `name_vi='—'`). Đã kiểm `dila_catalog_contributors.person_id` và `name_vi_map.dila_id`/`people.id` là cùng một không gian khóa (mẫu `A0xxxxx`), nên tái dùng chính xác cơ chế này cho `person_id`, không tự chế cột/bảng.
- **Vì sao `approved_by` không hard-code `'admin'` như `admin_namevi_map_update`:**
  `core.py:5073` định nghĩa `_t427_session_email(token)` — gọi `server.py` (`/api/login/check`) lấy email thật của session, đã được `routes_places.py:2914/2962/4276` dùng cho tab Place/Catalog. Endpoint `/pass` mới dùng đúng hàm này (import thêm vào `routes_namevi.py`) để `approved_by` = email admin thật, đúng yêu cầu đề bài.
- **Nơi khác đọc cùng nguồn tên (để xác nhận tên mới hiển thị đúng sau khi Pass):**
  - `routes_lineage.py:2439-2442` (`api_global_search`, dùng cho tìm kiếm trang chủ):
    `SELECT c.person_id, c.name_zh, COALESCE(p.name_vi, c.name_vi) AS name_vi, c.name_vi_src FROM dila_catalog_contributors c LEFT JOIN people p ON p.id = c.person_id` — ưu tiên `people.name_vi` ⇒ sau khi Pass (ghi `people.name_vi`) tên mới hiện ra ngay ở đây.
  - `routes_lineage.py:2452` (`dila_people`, thẻ người trong kết quả tìm kiếm): `LEFT JOIN people p ON p.id = c.person_id`, dùng `p.name_vi` trực tiếp ⇒ cũng đọc đúng nguồn vừa ghi.
  - `routes_lineage.py:2572-2597` (`public_dila_works`, nút "Xem tất cả" tác phẩm của 1 người trên trang Person): không SELECT tên người trực tiếp (chỉ trả về works + places_vi) — route này không hiển thị tên contributor, nên không bị ảnh hưởng và không cần sửa.
  - **Lưu ý còn hở:** `dila_catalog_contributors.name_vi` (cột riêng, nguồn `ZQLOCAL` ghi lúc import T453) **không** được đồng bộ lại khi Pass — chỉ `people.name_vi` được cập nhật. Mọi nơi đọc tên hiện tại đều ưu tiên `people.name_vi` (COALESCE hoặc join trực tiếp) nên hiển thị đúng, nhưng nếu sau này có code đọc thẳng `c.name_vi` mà không join `people`, sẽ thấy tên cũ — đã rà bằng `codegraph_explore` + `grep -rn dila_catalog_contributors`, không thấy route nào đọc `c.name_vi` mà không kèm fallback `people.name_vi` (xem bảng trên). Ghi rõ ở đây để Admin/agent sau biết.
- **Vì sao gom theo `person_id` bằng mode (giá trị xuất hiện nhiều nhất)** thay vì 1-1 theo dòng CSV: `file_value` (tên đề xuất) có thể khác nhau theo từng tác phẩm vì file `vi.json` ghi tên contributor theo từng cặp (person, work) riêng — ví dụ A034224 có 3 biến thể `Cống Cáp Hô Đồ Khắc Đồ` / `Cống Cáp` ở các cbeta_id khác nhau. Yêu cầu đề bài là "mỗi người một dòng", nên lấy giá trị phổ biến nhất làm đề xuất chính (ô input, sửa được), các biến thể khác hiển thị phụ (`name_file_variants`) để Admin biết trước khi Pass — không tự chọn/suy luận nghĩa, chỉ liệt kê nguyên văn từ file.

## 3. Thay đổi API/UI chính (contract trước/sau)

### Trước
Không có endpoint `/daoanh/api/admin/work-verify*`; không có tab "Xác minh tác giả" trong `namevimap.html`.

### Sau

**`GET /daoanh/api/admin/work-verify?group=A|B|C|ALL&page=&size=&q=`** (chỉ đọc, không ghi DB)
```json
{
  "ok": true, "mode": "ro", "total": 794, "page": 1, "size": 50, "pages": 16,
  "items": [{
    "person_id": "A000095", "name_zh": "Amoghavajra",
    "name_db": "Amoghavajra", "name_file": "Bất Không",
    "name_file_variants": ["A-mộ-già", "A-mộ-già Tam Tạng", "Bất Không"],
    "group": "B_untrans", "work_count": 183,
    "works": [{"cbeta_id": "F1048", "title_zh": "一切如來白傘蓋大佛頂陀羅尼"}, "..."],
    "passed": false
  }],
  "warning": "... (chỉ xuất hiện khi không đọc được CSV)"
}
```
Sắp theo `work_count` giảm dần, như yêu cầu. `name_db` lấy `people.name_vi` HIỆN TẠI (sống) nếu có, fallback giá trị đo trong CSV dry-run. `passed=true` khi `people.name_vi` hiện tại khác giá trị đã đo trong CSV (xem mục 7 — giới hạn của cách phát hiện này).

**`POST /daoanh/api/admin/work-verify/<person_id>/pass`** body `{"name_vi": "..."}`
- Header `X-Session-Token` bắt buộc → thiếu/sai trả `403 {"ok": false, "error": "Unauthorized"}` (đã kiểm, không raise 500).
- Ghi `name_vi_map` theo `dila_id=person_id` (update row confidence cao nhất, hoặc insert mới), `approved_by` = email thật từ `_t427_session_email(token)`, `approved_at` = ISO timestamp hiện tại.
- Sync `people.name_vi = name_vi` CHỈ cho `person_id` trong URL.
- Trả `{"ok": true, "person_id", "name_vi", "approved_by", "approved_at"}`.

**UI**: tab mới `✍️ Xác minh tác giả` (nút cuối tabbar, sau `📚 Catalog`), bảng `etl-ba-table` 8 cột (Mã người, Hán, Tên hiện tại DB, Tên đề xuất file + ô sửa, Nhóm, Số tác phẩm, Tác phẩm tiêu biểu, Pass), nút Pass dùng class `etl-flag-pass` có sẵn. Lọc nhóm bằng `.seg` (dùng lại style TTLLocal filter), tìm kiếm debounce 350ms, phân trang 50 dòng/trang (cùng mẫu với tab Catalog). Không dùng `localStorage` cho dữ liệu nghiệp vụ — chỉ gọi API; state tạm (`_wvPage`, `_wvGroup`, `_wvQ`) nằm trong biến JS module-scope, mất khi tải lại trang (chấp nhận được, đúng yêu cầu).

## 4. Files changed

- `daoanh/routes_namevi.py` — thêm import `_t427_session_email`, `csv as _t486_csv`; thêm 2 route mới `admin_work_verify_list` (GET) và `admin_work_verify_pass` (POST) + 2 hàm phụ `_t486_load_csv_rows`, `_t486_aggregate_person` (cuối file, sau `admin_namevi_map_places_delete`).
- `daoanh/admin/namevimap.html` — thêm nút tab `#workverify-tab-btn` (sau `#catalog-tab-btn`), panel `#tab-workverify` (sau `<!-- /tab-catalog -->`, trước Edit Modal), hook `switchTab()` cho `name === 'workverify'`, và cụm hàm JS `wvSearchDebounce/wvSetGroup/_wvWorksCell/wvLoad/wvPassPerson` (sau `catalogPassWork`, trước "AI Transliterate"). Không sửa nội dung tab Catalog/ETL/Place/Queue/TTL/Xác Minh hiện có.

## 5. Migration / DB — không áp dụng

Không đổi schema, không tạo bảng/cột mới, không migration. Backup 2 file trước khi sửa đã có sẵn tại `docs/sessions/2026-10-29/*.before-t486-verify` (do coordinator tạo trước khi giao việc).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| `py_compile` | `routes_namevi.py` | không lỗi cú pháp | `OK_COMPILE` | ✅ |
| `node --check` JS inline | script tách từ `namevimap.html` → file tạm trong scratchpad | không lỗi cú pháp | `JS_OK` | ✅ |
| GET mặc định (yêu cầu) | `GET /daoanh/api/admin/work-verify?group=ALL&page=1&size=5` qua `127.0.0.1:8080` | JSON hợp lệ, `ok:true`, `total=794`, sort theo `work_count` desc | `ok:true total:794 pages:397`, item đầu `person_id=A000095 work_count=183` (giảm dần đúng) | ✅ |
| Filter nhóm C | `?group=C` | chỉ trả người có nhóm `C_review` nặng nhất | `total=618` (618/794 người có ít nhất 1 dòng C_review) | ✅ |
| Tìm kiếm `q` | `?q=A001583` | ra đúng 1 người | `total=1` | ✅ |
| Edge: group lạ | `?group=X` | coi như `ALL`, không lỗi | `ok:true total:794` | ✅ (fallback) |
| Edge: size quá lớn | `?size=99999` | clamp về 200 | `size:200, 200 items` | ✅ (fallback) |
| Edge: CSV thiếu file (đổi tên tạm) | `GET .../work-verify` khi file không tồn tại | không 500, trả `total:0` + `warning` | `ok:true total:0 warning:"Không đọc được ... CSV dry-run."` — đã phục hồi file ngay sau | ✅ (fallback null/missing-source) |
| POST thiếu/sai token | `POST .../A001583/pass` không có header hoặc token rác | `403`, không ghi DB, không 500 | `HTTP 403 {"ok":false,"error":"Unauthorized"}` (2 lần: không header và token bogus) | ✅ |
| Không bấm Pass thật | — | theo yêu cầu, KHÔNG test luồng ghi thành công trong lượt build này | chỉ test nhánh 403 (auth reject) — không có request POST nào với token hợp lệ được gửi | ✅ (tuân thủ ràng buộc) |

## 9. Sửa 3 rủi ro còn lại trước khi Admin tự thử Pass (2026-10-29, build tiếp theo)

Agent nhận việc qua coordinator (task T486, 3 điểm rủi ro ở mục 7 cũ). Đọc lại
report này + `routes_namevi.py:1151-1421` trước khi sửa, đúng chỉ đạo.

**Backup trước khi sửa:**
`docs/sessions/2026-10-29/work-verify-fix/routes_namevi.py.before-fix3`,
`docs/sessions/2026-10-29/work-verify-fix/namevimap.html.before-fix3`
(namevimap.html cuối cùng không cần sửa — lỗi 400/403/404 đã hiển thị rõ qua
`alert('Lỗi: ' + e.message)` / dòng lỗi bảng có sẵn, xem bảng dưới).

### 9.1. Root cause đã xác minh cho từng điểm

**Điểm 1 — Group không hợp lệ fallback về ALL (đã xác minh đúng như báo cáo mục 6):**
Code cũ (`admin_work_verify_list`, trước sửa):
```python
group_filter = (request.args.get('group') or 'ALL').strip().upper()
group_map = {'A': 'A_format', 'B': 'B_untrans', 'C': 'C_review'}
group_filter_full = group_map.get(group_filter)  # None nếu 'ALL' hoặc giá trị lạ
```
`group_map.get('X')` trả `None` — **giống hệt** trường hợp `'ALL'` — nên nhánh
`if group_filter_full:` không lọc gì, coi `group=X` như `ALL`. Xác nhận bằng
UI thật: `admin/namevimap.html:963-966` chỉ gửi `A`/`B`/`C`/`ALL` (nút `.seg`
gọi `wvSetGroup('A'|'B'|'C'|'ALL', this)`), nên 4 giá trị đó là domain hợp lệ
thật của tham số, không phải suy đoán.

**Điểm 2 — approved_by fallback 'admin' (sâu hơn báo cáo cũ mô tả):**
Route `/pass` (trước sửa) gọi `_t427_session_email(token)` rồi
`or 'admin'`:
```python
editor_email = _t427_session_email(token) or 'admin'
```
Nhưng đọc tiếp **chính hàm `_t427_session_email()` trong `core.py:5073-5087`**
(hàm dùng chung cho tab Place/Catalog qua `routes_places.py`) thì thấy hàm đó
**tự fallback 'admin' bên trong nó**: `return d.get('email') or 'admin'` khi
`valid=True` nhưng thiếu `email`, và `return 'admin'` ở nhánh except/invalid.
Hệ quả: `_t427_session_email()` **không bao giờ trả về rỗng/None** — luôn là
email thật hoặc chuỗi `'admin'`. Nếu chỉ sửa thành
`if not _t427_session_email(token): return 403`, điều kiện này **sẽ không bao
giờ đúng** (vô dụng), vì giá trị trả về luôn truthy. Đây là phát hiện thêm so
với mô tả gốc trong đề bài — ghi rõ ở đây vì nó thay đổi cách sửa đúng.

**Điểm 3 — Không kiểm person_id tồn tại (đã xác minh đúng như báo cáo mục 6):**
Route `/pass` (trước sửa) không có bước `SELECT ... FROM dila_catalog_contributors
WHERE person_id = ?` nào trước khi `UPDATE/INSERT name_vi_map` và
`UPDATE people SET name_vi = ... WHERE id = person_id` — với `person_id` giả
(không tồn tại ở cả 2 bảng), 2 lệnh `UPDATE` không lỗi, chỉ `rowcount=0`, và
route vẫn trả `200 {"ok": true, ...}` như ghi thành công, sai lệch với thực tế.

### 9.2. Cách sửa (`routes_namevi.py`)

- **Điểm 1** (trong `admin_work_verify_list`, dòng ~1244-1250): thêm kiểm
  `if group_filter != 'ALL' and group_filter not in group_map: return 400`
  **trước** khi map sang `group_filter_full`, trả
  `{"ok": false, "error": "Giá trị group không hợp lệ. Dùng: A, B, C, hoặc ALL."}`.
- **Điểm 2**: **không** tái dùng `_t427_session_email()` (vì hàm đó tự fallback
  'admin' nội bộ — sửa nó sẽ ảnh hưởng `routes_places.py`/`routes_misc.py`,
  vi phạm ràng buộc "không sửa tab Catalog/Place"). Thêm hàm riêng
  `_t486_session_email_strict(token)` (dòng ~1174-1192, cạnh các hàm `_t486_*`
  khác) — gọi lại đúng endpoint `/api/login/check` nhưng trả **`None`** khi
  không có email thật (`valid=False` hoặc thiếu `email`), không tự thay bằng
  `'admin'`. Route `/pass` dùng hàm mới này:
  ```python
  editor_email = _t486_session_email_strict(token)
  if not editor_email:
      return jsonify({'ok': False, 'error': 'Không xác định được người duyệt (session email). Vui lòng đăng nhập lại.'}), 403
  ```
- **Điểm 3**: thêm, ngay sau khi mở `conn` và **trước** mọi `UPDATE/INSERT`:
  ```python
  exists_row = conn.execute(
      "SELECT 1 FROM dila_catalog_contributors WHERE person_id = ? LIMIT 1", (person_id,)
  ).fetchone()
  if not exists_row:
      return jsonify({'ok': False, 'error': 'Không tìm thấy person_id trong dữ liệu.'}), 404
  ```
  Dùng `dila_catalog_contributors.person_id` (không dùng `people.id`) vì đây
  là domain thật của tab "Xác minh tác giả" (tất cả `person_id` trong GET đều
  lấy từ bảng này) — một `person_id` có thể chưa có dòng `people` tương ứng
  nhưng vẫn là contributor hợp lệ, nên kiểm theo `people` sẽ false-reject.

### 9.3. Thay đổi contract API (before/after)

**GET `/daoanh/api/admin/work-verify?group=...`**
- Trước: `group=X` (giá trị lạ) → `200 {"ok": true, "total": 794, ...}` (coi như `ALL`, im lặng sai).
- Sau: `group=X` → `400 {"ok": false, "error": "Giá trị group không hợp lệ. Dùng: A, B, C, hoặc ALL."}`. `group=A|B|C|ALL` (hoa/thường đều được, do `.upper()`) không đổi hành vi.

**POST `/daoanh/api/admin/work-verify/<person_id>/pass`**
- Trước: token hợp lệ nhưng không lấy được email thật → ghi `approved_by='admin'`, trả `200 {"ok": true, ...}` (không thể xảy ra trong test HTTP vì token test luôn sai, nhưng xác nhận bằng đọc code `core.py:5073-5087`).
- Sau: cùng tình huống → `403 {"ok": false, "error": "Không xác định được người duyệt (session email). Vui lòng đăng nhập lại."}`, không ghi DB.
- Trước: `person_id` không tồn tại + token hợp lệ → `200 {"ok": true, "person_id": "...", ...}` (ghi `name_vi_map`/`people` cho 1 `id` không tương ứng contributor nào thật, `rowcount=0` âm thầm).
- Sau: cùng tình huống → `404 {"ok": false, "error": "Không tìm thấy person_id trong dữ liệu."}`, không ghi DB (kiểm **trước** mọi `UPDATE/INSERT`).
- Nhánh 403 token sai/thiếu và 400 `name_vi` rỗng: không đổi.

### 9.4. Kết quả test thực tế (2026-10-29, sau khi restart `app.py` để nạp code mới)

| Case | Lệnh | HTTP | Body |
|---|---|---|---|
| `py_compile` | `python -m py_compile routes_namevi.py` | — | `OK_COMPILE` (chạy 2 lần, sau mỗi vòng sửa) |
| GET `group=X` | `curl "http://127.0.0.1:8080/daoanh/api/admin/work-verify?group=X"` | **400** | `{"ok":false,"error":"Giá trị group không hợp lệ. Dùng: A, B, C, hoặc ALL."}` |
| GET `group=ALL` | `curl ".../work-verify?group=ALL&page=1&size=1"` | 200 | `total=794` (không đổi so với trước sửa — không regression) |
| GET `group=A` | — | 200 | `total=149` |
| GET `group=C` | — | 200 | `total=618` |
| POST không token | `curl -X POST .../A000095/pass -d '{"name_vi":"Test"}'` | 403 | `{"ok":false,"error":"Unauthorized"}` |
| POST token rác | cùng trên + `-H "X-Session-Token: bogus"` | 403 | `{"ok":false,"error":"Unauthorized"}` |
| POST token rác + `person_id` giả (`ZZZ_NOT_EXIST`) | — | 403 | `{"ok":false,"error":"Unauthorized"}` — **chỉ test được nhánh 403** (xem giới hạn dưới) |
| Regression — `GET /daoanh/api/admin/namevi-queue` (tab khác, không đụng tới) | `curl ".../namevi-queue?page=1&size=1"` | 200 | Trả danh sách bình thường — không bị ảnh hưởng |
| DB read-only — kiểm logic 404 bằng Python trực tiếp (không qua route, không ghi) | `sqlite3.connect(...).execute("SELECT 1 FROM dila_catalog_contributors WHERE person_id=?...")` | — | `A000095` → `(1,)` (tồn tại); `ZZZ_NOT_EXIST` → `None` (không tồn tại) — xác nhận câu SQL dùng trong route phân biệt đúng 2 trường hợp |

Server (`app.py`, port 5000, qua `local_gateway.py` 8080) đã được **restart** để
nạp code mới (PID cũ `4216` → `35356`), có log khởi động sạch trong
`app_local_err.log`/`app_local.log`, không lỗi.

## 7. Limitation / blocker còn lại (ĐÃ CẬP NHẬT 2026-10-29 — xem mục 9 để biết phần nào đã sửa)

**Trạng thái 3 điểm rủi ro gốc:** cả 3 đã được sửa và kiểm chứng (mục 9.1-9.4).
Không còn là limitation — chuyển các mục dưới thành "còn lại sau vòng sửa thứ 2":

0. **Giới hạn test đã biết (không tránh được bằng HTTP thật):** không có token
   session hợp lệ trong môi trường build này, nên 2 case sau **chỉ xác nhận
   bằng đọc code, không test qua HTTP thật**:
   - Nhánh `403` "Không xác định được người duyệt" (điểm 2) — vì mọi request
     test đều bị chặn ở bước `verify_session(token)` (401/403 "Unauthorized")
     **trước khi** chạy tới `_t486_session_email_strict()`, nên không thể tạo
     tình huống "token hợp lệ nhưng thiếu email" từ bên ngoài.
   - Nhánh `404` "Không tìm thấy person_id" (điểm 3) — cùng lý do, token sai
     luôn trả `403` trước khi route chạy tới bước kiểm `person_id`.
   Đã xác nhận logic đúng bằng đọc code (mục 9.1-9.2) + kiểm câu SQL tồn tại
   bằng Python độc lập (mục 9.4, dòng cuối bảng) — không phải chạy qua route
   thật. Cần Admin đăng nhập thật (có token hợp lệ) để tự tạo 2 tình huống này
   qua UI/HTTP nếu muốn xác nhận thêm lần nữa trước khi Pass thật.
1. **Chưa thử luồng Pass thật (cần Admin đăng nhập).** Theo đúng chỉ đạo "KHÔNG bấm Pass thật trong lúc build", chỉ kiểm được: (a) GET trả đúng cấu trúc/dữ liệu, (b) POST từ chối đúng khi thiếu/sai `X-Session-Token`. **Chưa kiểm chứng**: POST với token hợp lệ có ghi đúng `name_vi_map` + `approved_by`=email thật + `people.name_vi` hay không, và UI có hiển thị lại đúng trạng thái "đã Pass" sau khi reload hay không. Cần Admin đăng nhập `admin/namevimap.html` thật và tự bấm Pass 1-2 dòng để coordinator/QA xác nhận.
2. **Cách phát hiện "đã Pass" (`passed` field) là suy luận, không phải cờ trạng thái thật:** so `people.name_vi` hiện tại với `name_db` đã đo trong CSV dry-run — khác đi thì coi là đã Pass. Rủi ro: nếu `people.name_vi` của người đó bị đổi bởi **nơi khác** (ví dụ tab ETL/Xác Minh cũ dùng chung `name_vi_map`) sau thời điểm đo CSV nhưng không phải qua tab này, dòng đó cũng hiện `passed=true` dù Admin chưa bấm Pass ở tab mới. Không có cột trạng thái riêng cho tab này (đúng ràng buộc "không tạo cột/bảng mới"), nên đây là giới hạn đã biết, không phải bug.
3. **`file_value` có thể khác nhau theo từng tác phẩm của cùng 1 người** (181/794 người có >1 dòng CSV, 45 trong số đó có biến thể tên khác nhau thật — ví dụ A034224: "Cống Cáp Hô Đồ Khắc Đồ" / "Cống Cáp"). UI chọn giá trị phổ biến nhất làm đề xuất chính, liệt kê các biến thể khác bên dưới — Admin cần tự xem và sửa tay nếu giá trị mặc định không đúng ngữ cảnh.
4. **Cache CSV theo mtime file**, không theo nội dung — nếu ai ghi lại CSV với nội dung khác nhưng giữ mtime (hiếm, chỉ xảy ra khi copy file thủ công giữ timestamp), server sẽ không tự đọc lại. Khởi động lại app.py (đã làm trong lượt build này để nạp code mới) sẽ luôn đọc CSV mới nhất.
5. **Danh sách `works` (tối đa 5) sắp theo `cbeta_id` (ORDER BY c.cbeta_id)**, không phải theo số quyển/năm — đủ cho mục đích "xem tác phẩm tiêu biểu để nhận diện người", không phải danh sách đầy đủ hoặc có ý nghĩa xếp hạng.

## 8. Cập nhật spec UI (sau phản hồi Admin, 2026-10-29)

Admin phản hồi 5 điểm cần sửa UI (phần khác của spec cũ giữ nguyên). Agent nhận
message qua coordinator (không giữ context agent cũ `a045a99312c0e3cdd` —
agent mới khởi động lại, đọc report này + code hiện tại trước khi sửa, đúng
hướng dẫn trong message bàn giao).

### Rà soát trước khi sửa (đã đúng sẵn, không cần đổi)

| Yêu cầu Admin | Trạng thái code hiện tại |
|---|---|
| 1. Tab ngay sau Catalog | Đã đúng: `admin/namevimap.html:220-221` — nút `#workverify-tab-btn` nằm ngay sau `#catalog-tab-btn`, panel `#tab-workverify` nằm ngay sau `<!-- /tab-catalog -->` (dòng 943/949). Không cần sửa. |
| 2. Bố cục bảng giống Catalog | Đã đúng: cùng dùng `class="etl-ba-table"`, `search-bar`, `#...-pagination`, nút `.etl-flag-pass` như tab Catalog (`admin/namevimap.html:921-941` vs `974-994`). 8 cột, không thêm cột lạ. Không cần sửa. |
| 5. POST trả 400 khi `name_vi` rỗng/whitespace, không ghi DB | Đã đúng từ build trước: `routes_namevi.py:1356-1366` — kiểm `verify_session(token)` (403 nếu sai) **trước**, sau đó `name_vi = (data.get('name_vi') or '').strip()`; nếu rỗng → `return jsonify({'ok': False, 'error': 'Tên Việt không được rỗng'}), 400` **trước mọi lệnh SQL** (không `conn = sqlite3.connect(...)` nào chạy trước dòng này). Không cần sửa. |

### Đã sửa thật (điểm 3 + 4)

**Vấn đề:** ô "Tên đề xuất" trong cột Pass tự điền `it.name_file` (`admin/namevimap.html:3069` bản cũ) — vi phạm yêu cầu mới "mặc định TRỐNG, không tự điền từ DB/file". Nút Pass luôn bấm được, chỉ chặn bằng `alert()` sau khi click (không `disabled` thật).

**Cách sửa (file `admin/namevimap.html`):**
- Dòng ~3069: `value="${_esc(it.name_file || '')}"` → `value=""`; thêm `placeholder="Nhập tên Việt…"` và `title="Đề xuất (file): ${_esc(it.name_file || '—')}"` (tooltip tham khảo, không ghi vào input). Thêm `oninput="wvToggleBtn(this)"` trên input và `disabled` mặc định trên nút Pass.
- Thêm hàm mới `wvToggleBtn(input)` (sau `wvLoad`, trước `wvPassPerson`): lấy `input.nextElementSibling` (chính là nút Pass, cách nhau 1 khoảng trắng — `nextElementSibling` bỏ qua text node) và set `btn.disabled = !input.value.trim()`.
- `wvPassPerson()`: giữ nguyên logic gửi `name = tr.querySelector('.wv-pass-input').value.trim()` (đã đúng — gửi giá trị Admin gõ, không fallback `name_file`/`name_db`); chỉ đổi text thông báo lỗi từ `'Tên Việt không được rỗng'` sang đúng câu mẫu đề bài: `'Vui lòng nhập tên trước khi Pass.'`. Đây là lưới an toàn thứ 2 (phòng trường hợp `disabled` bị bypass bằng DevTools), vì nút đã bị `disabled` ngay từ đầu nên nhánh này hiếm khi chạy qua UI thật.
- Cột "Tên hiện tại (DB)" (`name_db`) và "Tên đề xuất (file)" (`name_file` + `name_file_variants`) giữ nguyên là 2 cột text riêng (dòng 3073-3074) — đã đúng yêu cầu "chuyển sang hiển thị ở cột riêng chỉ để tham khảo" từ bản build trước, không cần tạo cột mới.

**Backup trước khi sửa:** `docs/sessions/2026-10-29/namevimap.html.before-t486-verify-ui-fix`, `docs/sessions/2026-10-29/routes_namevi.py.before-t486-verify-ui-fix` (routes_namevi.py không đổi dòng nào, backup chỉ để đủ bộ theo quy tắc "backup trước khi sửa" — xem mục trước, không có diff).

### Kiểm chứng

| Case | Lệnh/thao tác | Kết quả |
|---|---|---|
| `py_compile` | `python -m py_compile routes_namevi.py` | `OK_COMPILE` |
| `node --check` JS | Trích toàn bộ `<script>` không-src trong `namevimap.html` ra file tạm trong scratchpad, `node --check` | `JS_OK` |
| GET vẫn đúng cấu trúc | `curl http://127.0.0.1:8080/daoanh/api/admin/work-verify?group=ALL&page=1&size=3` (qua `local_gateway.py`, server đang chạy sẵn) | JSON `items` giữ đủ field `person_id/name_zh/name_db/name_file/name_file_variants/group/work_count/works/passed` như cũ — không đổi contract GET |
| Code review — nút Pass disable khi Name trống | Đọc `admin/namevimap.html:3069` (`disabled` mặc định trên `<button>`) + `3102-3105` (`wvToggleBtn`) | Xác nhận: input rỗng ban đầu ⇒ nút `disabled=true` ngay khi render; Admin gõ ký tự non-whitespace đầu tiên ⇒ `oninput` gọi `wvToggleBtn` ⇒ `btn.disabled=false`; xoá hết/chỉ còn khoảng trắng ⇒ `disabled=true` lại |
| Code review — POST 400 khi rỗng, không ghi DB | Đọc `routes_namevi.py:1356-1366` | Xác nhận thứ tự: (1) check token → 403 nếu sai, (2) `name_vi = (data.get('name_vi') or '').strip()`, (3) `if not name_vi: return ... 400` — dòng này nằm **trước** `conn = sqlite3.connect(SQLITE_DB)` (dòng 1368), nên không có kết nối DB/UPDATE/INSERT nào chạy khi `name_vi` rỗng |
| POST thực tế (không có token hợp lệ, theo đúng ràng buộc không test Pass thật) | `curl -X POST .../A001257/pass -d '{"name_vi":""}'` không header token; và `-d '{}'` | Cả 2 đều `403 {"ok":false,"error":"Unauthorized"}` — đúng, vì token check chạy trước (không test được nhánh 400 mà không có token hợp lệ, đúng giới hạn đề bài đã chấp nhận: "chỉ cần đọc code logic") |

Không chạy lệnh Pass thật (không có token hợp lệ, không bấm UI thật) — đúng ràng buộc "KHÔNG bấm Pass thật / không gọi POST thật trong lúc sửa".
