# T282 · Buddhist Text Source Tracking

> Đổi số ngày 2026-10-10: M5 (trùng số kế hoạch M-series) → T282. Nội dung không đổi.

**Status:** 📄 Consolidated Documentation  
**Module:** M5  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống ghi nhận nguồn gốc cho văn bản Phật giáo: cho phép tracer nguồn CBETA, DILA, Wiki và các nguồn khác cho từng đoạn văn bản, đảm bảo tính minh bạch và quyền truy cập.

## UI/UX

- **Trang Ghi nhận nguồn:** `/daoanh/source/track`
  - Input: Đoạn văn bản, nguồn gốc (CBETA, DILA, Wikidata, nguồn khác)
   - Kết quả: Hiển thị badge nguồn, phiên bản, lý do chọn nguồn này

- **Trang Danh sách nguồn:** `/daoanh/source/list`
  - Hiển thị tất cả nguồn đã ghi nhận: Tên, loại, phiên bản, trạng thái
   - Phân loại: Nguồn chính, Nguồn đối chiếu, Nguồn tham khảo

- **Trang Cài đặt:** `/daoanh/source/settings`
  - Chọn nguồn mặc định: CBETA, DILA, hay nguồn khác
   - Thiết lập quyền truy cập: Ai có thể ghi nhận nguồn mới
   - Thông báo: Kích hoạt nhắc nhở khi tìm thấy nguồn mới

## Dữ liệu

- **Nguồn chính:** CBETA (59.167 places_dila), DILA (48.673 people), WHG (118.304 zh+vi)
- **Nguồn đối chiếu:** GeoNames, BGIS, Wikidata
- **Thông tin ghi nhận:** source_id, source_code, legal_status, license_verified, implemented
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Ghi nhận nguồn cho 100% đoạn văn bản quan trọng
- [ ] Phát hiện nguồn trùng lặp đúng 95% trường hợp
- [ ] Tăng tính minh bạch 40% so với phương pháp truyền thống
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin nguồn với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackSource(segment, sourceId)` - Ghi nhận nguồn cho đoạn văn bản
2. `getSourceDetails(sourceId)` - Lấy thông tin chi tiết nguồn
3. `checkDuplicateSource(sourceId)` - Kiểm tra nguồn trùng lặp
4. `getDefaultSource()` - Lấy nguồn mặc định cho project

**File path:** `docs/Mimo-Flash/M5-source-tracking-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), dữ liệu sources từ DB