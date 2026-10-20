# Session 2026-09-22 — T132 P2-P8: Authority Contract Completion

**Date:** 2026-09-22  
**Task:** T132 — B2.5 REFINE: Trusted Source Registry + Legal/Capability Contract  
**Scope:** P2–P8 (P1 đã commit `6cdc2e9` phiên trước)  
**Status:** DONE — 17/17 tests PASS, pipeline wired

---

## Tóm tắt công việc

### P2 — LicenseGate wrappers (§11)
**File:** `gate/license.py`  
Thêm 2 method vào `LicenseGate`:
- `can_display(source_id)` → `checkSourcePermission(source_id, 'READ_METADATA')`
- `can_quote(source_id)` → `checkSourcePermission(source_id, 'DERIVE')`

### P3 — SourceAdapter + ExtractedEvidence extensions (§6 §12)
**File:** `adapters/base.py`  
- `ExtractedEvidence`: thêm 3 fields: `license`, `license_status`, `source_version` (default None)
- `SourceAdapter`: thêm 3 default methods: `lookup_entity()`, `get_identifier()`, `get_license()`

### P4 — Evidence Graph Contract doc (§7)
**File:** `docs/EVIDENCE_GRAPH_CONTRACT.md` (mới)  
Map entity_claims columns ↔ spec §7, non-overwrite rules, backfill policy

### P5 — ConflictRecorder (§9)
**File:** `gate/conflict_recorder.py` (mới)  
`ConflictRecorder.record()` + `record_many()` — INSERT với SELECT-first duplicate check  
(conflict_pending thiếu UNIQUE constraint → không dùng INSERT OR IGNORE)

### P6 — Conformance docs (§15)
4 file mới, tất cả thin (pointer không duplicate):
- `docs/B1_ALREADY_EXISTS.md`
- `docs/B2_5_TRUSTED_SOURCE_REGISTRY.md`
- `docs/SOURCE_INTEGRATION_CONTRACT.md`
- `docs/LICENSE_POLICY.md`

### P7 — Tests (§13, A–J + extras)
**File:** `tests/test_b25_authority_contract.py` (mới)  
17 tests, dùng DB copy thật (temp file, xóa sau test):
```
17 passed in 15.49s
```
Cases: A (DILA claims) · B (multi-source) · C (UNKNOWN blocked) · D (conflicts exist)  
· E (license NULL) · F (unknown source_id) · G (dup claims) · H (2-source no merge)  
· I (adapter health_unknown + REVIEW_REQUIRED) · J (source_version NULL)  
+ P2 can_display/can_quote · P3 ExtractedEvidence fields

### P8 — Pipeline + docs + dashboard
- `package.json`: thêm `test:gov` script + wire vào pipeline
- `docs/tasktodo.md`: T132 status → ✅ DONE
- `tasks/T132-b25-trusted-source-conformance.md`: status → done, updated → 2026-09-22
- Dashboard rebuild: `python scripts/build_progress_data.py`
- Commit: `feat: T132 P2-P8 — authority contract completion`

---

## Files thay đổi

| File | Loại |
|------|------|
| `gate/license.py` | Modified (+can_display/can_quote) |
| `gate/conflict_recorder.py` | New |
| `adapters/base.py` | Modified (+3 fields ExtractedEvidence, +3 methods SourceAdapter) |
| `docs/EVIDENCE_GRAPH_CONTRACT.md` | New |
| `docs/B1_ALREADY_EXISTS.md` | New |
| `docs/B2_5_TRUSTED_SOURCE_REGISTRY.md` | New |
| `docs/SOURCE_INTEGRATION_CONTRACT.md` | New |
| `docs/LICENSE_POLICY.md` | New |
| `tests/test_b25_authority_contract.py` | New |
| `package.json` | Modified (+test:gov, pipeline) |
| `docs/tasktodo.md` | Modified |
| `tasks/T132-b25-trusted-source-conformance.md` | Modified |

---

## Verify

```
npm run test:gov → 17 passed in 15.49s ✅
```

---

## Rollback

`git revert <commit-T132-P2-P8>` — hoàn nguyên tất cả files trên.  
P1 (DB schema) đã committed riêng `6cdc2e9` — revert riêng nếu cần.

---

## Addendum 2026-09-22 (late) — P5 seed thật + P8 backups + pipeline

### P5 — Seed `conflict_pending` từ data THẬT (spec §9, "ghi nguồn — KHÔNG fake")
- **Script:** `scripts/seed_t132_conflict_pending.py` (mới) — modes `--stats / --apply [--limit N] / --revert`.
- Nguồn seed: `namevi_map_places.needs_review=1` (place-mapping chờ duyệt thật) — **18,165 ứng viên**, chọn deterministic 20 dòng đầu theo `id`.
- Ánh xạ mỗi dòng:
  - `entity_ref` = `dila_id` (PL…) · `field` = `name_vi`
  - `value_a` = `name_zh` · `source_a` = source_code theo `data_sources` (JOIN source_id → **DILA**)
  - `value_b` = `name_vi` (ứng viên transliteration) · `source_b` = `ZQLOCAL` (sinh tại chỗ)
  - provenance đầy đủ trong **`notes`**: `namevi_map_places id=<id> confidence=<c> method=auto_transliterate needs_review=1 (T132 P5 seed)`
- `conflict_pending` thiếu cột provenance → `ALTER TABLE ADD COLUMN notes TEXT` (additive, nullable) — idempotent; code `ConflictRecorder` đã dự sẵn nhánh `'notes' in cols`.
- **Kết quả thật:** 0 → **20 rows**, `status='pending'`, `needs_review=1`, `resolved_by/resolved_at=NULL`. Idempotent: chạy lại → 0 INSERT mới. Vòng đời đã validate: `--stats → --apply(20) → --revert(20) → --apply(20)`.
- **Rollback seed:** `python scripts/seed_t132_conflict_pending.py --revert` (xóa qua marker, cột `notes` giữ nguyên — 0 DROP).
- Lineage conflicts (lineage_conflicts_v2) KHÔNG đụng — đúng non-goal.

### P8 — Backups (pre-seed state)
- Code `.bak-t132-20260922` (4 file, snapshot trước seed): `gate/license.py`, `gate/status.py`, `adapters/base.py`, `app.py` → `docs/sessions/`.
- DB: `data/lineage_backup_t132.db` (**1,372 MB**, sqlite online backup, verified 14 sources / conflict_pending=0 pre-seed) — **gitignored** (data/), chỉ local rollback target.

### Pipeline 2026-09-22 (tester agent)
- `guard` ✅ · `lint` ✅ · `test` ✅ · `test:uat` ✅ 3/3 · `test:compliance` ⚠️ 7 pass / 2 fail (pre-existing: `claims_assertion_level 0%`, `conflicts_resolved 0%` — 0.00% đúng vì seed mới 20 pending chưa resolve) · `test:gov` ✅ **17/17** · `e2e` ✅ · `e2e:runtime` ❌ **EPERM: unlink `test-results/.last-run.json`** — file bị khóa bởi process/antivirus môi trường, **không phải lỗi code** (ghi nhận theo convention pre-existing; retry 5× vẫn locked).

### Commits cho phần này (mỗi pha 1 commit để revert riêng)
- `feat: ... T132 P5 seed ...` — `scripts/seed_t132_conflict_pending.py` (+ docs addendum này)
- `chore: ... T132 P8 ...` — 4 file `.bak-t132-20260922`
- `docs: ... T132 closure ...` — tasktodo.md + tasks/T132 (status đã done)

⚠ Ghi chú: `app.py` hiện có guard `if __name__ == '__main__':` — KHÔNG phải của T132; đã được `a1c0c16 fix: BUG-023` (agent khác) commit riêng.

---

## T157 B-4 — Tab lineage Profile DILA-axis (Session addendum 2026-09-22)

### Thay đổi

**Backend (`app.py`):** Endpoint mới `GET /daoanh/api/person/<person_id>/dila-axis`
- Query `lineage_edge_assertions` source_code='DILA' theo 2 chiều:
  - `subject_person_id=pid` (pid là thầy) → `students[]`
  - `object_person_id=pid` (pid là trò) → `teachers[]`
- GROUP BY để deduplicate, JOIN với `people` để lấy tên
- Trả về: `{ok, person_id, teachers[], students[]}` với fields: `{id, name_zh, name_vi, trust_level, mapping_verified}`

**Frontend (`places.html`):** Section "Truyền Thừa (DILA L2)" trong inspector evidence
- Thêm `<div id="lin-dila-axis"></div>` sau `lin-dila-extra` trong `_renderLineageInspector`
- `_loadDilaAxis(pid)` — lazy fetch với race guard `_dilaAxisPid`
- `_renderDilaAxis(container, d)` — hiển thị Thầy/Đệ tử với tên Việt, tên Hán, DILA ID, ✓L2 badge, click centerLineageOn

### Verify (2026-09-22)

```
API GET /daoanh/api/person/A004177/dila-axis
→ teachers: 2 (Đại Lượng A010825 ✓L2, Tông Sư Hòa Thượng/法慎 A009590 ✓L2)
→ students: 12 (Thường Chiếu, Chiêu Lượng, Pháp Tuấn, ...) ✓L2

lin-dila-axis.innerText:
"TRUYỀN THỪA (DILA L2)
Nguồn: lineage_edge_assertions · chiều chuẩn hóa 2026-09-17 (B-1)
THẦY THEO DILA (2): Đại Lượng 大亮 DILA ID: A010825 ✓L2 / Tông Sư Hòa Thượng 法慎 A009590 ✓L2
ĐỆ TỬ THEO DILA (12): Thường Chiếu 常照 A004179 ✓L2 / ..."

py_compile app.py → OK
node --check places.html → 3 blocks OK
```

### Backups
- `docs/sessions/app.py.bak-t157-b4-20260922`
- `docs/sessions/places.html.bak-t157-b4-20260922`

### Revert
`git revert --no-edit b1d364e` (app.py + places.html)
