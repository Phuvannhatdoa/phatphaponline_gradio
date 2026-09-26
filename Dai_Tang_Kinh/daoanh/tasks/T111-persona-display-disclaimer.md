---
id: T111
title: "Persona Display Layer (lock/mở Provenance) + ZenQ Disclaimer"
module: UI/UX / Evidence Presentation
priority: medium
depends_on: [T108, T100]
created: 2026-09-08
updated: 2026-09-09
status: done
done_when: >
  Trưng bày by-persona theo contract SCHEMA_DESIGN: Cử nhân (L1) = summary +
  claims đã verified, drawer đóng; Cao học (L2) = + evidence badges; Tiến sĩ (L3) =
  + provenance đầy đủ + review status + conflicts. API hỗ trợ ?level=L1|L2|L3.
  Disclaimer pháp lý ZenQ hiển thị trên các tab trả kết quả giáo lý.
---

# T111 — Persona Display Layer + ZenQ Disclaimer

## Mục tiêu (gap thật #3 của SCHEMA_DESIGN — đặc tả T01: "khóa Provenance / mở toàn bộ")
Hiện tại: scoring 3 cấp độ (Cử nhân 6 / Cao học 9 / Tiến sĩ 12) **đã có** (T100),
evidence drawer **luôn mở** — chưa có tầng trưng bày thay đổi theo persona.

## Contract (đã định nghĩa trong SCHEMA_DESIGN M2/M6 — triển khai code ở đây)
| Persona | Hiển thị |
|---|---|
| L1 Cử nhân | summary + claims verified; drawer đóng (chỉ badge nguồn) |
| L2 Cao học | + evidence badges (DILA/CBETA/MARCUS) |
| L3 Tiến sĩ | + provenance đầy đủ + verification_status + conflicts |

- API: `?level=L1|L2|L3` trả field khác nhau (không đổi data).
- Disclaimer pháp lý ZenQ (rõ nguồn/giấy phép/không phải tư vấn) trên tab trả giáo lý.

## Acceptance
- Chuyển persona đổi UI thật (không chỉ ẩn hiện class).
- Disclaimer xuất hiện đúng chỗ, không cản thao tác.
- `npm run pipeline` PASS.

## Tiến độ (2026-09-09) — DONE (commit `39d5fd57` code + `0cb62fc7` docs)
- **API `?level=L1|L2|L3`** (app.py, 2 endpoint): `/daoanh/api/places/<id>/doctrine`
  + `/daoanh/api/evidence/<subject_id>` — L1 server-side clip claims về
  `verification_status='verified'` + echo `persona_level`; 0 đổi data.
- **places.html tầng Persona Display Layer:**
  - State `localStorage['da_persona_level']` (mặc định L2) + switcher **L1/L2/L3** ngay
    trong drawer-head "Bằng chứng & nguồn dẫn".
  - **L1 Học viên** (drawer "đóng"): chỉ badge nguồn (không assertion/verification badges,
    không filter selects, không provenance); claims lọc verified; empty-state trung thực
    ("chưa có claim verified — toàn kho vẫn 100% unverified").
  - **L2 Cao học** (mặc định): + evidence badges (assertion_level + verification) + filter.
  - **L3 Nhà nghiên cứu**: + dòng provenance đầy đủ (claim_id · source_reference ·
    conf · verification_status).
  - **Disclaimer ZenQ** `_daZenqDisclaimer()` trên tab Giáo Lý (không cản thao tác):
    nhãn trình độ + "tham khảo học thuật · không tư vấn pháp lý/hướng dẫn tu hành"
    + nút đổi trình độ.
  - Đổi persona re-render ngay (drawer + giáo lý) từ cache.
- **Pipeline PASSED** (lint/test/e2e; e2e:runtime EPERM pre-existing — không hồi quy phần UI).

## Rà đặc tả "T117 Doctrine Retrieval Engine" (2026-09-09) — XÁC NHẬN ĐÃ PHỦ + 3 delta

Lee gửi đặc tả (header tự đề **"Task T117"**, mô tả lại hệ "Bộ máy Truy vấn Giáo lý" — cũng gọi nhầm
"T115"; chủ sở hữu thật = **T06 → T100 + T111 + T113**, đã DONE, QA live 9/9). "Doctrine Retrieval
Engine" = chính task này + `doctrine_concept` (T100) + tab Giáo Lý/evidence ở places.html.

Đối chiếu read-only (DB + app.py + places.html + API thật) — **phủ hầu hết**:

| Đặc tả | Thực trạng (verified) |
|---|---|
| Policy Filter 3 tầng (Cử nhân/Cao học/Tiến sĩ) | ✅ `?level=L1/L2/L3` trên `/places/<id>/doctrine` + `/evidence/<subject_id>`; L1 server-clip claims verified |
| Evidence Drawer luôn kèm, không giấu nguồn | ✅ tab Bằng chứng & nguồn dẫn (claims/passages/badges/co_mentions) |
| No Evidence = No Answer; trung thực ngoài ngữ liệu | ✅ `data_status` API + empty-state tiếng Việt ("Chưa có dữ liệu… trong phạm vi đã index", "Chưa có trích dẫn kinh điển xác nhận…", 404 untraced) — ngữ nghĩa NOT INDEXED/NO DATA, render tiếng Việt |
| Disclaimer động | ✅ `_daZenqDisclaimer()` tab Giáo Lý |
| Review Status bậc Tiến sĩ | ✅ claim `verification_status` + `reviewed_by/reviewed_at` trong provenance |

### 3 delta (chưa có / lệch — ghi nhận, KHÔNG phải lỗi)
1. **Bậc Tiến sĩ — public "Audit Trail" API KHÔNG CÓ.** `en_audit_log` (lịch sử thay đổi) +
   `entity_claims_audit.audit_id` (SHA-256) tồn tại nhưng **admin-only**; evidence response không
   kèm `audit_id`. → **Track 2 = task T118** (Research Audit Tier API, additive read-only), chờ duyệt.
2. **"Persona tự nhận diện người dùng" (đặc tả) ≠ triển khai hiện tại** = switcher tường minh
   L1/L2/L3 + mặc định L2 (quyết định có chủ đích). Đặc tả còn tự mâu thuẫn ("tự nhận diện" nhưng
   "không để người cấu hình"). Giữ nguyên switcher (rõ, trung thực).
3. **"Người dùng đặt câu hỏi" (Q&A tự do) — KHÔNG nằm ở hệ này.** Hệ = truy vấn có cấu trúc bám
   thực thể. Q&A văn bản tự do thuộc **T11 (RAG Vi chat, pending)** — không trộn vào doctrine.

### Cam kết
- **KHÔNG tạo** `docs/RETRIEVAL_ENGINE_SPEC.md` (trùng SCHEMA_DESIGN M2/M6 + task này + UX thật —
  theo pattern T109/KHÔNG tạo file đặc tả trùng).
- **KHÔNG re-open** T111/T115/T117; **KHÔNG** update `PROJECT_STATUS.md` (SSOT = tasktodo/roadmap).
- Status đặc tả ghi vào tasktodo/roadmap dòng này + dòng T118 (pending, Track 2).