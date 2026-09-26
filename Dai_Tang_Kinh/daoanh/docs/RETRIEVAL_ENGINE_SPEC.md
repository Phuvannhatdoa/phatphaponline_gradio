# RETRIEVAL_ENGINE_SPEC.md — Bộ máy Truy vấn Giáo lý (Doctrine Retrieval Engine)

> **Conformance-pointer document (T135, 2026-09-14).** KHÔNG lặp code/DB. File này ánh xạ đặc tả "Task T117: Doctrine Retrieval Engine"
> (mã "T115" trong đặc tả — số board T115 = Source Authority Matrix; đặc tả này = **board T117 = T100+T111+T113**)
> vào các module **đã tồn tại** của hệ thống. Mọi chi tiết kỹ thuật đọc ở nguồn được trỏ tới đây.

## 1. Mục tiêu (khớp đặc tả)
Role-based Query Logic: hệ thống tự điều chỉnh độ chi tiết + an toàn data theo cấp học thuật
(Cử nhân → Cao học → Tiến sĩ). Đây là "máy lọc học thuật", không phải tìm kiếm từ khóa kiểu Google.

## 2. Bảng ánh xạ ĐÃ-CÓ (KHÔNG làm lại)

| Đặc tả | Module tồn tại | Vị trí (verified 2026-09-14) |
|---|---|---|
| **Policy Filter 3 tầng** | **T111 persona L1/L2/L3** — `?level=L1\|L2\|L3`; **L1 server-side clip claims → chỉ `verified`** | app.py:14282/14350/14494/14557 |
| — Cử nhân (CoreClaim, ẩn Provenance, trả ngắn + nguồn) | L1: evidence drawer ẩn source_code/kỹ thuật, chỉ verified | places.html `_daEvidenceDrawer` L7595–7664 |
| — Cao học (CoreClaim + ContextTags + Assertion Relationship, so sánh cùng tag khác nguồn) | L2: drawer nhóm theo `claim_type` + badge `source_code` từng nguồn + bộ lọc assertion_level/claim_type → đối chiếu đa nguồn | `_daEvRows` (claim_type h1 + source_code badge) · filter L7633-7635 |
| — Tiến sĩ (Full Assertion Object: Audit ID + Review Status + Provenance) | L3: claim_id + confidence + source_reference + assertion_level + verification_status; `audit_id` SHA-256 **T118/T109** | app.py evidence endpoint L14332-14338 · `entity_claims_audit` · `/daoanh/api/research/entity/<id>/audit-trail` (**T135, mới**) |
| **Evidence Drawer luôn đi kèm** (No Evidence = No Answer) | `_daEvidenceDrawer` gắn mọi khối giáo lý/evidence — nguồn + passage đầy đủ, không trả lời suông | places.html:7504/8139 |
| **Data Disclaimer động** | `_daZenqDisclaimer()` (nhãn trình độ + học thuật tham khảo + không tư vấn + nút đổi trình độ) | places.html:7569 |
| **Persona-based Access** | Switcher **tường minh** localStorage `da_persona_level` (default L2) + server clip L1. **Lưu ý deviation:** đặc tả yêu cầu "tự nhận diện" — hệ thống dùng switcher có chủ ý (auto-detect bất định + riêng tư), giữ nguyên (đã phê chuẩn T111). | places.html:7526 |
| **NOT INDEXED / NO DATA trung thực** (không bịa) | **T126 QA** → `mode:'no_data'` status 200 + ghi `data_gap_requests` | app.py:18536 · `OPS_GAP_TABLE` |
| Bảng thẩm định (phân cấp/trung thực/minh bạch/negative) | UAT persona script chạy 3 case thật + Compliance Meter | `scripts/uat_persona_test.py` (T133) · `verify_design_compliance.py` (T113) |

## 3. Qui trình vận hành (trỏ nguồn, không lặp)
1. Người dùng truy vấn → hệ thống xác định trình độ (switcher tường minh).
2. Retrieval: QA backend **bắt buộc citations/evidence** (không AI summary trống) — hợp đồng phản hồi T126.
3. Render: L1 clip `verified`; L2/L3 thêm tầng assertion + provenance; mọi tầng đều mount Evidence Drawer.
4. Ngoài phạm vi ngữ liệu → `no_data` trung thực + ghi `data_gap_requests` (KHÔNG bịa).

## 4. Tiến sĩ Audit Trail (T118 — đóng trong T135 2026-09-14)
`GET /daoanh/api/research/entity/<entity_ref>/audit-trail` (public, read-only, 0 ALTER):
- `history`: `en_audit_log` append-only (ai · lúc nào · lý do · old/new · evidence_sources · authority_rank · verification_status) + `audit_id=en-<log_id>`.
- `claims_audit`: mỗi claim kèm `audit_id` SHA-256 (`entity_claims_audit`) + `verification_status` + sample 20.
- `data_status: indexed|no_data` trung thực (chuỗi không khớp → no_data, Không tự bịa lịch sử).

## 5. Bảng thẩm định (dành cho Lee Tổng) — cách verify từng dòng
| Tiêu chí | Cách verify |
|---|---|
| **Tính phân cấp** — Cử nhân không bị rối thuật ngữ | Mở places.html → đổi persona L1 → mở Evidence Drawer: không thấy claim_id/source_code/confidence; chỉ verified |
| **Tính trung thực** — Mọi kết quả có Evidence Drawer | Mọi khối giáo lý/evidence gọi `_daEvidenceDrawer`; grep `_daEvidenceDrawer(` tại chỗ render |
| **Tính minh bạch** — Rõ nguồn đang dùng | L2/L3 badge `source_code` + `source_reference`; không source_code → badge nguồn fallback |
| **Negative case** — Ngoài phạm vi báo trung thực | QA `mode:no_data` 200 + `data_gap_requests` có status `new`; không 502/504 (xem `uat_persona_test.py` Test 3) |

## 6. Non-goals (boundary)
- KHÔNG tạo `docs/PROJECT_STATUS.md` (SSOT: tasktodo + dashboard). KHÔNG rebuild engine. KHÔNG auto-detect persona.
- KHÔNG thay DOI/thay citation hiện có. Trạng thái task cập nhật qua `docs/tasktodo.md` (không qua PROJECT_STATUS.md).

## 7. Trách nhiệm
- Build/QA: AI Engineer · Giá trị/quyết định: Lee Tổng (admin) · Roadmap/kiểm soát tiến độ: TD.