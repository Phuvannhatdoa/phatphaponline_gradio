# T73 + T74 — Fix task file metadata (id front-matter, NUL byte, prefix)

**Ngày:** 2026-08-30
**Build:** TGS Build 2 — Phase 0 (trước Phase A defect-fix)
**Trạng thái:** ✅ DONE (scanner verified)

## Vấn đề (kế thừa từ commit `1963f41`)
Hai task file được commit với metadata sai so với đúng task ID, khiến
`scripts/build_progress_data.py` (đọc front-matter `id`) mis-parse thành T67/T68
→ sinh trùng lặp trong `progress_data.json`; T74 còn chứa NUL byte thật → git
commit dưới dạng binary.

| File | Lỗi cũ | Đã sửa thành |
|------|--------|--------------|
| `tasks/T73-admin-review-bio-vi-draft.md` | `id: T67`, `# T67` | `id: T73`, `# T73` |
| `tasks/T74-place-desc-vi-gemini-translate.md` | `id: T68`, `# T68`, NUL byte thật, prefix `t68_*` | `id: T74`, `# T74`, NUL→`\x00` (text), prefix `t74_*` |

## Việc đã làm
- **T73:** `id:T67→T73`, heading `#T73`, tham chiếu internal `T68(pending)`→`T73 (--copy-approved step)`.
- **T74:** viết lại qua Python (decode utf-8 → thay NUL byte thật bằng chuỗi `\x00` →
  thay prefix `t68_*`→`t74_*`, `data/t68_translate_log`→`t74_translate_log`, `id:T68`→`T74`, `#T68`→`#T74`).
  File giờ là text thuần (3401 bytes, không còn NUL). Sửa tham chiếu `T67 (pending)`→`T73`.
- **`docs/tasktodo.md`:** thêm mục ### T73 và ### T74 (cả hai pending).
- **Không đụng** các file T22* (founding-dates, VPS sync) — nằm ngoài scope Phase 0.

## Kết quả (verified)
- Scanner test: `T73 → id=T73 heading=T73`; `T74 → id=T74 heading=T74` (id == heading, hết trùng).
- `git check-attr text`: T74 giờ là text (trước là binary `Bin 0 -> 3398`).

## Reversible
- Revert commit Phase 0 trả nguyên các file cũ (git revert/reset). Không ảnh hưởng DB.
