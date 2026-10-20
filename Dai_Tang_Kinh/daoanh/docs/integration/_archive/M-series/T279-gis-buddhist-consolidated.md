# T279 · Buddhist GIS Maps for Temple Location

> Đổi số ngày 2026-10-10: M2 (trùng số kế hoạch M-series) → T279. Nội dung không đổi.

**Status:** 📄 Consolidated Documentation  
**Module:** M2  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bản đồ GIS cho vị trí tịnhiếu Phật giáo: cho phép practitioner tra cứu, đánh giá và đặt đường đến các chùa, tự viện Phật trên bản đồ Việt Nam và thế giới kèm thông tin cơ bản.

## UI/UX

- **Trang Tìm kiếm địa điểm:** `/daoanh/maps/search`
  - Input: Tên chùa, thành phố, tỉnh/thành
   - Kết quả: Hiển thị trên bản đồ kèm thông tin cơ bản (liền thủy, đáp ứng phim)

- **Trang Chi tiết địa điểm:** `/daoanh/maps/detail`
  - Hiển thị thông tin: Tên, địa chỉ, số điện thoại, giờ hành chính
   - Tính đường: Tính đường từ vị trí user đến temple

- **Trang Cài đặt bản đồ:** `/daoanh/maps/settings`
  - Chọn loại bản đồ: Ôn bản, vệ sinh,卫星
   - Thiết lập khoảng cách: Tính đường đi/bike/go

## Dữ liệu

- **Số lượng temple:** 500+ templo Phật giáo trên bản đồ Việt Nam
- **Thông tin cơ bản:** Tên, địa chỉ, tọa độ vĩ/kinh, loại (templo, nhà thờ, trung tâm)
- **Tích hợp:** Kết nối với Module M7 (GIS maps foundation)
- **Thiết bị hỗ trợ:** Điện thoại (iOS/Android), tablet, desktop

## Acceptance criteria

- [ ] Tìm kiếm 500+ temple chính xác
- [ ] Tính đường đúng 90% so với Google Maps
- [ ] Tương thích với iOS Maps, Android Google Maps, Desktop browsers
- [ ] Tích hợp được với Module M7 (GIS maps foundation)
- [ ] Bảo mật dữ liệu: Không lưu vị trí user dài hạn

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `searchTemples(query)` - Tìm kiếm temple theo tên/vị trí
2. `getTempleDetail(id)` - Lấy thông tin chi tiết temple
3. `calculateRoute(start, end)` - Tính đường từ điểm xuất phát đến temple
4. `getTemplesNearby(lat, lng)` - Lấy temple 근방 temple

**File path:** `docs/Mimo-Flash/M2-gis-buddhist-consolidated.md`  
**Dependencies:** Module M7 (GIS maps foundation)