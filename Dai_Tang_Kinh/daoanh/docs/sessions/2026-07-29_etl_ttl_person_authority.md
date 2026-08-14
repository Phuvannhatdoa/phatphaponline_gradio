# Session: TTL VN → Authority Person VN (Task 5)

**Date**: 2026-07-29
**Tasks**: Task 5

## What was done

### Task 5: Xây dựng `vn_person_authority` từ 16 file TTL thiền sư Việt Nam

**Problem**: Chưa có bảng authority nhân vật Việt Nam. Dữ liệu TTL thiền sư (16 file trong `data/ttl/old/`) là nguồn giàu có nhưng chưa được ETL vào DB. Các bảng `ttl_mapping`/`ttl_works`/`ttl_canon_works` cũ chưa khai thác hết dữ liệu.

**Solution**: ETL dùng rdflib 7.1.4 parse TTL → 5 bảng authority.

### ETL Script
- Viết `scripts/etl_ttl_person_authority.py`
- Tự động xử lý **2 định dạng TTL**:
  1. **Định dạng giàu** (Bạch Vân, Đại Huệ, Dương Kì, Ngũ Tổ, Viên Ngộ): tên qua `crm:P1_is_identified_by`/E41_Appellation + `bkg:hasAppellationType`; năm qua `crm:E67_Birth`/`crm:E69_Death` + `crm:P4_has_time-span`; có associatedPlaces/authoredWorks/hasKeyLifeEvent/hasContribution/hasPhilosophicalStance/hasRelatedFigure
  2. **Định dạng dòng phái** (Thiệt Định, Minh Hải, Toàn Ý...): năm qua `bkg:BirthEvent`/`bkg:DeathEvent` + `bkg:year`; có hasTeacher/hasDisciple/generationOrder/isLineageFounder
- Nối `dila_id` từ bảng `ttl_mapping` (5 nhân vật verified)
- Fallback trích năm sinh/tử từ `biographical_note_vi` (regex khoảng `YYYY-YYYY`)
- Chạy idempotent: DELETE 5 bảng trước khi ghi

### Kết quả
| Bảng | Số dòng |
|------|--------|
| `vn_person_authority` | 16 nhân vật |
| `vn_person_relations` | 84 quan hệ (hasTeacher 18, hasDisciple 49, hasRelatedFigure 17) |
| `vn_person_places` | 46 địa danh (Monastery 23, SacredSite 2) |
| `vn_person_works` | 10 tác phẩm |
| `vn_person_events` | 45 sự kiện |

### Liên kết chéo giữa các file (verified)
```
Minh Hải Pháp Bảo → Thiệt Đinh Ân Triêm, Thiệt Đăng Bảo Quang, Thiệt Bảo Cảm Ứng, Thiệt Thể Triêm Ân, Thiệt Đàm Chánh Luân
Thiệt Đinh Ân Triêm → Pháp Kiêm Minh Giác
Pháp Kiêm Minh Giác → Toàn Ý Phổ Huệ
Toàn Ý Phổ Huệ → Chương Hiệp Chánh Trì
Viên Ngộ Khắc Cần → Đại Huệ Tông Cảo
Ngũ Tổ Pháp Diễn → Viên Ngộ Khắc Cần
Dương Kì Phương Hội → Bạch Vân Thủ Đoan
```

### Bug đã sửa trong quá trình build
1. `rdflib.Namespace` không tự chuyển `_` thành `-`: `CRM.P4_has_time_span` → sai; dùng `URIRef('.../P4_has_time-span')` trực tiếp → event years chạy đúng
2. `placeType`/`gender`/`hasAppellationType` là literal `"bkg:Monastery"` → phải tách phần sau `:` (trước đây lưu cả prefix `bkg:`)
3. Khoảng năm trong note (`1089-1163`) không phải token thuần số → thêm regex bắt cặp `YYYY-YYYY`

## Files changed
- `scripts/etl_ttl_person_authority.py` — ETL script mới (rdflib parse 16 TTL)
- `data/lineage.db` — 5 bảng mới: `vn_person_authority`, `vn_person_relations`, `vn_person_places`, `vn_person_works`, `vn_person_events`
- `docs/db_schema.md` — thêm 5 bảng mới
- `docs/pipelines.md` — thêm pipeline #9 (TTL Person Authority)
- `docs/progress.md` — cập nhật mục "TTL thiền sư Việt Nam"

## How to test
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python scripts/etl_ttl_person_authority.py   # chạy ETL (idempotent)
# Kiểm tra nhanh:
sqlite3 data/lineage.db "SELECT name_vi, birth_year, death_year, dila_id FROM vn_person_authority ORDER BY birth_year IS NULL, birth_year;"
sqlite3 data/lineage.db "SELECT COUNT(*) FROM vn_person_relations;"
sqlite3 data/lineage.db "SELECT target_label_vi FROM vn_person_relations WHERE person_id='dai_hue_tong_cao' AND relation_type='hasTeacher';"
```

## Next
- Task 6 (theo tasktodo.md): ETL ~2000 file TTL còn lại + fact extraction → knowledge graph
- Gắn `dila_id` cho 11 nhân vật còn lại trong `ttl_mapping`
- Tích hợp API/UI cho `vn_person_authority`
