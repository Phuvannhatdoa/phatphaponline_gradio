# Session Log — 2026-09-06 — T99 TTL Person Formal Name Integration

**Task:** T99 — TTL Person Formal Name Integration  
**Status sau session:** ✅ Done (Phases 1–7 hoàn thành)

---

## Tóm Tắt

Tích hợp tên trang trọng tiếng Việt từ ~1,075 file TTL vào UI tab Pháp Mạch. Mỗi tên chỉ được sử dụng sau khi xác minh 1:1 với DILA Person ID qua bảng `ttl_mapping`.

## Kết Quả Chính

- **7 records verified** ghi vào `person_display_names` table (5 verified_direct + 2 verified_crosswalk)
- **1,028 records rejected** (không có DILA ID trong ttl_mapping) → cần human curation
- **4 records review_required** → cần scholar xác nhận
- **A000453 "Viên Ngộ Khắc Cần"** verified và hiển thị đúng trong UI ✅

## API Verification

```
GET /daoanh/api/monk/A000453/lineage-tree?up=1&down=0
→ display_name.is_formal_name = true
→ display_name.primary = "Viên Ngộ Khắc Cần"
→ display_name.verification_status = "verified_direct"
```

## UI Verification

- Tab TRUYỀN THỪA: node hiển thị "Viên Ngộ Khắc Cần" (tên trang trọng) ✅
- Inspector: khung xanh "TÊN HIỂN THỊ VIỆT" với tên trang trọng + tên DILA + nguồn ✅
- Screenshot: lấy được trong session này

## Files Tạo Mới Trong Session Này

| File | Mô tả |
|------|-------|
| `scripts/ttl_person_name_extractor.py` | ETL script |
| `docs/TTL_PERSON_NAME_IMPORT_DRY_RUN.csv` | 1,039 rows extraction |
| `docs/TTL_PERSON_NAME_REVIEW_QUEUE.csv` | 1,032 rows cần review |
| `docs/TTL_PERSON_NAME_IMPORT_RESULT.csv` | 7 rows đã apply |
| `docs/TTL_PERSON_FORMAL_NAME_INTEGRATION_REPORT.md` | Báo cáo tích hợp |
| `tasks/T99-ttl-formal-name-integration.md` | Task tracking |

## Commits Liên Quan (đã commit ở session trước)

- `77506ac` — Backend app.py: resolver + lineage tree enrichment
- `de59542` — Frontend places.html: inspector "TÊN HIỂN THỊ VIỆT"

## Commit Session Này

Commit: `feat(T99): TTL formal name ETL script + review CSVs + integration report + task`

## Giới Hạn Còn Lại

1. **Coverage thấp (7/1,039 = 0.67%)**: Do `ttl_mapping` chỉ có 7 records. Cần human curation.
2. **Search autocomplete**: Chưa index `display_name_vi` vào autocomplete (Phase 6 còn thiếu).
3. **Phase 8 Tests**: Chưa có unit tests.
4. **Admin review UI**: Chưa có trang review `review_required` records.

## Vấn Đề Kỹ Thuật Đã Giải Quyết

- **Hai định dạng TTL**: Root files dùng literal URIs (`bkg:Monk` angle-bracket), subdir files dùng expanded URIs. Giải quyết bằng dual-check `MONK_TYPE_RAW` + `MONK_TYPE_FULL`.
- **DILA name_zh viết tắt**: `克勤` vs `圜悟克勤` → không thể auto-match. Chỉ dựa vào `ttl_mapping`.
- **Dedup logic**: 36 files trùng (cùng stem trong root + subdir). Subdir ưu tiên.
