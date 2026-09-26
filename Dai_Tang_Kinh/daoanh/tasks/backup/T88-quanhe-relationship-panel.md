---
id: T88
title: "Tab Quan Hệ — Relationship Panel (Place → Text → Person)"
module: tab-daitang
priority: medium
status: done
depends_on: [T87]
created: 2026-09-03
updated: 2026-09-03
done_date: 2026-09-03
done_when: "Tab Quan Hệ hiển thị danh sách địa danh liên quan, thiền sư, và kinh điển dẫn chiếu — click-through hoạt động"
---

## Mục tiêu

Thay thế canvas placeholder trong Tab 🔗 Quan Hệ (Tab 3 của daitang-main-panel) bằng
Relationship Panel có cấu trúc 3 section:

1. **🏛 Địa Danh Liên Quan** — places co-mentioned trong cùng passage (passage_entity)
2. **👤 Thiền Sư / Nhân Vật** — persons từ place_person_link (curated) + passage_entity (canonical)
3. **📖 Kinh Điển Dẫn Chiếu** — texts[] + passages[] đã có từ /canon response

## Phân biệt với Nexus Points

| | Quan Hệ (T88) | Nexus Points (future) |
|---|---|---|
| Scope | 1 entity đang xem | Toàn bộ dataset |
| Entry | User đang đọc entity | User đi tìm discovery |
| UI | Structured list, click-through | Global graph, ranking |
| Status | ✅ Build now | ⏳ Future T-Nexus |

## Acceptance Criteria

- [x] API `GET /daoanh/api/entity/<id>/related` trả về `{places[], persons[], texts[]}`
- [x] Tab 3 hiển thị 3 section: Địa Danh / Thiền Sư / Kinh Điển
- [x] Click địa danh → load entity mới (selectItem)
- [x] Click thiền sư → mở person panel (selectPerson hoặc sidebar)
- [x] Click kinh điển → jump sang Tab Nguyên Văn (dtJumpToPassage)
- [x] Empty state rõ ràng khi không có data
- [x] Badge phân biệt nguồn: CURATED (place_person_link) vs CANONICAL (passage_entity) vs ĐỊA/CBETA

## Data sources

### Places (passage_entity co-mention)
```sql
SELECT pe2.entity_id, COUNT(*) as mentions
FROM passage_entity pe1
JOIN passage_entity pe2 ON pe1.passage_id = pe2.passage_id
WHERE pe1.entity_id = :id
  AND pe2.entity_id LIKE 'PL%'
  AND pe2.entity_id != pe1.entity_id
GROUP BY pe2.entity_id
ORDER BY mentions DESC LIMIT 15
```
Names từ `namevi_map_places.dila_id` (short format) hoặc `_resolve_dila_id()`

### Persons — layer 1: curated
```sql
SELECT l.person_id, l.relation_type, p.name_zh, p.name_vi, p.dynasty
FROM place_person_link l JOIN people p ON p.id = l.person_id
WHERE l.place_id = :id
```

### Persons — layer 2: canonical (passage_entity)
```sql
SELECT pe2.entity_id, COUNT(*) as mentions
FROM passage_entity pe1
JOIN passage_entity pe2 ON pe1.passage_id = pe2.passage_id
WHERE pe1.entity_id = :id AND pe2.entity_id LIKE 'A%'
GROUP BY pe2.entity_id ORDER BY mentions DESC LIMIT 10
```

### Texts — from /canon response
Reuse texts[] và passages[] đã có — không cần query thêm.

## Blockers

_(none)_

## Notes

- Canvas + dtDrawGraph() bị thay hoàn toàn — không xóa CSS `.dt-graph-*` để không break layout
- Rollback: git revert về commit 8506f47 nếu cần
