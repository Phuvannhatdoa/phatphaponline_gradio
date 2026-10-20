# TTL Person Formal Name Integration — Báo Cáo Tích Hợp

**Ngày:** 2026-09-06  
**Engineer:** Claude Code (Build Agent)  
**Task:** Tích hợp tên trang trọng từ ~1,000–2,000 file TTL vào UI Đạo Ảnh (Phases 1–7)

---

## 1. Tổng Quan

Hệ thống Đạo Ảnh có ~1,075 file TTL định nghĩa tên tiếng Việt trang trọng cho các thiền sư Phật giáo (ví dụ: "Bách Trượng Hoài Hải", "Viên Ngộ Khắc Cần"). Mục tiêu: sử dụng các tên này làm `preferred_display_name_vi` trong UI tab Pháp Mạch (Truyền Thừa), **chỉ khi đã xác minh 1:1 với DILA Person ID ổn định**.

---

## 2. Kết Quả Xử Lý TTL

### 2.1 Tổng Hợp File

| Chỉ số | Giá trị |
|--------|---------|
| Tổng file TTL được tìm thấy | 1,075 |
| File bị loại (duplicate root vs subdir) | 36 |
| File được xử lý (không trùng) | 1,039 |
| Có tên `@vi` | ~1,039 |
| Có tên `@zh` | ~890 |
| Có appellation node | ~650 |

### 2.2 Kết Quả Xác Minh

| Trạng thái | Số lượng | Ghi chú |
|------------|----------|---------|
| `verified_direct` | 5 | Khớp qua bảng `ttl_mapping` (direct file→DILA) |
| `verified_crosswalk` | 2 | Khớp qua tên Hán đã xác minh |
| `review_required` | ~4 | Có DILA candidate nhưng chưa xác nhận |
| `rejected` | ~1,028 | Không có DILA ID candidate trong `ttl_mapping` |
| **Tổng verified ghi vào DB** | **7** | |

### 2.3 Các Record Đã Verify

| person_id | Tên trang trọng | Tên DILA | Phương pháp |
|-----------|----------------|----------|-------------|
| A033489 | (từ TTL) | (DILA authority) | verified_direct |
| A038686 | (từ TTL) | (DILA authority) | verified_direct |
| A004146 | (từ TTL) | (DILA authority) | verified_direct |
| A036842 | (từ TTL) | (DILA authority) | verified_direct |
| A000453 | Viên Ngộ Khắc Cần | Khắc Cần | verified_direct |
| A010097 | (từ TTL) | (DILA authority) | verified_crosswalk |
| A014109 | (từ TTL) | (DILA authority) | verified_crosswalk |

---

## 3. Kiến Trúc Dữ Liệu

### 3.1 Bảng `person_display_names` (mới)

```sql
CREATE TABLE IF NOT EXISTS person_display_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,           -- DILA stable ID
    dila_person_id TEXT,
    locale TEXT NOT NULL DEFAULT 'vi',
    display_name_vi TEXT NOT NULL,     -- Tên trang trọng tiếng Việt
    display_name_zh TEXT,              -- Tên Hán tương ứng
    authority_name_vi TEXT,            -- Tên authority DILA (fallback)
    authority_name_zh TEXT,
    appellation_vi TEXT,
    appellation_zh TEXT,
    style_type TEXT DEFAULT 'formal',
    is_preferred INTEGER DEFAULT 1,
    verification_status TEXT NOT NULL, -- verified_direct | verified_crosswalk | review_required | rejected
    source_type TEXT DEFAULT 'ttl',
    source_file TEXT NOT NULL,
    source_subject_uri TEXT,
    source_predicate TEXT DEFAULT 'rdfs:label',
    source_ref TEXT,
    mapping_method TEXT,
    mapping_evidence TEXT,
    import_run_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (person_id, locale, source_file)
)
```

### 3.2 Script ETL

**File:** `scripts/ttl_person_name_extractor.py`

- **Dry-run mode** (mặc định): tạo CSV report, không ghi DB
- **Apply mode** (`--apply`): ghi vào `person_display_names`
- Xử lý 2 định dạng TTL: root files (literal URIs) và subdir files (expanded URIs)
- Dedup logic: subdir file ưu tiên hơn root file khi cùng stem

### 3.3 Resolver Pattern

**Hàm:** `_t86_resolve_display_name(conn, person_id, node)` trong `app.py`

```python
# Priority: verified_direct > verified_crosswalk > authority fallback (DILA)
```

Output structure:
```json
{
  "primary": "Viên Ngộ Khắc Cần",
  "secondary": "圜悟克勤",
  "authority_primary": "Khắc Cần",
  "authority_secondary": "",
  "source_type": "ttl",
  "source_file": "TS-Vien-Ngo-Khac-Can.ttl",
  "verification_status": "verified_direct",
  "is_formal_name": true
}
```

---

## 4. Thay Đổi UI

### 4.1 Node Label (vis.js)

Hàm `_t86NodeLabel()` trong `places.html`:
- Nếu `display_name.is_formal_name === true`: dùng `display_name.primary` (tên trang trọng TTL)
- Fallback: `_fmtName(n.name_vi, n.name_zh)` hoặc DILA ID

### 4.2 Inspector Panel

Khi node có `is_formal_name: true`:
- Header: tên trang trọng tiếng Việt (lớn, đậm)
- Subtitle: tên Hán tương ứng
- **Khung xanh "TÊN HIỂN THỊ VIỆT"** với:
  - Tên trang trọng
  - Tên authority DILA (để so sánh)
  - Nguồn tên: Kho TTL nội bộ
  - Tên file TTL nguồn
  - Phương pháp xác minh

Khi không có formal name:
- Hiển thị tên DILA authority như trước
- Badge xám "Đang hiển thị tên authority DILA"

---

## 5. Xác Minh API & UI

### 5.1 API Verification

```
GET /daoanh/api/monk/A000453/lineage-tree?up=1&down=0
```

Kết quả node trung tâm:
```json
{
  "id": "A000453",
  "display_name": {
    "primary": "Viên Ngộ Khắc Cần",
    "secondary": "圜悟克勤",
    "is_formal_name": true,
    "verification_status": "verified_direct",
    "source_file": "TS-Vien-Ngo-Khac-Can.ttl"
  }
}
```

### 5.2 UI Verification (Screenshot)

- Tab TRUYỀN THỪA: Node center hiển thị "Viên Ngộ Khắc Cần ★" ✅
- Inspector panel: Khung xanh "TÊN HIỂN THỊ VIỆT" xuất hiện ✅
- "Tên trang trọng: Viên Ngộ Khắc Cần" ✅
- "Tên authority DILA: Khắc Cần" ✅
- "Xác minh: Khớp tiếp qua ttl_mapping" ✅

---

## 6. Quy Tắc An Toàn

Theo đặc tả, các ràng buộc sau đã được tuân thủ:

| Ràng buộc | Trạng thái |
|-----------|-----------|
| Không hard-code riêng A015811, 明 hoặc 銀城防 | ✅ Resolver chung |
| Không dùng LLM/API dịch máy | ✅ Chỉ dùng rdflib + ttl_mapping |
| Không migration/import không cần thiết | ✅ Script có dry-run trước |
| Không gán tên Việt ZQ cho nguồn DILA | ✅ TTL source riêng biệt |
| Không phá schema DILA/CBETA | ✅ Bảng mới `person_display_names` |
| Không commit Gemini API key | ✅ Key không thay đổi |
| Raw DILA data không bị sửa | ✅ Bảng `people` nguyên vẹn |
| Graph dùng DILA person_id, không dùng display name | ✅ Edge relations không đổi |
| Mapping có provenance đầy đủ | ✅ source_file, source_subject_uri, mapping_method |

---

## 7. Deliverables

| File | Mô tả |
|------|-------|
| `scripts/ttl_person_name_extractor.py` | ETL script với dry-run + apply |
| `docs/TTL_PERSON_NAME_IMPORT_DRY_RUN.csv` | 1,039 rows — toàn bộ extraction |
| `docs/TTL_PERSON_NAME_REVIEW_QUEUE.csv` | 1,032 rows cần human review |
| `docs/TTL_PERSON_NAME_IMPORT_RESULT.csv` | 7 rows đã apply vào DB |
| `docs/TTL_PERSON_FORMAL_NAME_INTEGRATION_REPORT.md` | Báo cáo này |
| `app.py` | Thêm `_t86_resolve_display_name()` + `nd['display_name']` |
| `places.html` | Cập nhật `_t86NodeLabel()` + inspector "TÊN HIỂN THỊ VIỆT" |

---

## 8. Hạn Chế & Bước Tiếp Theo

### 8.1 Hạn Chế Hiện Tại

**Tỷ lệ xác minh thấp (7/1,039 = 0.67%):**

Nguyên nhân: Bảng `ttl_mapping` chỉ có 7 record (crosswalk thủ công giữa TTL filename và DILA ID). Phần lớn 1,028 file TTL bị `rejected` vì không tìm được DILA ID tương ứng.

**Tên Hán DILA bị viết tắt:**

DILA `people.name_zh` lưu dạng viết tắt (ví dụ: `克勤` thay vì `圜悟克勤`), nên không thể exact-match tự động với tên trong TTL.

### 8.2 Bước Tiếp Theo Đề Xuất

1. **Human curation** `ttl_mapping`: Học giả review `TTL_PERSON_NAME_REVIEW_QUEUE.csv`, thêm DILA ID cho từng TTL file → chạy lại extractor → tỷ lệ verified tăng dần
2. **Search index**: Index `display_name_vi` vào autocomplete search (Phase 6 còn lại)
3. **Admin UI**: Trang review `review_queue` để scholar xác nhận/từ chối từng record
4. **Phase 8 Tests**: Unit tests cho `_t86_resolve_display_name()` và extractor functions

---

## 9. Hai Định Dạng TTL — Ghi Chú Kỹ Thuật

Root files (`TS-*.ttl`, `Bo-Tat-*.ttl`) dùng angle-bracket URIs được lưu literal trong rdflib:

```python
# Root files: URIRef('bkg:Monk'), URIRef('crm:P1_is_identified_by')
MONK_TYPE_RAW = URIRef("bkg:Monk")
CRM_P1_RAW    = URIRef("crm:P1_is_identified_by")
```

Subdir files (`Lam Te Duong Ky/`, `Thien Tong Trung Quoc/`) dùng proper prefix notation:

```python
# Subdir files: expanded full URI
MONK_TYPE_FULL = BKG_NS.Monk  # http://www.phatphaponline.org/ontology/buddhist-kg#Monk
CRM_P1_FULL    = CRM_NS.P1_is_identified_by
```

Extractor kiểm tra cả hai dạng trong mọi truy vấn rdflib.

---

*Báo cáo được tạo tự động bởi Claude Code build agent — 2026-09-06*
