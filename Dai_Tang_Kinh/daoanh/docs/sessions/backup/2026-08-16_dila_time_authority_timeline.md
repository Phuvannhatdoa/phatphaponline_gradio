# Session: DILA Time Authority + Timeline Ver 30

**Date:** 2026-08-16

## Overview
Integrated DILA Time Authority import (time_periods table) with Entity Identity Hub for multi-source provenance (DILA + BDRC + CBETA + MARCUS + ZQLOCAL).

### T14: DILA Time Authority
- Import DILA Time Authority (time_periods = 0) into `time_periods` table (JDN-based calendar conversion)
- API tra cứu niên hiệu / đổi lịch Trung-Hoa-Nhật
- Tích hợp vào chronology / timeline nếu có
- Done when: time_periods có dữ liệu (lunar_month/era/emperor/dynasty) + API tra cứu닐 hiệu

### T15: Entity Identity Hub (Multi-source Provenance)
- ZQ INTERNAL ENTITY: entity_id INTEGER PK, canonical_label, entity_type
- SOURCE REGISTRY: data_sources (DILA, BDRC, CBETA, MARCUS, ZQLOCAL)
- ENTITY SOURCE IDS: entity_source_ids (mapping giữa ZQ internal ID và các source ID)
- CLAIM / EVIDENCE LAYER: entity_claims (claim_type, authority_role, confidence, verification_status)
- PROVENANCE: Mỗi thông tin truy ngược về nguồn gốc
- COMPATIBILITY VIEW: v_entity_places (frontend tiếp tục hoạt động)

### T16: BDRC Adapter (stub)
- adapters/bdrc/ module với discover/fetch_entity/normalize/resolve_identity/fetch_evidence
- BDRC data không có sẵn trong project → staging DB rỗng + schema sẵn sàng chờ data
- BDRC mapping là candidate trống cho đến có data

### T17: Conflict & Provenance Handling
- Mỗi factual paragraph có source badge
- Click source → xem source gốc
- UI không tự động overwrite text DILA/BDRC/CBETA

### Unified Response Object
Entity + identity + sources (DILA/BDRC/CBETA/MARCUS/ZQLOCAL) + claims + evidence

### Key Tables Created
- `entity_hub` (167,006 rows, INTEGER PK ZQ internal IDs)
- `entity_source_ids` (167,008 mappings, UNIQUE source+source_entity_id)
- `data_sources` (5 sources: DILA, BDRC, CBETA, MARCUS, ZQLOCAL)
- `entity_claims` (claim types包括 DATE/IDENTITY/NAME/LOCATION/COORDINATE/HISTORY/BIOGRAPHY/RELATIONSHIP/LINEAGE/TEXTUAL_REFERENCE/DESCRIPTION/VIETNAMESE_SUMMARY)
- `entity_summary` (VIETNAMESE_SUMMARY presentation layer)
- `v_entity_places` (compatibility view for frontend)

### Timeline Ver 30
- Places.html timeline: slider filter theo thế kỷ + dynasty, hiển thị chùa/sư theo thời gian (dark theme Amber Ver 30)
- Source badges: mỗi factual block có `[DILA] [BDRC] [CBETA] [MARCUS] [ZQLOCAL]` → click xem source gốc
- Evidence traceability: every fact → source provenance

### Acceptance Tests (TEST A-J)
- TEST A: User nhập "Thiếu Lâm Tự" → chỉ có một entity chính
- TEST B: User không cần chọn DILA / BDRC / CBETA
- TEST C: Dashboard tự lấy dữ liệu phù hợp
- TEST D: Mỗi factual result có source provenance
- TEST E: Click source → xem source gốc
- TEST F: CBETA T50n2060_p0457c16 → mở đúng text block
- TEST G: DILA GIS coordinates không bị thay đổi
- TEST H: Existing CBETA data không bị thay đổi
- TEST I: Existing Marcus data không bị thay đổi
- TEST J: Nếu BDRC mapping chưa verified: không coi là verified

### Migration Strategy (4 Phases)
- PHASE 1: Discovery (không sửa production)
- PHASE 2: Staging (import BDRC thử nghiệm)
- PHASE 3: Identity mapping (map vào entity_source_ids, chỉ verified/candidate)
- PHASE 4: Unified API (chỉ expose vào Dashboard khi test thành công)

### Rollback Plan
- Backup: data/lineage.db → data/backup/lineage_20260816_*.db
- Existing entity table GẮC chưa được sửa
- New tables: entity_hub, entity_source_ids, data_sources, entity_claims, entity_summary, v_entity_places
- Có thể xóa các table mới và khôi phục backup nếu cần
"""
)