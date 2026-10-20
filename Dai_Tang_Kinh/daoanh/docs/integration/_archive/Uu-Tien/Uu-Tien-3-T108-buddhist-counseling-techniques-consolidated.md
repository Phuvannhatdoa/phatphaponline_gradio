# M108 · Buddhist Counseling Techniques

**Status:** 📄 Consolidated Documentation  
**Module:** M108  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp library kỹ thuật tư vấn Phật giáo: 20+ phương pháp phối hợp práctica tradición với modern counseling skills cho counselor và teacher.

## UI/UX

- **Trang Library Kỹ thuật:** `/daoanh/counseling/techniques`
  - Filter theo: Meditation type (Samatha, Vipassana, Metta, Jhana), Issue (anxiety, depression, grief, relationship), Tradition (Theravāda, Mahāyāna, Vajrayāna)
  - Hiển thị từng technique: Goal, Duration, Script snippet, Required qualifications, Contraindications
  - User ratings: Practitioner feedback, effectiveness scale 1-5, difficulty level

- **Trang Script Chi tiết:** `/daoanh/counseling/technique/:id`
  - Full script: Step-by-step instructions kèm timing, posture, breathing pattern
  - Modifications: Variations kèm client profile (beginner, advanced, trauma-sensitive)
  - Integration: Kết hợp với modern counseling skills (active listening, reflection, normalization)

- **Trang Supervision:** `/daoanh/counseling/supervision`
  - Case presentation: Upload recording (with consent), written summary kèm supervisor feedback
  - Peer discussion: Forum kèm moderation guidelines, ethical boundaries
  - Resource library: Templates, worksheets, referral guidelines

- **Trang Cài đặt:** `/daoanh/counseling/settings`
  - Chọn tradition: Theravāda, Mahāyāna, Vajrayāna, Combined
  - Thiết lập client profile: Age, cultural background, trauma history, practice experience
  - Tích hợp ethical guidelines: Code of ethics kèm boundary settings, referral criteria

## Dữ liệu

- **20+ counseling techniques:** Kèm full script, goals, duration, qualifications
- **Client profiles:** 10+ common profiles kèm tailored modifications
- **Ethical guidelines:** Code of ethics kèm boundary settings, 15+ referral criteria
- **User ratings:** Practitioner feedback effectiveness 1-5 scale, difficulty level, cultural sensitivity
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, optional session recording (with consent)

## Acceptance criteria

- [ ] Library hiển thị đúng 20+ counseling techniques kèm full script kèm goals
- [ ] Client profiles hiển thị đúng 10+ common profiles kèm tailored modifications
- [ ] Ethical guidelines hiển thị đúng code of ethics kèm 15+ referral criteria
- [ ] User ratings hiển thị đúng effectiveness 1-5 scale, difficulty level, cultural sensitivity
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Session recording consent flow hoạt động đúng 95% trường hợp

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getCounselingTechniques()` - Lấy 20+ techniques kèm full script kèm goals
2. `getTechniqueDetails(techniqueId)` - Lấy chi tiết technique kèm modifications kèm integration
3. `getEthicalGuidelines()` - Lấy code of ethics kèm 15+ referral criteria
4. `getSettings()` - Lấy cài đặt tư vấn

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T108-buddhist-counseling-techniques-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Counseling techniques database (20+ scripts kèm goals kèm qualifications), Client profile system (10+ common profiles kèm tailored modifications), Ethical guidelines code (code of ethics kèm boundary settings kèm referral criteria), User rating system (effectiveness 1-5 scale, difficulty level, cultural sensitivity)

## Mối liên hệ với các module trước

- Xây dựng sâu trên M106 (Buddhist Psychotherapy framework): therapeutic techniques kèm full script kèm treatment plans kèm outcome measures
- Tích hợp kết quả từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm mental factors analysis kèm mental factors targeting kèm technique selection
- Kết nối dữ liệu với M107 (Neuroscience & Buddhism): neural correlates kèm technique selection kèm expected brain changes, practitioner level kèm technique effectiveness mapping
- Mở rộng từ M37 (Âm thanh Thiền): meditation technique kèm script guidance kèm audio guided meditation integration
- Mở rộng zero-RAM principle cho client data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable session details

---