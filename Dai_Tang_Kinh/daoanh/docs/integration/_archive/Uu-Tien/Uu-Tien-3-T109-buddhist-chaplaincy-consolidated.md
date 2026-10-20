# M109 · Buddhist Chaplaincy & Pastoral Care

**Status:** 📄 Consolidated Documentation  
**Module:** M109  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp framework chaplin Phật tử: chuẩn bị cho các practitioner đắc đạo hỗ trợ cộng đồng trong các tình huống chiến dịch (bệnh viện, quân đội, tù cải tạo, thiên tai), cung cấp pastoral care theo giáo pháp Phật tử.

## UI/UX

- **Trang Assessment Khách hàng:** `/daoanh/chaplaincy/assessment`
  - Spiritual needs assessment: 30+ câu hỏi kèm Buddhist framework
  - Life review kèm reflection prompts
  - Legacy planning: Values clarification, letter writing, family notification

- **Trang Lên kế hoạch Pastoral:** `/daoanh/chaplaincy/planning`
  - Care plan generation: 1-session, 3-session, 6-session options
  - Ritual prescriptions: Chanting, meditation, last rites traditions
  - Resource referral: Support groups, bereavement services, community connections

- **Trang Trình tự hướng dẫn:** `/daoanh/chaplaincy/guides`
  - Ritual scripts: Funeral, memorial, deathbed care
  - Grief support: Mini-modules cho family và community
  - Self-care for chaplin: Burnout prevention, practice maintenance

- **Trang Theo dõng progress:** `/daoanh/chaplaincy/progress`
  - Session-by-session tracking: Spiritual goals, comfort levels, ritual participation
  - Grief trajectory: Phases kèm indicators progress
  - Chaplin self-assessment: Practice quality, boundary maintenance, personal processing

## Dữ liệu

- **Assessment questionnaire:** 30+ câu hỏi kèm Buddhist spiritual framework
- **Care plans:** 1/3/6-session templates kèm ritual prescriptions
- **Ritual scripts:** 10+ scripts kèm full ceremony procedures
- **Grief modules:** 5+ modules kèm timeline và indicators
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, optional session recording (with consent)

## Acceptance criteria

- [ ] Assessment questionnaire hiển thị đúng 30+ câu hỏi kèm Buddhist spiritual framework
- [ ] Care plans generate đúng 1/3/6-session templates kèm ritual prescriptions
- [ ] Ritual scripts hiển thị đúng 10+ scripts kèm full ceremony procedures
- [ ] Grief modules hiển thị đúng 5+ modules kèm timeline indicators
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Session recording consent flow hoạt động đúng 95% trường hợp

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getAssessment()` - Lấy assessment questionnaire kèm 30+ câu hỏi kèm Buddhist framework
2. `getCarePlan(duration, focus)` - Lấy care plan kèm 1/3/6-session options kèm ritual prescriptions
3. `getRitualScripts()` - Lấy 10+ ritual scripts kèm full ceremony procedures
4. `getSettings()` - Lấy cài đặt chaplaincy

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T109-buddhist-chaplaincy-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Chaplaincy database (30+ assessment questions kèm Buddhist framework, 10+ ritual scripts kèm procedures, 5+ grief modules kèm timelines), Client management system, Session recording consent system

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): counseling techniques kèm integration kèm chaplaincy-specific modifications kèm ethical guidelines extension
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): therapeutic techniques kèm chaplaincy-specific adaptation kèm end-of-life care focus
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm spiritual needs assessment kèm existential distress targeting kèm ritual prescription
- Mở rộng zero-RAM principle cho client spiritual data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không spiritual-experiences-identifiable
- Mối liên hệ với M37 (Âm thanh Thiền): ritual chanting scripts kèm meditation music integration kèm ceremonial timing

---