# Handoff 2026-10-10 — T271 follow-up: Lô C (era) + Lô Ca (strip) + regex W1a + fix H1

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-10 |
| HEAD (trước commit) | `9cb1e7ffaa04ff5ce60c95ca9e859eb49be3107a` (T275 bước 2) · commit session này: `25a79d2fdbb8d62cec8a5d0552d0ce22555123eb` |
| Session đã làm | `docs/sessions/2026-10-10_T271-lot-CCa-h1.md` |
| Task | `tasks/T271-t202-post-review-revision.md` (follow-up §6) |
| Trạng thái test | `audit:honesty:strict` **PASS 7/7** (H1..H7 = 0). Lint/test/e2e chưa chạy lại trong session này (chỉ sửa docs + regex audit). |
| Preflight | SSOT toplevel = `visjs-app`; không `git init` trong daoanh; **index `.git/index` hỏng** (mất ~88 entry) → commit qua temp-index |
| DB | **Có mutation** — Lô C (17 era) + Lô Ca (596 label) + H1 (357 evidence). Backup đầy đủ cả 2 lô |
| TTL | Không đụng TTL |

## 2. Đọc trong 2 phút

- **Đã làm:** Admin "Đồng ý build" → ghi Lô C (17 era) + Lô Ca (strip 596 `(N年建)`) + nới regex W1a
  (đọc số Ả Rập) + fix H1 (357 evidence). `audit:honesty:strict` từ FAIL → **PASS 7/7**.
- **Phát hiện quan trọng nhất:** **H1=357 là pre-existing** — cũng có trong backup
  `lineage.T273-review-20261010_184054.db` (18:40, TRƯỚC khi apply Lô C/Ca). Gốc: T44-fix đổi
  `event_type` `founding`→khác và T44-102 thêm event nhưng không tạo `event_evidence` tương ứng.
- **3 việc Admin cần làm ngay:** (a) duyệt commit này (code + docs, 0 DB trong git); (b) quyết
  `canonical_decision` cho `phuoc_chau_dai_an` (A003636) + task `T213` (211 orphan) — **đang hoãn**;
  (c) lưu ý **index git hỏng 88 entry** (xem §4) — nên để session khác biết trước khi commit.

## 3. Đề xuất chữa dựng cho từng hạng mục

| Hạng mục | Vấn đề | Cách sửa | Bằng chứng | Kết quả đo |
|---|---|---|---|---|
| Lô C (H3 nhóm 1) | 16 niên hiệu thiếu trong `time_periods` | INSERT additive `source_origin='era_catalog'` | audit H3 | H3 nhóm 1 = 0 |
| Lô Ca (H4) | `label_zh` có nhãn bịa `(N年建)` | UPDATE strip 596 row | audit H4 | H4 = 0 |
| Regex W1a (H3 nhóm 2) | 6 row ghi năm bằng chữ số Ả Rập | `cn2int`/`era_year_in_text`/`era_year_exact` nhận `[0-9]` | audit H3 | H3 = 0 |
| H1 | 357 event lệch `event_type`↔evidence | INSERT additive `event_evidence` | audit H1 | H1 = 0 |

## 4. Cảnh báo bắt buộc

- **Index git hỏng:** `git diff --cached --name-status` báo **88 `D`** + 30 `M` + 1 `A` nhưng các file
  đó **VẪN tồn tại trên disk**. `git ls-files -s <path>` rỗng; `git cat-file -t :<path>` →
  `fatal: path '<path>' exists on disk, but not in the index`. ⇒ **KHÔNG commit từ shared index**
  (sẽ xóa nhầm 88 file thật). Chỉ commit qua temp-index `read-tree HEAD` + plumbing + CAS (AGENTS §14/§17).
- `git status`/`git diff` trên máy này **không đáng tin** (exit lạ, false "D"). Dùng
  `git rev-parse HEAD:<path>` vs `git hash-object <path>` để so worktree↔HEAD.
- Git **không rename được** file trong `.git/` (ACL `Users` không có DELETE) → dùng
  `GIT_INDEX_FILE` ở `%TEMP%` (rename được) hoặc ghi ref trực tiếp.
- `npm`/`node`/`rg` có thể là shim 0-byte → wrap `cmd /c "..."` hoặc gọi python.
- `data/*.json` bị `.gitignore` → regen dashboard phải `git add -f`.
- Session song song (T273/T274/T275) đang chạy — luôn dựng file chung từ HEAD, không lấy worktree.

## 5. Lệnh revert

| Phần | Lệnh | Mất dữ liệu? |
|---|---|---|
| Docs + code | `git revert --no-edit 25a79d2fdbb8d62cec8a5d0552d0ce22555123eb` | **0** (0 DB trong git) |
| DB Lô C | `DELETE FROM time_periods WHERE source_origin='era_catalog'` (17 row) | **0** (additive) |
| DB Lô Ca | restore `label_zh`/`year` từ `data/backups/2026-10-10-lot-C-Ca/backup_lotCCA_20261010_184438.sql` | 0 (label gốc còn trong backup) |
| DB H1 | chạy `data/backups/2026-10-10-H1-evidence/h1_revert.sql` (DELETE 357 id 4972–5328) hoặc restore `.db` | **0** (additive) |

## 6. Bảng file tạo/sửa (session này)

| File | Loại |
|---|---|
| `scripts/audit_data_honesty.py` | nới regex W1a |
| `docs/plans/2026-10-10-analysis-pack-t271-followups.md` | cập nhật C/Ca APPLIED + H1 |
| `docs/sessions/2026-10-10_T271-lot-CCa-h1.md` | session (mới) |
| `docs/tasktodo.md` | follow-up line T271 |
| `docs/ROLLBACK.md` | row C/Ca + H1 |
| `tasks/T271-t202-post-review-revision.md` | §6 follow-up |
| `docs/Handoff-2026-10-10-lot-CCa-h1.md` | Handoff (này) |

## 7. Sai lầm tự mình / bài học

- Ban đầu lọc Lô Ca bằng `LIKE '%年建%'` → **match nhầm note-text** "N年建…" (không phải nhãn `(N年建)`);
  sửa lại dùng đúng pattern regex `[（(]\s*\d{1,4}\s*年建\s*[)）]` (như H4). Còn 17 row `年建` là note-text
  hợp lệ, không phải lỗi.
- `apply_h1_evidence.py --no-backup` in nhầm file `.wal` cho "backup" khi in log — nhưng backup `.db`
  thật đã tồn tại (`lineage.H1-20261010_195950.db`). Không ảnh hưởng kết quả.
- Lần đầu chạy `apply_h1_evidence.py` timeout 120s ở bước backup (1633MB) → backup xong nhưng script bị kill;
  chạy lại với `--no-backup` reuse backup đã có.

## 8. Việc CHƯA xong (theo ưu tiên — chờ Admin)

1. **`canonical_decision` A003636** `phuoc_chau_dai_an` — ghi tường minh canonical vs biến thể (Admin hoãn).
2. **`T213`** — READ-ONLY classification 210 `''` + 1 NULL orphan vào bucket A–D (Admin hoãn).
3. Báo `pipip` sau commit.

## 9. Lệnh kiểm tra nhanh (1 phút)

```bash
cd .../daoanh
python -X utf8 scripts/audit_data_honesty.py --strict           # PASS 7/7
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);print(c.execute(\"SELECT COUNT(*) FROM time_periods WHERE source_origin='era_catalog'\").fetchone())"  # (17,)
git log --oneline -3
git rev-parse HEAD:<path>   # so với git hash-object <path> khi index nghi hỏng
```

## 10. Ghi chú cho agent kế tiếp

1. Đọc session + Handoff này + `docs/plans/2026-10-10-analysis-pack-t271-followups.md`.
2. Commit tiếp theo: **BẮT BUỘC** temp-index từ HEAD (index hỏng 88 entry) — `git add` thuần sẽ
   ghi sai (xóa file thật). Xem AGENTS §14/§17.
3. `audit:honesty:strict` nay PASS — có thể dùng làm gate.
4. Đóng task chỉ khi Admin xác nhận commit + quyết §8.
