# Đánh giá đặc tả "DILA ID làm khoá gốc + nhiều cây theo nguồn" (2026-10-19)

**Người đánh giá:** Claude Code (RC) · **Chế độ:** chỉ đọc DB/code · **Đặc tả:** JSON `implement_dila_id_as_canonical_key_multi_source_trees`
do Admin gửi 2026-10-19.

## Kết luận

**Hướng đúng và phù hợp mục tiêu "mỗi công trình một cây, xem riêng hoặc chồng lên nhau".** Các điểm rất tốt:

- Mỗi nguồn giữ bộ cạnh riêng.
- Chỉ gộp khi hiển thị.
- Không dùng "consensus" làm nguồn.
- Không tự gộp người, không tự tạo cạnh.
- Có quy trình nạp nguồn mới.

Bảng `lineage_edge_assertions` hiện có đã gần đúng mô hình này: cạnh theo `source_code`, hai đầu là DILA ID.

**Nhưng có 6 điểm cần sửa trước khi làm**, nếu không sẽ mất phần lớn dòng Việt hoặc tô màu sai.

## Số đo thực tế (DB 2026-10-19, chỉ đọc)

| Đo | Kết quả |
|---|---|
| Hồ sơ TTL (không tính alias) | 1.054, trong đó **204 không có DILA ID** (19%) |
| Cạnh TTL dòng Việt (`dharma_lineage_ttl_vn`) | 784, chỉ **553 (70,5%)** có cả 2 đầu map được sang DILA ⇒ **231 cạnh (29,5%) sẽ bị loại** theo luật "unmapped không vào overlay" |
| DILA ID bị ≥2 hồ sơ TTL (không alias) trỏ vào | 26 |
| Cạnh DILA lưu trùng | 22.992 cặp (BUG-027) |
| Mapping sai đã phát hiện | `lam_te_nghia_huyen` → A032162 (sư Triều Tiên, BUG-038); `ma_to_dao_nhat` → A038890; `hoang_ba_hy_van` chưa map |
| `dharma_lineage_unified` (T368) | 0 dòng — là bảng gộp, trái luật `no_consensus_as_source` nếu dùng làm nguồn |

## 6 điểm cần sửa

1. **Khoá gốc: cần "DILA ID nếu có, ID PTDA nếu không".** Nhiều thiền sư Việt Nam không có trong DILA. Nếu chỉ chấp nhận
   `dila_id` thì cây TTL mất 19% người và 29,5% cạnh, đúng phần dòng Việt quan trọng nhất của dự án.
   → `canonical_id` = `dila_id` khi có, ngược lại `ptda:<slug>` (namespace riêng), kèm cờ `has_dila`. Về sau khi tìm được
   DILA ID thì ghi đối chiếu `ptda:x → Axxxxxx` (bảng alias), không đổi ID cũ.
2. **Mapping là phần khó nhất, cần có trạng thái duyệt.** "Import xong tạo mapping là có cây mới" chỉ đúng khi mapping đúng.
   BUG-038 cho thấy một mapping sai làm cả trục tổ sư đi sai.
   → Dùng bảng `source_person_map(source, source_person_id, canonical_id, status{candidate|accepted|rejected}, method, confidence,
   evidence, reviewer, reviewed_at)`, không dùng cột `marcus_id` / `ttl_id` trong `persons`. Lý do: một người có thể ứng với
   nhiều bản ghi ở một nguồn, ví dụ alias, file TTL trùng.
   Ràng buộc: mỗi `(source, source_person_id)` chỉ có 1 dòng `accepted`. Chỉ cạnh có **cả 2 đầu `accepted`** mới vào overlay.
   Cạnh còn `candidate` vẫn hiện trong **cây riêng của nguồn đó**, kèm nhãn "chưa đối chiếu".
3. **Khoá gộp không nên chứa `predicate`.** DILA và Marcus chỉ có "thầy–trò" chung; TTL là "nối pháp". Nếu khoá gộp gồm
   predicate thì cùng một cặp thầy–trò bị tách thành nhiều cạnh, và số nguồn (màu) bị đếm sai.
   → Gộp theo `(from, to, direction)`. `predicate` là thuộc tính theo từng nguồn. Màu = số nguồn ghi nhận quan hệ.
   Nét liền/đứt = predicate mạnh nhất có bằng chứng (nối pháp hoặc tham học, xem T414).
4. **Màu: thống nhất với quy tắc Admin đã chốt (T410).** JSON ghi 3 nguồn = `blue`, nhưng T410 ghi "Xanh" (đang hiểu là xanh lá).
   JSON có `unknown_direction: gray_dashed`, nhưng nét đứt đã được dành cho "tham học, chưa đắc pháp".
   → Admin chốt: 3 nguồn là xanh dương hay xanh lá? Cạnh chưa rõ chiều vẽ thế nào (đề xuất: xám, nét chấm, khác hẳn nét đứt)?
5. **`no_sna_as_lineage_source` và Marcus.** Marcus gồm cả dữ liệu mạng xã hội (`marcus_networks`) lẫn quan hệ thầy–trò.
   → Ghi rõ: chỉ nhận cạnh **thầy–trò** của Marcus (`da:isTeacherOf`), loại cạnh mạng xã hội / đồng xuất hiện.
6. **Làm sạch trong từng nguồn trước khi gộp.** Có 22.992 cạnh DILA trùng. 26 DILA ID bị nhiều hồ sơ TTL trỏ vào: đây là vi phạm
   `one_person_one_dila_id_node` có sẵn, phải đưa vào hàng chờ review, không được tự gộp.

## Đặc tả đề xuất (sửa lại)

```json
{
  "canonical_key": "canonical_id (= dila_id nếu có, ngược lại ptda:<slug>)",
  "persons": {"primary_key": "canonical_id", "fields": ["canonical_id","has_dila","label_vi","aliases"]},
  "source_person_map": {"fields": ["source","source_person_id","canonical_id","status","method","confidence","evidence","reviewer"],
                        "unique_accepted": ["source","source_person_id"]},
  "lineage_edges": {"fields": ["id","source","from_cid","to_cid","predicate","direction","provenance","status","source_edge_key"],
                    "dedupe_within_source": ["source","from_cid","to_cid","predicate"]},
  "overlay": {"merge_key": ["from_cid","to_cid","direction"],
              "color_by_source_count": {"3": "<Admin chốt>", "2": "yellow", "1": "red"},
              "line_style": {"noi_phap": "solid", "tham_hoc": "dashed (chỉ quanh vị đang xem)", "unknown_direction": "<Admin chốt>"},
              "enter_overlay_only_if": "cả 2 đầu mapping status = accepted"},
  "source_tree": "hiện cả cạnh mapping candidate, gắn nhãn 'chưa đối chiếu'",
  "marcus": "chỉ cạnh thầy–trò, loại SNA"
}
```

## Thứ tự triển khai gợi ý (cần duyệt vì có đổi schema / ghi DB)

1. Tạo `source_person_map` (additive), nạp mapping TTL/Marcus hiện có ở trạng thái `candidate`. Mapping khớp chắc chắn thì
   `accepted` theo quy tắc. Xử lý trước các ca đã biết sai (BUG-038, Mã Tổ, Hoàng Bá).
2. Nạp cạnh TTL (`dharma_lineage_ttl_vn`) vào `lineage_edge_assertions` với `source='ttl'` qua mapping. Khử trùng cạnh DILA.
3. API `/lineage-tree?trees=dila,marcus,ttl&overlay=1` + badge nguồn trên cạnh và nút.
4. Quy trình nạp nguồn thứ 4, 5…: import → mapping (candidate → review) → kiểm 2 đầu cạnh → bật cây → bật overlay.

Liên quan: T410 (màu/nét), T412 (tên TTL), T413 (BUG-038), T414 (nối pháp), T368 (schema Phase 4).
