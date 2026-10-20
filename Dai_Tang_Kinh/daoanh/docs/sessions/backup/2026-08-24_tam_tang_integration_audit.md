# Audit Tích Hợp Tam Tạng — 84000 / VRI / Kanripo
**Ngày:** 2026-08-24  
**Mục tiêu:** Phân tích hiện trạng và lộ trình tích hợp 3 repo để mở rộng PTDA từ "Hán Truyền" sang "Tam Tạng Kinh Điển"

---

## Bức Tranh Toàn Cảnh — Tam Tạng Trong Kế Hoạch PTDA

| Truyền thống | Ngôn ngữ gốc | Repo | Hiện trạng |
|---|---|---|---|
| **Bắc Truyền / Hán Tạng** | Hán cổ | CBETA + Kanripo | ✅ CBETA hoạt động; Kanripo partial |
| **Nam Truyền / Pali Tạng** | Pali | VRI / Tipitaka.org | ⚠️ Schema có, data giả |
| **Tạng Truyền / Tây Tạng** | Tạng ngữ | 84000 | ⚠️ Route có, data hoàn toàn sai |

---

## 1. KANRIPO — Trạng Thái Tốt Nhất Trong 3

### Hiện trạng thực tế
- **DB tables:** `kanripo_catalog` (3 rows), `kanripo_place_mapping` (2 rows), `kanripo_text_cache` (0 rows)
- **API route:** `GET /daoanh/api/places/<id>/kanripo` — đã implement trong app.py (lines 10398-10436)
- **Text IDs có thật:** KR6s0102 (`大藏聖教法寶標目`), KR6a0001 (`長阿含經`), KR6e0162 (Tantra text)
- **Mapping:** KR6a0001 → PL000000000001 (confidence 0.7) — ID đích là placeholder

### Vai trò đúng trong PTDA
Kanripo = **bổ sung cho CBETA Hán Tạng**, không phải truyền thống riêng biệt:
- Cung cấp **bản hiệu đính phê bình** (critical editions) và **dị bản** mà CBETA chưa có
- `長阿含經` KR6a0001 = CBETA T1 — cùng kinh, Kanripo có variant readings từ nhiều bản thảo
- Không nên hiển thị riêng trong "Tam Tạng" mà bổ sung vào phần **Hán Tạng** của CBETA

### Đánh giá học thuật
- ✅ Text IDs thật, GitHub repos tồn tại: `github.com/kanripo/KR6a0001` v.v.
- ✅ License CC BY-SA 4.0 rõ ràng
- ⚠️ 3 rows là seed/demo, chưa ETL thật
- ⚠️ `KR6a0001 → PL000000000001`: PL000000000001 là gì? Cần xác minh — nếu là catch-all thì mapping vô nghĩa

### Kế hoạch tích hợp thật
1. ETL từ GitHub API: `https://api.github.com/orgs/kanripo/repos` → liệt kê text repos
2. Mỗi repo → clone metadata (title_zh, category, cbeta_ref nếu có)
3. Cross-reference: `kanripo_catalog.cbeta_ref` → `cbeta_catalog_vn.sigla` → `places_dila.listbibl`
   → đây là cách mapping Kanripo text → DILA place **qua CBETA**, không mapping trực tiếp
4. Script: `scripts/etl_kanripo_catalog.py`

---

## 2. VRI / TIPITAKA.ORG — DATA GIẢ, CẦN RESET HOÀN TOÀN

### Hiện trạng thực tế
- **DB tables:** `vri_tipitaka_catalog` (3 rows GIẢ), `vri_place_mapping` (42 rows GIẢ), `vri_cached_texts` (31 rows GIẢ)
- **API route:** `GET /daoanh/api/places/<id>/vri` — implement trong app.py (lines 10439-10488)

### ⚠️ Vấn đề học thuật nghiêm trọng trong data hiện tại

**Tất cả 42 rows `vri_place_mapping` đều map Pali suttas → Thiếu Lâm Tự (PL022435 / PL000000023255)**

Đây là **lỗi học thuật cơ bản**:
- VRI = Pali Tipitaka của truyền thống Theravāda (Ấn Độ → Sri Lanka → Đông Nam Á)
- Thiếu Lâm Tự là chùa Thiền Tông Trung Hoa thế kỷ 5 CN
- Pali suttas hoàn toàn KHÔNG nhắc đến chùa này — chúng được viết trước khi Phật giáo đến Trung Hoa hàng trăm năm
- Nếu để dữ liệu này lên HOME: người dùng học thuật sẽ mất tin ngay lập tức

**`vri_cached_texts`:** `text_pali = 'IDAM BUDDHAṂ... (Pali excerpt from vin1)'` — đây là placeholder, không phải Pali thật

**`title_zh = 'Tin1'`** trong `vri_tipitaka_catalog` — không phải Hán tự, rõ là generated text

### Vai trò đúng của VRI trong PTDA
VRI/Tipitaka.org = **Nam Truyền (Pali Canon)** — không map vào địa danh Hán truyền mà:
- Là tầng tham chiếu chéo: khi CBETA đề cập một địa danh Ấn Độ (vd. Vương Xá Thành 王舍城 = Rājagṛha), VRI có text Pali về cùng địa điểm đó
- Ứng dụng chính: tab "Giáo Lý" (Dhamma teachings) trên địa danh Ấn Độ cổ đại, không phải chùa Trung Hoa

**Lưu ý quan trọng:** Tipitaka.org VRI không có API công khai và không có sẵn Vietnamese translations.  
**SuttaCentral** (suttacentral.net) là lựa chọn tốt hơn: có API công khai + có bản dịch tiếng Việt (Thích Minh Châu).

### Kế hoạch xử lý
1. **XÓA NGAY** toàn bộ data trong 3 bảng VRI (fake data, lỗi học thuật)
2. **Đánh giá lại nguồn:** VRI vs SuttaCentral — khuyến nghị dùng SuttaCentral vì:
   - API: `suttacentral.net/api/suttaplex/<uid>?lang=vi`
   - Có bản dịch tiếng Việt chuẩn (Thích Minh Châu, CC BY-NC-SA 4.0)
   - Cùng dữ liệu Pali nhưng dễ tích hợp hơn
3. **Scope mapping đúng:** chỉ map Pali texts → địa danh Ấn Độ trong DILA (Rājagṛha, Vāiśālī, Sāvatthī, Bodh Gayā...) — không map vào địa danh Trung Hoa

---

## 3. 84000 — DATA SAI HOÀN TOÀN, DÙNG SAI MỤC ĐÍCH

### Hiện trạng thực tế
- **DB tables:** `eight_four_thousand` (3 rows SAI), `eight_four_thousand_place_map` (3 rows vô nghĩa)
- **API route:** `GET /daoanh/api/places/<id>/eight_four_thousand` — implement (lines 10328-10397)

### ⚠️ Lỗi học thuật trong data hiện tại

| Vấn đề | Chi tiết |
|---|---|
| Heart Sutra `toh=44` | SAI — Toh 44 là *Vimalakīrtinirdeśa*, Heart Sutra là Toh 21 |
| Platform Sutra `canon_section='Kangyur'` | SAI hoàn toàn — Platform Sutra (六祖壇經) là kinh Thiền Tông Trung Hoa, KHÔNG có trong Kangyur Tây Tạng |
| `eight_four_thousand_place_map`: `toh=44, dila_id=23255` | Vô nghĩa — Toh 44 là Vimalakīrti Sūtra, địa danh liên quan là Vaiśālī (Ấn Độ), không phải Thiếu Lâm Tự |
| `title_zh='惠能平南録'` cho Platform Sutra | Sai tên — tên đúng là `六祖壇經` |

### Vai trò đúng của 84000 trong PTDA

84000 = **Tạng Truyền (Tibetan Canon)** — HOÀN TOÀN khác với Hán Truyền (CBETA):

**84000 KHÔNG nên map vào địa danh Hán truyền** vì:
- Tibetan canon chứa texts dịch từ Sanskrit/Pali sang Tạng ngữ, không phải từ Hán
- Các địa danh trong Tibetan canon là địa danh Ấn Độ/Nepal/Tây Tạng cổ
- Thiếu Lâm Tự (Trung Hoa) không xuất hiện trong bất kỳ text Tạng nào

**84000 có thể đóng góp cho PTDA theo 2 cách:**

**Cách A — Sutra Cross-Reference (có giá trị học thuật):**
Nhiều Mahayana sutras tồn tại song song trong cả Hán Tạng (CBETA T-series) lẫn Tạng Tạng (84000 Toh numbers):
- Bát Nhã Tâm Kinh: CBETA T251 = 84000 Toh 21
- Kim Cang Kinh: CBETA T235 = 84000 Toh 16
- Kinh Hoa Nghiêm: CBETA T278 = 84000 Toh 44 (Avatamsaka)
→ Table `toh_cbeta_crossref(toh, cbeta_sigla, confidence)` — khi xem 1 kinh trong CBETA, hiển thị "Cũng có trong Tạng Tạng: Toh X"

**Cách B — Glossary/Term lookup (ứng dụng ngay):**
84000 có glossary thuật ngữ Phật học rất chuẩn (Sanskrit ↔ English ↔ Tibetan)
→ Click vào thuật ngữ khó trong văn bản → 84000 định nghĩa chuẩn
→ Đây chính là mục đích `trusted-sources.md` đã ghi: "Glossary | Click-to-define"

### Kế hoạch xử lý
1. **XÓA NGAY** data fake trong 2 bảng 84000
2. **Tạo thêm bảng** `toh_cbeta_crossref` (Cách A) — liên kết Toh ↔ CBETA T-number
3. **Không** map 84000 vào `places_dila` (địa danh Hán truyền) — sai truyền thống
4. ETL thật: 84000 có JSON API: `https://read.84000.co/api/translation-search.json`
   hoặc GitHub dataset: `https://github.com/84000/data`

---

## Kiến Trúc Đề Xuất — Tam Tạng Trên HOME

```
HOME PAGE — "Tam Tạng Kinh Điển" section
├── 🟡 Hán Tạng (Bắc Truyền)
│   ├── CBETA — 3,122 kinh có tên Việt ✅ HOẠT ĐỘNG
│   └── Kanripo — variant readings bổ sung (cần ETL thật)
├── 🔵 Pali Tạng (Nam Truyền)  
│   └── SuttaCentral/VRI — Nikaya texts
│       → chỉ map với địa danh Ấn Độ trong DILA (Rajgir, Vaishali, Sarnath...)
└── 🟠 Tây Tạng (Tạng Truyền)
    └── 84000 — sutra cross-reference (Toh ↔ CBETA T-number)
        + glossary terms
```

---

## Hành Động Ngay (theo thứ tự ưu tiên)

### 🔴 Khẩn cấp — Ngăn data sai lên HOME
1. XÓA data fake trong `eight_four_thousand`, `eight_four_thousand_place_map`
2. XÓA data fake trong `vri_tipitaka_catalog`, `vri_place_mapping`, `vri_cached_texts`
3. Giữ nguyên 3 bảng (schema đúng) nhưng để empty cho ETL thật sau

### 🟡 Ngắn hạn — Kanripo ETL thật
1. Script `etl_kanripo_catalog.py`: fetch từ GitHub Kanripo org → populate `kanripo_catalog`
2. Cross-reference: `kanripo.cbeta_ref` → `cbeta_catalog_vn` → `places_dila.listbibl`
3. Route `/kanripo` đã có — chỉ cần data thật

### 🟢 Trung hạn — SuttaCentral (thay VRI)
1. Quyết định: dùng SuttaCentral thay VRI (API tốt hơn, có tiếng Việt)
2. Chỉ map Pali texts → địa danh Ấn Độ cổ đại trong DILA
3. Rename bảng `vri_*` → `pali_*` nếu chuyển sang SuttaCentral

### 🔵 Dài hạn — 84000 Toh crossref + Glossary
1. Tạo `toh_cbeta_crossref` từ dữ liệu đã biết (Toh 21 = T251, etc.)
2. Fetch từ `read.84000.co/api` hoặc GitHub `84000/data`
3. Glossary term lookup cho tab Giáo Lý

---

## Ghi chú về Routes đã có trong app.py

Ba routes hiện có (lines 10328-10488) đều **hoạt động về mặt kỹ thuật** — chúng query đúng bảng, trả JSON đúng format. Vấn đề duy nhất là **data trong bảng là fake**. Sau khi xóa fake data và ETL thật, routes này sẽ dùng được ngay, không cần sửa backend.
