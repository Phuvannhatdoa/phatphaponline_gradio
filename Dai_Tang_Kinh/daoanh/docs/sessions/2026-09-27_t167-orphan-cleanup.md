# Session 2026-09-27 — Dọn 2 file orphan T167 (T177 supersede)

**Task:** Xóa 2 file `docs/Mimo-Flash/T167-directive-v2-trie-xml-dualhash-REVIEW.md` + `T167-dynamic-filter-absorb-directive-v2.md`.
**Admin:** "Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done."

---

## Đối chiếu logic (trước khi xóa)

| Kiểm chứng | Kết quả |
|---|---|
| 2 file T167 trong git history? | KHÔNG — `git log --all` rỗng ⇒ **untracked** từ đầu |
| `admin/app.py` (T167 §1 §5 dùng để audit) | KHÔNG TỒN TẠI — T168 xác nhận auditor nhầm `docs/sessions/2026-09-16/app.py.bak-dila-person-index.py`; stack thật = single `app.py` |
| Stats `translation_rules` | T167 ghi **96/10.529 chars**; thật hôm nay **110/13.230** (terminology 88 · style 10 · forbidden 6 · gate 3 · structure 1 · provenance 1 · grammar 1) |
| `NO_PINYIN`/`HANVIET_NAMES` D6 | T167 ghi "chờ Admin text"; thật: `NO_PINYIN` restored (`is_active=1`), `HANVIET_NAMES` deactivated (`is_active=0`) |
| Log "429 chưa xảy ra" | T167 dựa `app.log`/`translate.log` (0 byte) — 2 file đó KHÔNG tồn tại; log thật `app_local*.log` (T177 đã đính chính) |
| T177 thay thế | Có — 3 commits `62b593b` → `ef4c16d` → `0e5ec12`, status **done**, chứa mọi nội dung sửa/supersede |

**Kết luận:** T167 = snapshot audit cũ (25/09), đã bị T177 thay thế hoàn toàn; giữ = nhầm nguồn + chứa số liệu/stack sai.

## Thực thi

1. `Remove-Item` 2 file orphan (untracked ⇒ xóa không tạo diff git).
2. Verify: không còn file `T167*` trong `docs/Mimo-Flash/`; `grep` tham chiếu thật = 0 (T168:219 dùng backtick text, không gãy hiển thị).
3. Docs: session log này + tasktodo row T177 (append dòng dọn dẹp) + ROLLBACK row mới.
4. Commit **hunk-granular** (cacheinfo + byte-write index/ref, volume-E chặn update-ref): **CHỈ** tasktodo row T177 + ROLLBACK row mới + session file — GIỮ NGUYÊN WIP agent khác trong ROLLBACK (`1be7ed7` T180, `<sha_t166_security>`) dạng unstaged.
   - Commit build: `483561d5450b9524441f2c342342d8ad01d425d0` (parent `6b82ced`; 3 files +36/−1)
   - Commit hash-fill: `9c572b5d7178c049478e324833725a4d1d0b85f5` (thay placeholder cleanup → `483561d` trong tasktodo + ROLLBACK + session)
5. Sync worktree docs về HEAD; **phát hiện & khôi phục**: sync đè file đã xoá 2 WIP row unstaged của agent khác trong ROLLBACK.md → đã tái lập chính xác 2 row `1be7ed7` + `<sha_t166_security>` (worktree trở về `M` đúng như trước).

## Verify

- `git status`: ROLLBACK.md vẫn M (chỉ 2 WIP row agent khác đã khôi phục), tasktodo/session committed sạch, Mimo-Flash không còn T167, chuỗi WIP khác (app.py/tasks/places.html…) nguyên vẹn unstaged.
- `git show --stat 483561d`: 3 files docs, chỉ row của mình.
- **Revert (scratch worktree @ HEAD, T166 pattern):** `git revert --no-edit 9c572b5` EXIT=0 (3 files +5/−5) → `git revert --no-edit 483561d` EXIT=0 (3 files +1/−36, xoá session). Diff tree vs `6b82ced` (pre-cleanup) cho 3 path = **RỖNG** ⇒ khôi phục đúng trạng thái gốc. Đã `worktree remove`.
- **`pipip` (npm run pipeline):** guard PASS · lint PASS · test PASS · t165 11/11 · t166 18/18 · t178 69/69 · t179 49/49 · t167 15/15 + 15/15 · uat 3/3 · compliance 7 pass 2 fail (pre-existing) · gov 17/17 · audit:t166 PASS (0 FAIL, 1 WARN pre-existing Gemini key inline) · e2e PASS · **e2e:runtime EPERM pre-existing** (Volume-E không unlink `test-results\.last-run.json`) — không chặn.

## Revert row

- `git revert --no-edit 9c572b5d7178c049478e324833725a4d1d0b85f5` (hash-fill) rồi `git revert --no-edit 483561d5450b9524441f2c342342d8ad01d425d0` (build) — đã kiểm chứng 2 lần EXIT=0, tree về `6b82ced`.
- 2 file T167 không cần khôi phục (content = T177).