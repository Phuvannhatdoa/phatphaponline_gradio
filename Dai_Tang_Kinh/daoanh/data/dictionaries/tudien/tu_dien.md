# 📘 SPEC: TÍCH HỢP TỪ ĐIỂN PHẬT GIÁO → ĐẠO ẢNH (DILA)

## 1. Mục tiêu

Xây dựng hệ thống:

* Hợp nhất 22 bộ từ điển Phật giáo (StarDict format)
* Chuẩn hóa thành 1 nguồn dữ liệu thống nhất
* Trích xuất:

  * 🏯 Danh sách CHÙA / TỰ / VIỆN / TỔ ĐÌNH / ĐẠO TRÀNG
  * 👤 Danh sách TU SĨ (phục vụ truyền thừa)
* Đồng bộ với hệ thống Đạo Ảnh (DILA)
* Hỗ trợ mapping để tạo lớp GIS (Google Maps)

---

## 2. Cấu trúc dữ liệu đầu vào

### 📂 3 nhóm từ điển:

```
/dicts/
│
├── HanLam/        # Chuẩn học thuật (ưu tiên cao nhất)
├── PhoThong/      # Chuẩn phổ thông
└── ThamKhao/      # Tham khảo (ưu tiên thấp nhất)
```

* Tổng: **22 bộ từ điển**
* Format: **StarDict (text đã extract)**

### 📄 Format mỗi entry:

```
Line 1: TỪ (KEY)
Line 2: NGHĨA (VALUE)
```

Ví dụ:

```
Chùa Thiên Mụ
Ngôi chùa nổi tiếng tại Huế, xây dựng từ thời chúa Nguyễn...
```

---

## 3. Nguyên tắc hợp nhất dữ liệu

### 🔥 Priority (quan trọng):

```
HanLam > PhoThong > ThamKhao
```

### Rule:

* Nếu trùng từ:

  * Giữ nghĩa từ nguồn có priority cao hơn
* Nếu không trùng:

  * Thêm mới

### Output:

```json
{
  "Chùa Thiên Mụ": {
    "definition": "...",
    "source": "HanLam"
  }
}
```

---

## 4. Chuẩn hóa dữ liệu (Normalization)

### Xử lý trước khi lưu:

* Trim space
* Lowercase để so khớp
* Remove ký tự đặc biệt
* Normalize Unicode (NFC)

### Tạo thêm field:

```json
{
  "term": "Chùa Thiên Mụ",
  "normalized": "chua thien mu",
  "definition": "...",
  "source": "HanLam"
}
```

---

## 5. Trích xuất thực thể (Entity Extraction)

## 🎯 Mục tiêu:

### 5.1. Nhóm ĐỊA DANH PHẬT GIÁO

Detect các keyword:

* "chùa"
* "tự"
* "viện"
* "tổ đình"
* "đạo tràng"

Ví dụ match:

```
Chùa Thiên Mụ ✅
Thiếu Lâm Tự ✅
Tổ đình Bửu Long ✅
```

---

### 5.2. Nhóm TU SĨ

Detect:

* Hòa thượng
* Thượng tọa
* Đại đức
* Thiền sư
* Pháp sư

---

### Output Entity:

```json
{
  "type": "chua",
  "name": "Chùa Thiên Mụ",
  "normalized": "chua thien mu",
  "definition": "...",
  "source": "HanLam"
}
```

---

## 6. Export sang StarDict (cho Đạo Ảnh)

Sau khi extract:

* Tạo file StarDict riêng cho Đạo Ảnh:

```
daoanh_dict.txt
```

Format:

```
Chùa Thiên Mụ
Ngôi chùa nổi tiếng tại Huế...
```

---

## 7. Tích hợp vào Đạo Ảnh (DILA)

### 📂 Path:

```
/opt/phatphaponline_gradio/
└── truyenthua/
    └── visjs-app/
        └── Dai_Tang_Kinh/
            └── daoanh/
```

---

## 8. Luồng hoạt động (Flow)

### 🔁 Sync logic:

1. Admin nhập dữ liệu trong:

   ```
   daoanh/admin/
   ```

2. Ví dụ:

   ```
   Chùa Thiên Mục
   ```

3. System sẽ:

   * Normalize → `chua thien muc`
   * Search trong dictionary

4. Nếu match gần đúng:

   ```
   Chùa Thiên Mụ (dict)
   ≈ Chùa Thiên Mục (DILA)
   ```

→ Push vào queue:

```json
{
  "input": "Chùa Thiên Mục",
  "suggestion": "Chùa Thiên Mụ",
  "status": "pending_manual_check"
}
```

---

## 9. Fuzzy Matching (QUAN TRỌNG)

Dùng:

* Levenshtein distance
* hoặc fuzzy ratio

### Threshold:

```
>= 85% → đề xuất match
```

---

## 10. Admin Workflow

### 📋 Dashboard:

* Danh sách match:

| Input (DILA)   | Suggestion (Dict) | Action |
| -------------- | ----------------- | ------ |
| Chùa Thiên Mục | Chùa Thiên Mụ     | ✅ / ❌  |

---

### Action:

* ✅ Accept → lưu DB chính
* ❌ Reject → ignore

---

## 11. Database Schema (gợi ý)

### Table: `places`

```sql
id
name
normalized
definition
source
lat
lng
status
```

---

### Table: `match_queue`

```sql
id
input_name
suggested_name
score
status
created_at
```

---

## 12. Mục tiêu cuối cùng

### 🚀 Build hệ thống:

* 📍 Bản đồ chùa (GIS layer)
* 🧬 Truyền thừa tông phái (graph)
* 🔎 Search semantic theo từ điển
* 🔗 Liên kết:

  * Đạo Ảnh (DILA)
  * Từ điển
  * Google Maps

---

## 13. Yêu cầu kỹ thuật

### Backend:

* Python (ưu tiên)
* hoặc NodeJS

### Lib gợi ý:

* `rapidfuzz` (fuzzy match)
* `unidecode`
* `json`
* `sqlite` / `postgres`

---

## 14. Deliverables

### Dev cần build:

* [ ] Script merge 22 dict
* [ ] Script normalize
* [ ] Script extract entities
* [ ] Script export StarDict
* [ ] API search dictionary
* [ ] API fuzzy match
* [ ] Admin queue UI (simple)

---

## 15. Note quan trọng

* Không overwrite dữ liệu gốc
* Luôn giữ source để trace
* Ưu tiên Hàn Lâm tuyệt đối
* System phải scale được (sau này thêm dict mới)

---

# ✅ END SPEC
