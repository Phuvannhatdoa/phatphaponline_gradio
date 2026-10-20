# M81 · Edge Computing for Real-Time Meditation Analysis

**Spec · P2**

# M81 Tính toán biên cho Phân tích méditation thời thực

Cung cấp giải pháp tính toán biên (edge computing) cho phân tích méditation thời thực: xử lý dữ liệu EEG, tín hiệu não, và trạng thái cảm xúc trên thiết bị cụt (edge device) thay vì gửi về máy chủ đám mây, đảm bảo latency thấp và tuân thủ nguyên tắc Zero-RAM.

## Mục đích

Thực hiện tính toán biên cho Phật giáo: cho phép phân tích trạng thái méditation, độ sâu não, và cảm xúc tức thời trên thiết bị di động hoặc máy tính xách tay mà không cần kết nối internet liên tục, phù hợp cho practice tại các khu vực có kết nối yếu hoặc для практики méditation bất cứ lúc nào.

## UI/UX

- **Trang Phân tích biên:** `/daoanh/edge/analysis`
  - Hiển thị kết quả tức thời: Độ sâu méditation (1-3), Trạng thái não (Alpha/Beta/Theta/Gamma), Cảm xúc (Bình yên/Tranh tấn/Tâm lý)
  - Biểu đồ thời gian thực: Quay vòng não, sóng cảm xúc
  - Kết quả lưu cục bộ: Lưu trực tiếp vào bộ nhớ thiết bị (không gửi về server)

- **Trang Cài đặt biên:** `/daoanh/edge/settings`
  - Chọn thiết bị: iPhone, Android phone, Raspberry Pi, laptop
  - Thiết lập mức độ xử lý: Nhẹ (chỉ cơ bản), Trung bình, nặng (full analysis)
  - Chế độ ngoại tuyến: Kích hoạt/pNgắt chế độ hoạt động không cần internet

- **Trang Xuất bản kết quả:** `/daoanh/edge/export`
  - Xuất báo cáo: PDF kèm biểu đồ não, cảm xúc lưu cục bộ
   - Chia sẻ: Chia sẻ qua email, mạng xã hội hoặc lưu vào bộ sưu tập cá nhân

## Dữ liệu

- **Xử lý trên thiết bị:** EEG signals, PPG (heart rate), GSR (skin conductance)
- **Mô hình phân loại:** Mô hình nhẹ (lightweight) chạy trên CPU thiết bị, không cần GPU
- **Thời gian phản hồi:** < 200ms từ tín hiệu đầu vào đến kết quả hiển thị
- **Lưu trữ:** Tất cả dữ liệu lưu trên thiết bị user, không có dữ liệu nào được gửi về server mặc định

## Acceptance criteria

- [ ] Phân tích đúng 80% trạng thái méditation trên thiết bị cục bộ
- [ ] Thời gian phản hồi từ tín hiệu đến hiển thị < 200ms
- [ ] Tương thích với Emotiv EPOC+, Muse S, và các cảm biến não phổ biến
- [ ] Hoạt động đúng 100% chế độ ngoại tuyến (offline)
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu chỉ lưu trên thiết bị user, không bao giờ gửi về server

## File tương tự

- `docs/integration/M81-edge-computing.md`
- `docs/Mimo-Flash/T157-m81-edge-computing.md` (ưu đãi cho người test beta)