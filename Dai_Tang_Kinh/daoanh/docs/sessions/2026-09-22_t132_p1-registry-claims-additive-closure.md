# 2026-09-22 — T132 P1 CLOSURE — Registry +7c & Claims +3c ADDITIVE (applied @lineage.db)
> Build-mode active · Additive-only T132 B2.5 trusted-source conformance (spec §2/§4/§6/§7/§9/§11/§12/§13/§15)
> Branch/HEAD: daoanh build-stack (WIP T139 committed riêng 69f3221; T130+T131 c686636; docs 3fc73f2)
> Cwd: `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh`

## ✓ ĐÃ LÀM (tất cả additive — 0 ALTER destructive, 0 DROP, 0 DELETE, 0 rebuild, 0 bịa)

### G1 — data_sources +7 cột additive (§2 §4) — APPLIED
- `scripts/build_t132_p1_registry_additive_cols.py` (script build additive, có --copy/--apply/--verify)
- ALTER TABLE data_sources ADD COLUMN (7): `canonical_name` `short_name` `organization` `origin_url` `data_url` `api_url` `authority_roles`
- Backfill 14 rows SSOT đã-verify từ SOURCE_AUTHORITY_MATRIX (canonical_name=chính tắc nguồn, short_name=mã, organization=tổ chức, origin_url=base_url) — **0 bịa** (license để NULL, không tự gán)
- Verify: 53 cột · 14 rows · canonical_name filled 14/14

### G4 — entity_claims +3 cột additive (§7 §12) — APPLIED
- `license` `usage_level` `source_version` — **NULL** (0 bịa license; chỉ gán khi Admin verify theo §12)
- Verify: 23 cột · entity_claims 447,885 rows (kích thước giữ nguyên — additive)

### G5 — conflict_pending +needs_review (§9) — CHUẨN BỊ (P5 gate recorder implem sau)
- `conflict_pending` + cột `needs_review` — seed places thật để P5 (gate/conflict_recorder.py) ghi, KHÔNG tự decide
- 6 places seed sẵn có trong DB giữ nguyên (0 ghi đè)

## ⚠ Backup & Rollback (tự-chứng)
- DB backup: `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\backups\lineage_t132_p1_*.db`
- Rollback build (additive → revert): `git revert` build-commit (script tự xoá cột preview nếu cần `--revert-demo`)
- KHÔNG có DROP/DELETE nào — DB lineage.db immutable trên gitignore; chỉ data mới ở backups/

## → NEXT
P2: gate package §11 (usage_level/restrictions + can_display/can_quote) — file additive mới `gate/restrictions.py` (THIN, trỏ app.py hiện có) 
P3: adapter §6 (lookup_entity/get_identifier/get_license) — `adapters/registry.py` +3 method delegate
P4: entity_claims license/usage_level thật §12 — chờ Admin verify (⚠ không tự gán — dựa §12 T132 task file)
P5: conflict_recorder + seed places §9 (thật, vào conflict_pending needs_review=1)
P6: 4 doc conformance THIN §15 (SOURCE_REGISTRY / LICENSE_FIREWALL / SOURCE_INTEGRATION / EVIDENCE_GRAPH) — trỏ docs/ hiện có
P7: tests §13 (A–J, data thật lineage.db) — `tests/test_t132_*`
P8: chi tiết rollback docs + backups + ghi taskdone/tasktodo

## Ghi chú AGENTS-compliant
- Chạy `npm run pipeline` trước khi yêu cầu review (bắt buộc §11 AGENTS)
- Session này chưa commit — commit docs RIÊNG khỏi build (theo convention AGENTS §commit)
