# M23 · Buddhist Personalized Recommendations

**Status:** 📄 Consolidated Documentation  
**Module:** M23  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống khuyến nghị cá nhân cho practice Phật tử: đề xuất meditation, Kinh, retreat phù hợp với sở thích và tiến độ của từng người.

## UI/UX

- **Trang Khuyến nghị practice:** `/daoanh/recommendations/practice`
  - Input: Sở thích (Meditation, Kinh reading, Retreat), Mức độ (Beginner, Intermediate, Advanced)
   - Khuyến nghị: Practice đề xuất kèm lý do

- **Trang Khuyến nghị Kinh:** `/daoanh/recommendations/kinh`
  - Khuyên nghị đoạn Kinh: Theo lịch sử đọc, sở thích, mức độ
   - Xem trước: Preview đoạn Kinh trước khi đọc

- **Trang Khuyến nghị retreat:** `/daoanh/recommendations/retreat`
  - Khuyến nghị retreat: Theo mức độ, vị trí, thời lượng
   - Đăng ký: Đăng ký retreat trực tiếp

- **Trang Cài đặt:** `/daoanh/recommendations/settings`
  - Chọn loại khuyến nghị: Practice, Kinh, Retreat
   - Thiết lập sở thích: Đánh dấu sở thích/thích không
   - Thông báo: Kích hoạt nhắc nhở khi có khuyến nghị mới

## Dữ liệu

- **Hồ sơ sở thích:** 10,000+ hồ sơ sở thích người dùng
- **Khuyến nghị:** 500+ khuyến nghị Practice/Kinh/Retreat
- **Mức độ:** 3 mức độ (Beginner, Intermediate, Advanced)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Khuyến nghị practice đúng 80% phù hợp với sở thích user
- [ ] Khuyến nghị Kinh đúng 85% phù hợp với lịch sử đọc
- [ ] Khuyến nghị retreat đúng 75% phù hợp vớiPreference
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ hồ sơ sở thích với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPracticeRecommendations(preferences)` - Khuyến nghị practice
2. `getKinhRecommendations(history)` - Khuyên nghị đoạn Kinh
3. `getRetreatRecommendations(preferences)` - Khuyến nghị retreat
4. `updatePreferences(preferences)` - Cập nhật sở thích user

**File path:** `docs/Mimo-Flash/M23-personalized-recommendations-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), user preference DB