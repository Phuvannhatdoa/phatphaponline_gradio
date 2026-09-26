---
id: T31
title: BGIS ETL — GPS enrichment + bgis_id linkage cho DILA places
module: GIS / Data Enrichment
priority: high
status: done
depends_on: [T21]
created: 2026-08-24
updated: 2026-08-24
done_when: geo_cross_ref.bgis_id populated cho DILA places khớp BGIS (name-similarity gated); license BGIS hiển thị trên HOME page + trusted-sources.md
---

# T31 — BGIS ETL (GPS enrichment + bgis_id linkage)

## Tách từ T21 Giai đoạn 4 — Scope đã được điều chỉnh

BGIS (Jiang Wu / Bingenheimer Buddhist Geography Information System) là nguồn GPS cho 18,938
Buddhist sites Trung Quốc. **Quan trọng:** BGIS KHÔNG có founding dates lịch sử — `YEAR_START = 2006`
cho tất cả rows (là năm xuất bản directory Zhongguo Fojiao siyuan minglu, không phải năm lập chùa).

**Scope thực tế của T31:**
- Spatial join BGIS GPS ↔ DILA places → populate `geo_cross_ref.bgis_id`
- Bổ sung GPS cho 172 DILA 寺廟-places hiện thiếu GPS
- Thêm BGIS attribution/license vào HOME page và docs

## Data đã có (admin download xong 2026-08-24)

```
daoanh/data/dila_import/Bgis/
├── BGIS_v1-1_20130306.xls       (7.8MB — main data, GBK encoding)
├── BGIS_v1-1_20130306.ods       (OpenDocument)
├── BGIS_v1-1_20130306.zip       (Shapefile: .dbf 49MB, .shp, .shx, .prj)
├── BGIS_GIS_data_README.txt     (field descriptions)
├── README_BGIS_2006_Temple_Data_version_1.1.pdf
└── BGIS_v1-1_20130306.png       (map preview)
```

## License / Attribution (bắt buộc)

```
BGIS 2006 Temple Data Version 1.1
Edited by: Jiang Wu (University of Arizona)
GIS Editor: Lex Berman
Source data: Gui Weibing (ed.) "Zhongguo Fojiao siyuan minglu 2006". Hong Kong: Zhonghua fojiao chubanshe, 2006.
Distributed through: BGIS, CHGIS, ECAI
Harvard Dataverse: doi:10.7910/DVN/VAYEUZ
License: Academic use with attribution required
```

## Dữ liệu hiện tại (pre-BGIS)

| Metric | Giá trị |
|--------|---------|
| DILA 寺廟 places tổng | 12,919 |
| Có GPS | 12,747 (98.7%) |
| Thiếu GPS | 172 (1.3%) |
| BGIS Buddhist sites | 18,938 — tất cả có GPS tốt |

| Source | Rows | Coverage |
|--------|------|---------|
| wikidata | 122 | verified (Wikidata QID match) |
| dila_note | 429 | regex_note (CE year trong parentheses) |
| dila_era_name | 1,449 | era_name_exact / era_name_midpoint |
| dila_dynasty | 543 | dynasty_range (midpoint) |
| **Total (founding dates)** | **2,543** | **2,503 unique places (4.23% of 59K)** |

**BGIS KHÔNG đóng góp thêm founding dates** — xem lý do ở phần "Phát hiện quan trọng" dưới đây.
Scope thực tế của T31 là làm giàu `geo_cross_ref.bgis_id` (GPS cross-reference), không phải
`place_timeline_events`.

## Phát hiện quan trọng khi verify data (2026-08-24)

### 1. BGIS không có founding date lịch sử
`YEAR_START = 2006` cho **tất cả** 18,938 rows. Đây là năm xuất bản cuốn danh mục nguồn
(Gui Weibing, *Zhongguo Fojiao siyuan minglu 2006*), không phải năm lập chùa. Kế hoạch ban đầu
("BGIS dự kiến thêm 500–2000 founding dates") dựa trên giả định sai — đã bị bác bỏ bằng cách đọc
trực tiếp dữ liệu thật, không phải README.

### 2. 83.5% tọa độ BGIS là centroid hành chính, không phải vị trí chùa thực
Kiểm tra trùng lặp: 18,938 rows chỉ có 6,168 tọa độ duy nhất. Top tọa độ trùng nhiều nhất có
**142 chùa khác nhau dùng chung 1 điểm GPS** (rõ ràng là geocode theo centroid huyện/thị trấn).
→ Spatial-join theo khoảng cách đơn thuần **không đáng tin** — 2 điểm gần nhau chỉ có nghĩa
"cùng huyện", không phải "cùng chùa".

**Xử lý:** Name similarity (sau khi normalize giản thể→phồn thể qua bảng ánh xạ ký tự Phật giáo
thường gặp) làm **gate bắt buộc** (`sim >= 0.4`), khoảng cách chỉ dùng làm tiêu chí phụ/tie-break.

### 3. Kết quả thực tế sau khi siết ngưỡng
| Bước lọc | Số lượng |
|---------|---------|
| Spatial matches thô (±0.5km, bất kỳ tên) | 310 |
| Name similarity <40% (loại bỏ — không đáng tin) | 277 |
| **Passing threshold (sim≥0.4) — INSERTED** | **33** |
| — trong đó `bgis_spatial_verified` (sim≥0.6) | 29 |
| — trong đó `bgis_spatial_likely` (0.4≤sim<0.6) | 4 |

33 là con số thấp hơn nhiều so với kỳ vọng ban đầu (500-2000), nhưng là con số **thật và đáng tin**,
không phải suy diễn từ khoảng cách một mình.

## Đã thực thi (2026-08-24)

Script: [`scripts/bgis_spatial_join.py`](../scripts/bgis_spatial_join.py)

```bash
python scripts/bgis_spatial_join.py --dry-run   # preview, không ghi DB
python scripts/bgis_spatial_join.py             # backup + INSERT thật
```

Kết quả:
- Backup tạo tại `data/lineage.db.bak.2026-08-24`
- `geo_cross_ref`: inserted=33, updated=0, skipped(sim<0.4)=277
- Không có places nào bị OVERWRITE — chỉ INSERT rows mới hoặc UPDATE `bgis_id`/`notes` khi
  `dila_id` đã tồn tại trong `geo_cross_ref` (chưa xảy ra lần này — 0 pre-existing rows có bgis_id)

## Việc còn lại

- [ ] **GPS fill cho 172 DILA places thiếu GPS** — dùng flag `--fill-gps`, match theo tên only
      (không có tọa độ DILA để spatial-join). Cần review kỹ hơn vì risk sai cao hơn (không có
      khoảng cách để cross-check).
- [x] BGIS attribution/license → HOME page (xem `static/index.html`)
- [x] BGIS attribution/license → `docs/trusted-sources.md`

## Acceptance criteria (checklist)
- [x] `BGIS_v1-1_20130306.xls` verify format — XLS/ODS/Shapefile, GBK encoding, 41 columns
- [x] Phát hiện: `YEAR_START` = năm xuất bản (2006), không phải founding date → scope revised
- [x] Spatial join script viết (`scripts/bgis_spatial_join.py`) — bucket-index haversine + name-sim gate
- [x] Phát hiện: 83.5% tọa độ BGIS trùng (county centroid) → distance-only match không đáng tin
- [x] Name similarity threshold 0.4 áp dụng làm hard gate
- [x] BACKUP `data/lineage.db` trước khi INSERT (`data/lineage.db.bak.2026-08-24`)
- [x] INSERT vào `geo_cross_ref.bgis_id` — 33 rows (29 verified, 4 likely)
- [ ] GPS fill cho 172 places thiếu GPS (optional, risk cao hơn — cần review riêng)
- [x] License BGIS hiển thị trên HOME page + `docs/trusted-sources.md`
- [ ] Dashboard `progress_data.json` cập nhật (status → done sau khi hoàn tất GPS fill hoặc quyết định bỏ qua)
