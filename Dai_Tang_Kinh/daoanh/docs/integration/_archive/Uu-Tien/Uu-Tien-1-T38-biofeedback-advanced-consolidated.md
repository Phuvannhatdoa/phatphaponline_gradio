# M38 · Buddhist Biofeedback Meditation Optimization

**Status:** 📄 Consolidated Documentation  
**Module:** M38  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống tối ưu hóa méditation biofeedback nâng cao: theo dõng và điều chỉnh các tham số Physiological (nhịp đ tim, thở, căng thẳng) để tối ưu hóa trạng thái méditation theo thời gian thực với độ chính xác cao hơn.

## UI/UX

- **Trang Biofeedback méditation nâng cao:** `/daoanh/biofeedback/advanced`
  - Hiển thị các tham số sinh lý nâng cao: HRV (variability nhịp tim), đồ thị phân bào oxy hemoglobin (SpO2), tải ngoại thần kinh (EDA)
   - Biểu đồ thời gian thực: Đồng hoá hóa các tham số sinh lý với trạng thái méditation
   - Phản hồi tức thời: "Hãy hít sâu 4 lần" hoặc "Điều chỉnh tư thế ngồi dựa trên HRV"

- **Trang Tối ưu hóa cao cấp:** `/daoanh/biofeedback/optimize-advanced`
  - Kế hoạch tối ưu nâng cao: Khuyên hướng nhịp thở, tư thế méditation, và lịch exercise dựa trên AI phân tích
   - So sánh trước/sau: Biểu đồ so sánh hiệu quả méditation trước và sau khi tối ưu

- **Trang Cài đặt nâng cao:** `/daoanh/biofeedback/settings-advanced`
  - Chọn cảm biến nâng cao: HRM chest strap, SpO2 finger clip, Eda wristband
   - Thiết lập ngưỡng chuyên sâu: HRV cao/cấp tính/thấp, Eda nhẹ/trung tính/cao
   - Mô hình AI: Chọn mô hình phân tích (Mô hình 1, Mô hình 2, Mô hình kết hợp)

## Dữ liệu

- **Cảm biến nâng cao:** Chest strap HRM, SpO2 finger clip, Eda wristband
- **Tham số phân tích:** 30+ physiological parameters theo dõng (thêm vào 20 tham số cơ bản từ M93)
- **Mô hình AI:** Mô hình Phật học fine-tuned cho biofeedback nâng cao (chạy offline, Zero-RAM principle)
- **Thời gian phản hồi:** < 200ms từ tín hiệu đầu vào đến kết quả hiển thị

## Acceptance criteria

- [ ] Theo dõng đúng 90% các tham số sinh lý nâng cao qua cảm biến
- [ ] Phản hồi tức thời < 200ms từ tín hiệu đến hiển thị
- [ ] Tăng độ sâu méditation 30% qua tối ưu hóa biofeedback nâng cao
- [ ] Tương thích với chest strap HRM, SpO2 finger clip, Eda wristband
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu lưu trên thiết bị user

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackAdvancedBiofeedback(sensors)` - Theo dõng biofeedback nâng cao
2. `getAdvancedOptimizationPlan()` - Lấy kế hoạch tối ưu nâng cao
3. `getHigherInsights()` - Lấy kiến thức nâng cao
4. `getSettings()` - Lấy cài đặt biofeedback nâng cao

**File path:** `docs/Mimo-Flash/M38-biofeedback-advanced-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), advanced sensors, AI model cho biofeedback

---