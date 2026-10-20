# M93 · Buddhist Aura Reader

**Status:** 📄 Consolidated Documentation  
**Module:** M93  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp đọc aura Phật tử: sử dụng AI và cảm biến aura để đọc và phân tích aura cá nhân, cung cấp màu aura, ý nghĩa và đề xuất các phương pháp cân bằng.

## UI/UX

- **Trang Đọc aura:** `/daoanh/aura/read`
  - Input: Tín hiệu aura (tù chọn qua cảm biến), hoặc chọn thủ công (màu aura phổ biến)
   - Kết quả: Màu aura, ý nghĩa aura, độ mạnh mẽ aura, các tượng quan điểm
   - Phản hồi: Đồ biểu đồ aura qua thời gian

- **Trang Phân tích aura:** `/daoanh/aura/analyze`
  - Phân tích chi tiết: Xu hướng aura qua thời gian, phát hiện thay đổi aura
   - So sánh: So sánh aura hiện tại với aura trước đó

- **Trang Cài đặt:** `/daoanh/aura/settings`
  - Chọn phương pháp đọc: Tự động (qua cảm biến), Thủ công (chọn màu)
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi aura thay đổi đáng kể
   - Thông báo: Kích hoạt nhắc nhở khi aura cần chú ý

## Dữ liệu

- **Màu aura:** 10+ màu aura phổ biến (Trắng, Vàng, Xanh lá, Xanh dương, Hồng, và các màu khác)
- **Thời gian đọc:** < 5s cho mỗi lần đọc aura
- **Thiết bị hỗ trợ:** Cảm biến aura (tù chọn), hoặc đọc thủ công
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Đọc aura đúng 75% qua AI và cảm biến
- [ ] Phân tích đúng 80% xu hướng aura qua thời gian
- [ ] Tích hợp với Module M62 (Biofeedback Integration) và M63 (Emotion Analysis)
- [ ] Tương thích với cảm biến aura phổ biến
- [ ] Bảo mật dữ liệu: Không gửi tín hiệu aura về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `readAura()` - Đọc aura cá nhân
2. `getAuraAnalysis()` - Phân tích aura qua thời gian
3. `getSettings()` - Lấy cài đặt đọc aura
4. `getHistory()` - Lấy lịch sử đọc aura

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T93-aura-reader-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI đọc aura, cảm biến aura (tù chọn)