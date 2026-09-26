---
id: T113
title: "QA/UAT + Compliance Meter — live :5000, Data Quality Report"
module: QA / Testing
priority: high
depends_on: [T108]
created: 2026-09-08
updated: 2026-09-09
status: in_progress
done_when: >
  Server :5000 được restart & live-verify Batch 4 (T100) + case đặc biệt; script
  scripts/verify_design_compliance.py (read-only) sinh data/design_compliance.json
  (9 metrics SCHEMA_DESIGN M7.2) hiển thị Dashboard; alert #4/#5 có trạng thái
  đóng/mở cập nhật; Data Quality Report ghi docs.
---

# T113 — QA/UAT + Compliance Meter

## Mục tiêu
1. **QA live** (điều kiện tiên quyết: :5000 được restart — đang blocked bởi port chiếm):
   verify Batch 4, case Thiếu Lâm Tự (PL000000023255), evidence drawer, doctrine tab.
2. **Compliance meter**: `scripts/verify_design_compliance.py` (read-only, Zero-RAM,
   generator) → `data/design_compliance.json` cho Dashboard — 9 metrics M7.2.
3. **Đóng alert** #4 (entity_claims 100% unverified) / #5 (events 100% candidate) khi đủ điều kiện.

## Phạm vi
- QA code batch trước đó + báo cáo `docs/*QA*.md`.
- Script tính metric (KHÔNG sửa data).

## Acceptance
- Live test PASS (hoặc block rõ ràng kèm clip/evidence).
- `design_compliance.json` có 9 metrics + so sánh baseline 2026-09-08.
- `npm run pipeline` PASS.

## Tiến độ (2026-09-09)
- ✅ **Phần B — Compliance Meter DONE** (commit `1a51a356` code + `0ebffc29` docs):
  `scripts/verify_design_compliance.py` (read-only, Zero-RAM, generator/COUNT aggregate)
  sinh `data/design_compliance.json` (**9 metric M7.2** — gồm đủ bảng, script đo bằng COUNT
  không duyệt hàng; thực tế hiện tại: 5 pass ✅ / 1 warn (conflicts 0.01% bootstrap) / 3 fail
  (reviewed, verified, assertion_level) — đúng hiện trạng) + dashboard `dashboard_process.html`
  mục **Data Quality** (gọi `/daoanh/api/compliance/dashboard` — route app.py ở `39d5fd57`).
  **Pipeline PASSED** (lint/test/e2e).
- ✅ **Phần A — QA live :5000 PASS 2026-09-09** (restart thành công, PID 12592 — log sạch):
  | Probe | Kết quả |
  |---|---|
  | `GET /daoanh/api/places/PL000000023255` (Thiếu Lâm Tự) | 200 · 27 trường (name_vi/name_zh, DILA, confidence, founding_year…) |
  | `?level=L1/L2/L3` | 200 · cùng 27 keys — lock hiển thị ở tầng UI (đúng contract T111) |
  | `GET /daoanh/api/evidence/PL000000023255` (evidence drawer) | 200 · claims=**38** (mẫu DILA · confidence 0.8) · co_mentions=34 · events=1 · resolved=2 |
  | `GET /daoanh/api/places/PL000000023255/doctrine` (doctrine tab) | 200 · concepts=**12** (Tứ Diệu Đế + definition_vi + pth_uri + related_entities) |
  | `GET /daoanh/api/places/PL000000023255/cbeta` | 200 · passages **少林寺** (T50n2060 唐高僧傳·釋玄奘傳 · `T50n2060_p0457c16`) · fosizhi=10 · related_texts=3 |
  | `GET /daoanh/api/lineage-ref/passage?ref=T50n2060_p0457c16` (Batch 4) | **200 · found · passage_id=3918 · loc_ref `0-0425b-` resolve OK** |
  | `GET /daoanh/api/compliance/dashboard` | 200 · **read_only=True** · 9 metric (5 pass/3 fail/1 warn) · 132 bảng |
  - Quan sát (không FAIL): vài claim DILA có `assertion_level: null` — T108 cho phép; ghi bin data-quality nếu Lee chốt ngưỡng M4.
- ⏳ **Đóng alert #4/#5** (`tab_readiness.json`) —— cần admin review rate qua `admin/conflicts.html`;
  metrics phản ánh trung thực → T113 giữ **in_progress**.

## Rà đặc tả T113 (2026-09-09) — đối chiếu + quyết định

Lee đưa "Đặc tả khái niệm T113" (bản đính kèm). Rà soát theo thực trạng hệ thống — phê chuẩn:

| # | Điểm đặc tả | Kết luận | Quyết định |
|---|---|---|---|
| A1 | "Cập nhật Task T113 thành Doing trong `docs/PROJECT_STATUS.md`" | `PROJECT_STATUS.md` **KHÔNG tồn tại**; repo dùng SSOT = tasktodo/progress/roadmap/dashboard | KHÔNG tạo file; ghi trạng thái vào đây + `docs/tasktodo.md` + `docs/roadmap.md` |
| A2 | "Khởi tạo `/docs/QA_COMPLIANCE_SPEC.md`" | Metric/công thức/hiện trạng **đã là SSOT** ở `SCHEMA_DESIGN.md` M7.2 | KHÔNG tạo file trùng; viện dẫn M7.2 (task này là spec-holder) |
| A3 | "Tự gắn cờ đỏ (Flagged) khi source NULL / confidence thấp" | Meter = **read-only COUNT aggregate (Zero-RAM)**; `no_source` = 0 row (claims_with_source 100%); `low_confidence` chưa có ngưỡng (M4) | Giữ meter aggregate; flag chi tiết → **task riêng** (bảng dẫn xuất additive `claims_qa_flags`) sau khi chốt cutoff M4 |
| A4 | "Validation khớp Unified Assertion Schema (T108)" | 9 metric M7.2 đo gián tiếp (source/confidence/reviewed/verified/audit/events/provenance) | Không metric mới; M7.2 = lớp validation |
| A5 | "UAT 3 persona (Cử nhân/Cao học/Tiến sĩ)" | Phần hiển thị **đã xong ở T111** (`?level=L1/L2/L3`); DEMO live = Phần A T113 | Chờ :5000 (blocked); offline QA = e2e sẵn có |
| A6 | "7 metrics" trong đặc tả/file | Script thật có **9 metrics** M7.2 | Đã sửa 7→9 (file này) |
| — | Phạm vi "tự động gắn cờ" đọc Database | Giữ nguyên **read-only** (không UPDATE/ALTER) | Không đổi |

**Tổng:** đặc tả khái niệm T113 ≡ M7.2 — mọi cấu phần "Compliance Metering" đã code xong (Phần B);
phần còn sót = Phần A (QA live :5000) + luồng admin review (đóng alert #4/#5). 0 code mới trong mục này.

## Rà đặc tả "System QA & Compliance UAT" (2026-09-09) — ĐÃ PHỦ + 2 delta

Lee gửi đặc tả (header đề **"Task T119"**, mô tả "System QA & Compliance"; body ghi **"ĐẶC TẢ KHÁI
NIỆM T117"** và lệnh gọi **"Task T117"**; bảng STATUS đề **T116=Curation Done → nhầm**: T116 = System
Registry docs-only, Curation = T109/T119). Chủ sở hữu thật = **task này (T113)**. Đối chiếu read-only:

| Đặc tả | Hiện trạng (verified) |
|---|---|
| Bộ công cụ `scripts/verify_design_compliance.py` → `data/design_compliance.json` | ✅ **EXISTS** (Phần B, `read_only=True`, 2026-09-09) |
| 3 KPI (claims with source / reviewed / conflict pool) | ✅ phủ & hơn: **9 metrics M7.2** — `claims_with_source` 100% pass · `claims_reviewed` **0%** (fail thật) · `conflicts_resolved` 0.01% warn · `with_audit` 100% · `events_provenance` 100% · `glossary_vi` 75.54% |
| Dashboard KPI | ✅ `dashboard_process.html` mục Data Quality (9 metric + goal + baseline) |
| UAT 3 persona (Tứ Diệu Đế / Tiến sĩ / Negative) | ✅ Phần A QA live 7 probe: doctrine 12 concepts + L1/L2/L3 + evidence L3 provenance + negative case (honest Việt "Chưa có dữ liệu…") |
| Citation BibTeX | ✅ `places.html` `dtCopyCite('bibtex')` → `@incollection{...}` + 'chicago' |
| Failure criteria (No Source / tự gộp conflict / Unverified→L1) | ✅ kiến trúc ép buộc (claim_id làm assertion ref; conflict admin-only; L1 clips verified=0 → honest empty) |
| Update `PROJECT_STATUS.md` → T117 Doing | ❌ không tồn tại; SSOT = tasktodo/roadmap (bỏ) |

### 2 delta (không phải lỗi — là thiếu export chuẩn, thuộc T118 Track 2)
1. **CSL-JSON citation export: KHÔNG tồn tại** (0 khắp repo). BibTeX hiện tối giản (ref_code →
   `@incollection` không full metadata). → bổ sung vào **T118** (Research Audit Tier, deliverable export).
2. **Audit ID trong provenance/export public**: đã ghi nhận (T117 rà → T118), evidence chưa kèm
   `audit_id` → "trọn vẹn Provenance + Audit ID để tái lập" chờ T118.

**Cam kết:** KHÔNG tạo `QA_COMPLIANCE_SPEC.md` (A2 có sẵn) · KHÔNG re-open (task này đang in_progress;
đóng khi alert #4/#5) · không tạo task mới (delta nằm trong T118).

## R? ??c t? nh?m "T119 Production Deployment" (r?spec6 2026-09-09)
??c t? DEPLOYMENT_SPEC ghi maintenance b?ng `verify_design_compliance.py` **"(T117)"** ? SAI:
ch? s? h?u script = **task n?y (T113)** (Ph?n B). Th?m **ops cadence**: ch?y th?ng/qu?, ghi
k?t qu? v?o `docs/OPS_LOG.md` do T116 D-Ops ch? tr?.


## Batch A ? Lee review (2026-09-10)
- Lee ph? duy?t Batch ?? xu?t (g?m QA shutdown path). Nh?n x?t: claims metric s? t?ng d?n qua
  T119 bulk-review (batch) ch? kh?ng auto; gi? 3 metric t?nh theo verification_status=verified.
- Task GI? **in_progress** ? ??ng khi alert #4/#5 x? l? xong (claims_reviewed > 0 qua UI T119,
  + nh?n x?t conflicts m? #40321). KH?NG t? ??ng ?? tr?nh ??nh l??ng sai QA.
