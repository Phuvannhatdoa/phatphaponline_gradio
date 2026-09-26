# T76 — B2 Failures & Remediation

**Task:** T76 — B2 Real Data Acceptance Test
**Ngày:** 2026-08-31

> Theo fail-safe rule: không sửa code chỉ để test pass. Các mục dưới đây là điểm **PARTIAL** (dữ liệu/máy móc chưa đủ để đạt PASS), ghi root-cause + đề xuất khắc phục. **Chưa sửa gì cho tới khi admin xác nhận root-cause.**

---

## 1. Provenance — PARTIAL

**Root cause:** 
- DILA: `retrieved_at` = 0/293,177, ref = 175,440/293,177. DILA là canonical nên một phần claim nội sinh (ADMIN_UNIT/COORDINATE/NAME) không có `source_reference` chuẩn.
- ZQLOCAL: 118,295 claims nhưng `source_reference`/`retrieved_at` = 0 (import nội từ `zqlocal_content`, chưa gắn provenance record).

**File/module liên quan:**
- `scripts/wire_evidence_into_entity_claims.py` (T69) — nơi wire DILA/ZQLOCAL claims.
- `app.py` `/daoanh/api/places/<id>/claims` (L12227) — đọc, không tạo provenance.

**Remediation (đề xuất, chưa làm):**
- Task mới quét `entity_claims` còn `retrieved_at IS NULL` cho DILA/ZQLOCAL → backfill `retrieved_at`/`source_reference` từ transaction import (additive `UPDATE`, có backup + `--undo`).
- Cân nhắc: DILA canonical nội sinh có thể được phép provenance = canonical, nhưng phải **ghi rõ** thay vì để NULL.

---

## 2. Entity Matching — PARTIAL

**Root cause:**
- Dữ liệu cross-ref thật rất mỏng: `geo_cross_ref=181`, `name_vi_map_places=0`, `resolutions_log=0`.
- Không đủ case thật (same-name/different-location, transliteration variant) để chứng minh matcher phân biệt EXACT/LIKELY/POSSIBLE/CONFLICT/NO_MATCH.

**File/module liên quan:**
- Bảng: `geo_cross_ref`, `geo_cross_ref_candidates`, `name_vi_map_places`, `name_normalization`, `places_pending`.

**Remediation (đề xuất):**
- Task mới: **ingest thêm cross-ref thật** từ Wikidata spatial (T39/T64/T64b ceiling ~150) và CHGIS khi connector hoạt động, tạo case matching thật.
- Sau khi có case thật: chạy matcher phân biệt → chứng minh hoặc sửa theo root-cause.

---

## 3. Conflict Detection — PARTIAL

**Root cause:**
- `conflict_pending=0`, `conflicts=0` — chưa có conflict thật được ingest/detect.
- `_resolve_entity_id` + `_detect_conflicts()` (T68) tồn tại nhưng chưa có case thật để vận hành.

**File/module liên quan:**
- `app.py` `_detect_conflicts()` (T68) — logic phát hiện.
- Bảng `conflict_pending`, `conflicts`.

**Remediation (đề xuất):**
- KHÔNG seed theo luật. Đợi cross-ref thật (Wikidata/CHGIS) để phát sinh conflict thật, hoặc
- Task mới khảo sát data thật tìm app-conflict (vd 2 nguồn gán cùng entity → vị trí khác nhau trong `places_pending` vs `places_dila`) để có case thật không seed.

---

## Tóm tắt

| Mục | Status | Root cause | Cần |
|---|---|---|---|
| Provenance | PARTIAL | DILA/ZQLOCAL thiếu retrieved/ref | Backfill additive + ghi rõ canonical nội sinh |
| Matching | PARTIAL | dữ liệu cross-ref mỏng (181) | Ingest cross-ref thật (Wikidata/CHGIS) |
| Conflict | PARTIAL | 0 case thật | Khảo sát data thật / đợi cross-ref |

**Không có CRITICAL FAIL. Không sửa code tới khi root-cause được xác nhận.**
