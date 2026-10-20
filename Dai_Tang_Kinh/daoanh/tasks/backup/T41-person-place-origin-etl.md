---
id: T41
title: Person placeOfOrigin ETL — Liên kết nhân vật theo quê quán từ DILA Person Authority
module: Person Authority
priority: high
status: done
depends_on: [T40]
created: 2026-08-25
updated: 2026-08-25
done_when: Bảng person_origin_link có dữ liệu; API persons trả thêm nguồn "DILA Quê Quán"; ≥5,000 person-place links kiểu "birthplace"
---

# T41 — Person placeOfOrigin ETL

## Mục tiêu

Khai thác `<note type='placeOfOrigin'>` trong DILA Person Authority XML — mỗi người có
quê quán với DILA place ID cụ thể. Script `import_person_bio.py` đã parse được `origin_pl`
nhưng **không lưu**. T41 = bổ sung bước lưu này.

## Background — Phát hiện từ T40 Diagnosis

Từ chẩn đoán 2026-08-25:
- bibl ceiling = **7.5%** (tất cả places có bibl đã trong DB, không thể tăng bằng bibl)
- `import_person_bio.py` đã parse `origin_pl` (DILA place ID) nhưng bỏ qua không lưu
- Yield ước tính: nếu 30% của 48,673 người có origin → **~15,000 birthplace links**
- Coverage tăng: mở sang loại places hoàn toàn mới (tỉnh/thành phố/huyện quê quán)

## Phân biệt semantic

| Nguồn | Relation type | Ý nghĩa |
|---|---|---|
| T40 `place_person_bibl` | "CBETA @ 少林寺" | Người ĐƯỢC ĐỀ CẬP trong ngữ cảnh địa điểm đó |
| **T41 `person_origin_link`** | "quê quán" | Người SINH TẠI địa điểm đó |
| T40 bio text search | "住持/僧人 @ X" | Người TU TẠI địa điểm đó (inferred) |

Cả ba nguồn bổ trợ nhau, không thay thế.

## Cách tiếp cận

### Bước 1: Verify data tồn tại trong XML
```python
# Từ import_person_bio.py đã có sẵn:
origin_el = p.find("tei:note[@type='placeOfOrigin']//tei:ref", NS)
target = origin_el.get('target') or ''
# target = "PL000000023255" hoặc "/authority/place/detail/?id=PL000000023255"
```

### Bước 2: Script mới `scripts/import_person_origin.py`
1. Parse Person Authority XML: `person_id → origin_pl (DILA ID)`
2. Lọc: chỉ lấy DILA IDs có trong `places_dila` (để có tên hiển thị)
3. Insert vào bảng `person_origin_link`:

```sql
CREATE TABLE IF NOT EXISTS person_origin_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(person_id, place_id)
);
CREATE INDEX IF NOT EXISTS idx_pol_place ON person_origin_link(place_id);
CREATE INDEX IF NOT EXISTS idx_pol_person ON person_origin_link(person_id);
```

### Bước 3: Feed vào `api_places_persons()` — Source 5
- Query `person_origin_link` cho place_id → `origin_persons` array
- Badge UI khác: "DILA Quê Quán" (xanh lá, avatar 🏠 hoặc khác biệt)
- relation_type: "sinh tại / 籍貫"

### Bước 4: Feed vào `api_persons_detail()` (nếu có) — reverse link
- Khi xem thông tin 1 người → hiện "Quê quán: [地名]" với link tới place

## Feasibility check cần chạy trước khi build

Script check nhanh:
```python
# Đếm bao nhiêu persons có placeOfOrigin với DILA ID hợp lệ
# Đếm bao nhiêu origin place IDs có trong places_dila
# → yield thực tế
```

⚠️ **Note từ diagnosis**: XPath `tei:note[@type='placeOfOrigin']//tei:ref` trả 0 trong test script.
Cần debug lại format XML thực tế trước khi build. Có thể element nằm ở namespace khác hoặc
attribute `target` format khác (URL thay vì bare PL-ID).

## Acceptance criteria
- [x] Verify XPath → đếm được persons với origin DILA ID > 0 (11,968 persons có placeOfOrigin; PL ID trong ref.text không phải target attr)
- [x] Script `scripts/import_person_origin.py` chạy, idempotent
- [x] Bảng `person_origin_link` có ≥3,000 rows (thực tế: 11,929 rows)
- [x] API `/api/places/<id>/persons` trả thêm `origin_persons` array (Source 5)
- [x] Tab Nhân Vật hiển thị section "DILA Quê Quán / 籍貫" riêng biệt (avatar 🏠 xanh lá)
- [x] ETL log lưu vào `docs/sessions/2026-08-25/t41_etl.log`
- [x] Không regression: bibl_persons, bio_persons, wikidata_persons vẫn đúng

## Kết quả thực tế (2026-08-25)

| Metric | Giá trị |
|---|---|
| Persons có placeOfOrigin | 11,968 / 48,803 (24.5%) |
| Inserted person_origin_link | 11,929 |
| Unique places với origin persons | 4,266 |
| PL IDs không có trong places_dila | 39 |
| XPath bug fix | PL ID trong ref.text, không phải ref.target |

Script: `daoanh/scripts/import_person_origin.py`  
Log: `daoanh/docs/sessions/2026-08-25/t41_etl.log`
