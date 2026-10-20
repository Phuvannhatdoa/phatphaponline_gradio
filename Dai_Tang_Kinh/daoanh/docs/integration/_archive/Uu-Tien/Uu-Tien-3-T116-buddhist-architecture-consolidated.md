# M116 · Buddhist Architecture & Temple Design

**Status:** 📄 Consolidated Documentation  
**Module:** M116  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống Thiết kế chùa và kiến trúc Phật tử: hướng dẫn thiết kế chùa, tự viện, và các건물 Phật tử theo giáo pháp truyền thống và tiêu chuẩn hiện đại.

## UI/UX

- **Trang Thư viện Kiến trúc:** `/daoanh/architecture/library`
  - Duyệt qua thể loại: Chùa, Tự viện, Giảng đường, Viện nghiên cứu
  - Lọc theo truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Hiển thị thông tin: Tên thiết kế, tác giả, diện tích, năm xây, vật liệu

- **Trang Chi tiết Kiến trúc:** `/daoanh/architecture/detail/:id`
  - Thông tin: Kích thước, bố cục, hướng nhà, đặc điểm kiến trúc
  - Phân tích không gian: Luồng lưu thông, ánh sáng tự nhiên, không âm
  - Tài liệu xây dựng: Bản vẽ cơ bản, vật liệu recommendations, quy định an toàn

- **Trang Tìm kiếm:** `/daoanh/architecture/search`
  - Tra theo: Kiểu chùa, diện tích, truyền thống, năm xây
  - Hiển thị kết quả: Danh sách kèm thumbnail, thông tin tóm tắt
  - Tìm kiếm liên quan: Chùa/kiến trúc tương tự theo địa lý hoặc truyền thống

- **Trang Cài đặt:** `/daoanh/architecture/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập tiêu chuẩn: An toàn kết cấu, bảo tồnDi sản, bền vững môi trường
  - Tích hợp phê duyện: Phê duyện phiến đồ, giám sát bảo trì

## Dữ liệu

- **100+ dự án kiến trúc:** Kèm thông tin chi tiết kèm truyền thống
- **30+ kiểu chùa:** Kèm đặc điểm kiến trúc kèm truyền thống
- **10+ tiêu chuẩn:** Kèm an toàn kết cấu, bảo tồnDi sản, bền vững môi trường
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Thư viện hiển thị đúng 100+ dự án kiến trúc kèm thông tin truyền thống
- [ ] Tìm kiếm hoạt động đúng 85% từ khóa kiến trúc Phật tử
- [ ] Hiển thị đúng 30+ kiểu chùa kèm đặc điểm kiến trúc kèm truyền thống
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp tiêu chuẩn bảo tồn kèm 95% uptime
- [ ] Bộ lọc truyền thống hiển thị đúng 3 truyền thống kèm đặc điểm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getArchitectureLibrary()` - Lấy thư viện 100+ dự án kiến trúc kèm thông tin
2. `getArchitectureDetails(projectId)` - Lấy chi tiết dự án kèm thông tin kỹ thuật
3. `getTraditionStandards()` - Lấy bộ tiêu chuẩn kèm an toàn, bảo tồn, bền vững
4. `getSettings()` - Lấy cài đặt kiến trúc

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T116-buddhist-architecture-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Architecture database (100+ dự án kèm thông tin), Type classification (30+ kiểu chùa kèm đặc điểm), Standards system (10+ tiêu chuẩn kèm an toàn, bảo tồn, bền vững), Multi-language support (Việt, Anh, Trung)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M7 (GIS Maps): temple locations kèm architectural projects kèm geographic distribution kèm pilgrimage route visualization
- Kết nối dữ liệu với M112 (Buddhist Pilgrimage): sacred sites kèm associated architecture kèm temple buildings kèm pilgrimage accommodations
- Mở rộng từ M109 (Buddhist Chaplaincy): chapel design kèm chaplaincy support kèm ceremonial space kèm ritual room design
- Mở rộng từ M110 (Buddhist Engaged Social Work): community architecture kèm social change kèm public building kèm civic engagement
- Mở rộng zero-RAM principle cho architecture caching, chỉ hiển thị aggregates statistics chứ không user-identifiable building viewing history
- Mối liên hệ với M35 (Buddhist Calendar): festival scheduling kèm temple events kèm holy day celebrations kèm ritual timing

---