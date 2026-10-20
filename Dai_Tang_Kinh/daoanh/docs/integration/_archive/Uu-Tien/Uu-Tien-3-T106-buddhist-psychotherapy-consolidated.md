# M106 · Buddhist Psychotherapy

**Status:** 📄 Consolidated Documentation  
**Module:** M106  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp framework치료 Phật giáo tích hợp: kết hợp práctica truyền thống với modern psychotherapy techniques cho therapist và practitioner đau khổ tâm lý.

## UI/UX

- **Trang Assessment Khách hàng:** `/daoanh/psychotherapy/assessment`
  - Intake assessment questionnaire: 50+ câu hỏi kèm Buddhist perspective
  - Mental health screen: PHQ-9, GAD-7 integration kèm Buddhist overlay
  - Resource identification: Strengths, supports, practice history

- **Trang Lên kế hoạch Tái thiết kế:** `/daoanh/psychotherapy/planning`
  - Treatment plan generation: 6-session, 12-session, 24-session options
  - Integrated prática prescriptions: Meditation, mindfulness, moral disciplines
  - Modern techniques integration: CBT exercises, mindfulness-based interventions

- **Trang Trình tự hướng dẫn:** `/daoanh/psychotherapy/guides`
  - Mini-guides cho từng kỹ thuật: Body scan, Metta bhavana, Breath mindfulness
  - Progress tracking: Weekly check-ins, insight logging, challenge notes
  - Resource library: Audio guided meditation, worksheet, reading materials

- **Trang Theo dõng tiến độ:** `/daoanh/psychotherapy/progress`
  - Session-by-session tracking: Goals, breakthroughs, challenges
  - Phân tích xu hướng: Mental health metrics qua thời gian
  - Integration với client's practice: Meditation frequency, ethical conduct changes

## Dữ liệu

- **Assessment questionnaire:** 50+ câu hỏi kèm Buddhist rationale
- **Treatment plans:** 6/12/24-session templates kèm modular options
- **Therapeutic techniques:** 15+ techniques kèm script và instruction
- **Outcome measures:** 10+ validated scales (PHQ-9, GAD-7, WHO-5 kèm Buddhist adaptation)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, optional sensor (HRV, respiration)

## Acceptance criteria

- [ ] Assessment questionnaire hiển thị đúng 50+ câu hỏi kèm Buddhist rationale
- [ ] Treatment plans generate đúng 6/12/24-session templates kèm modular options
- [ ] Therapeutic techniques hiển thị đúng 15+ techniques kèm script instruction
- [ ] Outcome measures integration PHQ-9/GAD-7/WHO-5 kèm Buddhist adaptation
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Session tracking hiển thị đúng progress theo 10+ outcome measures

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getAssessment()` - Lấy assessment questionnaire kèm 50+ câu hỏi
2. `getTreatmentPlan(duration, focus)` - Lấy treatment plan kèm modular options
3. `getTherapeuticTechniques()` - Lấy 15+ therapeutic techniques kèm script
4. `getProgressTracking()` - Lấy session-by-session tracking system

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T106-buddhist-psychotherapy-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Psychotherapy database (CBT/ACT/DBT scripts), Buddhist practice library (meditation guides, ethical guidelines), Outcome measures system (PHQ-9/GAD-7/WHO-5 adaptation), Client management system

## Mối liên hệ với các module trước

- Xây dựng trên M103 (Buddhist Psychology foundation): 5 skandhas, 108感情 men, 75-door consciousness → framework assessment và treatment planning
- Tích hợp kết quả từ M37 (Âm thanh Thiền) cho meditation prescription kèm technique guidance
- Kết nối dữ liệu với M105 (Advanced Buddhist Psychology) cho 75-door consciousness mapping và mental factors analysis
- Mở rộng zero-RAM principle cho client session data tracking anony-mized
- Mở rộng từ M104 (Ethics Modern) cho ethical guidelines integration kèm therapeutic relationship

---