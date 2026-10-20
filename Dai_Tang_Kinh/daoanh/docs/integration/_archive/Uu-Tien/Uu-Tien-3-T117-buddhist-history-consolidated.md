# M117 · Buddhist History & Lineage

**Status:** 📄 Consolidated Documentation  
**Module:** M117  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống Lịch sử Phật giáo và Lập tiếp承: quản lý các sự kiện lịch sử, các nhà truyền承, và dây truyền Phật tử qua các đại phái và thời đại.

## UI/UX

- **Trang Lịch sử Phật giáo:** `/daoanh/history/timeline`
  - Hiển thị timeline: 2500+ năm lịch sử kèm sự kiện quan trọng
  - Bộ lọc theo thời đại: Biên thành Prasidantic, Thời trung đại, Thời đại mới, Thời đại contemporain
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna, Zen

- **Trang Nhà truyền承:** `/daoanh/lineage/master`
  - Duyệt qua nhà truyền承: Tên, phái, vị trị, học trò nổi tiếng
  - Hiển thị dây truyền: Sơ đồ dòng dõi, thời gian sống, học trò chính
  - Tham chiếu: Kết nối với các nguồn história bên ngoài

- **Trang Sự kiện quan trọng:** `/daoanh/history/events`
  - Tra事件: Tên sự kiện, năm, importantes, tác động lớn đến Phật tử
  - Phân tích tác động: Đầu ra cho các phái và thời đại
  - Tìm kiếm: Tra cứu theo từ khóa, thời đại, phái

- **Trang Cài đặt:** `/daoanh/history/settings`
  - Chọn phạm vi: Toàn bộ lịch sử hoặc chỉ một truyền thống
  - Thiết lập hiển thị: Mức độ chi tiết, hiển thị lối dây truyền
  - Đồng bộ nguồn: Kết nối với CBETA, Wikipedia, các nguồn historia chính thức

## Dữ liệu

- **2500+ năm lịch sử:** Kèm sự kiện quan trọng kèm ngày/tháng/năm
- **100+ Nhà truyền承:** Kèm派系, học trò nổi tiếng kèm dây truyền
- **50+ Sự kiện quan trọng:** Kèm tác động kèm phân tích
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Timeline hiển thị đúng 2500+ năm lịch sử kèm sự kiện quan trọng
- [ ] Nhà truyền承 hiển thị đúng 100+ nhà kèm派系, học trò nổi tiếng kèm dây truyền
- [ ] Sự kiện quan trọng hiển thị đúng 50+ sự kiện kèm tác động kèm phân tích
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Đồng bộ nguồn historia kèm 95% uptime
- [ ] Tìm kiếm hoạt động đúng 90% từ khóa Phật học historia

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getHistoryTimeline()` - Lấy timeline 2500+ năm lịch sử kèm sự kiện quan trọng
2. `getLineageMasters()` - Lấy 100+ nhà伝承 kèm派系, học trò nổi tiếng kèm dây truyền
3. `getImportantEvents()` - Lấy 50+ sự kiện quan trọng kèm tác động kèm phân tích
4. `getSettings()` - Lấy cài đặt historia

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T117-buddhist-history-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), History database (2500+ năm kèm sự kiện), Lineage system (100+ nhà传承 kèm派系, học徒 nổi tiếng kèm dây truyền), Events database (50+ sự kiện quan trọng kèm tác động kèm phân tích), Multi-source integration (CBETA, Wikipedia, official historia sources)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M105 (Advanced Buddhist Psychology): timeline kèm psychological events kèm practitioner development kèm insight milestones
- Kết nối dữ liệu với M108 (Buddhist Counseling Techniques): history kèm counseling development kèm lineage kèm teacher-student transmission
- Mở rộng từ M112 (Buddhist Pilgrimage): pilgrimage history kèm route development kèm sacred site kèm origin stories
- Mở rộng từ M109 (Buddhist Chaplaincy): history kèm end-of-life care kèm tradition kèm funeral rite evolution
- Mở rộng zero-RAM principle cho history data caching, chỉ hiển thị aggregates statistics chứ không user-identifiable history viewing
- Mối liên hệ với M37 (Buddhist Meditation Music): history kèm music evolution kèm chanting tradition kèm repertoire development

---