---
id: T27
title: Source-Neutral Integer entity_id — long-term migration
module: Identity Hub / Architecture
priority: low
status: blocked_until_needed
depends_on: [T23, T24, T25, T26]
created: 2026-08-20
updated: 2026-08-25
done_when: entity.entity_id là INTEGER tự tăng, không phụ thuộc DILA ID, tất cả sources được đối xử bình đẳng như peers
---

# T27 — Source-Neutral Integer entity_id (Undone / Long-term)

> **Undone — Đây là technical debt lớn nhất của Identity Hub. Không có tổ chức nào giải quyết được vấn đề này một lần cho xong — chỉ cần migrate đúng thời điểm.**

## Vấn Đề Kiến Trúc

### Hiện tại
```sql
entity.entity_id = "PL023255"  -- TEXT, chính là DILA ID
entity.dila_id   = "PL023255"  -- redundant column
```

**Hậu quả:** DILA IS the identity. Bất kỳ entity nào không có DILA ID thì không thể là ZQ entity. BDRC-only entities (ví dụ: Tibetan masters không có trong DILA) không thể tồn tại trong hub.

### Đúng chuẩn mission doc
```sql
entity.entity_id = 10001  -- INTEGER, source-neutral, auto-increment
-- DILA mapping chuyển sang:
entity_source_ids: (10001, 'DILA', 'PL023255')
entity_source_ids: (10001, 'BDRC', 'G00xxxxx')
entity_source_ids: (10001, 'MARCUS', '...')
```

## Tại Sao Chưa Làm Ngay

| Rủi ro | Chi tiết |
|--------|---------|
| **167K rows** | Mọi entity phải migrate → new integer ID |
| **API dependencies** | Tất cả endpoint hiện tại dùng `entity_id = DILA_ID` |
| **Frontend** | places.html, lineage.html, dashboard đều hardcode pattern `PL...` |
| **Rollback phức tạp** | Nếu migration fail → khó revert |

## Migration Plan (khi unblock)

### Step 1: Prepare

```sql
-- Thêm cột mới, không xóa cột cũ
ALTER TABLE entity ADD COLUMN zq_id INTEGER;
CREATE SEQUENCE entity_seq START 10001;

-- Gán zq_id cho mọi entity hiện có
UPDATE entity SET zq_id = rowid + 10000;
```

### Step 2: entity_source_ids migration

```sql
-- entity_source_ids hiện dùng entity_id = DILA TEXT
-- Sau migration: dùng entity.zq_id INTEGER
ALTER TABLE entity_source_ids ADD COLUMN zq_entity_id INTEGER;
UPDATE entity_source_ids eis
SET zq_entity_id = (SELECT zq_id FROM entity WHERE entity_id = eis.entity_id);
```

### Step 3: Compatibility views

```sql
-- View giữ backward compatibility
CREATE VIEW v_entity_by_dila AS
SELECT e.zq_id, e.entity_type, e.canonical_label,
       eis.source_entity_id as dila_id
FROM entity e
JOIN entity_source_ids eis ON eis.zq_entity_id = e.zq_id
WHERE eis.source = 'DILA';
```

### Step 4: API migration

```python
# Tất cả API hiện tại tiếp tục nhận DILA ID
# Backend tự resolve: DILA_ID → zq_id
def resolve_entity(entity_id):
    # Thử tìm trực tiếp (nếu là zq_id integer)
    # Nếu không → tìm trong entity_source_ids WHERE source='DILA'
    pass
```

## Khi Nào Unblock

- **T23 xong**: entity_claims đã có data → migration sẽ có data thật để test
- **T24 xong**: ZQLOCAL content rõ ràng
- **T25 xong**: BDRC entities cần lưu vào hub → thực sự cần integer ID
- **T26 xong**: Unified API đã stable → migration ít break hơn
- **Phiên bản 2.0**: Khi có sprint lớn + rollback plan đầy đủ

## Acceptance Criteria (khi thực hiện)

- [ ] `entity.zq_id INTEGER` tồn tại và populated
- [ ] `entity_source_ids` dùng zq_id thay vì text entity_id
- [ ] Compatibility view `v_entity_by_dila` hoạt động
- [ ] Tất cả existing APIs vẫn chạy (test suite PASS)
- [ ] BDRC entity (không có DILA ID) có thể insert vào hub
- [ ] Backup + rollback plan đã verify trước migration

## Giá Trị Khi Hoàn Thành

Sau T27, PTDA đạt được kiến trúc Identity Hub đúng chuẩn — không source nào là "anchor mặc định". BDRC-only entities, Tibetan masters không có DILA ID, future sources (WHG, CHGIS) đều có thể participate trong hub như peers.
