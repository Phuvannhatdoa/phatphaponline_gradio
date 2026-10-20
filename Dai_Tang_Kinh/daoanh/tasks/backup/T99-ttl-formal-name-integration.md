---
id: T99
title: TTL Person Formal Name Integration — Tên Trang Trọng Tiếng Việt
module: Person Authority / Lineage Visualization
priority: high
status: done
depends_on: [T86, T05]
created: 2026-09-06
updated: 2026-09-06
done_when: Tên trang trọng từ TTL hiển thị trên node vis.js + inspector "TÊN HIỂN THỊ VIỆT", chỉ khi verified 1:1 với DILA person_id qua ttl_mapping
---

# T99 — TTL Person Formal Name Integration

## Mục Tiêu

Sử dụng tên trang trọng tiếng Việt từ ~1,075 file TTL làm `preferred_display_name_vi` trong UI tab Pháp Mạch (Truyền Thừa). Chỉ áp dụng khi map đã xác minh chắc chắn (1:1) với DILA Person ID ổn định qua bảng `ttl_mapping`.

## Ràng Buộc

- Không hard-code riêng bất kỳ person_id cụ thể vào frontend
- Không dùng LLM/API dịch máy hoặc hard-coded dictionary
- Không migration/AI call nếu không thực sự cần
- KHÔNG gán tên Việt ZQ cho nguồn DILA — vi phạm học thuật
- Không phá schema DILA/CBETA
- Mapping phải có đầy đủ provenance: source_file, RDF subject, method, status
- Raw DILA/Marcus data không được sửa
- Graph relations tiếp tục dùng stable internal person_id, không dùng display name

## Kết Quả

### Files mới/sửa

| File | Thay đổi |
|------|---------|
| `scripts/ttl_person_name_extractor.py` | ETL script với dry-run + apply mode |
| `data/lineage.db` | Bảng `person_display_names` mới, 7 rows verified |
| `app.py` | `_t86_resolve_display_name()` + `nd['display_name']` trong lineage tree |
| `places.html` | `_t86NodeLabel()` + inspector "TÊN HIỂN THỊ VIỆT" |
| `docs/TTL_PERSON_NAME_IMPORT_DRY_RUN.csv` | 1,039 rows — toàn bộ extraction |
| `docs/TTL_PERSON_NAME_REVIEW_QUEUE.csv` | 1,032 rows cần human review |
| `docs/TTL_PERSON_NAME_IMPORT_RESULT.csv` | 7 rows đã apply |
| `docs/TTL_PERSON_FORMAL_NAME_INTEGRATION_REPORT.md` | Báo cáo tích hợp |

### Verification Status Breakdown

| Status | Count |
|--------|-------|
| verified_direct (qua ttl_mapping) | 5 |
| verified_crosswalk (qua tên Hán) | 2 |
| review_required | ~4 |
| rejected (không có DILA ID) | ~1,028 |
| **Total DB rows** | **7** |

### Commits Liên Quan

- `77506ac` — Backend: `_t86_resolve_display_name()` + `nd['display_name']` trong `api_monk_lineage_tree()`
- `de59542` / `a83660c` — Frontend: `_t86NodeLabel()` + inspector "TÊN HIỂN THỊ VIỆT"

## Acceptance Criteria

- [x] Script ETL có dry-run mode an toàn (mặc định không ghi DB)
- [x] Script ETL có --apply mode để ghi verified records vào person_display_names
- [x] Schema person_display_names với provenance đầy đủ
- [x] Resolver _t86_resolve_display_name() với fallback to DILA authority
- [x] API /api/monk/<id>/lineage-tree trả về display_name.is_formal_name=True cho verified records
- [x] Node label trong vis.js dùng tên trang trọng khi is_formal_name=True
- [x] Inspector hiển thị khung "TÊN HIỂN THỊ VIỆT" với tên trang trọng + tên DILA + nguồn + xác minh
- [x] A000453 "Viên Ngộ Khắc Cần": display_name.primary = "Viên Ngộ Khắc Cần", is_formal_name=True
- [x] Báo cáo tích hợp đầy đủ trong docs/
- [x] CSV review queue cho human curation

## Còn Lại (Phase tiếp theo)

- [ ] Phase 8 Tests: unit tests cho resolver + extractor functions
- [ ] Search autocomplete index formal name (Phase 6 còn thiếu)
- [ ] Human curation bảng ttl_mapping → tăng coverage verified records
- [ ] Admin UI review `review_required` records

## Blockers

- Bảng `ttl_mapping` chỉ có 7 records → chỉ 7 verified. Cần human curation để tăng coverage.
- `people.name_zh` lưu dạng viết tắt (e.g. `克勤` thay vì `圜悟克勤`) → không thể auto-match với TTL.
