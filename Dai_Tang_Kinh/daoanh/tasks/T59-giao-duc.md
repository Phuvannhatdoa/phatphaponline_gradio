---
id: T59
title: "Giáo Dục — Buddhist Learning Portal (Courses & Quizzes)"
module: Education / UI / Content
priority: low
status: pending
depends_on: [T51, T52, T53]
created: 2026-08-26
updated: 2026-08-26
done_when: >
  Tab Giáo Dục (đang placeholder) thành cổng học tập: khóa học/tài liệu từ CBETA catalog,
  TTL tiểu sử, glossary; quiz + tiến độ học; content do admin quản. Feature MỚI hoàn toàn.
---

# T59 — Giáo Dục (Buddhist Learning Portal)

> **Lưu ý:** Feature này trùng lặp thấp nhất (5-10%) — cần build từ đầu. Làm SAU CÙNG.

## Mục tiêu
Xây cổng học tập cho Tăng/Ni: khóa học, tài liệu, quiz, tiến độ.

## Hiện Trạng (Codebase)
- Tab Giáo Dục (`data-t="giaoduc"`) hiện là **placeholder** ("Đang tải...")
- `cbeta_catalog_vn` (3,122 texts) — có thể làm curriculum index
- `ontology/ttl/monks/` — tiểu sử nhân vật (nội dung học)
- `/daoanh/api/translate` + `/admin/llm/summarize` — có thể tạo nội dung
- RAG Viet Chat (T11) — treo, cần Gemini; KHÔNG dùng cho T59

## Khoảng Trống (Gap)
- Zero education platform infrastructure
- Không có course/lesson data model
- Không có quiz engine, progress tracking

## Subtasks

### T59a — Course/Lesson Data Model
- Bảng: `courses(id, title, desc, source_ref, series)`, `lessons(id, course_id, title, ref_code, order)`
- Chế độ: admin tạo course + gán CBETA texts/TTL biographies làm lessons
- Seed: 1-2 khóa mẫu (vd "Tổng quan Đại Tạng", "Thiền Tông truyền thừa")

### T59b — Quiz Engine
- Bảng: `quizzes(id, lesson_id, q, options, answer, explanation)`
- API: lấy quiz theo lesson, submit + chấm điểm
- Source câu hỏi: bio + kinh văn + glossary (tự động hoặc admin nhập)

### T59c — Progress Tracking
- Bảng: `user_progress(user_id, lesson_id, status, score, ts)`
- Trang cá nhân Tăng/Ni: danh sách khóa + % hoàn thành

### T59d — Giáo Dục Tab UI
- Hoàn thiện tab Giáo Dục: danh sách khóa → chi tiết lesson (đọc kinh + quiz)
- Layout: Tailwind + Lucide (theo design system)

## API Changes
- New: `GET/POST /daoanh/api/courses`, `/api/courses/<id>/lessons`
- New: `/api/lessons/<id>/quiz`, `POST /api/quiz/submit`
- New: `GET/PUT /api/progress`

## Frontend
- Update: `places.html` tab Giáo Dục — build từ placeholder

## Không Xung Đột Với
- T51 (Nhân Vật) — dùng bio làm lesson content, không đụng portal nhân vật
- T53 (CBETA) — dùng catalog làm curriculum, không sửa
- Đây là feature cuối cùng, sau khi T51-58 ổn định

## Estimated Effort: ~20 hours (lớn nhất)

## Mở rộng scope 2026-09-09 (ráspec5 — "T118 Knowledge Base Management & User Training")
Đặc tả nhầm header "T118" về Quản trị Tri thức & Đào tạo (Learning Path / Curation Registry /
Knowledge Packages) được phân mảnh → **Learning Path + Curation thuộc task này**. Bổ sung:
- **Learning Path theo truyền thừa**: dùng nền có sẵn — `lineage_chronology` (49,560 rows) ·
  Nexus graph · `events` (3,530) · T109 conflict · truyền thừa thầy-trò (Marcus) — xây **UI lộ
  trình có thứ tự** (vd Lâm Tế đời 41→42) hòa vào Curation Registry.
- **Curation Registry / Knowledge Packages**: Admin (Lee Tổng) đóng gói bộ tài liệu từ
  **Assertion đã duyệt** (`entity_claims.verification_status='verified'` — nhờ T100/T109) thành gói
  (vd "Thiền tông đời 42") → xuất bản/đào tạo nội bộ. Giao diện đóng gói tái dùng **T119** editor.
- **Phân vai**: Learner (Tăng Ni) public read-only, thấy gói theo trình độ qua **T111** persona
  (`?level=L1/L2/L3`); Canonical/Draft tách rõ (kiến trúc sẵn có).
- KHÔNG tạo `KNOWLEDGE_MGMT_SPEC.md` (A2) — task này là spec-holder cho Learning Path/Curation.
