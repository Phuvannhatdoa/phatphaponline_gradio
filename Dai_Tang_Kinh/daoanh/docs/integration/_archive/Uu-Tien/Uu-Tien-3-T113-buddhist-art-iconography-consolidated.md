# M113 · Buddhist Art & Iconography

**Status:** 📄 Consolidated Documentation  
**Module:** M113  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống Nghệ thuật Phật giáo và Thể symbol: quản lý các tượng Phật, tranh đáy壁, và các biểu tượng truyền thống, cung cấp hướng dẫn cho practitioner hiểu biết và التقدrespect nghệ thuật Phật tử.

## UI/UX

- **Trang Thư viện Nghệ thuật:** `/daoanh/art/library`
  - Duyệt qua thể loại: Tranh vẽ, Sáng tạo, Xúc tác
  - Lọc theo truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Hiển thị thông tin: Tên tác giả, ngày tạo, 재료, kích thước

- **Trang Chi tiết Tượng/Tranh:** `/daoanh/art/detail/:id`
  - Thông tượng: Kích thước, vật liệu, truyền thống, vị trí hiện tại
  - Biểu tượng: Các symbole chính kèm nghĩa Phật học
  - Lịch sử:Xuất phát, di chuyền qua thế kỷ

- **Trang Tìm kiếm Thể symbole:** `/daoanh/art/symbol-search`
  - Tra symbole: Lót Bodhisattva, Phật, Thiên vương, Dharma symbols
  - Hiển thị nghĩa: Mô tả Phật học kèm tham chiếu Kinh
  - Tìm kiếm liên quan: Các tượng/tranh chứa symbole tương tự

- **Trang Cài đặt:** `/daoanh/art/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập ngôn ngữ: Tiêu đề tiếng Việt, tiếng Anh, tiếng Trung
  - Tích hợp bảo tồn: Cảnh báo trạng thái hư hỏng, lịch bảo trì

## Dữ liệu

- **100+ tượng Phật/Tranh:** Kèm thông tin chi tiết kèm truyền thống
- **50+ Biểu tượng Phật học:** Kèm nghĩa giải kèm tham chiếu Kinh
- **Thể truyền thống:** 3 truyền chính kèm đặc điểm riêng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Thư viện hiển thị đúng 100+ tượng Phật/Tranh kèm thông tin truyền thống
- [ ] Tìm kiếm symbole hoạt động đúng 90% từ khóa nghệ thuật Phật giáo
- [ ] Biểu tượng hiển thị đúng 50+ symbole kèm nghĩa giải Phật học
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp hệ thống bảo tồn kèm 95% uptime
- [ ] Lọc truyền thống hiển thị đúng 3 truyền thống kèm đặc điểm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getArtLibrary()` - Lấy thư viện nghệ thuật Phật tử kèm 100+ tác phẩm
2. `getSymbolDetails(symbol)` - Lấy chi tiết symbole kèm nghĩa giải Phật học
3. `getTraditionFilter()` - Lấy bộ lọc truyền thống kèm đặc điểm
4. `getSettings()` - Lấy cài đặt nghệ thuật

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T113-buddhist-art-iconography-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Art database (100+ tượng/tran kèm thông tin), Symbol dictionary (50+ símbolo kèm nghĩa), Tradition classification system (3传统 kèm đặc điểm), Multi-language support (Việt, Anh, Trung)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M7 (GIS Maps): temple locations kèm artwork locations kèm geographic distribution kèm pilgrimage route art
- Kết nối dữ liệu với M112 (Buddhist Pilgrimage): sacred sites kèm associated artwork kèm ritual objects kèm pilgrimage artifacts
- Mở rộng từ M109 (Buddhist Chaplaincy): ritual objects kèm chaplaincy support kèm ceremonial art kèm ritual items
- Mở rộng từ M110 (Buddhist Engaged Social Work): community art projects kèm social change kèm public art installation kèm civic engagement
- Mở rộng zero-RAM principle cho artwork caching, chỉ hiển thị aggregates statistics chứ không user-identifiable artwork viewing history
- Mối liên hệ với M37 (Buddhist Meditation Music): ritual music kèm ceremonial art kèm temple decoration kèm seasonal displays

---