# CODER REPORT — T287

- **Task:** `tasks/T287-m1-noi-gate-etl-con-lai.md` — M1 Nối LicenseGate vào 2 script ghi entity_claims còn lại
- **Ngày:** 2026-11-01
- **Trạng thái:** `coding` → `testing` (chờ tester; Admin chưa xác nhận DONE)
- **Worktree:** `C:\Users\Nam Thien\.claude\worktrees\coder-t287\Dai_Tang_Kinh\daoanh`

## 1. File đã đổi

| File | Thay đổi |
|---|---|
| `scripts/wire_evidence_into_entity_claims.py` | Thêm LicenseGate (T78): `_gate_check`, `_gate_audit_refusal`, hằng `GATE_*`; gate chạy TRƯỚC khối xoá/ghi; khối `DELETE` idempotent dời xuống sát INSERT; từ chối → `PermissionError` + `sys.exit(2)` |
| `scripts/etl_t109_provenance.py` | Thêm LicenseGate: `resolve_source_id`, `_gate_check`, `_gate_audit_refusal`, `gate_preflight(conn, dry_run)` (op `DERIVE`, mọi source trong `entity_claims` + DILA); gọi trong `main()` trước khi tạo bảng/backfill; từ chối → `SystemExit(2)` |
| `tasks/T287-m1-noi-gate-etl-con-lai.md` | `status: testing`, `updated: 2026-11-01`, `outcome`, tick bước 1–4 |
| `docs/sessions/2026-11-01/T287-coder/backup/*.bak-before-coder` | Bản sao 2 script trước khi sửa |
| `docs/sessions/2026-11-01/T287-coder/verify_t287.py` | Script kiểm chứng (DB tạm, không đụng `data/lineage.db`) |

## 2. Hiện trạng kiểm lại (bước 1)

Grep `INSERT ... INTO entity_claims` trên toàn repo (trừ `tests/`, `docs/sessions/` backup):

- `scripts/etl_entity_claims.py` — 4 chỗ INSERT (đã có gate từ trước, dùng làm mẫu).
- `scripts/wire_evidence_into_entity_claims.py` — 1 chỗ INSERT → **thiếu gate** (đã nối).
- `scripts/etl_t109_provenance.py` — **KHÔNG INSERT `entity_claims`**; chỉ ghi 2 bảng dẫn xuất `entity_claims_audit` (hash nội dung) và `events_provenance` (gán cứng source `DILA` từ `places_dila`).

→ Kết luận: task mô tả "2 script ghi entity_claims" nhưng thực tế chỉ 1 script INSERT trực tiếp. Script còn lại vẫn được nối gate vì nó **dẫn xuất** (DERIVE) từ `entity_claims` / dữ liệu DILA — đúng tinh thần `done_when` ("mọi script ghi entity_claims gọi LicenseGate trước khi ghi").

## 3. Cách làm (bước 3)

### wire_evidence_into_entity_claims.py

```python
GATE_SCRIPT = 'scripts/wire_evidence_into_entity_claims.py'
GATE_TARGET_TABLE = 'entity_claims'
GATE_OPERATION = 'INGEST'
```
- Import `gate.license.LicenseGate` theo mẫu `etl_entity_claims.py` (dòng 26–29).
- `_gate_check(source_id, operation='INGEST', allow_block=False)`:
  - allowed → in `[GATE OK]`;
  - refused → `_gate_audit_refusal(...)` rồi `raise PermissionError`.
- Gate chạy **sau khi** đã dựng xong danh sách claim nhưng **trước mọi thao tác ghi**, chỉ cho nguồn thật sự có claim (`stats['cbeta']`, `stats['marcus']`, `stats['wikidata']`) để không chặn oan khi 0 row.
- **Sửa quan trọng:** khối `DELETE FROM entity_claims WHERE source_reference LIKE 'T69:%'` (idempotent) được **dời từ đầu `run()` xuống ngay trước INSERT**. Nếu để nguyên, gate từ chối sau khi đã DELETE thì mất dữ liệu T69 cũ oan.
- `--dry-run`: gate vẫn in cảnh báo nhưng `allow_block=True` → không chặn, **không ghi** `en_audit_log` (giữ đúng cam kết "No DB changes").

### etl_t109_provenance.py

```python
GATE_SCRIPT = 'scripts/etl_t109_provenance.py'
GATE_OPERATION = 'DERIVE'
GATE_TARGET_TABLE = 'entity_claims_audit,events_provenance'
```
- `gate_preflight(conn, dry_run)`: lấy `SELECT DISTINCT source_id FROM entity_claims` + `DILA` (tra `data_sources`, fallback 1) → `_gate_check(..., 'DERIVE')`.
- Gọi trong `main()` ngay sau khi `connect()`, **trước** `build_entity_claims_audit` / `build_events_provenance` / `build_views`; chế độ `--revert` không gate (chỉ DROP bảng dẫn xuất, 0 động dữ liệu base).
- Từ chối → `SystemExit(2)`, không tạo bảng, không ghi row.

### Nhánh từ chối — `en_audit_log`

1 dòng/lần từ chối (ghi vào cùng DB của `LicenseGate`):

| Cột | Giá trị |
|---|---|
| `entity_ref` | `source:<source_id>` |
| `action` | `license_gate_block` |
| `field_name` | bảng đích (`entity_claims` hoặc `entity_claims_audit,events_provenance`) |
| `new_value` | `reason` từ LicenseGate |
| `evidence_sources` | JSON `{gate, operation, status, source_id, target_table, script}` |
| `editor` | `scripts/<tên script>` |
| `verification_status` | `blocked` |
| `created_at` | ISO timestamp |

## 4. Kiểm chứng (bước 4)

```text
python -X utf8 -c "import ast; ast.parse(...)"        -> AST OK (2 file)
python -X utf8 -m py_compile scripts/etl_t109_provenance.py scripts/wire_evidence_into_entity_claims.py -> exit 0
python -X utf8 -m pytest tests/test_license_firewall.py -q -> 16 passed
python -X utf8 docs/sessions/2026-11-01/T287-coder/verify_t287.py -> KẾT QUẢ: PASS
```

`verify_t287.py` dựng DB tạm (`%TEMP%/t287_*.db`) với `data_sources` (CBETA/MARCUS hợp lệ, source 99 `BLOCKED`), `en_audit_log`, `entity_claims`; KHÔNG mở `data/lineage.db` thật. Kết quả:

- CBETA (3) → `[GATE OK] status=ACTIVE op=INGEST`.
- Source 99 BLOCKED → `PermissionError`, đúng 1 dòng `en_audit_log` (`action=license_gate_block`, `entity_ref=source:99`, `field_name=entity_claims`, `verification_status=blocked`, `editor=scripts/wire_evidence_into_entity_claims.py`, `evidence_sources` chứa `BLOCKED`).
- dry-run wire → không thêm dòng audit.
- `etl_t109.gate_preflight` gặp source 99 → `SystemExit(2)` + 1 dòng audit (`field_name=entity_claims_audit,events_provenance`).
- dry-run t109 → không chặn, không ghi audit.

## 5. Chưa làm / cần MA quyết

1. **Fail-open khi import gate lỗi:** cả `etl_entity_claims.py` (mẫu) và 2 script này đều `[WARN] ... bỏ qua kiểm tra` nếu `gate.license` không import được. Nếu MA muốn **fail-closed** (không có gate ⇒ không ghi) thì cần đổi cả 3 script — đề nghị task riêng, không tự mở rộng scope ở đây.
2. **etl_t109 gate theo mọi `source_id` có trong `entity_claims`:** nếu tương lai có claim của nguồn `BLOCKED` lọt vào DB, ETL này sẽ dừng (có audit). Đây là hành vi mong muốn nhưng cần tester biết để không coi là hồi quy.
3. Không chạy ETL thật (`--apply`) — đúng mục 5 của task; DB thật không được mở trong phiên này (worktree không có `data/lineage.db`).
4. Không commit/git — theo ranh giới vai Coder.

## 6. Revert

```text
copy /Y docs\sessions\2026-11-01\T287-coder\backup\wire_evidence_into_entity_claims.py.bak-before-coder scripts\wire_evidence_into_entity_claims.py
copy /Y docs\sessions\2026-11-01\T287-coder\backup\etl_t109_provenance.py.bak-before-coder scripts\etl_t109_provenance.py
```
(Không có thay đổi DB/schema; ETL không được chạy nên 0 dữ liệu bị ảnh hưởng.)
