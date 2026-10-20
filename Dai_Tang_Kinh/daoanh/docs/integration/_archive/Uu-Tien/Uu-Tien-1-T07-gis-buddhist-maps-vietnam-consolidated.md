# M7-VN · Buddhist Temple Maps Vietnam

**Status:** 📄 Consolidated Documentation  
**Module:** M7-VN (phụ trợ cho M7 bản toàn cầu — KHÔNG sửa file M7 gốc)  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

---

## Mục đích

Cung cấp hệ thống bản đồ chùa và địa danh Phật giáo **Việt Nam**: cho phép tra cứu, đối chiếu và xác minh tọa độ các chùa, tổ đình, tự viện, thiền viện tại lãnh thổ Việt Nam với độ tin cậy cao và nguồn dữ liệu đa tầng. Hỗ trợ nhu cầu lữ hành Phật tử, nghiên cứu địa danh và quản lý các cơ sở Phật giáo.

**Nguyên tắc cốt lõi (kế thừa quyết định đã chốt):**
- **Bỏ qua GPS DILA** cho phạm vi Việt Nam — DILA không phải nguồn GPS chùa VN hiện đại.
- **Ground truth GPS** = Wikidata (Tầng 0) + OpenStreetMap (Tầng 1).
- Format dữ liệu **mirror chuẩn DILA** nhưng ID namespace riêng `VN` (không chồng `PL`), GPS nằm trong lãnh thổ VN.
- Tuân thủ **Zero-RAM**, **3-Layer model**, **Code Preservation**.

---

## UI/UX

- **Trang Review địa lý chùa Việt:** `/daoanh/admin/vietnam_geo_review.html`
  - **Adapt** từ `geo_review.html` hiện có (/daoanh/admin/geo_review.html) — KHÔNG tạo hàng đợi trùng.
  - **Hàng đợi duyệt:** Mỗi dòng hiện hai ứng viên cạnh nhau (tên chùa, địa phận, tọa độ, nguồn dữ liệu).
  - Giữa hai bên là điểm khớp và khoảng cách. Các nút: Chấp nhận (Accept), Từ chối (Reject), Để sau (Later).
  - **Mini-map** cho mỗi ứng viên: Vẽ hai điểm và đường nối, đổi màu theo độ tin cậy (xanh: cao, vàng: trung bình, đỏ: thấp).
  - **Công cụ audit:** Hiển thị thông tin chi tiết cho từng ứng viên khi hover.

- **Trang Bản đồ chùa Việt:** `/daoanh/maps/vietnam`
  - Hiển thị tất cả chùa Việt kèm biểu tượng chùa.
  - **Phân biệt icon theo trạng thái hoạt động:** icon đầy đủ = còn hoạt động, icon mờ (khung đứt) = ngừng hoạt động, icon trung tính (xám) = **chưa rõ trạng thái** (mặc định cho nguồn Wikidata/OSM vốn không có field này).
  - **Tooltip** khi hover: tên, địa phận, tọa độ, nguồn dữ liệu, ngày thành lập (nếu có), tông phái (nếu có).
  - **Bộ lọc:** vùng (Bắc / Trung / Nam), nguồn (`Wikidata / OpenStreetMap / GeoNames-đối chiếu / User`), trạng thái (Hoạt động / Ngừng hoạt động / Chưa rõ / Mới thành lập).

- **Trang Tìm chùa:** `/daoanh/temples/search`
  - Tìm theo tên chùa, tên địa phận, tên thành phố/huyện.
  - Kết quả: danh sách chùa kèm khoảng cách từ vị trí hiện tại (nếu thiết bị cho phép) — **không lưu GPS người dùng trên server** (Zero-RAM + riêng tư).

---
## Dữ liệu

| Vai trò | Nguồn | License / Ghi chú |
|---|---|---|
| 🟢 **Seed chính — Tầng 0** | **Wikidata** (`P625` tọa độ, `P17=Q881` Việt Nam) | CC0, `usage_level=GREEN` |
| 🟢 **Seed chính — Tầng 1** | **OpenStreetMap** (Overpass `religion=buddhist`, bbox VN) | ODbL — tính centroid cho way/relation |
| 🟡 **Đối chiếu hành chính** | **GeoNames** (tâm xã/huyện) — KHÔNG dùng làm GPS chùa | CC-BY, 10.000 credit/ngày (registered) — chỉ gắn `admin_centroid` |
| 🟡 **Đối chiếu (hiếm)** | **DILA** — chỉ khi chùa VN có `dila_id` xác thực (rất hiếm) | Không dùng GPS DILA; gắn `REFERENCE_ONLY` |
| 🟠 **Tầng 2/3 (đợt sau)** | **CSDL chùa Việt** (danh bạ Niên Giám Phật giáo, disantongiao.vn) → geocode bằng **Nominatim** | Dữ liệu thô vào STAGING, review tay |
| ⚪ **User** | Tự cung cấp (tên, tọa độ, hình ảnh, địa phận) | Luôn qua hàng đợi review; đăng ký `dataset_sources` |

**Quy tắc chung:**
- Mỗi nguồn phải đăng ký vào `dataset_sources` (`origin_url`, `license`, `usage_level`).
- **Wikidata** được thăng cấp lên nguồn seed (so với M7 gốc chỉ là tham chiếu thứ ba) vì chùa VN có `P625` đầy đủ và license CC0 phù hợp.
- **GeoNames** không chứa chùa (chỉ địa lý/hành chính) → chỉ đối chiếu, không phải nguồn GPS chùa.
- **Không dùng `YEAR_START` hành chính** để suy ra năm thành lập chùa (kế thừa cảnh báo BGIS từ M7 gốc).

---

## Schema — `places_vn` (RAW, mirror chuẩn DILA)

ID namespace: **`VN` + 10 chữ số** (zero-padded). KHÔNG trùng format `PL` + 12 số của DILA.

| Cột (giữ tên DILA) | Kiểu | Diễn giải cho chùa VN |
|---|---|---|
| `id` | TEXT PK | `VN` + 10 digits |
| `name_vi` | TEXT | Tên chính (VD "Chùa Trấn Quốc") — đảo vai trò so với DILA (DILA lấy `name_zh` làm chính) |
| `name_zh` | TEXT | Pháp danh Hán nếu có (VD "鎮國寺") |
| `district` | TEXT | Hành chính VN: `Việt Nam-Tỉnh/TP-Quận/Huyện-Xã/Phường` (mirror format DILA) |
| `note_category` | TEXT | Loại: `chùa / tổ đình / tự / thiền viện / tịnh xá / tịnh thất / niệm Phật đường / tu viện / am / tháp` |
| `listbibl` | TEXT | Nguồn: danh bạ, Wikipedia, sắc phong, bia ký... |
| `geo_lat` | REAL | **GPS thực đo trên lãnh thổ VN** — validate bbox (xem Acceptance) |
| `geo_long` | REAL | Kinh độ — validate bbox |
| `name_en` | TEXT | Tên tiếng Anh |
| `name_other` | TEXT | Tên khác (giữ nguyên như DILA) |
| `sect` | TEXT | Tông phái: Lâm Tế / Tào Động / Trúc Lâm / Khất Sĩ / Tịnh Độ / Mật / Hoa / Khmer... |
| `founding_year` | TEXT | Năm thành lập (chỉ khi có bia ký/sử liệu — KHÔNG lấy từ hành chính) |
| `heritage_status` | TEXT | Di tích quốc gia / Di tích tỉnh / Di sản UNESCO... |
| `status` | TEXT | `active` / `inactive` / `unknown` (dùng cho icon bản đồ) |
| `source` | TEXT | `wikidata` / `osm` / `geonames` / `dila` / `user` |
| `accuracy` | TEXT | `dila_exact` (Wikidata) / `osm_centroid` (way/relation) / `no_gps` / `admin_centroid` |
| `raw_source` | TEXT | JSON/text nguồn gốc (thay `raw_xml` vì nguồn VN không phải TEI) |

**Luồng 3-Layer:**
```
RAW: places_vn (bất biến, chỉ ETL import)
  → STAGING: places_vn_pending (hàng đợi review — adapt geo_review.html)
  → FINAL: merge vào places (+ source='VN') + places_search_fts + entity(PLACE, dila_id=NULL)
```
**KHÔNG** ghi đè `places_dila` / `places` hiện có.

---

## Logic Khớp và Đối Chiếu

- **Chuẩn hóa tên:** NFKC, bỏ tiền tố `chùa/tự/thiền viện/...`, key không dấu tiếng Việt (tái dùng `normalize_text()` của `app.py`). Dùng cả Hán và phiên âm Việt.
- **Điểm khớp (đề xuất, chưa hiệu chỉnh):**
  ```
  0,5 tên + 0,3 đơn vị hành chính + 0,2 loại/chủng loại
  (+0,2 nếu trùng Hán — CẮT TRẦN tại 1,0)
  ```
- **Auto-link** (chỉ khi đủ): tên không dấu trùng **EXACT** + cùng `phường/xã`, HOẶC trùng chữ Hán và cách nhau tối đa **1–2 km**.
- **Vào hàng đợi:** 1–25 km, hoặc độ giống tên 0,85–0,95. **Mọi cặp không đạt auto → luôn vào queue** (đóng lỗ hổng), không bao giờ rơi giữa chừng.
- **Reject:** trên 25 km — **không bao giờ** tự liên kết.
- **Va chạm:** nhiều chùa chung một tọa độ → buộc duyệt tay, không bao giờ chọn ngầm.
- **Ngưỡng trên là giả định:** hiệu chỉnh trên mẫu gán nhãn tay (ít nhất 200 cặp) rồi ghi kết quả vào tài liệu.
- **Phân tách 2 khái niệm:**
  - **Thu thập GPS** cho chùa đang tồn tại = **BẬT** ngay (Tầng 0/1) — không cần 200 cặp.
  - **Tự động liên kết lịch sử ↔ hiện đại** (gazetteer TK17–18) = **VÔ HIỆU** đến khi có 200 cặp ground truth minh chứng.

---

## Acceptance criteria

- [ ] Mọi `places_vn.geo_lat/long` nằm trong **bbox VN** (lat 8°–24°N, lon 102°–110°E); ngoài bbox → rớt vào `places_vn_pending`.
- [ ] ID dùng namespace **`VN`+10 số**, không tồn tại row nào trùng format `PL`+12 số.
- [ ] Mỗi nguồn Dữ liệu đã đăng ký trong `dataset_sources` (`origin_url`, `license`, `usage_level`).
- [ ] Mỗi liên kết trong `geo_cross_ref` có nguồn, phiên bản, tọa độ, độ tin cậy.
- [ ] Hàng đợi duyệt cho phép chấp nhận / từ chối / để sau; **mỗi hành động có audit log**.
- [ ] GPS user + dữ liệu Tầng 2/3 **luôn** vào hàng đợi review, không bao giờ vào thẳng FINAL.
- [ ] Bản đồ phân biệt icon 3 trạng thái (`active/inactive/unknown`), không vỡ dark mode.
- [ ] Thu thập GPS Tầng 0/1 chạy được — thống kê precision/coverage, không có link lịch sử↔hiện đại tự động vượt 25 km.
- [ ] Tự động liên kết lịch sử↔hiện đại **vô hiệu** đến khi có ground truth 200 cặp minh chứng.
- [ ] Cuộc gọi nguồn tôn trọng giới hạn tốc độ và dừng khi cần.
- [ ] Attribution Wikidata / OpenStreetMap / GeoNames hiện trong chi tiết chùa (badge hoặc text).

---

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất.

**Key functions — ETL (Tầng 0/1):**
1. `importWikidataVN()` — SPARQL chùa VN kèm `P625`, `P131`, label vi/en/zh → ghi `places_vn`
2. `fetchOSMVietnam(bbox)` — Overpass `religion=buddhist`, tính centroid, dedupe với Wikidata
3. `validateVNBBox(lat, lon)` — kiểm tra tọa độ trong lãnh thổ VN
4. `mergeVNPlaces()` — gộp T0+T1, gắn `accuracy`, đẩy vào STAGING/FINAL
5. `registerDatasetSource(...)` — đăng ký nguồn vào `dataset_sources`

**Key functions — UI:**
6. `matchVietnameseTemples(sites)` — khớp chùa tại Việt Nam
7. `getMapStatusVietnam()` — trạng thái bản đồ chùa VN
8. `filterSitesByRegion(region)` — lọc theo vùng (Bắc / Trung / Nam)
9. `getAccuracyColor(accuracy)` — màu theo độ tin cậy

**File path gốc:** `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-vietnam-consolidated.md`  
**Dependencies:** Module M0 (base foundation), Wikidata + Overpass (Tầng 0/1), GeoNames (đối chiếu), CSDL chùa Việt (Tầng 2), Nominatim (Tầng 3), bảng `places_vn`.

---

## Mối liên hệ với các module

- **M7 bản toàn cầu (bản gốc)** — module này là bản mở rộng phạm vi Việt Nam; **KHÔNG sửa** file M7 gốc, chỉ bổ sung song song.
- **M112 (Buddhist Pilgrimage):** lộ trình lữ hành nối các điểm chùa VN — tiêu thụ chung bảng `places_vn`.
- **M35 (Lịch Phật giáo):** ngày thành lập chùa + ngày kỷ niệm, ngày truyền thừa, lịch tế tự.
- **Mở rộng Zero-RAM:** chỉ hiển thị aggregate statistics, không lưu vết vị trí định danh người dùng.
- **M37 (Âm thanh Thiền):** bản tụng niệm tại các chùa VN gắn theo điểm `places_vn`.