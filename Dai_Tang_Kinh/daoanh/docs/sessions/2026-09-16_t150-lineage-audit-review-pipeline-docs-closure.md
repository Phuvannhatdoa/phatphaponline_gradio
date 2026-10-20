# Session — T150 Lineage Integrity & Review Pipeline — Docs Closure (2026-09-16)

> **Canonical docs closure — additive · docs-only · 0 code · 0 DB · 0 ALTER · 0 Schema · 0 ALTER TABLE · mirror chuẩn T148/T149/T147/T146 (1 task = 1 commit, mirror 4-trụ SSOT).**
> Frame: `docs/sessions/2026-09-16_t149-session.md` (canonical T149 — add docs → regen real → hash-fill real 2-pass → 0 leftover → verify). 0 leftover, 0 gõ hash tay.

---

## 1. Bối cảnh

T149 (import name_zh bug fix — 28,273 rows real DONE + browser verified) đã phát hiện hệ quả cần pipeline: **28,273 name_vi sai do phiên âm từ name_zh sai** → cần re-seed (tracked T150 tracking) + **nhu cầu lineage integrity được ZQ review bảo vệ** (không tự sửa lỗi chiều/thiếu mắt xích/gộp nhầm đồng tên/nhiều nguồn mâu thuẫn).

T148 (DILA Full Inspector) + T147 (Person Index) đã map đủ người **→ nền tảng đã có đồng nhất entity** — giờ xây **audit + review pipeline** để mọi cạnh mới NHẬP chỉ khi đã ZQ duyệt.

## 2. Closure này (additive, docs-only)

| Trụ SSOT | File | Trạng thái |
|----------|------|-----------|
| Canonical task | `tasks/T150-lineage-audit-review-pipeline.md` | **1 unique** ✓ |
| Canonical session | `docs/sessions/2026-09-16_t150-lineage-audit-review-pipeline-docs-closure.md` | **1 unique** ✓ (file này) |
| tasktodo row | `docs/tasktodo.md` T150 | **DONE** ✓ |
| ROLLBACK row | `docs/ROLLBACK.md` T150 | hash-fill real 2-pass (placeholder → real `git rev-parse`) • xem `docs/ROLLBACK.md` |
| Dashboard | `data/progress_data.json` | regen real `build_progress_data.py` ✓ |
| Dashboard json | `data/progress_data.json` | T150 = 3 visible real ✓ |
| Leftover | scripts/ `*t150*` | **0 cleaned** ✓ |

## 3. CSDL thiết kế (docs-only — BẢNG MỚI additive đề xuất, KHÔNG tạo DB lúc này)

Thiết kế SSOT đã mô tả đầy đủ trong canonical task. Chốt add (docs closure):

- Bảng `lineage_relation_source` — assertion raw từng nguồn (DILA/Marcus/Zen/CBETA), additive, 0 ALTER.
- Bảng `lineage_relation_evidence` — locator + excerpt + bản dịch + citation.
- Bảng `lineage_relation_review` (ZQ decision, additive) — `decision ∈ verified|provisional|disputed|rejected|unresolved`.
- View `published_lineage_relation` — additive read-only view.
- Bảng `lineage_audit_issue` — 8 loại: self_loop · reverse_pair · source_conflict · skipped_generation · unresolved_entity · cycle · missing_provenance · weak_evidence.

## 4. Verify REAL (4-trụ SSOT)

```
task T150 (glob real) = 1 · session T150 = 1 · tasktodo T150 = 1 · ROLLBACK T150 = 1 (placeholder=0, hash-fill real) · json T150 = 3 visible real
```

## 5. Revert

```bash
git revert --no-edit <sha_closure_T150>
```
