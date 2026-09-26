# T76 — B2 Real Data Acceptance Report

**Task:** T76 — B2 Real Data Acceptance Test
**Ngày:** 2026-08-31
**Mode:** REAL DATA (không mock, không seed, không database test thay thế, không hard-code PASS)

---

## Verdict tóm tắt

```
B2 STATUS:      PARTIAL
REAL ENTITIES TESTED:    15 (≥10 yêu cầu)
SOURCES ACTUALLY TESTED: 5 (DILA, CBETA, MARCUS, ZQLOCAL, Wikidata)
EVIDENCE RECORDS TESTED: 447,885 (entity_claims)
CONFLICTS DETECTED:      0 (conflict_pending=0 thực tế)
HUMAN REVIEW CASES:      2 canonical_decision + 2 en_audit_log
CRITICAL FAILURES:       0
REGRESSION:              PASS (lint/test/e2e exit 0; checksum identical)
```

---

## Bảng acceptance 13 test

| # | Test | Result | Evidence (data thật) |
|---|---|---|---|
| 1 | Canonical Identity | ✅ PASS | 0 canonical PLACE ngoài prefix `PL0`; DILA giữ canonical (au=100); external ID chỉ trong `entity_source_ids`/`entity_claims` |
| 2 | Source Evidence | ✅ PASS | 5 source ingest: DILA 293,177 / ZQLOCAL 118,295 / MARCUS 22,332 / CBETA 13,933 / Wikidata 148 |
| 3 | Provenance | ⚠️ PARTIAL | CBETA/MARCUS/Wikidata 100% ref+retrieved; DILA ref 175,440/293,177 (retrieved=0); ZQLOCAL ref=0/118,295 |
| 4 | Cross-reference | ✅ PASS | DILA 167,006 + MARCUS 11,297 + CBETA 4,409 + ZQLOCAL 2 + BDRC 1; 15 entity ≥3 sources |
| 5 | Entity Matching | ⚠️ PARTIAL | `geo_cross_ref=181`, `name_vi_map_places=0` — dữ liệu quá mỏng để chứng minh same-name/different-location phân biệt |
| 6 | Authority Ranking | ✅ PASS | 13-source matrix (DILA=100>CBETA=80>SAT=75>MARCUS=60>ZQLOCAL=50>Wikidata=25); endpoint trả claims theo authority desc |
| 7 | Conflict Detection | ⚠️ PARTIAL | conflict_pending=0, conflicts=0 — KHÔNG seed; không có case thật để chứng minh phát hiện conflict |
| 8 | Evidence Graph | ✅ PASS | Trace entity→evidence→source→record→ref→retrieved đầy đủ (vd `PL000000023255 → CBETA → T50n2060_p0457c16`) |
| 9 | Human Review | ✅ PASS | `canonical_decision=2`, `en_audit_log=2`, 1 entity verified (Đạo Ảnh HITL) |
| 10 | Negative Tests | ✅ PASS | DILA không tồn tại → 0 claims (không crash); missing GPS 687 handled; missing source_id=0; API HTTP 200 |
| 11 | Data Integrity | ✅ PASS | Checksum trước/sau IDENTICAL (chỉ khác timestamp) — 0 thay đổi DB trong toàn bộ test |
| 12 | Performance | ✅ PASS | claims 1.18ms / source_ids 0.39ms / authority 0.19ms; hub 87ms; places LIKE 8.78s (ghi nhận, chưa tối ưu) |
| 13 | End-to-End | ✅ PASS | API thật `/daoanh/api/places/PL000000023255/claims` HTTP 200, resolved=181597, 38 claims, DILA xếp đầu |

---

## Chi tiết từng test (data thật)

### 1. Canonical Identity — PASS
- query: `SELECT COUNT(*) FROM entity_hub WHERE entity_type='PLACE' AND canonical_label NOT LIKE 'PL0%'` → **0**
- Baseline entity 181597 (Thiếu Lâm Tự): `entity_source_ids` giữ DILA + CBETA cùng trỏ về `PL000000023255`; **không** external ID trở thành canonical.
- 15 entity mẫu đều có canonical_label `PL0...` (DILA chuẩn).

### 2. Source Evidence — PASS
- 5 nguồn thực sự đã ingest evidence claim (xem bảng môi trường).
- 8 nguồn còn lại `implemented=0` → không ghi nhận evidence (không coi là PASS hoàn toàn — chỉ connector).

### 3. Provenance — PARTIAL
- CBETA: `source_reference` 13,933/13,933 (100%), `retrieved_at` 13,933/13,933.
- MARCUS: 22,332/22,332 (100%) ref + retrieved.
- Wikidata: 148/148 ref + url + retrieved.
- DILA: ref 175,440/293,177 (60%), retrieved 0/293,177.
- ZQLOCAL: ref 0/118,295, retrieved 0/118,295.
- **→ Chưa đạt "không evidence không rõ nguồn" toàn vẹn** ở DILA/ZQLOCAL.

### 4. Cross-reference — PASS
- 15 entity có ≥3 sources (DILA+CBETA+MARCUS+...).
- external refs đều gắn cùng canonical entity, **không merge mù** (mỗi source giữ record riêng trong `entity_source_ids`).

### 5. Entity Matching — PARTIAL
- Dữ liệu quá mỏng: `geo_cross_ref=181`, `name_vi_map_places=0`, `resolutions_log=0`.
- Không đủ case thật để chứng minh EXACT/LIKELY/POSSIBLE/CONFLICT/NO_MATCH + same-name/different-location.

### 6. Authority Ranking — PASS
- Ma trận 13 nguồn đầy đủ (DILA 100 → Wikidata 25).
- API xếp claims theo `authority_score DESC` → DILA xếp trước CBETA/ZQLOCAL/Wikidata.
- Phân biệt SOURCE AUTHORITY (matrix) với MATCH CONFIDENCE (cột `confidence` trong claims).

### 7. Conflict Detection — PARTIAL
- `conflict_pending=0`, `conflicts=0`. Theo fail-safe: không có case thật để phát hiện → KHÔNG tuyên PASS, ghi nhận PARTIAL (không seed, đúng luật).

### 8. Evidence Graph — PASS
- Trace ngược đầy đủ: `PL000000023255 → CBETA → TEXT_EVIDENCE → T50n2060_p0457c16 → retrieved 2026-08-30`.
- Không phải graph trần entity→source; có record + ref + retrieved.

### 9. Human Review — PASS
- `canonical_decision=2`, `en_audit_log=2`, 1 entity `verified`.
- Đạo Ảnh HITL hoạt động, ghi provenance (ai/khi nào/nguồn/trạng thái).

### 10. Negative Tests — PASS
- DILA không tồn tại `PL999999999999` → 0 entity, API trả 0 claims HTTP 200 (không crash).
- Missing GPS: 687 places không GPS (hệ thống xử lý được).
- Missing source_entity_id: 0.
- Không tạo canonical entity giả, không overwrite.

### 11. Data Integrity — PASS
- `data/t76_checksum_before.json` vs `after.json`: **mọi chỉ số + key-hash giống hệt** (chỉ timestamp khác). 0 thay đổi DB trong test read-only.

### 12. Performance — PASS (ghi số liệu)
- claims 1.18ms, source_ids 0.39ms, authority 0.19ms, hub 87ms, places LIKE 8.78s.

### 13. End-to-End — PASS
- Flow thật: `PL000000023255 → resolve 181597 → claims 38 → DILA đầu → provenance đủ` qua API live HTTP 200.

---

## Kết luận

- **Không critical failure** (0/13 CRITICAL).
- **5/13 PASS**, **3 PARTIAL** (Provenance, Entity Matching, Conflict Detection), 5 test còn lại PASS (tổng 13 ô: PASS=10, PARTIAL=3).
- Verdict **PARTIAL** vì: matching + conflict chưa được chứng minh trên data thật hiện có (do dữ liệu mỏng + conflict=0), và provenance chưa toàn vẹn ở DILA/ZQLOCAL. Chỉ đạt **B2 ACCEPTED** khi 3 phần này có case thật / đủ dữ liệu.
