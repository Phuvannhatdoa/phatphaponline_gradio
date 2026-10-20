---
task: T199 + T200 + T201
date: 2026-10-01
status: T199 PENDING ADMIN APPLY (script+docs xong, DB thật CHƯA ghi) · T200/T201 BLOCKED (cần sửa code)
scope: review + bác plan T179 · TRIM khoảng trắng Hán · docs schema caveat · phát hiện P0 DEAD CODE
admin: "1) quét task, 2) giải thích ý nghĩa cụ thể, 3) Trim hết" + "cần 1 canonical row, phê chuẩn đề xuất này, nếu cần hãy tạo task mới với name là Txx"
commit_pass1: "910d3ebfc9ae9b8213717e3769161fe2c966191b"
commit_pass2: "<sha_T199_pass2>"
revert: "git revert --no-edit 910d3ebfc9ae9b8213717e3769161fe2c966191b <sha_T199_pass2> && python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert"
---

# Session 2026-10-01 — T199/T200/T201: VNPA review, bác plan T179, phát hiện P0 DEAD CODE

## 1. Yêu cầu Admin

Admin yêu cầu review `docs/Mimo-Flash/T179-vnpa-verified-status-data-fix.md` ("check và xác nhận
vấn đề sau đúng logic chưa, nếu chưa hãy chỉ ra và đề xuất giải pháp"), sau đó chốt:
1. "quét task" (chọn ID)
2. "giải thích ý nghĩa cụ thể" (ý nghĩa `status`)
3. "Trim hết" (58 row `marcus_reference.label`)
4. "cần 1 canonical row, phê chuẩn đề xuất này" + "nếu cần hãy tạo task mới với name là Txx" +
   "Update lên /docs/ và các .md files tương ứng, cập nhật vào Dashboard để admin xem"

## 2. Quét ID

`tasks/` trên đĩa: max = **198** (T198 vừa tạo ở session trước). HEAD cũng max 198.
⇒ **ID tiếp theo: T199**; tách thêm **T200** (code change) và **T201** (P0 DEAD CODE).

## 3. Verify bác plan T179 (read-only DB + code)

| # | Claim T179 | Thực tế | Kết luận |
|---|---|---|---|
| P0-1 | `id: T179` | `tasks/T179-per-rule-fingerprint-phase8.md` đã tồn tại, DONE (commit `2e252d0`→`b46560a`) | trùng ID |
| P0-2 | row `person_id='A001984'` | Bảng **không có cột `person_id`** — PK = `id`. Row = `id='alias_A001984'`, `dila_id='A001984'`. Query như T179 viết ⇒ chạy thật: `sqlite3.OperationalError: no such column: person_id` | SQL hỏng |
| P0-3 | `status='alias_vi_suffix'` là lỗi → nâng `verified` | `id`-prefix ↔ `status` **1:1** (`alias_*`: 450 `alias_vi_suffix` + 7 `alias_zh_match`; khác: 599 `auto_ttl` + 448 `pending` + **2 `verified`**). **438/450 alias row khác `people.name_vi`** — vd `alias_A000035`=`Mạt Sơn Liễu Nhiên` vs `people[A000035]`=`Liễu Nhiên` | đảo ngược |
| P0-4 | status sai ⇒ A001984 không đạt LOCK threshold | `canonical_lock.py:901` `SELECT … WHERE status='verified'` chạy thật ⇒ **2 row** (A009460 `Đơn Hà Thiên Nhiên`, A010616 `Thúy Vi Vô Học`). A001984 **chưa từng** là nguồn 0.95 | cơ chế sai |
| P1-1 | trailing space trong giá trị VI | `name_vi` trailing = **0/1506**; `name_zh` = **2** row; `marcus_reference.label` = **58** row | sai field |
| P1-2 | `people.name_vi` A001984 cần sửa | = `vnpa.name_vi` = `Quy Sơn Linh Hựu` — thuộc **12/450** row khớp | không có regression |
| P1-3 | — | `name_vi_map` A001984 = 0 row; `person_display_names` A001984 = 0 row | đường ưu tiên cao trống |
| P1-4 | `pytest tests/test_t166_matrix.py -q` chưa chạy được | File **tồn tại**, PASS **23/23** ngay bây giờ ⇒ là **regression guard**, không phải fix-verifier | claim stale |

Đối chiếu: T195 đã ghi đúng chỗ khoảng trắng (`靈祐 ` ở `marcus_reference.label` **và**
`vn_person_authority.name_zh`) ⇒ T179 là bản restatement sai lệch.

## 4. Ý nghĩa cụ thể (Admin hỏi mục 2)

`vn_person_authority.status` là **nhãn nguồn gốc dòng dữ liệu**, KHÔNG phải thang chất lượng:

| `id` prefix | `status` | Rows | Nghĩa |
|---|---|---|---|
| `alias_*` | `alias_vi_suffix` | 450 | row alias: `name_vi` là tên đầy đủ có tiền/hậu tố Hán-Việt |
| `alias_*` | `alias_zh_match` | 7 | row alias: khớp qua tên Hán |
| khác | `auto_ttl` | 599 | tự sinh từ TTL |
| khác | `pending` | 448 | chờ duyệt |
| khác | `verified` | **2** | **hạng duy nhất `canonical_lock` đọc** (0.95) |

- `SOURCE_LEVELS` chỉ khai `'vn_person_authority.verified': 0.95`; `_LOCK_FLAGS` chỉ chứa
  `'vn_person_authority.verified'` ⇒ `alias_vi_suffix`/`alias_zh_match`/`auto_ttl`/`pending`
  **không ảnh hưởng** tới LOCK/CANDIDATE.
- `git grep` toàn bộ `*.py`: **không consumer nào** đọc 3 giá trị đó ⇒ nhãn chết/ghi đè.
- Trailing space là ở **Hán** (`name_zh`, `label`) vì đó là khoá ghép: `'靈祐 '` ≠ `'靈祐'` ⇒
  không khớp Hán ở TTL/marcus. TRIM chỉ làm Hán khớp đúng, **không** đụng identity.

## 5. ⚠ P0 BLOCKER phát hiện khi test end-to-end: `canonical_decision` là DEAD CODE

Đã chèn row `canonical_decision(A001984)` vào DB copy rồi chạy
`canonical_lock.build_canonical_lock(source_text='靈祐 …')`:

```
id=4bc1b80d  src_form='靈祐'  canonical='Linh Hữu'  lvl=0.7  src=name_vi_map.auto  LOCKED=False
```

⇒ `canonical_decision` **không đóng góp gì**. Chạy tay query nguồn #1:

```
sqlite3.OperationalError: no such column: pd.dila_id
```

**Nguyên nhân** — `canonical_lock.py:871`:
```python
LEFT JOIN places_dila pd ON pd.dila_id = cd.entity_ref   # ← SAI
```
`places_dila` có **PK = `id`**, không có cột `dila_id` (verify `PRAGMA table_info`; `people` cũng vậy).
`_safe()` (L854-862) nuốt `sqlite3.Error` ⇒ trả `[]` ⇒ **nguồn #1 chưa bao giờ chạy được**.

**Hệ quả:**
1. Row `admin_approved` `PL000000000314` (T68) **chưa từng** có tác dụng.
2. Nguồn **cao nhất** trong `SOURCE_PRIORITY` (`canonical_decision`, L808) đang trống hoàn toàn.
3. Nếu chèn row bây giờ (như kế hoạch ban đầu) sẽ là **1 row chết**.

⇒ **Canonical row A001984 defer sang T201** (sửa `pd.dila_id` → `pd.id`, rà trước khi bật,
thêm log cho `_safe()`, rồi mới chèn row).
⇒ Script T199 thêm cờ **`--with-canonical` mặc định TẮT** để không ghi row chết.

## 6. Rủi ro THẬT mà T179 bỏ sót: `dila_id` không unique + `LIMIT 1` không `ORDER BY`

- **1.259** `dila_id` khác nhau / **1.506** row ⇒ **33** `dila_id` mang **2–3 dòng**; **9/33** nhóm có cả `alias_*` lẫn non-alias.
- `app.py:5964` + `app.py:12841`: `SELECT … WHERE dila_id=? LIMIT 1` — **không `ORDER BY`** ⇒ dòng trả về không xác định.
- Vì dòng `alias_*` mang tên đầy đủ có tiền tố triều đình ⇒ nếu thắng `LIMIT 1` thì UI hiện **tên người khác**.
- Xung đột thật: **A021395** 3 tên khác (`Ngũ Tổ`/`Báo Ân`/`Tứ Tổ Pháp Diễn`) ·
  **A047679** `Phù Sơn Đức Tuyên` vs `Quảng Tuệ Đức Tuyên` = **2 người khác nhau chung 1 `dila_id`** ·
  **A026824** 3 dòng cùng gốc `Tuệ Giác` · **A010511** 3 dòng `Nam Nhạc Huyền Thái`.
- Liên quan T195: `name_vi_map.id=4689` gán `Quy Sơn Linh Hựu` lên **A021462** (người sai) — cùng lớp lỗi.
⇒ Tách **T200** (cần sửa code; cần Admin chốt tie-break, **không** tự gộp/tách 33 nhóm).

## 7. Deliverables

| File | Nội dung |
|---|---|
| `tasks/T199-vnpa-canonical-row-and-han-trim.md` | TRIM 2+58 row + guard; canonical row defer T201 |
| `tasks/T200-vnpa-dila-id-duplicate-limit1.md` | 33 nhóm trùng + `LIMIT 1` không `ORDER BY` (code) |
| `tasks/T201-canonical-lock-dila-id-dead-code-fix.md` | **P0** sửa `canonical_lock.py:871` + canonical row A001984 |
| `docs/Mimo-Flash/T199-vnpa-canonical-row-and-han-trim.md` | thay `T179-vnpa-verified-status-data-fix.md` (giữ plan cũ ở §5) |
| `scripts/t199_vnpa_trim_and_canonical.py` | `--stats`/`--dry-run`/`--apply`/`--revert`/`--with-canonical`/`--db-path`/`--force` |
| `docs/db_schema.md` §9 | 9.1 enum `status` + cảnh báo 438/450 · 9.2 `dila_id` không unique → T200 · 9.3 `canonical_decision` DEAD → T201 |

## 8. Test script (round-trip trên DB copy, DB thật KHÔNG đụng)

```
--stats      OK  2 name_zh + 58 label; canonical_decision A001984 chưa có; guard 0; status 599/450/448/7/2; dila_id trùng 33
--dry-run    OK  in 60 row TRIM + SQL mẫu + cảnh báo DEAD CODE
--apply      OK  backup + snapshot JSON → TRIM 60 row → verify 6 assert PASS (trailing 0/0/0, guard 0, people.name_vi không đổi, canonical_decision A001984 = [])
--revert     OK  60/60 row khôi phục đúng ('靈祐 ' trở lại; canonical_decision A001984 = 0)
```

Sửa 3 bug script khi test: (1) `--db-path` không map sang `args.db` → `AttributeError` (2) format string
`UPDATE %s SET %s=? WHERE %s=? AND %s=?` có 4 placeholder nhưng truyền 5 args (xuất hiện ở cả
`print_dry_run` và `do_apply`) (3) `n += con.total_changes and 0 or 0` rác → thay bằng kiểm
`cur.rowcount != 1` nghiêm ngặt.

## 9. Verify toàn repo

`npm run guard` PASS (SSOT root `visjs-app`) · `npm run lint` PASS (7 script blocks) ·
`npm run test` PASS · `npm run test:t166` **18/18 PASS** ·
`pytest tests/test_t166_matrix.py -q` **23/23 PASS** (PASS **trước** fix ⇒ regression guard).

## 10. Xoá artifact test

Đã xoá `data/backups/lineage_t199_*.db` + `lineage_t199_snapshot_*.json` tạo ra khi test
và DB copy `%TEMP%\t199_test.db`. **DB thật chưa bị ghi 1 byte nào.**

## 11. ROLLBACK

`python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert` (theo snapshot JSON) hoặc
khôi phục `data/backups/lineage_t199_<ts>.db`; `git revert --no-edit 910d3ebfc9ae9b8213717e3769161fe2c966191b <sha_T199_pass2>`.

## 12. ADMIN DUYỆT → APPLY DB THẬT + FIX T201 (2026-10-01, commit `b9a3216`)

Admin trả lời 3 câu hỏi: **1) ok · 2) ok · 3) giải thích**.

### 12.1 T199 — APPLY DB thật
| Bước | Backup | Kết quả |
|---|---|---|
| `--apply` (TRIM) | `lineage_t199_20261001_141928.db` | 60 row · trailing `name_zh` **0**, `label` **0**, `name_vi` **0** · guard **0** · `people.name_vi` không đổi · `marcus_reference` **18.127 row không đổi** |
| `--apply --with-canonical` (sau khi T201 fix) | `lineage_t199_20261001_142839.db` | `canonical_decision` A001984 = `('Quy Sơn Linh Hựu','admin_approved','verified')` |

### 12.2 T201 — fix code (P0)
`canonical_lock.py:871` `pd.dila_id` → `pd.id` + `_safe()` log lỗi + `_SAFE_ERRORS`/`safe_errors()` +
`scripts/t166_identity_audit.py` `_check_safe_errors()`.

**Verify trên DB thật** — `build_canonical_lock('靈祐')`:
| canonical_id | canonical_value | level | source | LOCKED |
|---|---|---|---|---|
| `A001984` | `Quy Sơn Linh Hựu` | **1.0** | `canonical_decision.admin_approved` | **✅ True** |
| `4bc1b80d` | `Linh Hữu` | 0.7 | `name_vi_map.auto` | ❌ False |

(trước fix: chỉ 1 entity, `name_vi_map.auto` 0.7, LOCKED=False ⇒ **đúng triệu chứng T179 mô tả**)

**Rà 2 row `canonical_decision` cũ TRƯỚC khi bật** (yêu cầu an toàn):
`PL000000000314` = `Th? S?t H?i` (hex `54683F20533F7420483F69`) ·
`PL000000000001` = `Kho?t T?t ?a Qu?c` (hex `4B686F3F7420543F74203F612051753F63`)
⇒ **corrupt với byte `?` thật (0x3F)**, không phải lỗi console.
`is_valid_vi()` trả **False** cho cả hai (chuỗi toàn ASCII) ⇒ **được lọc đúng** khi bật nguồn #1,
không khóa sai tên. Nhưng **cần sửa dữ liệu gốc** (task riêng).

**Red-team audit:** rename `places_dila` trong DB copy ⇒ `_check_safe_errors()` báo
`[FAIL] canonical_lock nguồn chết do lỗi schema ... no such table: places_dila` ✓

### 12.3 Regression sau cả 2 apply
`guard` PASS · `lint` PASS (7 blocks) · `test` PASS · `test:t166` **18/18** ·
`test_t166_matrix` **23/23** · `audit:t166` **PASS (0 FAIL)** · `test:uat` **3/3** ·
`test:compliance` PASS (glossary 75.54% ≥ goal 75.5) · `test:gov` **17 passed** · `e2e` PASS.

### 12.4 ⚠ Phát hiện thêm: docs bị hỏng encoding diacritics
`docs/tasktodo.md` có **một số entry bị hỏng dấu** (`KH?NG`, `ch?a`, `t?o`, `nh?m`, `r?ng`) — entry cũ
của session khác. Đã **sửa 2 entry của tôi** (T198, T200) bằng script UTF-8. Phần còn lại thuộc
task khác ⇒ **chưa tự sửa** (ngoài phạm vi), cần task riêng nếu Admin muốn.

⚠ **LƯU Ý commit:** `b9a3216` đưa **cả WIP P8.1 entity assertions của session khác** trong
`canonical_lock.py` vì fix T201 nằm trong cùng file (worktree dùng chung, không tách được hunk
không tương tác).

## 13. T200 BUILD — Admin chốt tie-break "ưu tiên theo status"

### 13.1 Đo trước khi chọn thứ tự (không đoán)
% khớp `people.name_vi` theo status: `pending` **10.5%** · `auto_ttl` 6.3% ·
`alias_vi_suffix` **2.7%** · `alias_zh_match` 0%. ⇒ thứ tự `verified` > `pending` >
`auto_ttl` > `alias_vi_suffix` > `alias_zh_match` khớp cả ngữ nghĩa lẫn dữ liệu.

**Bằng chứng phải nói ra:** 29/33 nhóm trùng **không có dòng nào khớp `people.name_vi`** ⇒
tiêu chí "khớp `people.name_vi" không dùng được để chọn.

### 13.2 Quét call site (toàn repo)
Module mới `vnpa_lookup.py` làm SSOT. 3 call site thực sự sửa; 5 chỗ quét được nhưng
**không** cần sửa (membership / key unique / không `LIMIT 1`) — đã ghi lý do trong task.

### 13.3 Verify
`tests/test_t200_vnpa_tiebreak.py` **25/25 PASS** + wire vào `test:translation`.
DB thật: lookup 50 lần × 33 nhóm ⇒ **0 lần khác đều**; **22/33 nhóm đổi dòng**.
Pipeline đầy đủ PASS. **0 DB change.**

### 13.4 Bug của chính tôi khi viết test (đã sửa)
1. `con.execute(_row(...))` truyền tuple thay vì `(sql, args)` ⇒ `TypeError`
2. Test 2 insert **mọi** status nên `verified` luôn thắng ⇒ phải chỉ insert target + status kém hơn
3. Còn sót `executemany` rỗng làm mất biến `rows`

## 14. T203 + T204 — sync DB sửa tên sai + cổng chặn TTL (2026-10-01)

Admin: *"tôi muốn bạn update DB trước theo phát hiện của bạn, bảo đảm sau này TTL update
cũng sẽ trùng với phát hiện lỗi và chỉnh trước"*.

### 14.1 T203 — sửa DB thật (DATA-ONLY)
Backup `data/backups/lineage_t203_20261001_191937.db` + snapshot JSON ⇒
**UPDATE 27/28 row** `vn_person_authority.name_vi` theo nhãn chuẩn (lấy từ triple
`<ex:monk/SLUG>`, không suy đoán). Guard mỗi dòng `AND name_vi=<giá trị sai>` +
`rowcount != 1` ⇒ rollback. Verify: còn **0** dòng cần sửa · 28 dòng đúng ·
`alias_vi_suffix` + `status='verified'` = **0** · 33 nhóm `dila_id` trùng **không đổi**
(không xoá dòng — nguyên nhân là `match_person`, xử ở T204).

### 14.2 T203 — phát loại 32 file TTL (Admin tự sửa)
- **TIER-1 17**: nhãn trùng tên 1 người KHÁC trong file (vd `TS-Nguyet-Chuong-Tri-Uyen`
  mang nhãn `Bảo Ninh Nhân Dũng` — tên thầy của chính mình)
- **TIER-2 15**: nhãn không liên quan (vd `TS-Dong-Son-Te-Vi`: `Giác A` vs `Đông Sơn Tề Vĩ`)
- **TIER-3 11**: chỉ khác danh xưng/tiền tố (`Cư Sĩ …`, `Sơn Chủ …`) ⇒ **GIỮ LẠI**
- **0 file bị move** — danh sách + đường dẫn tuyệt đối ở
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md` + `data/ttl_quarantine/_list.json`

### 14.3 T204 — cổng chặn TTL + siết `match_person` (CODE, 0 DB)
- `scripts/t204_ttl_preflight.py`: L1/L2/L3 **CHẶN** (exit 1) · L4/L5 cảnh báo (exit 2).
  Dùng chung `classify()` với T203 ⇒ một nguồn sự thật.
- Nối gate vào `etl_ttl_full_import.py` + `etl_ttl_person_authority.py`
  (gate **trước `DELETE`** vì script này xoá sạch rồi nạp lại). `--skip-preflight` để bypass.
- `match_person`: CŨ `exact → tail2..tail5 → zh` ⇒ MỚI `exact → zh → tail3..tailN`
  ⇒ **`dila_id` nhận >1 slug non-alias 41 → 7** (giải 36 nhóm).
- Verify: `full_import --dry-run` **DỪNG** 42 lỗi chặn · `person_authority` DỪNG trước khi
  xoá bảng (DB còn nguyên 1.506 / 2.096 row) · `tests/test_t203_ttl_guard.py` **16/16 PASS**.

### 14.4 Bug của chính tôi khi làm (đã sửa)
1. `t204._key()` flatten mất dấu `_` ⇒ **không khớp index** ⇒ âm thầm bỏ sót **toàn bộ** L1/L2
   (blocking chỉ còn 10 L3). Sửa: giữ `_`, bỏ đuôi `.ttl`.
2. `t204` tự viết lại logic so khớp ⇒ gắn nhầm 3 file `Cư Sĩ …` (hợp lệ) là L2.
   Sửa: dùng chung `t203_quarantine_ttl.classify()`.
3. `_t203_report.py` so sánh nhãn có dấu vs slug không dấu ⇒ **1.029 false positive**;
   `flat()` bỏ mất `Đ` (U+0110 không tách qua NFD) ⇒ 335 false positive. Sửa cả hai.
4. `t203_sync_vnpa_name.build_plan(db_path=DB_PATH)` default được bind sẵn ⇒ khi `None` thì
   `.replace` lỗi `AttributeError`. Sửa thành `db_path = db_path or DB_PATH`.
