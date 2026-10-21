# T429 — Giai đoạn 0: Environment Audit (khảo sát hiện trạng)

TASK: T429 · PHASE: 0 (environment-audit) · DATE: 2026-10-21 · STATUS: DONE (phạm vi GĐ0)

## 1. Mục tiêu

Phân biệt **code thật** với **chức năng chỉ có trong docs**, đo hiện trạng DB/schema liên quan
truyền thừa, làm cơ sở cho bản đồ tái sử dụng (reuse-map.md) trước khi viết bất kỳ parser nào.

## 2. Phương pháp

- Chỉ đọc. Truy vấn SQLite ở chế độ `file:...?mode=ro` (URI read-only, không ghi, không WAL checkpoint).
- Grep `app.py` để xác nhận bảng/VIEW được code gọi thật (không chỉ nhắc trong docs).
- Đọc task files T410, T414, T422–T426 (T422/T423 đã chuyển vào `tasks/archive_done/`).

## 3. Kết quả đo được (2026-10-21)

### 3.1 DB `data/lineage.db` (đọc read-only)

| Mục | Giá trị đo thật |
|---|---|
| Số bảng | 167 |
| `lineage_edge_assertions` | **35.243 rows** — DILA 23.014 · MARCUS 11.169 · TTL 1.060 |
| `relation_kind` trong bảng trên | **100% = 'unknown'** (35.243/35.243) — T414 chưa nạp nhãn |
| `entity_source_ids` | **183.769 rows** — DILA 167.006 (candidate) · MARCUS 11.297 · CBETA 4.409 · TTL_LOCAL 794 accepted + 260 candidate · ZQLOCAL 2 · BDRC 1 |
| `data_sources` | 15 rows; CBETA = `source_id=3`, `license_note="CC BY-SA 4.0"` (ghi chú chung cho cả bộ, **chưa phản ánh điều khoản riêng của X-series**) |
| VIEW T425 | `v_tree_dila`, `v_tree_marcus`, `v_tree_ttl`, `v_tree_overlay` — **tồn tại thật** trong sqlite_master |

### 3.2 Code thật (grep `app.py`)

| Thành phần | Bằng chứng code thật |
|---|---|
| `lineage_edge_assertions` | app.py dòng ~6165–6231 (API đối chiếu nguồn), ~21407–21428 (`/dila-axis`), ~24908–25026 (introspection T130) — **đang chạy production** |
| `entity_source_ids` | app.py ~2448–2704 (luồng ZENLINEAGE approve/reject), ~18075–18117 (entity unified) — **đang chạy production** |
| X86n1601 trong app.py | **1 lần duy nhất**, trong prompt dịch `birth_death_quote` (giữ mã CBETA khi dịch) — KHÔNG có tính năng phả hệ nào cho nguồn này |

### 3.3 Trạng thái chuỗi task liên quan (đọc task files)

| Task | Status thật | Nội dung đã xảy ra |
|---|---|---|
| T422 | done (archive) | `tasks/archive_done/T422-dila-edge-dedupe-unique.md` |
| T423 | done (archive) | Đăng ký `TTL_LOCAL` + 204 `ptda:` entities + 1.054 `entity_source_ids` |
| T424 | in_progress | 1.060 cạnh TTL đã nạp; còn 2 rủi ro: `edge_key` 16 cạnh BUG-038 chưa khớp subject mới + crosswalk slug `lam_te_nghia_huyen` chưa sửa |
| T425 | in_progress | 3 cột additive + 4 VIEW đã tạo; nhưng `relation_kind` toàn 'unknown', nhãn `tham_hoc` vs `khac` chưa thống nhất, so sánh overlay/consensus chưa liệt kê chi tiết |
| T426 | pending | API/UI chọn 4 cây chưa làm |
| T410 | in_progress | Quy tắc màu theo nguồn đã code; **nguồn mới chưa duyệt phụ thuộc không được tính vào "≥ 2 nguồn khớp"** |
| T414 | pending | Từ vựng `noi_phap / khac / unknown` — chưa nạp; có mâu thuẫn đặt tên với T425 (`tham_hoc`) |

### 3.4 Workstream X86n1601 có sẵn (khác T429)

- `docs/reports/x86n1601-delivery-qa-20261020/` — QA độc lập gói dataset "Cloud v0.1" (9 claim pilot):
  XSD PASS nhưng **test phủ định FAIL** (câu giả lập không truyền pháp vẫn sinh cạnh), evidence rỗng,
  extractor chưa tin cậy được. v0.2 chờ Cloud sửa.
- **T429 vùng `research/thiendang-thepho/` tách rời workstream này.** Không dùng artifact v0.1 làm
  chứng cứ; QA report chỉ dùng làm cảnh báo kinh nghiệm (extractor phải tách loại quan hệ + chiều).

### 3.5 Môi trường chạy

| Mục | Giá trị |
|---|---|
| Python | 3.14.3 |
| lxml | 6.0.2 (đủ parse TEI P5) |
| sqlite3 | 3.50.4 |
| Nguồn CBETA local | `data/cbeta/xml-p5-full/X/X86/X86n1601.xml` — 803.957 byte, mtime 2026-09-27T19:34:02+07:00 (không cần tải internet) |
| Script CBETA có sẵn | `audit_cbeta_corpus.py`, `build_cbeta_mentions.py`, `cbeta_build_text_passages.py`, `t424_load_ttl_edges.py`… (mẫu tham khảo, không sửa) |

## 4. Kết luận GĐ0

- Hạ tầng đích tích hợp (`lineage_edge_assertions` + `entity_source_ids` + chuỗi T422–T426) **tồn tại thật ở mức code**, nhưng đang `in_progress`/có nợ (T424 edge_key, T425 nhãn) — dataset mới phải thiết kế để nạp được mà không phụ thuộc việc các nợ đó xong trước.
- Không có code nào cho X86n1601 ngoài 1 prompt dịch — không có gì "thật" phải né tránh, cũng không có parser tái sử dụng trực tiếp cho cấu trúc sơ đồ list/item.
- DB đang bị process khác mở (Get-FileHash bị chặn, python open được) — mọi thao tác sau này phải read-only hoặc chờ Admin.

## 5. Kiểm không tác động production

Toàn bộ phép đo ở chế độ read-only URI; không có INSERT/UPDATE/DDL; không restart server; không đụng file production.
