# M120 · Buddhist Bioethics

**Status:** 📄 Consolidated Documentation  
**Module:** M120  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp khung đạo đức Sinh học Phật tử: hướng dẫn practitioner xử lý các vấn đề y học contemporary: hồi sinh, nghiên cứu tế bào mầm, y khoa dự báo, và hỗ trợ quyết định cuối cuộc sống kèm giáo pháp Phật tử.

## UI/UX

- **Trang Assessment Vấn đề:** `/daoanh/bioethics/assessment`
  - Assessment questionnaire: 20+ câu hỏi kèm Buddhist framework
  - Issue mapping: Hồi sinh, Nghiên cứu tế bào mầm, Y khoa dự báo, Hậu trường cuối cuộc sống
  - Buddhist framework analysis: Giữ nhận, Tâm thức, Dana

- **Trang Lên kế hoạch Phát triển:** `/daoanh/bioethics/planning`
  - Care plan generation: Các tùy chọn kèm Buddhist ethical guardrails
  - Treatment options: Medical procedures kèm Buddhist perspectives
  - Resource referral: Support groups, spiritual counseling, palliative care

- **Trang Trình tự hướng dẫn:** `/daoanh/bioethics/guides`
  - Mini-guides cho từng vấn đề: Hồi sinh, Nghiên cứu tế bào mầm, Phác đồ cuối cuộc sống
  - Ethical frameworks: Buddhist ethical principles kèm application
  - Reflection prompts: Journaling prompts, insight logging

- **Trang Cài đặt:** `/daoanh/bioethics/settings`
  - Chọn tradition: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập ngưỡng cảnh báo: Ethical thresholds, quality of life thresholds
  - Tích hợp medical records: Kết nối với EMR kèm ethical flagging

## Dữ liệu

- **Assessment questionnaire:** 20+ câu hỏi kèm Buddhist framework
- **Care plans:** 4/6/8-session templates kèm ethical guardrails
- **Ethical frameworks:** 10+ Buddhist ethical principles kèm application guidelines
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, optional integration với EMR

## Acceptance criteria

- [ ] Assessment questionnaire hiển thị đúng 20+ câu hỏi kèm Buddhist framework
- [ ] Care plans generate đúng 4/6/8-session templates kèm ethical guardrails
- [ ] Ethical frameworks hiển thị đúng 10+ Buddhist ethical principles kèm application guidelines
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp EMR kèm 90% trường hợp có ethical flagging
- [ ] Buddhist ethical principles hiển thị đúng 10+ principles kèm guidelines

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getAssessment()` - Lấy assessment questionnaire kèm 20+ câu hỏi kèm Buddhist framework
2. `getCarePlan(duration, focus)` - Lấy care plan kèm 4/6/8-session templates kèm ethical guardrails
3. `getEthicalFrameworks()` - Lấy 10+ Buddhist ethical principles kèm application guidelines
4. `getSettings()` - Lấy cài đặt đạo đức sinh học

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T120-buddhist-bioethics-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Bioethics database (20+ câu hỏi kèm Buddhist framework, 4/6/8-session templates kèm ethical guardrails, 10+ Buddhist ethical principles kèm application guidelines), EMR integration system (kèm 90% trường hợp có ethical flagging), Client management system

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): bioethical counseling kèm dana management kèm ethical guidelines extension kèm treatment planning kèm ethical guardrails
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): psychotherapy kèm end-of-life kèm palliative care kèm Buddhist bioethics kèm framework integration
- Mở rộng từ M104 (Buddhist Ethics Modern): bioethical foundations kèm ethical guardrails kèm contemporary issues kèm policy documents kèm regulatory compliance
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm mental factors kèm bioethical decision kèm consciousness expansion kèm near-death experience kèm framework
- Mở rộng zero-RAM principle cho bioethics data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không patient-identifiable medical history
- Mối liên hệ với M37 (Buddhist Meditation Music): bioethics meditation kèm end-of-life kèm palliative kèm ritual chanting kèm comfort care kèm audio guided meditation

---