# M13 · Căn chỉnh đa ngôn ngữ cho Cử Nhân

**Spec · P1**

# M13 Căn chỉnh Hán - Pali - Sanskrit

Cung cấp khả năng căn chỉnh và tra cứu Song-song giữa Hán, Pali, Sanskrit cho trình độ Cử Nhân.

## Mục đích

Đỗ người dùng Cử Nhân tìm kiếm và hiểu quan hệ giữa các phiên bản Kinh trên các ngôn ngữ khác nhau một cách trực quan.

## UI/UX

- **Trang so sánh Song-song:** `/daoanh/compare/parallel`
  - Input: Tên kinh hoặc ID Hán
  - Output: Bảng so sánh Pali/Sanskrit với badge nguồn
  - Hiển thị: Sự khác biệt ý nghĩa, từ đồng nghĩa, từ trái nghĩa

- **Trang tra cứu nhanh:** `/daoanh/search/quick`
  - Tự động chuyển đổi từ Hán sang Pali/Sanskrit
  - Hiện danh sách các bản tương ứng
  - Lọc theo độ chính xác: cao/trung bình/thấp

## Dữ liệu

- **CBETA texts:** 13.933 kinh Hán (phi thương mại)
- **SuttaCentral:** Kinh Pali (CC BY-SA)
- **DSBC:** Văn bản Sanskrit Bắc truyền
- **GRETIL:** Văn bản Indian Languages (CC BY-NC-SA)

## Acceptance criteria

- [ ] So sánhSong-song hiển thị đúng 3 phiên bản (Hán/Pali/Sanskrit) cho 80% kinh phổ biến
- [ ] Tra cứu nhanh chuyển đổi từ Hán sang Pali chính xác cho 100+ từ Hán phổ biến
- [ ] Badge nguồn hiện cho mọi kết quả
- [ ] Tốc độ phản hồi < 300ms cho truy vấn cơ bản

## File tương tự

- `docs/integration/M13-parallel-text-alignment.md`
- `docs/Mimo-Flash/T88-m13-parallel-text-alignment.md`