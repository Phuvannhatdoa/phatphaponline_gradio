# M75 · Haptic Feedback Suits for Meditation Enhancement

**Spec · P2**

# M75 Hoa tactor cho Pháº¡n méditation

Cung cấp hoa tactor cho pratica méditation: thiết bị áo pha hoic tactor hệ thống cung cấp phó tác rõ ràng cho trạng thái tâm lý, duy trì attention, và khuyên khích tu pratica phù hợp.

## Mục đích

Thực hiện công nghệ hoa tactor (haptic feedback) cho Phật giáo: cho phép người dùng nhận được phó tác físico khi trạng thái méditation thay đổi (focus giảm sút, thức giác, sâu méditation), và tự điều chỉnh tư thế/thư thái meditation phù hợp.

## UI/UX

- **Trang Theo dõi hoa tactor:** `/daoanh/haptic/monitor`
  - Hiển thị trạng thái phó tác: Mức độ focus (1-10), trạng thái méditation (thơmmội, sâu, awareness)
  - Phản hồi tức thời: Muaándo phó tác khi trạng thái thay đổi
  - Lịch sử: Ghi nhận các lần phó tác qua các session méditation

- **Trang Cài đặt hoa tactor:** `/daoanh/haptic/settings`
  - Chọn thiết bị: Áo hoa tactor, bàn tay, dây đệm
  - Thiết lập cường độ: Nhẹ (chỉ cảnh báo), Trung bình, Mạnh (khuyến khích mạnh mẽ)
  - Chọn chế độ: Theo cảm xúc, Theo độ focus, Theo giai đoạn méditation

- **Trang Phối hợp meditation:** `/daoanh/haptic/coordination`
  - Khớp phó tác với loại méditation: Thiền thọ, Vipassana, Zen, Pure Land
  - Tự động điều chỉnh: Phó tác khi focus giảm xuống dưới ngưỡng
  - Đảm chỉ: Tắt phó tác khi méditation sâu (để không gây distract)

## Dữ liệu

- **Thiết bị hoa tactor:** Áo pha tactor intégrated, band tay, dây đệm meditation
- **Tín hiệu:** EEG kết hợp hoa tactor (Module M73), hoặc standalone hoa tactor
- **Phản hồi:** 50+ mẫu phó tác khác nhau (nhẹng đấm, rung lên, nóng/lạnh)
- **Thời gian thực:** Phó tác tức khi trạng thái méditation thay đổi (latency < 500ms)

## Acceptance criteria

- [ ] Phát hiện đúng 80% trạng thái méditation qua tín hiệu hoa tactor
- [ ] Tăng thời lượng méditation 20% qua phó tác khuyến khích
- [ ] Tương thích với Emotiv EPOC+, Muse S, các thiết bị hoa tactor phổ biến
- [ ] Tự động bật/tắt phó tác khi đạt ngưỡng méditation sâu
- [ ] Bảo mật dữ liệu: Không chia sẻ tín hiệu não với bên thứ ba

## File tương tự

- `docs/integration/M75-haptic-suits.md`
- `docs/Mimo-Flash/T151-m75-haptic-suits.md`