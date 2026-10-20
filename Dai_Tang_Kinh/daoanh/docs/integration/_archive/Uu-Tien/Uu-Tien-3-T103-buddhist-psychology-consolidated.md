# M103 · Buddhist Psychology

**Status:** 📄 Consolidated Documentation  
**Module:** M103  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống tâm lý Phật giáo toàn diện: mô hình tâm trí, cảm xúc, nhận thức và các phương pháp tu tập tâm trí theo giáo pháp Abhidharma và các truyền thống hiện đại.

## UI/UX

- **Trang Tổng quan Tâm lý:** `/daoanh/psychology/overview`
  - Hiển thị mô hình tâm trí: 5aggregate (skandhas), 12 sense bases, 18 dhatus
  - Thống kê trạng thái tâm: Bức mentality hiện tại, niveau chú 집중, niveau an insights
  - Chọn pratica: Vipassana, Samatha, Mahamudra, Dzogchen

- **Trang Phân tích Cảm xúc:** `/daoanh/psychology/emotions`
  - Biểu đồ cảm xúc: Plutchik's wheel adapted Phật học
  - Theo dõng biến đổi cảm xúc qua practice
  - Phân loại 108感情 men (theo Abhidharma Theravāda)

- **Trang Phương pháp Tu tập:** `/daoanh/psychology/practice`
  - Hiển thị meditation technique: Mindfulness, Concentration, Insight
  - Hướng dẫn từng bước: Video, Text, Audio cho từng tecnica
  - Theo dõng tiến độ: Thời gian méditation, độ focuse, insight experiences

- **Trang Cài đặt:** `/daoanh/psychology/settings`
  - Chọn tradición: Theravāda, Mahāyāna, Vajrayāna, Zen
  - Thiết lập mục prática: Mục tiêu méditation hàng ngày, hàng tuần
  - Tích hợp thiết bị: Kết nối cảm biến HRV, EEG, respiration để enrich data

## Dữ liệu

- **Mô hình tâm trí:** 5aggregate (form, sensation, perception, mental formations, consciousness)
- **Cảm xúc cơ bản:** 108 감情 men (Abhidharma Theravāda) kèm characterize
- **Phương pháp méditation:** 20+ technique có nguồn gốc rõ ràng, instruction hướng dẫn
- **Kết quả tu tập:** 15+ insight уровня, từ sơ khai đến su realization
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, cảm biến ECG, EEG, respiration belt

## Acceptance criteria

- [ ] Hiển thị đúng 5 skandhas kèm(description, tương quan)
- [ ] Tra cứu 108感情 men hoạt động đúng 85% từ khóa Phật tâm lý
- [ ] Hiển thị đúng 20+ technique méditation kèm instruction
- [ ] Tương thích với tất cả các thiết bị: iOS, Android, Web, cảm biến bên ngoài
- [ ] Tích hợp dữ liệu cảm biến trong real-time (HRV, EEG minimum 10Hz)
- [ ] Báo cáo tiến độ prática đúng theo cohort analysis

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPsychologyOverview()` - Lấy tổng quan tâm lý Phật giáo
2. `getMentalModel(modelName)` - Lấy mô hình tâm trí được chọn
3. `getMeditationTechniques()` - Lấy danh sách technique méditation
4. `getSettings()` - Lấy cài đặt tâm lý

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T103-buddhist-psychology-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Abhidharma ontology, Meditation technique database, Real-time sensor integration (BLE/TCP), Charting library (D3/Chart.js) cho visualization

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M37 (Âm thanh Thiền) cho meditation technique
- Xây dựng trên M50 (Neural Network Optimization) cho emotion recognition và pattern detection
- Kết nối dữ liệu với M35 (Lịch Phật giáo) cho schedule pratica và retreat
- Mở rộng zero-RAM principle cho real-time tâm lý tracking

---