# T429 — Giai đoạn 0: Reuse Map (bản đồ tái sử dụng)

TASK: T429 · PHASE: 0 (reuse-map) · DATE: 2026-10-21 · STATUS: DONE (phạm vi GĐ0)

## Nguyên tắc

Tái sử dụng hạ tầng có thật trước khi viết mới. Vùng nghiên cứu dùng JSONL/JSON riêng
(cách ly), nhưng **schema phải ánh xạ được** sang bảng production để Giai đoạn 3 không dựng "hệ thứ hai".

## Bảng tái sử dụng

| Thành phần có sẵn | Trạng thái thật (đo 2026-10-21) | T429 tái sử dụng thế nào |
|---|---|---|
| `lineage_edge_assertions` (35.243 rows; cột additive `relation_kind`, `source_edge_ref`, `mapping_ok`) | Code thật, đang chạy (app.py `/dila-axis`, đối chiếu nguồn, T130) | Đích nạp về sau: `relation_claim` → `lineage_edge_assertions(source_code='CBETA_X1601', relation_kind, source_edge_ref=item/@xml:id)` — đúng bảng ánh xạ plan §7 |
| `entity_source_ids` (183.769 rows; `match_status` candidate/accepted, UNIQUE(source, source_entity_id)) | Code thật (ZENLINEAGE approve, entity unified) | Đích mapping danh tính: `identity_mapping` → `entity_source_ids(source='CBETA_X1601', match_status)` |
| `data_sources` (15 rows) | Code thật | Khi Admin duyệt tích hợp: thêm 1 dòng `source_code='CBETA_X1601'` (hoặc dùng CBETA hiện có + ghi chú per-text) — quyết định ở GĐ3+, không làm trong GĐ0–2 |
| VIEW `v_tree_dila/marcus/ttl/overlay` (T425) | Tồn tại thật trong sqlite_master | Overlay tự tính từ bảng cạnh ⇒ thêm nguồn mới **không cần đổi schema** — xác nhận thiết kế "chỉ nạp dữ liệu" là đủ |
| Chuỗi T422→T426 | T422/T423 done; T424/T425 in_progress; T426 pending | Quy trình nạp nguồn mới (đăng ký nguồn → crosswalk → cạnh → VIEW → UI) là mẫu quy trình cho giai đoạn tích hợp sau |
| T410 (quy tắc màu theo nguồn) | in_progress, màu đã code | Ràng buộc: cạnh từ 禪燈世譜 **không được tính vào "≥ 2 nguồn khớp"** cho tới khi `source-dependency-notes.md` được Admin duyệt (nguồn cùng gốc 傳燈錄/五燈會元 với DILA/Marcus) |
| T414 (từ vựng quan hệ) | pending; nhãn `noi_phap/khac/unknown` (T425 QA còn thấy `tham_hoc` chưa thống nhất) | Dataset dùng **cùng bộ từ vựng**; mặc định `dharma_successor` theo tiêu đề sơ đồ 法派世系圖; loại khác chỉ ghi khi tiểu sử làm chứng |
| Script CBETA có sẵn (`audit_cbeta_corpus.py`, `cbeta_build_text_passages.py`, `t424_load_ttl_edges.py`…) | Có thật trong `scripts/` | Tham khảo mẫu (idempotent, --dry-run/--apply/--revert, backup); không sửa file nào |
| QA workstream Cloud v0.1 (`docs/reports/x86n1601-delivery-qa-20261020/`) | Báo cáo thật, test phủ định FAIL | **Bài học bắt buộc**: extractor phải tách chứng minh loại quan hệ + chiều; đồng xuất hiện tên ≠ truyền pháp; evidence phải có locator/span xuất ra file, không giữ trong bộ nhớ |

## Không tái sử dụng / không đụng tới

| Thành phần | Lý do |
|---|---|
| `dharma_lineage_unified`, `lineage_edge_consensus` | Bảng gộp cũ — T425 đã chốt không dùng làm nguồn |
| `source_staging` (ZENLINEAGE) | Riêng cho nguồn Zen Lineage, không chung |
| Parser Cloud v0.1 | Chưa tin cậy (QA FAIL test phủ định); T429 tự xây parser riêng ở GĐ5 trên quy tắc R01–R07 đã chứng minh |
| DILA ID có sẵn | Không tự gán; mapping là GĐ6, chỉ candidate |

## Khoảng trống phải làm mới (GĐ3+)

1. Schema 7 đối tượng dataset (kèm bảng ánh xạ trường sang 2 bảng trên) — GĐ3.
2. Parser list/item lồng nhau theo R01–R07 — GĐ5 (chưa ai viết cho cấu trúc sơ đồ này).
3. `source-dependency-notes.md` (độc lập nguồn) — GĐ7, cần Admin duyệt.
