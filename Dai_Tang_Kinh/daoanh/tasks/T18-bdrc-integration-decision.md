---
id: T18
title: BDRC Integration — Decision & Scope Assessment
module: External Data
priority: low
status: blocked
depends_on: []
created: 2026-08-23
updated: 2026-08-23
done_when: Admin quyết định scope mới và approve ETL design trước khi bất kỳ code nào được viết
---

# T18 — BDRC Integration: Quyết Định & Đánh Giá Phạm Vi

## Quyết định hiện tại: **SKIP — Đúng và có lý do**

Ngày 2026-08-23, sau khi audit cả code base và verify dữ liệu thực tế từ BDRC:

**BDRC integration bị skip hoàn toàn. Đây là quyết định đúng.**

---

## Thực trạng tích hợp (audit 2026-08-23)

| Hạng mục | Trạng thái |
|---|---|
| `bdrc_adapter.py` | Không tồn tại |
| `bdrc_resolve.py` | Không tồn tại |
| `places.bdrc_id` column | Không tồn tại trong schema |
| `entity_source_ids` rows có `source='bdrc'` | 0 rows |
| `geo_cross_ref.bdrc_id` filled | 0/148 |
| Chip BDRC trên UI | Không có |

**Tổng: BDRC integration = 0%. Không phải "4/10" như tài liệu cũ ghi — đó là claim sai.**

---

## Lý do skip là đúng — Scope mismatch căn bản

### BDRC thực tế là gì

- **BDRC = Buddhist Digital Resource Center** (bdrc.io) — tiền thân là TBRC (Tibetan Buddhist Resource Center), thành lập 1999
- Mở rộng sang "all Buddhist traditions" từ 2015, nhưng **core data vẫn là Tạng ngữ**
- ~10,000 địa danh trong database, gần như toàn bộ Tạng-Mông-Himalaya
- Place IDs dùng prefix `G` (G2800 = Lhasa), type codes Tibetan-specific
- **Không có SPARQL endpoint công khai** — chỉ ~70 REST template cố định tại `ldspdi.bdrc.io`

### Overlap với hệ thống PTDA

| Hệ thống | Số địa danh | Truyền thống |
|---|---|---|
| DILA (PTDA đang dùng) | 59,167 | Hán Truyền (Chinese Buddhist) |
| BDRC | ~10,000 | Tạng Truyền (Tibetan Buddhist) |
| **Intersect ước tính** | **< 50** | Núi thiêng đa truyền thống (Ngũ Đài Sơn...) |

**Không có dự án alignment DILA–BDRC nào tồn tại**, kể cả trên Wikidata. Wikidata có property P1188 (DILA Place ID) nhưng không có property nối DILA ↔ BDRC.

### Commit lịch sử

```
4550684 Reapply "feat: Skip BDRC integration per admin decision — BDRC Tibetan-only scope, all bdrc_id remain NULL"
406677f Revert "feat: Skip BDRC integration per admin decision"
cbab40b feat: Skip BDRC integration per admin decision — BDRC Tibetan-only scope, all bdrc_id remain NULL
```

Đã từng có code để tích hợp, bị revert, sau đó skip lại. Lý do: thử tích hợp → tất cả `bdrc_id` đều NULL → confirm mismatch → skip.

---

## Nếu admin muốn tích hợp BDRC trong tương lai

### Điều kiện tiên quyết

1. **Chỉ có giá trị nếu mở rộng sang địa danh Tạng Truyền** (chùa Tây Tạng, Bhutan, Nepal, Mông Cổ)
2. Cần viết ETL mới từ đầu — không có gì tái sử dụng được từ code hiện tại
3. Cần thêm column `bdrc_id` vào schema + migration

### Các bước cần làm (chỉ khi approve)

```
1. Schema: ALTER TABLE places_dila ADD COLUMN bdrc_id TEXT;
2. ETL: Query ldspdi.bdrc.io REST API → match theo tọa độ GPS hoặc tên Tạng ngữ
3. Mapping: Tạo bảng geo_cross_ref với bdrc_id filled
4. API: Thêm bdrc_id vào /daoanh/api/places/<id> response
5. UI: Thêm chip BDRC trên entity header
```

### Nguồn thay thế tốt hơn cho địa danh Hán

Nếu mục tiêu là cross-reference địa danh **Hán Truyền**, nên dùng:

| Nguồn | Phù hợp | Trạng thái |
|---|---|---|
| **DILA** | ✅ 59,167 địa danh Hán | Đang dùng |
| **CBETA** | ✅ Văn bản Hán | Đang dùng |
| **Wikidata** | ✅ Pan-Buddhist, có GPS | Đang dùng |
| **CHGIS** (Harvard China Historical GIS) | ✅ Tọa độ lịch sử Trung Quốc | Chưa tích hợp |
| **BDRC** | ❌ Tạng ngữ chính | Skip — mismatch |

---

## Blockers

- **Admin chưa approve scope mới** (địa danh Tạng Truyền)
- Không có ETL design
- Không có tài nguyên (BDRC REST API cần authentication cho bulk queries)

---

## Kết luận cho admin

> BDRC không phải nguồn sai — chỉ là **sai scope** cho hệ thống địa danh Hán hiện tại.
> Nếu tương lai PTDA mở rộng sang **Buddhism Tây Tạng / Himalaya**, BDRC là nguồn chính xác cần tích hợp.
> Hiện tại: không cần làm gì. Task này để **blocked** cho đến khi có quyết định mới từ admin.
