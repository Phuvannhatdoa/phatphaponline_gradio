# Session: TGS Build 2 — Phase E (Docs Refresh)

**Date:** 2026-08-31
**Branch/Task:** TGS Build 2 Phase E (docs: build1_inventory + trusted-sources)
**Status:** DONE

## Objective
Đồng bộ tài liệu sau khi Build 2 Phase A→D hoàn tất:
- `docs/build1_inventory.md` — cập nhật các dòng stale (T68/T69/T70 từ MISSING/PARTIAL → DONE) + ghi nhận Build 2 phases.
- `docs/trusted-sources.md` — mở rộng từ "15 nguồn" → "20 nguồn" theo chiến lược CORE/EXPAND/BRIDGE/ASSESS/SKIP (theo `docs/TGS-integration-masterplan.md`).

## `docs/build1_inventory.md`
- Authority matrix: **MISSING (→ T68) → DONE** — matrix 13 nguồn (`DILA=100>CBETA=80>SAT=75>Kanripo=70>Marcus=60>CHGIS=58>TGAZ=55>ZQLOCAL=50>SuttaCentral=50>84000=BDRC=FoJin=40>Wikidata=25`).
- Conflict detection: **MISSING → DONE** (`conflict_pending` + `_detect_conflicts()` + GET /conflicts).
- Evidence wire: **PARTIAL → DONE** (`entity_claims` 447,885 + `source_url`/`retrieved_at` provenance + claims endpoint/UI).
- Governance: **PARTIAL → DONE** (`implemented=0` minh bạch cho các nguồn chưa tích hợp; cleanup test rows).
- `entity_claims` count cập nhật 411,472 → 447,885 (kèm provenance Phase B).
- Kết luận: ghi nhận Build 2 Phases A-D (fix CBETA id; Wikidata data_sources; provenance; evidence API/UI; cross-ref matrix reversible).

## `docs/trusted-sources.md`
- Title: "15 Nguồn" → **"20 Nguồn"**; bổ sung Strategy legend + `implemented` theo `source_authority`.
- Bảng trạng thái: 20 nguồn theo masterplan (CORE: CBETA/DILA/BGIS/ZQLOCAL/Wikidata/MARCUS; EXPAND: Kanripo/SuttaCentral/84000/VRI; BRIDGE: SAT/BuddhaNexus/CHGIS/TGAZ; ASSESS: ToL/IDP/GRETIL/DSBC; SKIP: THL/PTS/BDRC/OCBS) + foJin registered.
- Thêm cột "Reg" đánh dấu các nguồn đã đăng ký trong matrix (✅).
- Ma trận tích hợp cuối file: cập nhật status theo Build 2 + note Phase D reversible.

## Files Changed
- `docs/build1_inventory.md`
- `docs/trusted-sources.md`
- `docs/sessions/2026-08-31_TGS_B2_PhaseE_docs_refresh.md` (log này)

## Verification
- N/A (docs only — không đụng code). Pipeline không cần chạy lại; các phase trước đã verify (lint/test/e2e exit 0).

## Next Steps
- TGS Build 2 hoàn tất qua Phase E. Các bước tương lai:
  - Duyệt UI evidence panel + claims endpoint trong runtime (restart server qua `dashboard/restart_servers.ps1`).
  - T34 GĐ B/C/D (Kanripo/SuttaCentral/84000 real pipeline) → set `implemented=1`.
  - T21/CHGIS/TGAZ khi cần lớp lịch sử hành chính.
  - Cập nhật trạng thái T73/T74 trong tasktodo khi tiến triển.