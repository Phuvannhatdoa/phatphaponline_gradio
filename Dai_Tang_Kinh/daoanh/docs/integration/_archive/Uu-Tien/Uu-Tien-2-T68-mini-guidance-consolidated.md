# M68 · Buddhist Mini Guidance

**Status:** 📄 Consolidated Documentation  
**Module:** M68  
**Created:** 02-10-2026  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp lời khuyên trì tu cá nhân: dựa trên trạng thái cảm xúc, tiến độ méditation, và mục tiêu cá nhân, AI đề xuất lời khuyên thiền và prática phù hợp cho mỗi giai đoạn.

## UI/UX

- **Trang Lời khuyên:** `/daoanh/guidance/personalized`
  - Input: Trạng thái cảm xúc hiện tại, tiến độ méditation, mục tiêu práctica
   - Output: Lời khuyên thiền (5 phút, 15 phút, 30 phút), bài tập prática, đồ breathing
   - Xem tiếp theo: Lời khuyên cho session mai

- **Trang Lịch sử khuyên:** `/daoanh/guidance/history`
  - Lịch sử: Các lời khuyên đã đề xuất, practitioner đã thực hiện
   - Phản hồi: Đánh giá lời khuyên (1-5 sao), ghi nhận kết quả

- **Trang Cài đặt:** `/daoanh/guidance/settings`
  - Chọn loại khuyên: Theo cảm xúc, Theo tiến độ, Theo mục tiêu
   - Thiết lập mục tiêu cá nhân: Mục tiêu prática theo định nghĩa riêng
   - Thông báo: Kích hoạt nhắc nhở khi đến giờ práctica

## Dữ liệu

- **Lời khuyên:** 100+ bài lý khuyên thiền và pratica đã được curate
- **Giai đoạn:** Sơ cấp (Beginner), Nâng cao (Intermediate), Chuyên sâu (Advanced)
- **Thời gian thực:** Cập nhật mỗi khi practitioner đăng nhập hoặc session kết thúc
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Cung cấp lời khuyên đúng 75% phù hợp với trạng thái thực tế
- [ ] Tăng tỷ lệ pratica thường xuyên 20% qua khuyến nghị AI
- [ ] Tích hợp với Module M53 (Lộ trình học tập cá nhân) và M63 (Phân tích cảm xúc)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu cá nhân với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPersonalizedGuidance(userId)` - Lấy lời khuyên cá nhân
2. `updateGuidanceFeedback(userId, feedback)` - Cập nhật phản hồi khuyên
3. `getGuidanceHistory(userId, period)` - Lấy lịch sử khuyên
4. `getSettings()` - Lấy cài đặt khuyên

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T68-mini-guidance-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI model cho lời khuyên, DB theo dõng feedback