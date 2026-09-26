# CURATION_WORKFLOW_SPEC.md — Curation & Editor Workflow (Đạo Ảnh)

> **Conformance-pointer document (T134, 2026-09-14).** KHÔNG lặp code/DB. File này ánh xạ đặc tả "T116 Curation & Editor Workflow"
> (ZenQ naming — số trùng board T116 = System Registry) vào các module **đã tồn tại** của hệ thống = **T109 + T119**.
> Mọi chi tiết kỹ thuật đọc ở nguồn được trỏ tới đây.

## 1. Phạm vi
Curation = hàng chờ dữ liệu tranh chấp/chưa thẩm định → người biên tập (Human-In-The-Loop) **review → phán quyết → ghi sổ versioning**.
Không có auto-canonical: mọi thay đổi trạng thái đi qua admin, từng bước được ghi `en_audit_log`.

## 2. Bảng ánh xạ ĐÃ-CÓ (KHÔNG làm lại)

| Đặc tả | Module tồn tại | Vị trí |
|---|---|---|
| **Editor Dashboard** (1 cửa sổ hàng chờ tổng hợp) | **T119** — `admin/editor-dashboard.html` (7 tab: Claims / Feedback / Data Gaps / Resolutions / Audit Trail / Geo / Bio) + stats | app.py `GET /daoanh/api/admin/editor-stats` (L16848+) |
| **Dispute UI** (2 nguồn đối chiếu) | **T109** — `admin/conflicts.html` (so sánh DILA ↔ MARCUS side-by-side) | `GET /daoanh/api/admin/lineage-conflicts` (app.py L10572) · `POST .../<id>/resolve` (L10615) |
| **Conflict Pool** (hàng chờ tranh chấp) | `lineage_conflicts_v2` **40,327 rows (40,321 mở)** · `conflict_pending` (pool generic T68-format, T132 sẽ seed) | DB `data/lineage.db` | 
| **Audit Log / Versioning** (ai · lúc nào · lý do · nguồn bằng chứng) | `en_audit_log` (9,000+ rows từ T83; action=`resolve_lineage_conflict`/`claim_review`) + `entity_claims_audit` (447,885 audit_id SHA-256) | app.py L2048/8929/10643/16723 … |
| **Bulk Action** (duyệt hàng loạt nguồn tin cậy cao) | **T119** — `POST /daoanh/api/admin/claims/bulk-review` (≤500, 1 audit row/claim) | app.py L16687 |
| **Hàng chờ claims chưa thẩm định** | `GET /daoanh/api/admin/entity-claims/unverified` (447,885 unverified, pagination, `?status=`) | app.py L16650 |
| **Resolutions timeline** (lịch sử phán quyết) | **fix T134 2026-09-14** — UNION `en_audit_log(action='resolve_lineage_conflict')` + `resolutions_log` (cũ đọc bảng mồ côi → luôn trống) | `GET /daoanh/api/admin/resolutions/history` (app.py L16742) |
| **Phản hồi / lỗi người dùng** | `user_feedback` (inbox editor-dashboard) · `data_gap_requests` (NOT-INDEXED) | app.py L16475 / L16474 |
| **Trạng thái claim** | `verification_status ∈ verified / unverified / disputed / needs_review` — **KHÔNG có "Canonical"**; không auto-canonical | schema `entity_claims` |

## 3. Qui trình HITL 3 bước (Review → Acceptance → Commit)
1. **Review** — admin mở `admin/editor-dashboard.html` hoặc `admin/conflicts.html`, xem đối chiếu nguồn (DILA/MARCUS/CBETA) + dấu vết cũ.
2. **Acceptance** — phán quyết ở mức claim: `verified` (dùng được) · `disputed` (nghi vấn) · `needs_review` (đợi thêm nguồn); ở mức conflict: chọn `winner_source_id ∈ dila|marcus`.
3. **Commit** — endpoint ghi ngay **1 dòng `en_audit_log`** (entity_ref · action · old_value ([VERNEL]→new · evidence_sources · authority_rank · editor · verification_status · created_at). KHÔNG ALTER bảng base; dữ liệu nguồn bất biến.

Thuật ngữ spec "Canonical/Draft" = `verified` / `unverified|needs_review|disputed`. "No auto-Canonical" = **granted**: không code tự chuyển trạng thái hàng loạt (ngoài T83 bootstrap đã **được admin phê chuẩn trước**).

## 4. Self-check (thang điểm 4 trục) — cách verify từng dòng
| Trục | Yêu cầu | Verify |
|---|---|---|
| **Minh bạch** | Mọi phán quyết có ai/lúc nào/lý do/nguồn | `SELECT entity_ref,editor,created_at,evidence_sources FROM en_audit_log WHERE action='resolve_lineage_conflict'` → 5 mẫu T134; tab Resolutions hiển thị |
| **Kiểm soát** | HITL chỉ có người phê duyệt; không auto-quyết | Không có code `UPDATE ... verification_status` ngoài endpoint admin + T83 (đã duyệt); `conflicts.html` không có nút tự resolve |
| **An toàn** | Source data bất biến; 0 ALTER; Zero-RAM | `dila_data/marcus_data` không bị ghi bởi resolve (chỉ `resolved=1`+audit); `SCHEMA_FREEZE.md`; query phân trang |
| **Thuận tiện** | 1 cửa sổ hàng chờ + bulk cho nguồn tin cậy | `editor-dashboard.html` gộp claims/conflicts/bio/feedback/gap; `bulk-review` ≤500, editor chọn |

## 5. Đồng hồ (đọc từ DB/API)
- `lineage_conflicts_v2`: open 40,321 → 40,316 (sau 5 resolve mẫu T134) — tỉ lệ resolve nhích ~0.012%.
- `claims verified`: 44,000 → 44,015 (T134: 5 high + 10 medium).
- `resolutions/history`: tổng = COUNT(en_audit_log resolve) + COUNT(resolutions_log).

## 6. Trách nhiệm
- Build/QA: AI Engineer · Giá trị/phán quyết HITL: **Lee Tổng (admin)** · Roadmap/kiểm soát tiến độ: TD.

## 7. Non-goals (boundary)
- KHÔNG tạo `PROJECT_STATUS.md` (SSOT: tasktodo + roadmap + dashboard). KHÔNG build UI curation mới. KHÔNG seed `conflict_pending` (thuộc T132). KHÔNG xoá/đổi history cũ.