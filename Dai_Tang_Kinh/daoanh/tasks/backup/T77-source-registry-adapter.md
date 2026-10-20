---
id: T77
title: "Source Registry metadata + Adapter skeleton (READY FOR FUTURE SOURCE INTEGRATION)"
module: DILA Integration Layer
priority: high
status: done
depends_on: [T76]
created: 2026-08-31
updated: 2026-08-31
completed: 2026-08-31
done_when: >
  `data_sources` có đủ metadata (version, sync, enabled, capabilities, license flags) để quản trị
  nguồn; có SourceAdapter contract (adapters/base.py) + SourceAdapterRegistry (adapters/registry.py)
  nạp/dispatch data-driven theo `data_sources`; có adapter mẫu (BDRC skeleton); tài liệu BUILD1_AUDIT,
  SOURCE_INTEGRATION_ARCHITECTURE, SOURCE_ONBOARDING ghi rõ cách thêm nguồn mới.
---

# T77 — Source Registry metadata + Adapter skeleton

## Mục tiêu
Giúp TGS **thêm nguồn dữ liệu mới mà không phải sửa core** (`entity_unified`, routes clone,
canonical): "THÊM NGUỒN = đăng ký + adapter". Phương án **B** — chỉ registry + adapter (additive,
reversible), de-lock-in `entity_unified` để lại Build 4+.

## Nguyên tắc (Build hard-rules)
- **Additive + reversible**: ALTER chỉ thêm cột, không drop/sửa; script có `--undo` + backup.
- **KHÔNG đụng** `entity_unified`, routes clone, `geo_cross_ref`, canonical core, harvester hiện có.
- **DILA = canonical**; external = cross-reference.
- Chạy **sau T76** (cô lập checksum trước/sau).

## Kết quả (2026-08-31)

### 1. Registry metadata mở rộng — `data_sources` (+13 cột)
`source_version, adapter_version, schema_version, last_sync, last_verified, enabled, health,
capabilities(JSON), base_url, attribution_required, redistribution_allowed, commercial_use, api_terms`
- Backfill 5 nguồn đã biết (DILA/CBETA/MARCUS/ZQLOCAL/Wikidata) với version + capabilities + license.
- Script: `scripts/build3_source_registry_extend.py` — `--dry-run` / `--undo` (backup `data/lineage_backup_t77.db`).
- Idempotent (chạy lại không đổi), reversible (undo khôi phục backup), live API vẫn 200 sau khi ALTER.

### 2. Adapter skeleton — `adapters/`
- `adapters/__init__.py` — package doc.
- `adapters/base.py` — `SourceAdapter` (ABC) + `ExtractedEvidence` (provenance chuẩn) + `to_json`.
- `adapters/registry.py` — `SourceAdapterRegistry`: nạp data-driven từ `data_sources.capabilities`; dispatch theo source_code.
- `adapters/bdrc/__init__.py` — adapter mẫu (BDRC, health=`conector_only`, KHÔNG harvester thật).
- Smoke test pass: registry nhận 13 nguồn, BDRC has_adapter=True, SAT dispatch raises KeyError (chưa có adapter).

### 3. Tài liệu (3 file gộp, tránh duplicate)
- `docs/BUILD1_AUDIT.md` — gap map Build 1 → future-source-ready (mở rộng build1_inventory).
- `docs/SOURCE_INTEGRATION_ARCHITECTURE.md` — kiến trúc 2 giai đoạn + lock-in hiện tại.
- `docs/SOURCE_ONBOARDING.md` — lifecycle thêm nguồn + checklist acceptance A–I.

## Subtasks
- [x] T77a: `scripts/build3_source_registry_extend.py` (ALTER additive + backfill + backup, --undo) — đã chạy + idempotent + live API OK
- [x] T77b: `adapters/base.py` contract (SourceAdapter + ExtractedEvidence)
- [x] T77c: `adapters/registry.py` (data-driven dispatch)
- [x] T77d: `adapters/bdrc/__init__.py` adapter mẫu skeleton
- [x] T77e: smoke test (registry 13 nguồn, BDRC có adapter, SAT chưa có)
- [x] T77f: 3 doc gộp (BUILD1_AUDIT / SOURCE_INTEGRATION_ARCHITECTURE / SOURCE_ONBOARDING)
- [x] T77g: py_compile + lint OK

## Revert / Rollback
- DB ALTER: `python scripts/build3_source_registry_extend.py --undo` (khôi phục `data/lineage_backup_t77.db`).
- Adapter/docs: git revert (các file mới, atomic commit riêng).
- Không đụng canonical core; bất kỳ fix sau đều commit-back dễ bằng git.
