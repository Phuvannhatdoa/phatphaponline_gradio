# M7 · Buddhist GIS Maps

**Status:** 📄 Consolidated Documentation  
**Module:** M7  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp nền tảng bản đồ Phật giáo và hệ thống GIS (Geographic Information Systems): cho phép tra cứu, đối chiếu và xác minh tọa độ các chùa, tự viện và địa danh Phật giáo trên toàn cầu với độ tin cậy cao và nguồn dữ liệu đa tầng.

## UI/UX

- **Trang Review địa lý:** `/daoanh/admin/geo_review.html`
  - Hàng đợi duyệt: Mỗi dòng hiện hai ứng viên cạnh nhau (tên Hán, tên Việt, nguồn, tọa độ, độ chính xác).
  - Giữa hai bên là điểm khớp và khoảng cách. Các nút: Chấp nhận (Accept), Từ chối (Reject), Để sau (Later).
  - Mini-map cho mỗi ứng viên: Vẽ hai điểm và đường nối, đổi màu theo độ chính xác (xanh: cao, vàng: trung bình, đỏ: thấp).
  - Công cụ audit: Hiển thị thông tin chi tiết cho từng ứng viên khi hover.

- **Trang Bản đồ chính:** `/daoanh/maps/main`
  - Hiển thị tất cả địa điểm DILA kèm biểu tượng chùa.
  - Phân biệt chấm: Điểm nét liền (líền) = xác thực DILA chính xác, Điểm nét đứt (dashed) = tâm hành chính hoặc đối chiếu.
  - Tooltip khi hover: Hiển thị tên, nguồn, độ chính xác, phiên bản dữ liệu.
  - Bộ lọc: Chọn nguồn (DILA/GeoNames/WHG/BGIS), chọn độ chính xác (tất cả, chỉ DILA, chỉ BGIS).

## Dữ liệu

- **DILA place:** Khoảng 59.375 nơi, 58.500 có tọa độ (CC BY-SA 3.0) - là nguồn chính.
- **World Historical Gazetteer (WHG):** Đối chiếu qua `/reconcile`, trả định dạng LPF 1.1.
  - Giới hạn 50 truy vấn mỗi lô, 600 mỗi phút, 5.000 mỗi ngày (cờ `redistributable` và HTTP 451).
  - Chỉ dùng cho đối chiếu, không dùng làm nguồn chính.
- **GeoNames:** Tâm xã, huyện, tọa độ hiện đại. Ghi nguồn có link (CC BY).
  - 10.000 credit mỗi ngày miễn phí cho registered users.
  - Chỉ dùng bổ sung và đối chiếu.
- **Wikidata P625:** Tọa độ tham chiếu (chưa xác minh trang CC0).
  - Chỉ dùng là tham chiếu thứ ba, không dùng cho logic khớp.
- **BGIS (Bộ GIS):** Chỉ gợi ý tên và đơn vị hành chính.
  - 18.938 địa điểm, 83,5% tọa độ trùng nhau với DILA (hạng REFERENCE_ONLY).
  - YEAR_START=2006 không phải năm lập chùa - KHÔNG dùng để suy ra năm construir.
  - Chỉ dùng là nguồn tham khảo cho hành chính vùng.

## Logic Khớp và Đối Chiếu

- Chuẩn hóa tên: NFKC, bỏ hậu tố 寺, 院, 庵, chùa, tự. Có khóa phụ bỏ dấu tiếng Việt. Dùng cả Hán Việt và pinyin.
- Điểm khớp (đề xuất, chưa hiệu chỉnh): Công thức trọng số: 0,5 tên + 0,3 không gian + 0,2 loại và thời kỳ.
  - Trùng hoàn toàn chữ Hán được cộng điểm thêm 0,2.
- Điểm khớp tự động chỉ khi:
  - Trùng chữ Hán và cách nhau tối đa 2 km (địa điểm có tên tiếng Việt/Hán), hoặc
  - Tối đa 10 km khi một bên là tâm hành chính (tỉnh/thành).
- Vào hàng đợi khi: 2 đến 25 km hoặc độ giống tên 0,85 đến 0,95.
  - Trên 25 km **không bao giờ** tự liên kết.
- Va chạm: Nhiều chùa chung một tọa độ thì buộc duyệt tay, **không bao giờ chọn ngầm**.
- Ngưỡng trên là giả định: Phải hiệu chỉnh trên mẫu đã gán nhãn tay (ít nhất 200 cặp) rồi ghi kết quả vào tài liệu.
- **Không dùng BGIS** để suy ra năm lập, **không nâng độ chính xác** của tâm huyện thành điểm.
- Bản Việt Nam: Chưa tìm thấy gazetteer có tọa độ cho thế kỷ 17 đến 18.
  - Địa danh Việt cần duyệt tay hoặc nguồn do user cung cấp.
  - Tự động linking cho Việt Nam được vô hiệu hóa đến khi có dữ liệu ground truth.

## Acceptance criteria

- [ ] Chạy khớp thử trên mẫu có nhãn: Báo độ chính xác và độ phủ, **không có liên kết nào tự động vượt ngưỡng 25 km**.
- [ ] Mỗi liên kết trong `geo_cross_ref` có nguồn, phiên bản, độ chính xác, độ tin cậy.
- [ ] 33 liên kết BGIS từ T31 vẫn nguyên và được gắn `admin_centroid`.
- [ ] Hàng đợi duyệt cho phép chấp nhận, từ chối, để sau; **mỗi hành động có dòng audit (audit log)**.
- [ ] Bản đồ **phân biệt chấm nét liền và nét đứt**, không làm hỏng chế độ tối (dark mode).
- [ ] Cuộc gọi WHG tôn trọng giới hạn tốc độ và dừng khi nhận HTTP 451 (quyết định renew).
- [ ] Attribution DILA, GeoNames, WHG hiện trong chi tiết địa danh (bằng hình thức badge hoặc text).
- [ ] Tự động linking **vô hiệu cho dữ liệu Việt Nam** đến khi có ground truth 200 cặp minh chứng.

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `matchGeographicSites(sites)` - Khớp địa điểm bản đồ Phật giáo
2. `getMapStatus()` - Lấy trạng thái bản đồ
3. `filterSitesBySource(source)` - Lọc theo nguồn dữ liệu
4. `getAccuracyColor(accuracy)` - Lấy màu hiển thị theo độ chính xác

**File path:** `docs/Mimo-Flash/M7-gis-buddhist-maps-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), DILA/GeoNames/WHG/BGIS data sources, GIS matching algorithms

---

## Bàn giao triển khai — Danh sách Task (đọc 1 file M7 này + 8 task là hiểu toàn bộ quy trình tích hợp)

Claude Code: chỉ cần mở **file M7 này** (đặc tả) rồi đọc các task dưới theo **thứ tự + chuỗi phụ thuộc**.
Mỗi task đã **self-contained** (bảng "Liên kết các phần khác" có đủ path). Hoàn tất task trước mới qua task kế.

| TT | Task | Phần của tích hợp M7 | File | Phụ thuộc |
|---|---|---|---|---|
| 1 | **T243** | Data · Ingest DILA + chuẩn hóa tên | `tasks/T243-m7-data-normalize-places.md` | — |
| 2 | **T244** | Matching Engine `matchGeographicSites` | `tasks/T244-m7-matching-engine.md` | T243 |
| 3 | **T245** | Reference Linkage `geo_cross_ref` (+33 BGIS, Wikidata P625) | `tasks/T245-m7-reference-linkage-geo-cross-ref.md` | T244 |
| 4 | **T246** | WHG Client (LPF 1.1 + rate-limit + HTTP 451) | `tasks/T246-m7-whg-client.md` | T245 |
| 5 | **T247** | GeoNames Enrichment (admin centroid) | `tasks/T247-m7-geonames-enrichment.md` | T245 |
| 6 | **T248** | Geo Review UI + audit log | `tasks/T248-m7-geo-review-ui-audit.md` | T245,246,247 |
| 7 | **T249** | Maps Main (chấm liền/đứt + filter + dark mode) | `tasks/T249-m7-maps-main.md` | T243,245 |
| 8 | **T250** | Attribution + Gate VN + chạy acceptance M7 | `tasks/T250-m7-attribution-vn-gate-acceptance.md` | T243–T249 |

**Quy tắc:** mọi path tương đối từ thư mục `daoanh/`. Đặc tả chi tiết của từng task nằm trong từng file `Txxx-*.md`.