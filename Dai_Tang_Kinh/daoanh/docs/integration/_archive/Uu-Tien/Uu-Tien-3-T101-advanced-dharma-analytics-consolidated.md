# M101 · Advanced Dharma Analytics

**Status:** 📄 Consolidated Documentation  
**Module:** M101  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống phân tích triδharma tiên tiến: kết hợp neural network, knowledge graph, và real-time analytics để cung cấp insights sâu về các pattern practice Phật tử, xu hướng tu Sanctuary và hiệu quả prática theo thời gian thực.

## UI/UX

- **Trang Tổng quan Analytics:** `/daoanh/analytics/overview`
  - Hiển thị metrics tổng thể: Số lượng user đang practice, thời gian méditation trung bình, retention rate hàng ngày/tuần/tháng
  - Biểu đồ thống kê: Theo thời gian, theo khu vực, theo nível practice
  - Tối 6 widget tùy chỉnh: Chọn metrics muốn hiển thị, điều chỉnh thời gian hiển thị

- **Trang Phân tích Pattern:** `/daoanh/analytics/pattern`
  - Phát hiện pattern práctica: Tự động nhận diện các pattern méditation phổ biến, các đoạn kinh được đọc nhiều nhất, các lúc đúng ngày Thánh có activity cao nhất
  - Mạng nơ-ron kiến thức: Hiển thị mối liên hệ giữa practice, kinh, và kết quả tuệ tuệ
  - Phân khúc user: Phân loại user theo level practice, mục đích, và khu vực địa lý

- **Trang Dự báo xu hướng:** `/daoanh/analytics/prediction`
  - Dự báo xu hướng practice: Dự kiến tăng/giảm активность trong 7/30/90 ngày tới
  - Dự báo nhu cầu kinh: Dự kiến các kinh cần đọc phổ biến trong giai đoạn tới
  - Cảnh báo sớm: Phát hiện các user có nguy cơ 중단 practice và đề xuất can thiệp

- **Trang Cài đặt nâng cao:** `/daoanh/analytics/settings`
  - Chọn mô hình phân tích: Mô hình cơ bản, Nâng cao, Nâng cao hơn
  - Thiết lập ngưỡng cảnh báo: Ngưỡng activity, ngưỡng retention, ngưỡng dropout
  - Tích hợp thiết bị: Kết nối cảm biến méditation, HRV, SpO2 để enrich data

## Dữ liệu

- **Triết lý dữ liệu:** Kết hợp zero-RAM principle với distributed processing cho khả năng scale lên millions of practice records
- **Mô hình Neural Network:** 10+ mô hình đã được training cho Phật học, fine-tuned cho từng loại práctica (thiền, giữ giới, étud kinh)
- **Knowledge Graph:** 1000+ nút, 5000+ quan hệ giữa entity (kỹ thuật, kinh, practice, user)
- **Real-time streaming:** 1000+ events/second từ user interactions, device sensors, calendar events
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, cảm biến bên ngoài (Apple Watch, Fitbit, гармина)

## Acceptance criteria

- [ ] Hiển thị đúng 50+ metrics analytics cơ bản và nâng cao
- [ ] Phát hiện pattern práctica đúng 80% qua Neural Network validation
- [ ] Dự báo xu hướng accuracy > 75% so với kết quả thực tế sau 30 ngày
- [ ] Phản hồi API < 2s cho câu hỏi analytics phức tạp
- [ ] Tương thích với tất cả các thiết bị: iOS, Android, Web, và các cảm biến bên ngoài
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu user được mã hóa, không chia sẻ với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getAnalyticsOverview()` - Lấy tổng quan analytics practice
2. `detectPatterns()` - Phát hiện pattern práctica qua Neural Network
3. `getPredictionForecast(period)` - Dự báo xu hướng cho khoảng thời gian
4. `getSettings()` - Lấy cài đặt analytics nâng cao

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T101-advanced-dharma-analytics-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Neural Network framework (TensorFlow/Keras), Knowledge Graph database, Real-time streaming platform (Kafka/Socket.io), Charting library (D3/Chart.js) cho visualization

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M35 (Lịch Phật giáo), M37 (Âm thanh Thiền), M50 (Neural Network Optimization)
- Xây dựng trên kết nối dữ liệu từ M7 (GIS Maps), M36 (Decentralized Storage) cho persistence
- Tuân thủ cùng các acceptance criteria zero-RAM principle với toàn bộ hệ thống PTDA

---