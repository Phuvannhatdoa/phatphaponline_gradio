# Session — T82 Data-Lock Audit (read-only, 2026-09-11)

> Thuần read-only: 0 INSERT/UPDATE/DELETE, 0 ALTER, 0 index mới trong DB. Chỉ SELECT COUNT +
> orphan-check bằng Python set (Zero-RAM). Báo cáo = checkpoint "data-lock" trước release.

## Kết quả audit `data/lineage.db`

### Số dòng các bảng
| Bảng | Rows | Ghi chú |
|------|------|---------|
| text_reading_log | 0 | T55c log — sạch (test rows đã xóa) |
| place_desc_vi_draft | 14,000 | T66 draft mô tả place (Hán gốc) |
| person_bio_vi_draft | 2,093 | T63+T65 draft bio |
| entity_claims | 447,885 | +13,933 TEXT_EVIDENCE +22,332 NETWORK_EVIDENCE (T69) |
| entity_source_ids | 182,715 | |
| en_audit_log | 3 | audit log gần như trống → **cần chú ý HITL ghi audit** |
| geo_cross_ref | 190 | 9 candidate enrich (T121 D2) |
| places_dila | 59,167 | nguồn DILA |
| namevi_map_places | 118,296 | mapping VI |
| places | 59,161 | bản local (GPS) |
| people | 48,673 | |
| lexicon | 166,278 | |
| cbeta_catalog_vn | 3,122 | catalog kinh CBETA |
| cbeta_person_mentions | 72,628 | co-mention (T55b nhóm 2) |
| canonical_decision | 2 | T67 quyết định canonical |

### Integrity checks
| Check | Kết quả | Đánh giá |
|-------|---------|----------|
| place_desc_vi_draft.place_id → places_dila.id | 0 orphan / 14,000 | ✅ |
| person_bio_vi_draft.person_id → people.id | 0 orphan / 2,093 | ✅ |
| cbeta_person_mentions sigla → cbeta_catalog_vn.cbeta_ref | 0 orphan / distinct | ✅ |
| place_desc_vi_draft admin_approved=1 | 0 | ⚠️ chờ HITL (bình thường) |
| person_bio_vi_draft admin_approved=1 | 0 | ⚠️ chờ HITL (bình thường) |
| en_audit_log | 3 rows | ⚠️ rất ít audit so với lượng edit (cần theo dõi) |
| geo_cross_ref enrich_status='candidate' | 9 | T121 D2 đã chạy candidate, chưa approve |

## Kết luận
- **Data-lock đạt** cho non-HITL tables: 0 orphan ở 3 chuỗi draft chính.
- Chưa có admin approve nào (0/14,000 + 0/2,093) — đúng kỳ vọng, chờ T73/T74 UI review.
- `en_audit_log` chỉ 3 rows → cảnh báo nhẹ: các phiên build sau nên ghi audit nhiều hơn (hoặc chấp nhận vì phần lớn build là data ETL có script riêng không ghi en_audit_log).

## Files
- `docs/sessions/t82_data_lock_audit.json` (mới) — dữ liệu audit chi tiết
- `docs/sessions/2026-09-11_t82-data-lock-audit.md` (file này, chuẩn session)

## Revert
- Không có gì để revert (read-only). JSON là báo cáo dừng thời điểm, có thể xóa an toàn.