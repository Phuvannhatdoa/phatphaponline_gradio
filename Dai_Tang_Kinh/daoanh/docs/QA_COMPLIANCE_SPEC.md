# QA_COMPLIANCE_SPEC.md — System QA & Compliance (Đạo Ảnh)

> **Conformance-pointer document (T133, 2026-09-14).** KHÔNG lặp code/DB. File này ánh xạ đặc tả "System QA & Compliance"
> (spec T117) vào các module **đã tồn tại** của hệ thống. Mọi chi tiết kỹ thuật đọc ở nguồn được trỏ tới đây.

## 1. Phạm vi
Đảm bảo mọi dữ liệu ra người dùng từ Đạo Ảnh là: **trung thực · kế thừa nguồn · minh bạch · tuân thủ pháp lý nguồn · tái lập được**.

## 2. Bảng ánh xạ ĐÃ-CÓ (KHÔNG làm lại)

| Đặc tả | Module tồn tại | Vị trí |
|---|---|---|
| **Compliance Meter** (Claims with Source / Reviewed / Conflict Pool / No-Source-fail / Behavioral-fail) | **T113** — 9 metric read-only | `scripts/verify_design_compliance.py` → `data/design_compliance.json` · route `/daoanh/api/compliance/dashboard?regenerate=1` (app.py:11624) · khối "Data Quality" trong `dashboard/dashboard_process.html` |
| **Test 1 — Cử nhân** (tra cứu cơ bản + nguồn, không log kỹ thuật, chỉ data đã duyệt) | **T126 QA backend** + **T111 persona L1** (clip claims `verified` server-side) | `POST /daoanh/api/daitang/qa` (app.py) · `?level=L1` app.py:14282/14494 |
| **Test 2 — Tiến sĩ / Research** (provenance + audit + trích dẫn chuẩn) | **T118 citation export** (CSL-JSON/BibTeX + `signature=sha256(entity_id\|audit_id\|title)` + audit_id xuyên evidence) | `/daoanh/api/public/export/citation` (app.py:16895) · `entity_claims_audit` 100% phủ |
| **Negative case** (query ngoài phạm vi → trả trung thực, ghi nhận yêu cầu) | **data_gap_requests** (NOT-INDEXED → yêu cầu bổ sung) + trả no_data 200 trung thực | app.py:16474 `OPS_GAP_TABLE` · `POST /api/admin/data-gaps` · QA `no_data` |
| Không dùng AI summary thay thế (luôn retrieval AO) | QA yêu cầu citations/evidence bắt buộc | T126 response contract |
| Fail criteria (No Source / Conflict tự gộp / Unverified hiện L1) | KPI trong Compliance Meter + HITL conflict | claims_with_source=100% goal · conflict_pending HITL · persona clip |

## 3. Đồng hồ KPI (đọc từ design_compliance.json)
- `claims_with_source` goal **100%** (đạt) — không có No-Source.
- `claims_reviewed` / `claims_verified` goal ngưỡng tăng dần (hiện 9.82%).
- `claims_with_audit` goal **100%** (đạt).
- `conflicts_resolved` = Conflict Pool Ratio (0.02%; 99.98% mở — chờ admin, HITL-by-design).
- `glossary_vi_coverage` 75.54% (pass ≥75.5).
- `assertion_level` 0% = fail **HITL-by-design** (Enum do người review điền, bot không tự đặt).

## 4. UAT personas (script)
`scripts/uat_persona_test.py` (T133) — chạy 3 case thật, output `data/uat_report.json` + **exit code**:
1. **Cử nhân**: entity có đủ verified/unverified → assert L1 chỉ trả verified + answer không chứa log kỹ thuật.
2. **Tiến sĩ**: build CSL/BibTeX đúng contract + signature khớp sha256 (HTTP tới :5000 nếu reachable, ngược lại verify cục bộ).
3. **Negative**: token không tồn tại → answer trống trung thực; `data_gap_requests` schema có status `new` (web-layer ghi khi chạy).

## 5. Qui trình thẩm định
1. Dev/Agent chạy `npm run pipeline` (gồm `test:uat` + compliance).
2. Mọi metric fail → dừng, KHÔNG review tiếp.
3. Admin chỉ review khi "ALL TESTS PASSED".

## 6. Trách nhiệm
- Build/QN: AI Engineer · Giá trị/quyết định: Lee Tổng (admin) · Roadmap/kiểm soát tiến độ: TD.
- Siêu dữ liệu task: frontmatter `owner:` trong `tasks/*.md` (dashboard hiện "Người phụ trách").