# 20 Nguồn Tài Nguyên Uy Tín — Phật Tổ Đạo Ảnh / TGS

**Cập nhật:** 2026-08-31
**Nguyên tắc:** Mọi nghiên cứu tích hợp dữ liệu phải ưu tiên 20 nguồn này trước (theo chiến lược CORE/EXPAND/BRIDGE/ASSESS/SKIP — xem `docs/TGS-integration-masterplan.md`). Nếu không tìm được câu trả lời → mở rộng ra ngoài và báo cáo nguồn mới để admin duyệt bổ sung.

> **LEGAL STATUS (T78 — License Firewall):** từ 2026-08-31, mọi nguồn có `legal_status` riêng trong `data_sources` (tách khỏi Authority). 5 nguồn historical (DILA/CBETA/MARCUS/ZQLOCAL/Wikidata) = **AUDITING** (giữ data, muốn ingest mới → admin verify → ACTIVE); 8 nguồn còn lại (SAT/CHGIS/FoJin/Kanripo/SuttaCentral/84000/TGAZ/BDRC) = **UNKNOWN/BLOCKED** (chưa ingest mới). Xem `docs/SOURCE_REGISTRY.md` + `docs/LICENSE_FIREWALL.md`. Admin thêm nguồn theo dõi tại **Legal Check** (`/daoanh/admin/source_check.html`).

---

## Bảng Trạng Thái Tích Hợp (Agent Tích Hợp đọc file này)

> Status: `pending` | `researching` | `plan_ready` | `integrating` | `done`
> Strategy: `CORE` | `EXPAND` | `BRIDGE` | `ASSESS` | `SKIP` (theo TGS masterplan)
> `implemented` ở đây theo `source_authority` trong DB (Build 2 Phase D — matrix 13 nguồn, `implemented=0` = chưa có pipeline/data thật).

| # | Nguồn | Strategy | Status | Reg | Ghi chú |
|---|-------|----------|--------|-----|---------|
| 1 | CBETA | CORE | `done` | ✅ | `cbeta_catalog_vn` T-series; many claims TEXT_EVIDENCE |
| 2 | DILA/DDBC | CORE | `done` | ✅ | Primary authority — `places_dila`, `time_periods`, 293K claims |
| 3 | BGIS | CORE | `done` (T31) | — | GPS cross-ref only — KHÔNG có founding date |
| 4 | ZQLOCAL | CORE | `done` | ✅ | Tên Việt nội bộ, 118K claims |
| 5 | Wikidata | CORE | `integrating` | ✅ | 148 EXTERNAL_ID claims + `source_url` (Phase B) |
| 6 | MARCUS | CORE | `done` | ✅ | 11K networks + 18K references; NETWORK_EVIDENCE 22,332 |
| 7 | Kanripo | EXPAND | `integrating` | ✅ | Đã đăng ký matrix (imp=0); ETL T34-GĐB pending |
| 8 | SuttaCentral | EXPAND | `pending` | ✅ | Thay VRI; Đã đăng ký matrix (imp=0); T34-GĐC pending |
| 9 | 84000 | EXPAND | `pending` | ✅ | Đã đăng ký matrix (imp=0); Toh crossref T38; T34-GĐD pending |
| 10 | VRI/Tipitaka.org | EXPAND | `pending` | — | Được khuyến nghị thay bằng SuttaCentral |
| 11 | SAT (Tokyo) | BRIDGE | `integrating` | ✅ | Đã đăng ký matrix (imp=0); `sat_crossref` 2,913 (T35) |
| 12 | BuddhaNexus | BRIDGE | `done` (T36) | — | API `/cbeta/<sigla>/parallels`, cache 24h |
| 13 | CHGIS | BRIDGE | `pending` | ✅ | Đã đăng ký matrix (imp=0); chờ T21 |
| 14 | TGAZ | BRIDGE | `pending` | ✅ | Đã đăng ký matrix (imp=0); chờ T21 |
| 15 | Treasury of Lives | ASSESS | `pending` | — | Phả hệ Himalayan — sau T34-GĐD |
| 16 | IDP (Dunhuang) | ASSESS | `pending` | — | Bản thảo cổ Đôn Hoàng |
| 17 | GRETIL | ASSESS | `pending` | — | Validation Sanskrit/Pali |
| 18 | DSBC | ASSESS | `pending` | — | Kinh Sanskrit Bắc truyền |
| 19 | THL | SKIP | `decided` | — | Overlap BDRC (xem T18) |
| 20 | PTS | SKIP | `decided` | — | Copyright; dùng SuttaCentral thay thế |
| — | BDRC | SKIP (T18) | `done` (skip) | ✅ | Tibetan focus; data_sources id 2 active=0 |
| — | OCBS | SKIP | `decided` | — | Không phải DB — không tích hợp |
| — | FoJin | — | `registered` | ✅ | Đã đăng ký matrix (imp=0, score 40) |

<!-- EXTERNAL-SOURCES: nguồn ngoài 20 được admin duyệt thêm -->

### Nguồn mở rộng đã duyệt (ngoài 20 nguồn gốc)

| Nguồn | Nhóm | Status | Report | Ghi chú |
|-------|------|--------|--------|---------|
| BGIS (Jiang Wu) | Data (GIS) | `done` | T31 (2026-08-24) | GPS cross-ref only — KHÔNG có founding date |

---

## Chiến lược "Kiềng Ba Chân"

| Trụ cột | Vai trò | Nguồn tiêu biểu |
|---------|---------|----------------|
| **Tính Học thuật** | Chuẩn hóa phương pháp, validation layer | SAT, PTS, GRETIL, DSBC, OCBS |
| **Tính Dữ liệu** | Mass digitization, authority data | CBETA, BDRC, DDBC/DILA, Tipitaka.org, IDP |
| **Tính Công nghệ** | AI/text reuse, entity linking, cross-reference | BuddhaNexus, Kanripo, 84000, THL, Treasury of Lives |

---

## Nhóm 1 — Tính Dữ Liệu (Data Authority)

### 1. CBETA — Chinese Buddhist Electronic Text Association
- **Tổ chức:** CBETA, Đài Loan
- **GitHub:** `github.com/cbeta-org` · `github.com/cbeta-org/xml-model`
- **Format:** XML/TEI chuẩn chặt chẽ
- **Coverage:** Hán tạng đầy đủ — Taisho (T), Xuzangjing (X), Gaoli (K), v.v.
- **API:** Có — `api.cbeta.org`
- **License:** Open (với điều kiện attribution)
- **Ứng dụng TGS:**
  - Nền tảng kinh điển Hán tạng — ánh xạ sang Schema JSON của TGS
  - Schema `cbeta-org/xml-model` → chuẩn đóng gói bản dịch Hán văn
  - **Đã tích hợp một phần:** `cbeta_catalog_vn` (3,122 records), T-series JOIN với DILA places
- **Ưu tiên:** 🔴 Core — đã và đang tích hợp

### 2. BDRC — Buddhist Digital Resource Center (SKIPPED)

**Tình huống:** BDRC chủ yếu Tibetan Buddhist; Chinese Chan/Thiếu Lâm Tự không có trong BDRC. Theo quyết định admin, BDRC integration bị skip — giữ DILA/Wikidata/CHGIS làm nguồn chính cho các địa danh Hán truyền.

- **Tổ chức:** Buddhist Digital Resource Center, Boston USA (kế thừa TBRC của học giả E. Gene Smith)
- **GitHub:** `github.com/buda-base/buda` · `github.com/buda-base`
- **Format:** TTL (Linked Data), IIIF, JSON
- **Coverage:** Tạng tạng (Tibetan Canon), mở rộng Hán, Pali, Sanskrit
- **API:** `purl.bdrc.io/resource/` · SPARQL endpoint
- **Ontology:** `bdo:Place`, `bdo:Person`, `bdo:Work`, `bdo:placeEvent`
- **License:** CC BY 4.0
- **Ứng dụng TGS:**
  - Authority Data cho tên người, địa danh — gắn ID chuẩn quốc tế cho Tổ sư
  - `bdo:placeEvent` → founding/renovation/destroyed events (T21 timeline)
- **Lưu ý:** Tập trung Tibetan Buddhism; Chan/Chinese coverage hạn chế
- **Ưu tiên:** 🟡 Skipped — BDRC không cover Chinese Buddhist temples; DILA + Wikidata + CHGIS là nguồn chính cho PL000000023255 (Thiếu Lâm Tự)

### 3. DDBC / DILA — Dharma Drum Buddhist College
- **Tổ chức:** Dharma Drum Institute of Liberal Arts (Pháp Cổ Sơn), Đài Loan
- **GitHub:** `github.com/DILA-edu/Authority-Databases`
- **APIs:** `authority.dila.edu.tw` — Place, Person, Time, Bibliography
- **Wikidata bridge:** P1187 (person), P1188 (place)
- **Coverage:** 59,000+ địa danh, 48,000+ nhân vật Phật giáo Hán văn
- **Ứng dụng TGS:**
  - **Primary authority** cho place (DILA ID) và person
  - `time_periods` (117K rows): bộ chuyển đổi niên hiệu → dương lịch
  - P1188 bridge → Wikidata → founding date (T21)
- **Ưu tiên:** 🔴 Core — đang dùng làm authority chính

### 4. Tipitaka.org / VRI — Vipassana Research Institute
- **Tổ chức:** Vipassana Research Institute, Igatpuri, India
- **GitHub:** `github.com/tipitaka-org/tipitaka-data`
- **Format:** Dữ liệu thô Pali chuẩn mực nhất
- **Coverage:** Pali Tipitaka đầy đủ (Vinaya, Sutta, Abhidhamma)
- **Ứng dụng TGS:**
  - Reference Source cho Pali tạng — đối chiếu bản dịch Việt với nguyên tác Pali
  - Song ngữ Pali-Việt trên giao diện đọc kinh
  - Kho từ vựng Pali cho hệ thống học tập Tăng ni
- **Ưu tiên:** 🟠 Medium — khi mở rộng sang Nam truyền

### 4.5. BGIS — Buddhism Geographical Information System (bổ sung 2026-08-24)
- **Tổ chức:** University of Arizona — Investigator: Jiang Wu; GIS Editor: Lex Berman
- **Nguồn gốc dữ liệu:** Gui Weibing (biên tập), *Zhongguo Fojiao siyuan minglu 2006*
  (Danh mục tự viện Phật giáo Trung Quốc 2006). Hong Kong: Zhonghua fojiao chubanshe, 2006.
- **Phân phối qua:** BGIS, CHGIS, ECAI — Harvard Dataverse `doi:10.7910/DVN/VAYEUZ`
- **Format:** Shapefile (.shp/.dbf/.shx/.prj) + XLS/ODS song song, GBK encoding
- **License:** Academic use with attribution required (yêu cầu trích dẫn đầy đủ khi sử dụng)
- **Coverage:** 18,938 Buddhist sites Trung Quốc (monastery/temple/chapel/hall/association/...)
- **⚠️ Lưu ý quan trọng:** Trường `YEAR_START` trong dataset **KHÔNG phải founding date** — toàn bộ
  18,938 rows đều ghi `2006` (năm xuất bản cuốn danh mục nguồn). Không dùng BGIS để suy ra năm
  lập chùa.
- **⚠️ Lưu ý về tọa độ:** 83.5% tọa độ GPS trong BGIS bị trùng nhau giữa nhiều chùa khác nhau
  (geocode theo centroid hành chính cấp huyện/thị trấn, không phải vị trí chùa thực). Spatial-join
  chỉ dựa vào khoảng cách sẽ cho kết quả sai — bắt buộc phải kết hợp so khớp tên (xem `T31`).
- **Ứng dụng TGS:**
  - GPS cross-reference: `geo_cross_ref.bgis_id` — liên kết DILA place ↔ BGIS ID khi tên + tọa độ
    khớp đủ tin cậy (name similarity ≥ 0.4)
  - Kết quả T31 (2026-08-24): 33 matches đưa vào `geo_cross_ref` (29 verified sim≥0.6, 4 likely)
- **Ưu tiên:** 🟡 GPS enrichment only — không dùng cho founding date/timeline

### 5. IDP — International Dunhuang Project
- **Tổ chức:** British Library + 12 tổ chức quốc tế
- **GitHub:** `github.com/idp-uk`
- **URL:** `idp.bl.uk`
- **Coverage:** Bản thảo cổ Đôn Hoàng (manuscripts) — thế kỷ 4–11 CE
- **Format:** Hình ảnh IIIF + TEI text
- **Ứng dụng TGS:**
  - Reference Source cho văn bản cổ liên quan đến các đời Tổ sư
  - Xác thực văn bản cũ của ZenQ với primary sources
- **Ưu tiên:** 🟢 Research reference

---

## Nhóm 2 — Tính Học Thuật (Academic Standards)

### 6. SAT Daizōkyō Text Database — Đại học Tokyo
- **Tổ chức:** Đại học Tokyo (University of Tokyo), Japan
- **GitHub:** `github.com/SAT-Daizokyo`
- **URL:** `21dzk.l.u-tokyo.ac.jp/SAT/`
- **Coverage:** Hán tạng Taisho (T) — **chuẩn mực học thuật quốc tế cao nhất**
- **Đặc điểm:** Dữ liệu sạch tuyệt đối, phân đoạn chuẩn từng dòng từng ký tự
- **Ứng dụng TGS:**
  - Validation layer — so sánh với SAT trước khi import bất kỳ bộ kinh Hán nào
  - Hệ quy chiếu khi AI đối soát Đại Tạng Hán văn của ZenQ
- **Ưu tiên:** 🟠 Validation — dùng để verify CBETA data

### 7. PTS — Pali Text Society
- **Tổ chức:** Pali Text Society, UK (cơ quan chuẩn hóa Pali tạng toàn cầu)
- **GitHub:** `github.com/PaliTextSociety`
- **Coverage:** Pali Tipitaka chuẩn Latin transliteration
- **Ứng dụng TGS:**
  - Chuẩn quốc tế cho Kinh tạng Pali
  - Đối chiếu bản dịch Việt ngữ với nguyên tác Pali chuẩn
- **Ưu tiên:** 🟠 Medium — khi mở rộng Nam truyền

### 8. GRETIL — Göttingen Register of Electronic Texts in Indian Languages
- **Tổ chức:** Đại học Göttingen, Đức (Germany)
- **URL:** `gretil.sub.uni-goettingen.de`
- **Coverage:** Sanskrit, Pali, Prakrit — tiêu chuẩn vàng học thuật phương Tây
- **Đặc điểm:** Được kiểm duyệt kỹ lưỡng bởi chuyên gia ngôn ngữ học
- **Ứng dụng TGS:**
  - Validation layer cho văn bản Sanskrit/Pali
  - Đối chiếu nguyên tác trước khi đưa vào TGS
- **Ưu tiên:** 🟢 Validation — Sanskrit/Pali research

### 9. DSBC — Digital Sanskrit Buddhist Canon
- **Tổ chức:** University of the West (California) + học giả phương Tây
- **URL:** `dsbcproject.net`
- **Coverage:** Kinh điển Bắc truyền (Mahayana) bằng Sanskrit
- **Ứng dụng TGS:**
  - Cross-reference: bản dịch Hán văn (CBETA) ↔ nguyên tác Sanskrit (DSBC)
  - AI tự động trả lời: "Bản kinh Hán này có nguyên tác Sanskrit nào không?"
- **Ưu tiên:** 🟢 Research — khi cần đối chiếu Hán-Sanskrit

### 10. OCBS — Oxford Centre for Buddhist Studies
- **Tổ chức:** Đại học Oxford, UK
- **URL:** `ocbs.org`
- **Đặc điểm:** Kết hợp truyền thống Phật giáo + AI hiện đại phân tích kinh điển
- **Research focus:** Textual Reuse, NLP, AI-assisted Buddhist Studies
- **Ứng dụng TGS:**
  - Tích hợp libraries để AI tự động trích dẫn nghiên cứu mới nhất phương Tây
  - Hợp tác học thuật → tăng "Academic Credibility" cho TGS
- **Ưu tiên:** 🟢 Partnership — hợp tác học thuật lâu dài

---

## Nhóm 3 — Tính Công Nghệ (Technology & Innovation)

### 11. BuddhaNexus — Text Reuse Project
- **Tổ chức:** Liên minh quốc tế (IWoBS, Fragile Palm Leaves Foundation, v.v.)
- **GitHub:** `github.com/BuddhaNexus/buddhanexus-backend`
- **Công nghệ:** Machine Learning + NLP để phát hiện text reuse giữa các bộ kinh
- **Coverage:** Hán, Tạng, Pali, Sanskrit — cross-canon
- **Ứng dụng TGS:**
  - Recommendation Engine: "Đoạn ngữ lục này lấy ý từ Kinh A"
  - Khi user đọc kinh → tự động gợi ý trích dẫn từ các bộ kinh liên quan
  - Pipeline: ngữ lục Tổ sư ZenQ → BuddhaNexus → phát hiện kinh điển nguồn
- **Ưu tiên:** 🟠 AI Feature — text reuse detection

### 12. Kanripo — Digital Archive of Buddhist Studies
- **GitHub:** `github.com/kanripo`
- **Đặc điểm:** Liên kết cross-reference giữa các bản kinh, bình chú
- **Ứng dụng TGS:**
  - Tính năng: khi đọc kinh → gợi ý ngữ lục Tổ sư có trích dẫn từ kinh đó
  - "Bản đồ liên kết văn bản" giữa Đại Tạng và Ngữ Lục
- **Ưu tiên:** 🟠 Medium — cross-reference feature

### 13. 84000 — Translating the Words of the Buddha
- **Tổ chức:** 84000, USA/International
- **URL:** `read.84000.co`
- **Coverage:** Kangyur + Tengyur (Tạng tạng) — bản dịch tiếng Anh chuẩn mực
- **Đặc điểm:** Glossary thuật ngữ Phật học — mỗi khái niệm có link định nghĩa chuẩn
- **Ứng dụng TGS:**
  - Auto-chú giải: click thuật ngữ khó → AI hiện giải nghĩa chuẩn từ 84000
  - Glossary API → tích hợp vào giao diện đọc kinh
- **Ưu tiên:** 🟡 Glossary/UX feature

### 14. THL — The Tibetan and Himalayan Library
- **Tổ chức:** University of Virginia, USA + nhiều đại học phương Tây
- **GitHub:** `github.com/THDL`
- **Đặc điểm:** Mô hình Knowledge Base liên kết địa danh - nhân vật - văn bản - bản đồ - âm thanh
- **Ứng dụng TGS:**
  - **Bản mẫu kiến trúc** cho hệ thống Phả hệ Truyền thừa của Lee Tổng
  - Xây bản đồ số cho các đời Tổ sư — học hỏi cấu trúc THL
  - Mô hình "Knowledge Base" địa danh + nhân vật + văn bản
- **Ưu tiên:** 🟠 Architecture reference — phả hệ truyền thừa

### 15. Treasury of Lives — Biographies of Himalayan Masters
- **Tổ chức:** Treasury of Lives, international scholarly project
- **GitHub:** `github.com/treasury-of-lives`
- **Coverage:** Tiểu sử + phả hệ các bậc thầy Himalayan/Tibetan
- **Đặc điểm:** Lưu trữ mối quan hệ (gia phả/truyền thừa) giữa các Tổ sư — entity linking
- **Ứng dụng TGS:**
  - Bản mẫu hoàn hảo cho Phả Hệ Truyền Thừa của Lee Tổng
  - Mô hình "định danh thực thể" (Entity Linking) → áp dụng cho Thiền tông Việt Nam
  - AI học hỏi cách Treasury liên kết thầy-trò → xây phả hệ ZenQ
- **Ưu tiên:** 🟠 Architecture reference — phả hệ

---

## Quy trình nghiên cứu (Research Protocol)

Khi cần tích hợp tính năng mới hoặc data source mới:

```
1. Xác định câu hỏi: "Cần data gì?" (place timeline, text reuse, glossary, v.v.)

2. Research ưu tiên theo nhóm:
   - Nếu liên quan Hán tạng/địa danh/nhân vật → Nhóm 1 (CBETA, BDRC, DILA)
   - Nếu cần validation học thuật → Nhóm 2 (SAT, GRETIL, PTS)
   - Nếu cần AI/cross-reference → Nhóm 3 (BuddhaNexus, Kanripo, 84000)

3. Nếu 15 nguồn không trả lời được:
   → Mở rộng ra ngoài (Wikidata, CHGIS, BGIS, WHG, Marcus datasets, v.v.)
   → Trích nguồn URL + tên tổ chức đầy đủ
   → Báo cáo admin để duyệt bổ sung vào danh sách

4. Mọi data hiển thị phải có attribution rõ ràng (tên tổ chức + mã văn bản + link)
```

---

## Ma trận tích hợp hiện tại

> **Build 2 Phase D (2026-08-30/31):** matrix `source_authority` đã đăng ký 13 nguồn với `implemented` minh bạch. Các nguồn cross-ref mới đăng ký có `implemented=0` (chưa có pipeline/data thật) — chỉ set `implemented=1` khi ETL + data thật hoàn tất. Reversible via `scripts/build2_register_crossref_sources.py --undo`.

| Nguồn | Status | Module | Notes |
|-------|--------|--------|-------|
| DILA | ✅ Core | Place/Person/Time | `places_dila`, `time_periods`, `lineage_chronology`; authority 100 |
| CBETA | ✅ Core | Canon | `cbeta_catalog_vn`; TEXT_EVIDENCE 13,933 claims; authority 80 |
| BGIS | ✅ Done (T31) | GPS cross-ref | 33 `geo_cross_ref.bgis_id` — KHÔNG có founding date (xem ghi chú) |
| ZQLOCAL | ✅ Core | Tên Việt | 118,295 `zqlocal_content`; authority 50 |
| Wikidata | ✅ (B2-A/B) | Reference | 148 EXTERNAL_ID claims + `source_url` backfill; authority 25 |
| Marcus | ✅ Done | Person/Place | T04 SNA network; NETWORK_EVIDENCE 22,332; authority 60 |
| BDRC | ✅ Adapter | T18 (SKIP) | `bdrc_works` API adapter done; data_sources active=0; authority 40 |
| SAT | 🟡 Reg (B2-D) | Canon validation | `sat_crossref` 2,913 (T35); matrix imp=0; authority 75 |
| Kanripo | 🟡 Reg (B2-D) | Hán variants | Matrix imp=0; ETL T34-GĐB; authority 70 |
| SuttaCentral | 🟡 Reg (B2-D) | Pali Canon | Thay VRI; matrix imp=0; T34-GĐC; authority 50 |
| 84000 | 🟡 Reg (B2-D) | Tibetan Canon | Toh crossref T38; matrix imp=0; T34-GĐD; authority 45 |
| CHGIS | 🟡 Reg (B2-D) | Historical GIS | Matrix imp=0; chờ T21; authority 58 |
| TGAZ | 🟡 Reg (B2-D) | Historical gazetteer | Matrix imp=0; chờ T21; authority 55 |
| FoJin | 🟡 Reg (B2-D) | Hán corpus | Matrix imp=0; authority 40 |
| BuddhaNexus | ✅ Done (T36) | Text reuse | `/cbeta/<sigla>/parallels`, cache 24h |
| THL / Treasury | ❌ Not started | Lineage | Architecture reference / Himalayan |
| GRETIL, PTS, DSBC, IDP, OCBS | ❌ Not started | Research/validation | Chờ mở rộng scope
