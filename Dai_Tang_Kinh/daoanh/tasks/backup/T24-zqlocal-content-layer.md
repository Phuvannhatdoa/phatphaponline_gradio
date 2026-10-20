---
id: T24
title: ZQLOCAL Content Layer — tách Vietnamese editorial khỏi DILA schema
module: Identity Hub / ZQLOCAL
priority: medium
status: done
depends_on: [T23]
created: 2026-08-20
updated: 2026-08-24
done_when: zqlocal_content table có data, name_vi / editorial summary được tag source=ZQLOCAL trong entity_claims, không còn nhầm lẫn editorial ZQ với DILA data
---

## Cập nhật 2026-08-24 — bắt đầu, đính chính schema + phát hiện bug T23

**Đính chính:** phần "Vấn Đề" gốc ghi `places_dila.name_vi` — cột này **không tồn tại**
(`PRAGMA table_info(places_dila)` xác nhận). Tên Việt thật do ZQ tự-phiên-âm nằm ở
`namevi_map_places` (118,296 rows, cột `source` phân biệt `auto_transliterate`/`manual`/
`auto_generated`/`rag_auto`), join 100% với `entity` qua `dila_id`.

**Bước 1 (bảng `zqlocal_content`) — ĐÃ XONG:** script
[`scripts/t24_zqlocal_content_migration.py`](../scripts/t24_zqlocal_content_migration.py) (idempotent,
đã test chạy 2 lần — lần 2 insert 0 dòng mới). Kết quả: 118,295 rows trong `zqlocal_content`
(118,293 `generated_by='auto_transliterate'` confidence=0.5, 2 `generated_by='editor'`
confidence=0.8, từ 3 dòng `source='manual'` — 1 dòng bị trùng entity_id nên `INSERT OR IGNORE`
giữ 1).

**⚠ Phát hiện bug ở T23 (đã done) khi chuẩn bị bước "Link vào entity_claims":**
Theo thiết kế T23, `entity_claims.source_id` phải là FK trỏ `data_sources.source_id` (1-5:
DILA/BDRC/CBETA/MARCUS/ZQLOCAL). Thực tế kiểm tra live data: `entity_claims.source_id` có
118,312 giá trị khác nhau, lên tới 118,328 — không phải FK 1-5. Root cause:
[`scripts/etl_entity_claims.py`](../scripts/etl_entity_claims.py) dòng ~102/117 insert
`s.id` (row id của bảng `entity_source_ids`, một mapping-id riêng) vào cột `source_id`, thay vì
`data_sources.source_id` như thiết kế. Ảnh hưởng trực tiếp tới T24: claim `vietnameseName`
(dòng 113-122 file đó) lấy dữ liệu từ `namevi_map_places` (ZQ tự-phiên-âm) nhưng **join điều kiện
`entity_source_ids.source = 'DILA'`** — nghĩa là claim NAME/vietnameseName trong `entity_claims`
hiện đang ngầm gắn với nguồn DILA dù nội dung thật là ZQLOCAL, đúng chính xác vấn đề T24 muốn sửa,
nhưng ở tầng entity_claims chứ không phải `places_dila.name_vi` như mô tả gốc.

**Quyết định:** CHƯA ghi/sửa gì vào `entity_claims` (411K rows, bảng live, T23 đã đánh dấu done và
có thể đang được API/session khác dùng) cho tới khi được xác nhận cách sửa đúng — sửa tại chỗ cột
`source_id` sai lệch trên diện rộng (118K+ rows ảnh hưởng cả COORDINATE/NAME/ADMIN_UNIT claims, không
riêng NAME) là thay đổi rủi ro cao, cần quyết định của admin/user trước khi động vào. Đã KHÔNG tự ý
sửa `tasks/T23-entity-claims-provenance-layer.md` — chỉ ghi chú tại đây, chờ user quyết định có nên
mở lại T23 hay không.

## Hoàn thành 2026-08-24

T33 (Fix entity_claims.source_id) đã chạy thành công — 118,295 `vietnameseName` claims đã được gán
`source_id=5 (ZQLOCAL)` thay vì giả danh DILA. Bảng `zqlocal_content` (118,295 rows) + `entity_claims`
đã nhất quán và đúng nguồn.

Các phần còn lại được chuyển sang task tiếp theo:
- API phân biệt source → T26 (Unified API Response)
- Admin UI `zqlocal_editor.html` → task riêng nếu admin ưu tiên

# T24 — ZQLOCAL Content Layer

## Vấn Đề

Hiện tại:
- `places_dila.name_vi` — tên Việt do ZQ phiên âm, nhưng nằm trong bảng DILA → ngầm hiểu là DILA cung cấp
- `entity.alias_vi` — cùng vấn đề
- `namevi_map_places` — có source info nhưng không link vào entity_claims
- Editorial summaries (note_vi) — không rõ ai viết, không có source tag

**Mission doc:** "ZQLOCAL KHÔNG được giả danh nguồn lịch sử. Mọi Vietnamese editorial content phải được đánh dấu `source = ZQLOCAL`."

## Thiết Kế

### Tạo `zqlocal_content` table

```sql
CREATE TABLE IF NOT EXISTS zqlocal_content (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id     TEXT NOT NULL,       -- FK → entity.entity_id
    content_type  TEXT NOT NULL,       -- 'VI_NAME' | 'VI_SUMMARY' | 'EDITOR_NOTE' | 'ALIAS'
    content       TEXT NOT NULL,
    confidence    REAL DEFAULT 0.8,    -- 0.5=auto-generated, 0.8=reviewed, 1.0=scholar-verified
    generated_by  TEXT,                -- 'auto_transliterate' | 'editor' | 'scholar'
    reviewed_by   TEXT,                -- editor username nếu đã review
    reviewed_at   TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_id, content_type)
);
```

### Link vào entity_claims (sau T23)

```python
# Mỗi row zqlocal_content → 1 entity_claims row
INSERT INTO entity_claims (entity_id, source_id, claim_type,
    predicate, object_text, authority_role, confidence)
SELECT
    entity_id,
    (SELECT source_id FROM data_sources WHERE source_code='ZQLOCAL'),
    CASE content_type
        WHEN 'VI_NAME'    THEN 'NAME'
        WHEN 'VI_SUMMARY' THEN 'DESCRIPTION'
        WHEN 'EDITOR_NOTE' THEN 'ANNOTATION'
    END,
    'vietnameseContent',
    content,
    'PRESENTATION',
    confidence
FROM zqlocal_content;
```

## Phân biệt Source Origin

| Nơi lưu hiện tại | Source thật | Sau T24 |
|-----------------|-------------|---------|
| `places_dila.name_vi` | ZQ phiên âm | → `zqlocal_content` (VI_NAME, generated_by='auto') |
| `entity.alias_vi` | ZQ hoặc DILA? | → `zqlocal_content` hoặc rõ ràng hơn |
| `namevi_map_places` khi approved | Editor | → `zqlocal_content` (VI_NAME, generated_by='editor') |
| Editorial summary | ZQ editor | → `zqlocal_content` (VI_SUMMARY) |

## Admin UI

Trang `admin/zqlocal_editor.html`:
- Xem danh sách entities thiếu VI_NAME
- Edit/approve Vi name → lưu vào `zqlocal_content`
- Badge màu theo confidence (auto=grey, reviewed=blue, scholar=green)

## Acceptance Criteria

- [x] CREATE TABLE `zqlocal_content`
- [x] ETL: migrate `namevi_map_places` → `zqlocal_content` (118,295 rows; `places_dila.name_vi` không tồn tại nên mục dưới N/A, đã gộp)
- [ ] ~~ETL: migrate `places_dila.name_vi`~~ — cột không tồn tại, N/A (xem "Đính chính" trên)
- [x] Link `zqlocal_content` → `entity_claims` (source=ZQLOCAL) — đạt qua T33 (2026-08-24)
- [ ] API `/daoanh/api/places/<id>` phân biệt `source=DILA` vs `source=ZQLOCAL` cho name_vi
- [ ] Không còn implicit "DILA cung cấp tên Việt" khi thực tế là ZQ phiên âm

## Note

Sau T24, nếu admin thấy "Nguồn: ZQLOCAL" thay vì "Nguồn: DILA" cho tên Việt → đó là đúng, không phải bug. DILA chỉ cung cấp tên Hán, còn tên Việt là ZQ làm.
