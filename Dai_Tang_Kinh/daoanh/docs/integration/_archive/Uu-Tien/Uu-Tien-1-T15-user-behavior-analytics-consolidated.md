# M15 · Buddhist User Behavior Analytics

**Status:** 📄 Consolidated Documentation  
**Module:** M15  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp analytics hành vi người dùng Phật tử: theo dõng tương tác, engagement, và demographics để cải thiện trải nghiệm Phật tử trên nền tảng.

## UI/UX

- **Trang Phân tích hành vi:** `/daoanh/analytics/behavior`
  - Hiển thị tương tác: Click, scroll, time on page, phần tử được click nhiều nhất
   - Biểu đồ thời gian thực: Theo dõng hoạt động qua thời gian

- **Trang Phân khúc người dùng:** `/daoanh/analytics/segmentation`
  - Phân khúc: Mới gia nhập, tích cực, thụ động, inactive
   - Thống kê: Số lượng người dùng trong mỗi phân khúc, xu hướng qua thời gian

- **Trang Demographics:** `/daoanh/analytics/demographics`
  - Thông tin dân số: Tuổi tác, địa lý, thiết bị
   - Biểu đồ: Phân bố theo vùng, thiết bị phổ biến

- **Trang Cài đặt:** `/daoanh/analytics/settings`
  - Chọn metrics: Chọn metrics muốn theo dõng
   - Thiết lập báo cáo: Tạo báo cáo tùy chỉnh, lịch xuất bản
   - Thông báo: Kích hoạt email báo cáo định kỳ

## Dữ liệu

- **Metrics:** 20+ metrics hành vi theo dõng
- **Phân khúc:** 4 phân khúc người dùng (Mới gia nhập, Tích cực, Thụ động, Inactive)
- **Dân số:** 5000+ người dùng theo dõng kèm demographics
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Theo dõng 20+ metrics hành vi chính xác 90% so với survey trực tiếp
- [ ] Phân khúc người dùng đúng 80% so với behavior thực tế
- [ ] Biểu đồ demographics phản ánh đúng 85% cơ cấu dân số
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không phân phối dữ liệu行为 học về bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackBehavior(event)` - Theo dõng sự kiện hành vi
2. `getUserSegment(userId)` - Lấy phân khúc người dùng
3. `getDemographics()` - Lấy demographics tổng quan
4. `getAnalyticsReport(period)` - Lấy báo cáo analytics cho khoảng thời gian

**File path:** `docs/Mimo-Flash/M15-user-behavior-analytics-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), analytics DB