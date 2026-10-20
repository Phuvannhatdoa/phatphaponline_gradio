# M123 · Buddhist Epistemology & Logic

**Status:** 📄 Consolidated Documentation  
**Module:** M123  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống triết lý Phật tử về việc thức nhận biết, chứng minh kiến thức và Tổ chức tri tuệ: khung lý luận pramanavada, logic duy suy và tổ chức thông tin cho các nhà nghiên cứu và practitioner Phật tử.

## UI/UX

- **Trang Hệ thống Pramana:** `/dao epistemology/pramanas`
  - Hiển thị 3ゆる lý thức nhận biết chính: Pratyakṣa (thị giác), Anumāna (suy luận), Śabda (thông tin thừa nhận)
  - Biểu đồ logic inference: Flowchart logic inference kèm điểm yếu, điểm mạnh
  - Chọn customize: Chọn pramana kèm tradition (Theravāda, Mahāyāna, Vajrayāna)

- **Trang Logic Inquiry:** `/dao epistemology/inquiry`
  - Hỏi câu hỏi_logic: 50+ câu hỏi_logic Phật học tiêu biểu
  - Phân tích logic: Phân tích suy luận, tìm lỗi logic, đề xuất sửa đổi
  - Lưu trữ: Lưu trữ câu hỏi_logic kèm feedback, revision history

- **Trang Biểu đồ Wissen:** `/dao epistemology/knowledge-graph`
  - Hiển thị knowledge graph: Mối liên hệ giữa các khái niệm, pramana, inference pattern
  - Filter: Lọc theo tradition, theo cấp độ phức tạp, theo ứng dụng (thiền, học thuật, bảo trị)
  - Export: Xuất graph dưới dạng DOT, Mermaid, JSON kèm metadata

- **Trang Cài đặt:** `/dao epistemology/settings`
  - Chọn tradition logic: Pramana theory nào làm cơ sở
  - Thiết lập độ phức tạp: Cơ bản, Trung bình, Nâng cao
  - Tích hợp knowledge graph: Kết nối với knowledge graph system (M51/M101)

## Dữ liệu

- **3 Pramana chính:** Pratyakṣa (thị giác trực tiếp), Anumāna (suy luận), Śabda (thông tin từ nguồn uy tín)
- **5 Loại inference:** Direct perception, Indirect perception, Reasoning by analogy, Reasoning by contradiction, Testimony-based reasoning
- **7 Kategoriognition:** Root delusion, intermediate delusion, acute delusion, root delusion object, intermediate delusion object, acute delusion object, freedom from delusion
- **10 Hetu-pratyaya:** 10 nhân-kiện phối hợp cho mỗi loại inference
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, tùy chọn kết nối knowledge graph server

## Acceptance criteria

- [ ] Hiển thị đúng 3 pramana chính kèm định nghĩa Phật học
- [ ] Logic inquiry hiển thị đúng 50+ câu hỏi_logic Phật học tiêu biểu
- [ ] Biểu đồ logic inference hiển thị đúng 5 loại inference kèm điểm yếu/điểm mạnh
- [ ] Knowledge graph integration hoạt động đúng cho 90% truy vấn khái niệm Phật giáo
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tùy chọn tradition hiển thị đúng 3 tradition kèm characteristic logic pattern

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPramanas()` - Lấy 3 pramana chính kèm định nghĩa Phật học
2. `getInquiry(questionId)` - Lấy câu hỏi_logic kèm phân tích logic kèm đề xuất sửa đổi
3. `getKnowledgeGraphConnections(concept)` - Lấy kết nối knowledge graph kèm khái niệm
4. `getSettings()` - Lấy cài đặt triết lý epistemology

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T123-buddhist-epistemology-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Pramana database (3 pramana kèm định nghĩa, 5 loại inference kèm ví dụ, 7 kategoriognition kèm characterize, 10 hetu-pratyaya kèm characterize), Logic inference engine (anumana calculator, perception validator, testimony authenticator), Knowledge graph integration (M51/M101 API), Tradition selection system (Theravāda, Mahāyāna, Vajrayāna)

## Mối liên hệ với các module trước

- **Tích hợp sâu với M105 (Advanced Buddhist Psychology):** 75-door consciousness kèm epistemological categorization kèm mental factors analysis kèm pramana selection kèm meditation insight tracking
- **Kết nối dữ liệu với M51 (Advanced Knowledge Graph):** Pramana-based knowledge graph construction kèm inference pattern labeling kèm concept relationship mapping kèm graph validation
- **Mở rộng từ M50 (Neural Network Optimization):** Logic inference kèm pattern detection kèm consciousness stream analysis kèmpramana-based feature selection kèm model interpretability
- **Mở rộng từ M108 (Buddhist Counseling Techniques):** Epistemological assessment kèm cognitive distortion kèm logic error identification kèm therapeutic guideline kèm pramana-based intervention
- **Mở rộng từ M104 (Buddhist Ethics Modern):** Ethical framework kèm logical foundation kèm pramana-based ethical reasoning kèm contemporary issue analysis kèm ethical guardrails
- **Mở rộng từ M120 (Buddhist Bioethics):** Bioethical decision kèm logical validation kèm pramana selection kèm framework kèm decision support system
- **Mở rộng từ M118 (Buddhist Comparative Religion):** Comparative logic kèm tradition-specific pramana kèm cross-tradition dialogue kèm philosophical rigor
- **Mở rộng zero-RAM principle cho epistemology data caching, chỉ hiển thị aggregates statistics chứ không user-identifiable reasoning history**
- **Mối liên hệ với M37 (Buddhist Meditation Music):** Meditation logic kèm pramana kèm mindfulness kèm insight kèm ritual logic kèm chanting structure

---