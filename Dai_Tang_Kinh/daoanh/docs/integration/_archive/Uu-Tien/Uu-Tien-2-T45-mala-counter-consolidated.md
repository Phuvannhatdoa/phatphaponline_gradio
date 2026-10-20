# M45 · Buddhist Mala Counter

**Status:** 📄 Consolidated Documentation  
**Module:** M45  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bộ đếm phấn Phật học: theo dõng số lần phấn, meditation timer, và ghi nhận các kết quả pratique.

## UI/UX

- **Trang Đếm phấn:** `/daoanh/mala/counter`
  - Hiển thị số lần phấn: Số lượng phấn hôm nay, ngày hôm qua, tổng toàn thời gian
   - Chức năng: Đặt lại số đếm, ghi nhận kết quả pratica

- **Trang Cài đặt:** `/daoanh/mala/settings`
  - Thiết lập mục tiêu: Mục tiêu phấn mỗi ngày
   - Thông báo: Kích hoạt nhắc nhở phấn hàng ngày

- **Trang Lịch sử:** `/daoanh/mala/history`
  - Lịch sử phấn: Ghi nhận các session phấn qua các ngày/tháng/năm
   - Thống kê: Số liệu thống kê phấn qua thời gian

## Dữ liệu

- **Số liệu phấn:** 1000+ session phấn đã ghi nhận
- **Mục tiêu:** Mục tiêu phấn hàng ngày cá nhân
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, thiết bị đeo (Apple Watch, Fitbit)
- **Đồng bộ:** Cloud sync cho 100% dữ liệu phấn

## Acceptance criteria

- [ ] Ghi nhận 1000+ session phấn chính xác
- [ ] Đạt mục tiêu phấn hàng ngày đúng 80% cho user tích cực
- [ ] Đồng bộ cloud đúng 100% cho dữ liệu phấn
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop, thiết bị đeo
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu lưu cục bộ trên thiết bị user,cloud sync có mã hóa

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackMalaCount(count)` - Theo dõng số phấn
2. `getMalaStats(userId)` - Lấy thống kê phấn
3. `getMalaHistory(userId, period)` - Lấy lịch sử phấn
4. `getSettings()` - Lấy cài đặt phấn

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T45-mala-counter-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), mala counter DB, thiết bị đeo tích hợp