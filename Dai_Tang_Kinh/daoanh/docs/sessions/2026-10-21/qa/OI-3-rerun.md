# OI-3 — Chạy lại 4 bước FAIL trên worktree hiện tại (2026-10-21)

Người chạy: daoanh-qa (chỉ đọc). Mỗi bước chạy 1 lệnh riêng, không pipe, không ghép lệnh.
Tên script đã đối chiếu trong `package.json`: `audit:honesty:strict`, `test:t232`,
`test:translation`, `audit:t166` — đều tồn tại (dòng 54, 47, 25, 29).
Lưu ý môi trường: shim `npm` hỏng trên máy này, chạy qua `npm.cmd` (npm 10.8.2).
Exit code đo bằng wrapper `subprocess` trong %TEMP% (ngoài workspace), không suy đoán.

---

## Bước 1 — `npm.cmd run audit:honesty:strict`

- **EXITCODE: 1**
- 20 dòng lỗi đầu:

```
T234 DATA HONESTY GATE — read-only, 7 kiem tra
  [FAIL] H1  event_evidence.event_id khop event_type        41
         event_evidence khong khop event_type hien tai cua place_timeline_events
  [FAIL] H2  time_mentions.time_authority_id tro tai that   96
         authority goc placeholder reign_era_dict: 96 | authority sai dinh danh khac: 0
  [FAIL] H3  nam suy ra duoc tu note hoac bang trieu dai    969
         khong suy ra duoc (969) + ngoai khoang trieu dai (0) | W1a legacy note 0
         + W1a nghiem note 0/label 0 + W1b 0 + W1c 0 | QID 253 + midpoint co nhan 1538;
         midpoint khong hien khoang (6) va year ngoai khoang (0) van FAIL;
         vi du: [('PL000000000173', 467), ('PL000000000177', 467), ('PL000000000180', 467)]
  [FAIL] H4  nhan '(N年建)' co khop nguon                     745
         nhan '(N年建)' ma N khong co trong note (menh lenh bia): 745
  [FAIL] H5  source_ref khong tu tham chieu                 55
         source_ref tu tham chieu (source_ref = source)
  [ OK ] H6  time_periods era/dynasty co start_year
  [ OK ] H7  dila_id ton tai trong places_dila
[BAO CAO] FAIL 5/7 — du lieu BI DANG/SAI.
[STRICT] pipeline bi chan.
```

- **Kết luận: DO DATA có sẵn trong DB.** Script `scripts/audit_data_honesty.py` sạch
  so với HEAD (`git diff HEAD --name-only` rỗng), mở DB `mode=ro` (dòng 393), 5 FAIL
  đều là đếm bất thường nội dung dữ liệu (H1=41, H2=96, H3=969, H4=745, H5=55) —
  khớp đúng số liệu OI-3 ghi. Không phải code chưa commit.

## Bước 2 — `npm.cmd run test:t232`

- **EXITCODE: 1**
- Dòng lỗi:

```
test_09_missing_parent_is_incomplete ... FAIL
======================================================================
FAIL: test_09_missing_parent_is_incomplete (__main__.Tests.test_09_missing_parent_is_incomplete)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests\test_t232_generation_engine.py", line 40, in test_09_missing_parent_is_incomplete
    self.graph([(1,2),(4,2)]);r=self.compute(2);self.assertEqual(r['status'],'incomplete');...
                                                ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
AssertionError: 'candidate' != 'incomplete'
- candidate
+ incomplete
----------------------------------------------------------------------
Ran 20 tests in 1.429s
FAILED (failures=1)
```

- **Kết luận: DO CODE (đã commit), KHÔNG phải data, KHÔNG phải code chưa commit.**
  Test dùng SQLite `:memory:` tự dựng (dòng 8-9, không đụng lineage.db). Cả
  `tests/test_t232_generation_engine.py` lẫn `src_python/generation_engine_v2.py`
  đều sạch so với HEAD. Engine trả `'candidate'` trong khi test kỳ vọng
  `'incomplete'` cho case thiếu cha — mâu thuẫn logic giữa 2 file đã commit.

## Bước 3 — `npm.cmd run test:translation`

- **EXITCODE: 1**
- Chuỗi `&&` gồm 13 test; chạy tới `test:t178` thì dừng (t178 exit 1) ⇒
  t179, t200, t167, t169, t170, t74, t203, t207, t208, t211 KHÔNG chạy trong lượt này.
- t165 PASS 15/15, t166 PASS 18/18, t178: 68/69 PASS với 1 FAIL:

```
=== Gap 17: Test Case 2 fixture THẬT A009460 丹霞天然 (§8 mục 17) ===
  PASS  17a fixture A009460 có trong vn_person_authority
  PASS  17b name_zh = 丹霞天然  [丹霞天然]
  FAIL  17c name_vi = Đơn Hà Thiên Nhiên  [Thiên Nhiên]
  PASS  17d status = verified  [verified]
==================================================================
  FAIL: 17c name_vi = Đơn Hà Thiên Nhiên  [Thiên Nhiên]
KẾT QUẢ: 68/69 PASS
```

- Ghi chú phụ: hàng loạt cảnh báo `[canonical_lock] nguon chet do loi schema:
  no such table: namevi_map_places / people / canonical_decision /
  person_display_names / vn_person_authority / person_name_correction /
  name_vi_map` trong lúc chạy — code tự chịu lỗi (fallback), không làm test đỏ,
  nhưng cho thấy DB test context thiếu nhiều bảng nguồn tên.

- **Kết luận: DO DATA có sẵn trong DB.** Giá trị `vn_person_authority.name_vi`
  của fixture A009460 đang là `'Thiên Nhiên'`, test (đã commit, sạch so HEAD)
  kỳ vọng `'Đơn Hà Thiên Nhiên'`. Là lệch nội dung dữ liệu, không phải code.

## Bước 4 — `npm.cmd run audit:t166`

- **EXITCODE: 1**
- Dòng lỗi:

```
═══ T166 Identity Audit ═══
=== T166 identity status distribution ===
Traceback (most recent call last):
  File "scripts\t166_identity_audit.py", line 309, in <module>
    main()
  File "scripts\t166_identity_audit.py", line 290, in main
    _stats(conn)
  File "scripts\t166_identity_audit.py", line 263, in _stats
    rows = conn.execute(
        "SELECT COALESCE(identity_status,'(NULL=legacy)') s, COUNT(*) n "
        "FROM translation_cache GROUP BY s ORDER BY n DESC").fetchall()
sqlite3.OperationalError: no such column: identity_status
```

- Đối chiếu schema chỉ đọc: `pragma_table_info('translation_cache')` trả 14 cột
  (id, source_hash, source_type, entity_id, source_text, translated_text, model_id,
  rules_version, status, report_count, approved_by, approved_at, created_at,
  updated_at) — **không có `identity_status`**.
- Migration thêm cột tồn tại và đã commit: `scripts/t166_identity_migrate.py`
  (CACHE_COLS = ('identity_status', 'identity_issues', 'identity_lock_hash'),
  dòng 36). `t165_phase8_alignment_migrate.py:101` cũng yêu cầu T166 migrate trước.

- **Kết luận: DO SCHEMA DB chưa migrate (data/schema có sẵn), KHÔNG phải code
  chưa commit.** Cả audit script lẫn migration script đều sạch so với HEAD.
  Cần Admin duyệt chạy `t166_identity_migrate.py` (lệnh GHI DB — QA không chạy).

---

## Tổng hợp

| Bước | Exit | Nguyên nhân | Loại |
|---|---|---|---|
| audit:honesty:strict | 1 | 5/7 check FAIL trên dữ liệu DB | Data có sẵn |
| test:t232 | 1 | engine trả 'candidate' ≠ test kỳ vọng 'incomplete' | Code đã commit (logic lệch) |
| test:translation | 1 | t178 17c: name_vi DB 'Thiên Nhiên' ≠ kỳ vọng 'Đơn Hà Thiên Nhiên' | Data có sẵn |
| audit:t166 | 1 | translation_cache thiếu cột identity_status | Schema DB chưa migrate |

Không bước nào do code chưa commit gây ra (4 script/test + engine đều
`git diff HEAD` sạch). Chưa kiểm tra: 4 bước này trên HEAD sạch (worktree có
WIP phiên khác — nhưng các file liên quan đều không nằm trong WIP).
