# M104 · Buddhist Ethics in Modern Context

**Status:** 📄 Consolidated Documentation  
**Module:** M104  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp khung đạo đức Phật giáo ứng với các desafio đời sống hiện đại: công nghệ, kinh doanh, xã hội, y học và môi trường, giúp practitioner duy trì practice kết nối với thực tại đời sống.

## UI/UX

- **Trang Tổng quan đạo đức:** `/daoanh/ethics-modern/overview`
  - Hiển thị các vấn đề đạo đức chính: Công nghệ, Kinh doanh, Xã hội, Y học, Môi trường
  - Biểu đồ conflicts: Mối xung đột giữa đạo đức truyền thống và bối cảnh hiện đại
  - User stance: Hiển thị vị trí user trong mỗi vấn đề (đang tư vấn, đang tranh chấp, đã quyết định)

- **Trang Phân tích Vấn đề:** `/daoanh/ethics-modern/issue/:topic`
  - Chọn topic: Tự sinh sản, Kết hôn đồng giới, Mô hình kinh doanh, AI Ethics, Khí hậu
  - Hiển thị quan điểm Phật giáo: Trích dẫn Kinh, luận pháp, quan điểm các phái
  - Hiển thị quan điểm contemporáneo: Đọc giả, chuyên gia, quyết định pháp lý (kùm referral)

- **Trang Nghĩa giải Áp dụng:** `/daoanh/ethics-modern/application`
  - Hiển thị ứng dụng thực tiễn: Quy tắc sống hàng ngày, quy tắc làm việc, quy tắc tương tác
  - Biểu đồ case studies: Kết quả thực tiễn từ practitioner, trường hợp nghiên cứu
  - Tải nguyên tắc: Tải các quy tắc đạo đức (Sila, Patimokkha, Vinaya) dưới dạng PDF/CSV

- **Trang Thảo luận:** `/daoanh/ethics-modern/discussion`
  - Tham gia thảo luận: Lọc vào các chủ đề đạo đức, bình luận, upvote
  - Moderation: Well-defined guidelines, filter ngôn từ, user reputation system
  - Expert insights: Kết nối với thầy tọt, giáo viên Phật học contemporáneo

## Dữ liệu

- **Vấn đề đạo đức:** 15+ vấn đề contemporary có trích dẫn Kinh và luận pháp
- **Case studies:** 50+ case studies thực tiễn từ practitioner qua thế giới
- **Quan điểm phái:** 10+ phái/tradition kèm position trên mỗi vấn đề
- **Quan hệ pháp lý:** 20+ jurisdictions kèm referral luật applicable
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 15+ vấn đề đạo đức contemporary kèm trích dẫn nguồn
- [ ] Case studies hiển thị đúng 50+ trường hợp thực tiễn
- [ ] Quan điểm phái hiển thị đúng 10+ tradition kèm position statement
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp referral luật kèm 90% jurisdictions có document pháp lý
- [ ] Bảng tương xung vấn đề hiển thị đúng 80% casos 복잡

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getEthicsOverview()` - Lấy tổng quan đạo đức Phương Đông tương đại
2. `getIssueDetails(topic)` - Lấy chi tiết vấn đề được chọn
3. `getApplicationGuide(issue, context)` - Lấy hướng dẫn ứng dụng thực tiễn
4. `getSettings()` - Lấy cài đặt đạo đức hiện đại

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T104-buddhist-ethics-modern-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Contemporary ethics database, Multi-tradition position system, Legal referral database, Multi-language support (English, Vietnamese, Chinese, Tibetan)

## Mối liên hệ với các module trước

- Tích hợp dữ liệu từ M41 (Ethics Analytics) cho foundation analytics đạo đức
- Xây dựng trên M38 (Biofeedback Advanced) cho physiological response đến các vấn đề đạo đức
- Kết nối với M103 (Buddhist Psychology) cho psychological perspective
- Mở rộng từ M7 (GIS Maps) cho spatial analysis các cộng đồng practice kèm địa lý

---