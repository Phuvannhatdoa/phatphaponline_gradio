# M137 · Vietnamese Monk Data Extraction Vietnam

**Status:** 📄 Consolidated Documentation  
**Module:** M137  
**Created:** 2026-10-06  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quy trình trích xuất và scan dữ liệu **tu sĩ Việt Nam** (nhà sư, trụ trì, thiền sư, giảng sư Phật giáo Việt Nam) từ các nguồn nội địa (Wikipedia tiếng Việt, giacngo.vn, thuvienhoasen.org, khoa học Phật giáo) để xây dựng cơ sở dữ liệu tu sĩ tại lãnh thổ Việt Nam, bao gồm họ tên, pháp danh, chùa trú xứ, quê quán, thời kỳ, dòng pháp phái và thông tin tiểu sử.

## UI/UX

- **Trang Quản lý dữ liệu tu sĩ:** `/daoanh/monk-data/management`
  - Hiển thị danh sách tu sĩ: Pháp danh, họ tên, chùa trú xứ, tỉnh/thành, thời kỳ, nguồn dữ liệu, trạng thái verify
  - Bộ lọc: Theo vùng (Bắc/Miền Trung/Miền Nam), Theo thời kỳ (Lý/Trần/nhà Nguyễn/đương đại), Theo dòng phái (Thiền tông/Tịnh độ/Khối giáo), Theo nguồn (Wikipedia/giacngo/thuvienhoasen), Theo trạng thái (Chưa verify/Đã verify)
  - Import/Export: Nhập file CSV/JSON, Xuất báo cáo PDF

- **Trang Trình tự scan tu sĩ:** `/daoanh/monk-data/scan`
  - Trang điều khiển quét: URL nguồn, depth quét (10/50/100 tu sĩ), trình độ verify
  - Trạng thái quét: Số tu sĩ đã quét/đã verify/tổng số
  - Lịch sử quét: Nhật ký các lần quét trước đó

- **Trang Kiểm tra danh tính (Identity Validation):** `/daoanh/monk-data/identity-validation`
  - So sánh danh tính: Pháp danh vs họ tên thường gọi vs bí danh (nhiều nguồn ghi khác nhau)
  - Bản đồ dòng pháp phái: Hiển thị sự chênh lệch/quan hệ thầy–trò giữa hai nguồn trên graph
  - Đề xuất: Chấp nhận/Từ chối/Gạch sửa (merge duplicate, sửa thời kỳ, gỡ liên kết sai)

## Dữ liệu

- **Nguồn dữ liệu chính:** Wikipedia tiếng Việt (danh mục "Tu sĩ Phật giáo Việt Nam", các bài về thiền sư/trụ trì)
- **Nguồn bổ trợ:** giacngo.vn, thuvienhoasen.org, thuvienphatgiao.com, trang tin các chùa/giới chức Phật giáo
- **Nguồn xác thực:** Đối chiếu chéo nhiều nguồn (cross-source) + tiểu sử do chùa/trụ trì xác nhận
- **Dữ liệu sẵn có trong hệ thống:** `data/processed/monk_names.json` (2.865 pháp danh), `data/processed/genealogy_data.json` (912 nodes RDF), `data/lineage_tree.json` (3.196 tu sĩ offline)
- **Thời kỳ trọng tâm:** Từ thiền phái Lý–Trần đến tu sĩ đương đại (nhà Nguyễn, 1945→nay)
- **Khu vực có nhiều tu sĩ nhất:** Miền Bắc (Hà Nội, Bắc Ninh, Ninh Bình - các trung tâm thiền phái cổ), Miền Trung (Huế), Miền Nam (TP.HCM, Đồng Nai)

## Acceptance criteria

- [ ] Quét dữ liệu từ Wikipedia tiếng Việt thành công cho 100% các tu sĩ được liệt kê trong danh mục
- [ ] Trích xuất đúng pháp danh, họ tên, chùa trú xứ, tỉnh/thành cho 95% trường hợp
- [ ] Suy ra thời kỳ sinh–hoạt (năm mất hoặc khoảng thời gian) chính xác cho 80% tu sĩ có nguồn ghi rõ
- [ ] Tự động xác thực 50% tu sĩ đầu qua khớp ít nhất 2 nguồn độc lập, remained cần manual verification
- [ ] Gắn đúng dòng pháp phái / thầy–trò (thụ pháp sư) cho 85% trường hợp có dữ liệu liên kết
- [ ] Tương thích với định dạng DB: `name, dharma_name, alias, temple, province, era, lineage, teacher, birth_year, death_year, source, verified`
- [ ] Báo cáo xuất PDF chứa thống kê: Tổng tu sĩ, Đã verify, Chưa verify, Theo vùng, Theo thời kỳ

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `extractWikipediaMonks()` - Trích xuất danh sách tu sĩ từ Wikipedia tiếng Việt (danh mục + infobox)
2. `normalizeMonkIdentity(ten_phap_danh, ho_ten, bi_danh)` - Chuẩn hóa danh tính, gộp trùng tên (bỏ dấu, thứ tự tên)
3. `getLineageAndTemple(monk_name)` - Lấy chùa trú xứ + dòng phái + thầy–trò qua `/api/get_lineage` hoặc GraphDB SPARQL
4. `validateAndSave(monks_data)` - Validate và lưu vào database local
5. `getSettings()` - Lấy cài đặt quét và validate

**File path:** `Dai_Tang_Kinh/daoanh/docs/integration/M137-vietnamese-monk-data-extraction-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), Web scraping library (Playwright/Selenium), Database (PostgreSQL/MySQL), GraphDB SPARQL endpoint (dòng phái), Charting library (D3/Chart.js) cho báo cáo thống kê

## Mối liên hệ với các module trước

- **Tích hợp với M136 (Buddhist Temple Data Extraction):** Temple data kèm monk residence data kèm liên kết chùa–tu sĩ hai chiều
- **Tích hợp với VisJS Lineage App (`thientong.py`):** Monk extraction kèm tự động populate `monk_names.json` kèm mở rộng `genealogy_data.json` (912→n nodes) kèm lazy-load 3 thế hệ
- **Kết nối dữ liệu với M7 (Buddhist GIS Maps):** Monk data kèm bản đồ phân bố tu sĩ theo vùng miền kèm pilgrimage site gắn với vị trí trú xứ
- **Kết nối dữ liệu với M112 (Buddhist Pilgrimage):** Monk biography kèm sacred site origin stories kèm chùa thờ/nhục thân tu sĩ
- **Mở rộng từ M105 (Advanced Buddhist Psychology):** Monk teachings kèm meditation lineage kèm practice location
- **Mở rộng từ M114 (Buddhist Festivals):** Monk dates (ngày mất/ngày Đản) kèm lịch lễ kỷ niệm tại chùa
- **Mở rộng zero-RAM principle cho monk data tracking anonymized, chỉ hiển thị aggregates statistics (thống kê theo vùng/thời kỳ) chứ không personal data nhận diện tu sĩ còn hoạt động**
- **Mối liên hệ với M37 (Buddhist Meditation Music):** Monk names kèm chanting/lecture audio kèm thiền âm playlist theo thầy

---