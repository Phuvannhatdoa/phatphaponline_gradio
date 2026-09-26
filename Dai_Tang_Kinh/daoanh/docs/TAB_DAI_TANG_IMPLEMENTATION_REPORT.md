# TAB_DAI_TANG_PLACE — Báo cáo triển khai (Implementation Report)

**Ngày:** 2026-09-01
**Cấu phần:** Tab 📜 Đại Tạng (canon Tam Tạng 3 lớp) trong trang địa danh `places.html`
**Trạng thái:** ✅ DONE (B1–B3) — B4 tài liệu này

> **Quan trọng về concurrency:** Code feature đã được **commit vào `8e7c77f`** bởi một session
> song song trong cùng thư mục (branch `master`). Git diff hiện tại của `app.py`/`places.html`
> chỉ còn chứa thay đổi **in-progress của session T74** (LLM config/translate) — **KHÔNG thuộc**
> feature này, và **không được đưa vào commit tài liệu** của task. Hành động B4 chỉ commit
> **tài liệu** (task file + report + session + tasktodo + progress + dashboard).

---

## 1. Bối cảnh / Vấn đề

Tab "Đại Tạng" trong `places.html` trước đây là **alias của tab `cbeta`**
(`data-t="daitang"` → render `cbeta`), nên:

- Không bao giờ hiển thị **`raw_text` passage thật** (bảng `passage`).
- Không phân biệt 3 lớp dữ liệu canon: (A) dẫn DILA thô / (B) passage indexed / (C) metadata text.
- Không có cơ chế empty-state trung thực cho bản dịch Việt.

## 2. Phạm vi giải pháp (mô hình 3 lớp)

| Lớp | Nguồn DB | Nội dung | Hiển thị |
|-----|----------|----------|----------|
| **A — DILA raw refs** | `places_dila.listbibl`, `raw_xml` | Dẫn CBETA (vd `T50n2060_p0457c16`) + FOSIZHI | copy + link |
| **B — Indexed passages** | `passage_entity` → `passage` | `raw_text` theo `loc_ref`, phân trang | card + chip `evidence:` + modal đọc |
| **C — Text metadata** | `catalog_mapping` → `canon_catalog`/`cbeta_catalog_vn` | 1524, 2059, 2060, 2061, 2062, 2210 | danh sách mapping/source/status/note |
| **Emptystate Việt** | `passage.vi_text` (0 rows) | Không bịa / không LLM | banner trung thực |

## 3. Data Reality (probe DB thật — read-only) — PL000000023255

| Điểm | Giá trị thật | Ý nghĩa |
|------|--------------|---------|
| `entity.alias_zh` | `少林寺` | Header dùng cái này |
| `places_dila.name_zh` | `少室寺` | Tên Hán canon LƯU TRỮ (≠ 少林寺) — Lớp A hiển thị |
| `passage_entity` | **15** | Lớp B passages |
| `passage.vi_text` | **0** | Không có bản dịch Việt → empty-state |
| `catalog_mapping` | **6** | Lớp C text metadata |
| `translation_cache` | **0** | translation_count=0 |
| `dila_reference` | bảng person-refs | KHÔNG phải place canon refs — Lớp A dùng `listbibl`/`raw_xml` |
| JOIN bảng | không có JOIN lưu trữ DILA↔passage | Lớp A & B độc lập (đã xác minh) |

## 4. Files Changed

| File | Thay đổi |
|------|----------|
| `app.py` | `entity_canon` (+ route `/daoanh/api/entity/<entity_id>/canon`) ~line 11530; `_resolve_dila_id` line 4015 |
| `places.html` | `#tp-daitang` (224); tab handler (~988); `loadTabData` (~1219); `_daitangChip` (~1467); `openDaiTangReader` (~1474); `renderDaiTangTab` (~1513); `daiTangGoPage` (~1660); `daiTangReport` (~1700) |

> Code đã được commit trong `8e7c77f` (session song song). Tài liệu task này là B4 bổ sung.

## 5. DB Tables Used (chỉ đọc)

`entity`, `places_dila`, `passage_entity`, `passage`, `catalog_mapping`,
`canon_catalog`/`cbeta_catalog_vn` (join qua `CAST(cb_cbeta AS TEXT)=catalog_id`).

## 6. SQL read-only (chạy lại được, để tái tạo số liệu)

```sql
-- PL000000023255 (Thiếu Lâm Tự / 少林寺)
SELECT entity_id, entity_type, alias_vi, alias_zh FROM entity WHERE entity_id='PL000000023255';
SELECT name_zh, substr(listbibl,1,80) FROM places_dila WHERE id='PL000000023255';
SELECT COUNT(*) FROM passage_entity WHERE entity_id='PL000000023255';            -- 15
SELECT COUNT(*) FROM passage_entity pe JOIN passage p ON pe.passage_id=p.passage_id
  WHERE pe.entity_id='PL000000023255' AND p.vi_text IS NOT NULL;                -- 0
SELECT COUNT(*) FROM catalog_mapping WHERE place_id='PL000000023255';           -- 6
SELECT COUNT(*) FROM translation_cache;                                         -- 0
```

## 7. Endpoint Contract

`GET /daoanh/api/entity/<entity_id>/canon`

```jsonc
{
  "entity": {"entity_id":"...","entity_type":"PLACE","alias_vi":"Thiếu Lâm Tự","alias_zh":"少林寺",
             "authority_sources":["DILA","CBETA"]},
  "summary": {"dila_reference_count":49, "indexed_passage_count":15,
              "text_count":6, "translation_count":0},
  "data_status": "...",
  "dila_references": [{"ref":"...","source":"CBETA|FOSIZHI","text":"..."}],
  "passages": {"items":[...], "total":15, "page":1, "page_size":10, "has_more":true},
  "texts": [{"catalog_id":"...","title":"...","mapping_source":"...","status":"...","note":"..."}],
  "mapping": [...]
}
```

- Resolve id: `PL022435`→`PL000000023255`, `PL023255`→湯陰. 404 khi không tồn tại.
- Phân trang đã kiểm (page_size=10: page1 has_more True, page2 5 items).

## 8. Test Results

| Test | Kết quả |
|------|---------|
| `py_compile app.py` | ✅ PASS |
| `node --check` script blocks places.html | ✅ PASS |
| `npm run e2e` (mọi trang) | ✅ PASS |
| `npm run test` | ✅ PASS |
| Regression `/daoanh/api/places/PL000000023255/cbeta` | ✅ OK (39 passages, 3 related_texts) |
| Endpoint canon (Flask test client: page 2, 404, id ngắn/dài) | ✅ PASS |

## 9. Missing-data list

- **Bản dịch Việt**: 0/15 passage có `vi_text` → empty-state trung thực (quyết định: không bịa,
  không realtime LLM). Có thể bổ sung sau qua Translation Pipeline nếu/admin mong muốn.
- **DILA↔passage join lưu trữ**: không tồn tại bảng join — chỉ suy ra theo page/cột; Lớp A & B độc lập.

## 10. Migration / Rollback

**Không có migration DB** — feature additive. Rollback = revert commit chứa code:

```bash
git revert 8e7c77f
```

## 11. Ghi chú handover admin

- Vào một địa danh (vd **Thiếu Lâm Tự**) trong `places.html` → tab **📜 Đại Tạng**.
- Hiển thị 3 lớp: dẫn DILA (copy/link) → từng passage (đọc nguyên văn trong modal) → metadata text.
- Nút **báo sai** đưa về tổng đài/admin; **HỒ SƠ LIÊN KẾT** sidebar.
- Nếu KHÔNG tự động có dữ liệu (trang trống + `da-warn`) → xem tab khác hoặc báo admin.
