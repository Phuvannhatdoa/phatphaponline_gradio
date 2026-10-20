# M136 · Buddhist Temple Data Extraction Vietnam

**Status:** 📄 Consolidated Documentation  
**Module:** M136  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quy trình trích xuất và scan dữ liệu chùa Phật giáo tại Việt Nam từ các nguồn nội địa (Wikipedia tiếng Việt, giacngo.vn) để xây dựng cơ sở dữ liệu địa lý chùa tại lãnh thổ Việt Nam, bao gồm tên chùa, địa phận, tọa độ GPS và thông tin liên hệ.

## UI/UX

- **Trang Quản lý dữ liệu chùa:** `/daoanh/temple-data/management`
  - Hiển thị danh sách chùa: Tên, địa phận, tọa độ, nguồn dữ liệu, trạng thái verify
  - Bộ lọc: Theo vùng (Bắc/Tây Bắc/Miền Nam), Theo nguồn (Wikipedia/Google Places/giacngo), Theo trạng thái (Chưa verify/Đã verify)
  - Import/Export: Nhập file CSV/JSON, Xuất báo cáo PDF

- **Trang Trình tự scan chùa:** `/daoanh/temple-data/scan`
  - Trang điều khiển quét: URL nguồn, depth quét (10/50/100 chùa), trình độ verify
  - Trạng thái quét: Số chùa đã quét/đã verify/tổng số
  - Lịch sử quét: Nhật ký các lần quét trước đó

- **Trang Kiểm tra địa lý:** `/daoanh/temple-data/geo-validation`
  - So sánh tọa độ: Nguồn gốc vs Google Places
  - Bản đồ hiện tại: Hiển thị sự chênh lệch giữa hai vị trí trên bản đồ
  - Đề xuất: Chấp nhận/Từ chối/Gạch sửa tọa độ

## Dữ liệu

- **Nguồn dữ liệu chính:** Wikipedia tiếng Việt (trong đó có 18.491 chùa đã được liệt kê nationwide)
- **Nguồn bổ trợ:** giacngo.vn, thu viện hỏa sen, tu viến quảng đức
- **Nguồn xác thực:** Google Places API (độ chính xác ±10m)
- **Tổng số chùa:** 18.491 chùa trên lãnh thổ Việt Nam (theo thống kê Wikipedia)
- **Thành phố có nhiều chùa nhất:** Hà Nội (có hơn 1.000 chùa), Thành phố Hồ Chí Minh (có hơn 800 chùa)
- **Thành phố có ít chùa nhất:** Các tỉnh duyên hải (Có thể chỉ 1-2 chùa lớn)

## Acceptance criteria

- [ ] Quét dữ liệu từ Wikipedia tiếng Việt thành công cho 100% các chùa được liệt kê
- [ ] Trích xuất đúng tên chùa, địa phận (tỉnh/thành/xã) cho 95% trường hợp
- [ ] Lấy tọa độ GPS chính xác ±10m cho 80% chùa qua Google Places API
- [ ] Tự động xác thực 50% chùa đầu tiên, remained cần manual verification
- [ ] Tương thích với định dạng DB: tên, province, latitude, longitude, source, verified
- [ ] Báo cáo xuất PDF chứa thống kê: Tổng chùa, Đã verify, Chưa verify, Theo vùng

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `extractWikipediaTemples()` - Trích xuất danh sách chùa từ Wikipedia tiếng Việt
2. `getGPSFromGoogle(ten_chua, tinh_ten)` - Lấy tọa độ qua Google Places API
3. `validateAndSave(temples_data)` - Validate và lưu vào database local
4. `getSettings()` - Lấy cài đặt quét và validate

**File path:** `docs/Mimo-Flash/M136-buddhist-temple-data-extraction-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), Web scraping library (Playwright/Selenium), Google Places API key, Database (PostgreSQL/MySQL), Charting library (D3/Chart.js) cho báo cáo thống kê

## Mối liên hệ với các module trước

- **Tích hợp với M7 (Buddhist GIS Maps):** Dữ liệu temple extraction kèm cập nhật vào bản đồ chùa Việt Nam kèm visualize kèm phân tán vùng miền kèm pilgrimage route visualization kèm spatial analysis
- **Kết nối dữ liệu với M112 (Buddhist Pilgrimage):** Temple data kèm pilgrimage routes kèm optimal travel dates kèm sacred site origin stories kèm temple amenities
- **Mở rộng từ M105 (Advanced Buddhist Psychology):** Temple data kèm meditation tracking kèm practice location kèm community center finder kèm therapist finder
- **Mở rộng từ M108 (Buddhist Counseling Techniques):** Temple data kèm counseling session finder kèm ethical guidelines kèm therapist directory kèm session booking
- **Mở rộng từ M114 (Buddhist Festivals):** Festival dates kèm temple schedules kèm ritual participation kèm participation tracking kèm festival attendance
- **Mở rộng từ M119 (Buddhist Economics):** Dana management kèm temple donation tracking kèm dana flow kèm transparency reports kèm audit logs
- **Mở rộng zero-RAM principle cho temple data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không temple-owner-identifiable location history**
- **Mối liên hệ với M37 (Buddhist Meditation Music):** Temple names kèm chanting schedules kèm meditation music playlist kèm ritual timing kèm ambient sound recommendations

---