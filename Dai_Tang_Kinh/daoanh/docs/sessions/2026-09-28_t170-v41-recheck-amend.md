# Session 2026-09-28 — T170 AMEND re-check sau T169-BUILD (docs-only)

**Task:** `tasks/T170-dila-place-person-v41-amend.md` · **SPEC:** `docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md` · **pointer:** `docs/Mimo-Flash/T170-dila-place-person-v41-verify.md`

## Bối cảnh

Admin yêu cầu "check và xác nhận vấn đề sau đúng logic chưa" (claim cụ thể bị cắt). Tôi tự rà 2 file
T170 (viết 2026-09-25) so với hiện trạng T169 **ĐÃ BUILD** (`393676f` + `4c8228b`, 2026-09-28) qua
DB thật read-only + code T169 committed. Kết luận: **premise "T169 docs-only / 0 file tồn tại / build
mới từ zero" = SAI**. Admin xác nhận đúng vấn đề (đáp án: "Đúng — premise build mới sai") rồi duyệt
"Đồng ý build... Gọi pipip khi done".

## Verification read-only đã chạy (DB thật `data/lineage.db` + code)

- `place_groq_audit` **tồn tại** (13 cột, 0 rows, idx_pga_review/idx_pga_diff) — T169 migrate `--apply`.
- `person_groq_audit` / `dila_places` / `dila_persons` **KHÔNG tồn tại**.
- `people` = 48.673 · id `A000001…A049062` TEXT · 0 NULL · `name_zh`/`name_vi` đủ · `people_full` = 0.
- `places_dila` = 59.167 · 0 bảng có cột `trans_dict_vi` · `journal_mode=wal` · `busy_timeout` đo thật = **5000** (Python sqlite3 default `timeout=5.0`, không phải 0).
- `scripts/t169_classify.py:22` **đã có** `'行':['hành','hạnh','hàng']` · `:104-107` đã dùng `r_d != r_g and (r_d or r_g)` word-token (== R1 core) · taxonomy word-boundary không nest.
- `scripts/verify_dila_places_groq.py`: batch 25 · `:cursor` · resume · RPM adaptive · atomic · json_object fallback (:298) · `max_tokens=512` · set WAL lại :75 (vi phạm R5 cũ). KHÔNG có busy_timeout / R6 flat-JSON / R7 truncation salvage.
- `tests/test_t169_classify_diff.py` 11/11 PASS · app.py GET/PUT `place-groq-review` + `admin/place_update.html` đã build.

## Kết quả — bảng đối chiếu S1–S10 (ghi thẳng vào SPEC)

| # | T170 cũ | Thực tế | Sửa tại chỗ |
|---|---------|---------|-------------|
| S1 | P0-5 "0 file tồn tại → Build mới" | script+tests đã có/commit | REFACTOR/EXTEND |
| S2 | "Migrate 2 side-car" | place đã apply T169 | chỉ tạo `person_groq_audit`, giữ place (guard không DROP) |
| S3 | §6 tests "build mới" | base `test_t169_classify_diff.py` tồn tại | giữ base + thêm case mới (import module T169) |
| S4 | §7 API/UI place "theo T169 §6–§7" | đã build | phase 5 = đối chiếu enum mở rộng |
| S5 | §10 "T169 chưa build → không block" | T169 đã build | "đã build 2026-09-28, T170 absorb" |
| S6 | §3.1 #8 place thiếu `行` | `t169_classify.py:22` có sẵn | [absorbed T169] DONE |
| S7 | §3bis R1 "vẫn len>=1" | T169 dùng `r_d≠r_g` word-token | core absorbed; chỉ thêm test regression |
| S8 | R5 "busy_timeout default 0" | đo thật 5000 (Python) · T169 script set WAL lại :75 | set 10000 + bỏ WAL pragma ở refactor |
| S9 | §5 "build mới" (bỏ sót code T169) | T169 đã có batch/cursor/atomic/json fallback/mock | giữ + thêm R2/R3/R4/R6/R7 + `--entity person` |
| S10 | enum mở rộng §3.4 | API/UI T169 filter 4 status cũ + sort CASE | rà GET filter + UI tabs khi mở rộng enum |

**Kết quả chung:** số liệu nền của T170 (people 48.673 · id zero-pad · 0 NULL · people_full 0 ·
places_dila 59.167 · wal) **ĐÚNG**; chỉ các phát biểu về "T169 còn docs-only/build mới" là lỗi thời.

## Việc đã làm (docs-only)

1. **SPEC T170** — sửa tại chỗ: frontmatter `updated: 2026-09-28` + `done_when` (migrate person-only, R2–R8, giữ R1/P1-8 absorbed); banner `[2026-09-28 · T169-BUILD re-check]` (S1–S10); §2 P0-5 → REFACTOR/EXTEND; §3.1 #1/#2 note absorbed + #8 `行` DONE; §3bis header R1 note + row 3.1 (busy_timeout 5000) + R5 (phải xóa WAL pragma T169:75); §4 migrate **person-only** + guard place không DROP + revert chỉ person; §5 retitle REFACTOR/EXTEND + bảng "giữ/+thêm" (max_tokens 2048–4096, R6/R7); §6 note base test T169; §7 note place đã build; §9 Phase 1 person-only + Phase 5 đối chiếu + Revert person/place tách; §10 "T169 đã build → T170 absorb"; §11 Files (Mới/Refactor/Không đụng + `place_groq_audit` T169).
2. **Pointer T170** — `updated: 2026-09-28` + bullet re-check S1–S10 + revert person.
3. Task `tasks/T170-dila-place-person-v41-amend.md` (mới) + session này.

## Còn lại

- Không gồm trong amend này: build code T170 thật (migrate person, `--entity person`, R2/R3/R4/R6/R7, enum API/UI) — task `T170-dila-place-person-v41-verify` chờ ("ready-for-dev").
- Lưu ý build sau: KHÔNG DROP `place_groq_audit` (T169) · bỏ `PRAGMA journal_mode=WAL` đang set trong verify script · `max_tokens` 512→2048–4096 · enum mới phải map GET sort CASE + UI tabs.

## Revert

- `git revert --no-edit 61b1c0afe2637d2467525745c86dfea5cb0f1843` (docs-only — khôi phục SPEC/pointer cũ + docs; 0 code/0 DB).