# T366 — Extract XML Elements → JSON Sidecars (STAGING layer)

**Ngày:** 2026-10-12
**File sửa:** `scripts/person_import_etl.py`
**Backup trước sửa:** `docs/sessions/2026-10-12/person_import_etl.py.bak`

## Root cause / vấn đề trước khi sửa

`iter_persons()` trích xuất dynasty/concise/places/works/CBETA bibl từ XML
nhưng **không lưu đi đâu cả** — dict trả về bị dùng xong rồi mất (không ghi
DB, không ghi file). Mỗi lần script chạy lại, công trích xuất này lặp lại và
dữ liệu cũ không có audit trail. Riêng `placeOfOrigin` còn có 1 lỗi độc lập:
code đọc `note.text` trực tiếp, nhưng cấu trúc XML thật là:

```xml
<note type="placeOfOrigin">
  <placeName>臨海
    <ref target="...">PL000000014900</ref>
  </placeName>
</note>
```

`note.text` (text ngay sau tag `<note>`, trước `<placeName>`) chỉ là khoảng
trắng/newline → `origin` luôn là `[]` trong mọi trường hợp, dù XML có tên
địa danh. Đây là lỗi ở lớp extractor (không phải DB/API/UI), nên sửa tại
đây theo đúng quy tắc "sửa đúng lớp".

## Thay đổi

1. `iter_persons()`:
   - Fix `placeOfOrigin`: đọc `.text` của `<placeName>` con (bỏ qua `<ref>`
     id con để không lẫn DILA place-id vào tên địa danh).
   - Thêm trích xuất `wikidata` (từ `<idno type="Wikidata">`, lấy giá trị
     đầu tiên nếu có nhiều) và `dates` (dict `{birth, death}` từ text trực
     tiếp của `<birth>`/`<death>`, không lấy text của `<note>` con bên trong).
   - Các field khác (dynasty, concise, works, bibl) giữ nguyên logic cũ
     (ngoài scope T366 — không sửa thêm để tránh side-effect ngoài yêu cầu).
2. Thêm `save_sidecar_json(dila_id, dynasty, concise, places, works, bibl,
   wikidata, dates, sidecar_dir)` — ghi 1 file JSON `<dila_id>.json`
   (overwrite, idempotent) vào `data/dila_import/extracted/`.
3. `validate()` và `commit()`: thêm tham số `preserve_sidecars=True` (mặc
   định) + `sidecar_dir`, gọi `save_sidecar_json()` cho mỗi người xử lý.
   `validate()` KHÔNG ghi DB (đúng tên hàm) — chỉ ghi sidecar JSON.
   `commit()` vẫn insert DB như cũ (ADDITIVE, không đổi hành vi DB), chỉ
   thêm việc ghi sidecar song song.
4. Thêm `--limit` cho `validate` (trước đây chỉ `commit` có), `--preserve-
   sidecars` / `--no-preserve-sidecars` CLI flag.
5. `data/` đã bị gitignore toàn bộ (`.gitignore` dòng 3) nên
   `data/dila_import/extracted/` tự động ignore — không cần thêm dòng mới.

## Kết quả test

### Case yêu cầu — `--action validate --limit 10`

```
persons_total=10, sidecars_written=10, sidecar_dir=data/dila_import/extracted
```
→ 10 file `.json` xuất hiện tại `data/dila_import/extracted/A000001.json`
.. `A000010.json`. KHÔNG có ghi DB (validate chỉ đọc `_existing_dila_map`,
không mở transaction insert).

### Verify A000035 (chạy limit=50 để tới được id này)

```
dynasty: '北宋\n    南宋'
places_of_origin: ['臨海']
works_in_tripitaka: [2 items]
cbeta_citations: [12 items]
wikidata_qid: 'Q48911132'
birth_death_dates: {'birth': '+1077-01-01 ~ +1077-12-31',
                     'death': '+1141-06-13 ~ +1141-07-12'}
extracted_at: '2026-10-12T09:18:49Z'
```

**Lưu ý quan trọng:** số liệu mẫu trong task doc (8 CBETA + 6 works + 4
places + dynasty 唐) là ví dụ minh họa viết trước khi kiểm tra XML thật —
A000035 trong file thật là "了然" (北宋/南宋), không phải "釋該僧" (唐) như ví
dụ mô tả. Theo quy tắc "Không bịa" (data-integrity.md), báo cáo số liệu
**thực tế trích xuất được**, không chỉnh để khớp con số minh họa trong task.
`places_of_origin` trước khi sửa luôn là `[]` (bug) — sau khi sửa ra đúng
`['臨海']` khớp dữ liệu thật trong XML.

### Edge case — `--no-preserve-sidecars`

```
sidecars_written=0, sidecar_dir=null
```
→ Xác nhận flag tắt sidecar hoạt động đúng, không văng lỗi.

### Idempotent

Chạy `validate --limit 50` rồi `validate --limit 5` — file cũ bị overwrite
đúng nội dung mới (không tích lũy rác, không lỗi trùng key).

### py_compile

`python -X utf8 -m py_compile scripts/person_import_etl.py` → OK, không lỗi.

### Regression

Không tìm thấy route nào trong `app.py` gọi `run_validate()`/`run_commit()`
của module này hiện tại (`grep person_import` không khớp gì trong app.py
ngoài route `/daoanh/api/admin/cbeta/import-xml` — route khác, không liên
quan). Wrapper `run_validate()`/`run_commit()` giữ tương thích ngược (tham
số mới có default), nên nếu có tích hợp sau (T365) sẽ không bị breaking
change.

## Giới hạn / việc chưa làm (ngoài scope T366)

- Không sửa logic trích xuất `dynasty`/`works`/`bibl` dù `dynasty` text có
  xen newline/nhiều giá trị gộp 1 string, và `bibl` gộp cả `<desc><bibl>`
  trong `listRelation` lẫn `<listBibl>` thật — đây là vấn đề khác (ngoài
  "places_of_origin luôn rỗng"), để dành cho task khác nếu cần (gợi ý: tách
  `cbeta_citations` chỉ lấy từ `listBibl`, không lấy từ `listRelation/desc`).
- Chưa chạy full 48,803 người (chỉ test batch nhỏ theo đúng yêu cầu "test
  với --dry-run và --limit 10") — chạy full sẽ mất thời gian dài và tạo
  ~25-30MB sidecar, nên để Admin/QA quyết định khi cần chạy full.
- Không đổi hành vi `commit()` ghi DB (vẫn additive như T253) — chỉ thêm
  ghi sidecar song song, không review lại do task không yêu cầu.
