# M73 · Brain Wave Monitoring for Meditation Depth

**Spec · P2**

# M73 Theo dõi sóng não độ méditation

Cung cấp theo dõi sóng não (EEG) cho độ sâu méditation: theo dõi các tín hiệu não thời thực, phân tích độ sâu méditation (Thiền nhập samadhi, Thiền nền, Phát triển trí tuệ), và xuất báo cáo tiến độ não.

## Mục đích

Thực hiện thiết bị EEG kết hợp với ứng dụng Phật giáo: cho phép sinh viên, tăng ni theo dõi độ sâu méditation qua tín hiệu não, phát hiện các giai đoạn méditation (Thiền cơ bản, Thiền sâu, Samadhi), và nhận được phản hồi tức thời về trạng thái não.

## UI/UX

- **Trang Theo dõi sóng não:** `/daoanh/brain-wave/monitor`
  - Hiển thị tín hiệu EEG thời thực: Biểu đồ sóng não (Alpha, Beta, Theta, Gamma)
  - Phân tích độ sâu: Mức 1 (Thiền nền), Mức 2 (Thiền sâu), Mức 3 (Samadhi)
  - Phản hồi: Thông báo khi đạt được ngưỡng độ sâu méditation

- **Trang Phân tích tiến độ:** `/daoanh/brain-wave/analysis`
  - Lịch sử tín hiệu: Quá khứ 7 ngày, 30 ngày, 90 ngày
  - Biểu đồ tiến độ: Độ sâu méditation tăng giảm qua thời gian
  - Xuất báo cáo: PDF kèm biểu đồ sóng não và phân tích

- **Trang Cài đặt:** `/daoanh/brain-wave/settings`
  - Chọn thiết bị EEG: Emotiv EPOC+, Muse S, OpenBCI, 기타
  - Thiết lập ngưỡng: Độ sâu méditation cao/trung bình/thấp
  - Thông báo: Kích hoạt nhắc nhở khi đạt ngưỡng mới

## Dữ liệu

- **Tín hiệu EEG:** Alpha (8-12Hz), Beta (13-30Hz), Theta (4-7Hz), Gamma (30-100Hz)
- **Mức độ sâu:** Mức 1-3 kèm định nghĩa Phật giáo
- **Thời gian theo dõi:** Tiếp tục trong suốt session méditation, lưu trữ lịch sử
- **Thiết bị hỗ trợ:** Emotiv EPOC+, Muse S, OpenBCI, outras (có API)

## Acceptance criteria

- [ ] Phát hiện đúng 80% giai đoạn méditation qua tín hiệu EEG
- [ ] Thời gian phản hồi từ tín hiệu đến hiển thị < 1s
- [ ] Tương thích với Emotiv EPOC+, Muse S, OpenBCI
- [ ] Tạo báo cáo PDF kèm biểu đồ trong 3 phút
- [ ] Tăng nhận thức độ sâu méditation 30% qua theo dõi trực tiếp

## File tương tự

- `docs/integration/M73-brain-wave-monitoring.md`
- `docs/Mimo-Flash/T148-m73-brain-wave-monitoring.md`