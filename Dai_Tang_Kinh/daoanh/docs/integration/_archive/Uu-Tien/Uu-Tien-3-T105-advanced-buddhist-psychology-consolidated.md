# M105 · Advanced Buddhist Psychology

**Status:** 📄 Consolidated Documentation  
**Module:** M105  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp deeper analysis Abhidharma: 75-door consciousness, 52 mental factors, jhana factors, and vimokkha doors với correlation moderno brain science và clinical psychology.

## UI/UX

- **Trang Mô hình Tâm trí sâu:** `/daoanh/psychology/advanced-model`
  - Hiển thị 75-door consciousness (dvāravāti vijñāna) kèm flowchart tương quan
  - Biểu đồ 52 mental factors (cetasika) kèm陈述 (descriptions) và tương tác
  - Chọn xem theo Abhidharma Theravāda hoặc Sarvāstivāda tradition

- **Trang Jhana & Vimokkha:** `/daoanh/psychology/jhana-vimokkha`
  - Hiển thị 8 jhana factors kèm progress bar attainment level
  - 4 vimokkha doors kèm insight characteristics
  - So sánh giữa các tradición: Theravāda vs Mahāyāna vs Vajrayāna

- **Trang Áp dụng Clinical:** `/daoanh/psychology/clinical`
  - Mapping mental factors đến DSM-5 categories (có cờ cảnh báo)
  - Treatment planning kèm Buddhist psychology perspectives
  - Integration với modern psychotherapy: CBT, ACT, DBT lens

- **Trang Cài đặt Nâng cao:** `/daoanh/psychology/settings-advanced`
  - Chọn tradition: Theravāda, Sarvāstivāda, Mahāyāna, Vajrayāna
  - Thiết lập depth analysis: Sơ khai, Trung bình, Sâu
  - Tích hợp sensor: EEG frequency bands, NIRS oxygenation, HRV parameters

## Dữ liệu

- **75-door consciousness:** Complete Abhidharma mapping kèm hierarchical structure
- **52 mental factors:** Arousal, unwholesome, wholesome, rooted, unrooted categorization
- **Jhana factors:** 5 jhana factors kèm piti, sukha, ekaggata, passaddhi, sati
- **Vimokkha doors:** 4 vimokkha doors kém corruptions (anupsava)
- **Thiết bị hỗ trợ:** EEG (16 kê), NIRS (8 kê), ECG, respiration belt, GSR

## Acceptance criteria

- [ ] Hiển thị đúng 75-door consciousness kèm hierarchical structure
- [ ] Tra cứu 52 mental factors hoạt động đúng 90% từ khóa Abhidharma
- [ ] Mapping mental factors → DSM-5 categories đúng 80% cases study
- [ ] Tích hợp sensor EEG real-time (16 kê minimum, 256Hz sampling minimum)
- [ ] Tương thích với tất cả các thiết bị: iOS, Android, Web, equipment EEG
- [ ] Báo cáo tiến độ practice đúng theo Abhidharma categorization

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getConsciousnessDoors()` - Lấy 75-door consciousness mapping
2. `getMentalFactors()` - Lấy 52 mental factors với categorization
3. `getJhanaFactors()` - Lấy 8 jhana factors kèm attainment level
4. `getSettings()` - Lấy cài đặt tâm lý nâng cao

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T105-advanced-buddhist-psychology-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Abhidharma Pitaka API, EEG data integration (OpenBCI/Emotiv), Modern psychology mapping (DSM-5/ICD-11), Charting library (D3/Chart.js) cho visualization 75-door hierarchy

## Mối liên hệ với các module trước

- Xây dựng sâu trên M103 (Buddhist Psychology foundation): 108感情 men → 52 mental factors, 5 skandhas → 75-door consciousness
- Tích hợp kết quả từ M37 (Âm thanh Thiền) cho jhana analysis và depth measurement
- Kết nối dữ liệu với M50 (Neural Network Optimization) cho pattern detection trong consciousness streams
- Mở rộng zero-RAM principle cho real-time consciousness tracking 75-door
- Mở rộng từ M103 clinical application cho Abhidharma-psychology integration

---