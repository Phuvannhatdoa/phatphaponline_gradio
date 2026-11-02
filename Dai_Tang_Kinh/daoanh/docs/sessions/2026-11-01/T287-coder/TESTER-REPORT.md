# TESTER-REPORT — T287 (M1: nối LicenseGate vào script ghi entity_claims)

Ngày: 2026-11-01 · Người kiểm: Tester (Claude Code, chỉ đọc + chạy kiểm tra)
Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t287\Dai_Tang_Kinh\daoanh`
Không sửa code/task/status, không ghi DB, không commit. Không đánh DONE (Admin xác nhận).

## Tóm tắt

| # | Mục kiểm | Kết quả |
|---|----------|---------|
| 1 | Phạm vi diff | PASS (có ghi chú) |
| 2 | Gate trước DELETE/INSERT trong wire_evidence | PASS (đọc code; chưa chạy run() thật) |
| 3 | etl_t109: gate trước tạo bảng/backfill, audit, dry-run | PASS |
| 4 | ast.parse, pytest, verify_t287 | PASS (16 passed; verify PASS, DB tạm) |
| 5 | Fail-open khi import gate lỗi | Rủi ro đã biết, xác nhận đúng như coder ghi |
| 6 | done_when: mọi script ghi entity_claims gọi gate | FAIL (4 script ghi entity_claims chưa có gate) |

Kết luận: phần code của 2 script đạt yêu cầu scope T287. Tuy nhiên done_when rộng hơn scope "2 script": còn script khác ghi `entity_claims` mà chưa gọi gate. Cần Admin/MA quyết định mở rộng scope hoặc tách task.

---

## 1. Phạm vi diff — PASS (ghi chú)

Lệnh: `git status --short` và `git diff HEAD --stat`

```
 M scripts/etl_t109_provenance.py
 M scripts/wire_evidence_into_entity_claims.py
 M tasks/T287-m1-noi-gate-etl-con-lai.md
?? .opencode/agents/coder.md
?? docs/sessions/2026-11-01/
 3 files changed, 270 insertions(+), 17 deletions(-)
```

- Thay đổi code nằm đúng 2 script. Task file được sửa (outcome/frontmatter).
- Ghi chú: có `.opencode/agents/coder.md` (untracked) và `docs/sessions/2026-11-01/` ngoài phạm vi 2 script + thư mục T287-coder. Đây là file không theo git, không thuộc diff của T287. Cần Admin xác nhận có nên đưa vào commit hay không.
- Không có thay đổi schema (không có lệnh ALTER/CREATE mới trong script wire; etl_t109 chỉ thêm gate, các CREATE đã có từ trước).

## 2. Thứ tự trong wire_evidence_into_entity_claims.py — PASS (đọc code)

Vị trí dòng (từ `grep -n`):
- Dòng 114 `def run():`. Từ dòng 114 đến 274 chỉ có SELECT (không có INSERT/UPDATE/DELETE/COMMIT trước khối gate).
- Dòng 275 `# INSERT` (phần ghi dữ liệu bắt đầu sau khối tính toán claims).
- Dòng 287-303: khối `gate_plan` + `_gate_check(...)` cho CBETA/MARCUS/Wikidata. Nếu bị từ chối: `PermissionError` -> `sys.exit(2)` tại dòng 303.
- Dòng 306-315: `if DRY_RUN ... else:` chứa khối DELETE idempotent (dòng 309-315). DELETE chỉ chạy khi nhánh `else` được thực thi.
- Dòng 319-338: INSERT OR IGNORE vào entity_claims và entity_source_ids.

Kết luận: gate chạy trước DELETE/INSERT. Khi gate từ chối, `sys.exit(2)` dừng trước khi tới khối DELETE, nên không xoá dữ liệu T69 cũ.

Hạn chế: `verify_t287.py` chỉ kiểm `_gate_check` và `gate_preflight`, không chạy `run()` đầy đủ (cần schema entity_hub, cbeta, marcus... nên không dựng được DB tạm đơn giản). Vì vậy mục này dựa trên đọc code, không có chạy thực tế end-to-end.

## 3. etl_t109_provenance.py — PASS

Vị trí dòng trong `main()`:
```
conn = connect()                # chỉ sqlite3.connect, không DDL
try:
    if revert_mode: revert(...)
    else:
        gate_preflight(conn, dry_run)        # dòng 446
        build_entity_claims_audit(conn, ...) # CREATE TABLE tại dòng 241
        build_events_provenance(conn, ...)   # CREATE TABLE tại dòng 319
        build_views(conn, ...)
```
- `gate_preflight` nằm trước mọi CREATE TABLE/backfill. Đúng yêu cầu.
- Nhánh từ chối (không dry-run): `_gate_audit_refusal` ghi 1 dòng `en_audit_log` (action=license_gate_block, verification_status=blocked), sau đó `raise SystemExit(2)`. Đã kiểm chứng ở verify mục [4].
- `--dry-run`: `allow_block=True`, không ghi audit (`written = False`), chỉ in `[GATE BLOCK — dry-run]`, không exit. Đã kiểm chứng ở verify mục [5].

Ghi chú (không chặn PASS):
- Trong nhánh apply, `make_backup()` (dòng ~437) chạy trước `gate_preflight`. Đây là copy file sang `data/backups`, không ghi DB. Nếu gate từ chối thì vẫn còn file backup thừa. Ít rủi ro, nhưng nên ghi nhận.
- `--revert` không đi qua gate. Revert chỉ DROP view/bảng dẫn xuất, không ghi dữ liệu base. Chấp nhận được.

## 4. Kiểm chứng kỹ thuật — PASS

**4a. ast.parse** (`python -X utf8 -c "import ast..."`):
```
AST OK scripts/wire_evidence_into_entity_claims.py
AST OK scripts/etl_t109_provenance.py
exit=0
```

**4b. pytest** (`python -m pytest tests/test_license_firewall.py -q`):
```
................                                                         [100%]
16 passed in 0.46s
```

**4c. verify_t287.py** (`python -X utf8 docs/sessions/2026-11-01/T287-coder/verify_t287.py`):
- DB: `tempfile.mkstemp` (file tạm trong %TEMP%, `t287_*.db`), không đụng `data/lineage.db`. Script xoá DB tạm khi xong.
- Script nạp đúng 2 file thật bằng `importlib` và gọi `_gate_check` / `gate_preflight`.
- Kết quả rút gọn:
```
[1] CBETA được phép ........................... PASS
[2] raise PermissionError ..................... PASS
    có đúng 1 dòng audit [rows=1] ............. PASS
    action/entity_ref/field_name/verification_status/editor ... PASS (5 mục)
[3] dry-run không thêm dòng audit ............. PASS
[4] raise SystemExit(2) [code=2] .............. PASS
    có thêm 1 dòng audit [1->2] ............... PASS
    audit target=entity_claims_audit,events_provenance ........ PASS
[5] dry-run không thêm dòng audit ............. PASS
==== KẾT QUẢ: PASS ====   (exit=0)
```
- Lưu ý: `verify_t287.py` không dùng DB thật, đáp ứng yêu cầu.

## 5. Fail-open khi import gate lỗi — Rủi ro đã biết (xác nhận đúng mô tả của coder)

Đã đọc code:
- `scripts/etl_entity_claims.py` dòng 25-29: `except ImportError:` -> `_gate = None`. `_gate_check` (dòng 32-35) khi `_gate is None` chỉ in `[WARN]` và return, không chặn.
- `scripts/wire_evidence_into_entity_claims.py` dòng 36-39: `except Exception` -> `_gate = None` + WARN. `_gate_check` trả về `None` khi `_gate is None` (fail-open).
- `scripts/etl_t109_provenance.py`: cùng mẫu fail-open.

Đánh giá:
- Đây là đúng mẫu coder đã ghi, không phải lỗi mới của T287. Task không yêu cầu fail-closed nên không tính là FAIL T287.
- Rủi ro thực tế thấp (constructor `LicenseGate(db_path)` chỉ lưu đường dẫn, không mở DB), nhưng nếu module `gate/license.py` bị xoá hoặc lỗi import thì script vẫn chạy và ghi dữ liệu không qua gate.
- Ghi chú: khi `checkSourcePermission` ném exception trong lúc chạy (ví dụ DB bị khoá, bảng data_sources thiếu), wire và t109 không bắt exception đó và script dừng. Đây là fail-closed, không fail-open.
- Khác mẫu: `etl_entity_claims.py` khi từ chối chỉ raise PermissionError, không ghi en_audit_log. Chỉ T287 (wire, t109) có nhánh audit. Không đồng nhất.

## 6. done_when: "Mọi script ghi entity_claims gọi LicenseGate trước khi ghi" — FAIL

Phương pháp: `Grep "entity_claims"` trong `scripts/` (21 file), sau đó `Grep` các câu lệnh INTO/UPDATE/DELETE/executemany liên quan đến `entity_claims`, và `Grep` tìm `LicenseGate|checkSourcePermission|_gate_check`.

Script có gate (5 file gọi LicenseGate/_gate_check; một số không ghi entity_claims):
- `scripts/etl_entity_claims.py` — CÓ gate. Mỗi phase gọi `_gate_check` trước INSERT: phase_coordinate (dòng 110 -> INSERT 113), phase_names (132-133 -> INSERT 137, 152), phase_admin_unit (171 -> INSERT 174). Đạt yêu cầu về thứ tự.
- `scripts/wire_evidence_into_entity_claims.py` — CÓ gate (T287).
- `scripts/etl_t109_provenance.py` — CÓ gate (T287), ghi bảng dẫn xuất (entity_claims_audit, events_provenance), không INSERT vào entity_claims.
- `scripts/build3_license_firewall.py`, `scripts/t278_make_backlog_tasks.py`: chỉ đề cập LicenseGate/gate, không ghi entity_claims (t278 chỉ là chuỗi text).

Script GHI entity_claims nhưng CHƯA có gate:

| Script | Thao tác ghi entity_claims | Có gate? |
|--------|---------------------------|----------|
| `scripts/t33_fix_entity_claims_source_id.py` | `UPDATE entity_claims SET source_id=...` (dòng 44, 53) | KHÔNG |
| `scripts/t83_bootstrap_review.py` | `UPDATE entity_claims SET verification_status='verified', reviewed_by, reviewed_at` (dòng 140), và revert (dòng 180-181) | KHÔNG |
| `scripts/build2_add_evidence_provenance_columns.py` | `UPDATE entity_claims SET source_url=...` (dòng 67, 81), `UPDATE ... SET retrieved_at` (dòng 120) | KHÔNG |
| `scripts/etl_t100_batch4.py` | `ALTER TABLE entity_claims ADD COLUMN assertion_level/reviewed_by/reviewed_at` (dòng 211, DDL, không ghi row) và `--revert` có `DROP COLUMN` (dòng 239) | KHÔNG (chỉ đổi schema) |

Ghi chú về các file còn lại có nhắc đến entity_claims nhưng chỉ đọc (không ghi): `t455_apply_planA.py`, `t455_claims_and_lotA.py`, `t455_claim_probe.py`, `t418_import_claude_xml.py`, `t24_zqlocal_content_migration.py`, `qa_data_integrity.py`, `verify_design_compliance.py`, `uat_persona_test.py`, `todo_audit.py`, `t82_checksum.py`, `t39_spatial_join.py`, `build_tab_readiness.py`, `build_t132_p1_db_additive.py`. Các file này không có câu lệnh INSERT/UPDATE/DELETE vào `entity_claims` theo kết quả grep. Chưa đọc hết từng file, nên đánh giá là "không thấy lệnh ghi".

**Kết luận done_when: FAIL.** T287 chỉ nối gate cho 2 script (theo phạm vi task "2 script còn lại"), nhưng done_when yêu cầu MỌI script ghi entity_claims. Có 3 script UPDATE (t33, t83, build2) và 1 script ALTER (t100_batch4) chưa có gate. Đây là quyết định phạm vi cho Admin/MA:
- Phương án A: mở rộng T287 để thêm gate cho t33, t83, build2 (các script UPDATE entity_claims).
- Phương án B: giữ scope 2 script, sửa done_when thành "2 script INSERT entity_claims", và mở task riêng cho các script UPDATE.
- Lưu ý: t33 và t83 là script đã/đang dùng một lần cho sửa lỗi dữ liệu; cần kiểm tra có còn được chạy không trước khi quyết định.

## Rủi ro/ghi chú bổ sung (không phải FAIL)

1. Chưa có kiểm chứng end-to-end của `run()` trong wire (mục 2 dựa trên đọc code).
2. `etl_entity_claims.py` không ghi en_audit_log khi từ chối; chỉ T287 có nhánh audit. Không đồng nhất giữa các script.
3. `make_backup()` trong t109 chạy trước gate, có thể để lại file backup khi gate từ chối.
4. Không kiểm DB thật (không có `data/lineage.db` trong worktree; và theo quy định không chạy ETL thật).

## Không làm

- Không sửa code/task/status; không ghi DB; không commit/add.
- Không đánh DONE. Quyết định DONE thuộc Admin.
