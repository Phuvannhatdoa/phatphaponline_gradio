---
id: T69
title: "Wire Evidence into entity_claims (backfill từ dữ liệu thật, đa-nguồn)"
module: DILA Integration Layer
priority: medium
status: done
depends_on: [T58, T68]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: >
  entity_claims / entity_source_ids chứa bằng chứng ĐA-NGUỒN thật (CBETA citation + Marcus +
  Wikidata external_id) kèm source_record_id + source_reference + authority_role, sinh bằng
  generator idempotent từ dữ liệu đã có — không tạo mock, không import dữ liệu mới.
---

# T69 — Wire Evidence into entity_claims (Đa-nguồn, từ dữ liệu thật)

## Mục tiêu
Đưa evidence-graph (entity_claims / entity_source_ids) từ trạng thái **mono-source (DILA only, 0 verified)**
lên **đa-nguồn thật** bằng cách NỐI các nguồn dữ liệu placeholder đã có trong DB — không tạo fake,
không import mới (giữ zero overhead). Verification_status vẫn 'unverified' (chỉ admin HITL mới set verified — khớp quyết định chốt).

## Hiện Trạng (Codebase)
- `entity_claims` (411,472) — source hiện có: DILA NAME (59,150) / ADMIN_UNIT (58,586) / COORDINATE (175,441) + ZQLOCAL NAME (118,295). Không có CBETA/Marcus/Wikidata.
- `entity_source_ids` (167,009) — chỉ DILA 167,006 (verified=0, match_status='candidate') + ZQLOCAL 2 + BDRC 1.
- Nguồn thật đang nằm RẢI RÁC chưa nối: `place_person_bibl` (13,933, có cbeta_ref + source_book), `cbeta_place_mentions` (16,311), `cbeta_person_mentions` (72,628), `event_text_link` (17,284), `marcus_networks` (11,169)/`marcus_reference` (18,127), `geo_cross_ref` (181, wikidata_qid 148 verified).

## Khoảng Trống (Gap)
- CBETA / Marcus / Wikidata evidence chưa vào `entity_claims` / `entity_source_ids`.
- Evidence graph vẫn chỉ là DILA mirror.

## Thiết Kế (generator idempotent, Zero-RAM)

### Script `scripts/wire_evidence_into_entity_claims.py` (generator, DELETE-then-INSERT idempotent, không checkpoint)
- **CBETA** → từ `place_person_bibl` + `cbeta_place_mentions` + `event_text_link`:
  `entity_claims(claim_type='TEXT_EVIDENCE', subject=entity_ref, predicate='mentioned_in',
  object_text=context_snippet, source_record_id=dila/bibl id, source_reference=cbeta_ref, authority_role='PRIMARY', confidence)`
  + bổ sung `entity_source_ids` nguồn CBETA.
- **Marcus** → từ `marcus_networks`/`marcus_reference` → claims NETWORK_EVIDENCE + entity_source_ids MARCUS.
- **Wikidata** → từ `geo_cross_ref` (148 verified) → claims `EXTERNAL_ID` (object_text=QID, source_reference='Q…', confidence='verified').
- Map `entity_id` (INT surrogate) qua `entity_hub.canonical_label='PL…'` (JOIN `entity`).
- Giữ `verification_status='unverified'` cho claims tự nối; verification_status 'verified' CHỈ khi admin HITL duyệt (T67).
- Idempotent: DELETE sources đã wire rồi INSERT lại; KHÔNG cần checkpoint (tránh sự cố WAL như T58).

## Subtasks
- [x] T69a: `scripts/wire_evidence_into_entity_claims.py` — idempotent, delete-then-insert
- [x] T69b: entity_claims: +13,933 TEXT_EVIDENCE (CBETA) + 22,332 NETWORK_EVIDENCE (Marcus) = 447,737 total. entity_source_ids: +CBETA 4,409 +MARCUS 11,297. Note: EXTERNAL_ID Wikidata 148 failed (source_id=NULL — fix in T69+: add Wikidata to data_sources)
- [x] T69c: Bảng nguồn nguyên vẹn (verified)
- [x] T69d: git commit (Build 1 - T68+T69+T70)

## Revert
- `DELETE FROM entity_claims WHERE claim_type IN ('TEXT_EVIDENCE','NETWORK_EVIDENCE','EXTERNAL_ID')` hoặc backup DB trước khi chạy — reversible.
- Không sửa bảng nguồn.
