# M115 · Buddhist Rituals & Ceremonies

**Status:** 📄 Consolidated Documentation  
**Module:** M115  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp thư viện Kỹ thuật Lễ tiễn Phật tử: 50+ kỹ thuật ritual kèm full procedure, timing, offering requirements, dành cho practitioner và chaplin thực hành lễ đúng giáo pháp.

## UI/UX

- **Trang Library Kỹ thuật:** `/daoanh/rituals/library`
  - Lọc theo: Kiểu ritual (offering, chanting, meditation, purification), Tình huống (deathbed, funeral, memorial, holiday)
  - Hiển thị từng ritual: Goal, Duration, Step-by-step procedure, Required items, Contraindications
  - User ratings: Practitioner feedback, effectiveness scale 1-5, difficulty level

- **Trang Script Chi tiết:** `/daoanh/rituals/ritual/:id`
  - Full script: Step-by-step instructions kèm timing, posture, breathing pattern
  - Modifications: Variations kèm client/profile (beginner, advanced, trauma-sensitive)
  - Integration: Kết hợp với modern practice: Music, lighting, environment setup

- **Trang Theo dõng:** `/daoanh/rituals/tracking`
  - Session tracking: Ritual participation, personal insights, challenges
  - Progress overview: Completed rituals, favorite rituals, areas for expansion
  - Sharing: Export ritual history, export insights kèm reflection

- **Trang Cài đặt:** `/daoanh/rituals/settings`
  - Chọn tradition: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập practice schedule: Frequency, duration, ritual goals
  - Tích hợp calendar: Đối chiếu với Lịch Phật giáo (M35), ngày holy days

## Dữ liệu

- **50+ ritual techniques:** Kèm full script, goals, duration, required items
- **Client profiles:** 10+ common profiles kèm tailored modifications
- **Ethical guidelines:** Code of ethics kèm boundary settings, 15+ contraindications
- **User ratings:** Practitioner feedback effectiveness 1-5 scale, difficulty level, cultural sensitivity
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, optional session recording (with consent)

## Acceptance criteria

- [ ] Library hiển thị đúng 50+ ritual techniques kèm full script kèm goals
- [ ] Client profiles hiển thị đúng 10+ common profiles kèm tailored modifications
- [ ] Ethical guidelines hiển thị đúng code of ethics kèm 15+ contraindications
- [ ] User ratings hiển thị đúng effectiveness 1-5 scale, difficulty level, cultural sensitivity
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Session recording consent flow hoạt động đúng 95% trường hợp

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getRitualLibrary()` - Lấy 50+ ritual techniques kèm full script kèm goals
2. `getRitualDetails(ritualId)` - Lấy chi tiết ritual kèm modifications kèm integration
3. `getEthicalGuidelines()` - Lấy code of ethics kèm 15+ contraindications
4. `getSettings()` - Lấy cài đặt ritual

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T115-buddhist-rituals-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Ritual techniques database (50+ scripts kèm goals kèm qualifications), Client profile system (10+ common profiles kèm tailored modifications), Ethical guidelines code (code of ethics kèm boundary settings kèm contraindications), User rating system (effectiveness 1-5 scale, difficulty level, cultural sensitivity)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): ritual techniques kèm counseling kèm integration kèm ethical guidelines extension
- Kết nối dữ liệu với M109 (Buddhist Chaplaincy): chaplaincy rituals kèm end-of-life kèm funeral ceremonial kèm ritual scripts kèm chanting guidance
- Mở rộng từ M112 (Buddhist Pilgrimage): pilgrimage rituals kèm ritual techniques kèm pilgrimage ceremony kèm route rituals
- Mở rộng từ M37 (Buddhist Meditation Music): ritual music kèm chanting scripts kèm audio guided meditation kèm ritual soundtrack
- Mở rộng zero-RAM principle cho ritual data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không ritual-participant-identifiable session details
- Mối liên hệ với M35 (Buddhist Calendar): ritual scheduling kèm holy days kèm festival dates kèm timing optimization

---