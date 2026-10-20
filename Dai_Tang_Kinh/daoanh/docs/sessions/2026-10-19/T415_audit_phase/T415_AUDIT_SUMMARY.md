# T415 — Audit `vn_person_authority` crosswalk (slug ↔ dila_id) — CHỈ ĐỌC

**Ngày**: 2026-10-19
**DB**: `daoanh/data/lineage.db` (mở read-only qua `sqlite3.connect('file:...?mode=ro', uri=True)`)
**Trạng thái**: Audit xong (bước 1-4 của task). **CHƯA sửa DB, chờ Admin duyệt bước 5-6.**

Xác nhận rõ: **không có UPDATE/DELETE/INSERT nào chạy trên `daoanh/data/lineage.db`** trong
suốt phiên audit này. Mọi query là SELECT/PRAGMA; `classify_ttl_edges()` của
`scripts/t381_etl_ttl_into_consensus.py` được import và gọi lại nguyên bản (không sửa file đó),
chạy với connection read-only.

## Schema xác nhận thật (không đoán)

```
PRAGMA table_info(vn_person_authority):
  id TEXT PRIMARY KEY   -- đây là "slug" (vd. 'dien_phuc_tue_thang')
  dila_id TEXT          -- không có UNIQUE constraint -> N:1 có thể xảy ra
  ...
PRAGMA table_info(dharma_lineage_ttl_vn):
  teacher_id TEXT, student_id TEXT  -- dạng 'ex:monk/<slug>'
```
`vn_person_authority` chỉ có 1 index: `sqlite_autoindex_vn_person_authority_1` (PK trên `id`).
→ **1:N (1 slug → nhiều dila_id) về cấu trúc KHÔNG THỂ xảy ra** vì `id` là PRIMARY KEY (mỗi
slug chỉ có đúng 1 dòng, đúng 1 dila_id). Đã verify bằng `GROUP BY id HAVING COUNT(*)>1` → 0 dòng.

## 1. N:1 (nhiều slug → 1 dila_id)

**36 case** tìm được (`GROUP BY dila_id HAVING COUNT(*)>1` trên 1511 dòng có dila_id không rỗng).
File: `n1_slug_to_dilaid.tsv`. Lớn nhất: `A010511` (3 slug), `A021395` (3 slug, trong đó có 1 slug
đáng chú ý `alias_A021395` — có vẻ là placeholder/alias tự sinh, không phải slug TTL thật, cần
Admin xem riêng), `A026824` (3 slug). Phần lớn còn lại là cặp 2 slug.

## 2. 1:N (1 slug → nhiều dila_id)

**0 case** — không thể xảy ra vì `id` là PRIMARY KEY của `vn_person_authority` (xác nhận bằng
query, không chỉ bằng lý luận schema). File `1n_slug_multiple_dilaid.tsv` vẫn được tạo, chỉ có
header, đúng yêu cầu task.

## 3. 229 slug TTL thiếu dila_id — đối chiếu với T381_EXECUTION_LOG.md

Số liệu T381 Bước 1 ghi: 101 mismatch teacher + 128 mismatch student = 229 (tính theo **dòng
cạnh TTL**, không phải slug duy nhất) + 2 "empty teacher slug" (`ex:monk/` không có slug, khai tổ
không thầy) riêng biệt, không tính vào 229.

Audit này **import và chạy lại chính hàm `classify_ttl_edges()`** của script T381 (không viết
lại logic bằng tay, tránh sai khác cách strip prefix/thứ tự check) trên DB hiện tại (read-only):

| Hạng mục | Số đo lại hôm nay | Số T381 log |
|---|---|---|
| TTL edges tổng | 784 | 784 |
| Matched cả 2 đầu | 553 | 553 |
| Mismatch teacher (dòng cạnh) | 101 | 101 |
| Mismatch student (dòng cạnh) | 128 | 128 |
| Empty teacher slug | 2 | 2 |
| Tổng | 784 | 784 |

**Khớp 100% với T381** — xác nhận dữ liệu `vn_person_authority`/`dharma_lineage_ttl_vn` không
đổi từ lúc đó đến nay, và không có sai khác cần báo.

Quy đổi sang **slug duy nhất** (để Admin dễ rà từng trường hợp — file `229_orphan_ttl_slugs.tsv`,
159 dòng kể cả header):
- 56 slug teacher duy nhất (trải trên 101 dòng cạnh — một số slug lặp lại ở nhiều cạnh)
- 128 slug student duy nhất (128 dòng cạnh — không trùng nhau trong nhóm mismatch_student)
- Hợp nhất (loại trùng teacher ∩ student): **158 slug duy nhất**

Mỗi dòng trong `229_orphan_ttl_slugs.tsv` ghi rõ lý do: slug không tồn tại trong
`vn_person_authority`, hay tồn tại nhưng `dila_id` rỗng/NULL, và số cạnh TTL bị ảnh hưởng
(teacher_edges/student_edges).

## 4. Xác minh 6 dòng đã xóa ở T381 QA round 2 — PHÁT HIỆN QUAN TRỌNG

Task giả định cả 6 lỗi đều do N:1 crosswalk. **Audit thực tế cho thấy chỉ 2/6 là do N:1**, còn
4/6 có nguyên nhân khác — cần Admin biết trước khi duyệt sửa:

| dila_id (cũ, đã xóa khỏi consensus) | Số slug hiện map vào trong `vn_person_authority` | Nguyên nhân thật |
|---|---|---|
| **A000108** | 2 (`bao_ninh_nhan_dung`, `nguyet_chuong_tri_uyen`) | **N:1 thật** — TTL row `bao_ninh_nhan_dung → nguyet_chuong_tri_uyen` (2 slug khác nhau), cả 2 cùng crosswalk ra A000108 |
| **A014491** | 2 (`long_khanh_khanh_nhan`, `an_hoa_van_nhat`) | **N:1 thật** — TTL row `long_khanh_khanh_nhan → an_hoa_van_nhat`, cả 2 cùng crosswalk ra A014491 |
| **A008431** | 1 (`dien_phuc_tue_thang`) | **KHÔNG phải N:1.** Dòng TTL gốc (`dharma_lineage_ttl_vn.id=525`, nguồn `TS-Dien-Phuc-Tue-Thang.ttl`) có `teacher_id = student_id = 'ex:monk/dien_phuc_tue_thang'` — tự tham chiếu ngay trong **raw TTL**, không liên quan vn_person_authority |
| **A026988** | 1 (`dinh_lam_canh_phuong`) | **KHÔNG phải N:1.** Tương tự: TTL row id=540 (`TS-Dinh-Lam-Canh-Phuong.ttl`) tự tham chiếu |
| **A010985** | 1 (`dong_son_trach_ngon`) | **KHÔNG phải N:1.** TTL row id=577 (`TS-Dong-Son-Trach-Ngon.ttl`) tự tham chiếu |
| **A003868 ↔ A010427** (cạnh đảo chiều) | 1 mỗi id | **KHÔNG phải N:1.** 2 dòng TTL riêng biệt và hợp lệ: id=586 (`duc_son_tuyen_giam→long_dam_sung_tin`) và id=583 (`long_dam_sung_tin→duc_son_tuyen_giam`) — raw TTL có cả 2 chiều giữa cùng 2 người, tạo vòng 2 nút khi insert vào consensus. Mỗi slug chỉ map đúng 1 dila_id (không N:1) |

**Kết luận root cause**:
- **2/6 lỗi** (A000108, A014491) đúng là do `vn_person_authority` N:1 (2 slug TTL khác nhau trỏ
  cùng 1 dila_id) — thuộc đúng phạm vi sửa của T415.
- **3/6 lỗi** (A008431, A026988, A010985) là do **raw `dharma_lineage_ttl_vn` tự chứa dòng cạnh
  tự tham chiếu** (teacher_id = student_id trong cùng 1 dòng TTL) — đây là lỗi ở nguồn TTL hoặc
  ở bước import TTL ban đầu, KHÔNG sửa được bằng cách đổi `dila_id` trong `vn_person_authority`.
  Sửa đúng lớp sẽ là lọc/validate tại ETL (loại edge có teacher_id=student_id trước khi insert),
  không phải sửa crosswalk.
- **1/6 lỗi** (cặp A003868/A010427) là do raw TTL có 2 cạnh ngược hướng giữa đúng 2 người thật
  (không phải lỗi identity/crosswalk) — cần Admin quyết định cạnh nào đúng hướng, dữ liệu gốc
  TTL có thể có cả 2 vì 2 nguồn `.ttl` khác nhau ghi ngược nhau.

Việc này **không nằm trong scope sửa `vn_person_authority`** của T415 mục (4) — nên tách riêng
(task mới, không chữa bằng cách đổi dila_id) nếu Admin muốn xử lý 4/6 case này.

## Tổng số liệu

- N:1: **36 case** (file `n1_slug_to_dilaid.tsv`)
- 1:N: **0 case** (file `1n_slug_multiple_dilaid.tsv`, chỉ có header)
- Orphan slug (đo lại, khớp T381): **229 dòng cạnh TTL** (101 teacher + 128 student), tương ứng
  **158 slug duy nhất** (file `229_orphan_ttl_slugs.tsv`)
- 6 case self-loop/reversed T381: **2/6 do N:1 thật**, **4/6 do nguyên nhân khác** (raw TTL tự
  tham chiếu hoặc cạnh ngược hướng) — không sửa bằng đổi dila_id trong vn_person_authority

## File output

- `daoanh/docs/sessions/2026-10-19/T415_audit_phase/n1_slug_to_dilaid.tsv`
- `daoanh/docs/sessions/2026-10-19/T415_audit_phase/1n_slug_multiple_dilaid.tsv`
- `daoanh/docs/sessions/2026-10-19/T415_audit_phase/229_orphan_ttl_slugs.tsv`
- `daoanh/docs/sessions/2026-10-19/T415_audit_phase/T415_AUDIT_SUMMARY.md` (file này)

## Xác nhận an toàn

**CHƯA sửa DB, chờ Admin duyệt bước 5-6.** Toàn bộ phiên làm việc chỉ chạy `SELECT`/`PRAGMA
table_info`/`PRAGMA quick_check` (không gọi quick_check vì không cần, không đổi DB) qua
connection mở `mode=ro`. Không có `UPDATE`/`DELETE`/`INSERT` nào được thực thi trên
`daoanh/data/lineage.db`. Không sửa `scripts/t381_etl_ttl_into_consensus.py` (chỉ import và gọi
hàm `classify_ttl_edges()` để đối chiếu, file gốc không đổi).

## Attribution

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
