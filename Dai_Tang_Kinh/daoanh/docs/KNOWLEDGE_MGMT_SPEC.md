# KNOWLEDGE_MGMT_SPEC.md — Knowledge Management & Training (Đạo Ảnh)

> **Conformance-pointer document (T133, 2026-09-14).** Ánh xạ đặc tả "Knowledge Base Management & Training" (spec T118)
> vào hệ thống hiện hữu + ghi rõ phần **chưa build** (task sau). KHÔNG lặp code/DB.

## 1. Khái niệm cốt lõi
- **Canonical ≠ Draft**: một claim chỉ là *canonical* khi đã qua HITL duyệt (`verification_status='verified'` + `en_audit_log`). Draft nằm `entity_claims` unverified / `*_draft` bảng — không ra người thường (trừ L2/L3 hiển thị gắn nhãn).
- **Academic Scaffolding**: 3 tầng người dùng — Cử nhân (L1, verified-only), Cao học (L2, +evidence badges), Tiến sĩ (L3, +provenance đầy đủ). Implement: T111 `?level=L1|L2|L3`.
- **Learning Path (nền tảng)**: backbone là **phả hệ truyền thừa** — lineage Lâm Tế (41 truyền 42), node 1-tầng mở rộng, nút ấn "+N nhánh"/chooser — implement T129/T130. **Gói "Lộ trình tu học" đóng gói (curriculum package, phân quyền Tăng Ni/admin) CHƯA build — task sau (candidate T134).**
- **Curation Registry (HITL)**: mọi nguồn mới qua Source Registry + License Gate (T77/T78, `data_sources` 40+ cột) → candidate (blu phases) → admin Approve/Reject, 0 auto-canonic.

## 2. Bảng ánh xạ ĐÃ-CÓ (KHÔNG làm lại)

| Đặc tả | Module tồn tại | Vị trí |
|---|---|---|
| Curriculum / nội dung học thuật chuẩn | QA retrieval + Glossary Việt + Cảnh Đức Truyền Đăng Lục (T51n2076) | `/daoanh/api/daitang/qa` · `/api/glossary?term=` (T110) · passages CBETA |
| Academic Scaffolding L1/L2/L3 | T111 | `?level=L1|L2|L3` app.py:14282/14494 |
| Trích dẫn chuẩn cho công cụ học thuật (CSL/BibTeX) | T118 | `/daoanh/api/public/export/citation` app.py:16895 |
| Feedback / bổ sung dữ liệu (yêu cầu chưa index) | data_gap_requests + user_feedback | app.py:16474–16533 ·
| Curation an toàn (0 auto-canonical, ta luôn candidate→duyệt) | T121/T120 + Source Registry | geo_cross_ref HITL · SOURCE_REGISTRY.md |
| Đánh dấu chất lượng dữ liệu | Compliance Meter | design_compliance.json + `/api/compliance/dashboard` |
| Tăng ni/admin phân quyền học thuật | Persona L1–L3 (frontend) + admin :5001 auth | server.py + T111 switcher |

## 3. Vòng phản hồi (Feedback Loop)
Khép kín 2 chiều:
- **Nội dung thiếu** (query ngoài phạm vi / NOT INDEXED) → log `data_gap_requests` (status `new`) → admin inbox.
- **Chất lượng** (lỗi bản dịch, cần hiệu đính) → `translation_error_report` (T123) + `user_feedback` → admin resolve/reject → rule fix.

## 4. CHƯA build (ghi nhận, ngoài phạm vi T133)
- Knowledge Package / Learning Path UI đóng gói theo tông (Thiền tông hiện là skeleton dữ liệu).
- Phân quyền mịn (curator vai trò) — hiện admin :5001 + persona 3 mức.
- Cross-sect interop bridge (spec T121) — `people.sect` có sẵn, chưa có bảng ánh xạ liên tông.

## 5. Trách nhiệm
- Build/QN: AI Engineer · Giá trị/quyết định: Lee Tổng · Roadmap: TD. Xem `docs/tasktodo.md` (có cột Người phụ trách trong task frontmatter `owner:`).