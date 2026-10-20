# M111 · Buddhist Language & Translation

**Status:** 📄 Consolidated Documentation  
**Module:** M111  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống học thuật Phật ngữ và dịch thuật: quản lý Pali/Sanskrit/Hán từ, chuẩn hóa bản dịch, và tích hợp CBETA/SuttaCentral/Vietnamese dictionaries cho các practitioner nghiên cứu kinh.

## UI/UX

- **Trang Từ điển Phật ngữ:** `/daoanh/language/dictionary`
  - Tra từ Pali, Sanskrit, Tiếng trung cổ, Tiếng Việt
  - Hiển thị origin, biếniên qua bảnVietnamese, tham chiếu Kinh
  - Tìm kiếm liên quan: Từ đồng nghĩa, từ trái nghĩa, xuất현 trong các Kinh

- **Trang Dịch thuật Đoạn trích:** `/daoanh/language/translation`
  - Input: Đoạn kinh Hán, Pali, Sanskrit
  - Output: Bản dịch Việt kèm footnote, citation format
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna preferences

- **Trang Cạnh thu Thư viện:** `/daoanh/language/library`
  - Quản lý từ: Thêm từ mới, sửa định nghĩa, gán thẻ
  - Biếniên bản: Theo dõng biếniên qua thời gian, phiên bản so sánh
  - Phê duyệt: Review hệ thống kèm comments từ chuyên gia

- **Trang Cài đặt:** `/daoanh/language/settings`
  - Chọn từ điển mặc định: CBETA, SuttaCentral, THL, Vietnamese custom
  - Thiết lậpưu tiên dịch: Nền tảng chính, fallback sources
  - Tích hợp API: Dictionary API keys, authentication management

## Dữ liệu

- **Thư viện từ:** 10.000+ từ Phật ngữ (Pali, Sanskrit, Hán tự, Tiếng Việt)
- **Bản dịch:** 5.000+ Đoạn trích kèm bản dịch Việt kèm citation
- **Tham chiếu:** CBETA (60.000+ bản kinh), SuttaCentral (2.000+ Sutta), THL (1.000+ bài giảng)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Từ điển hiển thị đúng 10.000+ từ Phật ngữ kèm định nghĩa
- [ ] Dịch thuật Đoạn trích đúng 90% cho 100+ Đoạn kinh mẫu
- [ ] Tìm kiếm liên quan hoạt động đúng 85% từ khóa Phật ngữ
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp API Dictionary kèm 95% uptime
- [ ] Phê duyệt bảnVietnamese đúng 80% comments chuyên gia

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getDictionarySearch(term, lang)` - Tra từ điển Phật ngữ kèm đa ngôn ngữ
2. `getTranslationUnit(sutraId, tradition)` - Dịch Đoạn trích kèm tradition preferences
3. `getLibraryManagement()` - Quản lý thư viện từ kèm biếniên tracking
4. `getSettings()` - Lấy cài đặt ngôn ngữ và từ điển

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T111-buddhist-language-translation-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Dictionary database (10.000+ từ Phật ngữ kèm đa ngôn ngữ), Translation system (sutra translation kèm citation format), Reference sources (CBETA API, SuttaCentral API, THL API), Client management system

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): therapeutic terms kèm bilingual definitions kèm translation support kèm client psychoeducation
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): mindfulness terms kèm translation kèm guided meditation scripts kèm multilingual delivery
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm Pali/Sanskrit terms kèm Abhidharma categorization kèm precise mapping
- Mở rộng từ M104 (Buddhist Ethics Modern): ethical terms kèm translation kèm contemporary discourse kèm policy documents
- Mở rộng zero-RAM principle cho dictionary lookup caching, chỉ hiển thị aggregates statistics chứ không user-search-identifiable
- Mối liên hệ với M7 (GIS Maps): geographic terms kèm temple names kèm location gazetteers kèm pilgrimage route documentation

---