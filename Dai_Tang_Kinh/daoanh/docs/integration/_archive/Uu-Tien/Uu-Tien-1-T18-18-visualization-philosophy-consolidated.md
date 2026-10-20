# M18 · Buddhist Visualization Philosophy

**Status:** 📄 Consolidated Documentation  
**Module:** M18  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp triết lý trực quan hóa cho Phật học: thiết kế các biểu đồ, đồ thị, và các trực quan hóa triết lý Phật giáo để truyền đạt các khái niệm sâu đến practitioner.

## UI/UX

- **Trang Triết lý trực quan:** `/daoanh/visualization/philosophy`
  - Hiển thị các khái niệm triết lý: Tứ Đại, Nguyên nhân quả, 12 phátheiten, v.v.
   - Trực quan hóa: Biểu đồ, đồ thị, minh họa hình học

- **Trang Các loại trực quan hóa:** `/daoanh/visualization/types`
  - Hiển thị các loại: Trình tròn (pie chart), đường (line chart), mặt trống (tree map), v.v.
   - Tùy chọn: Chọn loại triết lý, tùy chỉnh màu sắc, kích thước

- **Trang Cài đặt trực quan hóa:** `/daoanh/visualization/settings`
  - Chọn phong cách: Trình độ học trò, trình độ tiến sĩ, trình độ chuyên gia
   - Tùy chỉnh: Màu sắc, kích thước, dữ liệu hiển thị
   - Thông báo: Lưu cài đặt mặc định

## Dữ liệu

- **Khái niệm triết lý:** 20+ khái niệm Phật học cơ bản có trực quan hóa
- **Loại trực quan hóa:** 10+ loại biểu đồ và đồ thị
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Thời gian tạo:** Tạo trực quan hóa trong 10 phút cho mỗi khái niệm

## Acceptance criteria

- [ ] Hiển thị đúng 20+ khái niệm triết lý có trực quan hóa
- [ ] Tạo trực quan hóa đúng 90% theo thiết kế
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tạo biểu đồ trong 10 phút cho mỗi khái niệm
- [ ] Bảo mật dữ liệu: Không lưu trữ dữ liệu triết lý nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `visualizePhilosophy(concept)` - Trực quan hóa khái niệm triết lý
2. `getVisualizationTypes()` - Lấy danh sách loại trực quan hóa
3. `customizeVisualization(concept, options)` - Tùy chỉnh trực quan hóa
4. `getVisualizationSettings()` - Lấy cài đặt trực quan hóa

**File path:** `docs/Mimo-Flash/M18-visualization-philosophy-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), thư viện trực quan hóa