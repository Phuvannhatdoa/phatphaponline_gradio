# TGS Integration Master Plan — Tuệ Giác Số
**Phiên bản:** 2026-08-24  
**Phạm vi:** Đánh giá 20 nguồn dữ liệu Phật giáo quốc tế, ánh xạ vào PTDA, lộ trình tích hợp

---

## Bức Tranh Toàn Cảnh

PTDA (Phật Tổ Đạo Ảnh) hiện đang xây dựng **"Tuệ Giác Số" (TGS)** — trung tâm trí tuệ Phật giáo đa ngôn ngữ, đa truyền thống. Để tránh trùng lặp và phân tán nguồn lực, cần phân loại rõ 20 nguồn theo chiến lược:

| Chiến lược | Nghĩa | Các nguồn |
|---|---|---|
| **CORE** | Đã tích hợp sâu, là nền tảng | CBETA, DILA/DDBC/Marcus, ZQLOCAL, BGIS, Wikidata |
| **EXPAND** | Cần tích hợp thật, đang trong lộ trình | 84000, VRI/SuttaCentral, Kanripo |
| **BRIDGE** | Tích hợp layer mỏng, cross-reference | SAT, BuddhaNexus, CHGIS, TGAZ |
| **ASSESS** | Đang đánh giá, có giá trị nhưng phức tạp | Treasury of Lives, PTS, IDP, DSBC, GRETIL |
| **SKIP** | Quyết định không tích hợp, có lý do | BDRC (T18), OCBS (không phải DB), THL (overlap BDRC) |

---

## Đánh Giá Chi Tiết 20 Nguồn

### ✅ CORE — Đã Tích Hợp

---

#### 1. CBETA (Chinese Buddhist Electronic Text Association)
**Trạng thái PTDA:** ✅ TÍCH HỢP ĐẦY ĐỦ — Nền tảng Hán Tạng  
**Dữ liệu trong DB:** `cbeta_catalog_vn` (3,122 texts có tên Việt), `places_dila.listbibl` (FK chuẩn)  
**Route tin cậy:** `GET /daoanh/api/places/<id>/cbeta` — duy nhất được phép dùng cho UI  
**License:** CC BY-SA 4.0  
**Hành động:** Không cần gì thêm ở tầng core. T20 (X-series) là mở rộng tự nhiên.

---

#### 2. Dharma Drum Buddhist College (DDBC) / DILA
**Trạng thái PTDA:** ✅ TÍCH HỢP ĐẦY ĐỦ — Authority tối cao về địa danh Phật giáo Hán Truyền  
**Dữ liệu trong DB:** `places_dila` (59,167 rows), `entity` (59,167 text IDs 'PL…'), `entity_hub`, `entity_claims`  
**Ghi chú quan trọng:** DILA dataset = **công trình của Marcus Bingenheimer** (GIS #17 trong danh sách) — đây là cùng một nguồn, không phải hai nguồn khác nhau.  
**Hành động:** Không cần gì. Marcus GIS (#17) đã là DILA.

---

#### 16. BGIS (Buddhist GIS)
**Trạng thái PTDA:** ✅ TÍCH HỢP — T31 done (2026-08-24)  
**Đóng góp:** 33 GPS cross-refs (29 verified, 4 likely) trong `geo_cross_ref.bgis_id`  
**Phát hiện quan trọng:** BGIS không có founding date lịch sử (YEAR_START=2006 = năm xuất bản), 83.5% tọa độ là centroid hành chính  
**Hành động:** Không cần gì. Đã done.

---

#### 17. Marcus Bingenheimer's GIS
**Trạng thái PTDA:** ✅ = DILA (#2) — cùng nguồn, không phải khác nhau  
Marcus Bingenheimer tạo ra DILA database cho DDBC. Dữ liệu đã trong `places_dila`.  
**Hành động:** Không làm gì. Đây không phải nguồn riêng.

---

#### 20. Wikidata P1188 (Buddhist sites)
**Trạng thái PTDA:** ✅ TÍCH HỢP — bridge P112 (founder) cho lineage  
**Trong code:** `app.py` T28 routes dùng Wikidata P112 để lấy founder của địa điểm  
**Lưu ý:** Wikidata là "cổng nối" — KHÔNG phải nguồn authority. Cần bộ lọc xác thực.  
**Hành động:** Chỉ dùng Wikidata khi DILA/CBETA không có data. Không mở rộng thêm.

---

### ⚠️ EXPAND — T34 Đang Triển Khai

---

#### 5. Kanripo (Digital Archive of Buddhist Studies)
**Trạng thái PTDA:** ⚠️ Schema có, ETL cần làm (T34 Giai đoạn B)  
**Vai trò đúng:** Bổ sung CBETA Hán Tạng — cung cấp critical editions và variant readings  
**Dữ liệu trong DB:** `kanripo_catalog` (3 seed rows — text IDs thật), `kanripo_place_mapping`, `kanripo_text_cache`  
**Route:** `GET /daoanh/api/places/<id>/kanripo` — hoạt động kỹ thuật, cần data thật  
**License:** CC BY-SA 4.0  
**ETL plan:** GitHub API `github.com/kanripo/` → metadata → cross-ref CBETA T# → DILA  
**Ưu tiên:** MEDIUM — Giai đoạn B của T34

---

#### 3. 84000 (Translating the Words of the Buddha)
**Trạng thái PTDA:** ⚠️ Schema có, data FAKE + sai học thuật (T34 Giai đoạn D)  
**Vai trò đúng:** Tạng Truyền (Tibetan Canon) — Toh cross-reference với CBETA + Glossary  
**Dữ liệu trong DB:** `eight_four_thousand` (3 rows SAI), `eight_four_thousand_place_map` (3 rows vô nghĩa)  
**Lỗi nghiêm trọng:** Heart Sutra Toh=44 (đúng là Toh 21), Platform Sutra trong Kangyur (không tồn tại)  
**KHÔNG làm:** map Tibetan texts → địa danh Hán truyền (Thiếu Lâm Tự v.v.)  
**Đúng là:** `toh_cbeta_crossref` table + Glossary lookup  
**Ưu tiên:** MEDIUM — Giai đoạn D của T34

---

#### 4. Vipassana Research Institute (VRI) / Tipitaka.org
**Trạng thái PTDA:** ⚠️ Schema có, data FAKE + lỗi học thuật nghiêm trọng (T34 Giai đoạn C)  
**Vai trò đúng:** Nam Truyền (Pali Canon) — chỉ liên kết địa danh Ấn Độ cổ đại  
**Lỗi nghiêm trọng:** 42 rows Pali suttas map → Thiếu Lâm Tự (học thuật không thể chấp nhận)  
**Khuyến nghị:** Thay bằng **SuttaCentral** (có API + bản dịch tiếng Việt Thích Minh Châu)  
**Ưu tiên:** MEDIUM — Giai đoạn C của T34

---

### 🔗 BRIDGE — Tích Hợp Layer Mỏng, Giá Trị Cao

---

#### 6. SAT Daizōkyō Text Database (Đại Tạng Kinh SAT — Nhật Bản)
**Nguồn:** `21dzk.l.u-tokyo.ac.jp/SAT/` (Đại học Tokyo)  
**Nội dung:** Hán Tạng — cùng corpus với CBETA, bổ sung một số texts Nhật Bản và chú giải  
**Overlap với CBETA:** ~85% trùng (cùng T-series Taishō)  
**Giá trị độc nhất:** Texts không có trong CBETA (Nhật Bản chú giải, bản Nhật), Kanji Unicode chuẩn  
**License:** CC BY 4.0 (từ 2022)  
**API:** SAT có IIIF API + REST endpoint cho text lookup  
**Chiến lược PTDA:**
- KHÔNG import toàn bộ (quá trùng với CBETA)
- CHỈ: cross-reference SAT text ID khi user đang xem CBETA text → badge "Xem trên SAT"
- Bảng: `sat_crossref(cbeta_sigla, sat_id)` — lightweight mapping
**Ưu tiên:** LOW — task mới T35 (sau T34)

---

#### 8. BuddhaNexus (Text Reuse / Parallel Passages)
**Nguồn:** `buddhanexus.net` (Khyentse Foundation + đối tác)  
**Nội dung:** Phân tích đối chiếu văn bản — tìm đoạn văn xuất hiện trong nhiều kinh khác nhau  
**Ví dụ:** Đoạn "Tứ Đế" xuất hiện trong DN 16 (Pali) + T 99 (Hán Tạng) + Toh 310 (Tây Tạng)  
**API:** `api.buddhanexus.net/graphql` (GraphQL API công khai)  
**Giá trị cho TGS:**  
- Tab "Giáo Lý": hiển thị "Đoạn này cũng xuất hiện trong [X kinh khác]"
- Cross-tradition: khi xem CBETA text → "Pali parallel: DN X" → liên kết SuttaCentral
- Là cầu nối học thuật giữa Hán / Pali / Tây Tạng — đúng mục tiêu "Tam Tạng"
**Chiến lược PTDA:**
- Không import dữ liệu BuddhaNexus vào DB (quá lớn, domain riêng)
- Gọi API realtime khi cần: `buddhanexus.net/api/v2/parallels/<text_id>`
- Thêm "Parallel Passages" section trong tab Đại Tạng
**Ưu tiên:** MEDIUM — task mới T36

---

#### 18. CHGIS (China Historical GIS — Harvard)
**Nguồn:** `chgis.fas.harvard.edu` (Harvard University)  
**Nội dung:** GIS lịch sử Trung Hoa — ranh giới hành chính qua các triều đại, địa danh lịch sử  
**Overlap với DILA:** Địa danh hành chính (tỉnh/huyện/phủ) — không phải chùa/tự viện  
**Giá trị cho TGS:**
- Khi xem chùa ở tỉnh X → "Thuộc [Tỉnh Y triều đại Z] theo CHGIS"
- Nâng cao lớp lịch sử trong tab Niên Đại (liên kết với T21)
- API: dataset download (không có REST API đơn giản)
**Chiến lược PTDA:**
- Import một lần dữ liệu tỉnh/huyện lịch sử cần thiết (không toàn bộ)
- Bảng: `chgis_admin_units(chgis_id, dynasty, name_zh, geom_wkt)` → cross-ref với `places_dila`
**Ưu tiên:** LOW — phụ thuộc T21 (timeline) trước

---

#### 19. TGAZ (Harvard China Historical GIS Gazetteer API)
**Nguồn:** `maps.cga.harvard.edu/chgis/` (Harvard CGA)  
**Nội dung:** API tra cứu địa danh lịch sử Trung Hoa theo tọa độ hoặc tên  
**Giá trị cho TGS:**
- Tự động hóa: cho GPS tọa độ một chùa → query TGAZ → lấy tên hành chính lịch sử
- Bổ sung context lịch sử cho tab Niên Đại mà không cần import toàn bộ CHGIS
**Chiến lược PTDA:**
- Gọi API realtime hoặc batch job cho các địa điểm có GPS trong `geo_cross_ref`
- Lưu kết quả vào `places_dila.admin_hist` hoặc bảng mới
**Ưu tiên:** LOW — phụ thuộc T21

---

### 📋 ASSESS — Cần Đánh Giá Thêm Trước Khi Quyết Định

---

#### 7. Treasury of Lives (Biographies of Himalayan Masters)
**Nguồn:** `treasuryoflives.org` (online encyclopedia)  
**Nội dung:** Tiểu sử hơn 6,000+ vị thầy Phật giáo Tây Tạng/Himalaya  
**Overlap:** Không overlap với PTDA hiện tại (PTDA tập trung nhân vật Hán truyền)  
**Giá trị:** Cao nếu mở rộng sang Tạng Truyền (nhân vật T28 cho Tây Tạng)  
**Rào cản:** Cần copyright check; dữ liệu có license nhưng terms of use phức tạp  
**Chiến lược PTDA:**
- ASSESS — chỉ làm sau khi T34 Giai đoạn D (84000 Tạng truyền) ổn định
- Nếu làm: bổ sung cho T28 (Nhân Vật tab), không phải địa danh
**Ưu tiên:** LOW — sau T34

---

#### 9. Pali Text Society (PTS) Digital Editions
**Nguồn:** `palitext.com` (Oxford-based scholarly society)  
**Nội dung:** Bản hiệu đính Pali chuẩn nhất thế giới (Romanized Pali)  
**Rào cản:** Copyright nghiêm ngặt — PTS giữ copyright nhiều editions, không phải open data  
**Overlap với SuttaCentral:** Cao — SuttaCentral dùng PTS numbering nhưng data họ tự xây dựng  
**Chiến lược PTDA:**
- SKIP tích hợp trực tiếp — copyright không cho phép
- CHỈ dùng PTS numbering system (DN/MN/SN/AN/KN) như chuẩn tham chiếu
- SuttaCentral là nguồn thực tế cho Pali content
**Ưu tiên:** SKIP trực tiếp; dùng SuttaCentral thay thế

---

#### 10. International Dunhuang Project (IDP)
**Nguồn:** `idp.bl.uk` (British Library)  
**Nội dung:** Bản thảo Dunhuang (敦煌) — ảnh scan + metadata  
**Phạm vi:** Cực kỳ chuyên biệt — chỉ văn bản phát hiện ở Dunhuang (Cam Túc)  
**Giá trị:** Học thuật cao, nhưng không phải "kinh điển chuẩn" — là văn bản thủ tịch  
**Chiến lược PTDA:**
- ASSESS — chỉ hữu ích nếu PTDA mở rộng sang "Văn bản cổ / Thủ tịch"
- Nếu làm: IDP có IIIF API + REST endpoint cho ảnh + metadata
- Phụ thuộc có địa danh Dunhuang trong DILA không (địa điểm 敦煌 khả năng có)
**Ưu tiên:** VERY LOW

---

#### 11. GRETIL (Göttingen Register of Electronic Texts in Indian Languages)
**Nguồn:** `gretil.sub.uni-goettingen.de` (Đại học Göttingen, Đức)  
**Nội dung:** Sanskrit Buddhist texts (Mahayana sutras gốc Sanskrit)  
**Giá trị:** Xem text gốc Sanskrit khi CBETA có bản Hán dịch  
**Rào cản:** Không có API chuẩn, data trong nhiều format (TEI, plain text, Unicode)  
**Chiến lược PTDA:**
- ASSESS — giá trị học thuật cao nhưng kỹ thuật phức tạp
- Nếu làm: tầng "Sanskrit Original" cho Mahayana sutras (Kim Cang, Tâm Kinh...)
- Cần ETL script custom để parse GRETIL format
**Ưu tiên:** LOW — sau DSBC đánh giá

---

#### 12. THL (Tibetan and Himalayan Library — UVA)
**Nguồn:** `thlib.org` (University of Virginia)  
**Nội dung:** Comprehensive Tibetan resources — text, ngữ điển, GIS  
**Overlap:** Cao với BDRC (Tibetan texts) và 84000 (translations)  
**Rào cản:** Data phân tán qua nhiều projects, không có single API  
**Chiến lược PTDA:**
- SKIP — bị superseded bởi 84000 (translations) và BDRC (raw texts, đã skip T18)
- THL tốt cho nghiên cứu nhưng quá phức tạp để tích hợp vào PTDA
**Ưu tiên:** SKIP

---

#### 13. Digital Sanskrit Buddhist Canon (DSBC — University of the West)
**Nguồn:** `dsbc.uwest.edu`  
**Nội dung:** Sanskrit Buddhist texts — bổ sung GRETIL  
**Giá trị:** Xem Sanskrit original song song với Hán dịch (CBETA)  
**Rào cản:** Website khá static, download bulk chứ không có REST API  
**Chiến lược PTDA:**
- ASSESS — làm sau GRETIL nếu cần Sanskrit layer
**Ưu tiên:** VERY LOW

---

#### 15. Oxford Centre for Buddhist Studies (OCBS)
**Nguồn:** `ocbs.org`  
**Nội dung:** Research centre — học bổng, conferences, publications  
**Loại:** KHÔNG phải database, không phải structured data  
**Chiến lược PTDA:**
- SKIP hoàn toàn — không phải nguồn dữ liệu có thể tích hợp API
**Ưu tiên:** SKIP

---

### ⛔ SKIP — Đã Quyết Định Không Tích Hợp

---

#### 14. BDRC (Buddhist Digital Resource Center)
**Trạng thái:** ⛔ SKIP — T18 đã quyết định (2026-08-23)  
**Lý do:** BDRC = Tạng ngữ (~10,000 places), PTDA = Hán truyền (59,167 places), giao nhau < 50  
**Mở lại khi:** Admin mở rộng scope sang địa danh Tây Tạng/Himalaya  
**Note:** 84000 (#3) phục vụ Tạng Truyền tốt hơn BDRC cho mục tiêu TGS

---

## Tóm Tắt Quyết Định — 20 Nguồn

| # | Nguồn | Chiến lược | Task | Ưu tiên |
|---|---|---|---|---|
| 1 | CBETA | ✅ CORE | T20 (X-series mở rộng) | LOW |
| 2 | DDBC/DILA | ✅ CORE | Xong | — |
| 3 | 84000 | ⚠️ EXPAND | T34 Giai đoạn D | MEDIUM |
| 4 | VRI→SuttaCentral | ⚠️ EXPAND | T34 Giai đoạn C | MEDIUM |
| 5 | Kanripo | ⚠️ EXPAND | T34 Giai đoạn B | MEDIUM |
| 6 | SAT | 🔗 BRIDGE | T35 (mới, cross-ref chỉ) | LOW |
| 7 | Treasury of Lives | 📋 ASSESS | Sau T34 | LOW |
| 8 | BuddhaNexus | 🔗 BRIDGE | T36 (mới, API realtime) | MEDIUM |
| 9 | PTS | ⛔ SKIP | Dùng SuttaCentral thay | — |
| 10 | IDP Dunhuang | 📋 ASSESS | Sau scope mở rộng | VERY LOW |
| 11 | GRETIL | 📋 ASSESS | Sau Sanskrit scope | LOW |
| 12 | THL | ⛔ SKIP | Overlap BDRC+84000 | — |
| 13 | DSBC | 📋 ASSESS | Sau GRETIL | VERY LOW |
| 14 | BDRC | ⛔ SKIP | T18 đã quyết định | — |
| 15 | OCBS | ⛔ SKIP | Không phải DB | — |
| 16 | BGIS | ✅ CORE | T31 done | — |
| 17 | Marcus GIS | ✅ CORE | = DILA, đã xong | — |
| 18 | CHGIS | 🔗 BRIDGE | Sau T21 | LOW |
| 19 | TGAZ | 🔗 BRIDGE | Batch job sau T21 | LOW |
| 20 | Wikidata | ✅ CORE | T28 đang dùng | — |

---

## Lộ Trình Task — TGS Integration

### Giai Đoạn 1 (Ngay bây giờ — T34)
```
T34: Tam Tạng Integration
├── Giai đoạn A: Xóa fake data 84000/VRI [cần admin OK]
├── Giai đoạn B: Kanripo ETL thật (GitHub API)
├── Giai đoạn C: SuttaCentral ETL (Pali → địa danh Ấn Độ)
└── Giai đoạn D: 84000 toh_cbeta_crossref + Glossary
```

### Giai Đoạn 2 (Sau T34)
```
T35: SAT cross-reference (lightweight, badge "Xem trên SAT")
T36: BuddhaNexus parallel passages API (tab Giáo Lý)
T20: CBETA X-series catalog (mở rộng CBETA)
```

### Giai Đoạn 3 (Dài hạn — sau khi Giai đoạn 1+2 ổn)
```
CHGIS/TGAZ: Historical administrative context (sau T21)
Treasury of Lives: Tibetan master biographies (sau T34 Giai đoạn D)
GRETIL/DSBC: Sanskrit layer (nếu scope mở rộng)
```

---

## Tasks Cần Remove / Decommission

### T13 — CBDB Chatling AI
**Lý do remove:** 
- CBDB (China Biographical Database, Harvard) không nằm trong 20 nguồn ưu tiên
- Task phụ thuộc vào Gemini API key (đang treo)
- Chức năng "AI chatling" bị superseded bởi T11 (RAG Việt) nếu/khi mở lại
- Scope hẹp: CBDB chủ yếu là nhân vật lịch sử Trung Quốc, không phải Phật giáo riêng

**Quyết định đề xuất:** → `status: cancelled` — chức năng AI sẽ được T11 cover khi unblock

### T15 — Keyword Export Delete  
**Lý do review:**
- Task này export/delete keywords — cần admin xem lại mục tiêu có còn relevant không
- Không liên quan đến 20 nguồn TGS

**Quyết định đề xuất:** Admin xem `tasks/T15-keyword-export-delete.md` để xác nhận còn cần không

### T22 — NLP Founding Dates Pipeline (full)
**Lý do review:**
- T22.1 audit (đang làm) kết luận: 4.23% coverage từ reuse (không cần NLP)
- Nếu T22.1 kết luận "không cần NLP" → T22 có thể cancel
- **Chưa cancel** — chờ T22.1 Gate 1 decision từ admin

---

## Kiến Trúc TGS — HOME Page

Sau khi T34 hoàn thành, HOME hiển thị:

```
TGS — Tuệ Giác Số
├── 📚 TAM TẠNG KINH ĐIỂN
│   ├── 🟡 Hán Tạng (Bắc Truyền) — CBETA + Kanripo [HOẠT ĐỘNG]
│   ├── 🔵 Pali Tạng (Nam Truyền) — SuttaCentral [T34 Giai đoạn C]
│   └── 🟠 Tây Tạng (Tạng Truyền) — 84000 cross-ref [T34 Giai đoạn D]
│
├── 🗺️ BẢN ĐỒ PHẬT GIÁO — DILA + BGIS + CHGIS (historical)
│
├── 🔗 THAM CHIẾU CHÉO
│   ├── BuddhaNexus — parallel passages [T36]
│   └── SAT Daizōkyō — cross-ref Nhật [T35]
│
└── 👤 NHÂN VẬT — DILA persons + Wikidata + Treasury of Lives (tương lai)
```

---

## Nguyên Tắc Chống Trùng Lặp

1. **DILA là trục** — mọi nguồn đều phải map vào DILA ID (`PL…`), không map sang nhau trực tiếp
2. **Kanripo/SAT → qua CBETA** — Kanripo text → CBETA T# → DILA (không direct)
3. **84000 → qua Toh#** — không map Toh directly vào places_dila (sai truyền thống)
4. **VRI/SuttaCentral → địa danh Ấn Độ cổ** — không map Pali texts vào chùa Trung Hoa
5. **ZQ là bridge tiếng Việt** — tất cả tên Việt từ ZQ, không gán nhầm cho nguồn nước ngoài
6. **Wikidata là last resort** — không phải authority, chỉ dùng khi không có data từ DILA/CBETA
