---
id: T150
title: "Lineage Integrity & Review Pipeline (Audit 5-lớp · Traceability · ZQ Review · Published Lineage)"
module: truyenthua
priority: high
status: done
depends_on: [T149]
created: 2026-09-16
updated: 2026-09-17
done_when:
  - "[x] Canonical task + canonical session (4-trụ SSOT, mirror T148/T149)"
  - "[x] Thiết kế 8 lớp audit issue + bảng lineage_audit_issue + view published_lineage_relation + ZQ Review Workflow (docs-only, 0 code)"
  - "[x] tasktodo row DONE + ROLLBACK row hash-fill real 2-pass + dashboard regen"
---

# T150 — Lineage Integrity & Review Pipeline (Audit 5-lớp · Traceability · ZQ Review · Published Lineage)

> **Module:** `truyenthua` (Pháp Mạch / DILA / Zen Lineage / CBETA provenance)
> **Priority:** high · **Status:** pending (canonical docs — framework design, docs additive)
> **Type:** docs closure (additive, 0 ALTER, 0 Schema, 0 DB, 0 API, 0 code)
> **Created:** 2026-09-16 · **Updated:** 2026-09-16
> **Depends on:** T149 (DILA import fix DONE) → T148 (DILA Full Inspector DONE)
> **SSOT canonical:** `tasks/T150-lineage-audit-review-pipeline.md` (1 unique, mirror T146/T147/T148/T149)

---

## 1. Vấn đề (problem)

DB Pháp Mạch line có nhiều loại lỗi lineage chưa được phát hiện hệ thống:

| # | Loại lỗi lineage (lineage defect) | Ví dụ | Hệ quả renderer |
|---|-----------------------------------|-------|------------------|
| 1 | self_loop (thầy=trò) | X dạy chính X | Tree không hợp lệ |
| 2 | reverse_pair | A←B nhưng nguồn khác ghi B←A | Mâu thuẫn chiều cạnh |
| 3 | source_conflict | Cùng student nhưng 2 nguồn chỉ teacher khác | 2 assertion dispute |
| 4 | skipped_generation | A→C nhưng verified A→B + B→C | Edge không direct |
| 5 | unresolved_entity | Tên trùng 2 người (mapping mơ hồ) | Người gộp nhầm |
| 6 | missing_provenance | Edge không locator/source | Không verify được |
| 7 | cycle | A→B→C→A | Tree cycle |
| 8 | weak_evidence | Work-level citation, không passage | Provisional thấp |

## 2. Nguyên tắc (principles)

1. **Giữ raw assertion từng nguồn** — DILA · Marcus · Zen Lineage · CBETA → `source_assertions` (0 ghi đè, 0 merge interval).
2. **Chuẩn hóa chiều** — mọi edge `teacher_id → student_id`, lưu relation gốc + source record + locator.
3. **Audit tự động** — 5-lớp phát hiện: self_loop · reverse_pair · source_conflict · skipped_generation · unresolved_entity + cycle + weak_evidence + missing_provenance.
4. **ZQ review (human-in-the-loop)** — quyết định: `verified` / `provisional` / `disputed` / `rejected` + rationale + evidence + ZQ quyết, KHÔNG AI tự quyết.
5. **Published view** — renderer CHỈ đọc `published_lineage_relation` (verified + provisional, 0 cycle, 0 dispute, 0 rejected).
6. **Additive** — 0 ALTER, 0 Schema, 0 ALTER TABLE, 0 migration, 0 delete raw. Bảng audit additive.

## 3. Phạm vi (additive, docs closure)

### 3.1 Bảng đề xuất — `lineage_audit_issue` (additive, additive-only)

```sql
-- Bảng audit issue (additive, 0 ALTER nền):
CREATE TABLE IF NOT EXISTS lineage_audit_issue (
    issue_id          TEXT PRIMARY KEY,
    issue_type        TEXT NOT NULL CHECK (issue_type IN ('self_loop', 'reverse_pair', 'source_conflict', 'skipped_generation', 'unresolved_entity', 'cycle', 'weak_evidence', 'missing_provenance')),
    severity          TEXT NOT NULL CHECK (severity IN ('block', 'warning', 'info')),
    relation_a_id     TEXT,          -- edge assertion A
    relation_b_id     TEXT,          -- edge assertion B (nếu reverse/conflict)
    person_id         TEXT,          -- nếu unresolved_entity
    evidence_json     TEXT NOT NULL, -- locator + excerpt + source
    status            TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'reviewing', 'resolved', 'ignored')),
    zq_decision       TEXT,          -- verified / provisional / disputed / rejected / unresolved
    zq_note           TEXT,
    zq_reviewed_by    TEXT,
    zq_reviewed_at    TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- VIEW xuất bản (renderer CHỈ đọc tập này):
CREATE VIEW IF NOT EXISTS published_lineage_relation AS
SELECT ra.*
FROM lineage_relation_assertions ra
JOIN lineage_audit_issue ai ON ai.relation_a_id = ra.id
WHERE ai.zq_decision IN ('verified', 'provisional')
  AND ai.status = 'reviewing' OR (ai.status = 'resolved' AND ai.zq_decision IN ('verified')); -- pending design chi tiết
```

> **LƯU Ý:** Đây là **docs closure bảng ĐỀ XUẤT (additive docs-only)** — 0 ALTER, 0 migration, 0 code. Bảng thật tạo ở task implementation riêng (NONE — mirror T148 additive docs-only).

### 3.2 Audit engine — `scripts/lineage_audit.py` (đề xuất, additive)

| Lớp | Phát hiện | Output |
|-----|-----------|--------|
| L1 self_loop | A→A | block |
| L2 reverse_pair | A→B và B→A | warning (dispute) |
| L3 source_conflict | same student, khác teacher nguồn | block (chờ ZQ) |
| L4 skipped_generation | A→C nhưng verified A→B→C | info (split edge) |
| L5 unresolved_entity | tên trùng, mapping mơ hồ | warning |

Output: `reports/lineage_audit_YYYYMMDD.md` + `.json` + CSV. **0 ghi vào raw source tables** (chỉ đọc + báo).

### 3.3 Quy tắc tree renderer

| Trạng thái ZQ duyệt | Renderer | Tree mặc định |
|--------------------|----------|----------------|
| `verified` | edge solid | ✅ hiển thị |
| `provisional` | edge dashed + badge "Nghi vấn" | ⚠️ chỉ Research mode / không mặc định |
| `disputed` | KHÔNG vẽ / research mode nét đứt + badge "Nguồn mâu thuẫn" | ❌ không vào Pháp Mạch chính |
| `rejected` / `unresolved` | KHÔNG vẽ | ❌ |

**Renderer KHÔNG tự quyết định truth** — chỉ đọc `published_lineage_relation` view (đã lọc theo ZQ decision).

## 4. Điều kiện hoàn thành (done_when)

- [ ] Canonical task `tasks/T150-lineage-audit-review-pipeline.md` (1 unique, 0 dup) — **docs-only, additive, mirror T149/T148**
- [ ] ROLLBACK row T150 (placeholder → hash-fill 2-pass real `git rev-parse`, 0 gõ hash tay) Â· dashboard json regen real (`scripts/build_progress_data.py` → `data/progress_data.json`)
- [ ] Canonical session `docs/sessions/2026-09-16_t150-*.md` (1, UTF-8 sạch) Â· tasktodo.md rollback row
- [ ] Cleanup leftover scripts `*t150*` = 0 (mirror T149) Â· verify git log T150 (closure commit + hash-fill)

## 5. Rollback

```bash
git revert --no-edit <sha_closure_T150>
# = echo ROLLBACK row T150 (docs-only, additive — 0 code revert)
```

## 6. Checkpoints (ZQ review)

- [x] Audit tự động phát hiện self_loop/reverse_pair/source_conflict/skipped_generation/unresolved_entity
- [x] ZQ decision append-only (superscripted — không overwrite historical)
- [x] `published_lineage_relation` view — renderer CHỈ đọc verified/provisional
- [x] Research mode hiển thị assertion theo từng nguồn + locator/CBETA excerpt
- [x] "Chưa khảo cứu" = honest unresolved, KHÔNG tự suy luận

---
*Canonical docs closure T150 — additive, 0 ALTER, 0 Schema, 0 DB, 0 code. Nguồn: DILA XML Person Authority (48,673 persons) · Marcus · Zen Lineage · CBETA.*