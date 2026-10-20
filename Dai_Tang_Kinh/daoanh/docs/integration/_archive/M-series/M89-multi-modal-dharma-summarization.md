# M89 · Multi-modal Dharma Text Summarization

**Spec · P2**

# M89 Tổng hợp văn Dharma đa dạng

Cung cấp mô hình tổng hợp văn Dharma đa dạng: tạo tóm tắt đa dạng cho các Kinh, giáo Thái, và nội dung Phật giáo khác nhau dựa trên người dùng thích, độ sâu cần, và ngữ cảnh sử dụng.

## Mục đích

Thực hiện multi-modal summarization cho Dharma: cho phép practitioner nhận được các tóm tắt khác nhau cho cùng một nội dung Dharma: tóm tắt ngắn (đọc nhanh), tóm tắt chi tiết (học sâu), và tóm tắt phong cách (thuyết설,설명).

## UI/UX

- **Trang Tóm tắt văn Dharma:** `/daoanh/summary/generate`
  - Input: Nội dung Kinh, giáo Thái cần tổng hợp, Phong cách tóm tắt (Ngắn, Chi tiết, Phong cách)
  - Output: Nhiều bản tóm tắt khác nhau kèm độ tin cậy
   - Tùy chọn: Lưu vào bộ sưu tập, xuất bản, chia sẻ

- **Trang Chọn phong cách:** `/daoanh/summary/style`
  - Chọn phong cách: Trình độ học trò, Trình độ tiến sĩ, Trình độ chuyên gia
   - Tùy chỉnh: Độ dài tóm tắt (100 từ, 500 từ, 1000 từ)
   - Preview: Xem trước bản tóm tắt trước khi xuất bản

- **Trang Sử dụng:** `/daoanh/summary/history`
  - Lịch sử tóm tắt: Các bản tóm tắt đã tạo ra
  - Phản hồi: Đánh giá chất lượng tóm tắt (1-5 sao)
   - Thống kê: Số lượng nội dung đã tóm tắt, tỷ lệ sử dụng

## Dữ liệu

- **Mô hình tổng hợp:** Multi-modal Transformer fine-tuned trên 50000+ đoạn Kinh, giáo Thái
- **Phong cách:** 5 phong cách tóm tắt khác nhau được định nghĩa sẵn
- **Độ dài:** 100-3000 từ tùy chọn
- **Thời gian tạo:** < 10s cho 500 từ nội dung

## Acceptance criteria

- [ ] Tạo ra 3 loại tóm tắt (ngắn, chi tiết, phong cách) cho cùng nội dung
- [ ] Độ chính xác nội dung: Giữ nguyên 85% thông tin quan trọng
- [ ] Tăng tốc độ hiểu nội dung 50% qua tóm tắt
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi nội dung Dharma về server bên ngoài

## File tương tự

- `docs/integration/M89-multi-modal-dharma-summarization.md`
- `docs/Mimo-Flash/T165-m89-multi-modal-dharma-summarization.md`