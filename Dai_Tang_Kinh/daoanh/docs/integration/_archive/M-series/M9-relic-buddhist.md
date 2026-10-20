# M9 · Nền bản vá và kiểm chứng Phật giáo

**Spec · P1**

# M9 Bản vá và kiểm chứng

Hỗ trợ bản vá texts, kiểm chứng sai sót, so sánh phiên bản và provenance tracking cho Kinh Đạo Phật.

## Mục đích

Đảm bảo tính chính xác và nguồn gốc可追溯 cho toàn bộ dữ liệu kinh văn Phật giáo trong hệ thống.

## UI/UX

- **Trang so sánh phiên bản:** `/daoanh/text/compare`
  - So sánh hai phiên bản text (Hán/Pali/Sanskrit)
  - Highlight differences, thêm/xóa/sửa
  - Hiển thị source cho từng thay đổi

- **Trang kiểm chứng:** `/daoanh/verify/check`
  - Kiểm tra độ chính xác từ Hán-Pali-Sanskrit
  - Điểm sinh ra từ: tự động/manual
  - Lịch sử thay đổi và ai thực hiện

- **Trang provenance:** `/daoanh/provenance/tracking`
  - Theo dõi nguồn gốc từng dòng text
  - Bản vá, thay đổi, di chuyển provenance
  - Audit log cho mọi thay đổi

## Dữ liệu

- **DILA biographies** – Sự kiện đời sống (CC BY-SA)
- **CBETA texts** – Kinh bản Hán (phi thương mại)
- **SuttaCentral** – Kinh Pali (CC BY-SA)
- **GRETIL** – Văn bản Indian Languages (CC BY-NC-SA)

## Acceptance criteria

- [ ] So sánh phiên bản hiển thị đúng các điểm khác nhau
- [ ] Kiểm chứng xác nhận nguồn gốc cho 90%+
- [ ] Provenance tracking duy trì toàn bộ lịch sử thay đổi
- [ ] Audit log chứa user, timestamp, thay đổi-type

## File tương tự

- `docs/integration/M9-relic-buddhist.md`