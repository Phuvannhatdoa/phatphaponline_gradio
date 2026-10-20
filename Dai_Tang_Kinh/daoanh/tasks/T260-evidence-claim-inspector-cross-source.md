---
id: T260
title: "Evidence Claim Inspector — Cross-Source Claim Grouping & Conflict Signal"
status: done
priority: high
created: "2026-10-08"
completed: "2026-10-08"
tags: [evidence, claims, inspector, cross-source, t259-extension, read-only]
depends_on: [T259]
blocks: []
former_ids: []
---

# T260 — Evidence Claim Inspector (Cross-Source)

**Code:** `T260-EVIDENCE-CLAIM-INSPECTOR-CROSS-SOURCE-01`  
**Mở rộng:** T259 "Bằng Chứng & Nguồn Gốc" — thêm toggle Đối chiếu / Chi tiết  
**HEAD baseline:** a1b7a50 (T259 commit)  
**Nguyên tắc:** READ-ONLY · ZERO DB mutation · ZERO schema change · ZERO external LLM

---

## Phase 0 — Contract Inspection

### Dữ liệu thực A001897

| Trường | Giá trị |
|--------|---------|
| canonical_label | A001897 |
| entity_id (entity_hub) | 220093 |
| Số claims | 34 (32 lineage_teacher + 2 lineage_student) |
| source_code | MARCUS (duy nhất — source_id=4) |
| verification_status | unverified (100% PERSON claims) |
| source_reference format | T69:marcus:A001897:A000490 (4 segment) |
| lineage_conflicts_v2 | 1 row: student_set, DILA=33, MARCUS=32, dila_only=['A046466'] |

### Grouping key

```
(predicate, object_dila_id)
object_dila_id = source_reference.split(':')[-1]
                 CHỈ KHI format khớp: T69:marcus:{subject}:{object} (4 phần, cuối = A\d{6})
```

### CASE B

- PERSON claims chỉ có MARCUS (không cross-source agreement trong entity_claims)
- Conflict signal từ `lineage_conflicts_v2` (governed semantics) → thêm `lineage_conflicts` field vào evidence API
- Additive READ-ONLY query: `WHERE person_id=? AND is_conflict=1 AND resolved=0`

---

## Triển khai

### Backend — `app.py`

Thêm vào `api_evidence()` trước `conn.close()`:

```python
# T260 — lineage conflict signal (READ-ONLY, governed semantics)
lineage_conflicts = []
if ref:
    try:
        lc_rows = conn.execute(
            "SELECT conflict_type, dila_count, marcus_count, dila_data, marcus_data "
            "FROM lineage_conflicts_v2 WHERE person_id=? AND is_conflict=1 AND resolved=0",
            (ref,)
        ).fetchall()
        for r in lc_rows:
            dila_ids = json.loads(r["dila_data"] or "[]")
            marcus_ids = json.loads(r["marcus_data"] or "[]")
            lineage_conflicts.append({
                "conflict_type": r["conflict_type"],
                "dila_count": r["dila_count"],
                "marcus_count": r["marcus_count"],
                "dila_only": sorted(set(dila_ids) - set(marcus_ids)),
                "marcus_only": sorted(set(marcus_ids) - set(dila_ids)),
            })
    except Exception:
        pass  # bảng không tồn tại → trả list rỗng
```

Return JSON thêm field: `"lineage_conflicts": lineage_conflicts`

### Frontend — `places.html`

**DOM:** `#entityEvidenceToggle` div (đã có từ T260 build)

**JS mới (sau End T259):**

- `_evData = null` — cache payload
- `_evMode = 'grouped'` — default view
- `_parseObjId(ref)` — extract object DILA ID (4-segment guard)
- `_setEvMode(mode)` — toggle handler
- `_renderEvBlock(d)` — render based on `_evMode`
- `_buildGroupedHtml(d)` — T260: assertion cards + conflict signal
- `_buildRawHtml(d)` — T259: raw detail view (preserved)
- `_assertionCard(g)` — single assertion card với provenance `<details>`
- `loadEntityEvidence()` — mở rộng: store `_evData`, call `_renderEvBlock()`

**Toggle UI:**

```
[ 🔬 Đối chiếu ]  [ 📋 Chi tiết ]
```

---

## Constraint cứng

| Ràng buộc | Trạng thái |
|-----------|-----------|
| READ-ONLY, zero DB write | ✅ |
| source_reference = TEXT, không URL | ✅ |
| Nhóm deterministic: (predicate, object_dila_id) | ✅ |
| KHÔNG fuzzy/semantic/LLM | ✅ |
| Source independence: 5 MARCUS rows = 1 nguồn | ✅ |
| Conflict CHỈ từ lineage_conflicts_v2 | ✅ |
| KHÔNG write action, KHÔNG approve/reject button | ✅ |
| T259 raw view vẫn accessible | ✅ |
| KHÔNG đụng T139/T140/T181/T223 | ✅ |
| KHÔNG integrate T236 (no cbeta_person_mentions) | ✅ |
| T165-P8 GOVERNANCE HOLD — không đụng | ✅ |

---

## Tests

File: `tests/test_t260_evidence_claim_inspector.py`

| Test | Mô tả |
|------|-------|
| A | Identical assertions grouped deterministically |
| B | Different canonical objects not merged |
| C | Missing object_id → no unsafe merge |
| D | Repeated rows from one source = one source |
| E | Distinct sources counted correctly |
| F | source_count != record_count |
| G | Verification states preserved |
| H | Agreement does not auto-verify |
| I | Unknown verification state preserved |
| J | Unknown claim_type preserved |
| K | source_reference remains plain text |
| L | No guessed URL |
| M | Underlying records expandable |
| N | Bounded rendering |
| O | Race guard logic |
| P | XSS escaping |
| Q | Zero DB mutation |
| R | Zero schema mutation |
| S | Zero external API/LLM |
| T | T259 raw evidence remains accessible |
| U | Only governed conflicts trigger badge |
| V | Multiple legitimate values not auto-conflicts |
| real_db_A001897 | Real DB regression (skipif no DB) |
| real_db_conflicts | lineage_conflicts_v2 regression |
| real_db_zero_write | Zero write after evidence read |
| ast_guard | app.py AST parse valid |

---

## Revert

```bash
# Revert code (git plumbing commit)
git revert --no-edit <T260_COMMIT_SHA>

# Không có DB mutation → không cần revert DB
```

---

## Rollback SHA

| Pass | SHA |
|------|-----|
| T260 plumbing commit | 7bf11c8ae5e8ec41a41cee7a1271654e14e341b1 |
