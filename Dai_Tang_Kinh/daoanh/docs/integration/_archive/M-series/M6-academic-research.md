# M6 · Nền tài liệu học thuật và nghiên cứu Phật giáo

**Spec · P1**

# M6 Nguồn học thuật và nghiên cứu

Cung cấp kho tài liệu học thuật Phật giáo: glossary, tham khảo peer-reviewed, citation generation, bibliography generation.

## Mục đích

Cung cấp năng lực tra cứu từ, kiểm chứng nguồn acadêmic và tạo citation cho người nghiên cứu Phật giáo.

## UI/UX

- **Trang tìm kiếm glossary:** `/daoanh/academic/glossary`
  - Ô tìm kiếm từ Hán, Pali, Sanskrit, Tiếng Việt
  - Lọc theo nguồn: GRETIL, DSBC, PTS, THL, Open Philology
  - Kết quả hiển thị: từ, định nghĩa, nguồn, citation format

- **Trang citation:** `/daoanh/academic/citation`
  - Chọn format: Chicago, MLA, APA
  - Input: Tên từ/ kinh, hoặc ID
  - Output: Citation kèm footnote, bibliography entry

- **Trang bibliography:** `/daoanh/academy/bibliography`
  - Xuất JSON/CSV cho toàn bộ từ/search history
  - Filter: ngôn ngữ, nguồn, bậc học

## Dữ liệu

- **GRETIL** – Göttinger Register of Electronic Texts in Indian Languages (CC BY-NC-SA)
- **DSBC** – Digital Sanskrit Buddhist Canon (phi thương mại)
- **PTS** – Pali Text Society Digital Editions (CC BY-NC)
- **THL** – The Tibetan and Himalayan Library (CC BY-SA)
- **Open Philology** – Œuvres philosophiquesouvertes (CC0)

## Acceptance criteria

- [ ] Glossary search trả kết quả cho 100+ từ Hán-Pali-Sanskrit phổ biến
- [ ] Peer-review validation đánh giá nguồn có badge uy tín/không uy tín
- [ ] Citation tạo đúng format Chicago/MLA/APA kèm footnote
- [ ] Bibliography xuất JSON có `title, author, language, source, url`
- [ ] Full-text search hoạt động trên CBETA + SuttaCentral texts

## File tương tự

- `docs/integration/M6-academic-research.md`
- `docs/Mimo-Flash/T80-m6-academic-research.md`