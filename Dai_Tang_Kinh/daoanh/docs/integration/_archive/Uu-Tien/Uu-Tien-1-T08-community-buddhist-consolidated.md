# M8 · Buddhist Community Tracking

**Status:** 📄 Consolidated Documentation  
**Module:** M8  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống tracking cộng đồng Phật tử: theo dõng dana, retreat, Sangha directory và các hoạt động cộng đồng Phật giáo.

## UI/UX

- **Trang Tracking dana:** `/daoanh/community/dana`
  - Hiển thị lịch sử dana: Số lượng, frequence, nguồn dana
   - Biểu đồ thống kê: Theo tháng, theo năm, theo nguồn

- **Trang Directory Sangha:** `/daoanh/community/sangha`
  - Hiển thị danh sách sangha: Tên, địa vị, vị trí, contato
   - Tìm kiếm: Tìm theo tên, vị trí, phái

- **Trang Quản lý retreat:** `/daoanh/community/retreat`
  - Quản lý retreat: Đăng ký, hủy, thay đổi ngày
   - Theo dõng tham gia: Ai đã tham gia, ai đã hủy

## Dữ liệu

- **Lịch sử dana:** 1000+ giao dịch dana ghi nhận
- **Danh sách sangha:** 500+ sangha có thông tin liên hệ
- **Hoạt động retreat:** 50+ retreat đã tổ chức kèm danh sách tham gia
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tracking dana chính xác 95% cho giao dịch được ghi nhận
- [ ] Directory sangha hiển thị đúng 80% sangha có thông tin đầy đủ
- [ ] Quản lý retreat đúng 90% cho các hoạt động đã tổ chức
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin cá nhân với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackDana(transaction)` - Ghi nhận giao dịch dana
2. `getSanghaDetail(id)` - Lấy thông tin chi tiết sangha
3. `getSanghasNearby(lat, lng)` - Lấy sangha근방
4. `manageRetreat(event, action)` - Quản lý retreat (đăng ký/hủy)

**File path:** `docs/Mimo-Flash/M8-community-buddhist-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created)