# M75 · Buddhist Dream Interpretation

**Status:** 📄 Consolidated Documentation  
**Module:** M75  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp giải mã giấc mộng Phật học: sử dụng triết lý Phật tử và AI để giải mã các giấc mộng, tìm ra ý nghĩa tiềm ẩn và liên hệ với pratica méditation.

## UI/UX

- **Trang Giải mã giấc mộng:** `/daoanh/dreams/interpret`
  - Input: Mô tả giấc mộng, hoặc chọn từ danh sách tượng mộng phổ biến
   - Kết quả: Ý nghĩa giấc mộng, các tượng biểu tượng liên quan, liên hệ với pratica méditation
   - Biểu đồ: Đồ ý nghĩa giấc mộng qua thời gian (nếu có lịch sử)

- **Trang Lịch sử giấc mộng:** `/daoanh/dreams/history`
  - Lịch sử: Các giấc mộng đã giải mã, xu hướng tượng mộng qua thời gian
   - Phản hồi: Đánh giá độ chính xác giải mã (1-5 sao)

- **Trang Cài đặt:** `/daoanh/dreams/settings`
  - Chọn hệ thống tượng mộng: Hệ thống Phật tử, Hệ thống Tây Âu, Kết hợp cả hai
   - Thiết lập ngưỡng: Chọn tượng mộng muốn theo dõng
   - Thông báo: Kích hoạt nhắc nhở khi mộng về tượng quan trọng

## Dữ liệu

- **Hệ thống tượng mộng:** 100+ tượng mộng Phật tử đã được curate
- **Thể loại:** Tý, Sùng, Tà, Phục, và các tượng mộng khác
- **Thời gian giải mã:** < 5s cho mỗi giấc mộng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Giải mã đúng 75% giấc mộng qua hệ thống tượng mộng Phật tử
- [ ] Tăng awareness tiềm ẩn qua giải mã giấc mộng 15%
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp với Module M63 (Phân tích cảm xúc) và M68 (Lời khuyên trì tu)
- [ ] Bảo mật dữ liệu: Không lưu trữ mô tả giấc mộng nhạy cảm lâu dài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `interpretDream(dreamText)` - Giải mã giấc mộng
2. `getDreamHistory(userId)` - Lấy lịch sử giấc mộng
3. `getSettings()` - Lấy cài đặt giải mã giấc mộng
4. `getSymbolDictionary()` - Lấy từ điển tượng mộng

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T75-dream-interpretation-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI model giải mã giấc mộng, từ điển tượng mộng