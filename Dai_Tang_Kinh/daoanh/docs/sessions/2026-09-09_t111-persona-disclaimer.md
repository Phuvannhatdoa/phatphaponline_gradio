# Session — T111 Persona Display Layer + ZenQ Disclaimer (DONE)

**Ngày:** 2026-09-09 · **Trạng thái:** DONE (0 DB)

## Mục tiêu (độ lệch #3 SCHEMA_DESIGN — đặc tả T01 "khóa Provenance / mở toàn bộ")
Trưng bày by-persona: L1 Học viên = summary + claims verified + badge nguồn, drawer "đóng";
L2 Cao học = + evidence badges; L3 Nhà nghiên cứu = + provenance đầy đủ + review/conflicts.
API hỗ trợ `?level=L1|L2|L3`; disclaimer ZenQ trên tab trả kết quả giáo lý.

## Việc đã làm (additive, 0 ALTER DB)

### app.py
- Route `/daoanh/api/places/<place_id>/doctrine`: đọc `level=L1|L2|L3` (mặc định L2);
  **L1 → clip `related_claims` nguyên bản theo `verification_status='verified'`** (server-side);
  response thêm `persona_level`.
- Route `/daoanh/api/evidence/<subject_id>`: cùng cơ chế `?level=` cho danh sách `claims`;
  response thêm `persona_level`.

### places.html (Persona Display Layer)
- State `localStorage['da_persona_level']` mặc định **L2** (`_daPersona()`/`_daPersonaSet()`).
- Switcher **L1/L2/L3** trong drawer-head `#lineage-persona` (stopPropagation — không mở/đóng drawer).
- `_daEvidenceDrawer(..., persona)`:
  - **L1**: strip thông báo chế độ + chỉ đếm claims verified + badge nguồn (không assertion/verification
    badges, không 2 select filter assertion/verification, không dòng provenance).
  - **L2**: giữ nguyên hành vi cũ (badges + 3 filter + source code).
  - **L3**: dòng provenance bổ sung `claim_id · source_reference · conf=.. · verification_status`.
- `_daFilterEvidence`/`_daEvRows`: persona-aware (L1 luôn ép bộ lọc verified).
- `_daRenderDoctrine`: fetch `?level=<persona>`; empty-state L1 trung thực
  ("chưa có claim verified trong entity_claims — toàn kho vẫn 100% unverified").
- Disclaimer ZenQ `_daZenqDisclaimer()` trên tab Giáo Lý (`#da-zq-disclaimer`):
  nhãn trình độ + "tham khảo học thuật · không phải tư vấn pháp lý/hướng dẫn tu hành cá nhân"
  + nút "Đổi trình độ →".
- Đổi persona → re-render drawer + giáo lý ngay từ cache (`window._daCurrentSubjectId/_daCurrentPlaceId`).

### Route kèm theo (phục vụ T113m)
- `/daoanh/api/compliance/dashboard` (mirror progress/dashboard, `?regenerate=1`) — để
  `dashboard_process.html` mục Data Quality đọc `design_compliance.json`.

## Kiểm chứng
- `npm run pipeline` PASSED (lint ✅ test ✅ e2e ✅; e2e:runtime EPERM pre-existing).
- `node --check` trên block script chính places.html (424,867 chars) → OK.
- L1 ep server-side: doctrine/evidence trả ít claims hơn khi `?level=L1` (verified=0 hiện tại
  → trả rỗng + UI nói trung thực) — đúng contract, không sai data.

## Ghi chú chuyển giao
- Trong lúc review rate còn 0%, L1 sẽ "trống" nhiều — đây là hành vi đúng (honest UI).
- Revert: `git revert --no-edit 39d5fd57` (code, gồm cả route compliance) + `0cb62fc7` (docs).