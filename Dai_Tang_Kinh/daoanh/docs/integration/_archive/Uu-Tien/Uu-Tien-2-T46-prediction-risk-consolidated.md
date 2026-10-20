# M46 · Buddhist Prediction Risk

**Status:** 📄 Consolidated Documentation  
**Module:** M46  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống dự báo rủi ro Phật học: sử dụng AI và dữ liệu lịch sử practice để dự báo các rủi ro tiềm ẩn trong practice, và đề xuất các phương pháp khắc phục.

## UI/UX

- **Trang Dự báo rủi ro:** `/daoanh/risk/prediction`
  - Hiển thị rủi ro tiềm ẩn: Rủi ro méditation, rủi ro saúde, rủi ro tâm lý
   - Mức độ rủi ro: Thấp, Trung bình, Cao
   - Phương pháp khắc phục: Khuyên hướng khắc phục dựa trên AI

- **Trang Theo dõng rủi ro:** `/daoanh/risk/monitoring`
  - Theo dõng rủi ro: Theo dõng các chỉ số rủi ro qua thời gian
   - Biểu đồ: Thống kê rủi ro theo tuần/tháng/năm

- **Trang Cài đặt:** `/daoanh/risk/settings`
  - Chọn loại rủi ro: Theo dõng các loại rủi ro mong muốn
   - Thiết lập ngưỡng cảnh báo: Ngưỡng cảnh báo rủi ro cao/trung bình/thấp
   - Thông báo: Kích hoạt nhắc nhở khi rủi ro đạt ngưỡng

## Dữ liệu

- **Chỉ số rủi ro:** 10+ chỉ số rủi ro Phật học theo dõng
- **Mô hình dự báo:** Mô hình AI fine-tuned cho rủi ro Phật học (chạy offline, Zero-RAM principle)
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Dự báo rủi ro chính xác 80% so với kết quả thực tế
- [ ] Theo dõng 10+ chỉ số rủi ro chính xác 90% qua thời gian
- [ ] Biểu đồ thống kê cập nhật dưới 5s
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không phân phối dữ liệu rủi ro về bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `predictRisk(userId)` - Dự báo rủi ro cho user
2. `getRiskMonitoring(userId)` - Theo dõng rủi ro
3. `getRiskHistory(userId, period)` - Lấy lịch sử rủi ro
4. `getSettings()` - Lấy cài đặt dự báo rủi ro

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T46-prediction-risk-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI model cho rủi ro, DB theo dõng rủi ro