# TESTER-REPORT-2 — T287 (phạm vi mới, 2026-11-01)

Người kiểm: Tester (Claude Code), chỉ đọc và chạy kiểm tra. Không sửa code/task/status, không ghi DB, không git add/commit.
Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t287\Dai_Tang_Kinh\daoanh`

## Tóm tắt

| # | Mục | Kết quả |
|---|-----|---------|
| 1 | done_when mới: gate trước mọi ghi, nhánh từ chối (exit 2 / SystemExit 2), dry-run không chặn và không ghi audit | PASS (có ghi chú rủi ro, xem mục 1) |
| 2a | ast.parse 2 file | PASS |
| 2b | pytest tests/test_license_firewall.py | PASS: 16 passed, 0 failed |
| 2c | verify_t287.py | PASS (KẾT QUẢ: PASS), dùng DB tạm |
| 2d | verify không chạm data/lineage.db | PASS (file không tồn tại trong worktree, script dùng tempfile) |
| 3 | Phạm vi diff | PASS, có 2 file untracked ngoài phạm vi (xem mục 3) |
| 4 | T510 tồn tại, 3 script + ghi chú etl_t100_batch4 | PASS |
| 5 | Rủi ro fail-open đã biết | Ghi nhận (xem mục 5) |

Kết luận tester: theo done_when mới, T287 đạt về mặt kỹ thuật. Không đánh DONE, Admin xác nhận.

---

## 1. Đọc code gate (2 script)

### 1a. scripts/wire_evidence_into_entity_claims.py

- Các thao tác ghi DB trong `run()` trước gate (dòng 114-285): chỉ SELECT. Không có INSERT/UPDATE/DELETE nào trước dòng 285. Các INSERT duy nhất trong file là ở hàm `_gate_audit_refusal` (dòng 56, ghi en_audit_log, chỉ chạy trong nhánh từ chối).
- Gate nằm ở dòng 285-303: build `gate_plan` từ CBETA/MARCUS/Wikidata, gọi `_gate_check` cho từng nguồn.
- DELETE idempotent (dòng 309-315) đã dời xuống SAU gate, ngay trước INSERT (dòng 319-330). PASS, thứ tự đúng.
- Nhánh từ chối: `_gate_check` raise PermissionError, `run()` bắt, in ABORT, `conn.close()`, `sys.exit(2)` (dòng 300-303). PASS (exit 2).
- Dry-run: `allow_block=DRY_RUN` nên không raise và không gọi `_gate_audit_refusal` (dòng 99-103 của `_gate_check`). PASS.

### 1b. scripts/etl_t109_provenance.py

- Script không INSERT entity_claims (đúng như CODER-REPORT). Nó ghi 2 bảng dẫn xuất: `entity_claims_audit` và `events_provenance`, cùng 2 view.
- `main()` (dòng 419-456): apply mode gọi `make_backup()` (dòng 441-442, chỉ copy file, không ghi DB) rồi `connect()`, sau đó `gate_preflight(conn, dry_run)` (dòng 446) TRƯỚC `build_entity_claims_audit`, `build_events_provenance`, `build_views`. PASS về thứ tự với các CREATE/INSERT.
- `gate_preflight` (dòng 148-168): kiểm DERIVE cho mọi source_id trong entity_claims và DILA. Từ chối => ghi audit qua `_gate_check`, rồi `raise SystemExit(2)` (dòng 168). PASS (SystemExit 2).
- Dry-run: `gate_preflight(conn, dry_run)` truyền `allow_block=True`, không chặn, không ghi audit. PASS (xác nhận bằng test [5] của verify).

### 1c. Ghi chú không chặn (không phải lỗi done_when)

- `--revert` trong t109 (dòng 442-444) KHÔNG đi qua gate, và nó DROP 2 view và 2 bảng dẫn xuất. Done_when không yêu cầu gate cho revert (nó không ghi entity_claims). Ghi nhận để Admin biết.
- `make_backup()` chạy trước gate trong apply mode. Chỉ là copy file vào data/backups, không ghi DB. Không vi phạm "trước khi ghi DB".

---

## 2. Kiểm chứng kỹ thuật

### 2a. ast.parse

Lệnh: `python -c "import ast; [ast.parse(open(f,encoding='utf-8').read(),f) for f in [...]]"`
Output: `AST OK`. PASS.

### 2b. pytest tests/test_license_firewall.py

Lệnh: `python -m pytest tests/test_license_firewall.py -q`
Output rút gọn:
```
................                                                         [100%]
16 passed in 0.71s
```
PASS: 16 passed, 0 failed.

### 2c. verify_t287.py

Lệnh: `python docs/sessions/2026-11-01/T287-coder/verify_t287.py`
Output rút gọn:
```
[temp db] C:\Users\NAMTHI~1\AppData\Local\Temp\t287_7gfle50y.db
[1] CBETA (source_id=3) ACTIVE: [GATE OK] ... PASS CBETA được phép
[2] source_id=99 BLOCKED:
  [ABORT] Không ghi row nào. en_audit_log: đã ghi
  PASS raise PermissionError
  PASS có đúng 1 dòng audit [rows=1]
  PASS action=license_gate_block / entity_ref='source:99' / field_name=entity_claims
  PASS verification_status=blocked / editor=scripts/wire_evidence_into_entity_claims.py
  PASS evidence_sources chứa status BLOCKED
[3] wire dry-run: PASS không thêm dòng audit khi dry-run
[4] etl_t109 gate_preflight, source 99 -> SystemExit(2):
  [ABORT] ... en_audit_log: đã ghi
  PASS raise SystemExit(2) [code=2]
  PASS có thêm 1 dòng audit [1->2]
[5] etl_t109 dry-run: PASS không thêm dòng audit khi dry-run
==== KẾT QUẢ: PASS ====
EXIT=0
```
PASS.

Giới hạn của verify: test [1]-[5] gọi `_gate_check` và `gate_preflight` trực tiếp. KHÔNG chạy `run()` của wire hay `main()` của t109 end-to-end, nên thứ tự gate so với DELETE/INSERT được kiểm bằng đọc code (mục 1), không bằng chạy. Đây là khoảng trống kiểm chứng, không phải lỗi đã biết.

### 2d. verify không chạm data/lineage.db

- Script dùng `tempfile.mkstemp(prefix='t287_', suffix='.db')` (dòng 49), in ra path %TEMP%, mọi kết nối sqlite đi qua path này.
- Kiểm thực tế: `ls data/lineage.db` trong worktree trả về "No such file or directory". Worktree không có data/lineage.db nên verify không thể đụng file này.
- Kết luận: PASS.

---

## 3. Phạm vi diff (git diff HEAD, chỉ đọc)

Lệnh: `git diff HEAD --name-only` (đã chạy trong worktree daoanh):
```
Dai_Tang_Kinh/daoanh/scripts/etl_t109_provenance.py
Dai_Tang_Kinh/daoanh/scripts/wire_evidence_into_entity_claims.py
Dai_Tang_Kinh/daoanh/tasks/T287-m1-noi-gate-etl-con-lai.md
```
Diff stat: 3 file, 272 insertions, 18 deletions.

Trong phạm vi: 2 script, task T287 (đã sửa), tests (không có thay đổi trong diff, chỉ chạy), docs/sessions/2026-11-01/T287-coder/ (untracked, xem dưới).

Untracked (`git status --untracked-files=all`):
```
?? .opencode/agents/coder.md                              <- NGOÀI PHẠM VI T287
?? docs/sessions/2026-11-01/T287-coder/CODER-REPORT.md    <- trong phạm vi
?? docs/sessions/2026-11-01/T287-coder/TESTER-REPORT.md   <- trong phạm vi
?? docs/sessions/2026-11-01/T287-coder/verify_t287.py     <- trong phạm vi
?? tasks/T510-licensegate-3-script-update.md              <- task mới, theo quyết định Admin
```
Ngoài phạm vi cần Admin/coder xác nhận: `.opencode/agents/coder.md` (không liên quan đến 2 script).
Thư mục `docs/sessions/2026-11-01/T287-coder/backup/` có 2 file .bak-before-coder, là backup, không phải thay đổi code.

---

## 4. T510

- File `tasks/T510-licensegate-3-script-update.md` tồn tại (untracked, status pending).
- done_when liệt kê đúng 3 script: `t33_fix_entity_claims_source_id.py`, `t83_bootstrap_review.py`, `build2_add_evidence_provenance_columns.py`. Cả 3 file đều có trong `scripts/` (đã kiểm `ls`).
- Ghi chú `etl_t100_batch4.py` là DDL-only: có trong done_when và mục 2 của T510. Kiểm nhanh header file: mô tả "ADDITIVE: chỉ CREATE TABLE + ALTER TABLE ADD COLUMN". Lưu ý: dòng 19 của header có `--apply` "CREATE + ALTER + seed". Chữ "seed" có thể có INSERT dữ liệu mẫu. Tester không kiểm code sâu (theo chỉ dẫn), nên ghi chú DDL-only chưa được xác minh bằng code. Đề nghị coder/T510 xác nhận.
- Không kiểm code của T510 (theo chỉ dẫn).

---

## 5. Rủi ro fail-open đã biết (ghi nhận, không phải lỗi phạm vi này)

1. Mẫu fail-open (đã ghi trong CODER-REPORT): nếu `from gate.license import LicenseGate` hoặc khởi tạo lỗi, `_gate = None`, script in WARN rồi BỎ QUA gate và vẫn ghi. Áp dụng cho cả wire và t109 (`_gate_check` trả về None khi `_gate is None`). Done_when T287 không yêu cầu fail-closed, nên không tính là FAIL.
2. LEGACY pass-through trong `checkSourcePermission` (gate/license.py): nguồn có `legal_status_at_ingest=LEGACY` luôn được allowed, bất kể legal_status. Đây là chính sách có chủ đích, nhưng nghĩa là gate không chặn các nguồn legacy đã đánh dấu.
3. Lỗi không phải PermissionError trong `checkSourcePermission` (ví dụ DB lock, thiếu bảng data_sources) không bị bắt bởi `except PermissionError`, nên script thoát với traceback (exit 1) trước khi ghi. Đây là fail-closed, không phải fail-open.
4. `--revert` của t109 không có gate (mục 1c).
5. Chưa kiểm end-to-end `run()` của wire với DB thật (khoảng trống kiểm chứng, mục 2c).

---

## Lệnh đã chạy (chỉ đọc hoặc test tạm)

- `git status --short`, `git diff HEAD --stat`, `git diff HEAD -- <2 script>`, `git diff HEAD --name-only`, `git status --short --untracked-files=all`
- `grep`/`sed` đọc 2 script, gate/license.py, etl_t100_batch4.py header
- `python -c "ast.parse ..."`
- `python -m pytest tests/test_license_firewall.py -q`
- `python docs/sessions/2026-11-01/T287-coder/verify_t287.py` (DB tạm)
- `ls data/lineage.db` (không tồn tại)

Không ghi DB thật, không sửa code/task/status, không git add/commit.
