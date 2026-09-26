# T69 — Wire Evidence into entity_claims (đa-nguồn, từ dữ liệu thật)

**Ngày:** 2026-08-30
**Build:** TGS Build 1 Acceptance — commit 3/4 (sau T68, trước T70)
**Trạng thái:** ✅ DONE (DB verified)

## Mục tiêu
Đưa evidence-graph (`entity_claims` / `entity_source_ids`) từ trạng thái **mono-source (DILA only)** lên
**đa-nguồn thật** bằng cách NỐI các nguồn dữ liệu placeholder ĐÃ CÓ trong DB (không tạo fake, không import mới).
`verification_status` vẫn `unverified` — chỉ admin HITL mới set verified (khớp quyết định chốt T67).

## Việc đã làm

### Script `scripts/wire_evidence_into_entity_claims.py` (generator, Delete-then-Insert idempotent, KHÔNG checkpoint)
- **CBETA** → từ `place_person_bibl` + `cbeta_place_mentions` + `event_text_link`:
  `entity_claims(claim_type='TEXT_EVIDENCE', ...)` + bổ sung `entity_source_ids` nguồn CBETA.
- **Marcus** → từ `marcus_networks` / `marcus_reference` → claims `NETWORK_EVIDENCE` + `entity_source_ids` MARCUS.
- Map `entity_id` (INT surrogate) qua `entity_hub.canonical_label='PL…'` (JOIN `entity`).
- Giữ `verification_status='unverified'` cho claims tự nối; verified chỉ khi admin HITL duyệt.
- Idempotent: DELETE sources đã wire rồi INSERT lại; KHÔNG checkpoint (tránh sự cố WAL như T58).

## Kết quả (DB verified)
- `entity_claims`: total **447,737** = NAME 177,445 + COORDINATE 175,441 + ADMIN_UNIT 58,586
  + NETWORK_EVIDENCE **22,332** (Marcus) + TEXT_EVIDENCE **13,933** (CBETA).
- `entity_source_ids`: DILA 167,006 + MARCUS **11,297** + CBETA **4,409** + ZQLOCAL 2 + BDRC 1.
- Ghi chú: Wikidata EXTERNAL_ID (148 verified) fail vì `source_id=NULL` — đánh dấu T69+ fix (thêm Wikidata vào data_sources).

## Nguồn nguyên vẹn
- Không sửa bảng nguồn (place_person_bibl, cbeta_*_mentions, event_text_link, marcus_*, geo_cross_ref).
- Reversible: `DELETE FROM entity_claims WHERE claim_type IN ('TEXT_EVIDENCE','NETWORK_EVIDENCE','EXTERNAL_ID')`
  hoặc restore backup.
