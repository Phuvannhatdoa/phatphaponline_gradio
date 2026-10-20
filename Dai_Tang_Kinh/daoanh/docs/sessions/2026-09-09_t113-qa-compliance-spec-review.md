# Session — Rà đặc tả "System QA & Compliance UAT" (ĐÃ PHỦ + 2 delta → T118)

**Ngày:** 2026-09-09 · **Commit:** `04c8e1a`

## Bối cảnh
Lee gửi đặc tả tiêu đề **"Task T119: System QA & Compliance"**; bên trong ghi **"ĐẶC TẢ KHÁI NIỆM
T117"** và lệnh gọi **"Task T117: System QA & Compliance"**; bảng STATUS đề **T116=Curation Done →
nhầm** (T116 = System Registry docs-only; Curation = T109/T119). Yêu cầu tạo `QA_COMPLIANCE_SPEC.md`
+ update `PROJECT_STATUS.md` (= lặp lỗi SSOT, đã có quyết định A2 không tạo file trùng).

## Kết luận (read-only, verified)
**"System QA & Compliance (Khảo khóa)" = task T113 (in_progress).** Mọi cấu phần đã xây:

| Đặc tả | Hiện trạng |
|---|---|
| `scripts/verify_design_compliance.py` → `data/design_compliance.json` | ✅ EXISTS (Phần B · read_only=True · 2026-09-09) |
| KPI (source/reviewed/conflict) | ✅ 9 metric M7.2 (`claims_with_source` 100% · `claims_reviewed` 0% fail · `conflicts_resolved` 0.01% warn · `with_audit` 100% · `events_provenance` 100% · `glossary_vi` 75.54%) |
| Dashboard Data Quality | ✅ `dashboard_process.html` |
| UAT 3 persona (Tứ Diệu Đế / Tiến sĩ / Negative) | ✅ Phần A QA live 7 probe (doctrine 12 · L1–L3 · evidence provenance · negative honest Việt) |
| Citation BibTeX | ✅ `places.html` `dtCopyCite('bibtex')` `@incollection` + 'chicago' |
| Failure criteria (No Source / conflict admin-only / Unverified→L1) | ✅ kiến trúc ép buộc |

### 2 delta (thuộc T118, Track 2 — không phải lỗi)
1. **CSL-JSON citation export KHÔNG tồn tại** (0 khắp repo); BibTeX tối giản (ref_code, không full metadata).
2. **Audit ID public** chưa có (`entity_claims_audit.audit_id` admin-only) — đã ghi nhận tại T117 rà.

## Cam kết
- KHÔNG tạo `QA_COMPLIANCE_SPEC.md` (A2 có sẵn: SSOT = SCHEMA_DESIGN M7.2).
- KHÔNG re-open T113/T117/T119; không tạo task mới (delta nằm trong T118).
- Không tạo `PROJECT_STATUS.md` (SSOT = tasktodo/roadmap).

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T113-qa-uat-compliance-meter.md` — mục "Rà đặc tả System QA & Compliance UAT".
2. `tasks/T118-research-audit-tier-api.md` — mở rộng deliverable: CSL-JSON export + BibTeX chuẩn + `?raw=1` tái lập.
3. `docs/ROADMAP_META_UPDATE.md` §5 — luật QA/Compliance = T113; CSL-JSON/audit → T118.
4. `docs/tasktodo.md` — `ráspec3` ở T113.
5. `docs/ROLLBACK.md` — row `04c8e1a`.
6. Session này.

## Rollback
- `git revert --no-edit 04c8e1a` (docs-only, 0 DB).