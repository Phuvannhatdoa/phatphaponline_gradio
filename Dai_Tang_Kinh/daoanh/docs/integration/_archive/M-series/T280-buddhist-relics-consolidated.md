# T280 · Buddhist Relic Buddhist Maps

> Đổi số ngày 2026-10-10: M3 (trùng số kế hoạch M-series) → T280. Nội dung không đổi.

**Status:** 📄 Consolidated Documentation  
**Module:** M3  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bản đồ và tra cứu đồ vật Phật giáo relic: cho phép practitioner tra cứu, xác minh và học về đồ vật Phật giáo relic (xa bảo vật, tháp pagoda, tượng Phật) trên toàn cầu.

## UI/UX

- **Trang Tra cứu relic:** `/daoanh/relics/search`
  - Input: Tên relic, loại relic (xa bảo vật, tháp, tượng), nguồn gốc
   - Kết quả: Hiển thị trên bản đồ kèm thông historia (lịch sử,ynasty, vị trí hiện tại)

- **Trang Chi tiết relic:** `/daoanh/relics/detail`
  - Hiển thị thông tin: Tên, loại, kích thước, 재료, lịch sử, vị trí hiện tại
   - Hình ảnh: Hiển thị hình ảnh relic (nếu có sẵn)
   - Tương ứng: Thông tin về bảo quản và bảo tồn

- **Trang Danh mục relic:** `/daoanh/relics/catalog`
  - Lọc theo loại: Xa bảo vật, Tháp pagoda, Tượng Phật, Hồ sinh
   - Thống kê: Số lượng relic theo loại, quốc gia, thời đại

## Dữ liệu

- **Số lượng relic:** 1000+ đồ vật Phật giáo relic trên toàn cầu
- **Loại relic:** 10+ loại relic Phật học được phân loại
- **Thông historia:** Mỗi relic có historia (lịch sử,ynasty, lý-do quan trọng)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tra cứu 1000+ relic chính xác
- [ ] Hiển thị história đúng 80% relic có documentation
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp được với cơ sở dữ liệu relic Phật học
- [ ] Bảo mật dữ liệu: Không lưu truy vấn user dài hạn

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `searchRelics(query)` - Tra cứu relic theo tên/loại/nguồn gốc
2. `getRelicDetail(id)` - Lấy thông tin chi tiết relic
3. `getRelicsByType(type)` - Lấy relic theo loại (xa bảo vật, tháp, tượng...)
4. `getRelicsHistory(id)` - Lấy historia relic

**File path:** `docs/Mimo-Flash/M3-buddhist-relics-consolidated.md`  
**Dependencies:** Module relic database (custom backend)