# Session — Rà đặc tả "T117 Doctrine Retrieval Engine" (GHI NHẬN + TẠO T118)

**Ngày:** 2026-09-09 · **Commit:** `ffebe24`

## Bối cảnh
Lee gửi đặc tả có tiêu đề **"Task T117: Doctrine Retrieval Engine"** (mô tả "Bộ máy Truy vấn Giáo lý").
Đề cập nội dung nhầm số: ghi **"ĐẶC TẢ KHÁI NIỆM T115"** và **"Task T115"**; yêu cầu tạo
`RETRIEVAL_ENGINE_SPEC.md` và update `PROJECT_STATUS.md`.

## Kết luận rà đặc tả (read-only, verified)
**"Doctrine Retrieval Engine" = chính hệ T100 (doctrine_concept) + T111 (Persona Display + ZenQ
Disclaimer) + T113 (QA live 2026-09-09).** Governance đã ghi rõ trong `docs/roadmap.md`:
`T06 → T100 + T111`.

### Phủ 100% (verified)
| Đặc tả | Hiện trạng |
|---|---|
| Policy Filter 3 tầng (L1/L2/L3) | `?level=L1/L2/L3` trên doctrine + evidence (T111) |
| Evidence Drawer luôn kèm | tab Bằng chứng & nguồn dẫn |
| No Evidence = No Answer (trung thực) | `data_status` API + empty-state tiếng Việt |
| Disclaimer động | `_daZenqDisclaimer()` |
| Review Status bậc Tiến sĩ | `verification_status` + `reviewed_by/at` |

### 3 delta ghi nhận (không phải lỗi hồi quy)
1. **Bậc Tiến sĩ — Audit Trail API CHƯA CÓ**: `en_audit_log` + `entity_claims_audit.audit_id` tồn
   tại nhưng admin-only; evidence response chưa kèm `audit_id`. → **Task T118 (Track 2, pending).**
2. **"Persona tự nhận diện" ≠ switcher tường minh L1/L2/L3** (quyết định T111, giữ nguyên).
3. **Q&A tự do** thuộc **T11 (RAG Vi chat, pending)**, không trộn vào doctrine.

### Cam kết tránh lặp
- KHÔNG tạo `docs/RETRIEVAL_ENGINE_SPEC.md` (trùng SCHEMA_DESIGN M2/M6 + T111).
- KHÔNG re-open T111/T115; KHÔNG update `PROJECT_STATUS.md` (SSOT = tasktodo/roadmap).
- Đặc tả được ghi nhận bằng `[ráspec 2026-09-09]` + tạo task mới **T118** (đúng tiền lệ).

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T111-persona-display-disclaimer.md` — mục "Rà đặc tả ... — XÁC NHẬN ĐÃ PHỦ + 3 delta".
2. `tasks/T118-research-audit-tier-api.md` — task mới (pending, Track 2).
3. `docs/ROADMAP_META_UPDATE.md` §5 — thêm 2 Meta-luật (chống tạo SPEC trùng; T118 deferred).
4. `docs/tasktodo.md` — `[ráspec 2026-09-09]` ở T111 + dòng T117/T118.
5. `docs/roadmap.md` — 2 bảng + rows T117/T118.
6. `docs/ROLLBACK.md` — row `ffebe24`.
7. Session này.

## Rollback
- `git revert --no-edit ffebe24` (docs-only, 0 DB).