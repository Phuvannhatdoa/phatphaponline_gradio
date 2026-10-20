# M22 · Buddhist Festivals & Community

**Status:** 📄 Consolidated Documentation  
**Module:** M22  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp thông tin lễ hội Phật giáo và cộng đồng: thông tin các lễ quan trọng, lịch hội, và hoạt động cộng đồng Phật tử.

## UI/UX

- **Trang Lễ hội Phật giáo:** `/daoanh/festivals`
  - Hiển thị lễ quan trọng: Phật Đản, Vu Lan, Thành đạo, Bát Tháng Lập, v.v.
   - Thông tin: Ngày, nơi tổ chức,-description, ảnh lễ

- **Trang Hoạt động cộng đồng:** `/daoanh/community-events`
  - Hiển thị hoạt động: Retreat, Talk, Workshop, Charity
   - Theo dõng: Đăng ký, xem lịch sử

- **Trang Cài đặt:** `/daoanh/festivals/settings`
  - Chọn lễ quan tâm: Chọn lễ quan tâm sẽ hiển thị trên calendar
   - Thiết lập nhắc nhở: Kích hoạt nhắc nhở lễ hội

## Dữ liệu

- **Lễ quan trọng:** 20+ lễ Phật quan trọng được định nghĩa sẵn
- **Hoạt động cộng đồng:** 50+ hoạt động gần đây
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 20+ lễ quan trọng Phật giáo
- [ ] Thông tin lễ đúng 90% so với nguồn gốc
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp được với calendar cá nhân
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin cá nhân

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getFestivals()` - Lấy danh sách lễ quan trọng
2. `getCommunityEvents()` - Lấy danh sách hoạt động cộng đồng
3. `getFestivalDetail(id)` - Lấy chi tiết lễ
4. `getSettings()` - Lấy cài đặt lễ và hội

**File path:** `docs/Mimo-Flash/M22-festivals-community-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), dữ liệu lễ và hội từ DB