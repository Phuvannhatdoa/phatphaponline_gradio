# CONFLICT_ENGINE_SPEC.md — Bộ máy Xử lý xung đột (Lineage Consensus Engine)

> **Conformance-pointer document (T136, 2026-09-14).** KHÔNG lặp code/DB. File này ánh xạ đặc tả
> "Task T115: Lineage Consensus Engine" (body ghi "Task T109") vào các module **đã tồn tại** của hệ thống = **board T109
> (Provenance & Conflict Workflow, DONE) + fix T134 + mở rộng T136**.
> Lưu ý số board: T115 = Source Authority Matrix (DONE); đặc tả này thực chất = T109.
> Mọi chi tiết kỹ thuật đọc ở nguồn được trỏ tới đây.

## 1. Mục tiêu (khớp đặc tả)
Human-in-the-loop (HITL): hệ thống **tuyệt đối không tự xóa/gộp dữ liệu mâu thuẫn** — mọi phán quyết do Admin (Lee Tổng).
Quy trình bắt buộc: **[Phát hiện] → [Trình Admin] → [Phê duyệt] → [Ghi log & cập nhật]**.

## 2. Bảng ánh xạ ĐÃ-CÓ (KHÔNG làm lại)

| Đặc tả | Module tồn tại | Vị trí (verified 2026-09-14) |
|---|---|---|
| **Detection** — phát hiện 2 nguồn cùng Identity khác thuộc tính | Batch ETL so sánh DILA↔Marcus **tập thầy/trò** (`deep_conflict_analysis.py`) → 40,327 rows. **Phạm vi hiện tại:** lineage teacher_set/student_set. Conflict thuộc tính chung (ngày sinh/nơi sinh…) = `conflict_pending` — **0 rows, thuộc T132 (chờ)** | `src_python/db/deep_conflict_analysis.py` (INSERT L141) |
| **Flagging** — record vào `lineage_conflicts_v2`, KHÔNG xuất hiện cho Tăng Ni Sinh/Cử nhân, chỉ Admin | ✓ conflict pool chỉ phục vụ **admin** (`admin/conflicts.html` + endpoint `/daoanh/api/admin/lineage-conflicts`). Hiển thị người dùng **show+mark** (chip `is_conflict=1 AND resolved=0`, `_t86_person_conflict`) — **deviation có chủ đích: minh bạch thay vì ẩn** (xem §4) | app.py L10573 / L5065 (+ app.py L5050 chip) |
| **Comparative UI** — song song Nguồn A/B + Authority Score + Lịch sử "ai đưa vào" | `admin/conflicts.html` song song DILA↔MARCUS (count + **Authority Score badge DILA 100 / MARCUS 60 từ `source_authority`** — T136) + `last_verdict/last_editor/last_reviewed_at`; lịch sử DETECTION = `created_at` (batch) | `admin/conflicts.html` · `GET /daoanh/api/admin/lineage-conflicts` |
| **Resolution — chọn 1 giá trị / gộp / bác bỏ cả hai** | `POST .../lineage-conflicts/<id>/resolve` — **T136 mở rộng `resolution_type ∈ pick\|merge\|reject`** + `winner_source_id` (pick:dila\|marcus · merge:both · reject:none); ghi `en_audit_log` (editor·created_at·reason·evidence·authority_rank) | app.py `admin_lineage_conflict_resolve` |
| **Audit Trail** — ai · lúc nào · lý do, không bao giờ xóa | `en_audit_log` append-only (action=`resolve_lineage_conflict`/`claim_review`/`review`…) + `audit_id` SHA-256 (`entity_claims_audit`) + endpoint public L3 `GET /daoanh/api/research/entity/<id>/audit-trail` | app.py (ghi L10635+) · T135 |
| **`resolutions_log`** | ⚠️ **Bảng mồ côi: 0 INSERT trên toàn repo** (T134 phát hiện). Dữ liệu phán quyết THẬT nằm ở `en_audit_log`. `GET /daoanh/api/admin/resolutions/history` đã fix UNION 2 nguồn (T134) → timeline đầy đủ. **Spec điều chỉnh: "ghi vào resolutions_log" = ghi `en_audit_log`** | app.py `api_admin_resolutions_history` |
| **Data Lock** | Deviation có chủ đích: conflict **HIỆN + flagged** (không ẩn). `v_assertions` (T109 adapter view) không lọc conflict. → record tránh thông tin sai = chip cảnh báo + verification_status, KHÔNG biến mất khỏi tìm kiếm | `scripts/etl_t109_provenance.py` (v_assertions) |

## 3. Qui trình HITL (khớp đặc tả)
1. **Phát hiện** — batch ETL so sánh DILA↔Marcus (lineage). (Thuộc tính chung → T132.)
2. **Trình Admin** — pool `lineage_conflicts_v2` hiển thị song song: giá trị 2 nguồn + Authority Score (T136) + dấu vết review cũ.
3. **Phê duyệt** — Admin chọn: **✓ Dùng DILA / ✓ Dùng Marcus** (pick) · **⟷ Giữ cả hai** (merge) · **✗ Bác bỏ cả hai** (reject) — kèm lý do tùy chọn.
4. **Ghi log & cập nhật** — `resolved=1` + notes tag convention (`T109 winner=…` / `T136 merge: giu ca hai` / `T136 reject: bac bo ca hai`) + **1 dòng `en_audit_log`** (ai/lúc nào/lý do/nguồn bằng chứng). Nguồn gốc bất biến; KHÔNG xóa lịch sử.

## 4. Điều chỉnh quy chiếu (ghi rõ cho ClaudeCode/Admin)
- **`resolutions_log` → `en_audit_log`**: bảng resolutions_log không bao giờ được ghi (0 INSERT); T134 đã sửa timeline UNION để THỎA yêu cầu "không bao giờ xóa lịch sử". Không tạo writes mới vào resolutions_log.
- **Sanction "Canonical" ngôn từ**: đặc tả dùng "CoreClaim"; hệ thống dùng `verification_status ∈ verified/unverified/disputed/needs_review` — "Canonical" không tồn tại, đảm bảo không auto-canonical.
- **Data Lock**: giữ **show+mark** (minh bạch — đã phê chuẩn). Không chuyển sang ẩn.
- **Detection scope**: lineage chỉ; conflict thuộc tính chung giao **T132** (seed `conflict_pending`) — KHÔNG làm trùng trong T136.

## 5. Bảng thẩm định (dành cho Lee Tổng) — cách verify từng dòng
| Tiêu chí | Cách verify |
|---|---|
| **Minh bạch** | `admin/conflicts.html` hiển thị đủ: giá trị 2 nguồn (count) + **Authority Score badge** + last verdict/editor/time; resolve → dòng `en_audit_log` |
| **Kiểm soát (HITL)** | Không có code tự resolve; mọi nút gọi endpoint POST admin; `is_conflict=1 AND resolved=0` chỉ hiển thị chứ không tự đổi |
| **An toàn** | `dila_data/marcus_data` bất biến; 0 ALTER; `resolved=1` + audit append-only; parametrized SQL |
| **Thuận tiện** | 1 trang gộp pool; 4 nút phán quyết (pick/merge/reject) 1 chạm; lý do prompt trên card |
| **Trung thực (negative)** | Chuỗi không có conflict → "Không có conflict nào"; entity không có audit → `data_status:no_data` (T135) |

## 6. Non-goals (boundary)
- KHÔNG tạo `PROJECT_STATUS.md` (SSOT: tasktodo + dashboard). KHÔNG seed conflict thuộc tính chung (T132). KHÔNG chuyển Data Lock sang ẩn. KHÔNG ghi `resolutions_log` (bảng mồ côi giữ nguyên; timeline đã UNION). KHÔNG xóa lịch sử phán quyết.

## 7. Trách nhiệm
- Build/QA: AI Engineer · Phán quyết HITL: **Lee Tổng (admin)** · Roadmap/kiểm soát tiến độ: TD.