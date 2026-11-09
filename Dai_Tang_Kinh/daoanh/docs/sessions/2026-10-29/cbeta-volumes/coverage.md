# T500 — Đo coverage CBETA Catalog API (chỉ đọc)

- Ngày: 2026-10-29
- Task: `tasks/T500-cbeta-catalog-volume-relations.md`
- Phạm vi: chỉ đọc. Không ghi DB, không ghi `data/`. Chưa snapshot, chưa qua cổng license.

## Nguồn API đã xác minh

- Endpoint đang hoạt động: `https://cbdata.dila.edu.tw/stable/catalog_entry`
- Endpoint `http://cbdata.dila.edu.tw/v1.2/catalog_entry` trong issue cũ (2020) hiện trả 404.
- Python không xác thực được chứng chỉ của cbdata (lỗi OpenSSL strict), nên việc gọi API dùng curl.
- Duyệt cây theo BFS từ gốc `catalog_entry` (không có `q`), mỗi node gọi `?q=<n>` để lấy con.

## Kết quả

| Chỉ số | Giá trị |
|---|---|
| Dòng trong `dila_catalog_works` | 5.747 |
| `cbeta_id` phân biệt | 5.747 |
| `cbeta_id` NULL | 0 |
| Node tổng từ API | 13.710 |
| Lỗi khi gọi API | 0 |
| Work có node tác phẩm (`node_type = work`, có trường `work`) | **4.899** |
| Work không có node tác phẩm | **848** (847 không có node nào, 1 chỉ có node alt tương đương) |

**Hiệu chỉnh (2026-10-29):** bản đầu đếm theo nhãn đầu node và đếm nhầm 2 work. Con số đúng là đếm theo trường `work` ở trên. Chi tiết và số quyển xem `etl_dryrun_report.md`.

Phân loại `node_type` trong API: `work` 11.209, `html` 606, `alt` 902, `null` 993.

## Cách khớp

- Lấy mã đầu của `label` node, ví dụ `T0220 大般若波羅蜜多經 (1~200卷)` → `T0220`.
- Regex: `^([A-Za-z]{1,3}\d{3,4}[A-Za-z]?)(?![A-Za-z0-9])`. Bản đầu thiếu hậu tố chữ hoa (ví dụ `T0150A`) làm 197 work báo sai là không có node. Đã sửa và đo lại từ bản thô, không gọi API lần nữa.
- Work có node tác phẩm = có node có trường `work` bằng cbeta_id (mọi node như vậy đều có `node_type = work`).
  Node `alt` không có trường `work`, nên không tính vào 4.899.

## Giới hạn cần biết

- 606 node `html` có thể là trang văn bản chứ không phải tác phẩm. Chưa tách riêng nên "node thường" có thể gồm cả khớp `html`. Cần kiểm trước khi đếm quyển.
- Đo coverage chỉ kiểm có node hay không. Chưa đối chiếu `juan_start`/`juan_end` với `dila_catalog_works.juans`.
- Một cbeta_id có thể có nhiều node (ví dụ `T0150` và `T0150A`). Báo cáo này chỉ đếm theo cbeta_id.

## Bằng chứng

- Bản thô phản hồi API: `C:\Users\NAMTHI~1\AppData\Local\Temp\claude\E--Backup-2025-QuaiTieuTu-Anan-Son-phatphaponline-gradio-truyenthua-visjs-app-Dai-Tang-Kinh\f6f5afde-6481-4575-8bbd-4ca594d05ab8\scratchpad\t500_catalog_raw.json` (sẽ chuyển thành snapshot ở bước 2 sau khi có duyệt)
- Script đo: `...\scratchpad\t500_coverage.py`
- Tóm tắt JSON: `...\scratchpad\t500_coverage_summary.json`

## Bước tiếp theo (cần Admin)

1. Duyệt snapshot vào `data/dila_import/cbeta_catalog_api/2026-10-29/` kèm SHA256SUMS.
2. Qua cổng license (`license-gate.md`).
3. Duyệt schema ba bảng trong mục 3 của `tasks/T500`.
