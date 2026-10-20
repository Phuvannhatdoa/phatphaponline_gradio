---
id: T33
title: Fix entity_claims.source_id — gán đúng nguồn DILA vs ZQLOCAL
module: Identity Hub / ZQLOCAL
priority: high
status: done
depends_on: [T23, T24]
created: 2026-08-24
updated: 2026-08-24
done_when: entity_claims.source_id trỏ đúng data_sources.source_id (1=DILA/5=ZQLOCAL); claim vietnameseName gắn ZQLOCAL, không còn giả danh DILA
---

# T33 — Fix entity_claims.source_id (bug từ etl_entity_claims.py)

## Vấn Đề

[`scripts/etl_entity_claims.py`](../scripts/etl_entity_claims.py) đã ghi sai cột `source_id` trong
`entity_claims`: thay vì ghi FK trỏ `data_sources.source_id` (1=DILA, 3=CBETA, 5=ZQLOCAL...), nó
ghi `entity_source_ids.id` — là row-id nội bộ của bảng mapping, lên tới 118,328 giá trị khác nhau.

Hệ quả:
- **118,293 claim `vietnameseName`** hiện mang `source_id` tuỳ tiện (không phải 5/ZQLOCAL), dù nội
  dung là tên Việt do ZQ tự-phiên-âm từ `namevi_map_places`.
- Nếu T26 (Unified API Response) build xong mà chưa fix, web sẽ hiển thị "Nguồn: DILA" cho toàn
  bộ 118K tên Việt — giả danh nguồn học thuật, vi phạm đúng nguyên tắc content-integrity của dự án.
- Bảng `entity_claims` hiện **chưa được `app.py` đọc ở đâu** (grep xác nhận 0 matches), nên fix
  bây giờ không ảnh hưởng gì tới giao diện đang chạy — rủi ro thấp nhất có thể.

## Phân tích nguồn gốc từng claim_type

Theo đọc kỹ code `etl_entity_claims.py`:

| claim_type | predicate | Nguồn thật | source_id đúng |
|---|---|---|---|
| COORDINATE | hasCoordinate | places_dila (DILA) | 1 (DILA) |
| ADMIN_UNIT | hasAdministrativeUnit | places_dila (DILA) | 1 (DILA) |
| NAME | canonicalNameZh | places_dila.name_zh (DILA) | 1 (DILA) |
| NAME | vietnameseName | namevi_map_places (ZQ tự-phiên-âm) | 5 (ZQLOCAL) |

## Kế Hoạch Fix

**Backup (bắt buộc, đã làm):**
```
docs/sessions/2026-08-24/lineage_pre_T33_source_id_fix.db.bak  (849MB)
```

**Script fix idempotent** (xem [`scripts/t33_fix_entity_claims_source_id.py`](../scripts/t33_fix_entity_claims_source_id.py)):

```sql
-- Bước 1: Các claim từ DILA thật sự
UPDATE entity_claims
SET source_id = (SELECT source_id FROM data_sources WHERE source_code='DILA')
WHERE claim_type IN ('COORDINATE', 'ADMIN_UNIT')
   OR (claim_type='NAME' AND predicate='canonicalNameZh');

-- Bước 2: Tên Việt từ ZQ (namevi_map_places), không phải DILA
UPDATE entity_claims
SET source_id = (SELECT source_id FROM data_sources WHERE source_code='ZQLOCAL')
WHERE claim_type='NAME' AND predicate='vietnameseName';
```

**Verify sau fix:**
- `SELECT source_id, COUNT(*) FROM entity_claims GROUP BY source_id` phải chỉ còn các giá trị 1-5
- Spot-check Thiếu Lâm Tự (`PL023255`): claim `vietnameseName` phải `source_id=5 (ZQLOCAL)`

## Ghi chú thực hiện 2026-08-24

Fix cần 2 bước thực tế (do phát hiện thêm sai sót trong quá trình chạy):

**Bước 1 — script gốc**: `t33_fix_entity_claims_source_id.py` — sửa đúng COORDINATE/ADMIN_UNIT
(234,028 rows → source_id=1/DILA), nhưng phần NAME dùng nhầm `predicate=` thay vì `subject=`
→ 177,440 NAME claims vẫn còn source_id sai sau bước này. Script đã được archive như tài liệu lịch sử
(không dùng lại).

**Bước 2 — fix inline trong Python REPL**:
- `subject='canonicalNameZh'` → source_id=1 (DILA): 59,150 rows ✓
- `subject='vietnameseName'` → source_id=5 (ZQLOCAL): 118,295 rows ✓

**Trạng thái cuối** (verified 2026-08-24):
- source_id=1 (DILA): 293,177 rows (COORDINATE + ADMIN_UNIT + canonicalNameZh)
- source_id=5 (ZQLOCAL): 118,295 rows (vietnameseName)
- Still unknown: **0**

Phát hiện thêm về schema thật của `entity_claims`:
- `entity_id` là INTEGER (từ `entity_hub`), KHÔNG phải TEXT (từ `entity`) — 2 hệ thống song song
- `subject` = label của claim type ('vietnameseName', 'canonicalNameZh', 'hasCoordinate'...)
- `predicate` = giá trị thực tế (tên Việt, tên Hán, toạ độ...)

## Acceptance Criteria

- [x] Backup lineage.db trước khi chạy (docs/sessions/2026-08-24/lineage_pre_T33_source_id_fix.db.bak)
- [x] source_id fix chạy thành công
- [x] `entity_claims.source_id` chỉ còn {1, 5} — 0 unknown
- [x] Claim `vietnameseName` → source_id=5 (ZQLOCAL): 118,295 rows
- [x] Claim `COORDINATE`/`ADMIN_UNIT`/`canonicalNameZh` → source_id=1 (DILA): 293,177 rows
- [x] T24 acceptance criteria "Link zqlocal_content → entity_claims" đạt được

## Ghi chú

- T26 (Unified API Response) phụ thuộc task này: KHÔNG build T26 trước khi T33 done.
- Sau fix, `tasks/T23-entity-claims-provenance-layer.md` cần note thêm về bug này và cách đã sửa.
- `scripts/etl_entity_claims.py` cần patch để nếu ai chạy lại sẽ không tái tạo bug cũ.
