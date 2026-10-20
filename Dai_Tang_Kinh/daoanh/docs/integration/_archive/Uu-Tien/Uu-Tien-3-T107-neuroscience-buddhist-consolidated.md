# M107 · Neuroscience & Buddhism

**Status:** 📄 Consolidated Documentation  
**Module:** M107  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bridge Neuroscience & Buddhism: hiển thị các results nghiên cứu contemporary, neural correlates meditation, và cách khớp khái niệm Abhidharma với brain function hiện đại.

## UI/UX

- **Trang Neural Correlates:** `/daoanh/neuroscience/correlates`
  - Hiển thị mạng nơ-ron hoạt động (fMRI, EEG) kèm meditation type (Samatha, Vipassana, Metta, Jhana)
  - Biểu đồ connection strength kèm practitioner level (beginner, intermediate, advanced, master)
  - Toggle tradition: Theravāda, Mahāyāna, Vajrayāna practice styles

- **Trang Khái niệm ↔ Brain:** `/daoanh/neuroscience/mapping`
  - Tra khái niệm Abhidharma (52 mental factors, 75-door consciousness) kèm brain regions activations
  - Hiển thị lateralization: Left vs right hemisphere dominance cho từng mental factor
  - Tham chiếu nghiên cứu: Danh sách peer-reviewed studies kèm effect sizes

- **Trang Nghiên cứu mới:** `/daoanh/neuroscience/research`
  - Feed latest papers: Auto-update từ PubMed, Google Scholar cho Buddhist neuroscience
  - Filter theo: Year, tradition, meditation type, brain region, effect size
  - Full-text access: Links tới articles (open access kèm payment gateway)

- **Trang Cài đặt:** `/daoanh/neuroscience/settings`
  - Chọn modality: EEG (most accessible), fMRI (highest resolution), MEG (temporal resolution)
  - Thiết lập practitioner level: Beginner, Intermediate, Advanced, Master
  - Tích hợp device: Optional headset, caps, full-brain imaging referrals

## Dữ liệu

- **Neural correlates:** 20+ meditation types kèm brain region activation maps
- **Brain regions:** 50+ regions kèm function descriptions kèm Buddhist correlation
- **Peer-reviewed studies:** 100+ papers kèm abstract, effect sizes, methodological quality scores
- **Practitioner levels:** 4 levels kèm average session count, hours practice, reported insights
- **Thiết bị hỗ trợ:** EEG (16/32/64 kê), fMRI referrals, MEG referrals, consumer headsets (Muse, Emotiv)

## Acceptance criteria

- [ ] Hiển thị đúng 20+ meditation types kèm neural correlates brain region maps
- [ ] Tra cứu khái niệm ↔ brain mapping hoạt động đúng 85% từ khóa Abhidharma
- [ ] Feed papers auto-update mỗi semaine từ PubMed search
- [ ] Tích hợp device EEG real-time (16 kê minimum, 256Hz sampling minimum)
- [ ] Tương thích với tất cả các thiết bị: iOS, Android, Web, equipment neuroscience
- [ ] Quality filter studies hiển thị đúng methodological quality score >= 3/5

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getNeuralCorrelates(meditationType)` - Lấy neural correlates kèm brain region maps
2. `getConceptBrainMapping(concept)` - Lấy mapping khái niệm Abhidharma kèm brain regions
3. `getResearchFeed()` - Lấy research feed auto-update từ PubMed
4. `getSettings()` - Lấy cài đặt neuroscience

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T107-neuroscience-buddhist-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Neuroscience database (fMRI/EEG/MRI data), Peer-reviewed literature system (PubMed integration), Brain visualization library (Nigh/Three.js), Data API (REST/GraphQL cho neuroscience data)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M105 (Advanced Buddhist Psychology): 75-door consciousness → neural correlates mapping, 52 mental factors → brain region activations
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): therapeutic techniques kèm neural basis, outcome measures kèm brain change tracking
- Mở rộng từ M50 (Neural Network Optimization): mô hình neural network so sánh với brain imaging data, pattern detection kèm consciousness streams
- Mở rộng zero-RAM principle cho real-time brain data analysis anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable
- Mối liên hệ với M37 (Âm thanh Thiền): EEG patterns kèm meditation type, brainwave entrainment correlation

---