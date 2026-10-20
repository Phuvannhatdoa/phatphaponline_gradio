---
id: T261
title: "Marcus Object Label Enrichment — Hi Vận (希運) trong assertion cards"
status: done
priority: high
created: "2026-10-08"
completed: "2026-10-08"
tags: [evidence, marcus, label, enrichment, t260-extension, read-only]
depends_on: [T260]
blocks: []
former_ids: []
---

# T261 — Marcus Object Label Enrichment

**Mở rộng:** T260 `_assertionCard()` — hiển thị tên người thay vì DILA ID opaque  
**HEAD baseline:** 7bf11c8 (T260 commit)  
**Nguyên tắc:** READ-ONLY · ZERO DB mutation · ZERO schema change · ZERO external LLM

---

## Phase 0 — Join Contract

| Kiểm tra | Kết quả |
|----------|---------|
| `marcus_reference` PK | `node_id TEXT PRIMARY KEY` (unique, 0 duplicate) |
| source_reference format | `T69:marcus:A######:A######` (26 chars, 22332/22332) |
| Subject = SUBSTR(ref,12,7) | Verified: 0 mismatch vs canonical_label |
| Object = SUBSTR(ref,-7) | Verified: 22332/22332 match xác định |
| Join cardinality | 22332 resolved, 0 unresolved, 0 duplicate |
| Field conflicts | Không có `object_label_zh`/`object_label_vi` trong app.py |

**Join key chính xác:** `mr.node_id = SUBSTR(c.source_reference, -7)`  
**Guard điều kiện:** `c.source_id = 4 AND c.source_reference LIKE 'T69:marcus:_______:_______'`

---

## Triển khai

### Backend — `app.py` (api_evidence)

Thêm LEFT JOIN vào claim SELECT:

```python
LEFT JOIN marcus_reference mr
    ON c.source_id = 4
    AND c.source_reference LIKE 'T69:marcus:_______:_______'
    AND mr.node_id = SUBSTR(c.source_reference, -7)
```

Thêm fields vào SELECT: `mr.label AS object_label_zh, mr.label_vi AS object_label_vi`

Thêm vào claim dict: `"object_label_zh": c["object_label_zh"], "object_label_vi": c["object_label_vi"]`

Existing fields không thay đổi: `claim_id, predicate, object_text, source_reference, verification_status, source_id, claim_type`

### Frontend — `places.html` (_assertionCard)

Thêm `_getObjLabels(g)` — lấy label từ first record có labels.

Fallback order:

1. `VI_ZH` — vi + zh (khi vi ≠ zh): `Hi Vận 希運 A000490`
2. `VI_ONLY` — chỉ vi: `Hi Vận A000490`
3. `ZH_ONLY` — chỉ zh: `希運 A000490`
4. `ID_ONLY` — chỉ ID: `A000490`

DILA ID luôn visible dưới dạng monospace. Tất cả qua `_escHtml()`.

---

## A001897 Real Data Verification

| Metric | Giá trị |
|--------|---------|
| Claim count before | 34 |
| Claim count after | 34 (unchanged) |
| Grouped assertions before | 34 |
| Grouped assertions after | 34 (unchanged) |
| Resolved object labels | 34/34 (100%) |
| Missing labels | 0 |
| A000490 → label_zh | 希運 |
| A000490 → label_vi | Hi Vận |

---

## Tests

File: `tests/test_t261_marcus_object_labels.py`

| Test | Mô tả |
|------|-------|
| A | A001897 returns actual object labels |
| B | A000490 resolves to '希運'/'Hi Vận' |
| C | Canonical DILA ID remains visible |
| D | Missing vi → ZH_ONLY fallback |
| E | Missing zh → VI_ONLY fallback |
| F | Both missing → ID_ONLY fallback |
| G | Non-MARCUS sources unchanged |
| H | Existing API fields compatible |
| I | Claim count unchanged |
| J | JOIN no duplication |
| K | Grouping key unchanged |
| L | T260 conflict behavior unchanged |
| M | T259 raw view unchanged |
| N | XSS escaping |
| O | Zero DB mutation |
| P | Zero schema mutation |
| Q | Zero external API/LLM |
| real_db_full | A001897 full enrichment regression |
| ast_guard | app.py AST parse valid |

T261: 19/19 PASS · T260 regression: 26/26 PASS · Total: 45/45

---

## Revert

```bash
git revert --no-edit <T261_COMMIT_SHA>
# Không có DB mutation → không cần revert DB
```

---

## Rollback SHA

| Pass | SHA |
|------|-----|
| T261 plumbing commit | 204e95b7fabe6330456390300f9208751d93e090 |
