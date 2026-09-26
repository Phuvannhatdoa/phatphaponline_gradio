# Build 1 Frozen Contract — Đạo Ảnh (daoanh)

**Cập nhật:** 2026-08-30
**Phạm vi:** app daoanh (`Dai_Tang_Kinh/daoanh`) — `app.py`, `admin/*.html`, bảng SQLite `lineage.db`
**Trạng thái:** CHÍNH THỨC ÁP DỤNG từ 2026-08-30

## Tuyên bố

> **BUILD 1 COMPONENTS ARE FROZEN.**

Build 1 cung cấp nền tảng (identity, mapping, admin workflow, dashboard Đạo Ảnh, GIS, save API, search, VPS backend).
Chúng là **BASELINE BẤT BIẾN** — giữ nguyên hành vi hiện có.

## Future Builds (2+) ĐƯỢC PHÉP

- **Consume** các component Build 1 (gọi API, đọc bảng).
- **Extend** component Build 1 (thêm trường/field một cách additive).
- **Add cấu trúc MỚI**: bảng mới, adapter, service, API mới, evidence layer mới.
- Thêm **source identity** vào `entity_source_ids` / `entity_claims` (đúng mô hình Identity Hub T23).
- Thêm **canonical decision / provenance** vào `canonical_decision` / `en_audit_log` (T67).

## Future Builds (2+) KHÔNG ĐƯỢC

- **Duplicate** component Build 1 (không tạo SQLite mapping thứ hai, dashboard thứ hai, MapComponent thứ hai, identity layer thứ hai).
- **Replace** component Build 1 nếu không có demonstrated requirement.
- Tạo **parallel identity system** (không tạo id song song mới; TGS entity_id = `entity_hub.entity_id` INT hiện có).
- Tạo **parallel mapping system** / **parallel admin system**.
- **Overwrite / transform** dữ liệu nguồn (DILA/CBETA/Marcus/CHGIS/BDRC/Wikidata) thành 1 record gộp.
- **DROP / TRUNCATE / DELETE ALL** nguồn mà không có migration an toàn + backup.

## Bất biến bắt buộc

1. **DILA ID giữ nguyên** — `PL…` (raw/padded theo `ensure_long_id`) là identifier nguồn; không đổi.
2. **Source data giữ nguyên** — source record → identity mapping → canonical entity; nguồn luôn traceable.
3. **API contract Build 1 giữ nguyên** trừ khi versioned.
4. **Schema bảng nguồn** không rename/drop/đổi kiểu.

## Mô hình canonical (không overwrite)

```
SOURCE RECORD          ↔  DILA raw / places_dila / cbeta_* / marcus_* / geo_cross_ref
      ↓
IDENTITY MAPPING       ↔  entity_source_ids / entity_claims
      ↓
TGS CANONICAL ENTITY   ↔  entity_hub (INT surrogate) + entity (PL…) + canonical_decision
```

## Revert / Safety

- Mọi build sau phải **additive + reversible**; commit tách riêng từng task để `git revert` thuận tiện.
- Backup DB an toàn (KHÔNG `wal_checkpoint(TRUNCATE)` khi server mở WAL — bài học T58).
- Ref: `docs/build1_inventory.md`, `docs/architecture-identity-hub.md`, `docs/db_schema.md`, `docs/roadmap.md`.
