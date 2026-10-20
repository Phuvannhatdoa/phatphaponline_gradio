# M62 · Buddhist Biofeedback Integration

**Status:** 📄 Consolidated Documentation  
**Module:** M62  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp tích hợp biofeedback cho pratica méditation: kết hợp tín hiệu não (EEG), nhịp tim, và dữ liệu 신체 cơ bắp với ứng dụng méditation để theo dõng và cải thiện chất lượng session méditation.

## UI/UX

- **Trang Biofeedback:** `/daoanh/feedback/bio`
  - Hiển thị các chỉ số: Mức độ attention (1-10), độ hình thái não (theta/alpha/beta), nhịp tim (BPM)
   - Phản hồi tức thời: Đồ graphs cập nhật mỗi 1s, cảnh báo khi chỉ số vượt quá ngưỡng
   - Lịch sử: Ghi nhận các session qua các ngày

- **Trang Cài đặt biofeedback:** `/daoanh/feedback/settings`
  - Chọn thiết bị: Emotiv EPOC+, Muse S, Fitbit, Apple Watch, hoặc standalone sensor
   - Thiết lập ngưỡng: Ngưỡng attention, ngưỡng nhịp tim, ngưỡng độ hình thái não
   - Chọn chế độ: Theo cảm xúc, Theo focus, Theo nhịp tim

- **Trang Phối hợp:** `/daoanh/feedback/coordination`
  - Khớp biofeedback với loại méditation: Thiền thọ, Vipassana, Zen, Pure Land
   - Tự động điều chỉnh: Điều chỉnh ngưỡng khi chuyển đổi loại méditation
   - Đảm chỉ: Tắt biofeedback khi méditation sâu (để không gây distract)

## Dữ liệu

- **Tín hiệu:** EEG (Module M33), nhịp tim, dữ liệu 신체 cơ bắp
- **Chỉ số:** 10+ chỉ số biofeedback chính
- **Thiết bị hỗ trợ:** Emotiv EPOC+, Muse S, Fitbit, Apple Watch, các cảm biến standalone
- **Thời gian thực:** Cập nhật mỗi 1s, latency < 500ms

## Acceptance criteria

- [ ] Theo dõng đúng 80% các chỉ số biofeedback chính
- [ ] Tăng chất lượng méditation 15% qua biofeedback khuyến khích
- [ ] Tương thích với Emotiv EPOC+, Muse S, Fitbit, Apple Watch
- [ ] Cập nhật dữ liệu mỗi 1s chính xác
- [ ] Bảo mật dữ liệu: Không gửi tín hiệu não về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getBiofeedbackData()` - Lấy dữ liệu biofeedback
2. `getOptimizationPlan()` - Lấy kế hoạch tối ưu
3. `getFeedbackInsights()` - Lấy kiến thức biofeedback
4. `getSettings()` - Lấy cài đặt biofeedback

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T62-biofeedback-integration-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), advanced sensors, AI model cho biofeedback