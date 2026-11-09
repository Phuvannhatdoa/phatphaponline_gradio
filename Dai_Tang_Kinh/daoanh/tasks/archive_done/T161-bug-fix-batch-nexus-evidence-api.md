---
id: T161
title: "Bug Fix Batch — Nexus evidence_type API + _nexusSafeLabel + auto-expand tang_nhan"
module: graph
priority: medium
status: done
depends_on: [T157]
created: 2026-09-22
updated: 2026-09-22
done_when:
  - "[x] BUG-001: api_places_graph — tất cả edges có evidence_type (verified in code)"
  - "[x] BUG-002: api_nexus — tất cả edges có evidence_type (etype=person branch fixed)"
  - "[x] BUG-005: _nexusSafeLabel — đủ fallback chain theo spec §6 (verified in code)"
  - "[x] BUG-006: _nexusGroupState — place auto-expand tang_nhan (verified in code)"
  - "[x] docs/bugs.md cập nhật status fix applied cho 4 bugs"
  - "[x] tasks/T161 task file created"
---

# T161 — Bug Fix Batch: Nexus Evidence API + Label + Auto-expand

> **Module:** `graph` · **Priority:** medium · **Status:** done
> **Created:** 2026-09-22

---

## Tóm tắt

Batch 4 bugs nhỏ liên quan đến Nexus graph API và UI:

| Bug | File | Vấn đề | Fix |
|-----|------|---------|-----|
| BUG-001 | app.py | api_places_graph edges thiếu evidence_type | Đã có trong code (T101) |
| BUG-002 | app.py | api_nexus etype=person edges thiếu evidence_type | Fixed 2026-09-22 |
| BUG-005 | places.html | _nexusSafeLabel thiếu fallback chain đầy đủ | Đã có trong code |
| BUG-006 | places.html | Place view không auto-expand tang_nhan | Đã có trong code (line 7165) |

---

## BUG-002 Fix chi tiết (etype=person branch)

File `app.py` function `api_nexus`, branch `etype == 'person'` tại lines 6418-6424:

**BEFORE:** 2 edges thiếu evidence_type
```python
edges.append({"from": entity_id, "to": eid, "label": '—', "ref": None})
edges.append({"from": eid, "to": placeid, "label": 'cư trú tại',
              "ref": ev['source_book'] or None})
```

**AFTER:**
```python
_src = ev['source_book'] or None
edges.append({"from": entity_id, "to": eid, "label": '—', "ref": None,
              "evidence_type": "unverified"})
edges.append({"from": eid, "to": placeid, "label": 'cư trú tại',
              "ref": _src,
              "evidence_type": "partial" if _src else "unverified",
              "partial_reason": "Chưa có CBETA locator cụ thể" if _src else None})
```

---

## Ghi chú BUG-001/005/006

Những bugs này **đã được fix trong các session trước** (T101 và các session sau).
Bugs.md vẫn ghi "pending_confirm" — đúng (fix applied, chờ admin xác nhận DONE).
Không cần code change thêm.

---

## Revert

```bash
git revert <commit-T161>
```
Chỉ ảnh hưởng app.py (BUG-002 fix — 2 edges trong api_nexus person branch).
