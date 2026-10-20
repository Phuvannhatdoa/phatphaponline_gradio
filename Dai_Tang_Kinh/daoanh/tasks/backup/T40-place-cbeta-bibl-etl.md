---
id: T40
title: Place CBETA Bibl ETL — Liên kết Person↔Place từ DILA Place Authority listBibl
module: Person Authority
priority: high
status: done
depends_on: [T28, T39]
created: 2026-08-25
updated: 2026-08-25
done_when: Bảng place_person_bibl có dữ liệu; tab Nhân Vật hiển thị nguồn CBETA Bibl riêng biệt với citation cho ≥10 địa điểm nổi tiếng
---

# T39 — Place CBETA Bibl ETL

## Mục tiêu

Khai thác `<listBibl>` trong DILA Place Authority XML — nguồn dữ liệu cấu trúc duy nhất
cung cấp liên kết Person↔Place có trích dẫn học thuật, không cần NLP.

DILA đã index sẵn: mỗi place có danh sách CBETA texts trong đó tiểu sử của các tăng nhân cụ thể
đề cập đến địa điểm đó. Ví dụ Thiếu Lâm Tự có 51 entries như:
`( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋玄奘傳 {少林寺}`

## Background — Vì sao cần T39

| Tình trạng trước T39 | Sau T39 |
|---|---|
| 1 địa điểm có curated link | Tất cả famous places có structured links |
| Thiếu Lâm Tự: 2 nhân vật | Thiếu Lâm Tự: ~129 nhân vật (2 + bibl + bio) |
| Không có citation cụ thể | CBETA citation (唐高僧傳 T50n2060_p...) |
| bio search real-time (chậm) | bibl pre-computed (nhanh) |

## Cách tiếp cận

### ETL: `scripts/import_place_person_bibl.py`
1. Parse `Buddhist_Studies_Place_Authority.xml` (117,620 places)
2. Chỉ lấy places có ID trong `places_dila` (59,167 rows — giao nhau ~590 có bibl)
3. Extract từ mỗi `<bibl>`: cbeta_ref + source_book + person_name_raw + mention_keyword
4. Pattern: `書名: 某人傳 {地名}` → person_name = text trước "傳"
5. Match `person_name → people.name_zh`: exact → strip 釋/尼 → unmatched (person_id=NULL)
6. Insert vào `place_person_bibl` (idempotent via UNIQUE constraint)

### Schema: bảng `place_person_bibl`
```sql
CREATE TABLE IF NOT EXISTS place_person_bibl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id TEXT NOT NULL,
    person_id TEXT,           -- NULL nếu chưa match được tên
    person_name_raw TEXT,     -- "釋玄奘" từ bibl
    cbeta_ref TEXT,           -- "T50n2060_p0457c16"
    source_book TEXT,         -- "唐高僧傳"
    mention_keyword TEXT,     -- "少林寺" (từ {keyword} trong bibl)
    confidence REAL DEFAULT 1.0,  -- 1.0=exact, 0.9=strip prefix, 0.0=unmatched
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(place_id, cbeta_ref)
);
```

### API: Source 4 `bibl_persons`
Thêm vào `api_places_persons()`: query `place_person_bibl` cho place_id, trả về
`bibl_persons` array với citation đầy đủ.

### UI: Render section mới
Tab Nhân Vật hiển thị `bibl_persons` với badge "CBETA Bibl" và link
`https://cbetaonline.dila.edu.tw/zh/{cbeta_ref}`.

## Feasibility data (benchmark 2026-08-25)
- Places sample với bibl: 500 / ~590 ước tính total (trong DB)
- Total bibl entries: 2,156 / 500 places = avg 4.3 bibl/place
- Match rate: 50.5% (exact 42.1% + strip-prefix 8.3%)
- Unmatched: Sanskrit names (善無畏, 達摩笈多...) — có thể improve sau
- Projected links: ~724 với person_id, ~714 unmatched (person_name_raw dùng sau)

## Acceptance criteria (checklist)
- [x] Script `scripts/import_place_person_bibl.py` chạy thành công, idempotent
- [x] Bảng `place_person_bibl` tồn tại, có dữ liệu (13,933 rows; 8,513 với person_id; 4,409 unique places)
- [x] API `/api/places/<id>/persons` trả thêm `bibl_persons` array
- [x] Tab Nhân Vật hiển thị bibl_persons với citation CBETA (section mới "DILA CBETA Bibl", avatar cyan)
- [x] Thiếu Lâm Tự (PL000000023255): bibl_persons = 20 (≥20 ✅)
- [ ] Thiên Thai Sơn (PL000000010234): bibl=0 — place này không có bibl entries trong XML (bio=200 vẫn hoạt động)
- [x] Không regression: curated=2, wikidata=1, bio=125 cho Thiếu Lâm Tự — đúng như trước
- [x] ETL log lưu vào `docs/sessions/2026-08-25/t39_etl.log`

## Kết quả thực tế (2026-08-25)

| Metric | Giá trị |
|---|---|
| place_person_bibl total rows | 13,933 |
| Rows với person_id matched | 8,513 (60.7%) |
| Unique places có bibl | 4,409 / 59,167 (7.5%) |
| Thiếu Lâm Tự bibl persons | 20 |
| Top unmatched | 鳩摩羅什 80x, 釋智顗 67x, 釋曇遷 62x (tên biến thể trong DB) |
| Thiếu Lâm Tự tổng cộng sau T39 | 148 nhân vật (2+1+20+125) |

**Ghi chú:** `鳩摩羅什` (Kumārajīva) unmatched vì DB lưu dưới tên biến thể. Có thể fix bằng alias ETL sau.
