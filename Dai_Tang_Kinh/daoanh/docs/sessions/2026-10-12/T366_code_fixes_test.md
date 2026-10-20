# T366 Code Fixes — Test Report

File sửa: `scripts/person_import_etl.py`
Backup trước sửa: `docs/sessions/2026-10-12/person_import_etl.py.bak-before-T366-fixes`

## Phạm vi

Chỉ sửa code theo 5 bug + 2 bonus từ daoanh-qa. KHÔNG re-run full validation,
KHÔNG generate sidecar mới cho 48k person (như yêu cầu). Thư mục thật
`data/dila_import/extracted/` vẫn giữ 100 file cũ (chưa clean, chưa động) —
admin/daoanh-qa tự quyết định khi nào chạy `--clean-extracted` thật.

## Đối chiếu XML gốc (A000035)

Đọc trực tiếp block `<person xml:id="A000035">` trong
`Buddhist_Studies_Person_Authority.xml` để xác nhận đúng cấu trúc trước khi sửa
(không đoán field path).

## 5 Fix chính

### 1. cbeta_citations lẫn nguồn — FIXED
Trước: `el.iter(BIBL)` quét mọi `<bibl>` trong `<person>`, gồm cả
`listRelation/.../desc/bibl` (quan hệ thầy-trò, 6 bibl) lẫn
`listBibl/bibl` (CBETA citation thật, 8 bibl, 2 trong đó có `<ref>` con).
Sau: chỉ `el.find(listBibl).findall(bibl)`, dùng `itertext()` để lấy cả text
trong `<ref>`.
Test A000035: `cbeta_citations` = 8 mục, không còn chuỗi "望月‧卷六‧附錄" nào,
2 mục `g089p0284(...)` / `g009p0074(...)` trước đây bị mất nay có đủ.

### 2. concise_bio bị cắt — FIXED
Trước: `n.text` (chỉ text trực tiếp, mất phần trong `<ref>` + tail).
Sau: `''.join(n.itertext())`.
Test A000035: chuỗi đầy đủ đến hết
`"...（http://baike.baidu.com/view/550618.htm，2012.07.24）"` — không còn bị
cắt ở `…等。（`.

### 3. works/activeAt — FIXED
Trước: `works` giữ nguyên blob nhiều dòng (1 string/note, không tách).
`activeAt` không được trích xuất.
Sau: tách theo dòng (`worksInTripitaka`, `worksBy`) gộp vào `works_in_tripitaka`;
`activeAt` tách theo dấu `；` (ideographic semicolon — phân cách thật trong
XML) + `\n`, ghi vào field mới `active_at_places`.
Test A000035: `active_at_places` = 4 mục
(`東掖白蓮`, `東掖虎溪`, `蕭山`, `臨安府不空教院`) — khớp đúng "4 places" trong
yêu cầu.

**Lệch so với "6 works" nêu trong yêu cầu gốc:** sau khi đối chiếu XML thật,
`worksInTripitaka` có 4 dòng (大乘止觀法門宗圓記(X0904) …) và `worksBy` có 6
dòng — tổng `works_in_tripitaka` sau khi tách đúng = **10 mục** (4+6), không
phải 6. Quyết định giữ cả 2 loại note trong field `works_in_tripitaka` (thay
vì chỉ lấy `worksBy`) vì cả hai đều là dữ liệu tác phẩm thật từ DILA, bỏ
`worksInTripitaka` sẽ mất dữ liệu catalog X-number không có lý do rõ ràng.
Nếu daoanh-qa cần đúng 6 (chỉ `worksBy`), cần xác nhận lại ý định — có thể
sửa 1 dòng (`t in ('worksInTripitaka','worksBy')` → `t == 'worksBy'`) để tách
riêng 2 field nếu được yêu cầu.

### 4. dynasty nên là list — FIXED
Trước: nối bằng `\n` thành 1 string.
Sau: `dynasty.split('\n')` → list, strip từng phần tử rỗng.
Test A000035: `dynasty` = `["北宋", "南宋"]`.

### 5. validate() mutate state mặc định — FIXED
`validate(..., preserve_sidecars=False)` (đổi từ `True`). Áp dụng luôn cho
wrapper `run_validate()` và CLI (`--preserve-sidecars`/`--no-preserve-sidecars`
giờ mặc định `None` → validate dùng `False`, commit dùng `True`, giữ hành vi
ghi sidecar mặc định khi commit thật — vì commit là ghi DB thật, cần audit
trail; validate là dry-run, không được tự ý ghi 49k file).

## 2 Bonus fix

### 6. xml_sha256 trong sidecar — ADDED
`save_sidecar_json()` nhận thêm `xml_sha256` param, ghi vào mọi sidecar mới.
Test A000035: `"xml_sha256": "b3d3e8b07beeb5bd4b4a12826d8bb29bb3e360e721d18a901ea0a9206d956a53"`.

### 7. --clean-extracted CLI flag — ADDED
Thêm `--clean-extracted` (xoá *.json trong `--sidecar-dir` trước khi chạy) +
`--sidecar-dir` tùy chỉnh (test không đụng thư mục thật). Test: tạo 100 file
trong thư mục test, chạy `--clean-extracted` → còn 0 file trước khi ghi lượt
mới.

## Kết quả test

1. `validate --limit 50` (mặc định, không cờ) → `sidecars_written: 0`,
   0 file tạo trong `--sidecar-dir` test. (Fix #5 xác nhận: đọc-only thật.)
2. `validate --preserve-sidecars --limit 100` (thư mục test riêng, KHÔNG
   phải `data/dila_import/extracted/` thật) → 100 sidecar tạo, A000035.json
   đúng như mô tả ở trên cho tất cả field (trừ lệch "6 works" đã giải thích).
3. `validate --no-preserve-sidecars --limit 10` → `sidecars_written: 0`
   (tường minh, tương đương mặc định).
4. `--clean-extracted` trên thư mục có 100 file test → xoá hết, còn 0 file.
5. `python -m py_compile scripts/person_import_etl.py` → OK, không lỗi
   syntax.
6. `pytest tests/test_t253_person_import.py` → **4 passed**, không
   regression (test cũ không set `sidecar_dir`/`preserve_sidecars` nên giờ
   mặc định không ghi sidecar — an toàn, không đụng fixture).
7. Thư mục thật `data/dila_import/extracted/` — xác nhận KHÔNG bị động tới
   trong toàn bộ quá trình test (vẫn 100 file cũ, đúng phạm vi "không re-run
   full validation").

## Giới hạn / cần xác nhận thêm

- Mục #3 (works_in_tripitaka = 10 thay vì 6 theo mô tả gốc) — cần daoanh-qa
  xác nhận ý định: giữ gộp cả 2 loại note (hiện tại, đầy đủ hơn) hay tách
  riêng để `works_in_tripitaka` chỉ còn đúng `worksBy` (6).
- Chưa chạy `--clean-extracted` trên thư mục `data/dila_import/extracted/`
  thật (100 file mixed) — theo đúng phạm vi yêu cầu "không re-run full
  validation/generate sidecar mới", việc dọn thư mục thật + chạy lại full
  48k để daoanh-qa tự quyết định bước tiếp theo.
