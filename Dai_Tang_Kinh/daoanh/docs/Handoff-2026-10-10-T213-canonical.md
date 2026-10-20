# Handoff 2026-10-10 — T213 classification + canonical_decision A003636

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-10 |
| HEAD (trước commit) | `f0d58d3a83502d8b8642c22c44bdc4197be0eadd` · commit session này: `b3bc2b0fc5ebf31b8958a76d973a9e35c375c1c5` |
| Session đã làm | `docs/sessions/2026-10-10_T213-classification-canonical.md` |
| Task | `tasks/T213-vnpa-orphan-211-classification.md` (status→done) + pack §7 item 1 |
| Trạng thái test | `audit:honesty:strict` PASS 7/7 (từ session trước). Lint/test/e2e chưa chạy lại. |
| Preflight | SSOT toplevel = `visjs-app`; **shared `.git/index` stale** (mtime 2026-10-06, 90 `D`+30 `M`+1 `A` giả) → commit qua temp-index |
| DB | **Có mutation** — canonical_decision A003636 (1 row INSERT additive). T213 READ-ONLY (0 mutation). |
| TTL | Không đụng TTL |

## 2. Đọc trong 2 phút

- **Đã làm:** (1) Thêm `canonical_decision` cho A003636 (Phước Châu Đại An canonical, Phúc Châu Đại An biến thể). (2) Classify 211 VNPA orphans → A=186, B=6, C=11, D=8. (3) Cập nhật task T213 status=done.
- **Phát hiện quan trọng:** Shared `.git/index` **stale 4 ngày** (mtime 2026-10-06), chứa 90 `D` + 30 `M` + 1 `A` giả so với HEAD. ACL Windows chặn ghi `.git/` → **không thể sửa shared index**. Tất cả commit **BẮT BUỘC** qua temp-index (GIT_INDEX_FILE ở %TEMP%).
- **3 việc Admin cần biết:** (a) canonical_decision A003636 đã ghi; (b) T213 classification hoàn tất (report + evidence); (c) shared index stale — session sau PHẢI dùng temp-index.

## 3. Đề xuất chữa dựng

| Việc | Cách làm | Bằng chứng | Kết quả |
|---|---|---|---|
| canonical_decision A003636 | INSERT 1 row (admin_approved/verified) | `canonical_decision` 4 rows | 4/4 verified |
| T213 classification | READ-ONLY scan + rule-based bucketing | `%TEMP%\opencode\t213_classification_20261010.json` | 211 rows classified, 0 review needed |

## 4. Cảnh báo bắt buộc

- **Shared `.git/index` STALE** — mtime 2026-10-06 17:04. `git read-tree HEAD` fail (`fatal: unable to write new index file` — ACL `Users` thiếu DELETE). **KHÔNG sửa được**. Commit qua temp-index:
  ```bash
  GIT_INDEX_FILE=%TEMP%\wt_<name> git read-tree HEAD
  git add -- <files>  # each file
  git write-tree; git commit-tree -p HEAD -m "msg"
  git update-ref refs/heads/master <new> <old>  # CAS
  ```
- `git status`/`git diff`/`git add` thư mục **sẽ fail/sai** (88 false `D`). Dùng `git rev-parse HEAD:<path>` vs `git hash-object <path>`.
- `npm`/`node`/`rg` = shim 0-byte → `cmd /c "npm run ..."` hoặc python.
- `data/*.json` ignored → `git add -f data/progress_data.json`.

## 5. Lệnh revert

| Phần | Lệnh | Mất dữ liệu? |
|---|---|---|
| Docs + code | `git revert --no-edit b3bc2b0fc5ebf31b8958a76d973a9e35c375c1c5` | **0** |
| DB canonical_decision A003636 | `DELETE FROM canonical_decision WHERE entity_ref='A003636'` | **0** (additive) |
| DB T213 | (READ-ONLY, 0 mutation) | **0** |

## 6. Bảng file tạo/sửa

| File | Loại |
|---|---|
| `docs/reports/T213-classification-report-20261010.md` | report (mới) |
| `tasks/T213-vnpa-orphan-211-classification.md` | task (updated status=done) |
| `docs/tasktodo.md` | block T213 (mới) |
| `docs/ROLLBACK.md` | row T213 (mới) |
| `docs/sessions/2026-10-10_T213-classification-canonical.md` | session (này) |
| `docs/Handoff-2026-10-10-T213-canonical.md` | Handoff (này) |
| `data/progress_data.json` | regen dashboard |

## 7. Sai lầm / bài học

- **Shared index stale 4 ngày** — không nhận ra ngay, đã thử `git read-tree` trên shared index và fail. Lesson: luôn kiểm tra `.git/index` mtime trước khi tin `git status`.
- T213 task gốc ghi "211 row `dila_id=''`" — thực tế 210 `''` + 1 `NULL`. Đã sửa trong task + report.

## 8. Việc CHƯA xong

1. **Bucket B (6 Indian Patriarchs)** — task riêng link DILA IDs (cần DILA evidence).
2. **Bucket C (11 Non-monk)** — Admin decide keep/tag/separate table.
3. **Bucket D (8 Mythological)** — tag `is_mythological` / move to reference table.
4. Shared index stale — cần Admin quyết định có bỏ qua hay không (hiện tại workaround bằng temp-index).

## 9. Lệnh kiểm tra nhanh (1 phút)

```bash
cd .../daoanh
# canonical_decision
sqlite3 data/lineage.db "SELECT entity_ref,canonical_name_vi,verification_status FROM canonical_decision WHERE entity_ref='A003636';"
# T213 counts
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);print('dila_id=\"\":',c.execute(\"SELECT COUNT(*) FROM vn_person_authority WHERE dila_id=''\").fetchone()[0]);print('NULL:',c.execute('SELECT COUNT(*) FROM vn_person_authority WHERE dila_id IS NULL').fetchone()[0])"
# audit
python -X utf8 scripts/audit_data_honesty.py --strict
# HEAD
git rev-parse HEAD
```

## 10. Ghi chú cho agent kế tiếp

1. Đọc session + Handoff này + `docs/reports/T213-classification-report-20261010.md`.
2. **BẮT BUỘC** temp-index cho commit tiếp theo (shared index stale).
3. T213 classification evidence ở `%TEMP%\opencode\t213_classification_20261010.json`.
4. Bucket B/C/D next steps cần Admin duyệt trước khi làm task mới.