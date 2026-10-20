# DB hiện tại có đáp ứng "3 cây (DILA / Marcus / TTL) + chồng cây" chưa? (2026-10-19)

**Đo:** RC, chỉ đọc `data/lineage.db`. **Căn cứ:** đặc tả Admin 2026-10-19 + bản đánh giá
`DILA-CANONICAL-MULTI-TREE-REVIEW-2026-10-19.md`.

## Kết luận nhanh

| Cây | Sẵn sàng? | Lý do (số đo) |
|---|---|---|
| **DILA** | **Gần sẵn** | `lineage_edge_assertions` source DILA: 23.014 cặp thầy–trò, nhưng lưu **46.006 dòng (mỗi cặp 2 lần)**. Hai đầu cạnh là DILA ID. |
| **Marcus** | **Sẵn** | 11.169 cạnh. **Marcus dùng chính DILA ID** (`marcus_people_link` 18.121 dòng, đều `exact_id`); 11.166/11.169 cạnh có cả 2 đầu trong `people`. |
| **TTL** | **CHƯA** | Cạnh TTL nằm riêng ở `dharma_lineage_ttl_vn` (784 cạnh, ID dạng `ex:monk/<slug>`), không có trong bảng cạnh chung. Chỉ 553/784 cạnh map được 2 đầu sang DILA. 204/1.054 thiền sư TTL không có DILA ID. TTL **chưa được đăng ký** trong `data_sources` và **không có** trong lớp định danh `entity_source_ids`. |
| **Chồng cây** | **Chưa đúng mô hình** | Đang có bảng gộp `lineage_edge_consensus` (23.411 dòng) lưu sẵn cờ dila/marcus/ttl. Đây là dữ liệu dẫn xuất được cập nhật tay, dễ lệch với nguồn. Ví dụ BUG-038: cạnh TTL sai vẫn được tô xanh. |

**Tin tốt:** dự án đã có sẵn **lớp định danh** đúng ý tưởng:
- `entity_hub`: 48.673 PERSON.
- `entity_source_ids`: `(entity_id, source, source_entity_id, match_status, confidence, verified)`; DILA 167.006 dòng, MARCUS 11.297 dòng.

Không cần tạo bảng `persons` mới; chỉ cần dùng đúng và bổ sung TTL vào lớp này.

## Bảng hiện có, vai trò đề xuất

| Bảng | Hiện trạng | Vai trò trong mô hình mới |
|---|---|---|
| `entity_hub` (PERSON) | 48.673 người, toàn DILA | **Nút người duy nhất.** Thêm người không có DILA với `canonical_label = 'ptda:<slug>'` |
| `entity_source_ids` | DILA, MARCUS (đều `candidate`, `verified = 0`) | **Bảng mapping nguồn → người.** Thêm TTL; dùng `match_status` candidate / accepted / rejected |
| `lineage_edge_assertions` | DILA (trùng ×2) + MARCUS; chưa có TTL; chưa có ràng buộc chống trùng | **Bảng cạnh duy nhất theo nguồn.** Thêm TTL; thêm cột loại quan hệ; UNIQUE chống trùng |
| `vn_person_authority` | 1.511 dòng trộn người + 457 alias, có mapping sai | Giữ làm **dữ liệu thô TTL**; mapping chuyển sang `entity_source_ids` |
| `dharma_lineage_ttl_vn` | 784 cạnh TTL (có thể thiếu so với 1.007–1.321 cạnh đếm ở T274/T275) | **Nguồn nạp** cạnh TTL; nạp lại đầy đủ từ file TTL |
| `lineage_edge_consensus`, `lineage_primary_teacher`, `dharma_lineage_base`, `dharma_lineage_unified` (0 dòng) | Bảng gộp / dẫn xuất | **Không làm nguồn.** Thay bằng VIEW tính từ bảng cạnh; bảng cũ giữ làm lưu trữ |
| `data_sources` | 14 nguồn, **không có TTL** | Thêm `TTL_LOCAL` (và nguồn mới về sau) |

## Chỉnh cấu trúc DB đề xuất (additive, không xoá bảng cũ)

1. **Đăng ký nguồn:** `INSERT data_sources (source_code='TTL_LOCAL', …)`.
2. **Người không có DILA:** thêm `entity_hub(entity_type='PERSON', canonical_label='ptda:<slug>')` cho 204 thiền sư TTL chưa có DILA ID.
   Khoá hiển thị `canonical_id` = DILA ID nếu có, ngược lại `ptda:<slug>`.
3. **Mapping:** thêm `entity_source_ids(source='TTL_LOCAL', source_entity_id=<slug>, entity_id, match_status, confidence, verification_note)`.
   - Ràng buộc: mỗi `(source, source_entity_id)` chỉ 1 dòng `accepted` (UNIQUE partial index).
   - Các ca đã biết sai (BUG-038 Lâm Tế, Mã Tổ, Hoàng Bá, 26 DILA ID trùng) để `candidate` / `rejected` chờ Admin.
4. **Bảng cạnh:** `lineage_edge_assertions` thêm
   - `relation_kind` (noi_phap / tham_hoc / unknown, T414);
   - `source_edge_ref` (file TTL / locator CBETA);
   - `mapping_ok` (cả 2 đầu accepted?).
   Khử trùng DILA (46.006 → 23.014). Thêm `UNIQUE(source_code, subject_person_id, object_person_id, relation_type)`.
   Nạp cạnh TTL với `source_code='TTL'`, hai đầu = canonical_id (DILA ID hoặc `ptda:`).
5. **VIEW thay cho bảng gộp:**
   - `v_tree_dila`, `v_tree_marcus`, `v_tree_ttl`: `WHERE source_code = …`. Cây riêng hiện cả cạnh mapping chưa duyệt, gắn nhãn.
   - `v_tree_overlay`: `GROUP BY subject, object` → `n_sources`, danh sách nguồn, `relation_kind` mạnh nhất. Chỉ lấy cạnh `mapping_ok = 1`.
   Màu = `n_sources` (quy tắc T410).
6. **API:** `/daoanh/api/monk/<id>/lineage-tree?trees=dila,marcus,ttl&overlay=1` đọc các VIEW trên. Giao diện có bộ chọn
   "Cây DILA / Cây Marcus / Cây TTL / Chồng cây".
7. **Nguồn thứ 4, 5…:** thêm 1 dòng `data_sources` → nạp cạnh vào `lineage_edge_assertions(source_code=<mới>)` → mapping vào
   `entity_source_ids` → VIEW tự có cây mới. **Không cần đổi schema nữa.**

## Thứ tự làm (mỗi bước một task, cần Admin duyệt vì đổi schema / ghi DB, backup SQLite API trước)

1. Khử trùng cạnh DILA + UNIQUE index (an toàn, tách riêng).
2. Đăng ký TTL_LOCAL + người `ptda:` + mapping TTL vào `entity_source_ids` (dry-run trước, Admin duyệt các ca sai).
3. Nạp lại cạnh TTL đầy đủ từ file TTL vào `lineage_edge_assertions`.
4. Thêm cột `relation_kind` / `source_edge_ref` / `mapping_ok` + 4 VIEW.
5. API + giao diện chọn cây (gộp với T410 màu/nét, T412 tên TTL).

Rủi ro: T368 (Phase 4) đã tạo `dharma_lineage_unified` (bảng gộp) — trái nguyên tắc "không coi gộp là nguồn". Đề xuất để
trống / ngưng dùng làm nguồn.
