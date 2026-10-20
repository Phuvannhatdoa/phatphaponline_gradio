# M118 · Buddhist Comparative Religion

**Status:** 📄 Consolidated Documentation  
**Module:** M118  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống So sánh Phật giáo với các tradición khác: phân tích quan điểm 공통, khác nhau giữa Phật giáo và các tradición Phật học alongside các faith khác (Hindu, Christ, Islam, ...) để hỗ trợ nghiên cứu và dialogue.

## UI/UX

- **Trang So sánh Quan điểm:** `/daoanh/comparison/philosophy`
  - Chọn chủ đề: Không-an, Thân xác, Niết-bàn, Phúc địa
  - Hiển thị quan điểm Phật giáo kèm quan điểm khác
  - Biểu đồ tương quan: Mối liên hệ và sự khác biệt

- **Trang So sánh Phương pháp:** `/daoanh/comparison/method`
  - Chọn kỹ thuật: Trình tấn, Tâm lý, Rituал, Sách sách
  - Hiển thị contrast: Phật giáo kèm tradición khác kèm so sánh chi tiết
  - Tham chiếu nguồn: Kinh, Tân kinh, Quran, Veda, ...

- **Trang Đialogue:** `/daoanh/comparison/dialogue`
  - Chủ đề tranh luận: 10+ chủ đề kèm guideline
  - Tham gia discussion: Lọc vào chủ đề, bình luận, upvote
  - Expert insights: Kết nối với thầy tọt, giáo viên Phật học contemporáneo

- **Trang Cài đặt:** `/daoanh/comparison/settings`
  - Chọn tradition so sánh: Hindu, Christ, Islam, ...
  - Thiết lậpdepth analysis: Sơ khai, Trung bình, Sâu
  - Tích hợp nguồn: Kết nối với các thư viện tài liệu

## Dữ liệu

- **10+ Chủ đề so sánh:** Kèm quan điểm Phật giáo kèm tradición khác
- **30+ Quan điểm công khai:** Kèm tham chiếu nguồn kèm hiệu lực
- **10+ Chủ đề tranh luận:** Kèm guideline kèm moderation
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] So sánh quan điểm hiển thị đúng 10+ chủ đề kèm quan điểm Phật giáo kèm tradición khác
- [ ] So sánh phương pháp hiển thị đúng 30+ quan điểm công khai kèm tham chiếu nguồn kèm hiệu lực
- [ ] Trang tranh luận hiển thị đúng 10+ chủ đề kèm guideline kèm moderation
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp nguồn tài liệu kèm 95% uptime
- [ ] Bộ lọc truyền thống hiển thị đúng các tradition cần so sánh

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getComparisonPhilosophy(topic)` - So sánh quan điểm kèm quan điểm Phật giáo kèm tradición khác
2. `getComparisonMethod(method)` - So sánh phương pháp kèm 30+ quan điểm công khai kèm tham chiếu nguồn
3. `getDialogueGuide(topic)` - Lấy guideline tranh luận kèm 10+ chủ đề kèm moderation
4. `getSettings()` - Lấy cài đặt so sánh宗教

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T118-buddhist-comparative-religion-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Comparison database (10+ chủ đề kèm quan điểm Phật giáo kèm tradición khác), Philosophy database (30+ quan điểm công khai kèm tham chiếu nguồn kèm hiệu lực), Dialogue system (10+ chủ đề tranh luận kèm guideline kèm moderation), Multi-religion support (Hindu, Christ, Islam, ...)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M105 (Advanced Buddhist Psychology): comparative psychology kèm mental factors kèm tradition-specific patterns kèm cross-tradition analysis
- Kết nối dữ liệu với M108 (Buddhist Counseling Techniques): comparative counseling kèm tradition-specific techniques kèm cross-cultural kèm therapeutic alliance
- Mở rộng từ M117 (Buddhist History): comparative history kèm tradition kèm historical development kèm evolution comparison
- Mở rộng từ M104 (Buddhist Ethics Modern): comparative ethics kèm ethical guardrails kèm interfaith dialogue kèm policy documents
- Mở rộng zero-RAM principle cho comparison data caching, chỉ hiển thị aggregates statistics chứ không user-identifiable comparison history
- Mối liên hệ với M7 (GIS Maps): comparative geography kèm religious distribution kèm spatial analysis kèm conversion hotspots

---