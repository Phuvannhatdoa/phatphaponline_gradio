---
id: T200
title: "vn_person_authority.dila_id KHÔNG unique (29 nhóm / 61 row) + app.py LIMIT 1 không ORDER BY ⇒ chọn tên ngẫu nhiên; thêm tie-break deterministic"
module: Code / Data Integrity
priority: high
status: blocked
undone_reason: "Build ĐÃ XONG (tie-break theo status, Admin chốt 2026-10-01, test hồi quy deterministic, 0 DB change). Phần còn lại là quyết định gộp/tách dila_id — đã chuyển sang T223."
undone_until: "Khi T223 xong. T223 lại cần L7 = 0 (13 file URI sai) và L1/L2 = 0 (24 nhãn sai) trước, vì 11/23 file L1/L2 nằm trong chính các nhóm dila_id trùng."
undone_action: "ADMIN duyệt 29 nhóm tại T223 §3 (tách 15 / gộp 3 / giữ nguyên 3 / kiểm 7)."
blocked_by: T223
note: "BUILD ĐÃ XONG — phần còn lại CHỜ T223 (2026-10-03, Admin phê chuẩn). T223 giữ quyết định gộp/tách `dila_id` cho 29 nhóm / 61 row (đo lại 2026-10-03; con số 33 của bản gốc là mốc đo cũ). Lý do chờ: 11/23 file L1/L2 của T209 nằm trong các nhóm này ⇒ L7 URI sai → L1/L2 nhãn sai → nhiều row chung 1 `dila_id`. Phải sửa L7 → L1/L2 → rồi mới tới `dila_id`."
owner: claudecode
depends_on: [T199, T195]
created: 2026-09-30
updated: 2026-10-03
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-10-01 Admin: 'a) ưu tiên theo status, làm a'"
done_when: |
  Admin chốt tie-break rule cho vn_person_authority khi 1 dila_id có nhiều dòng;
  app.py:5964 và app.py:12841 (và mọi call site `FROM vn_person_authority WHERE dila_id=?`)
    có ORDER BY deterministic + LIMIT 1;
  index hỗ trợ (vd idx_vnpa_dila_id_status) nếu chạy chậm — đo trước khi thêm;
  ~~33 nhóm~~ → **29 nhóm / 61 row** (đo lại 2026-10-03). Phần phân loại + quyết gộp/tách → **chuyển sang T223** §3;
  ~~A021395 (3 tên khác) + A047679 (2 người khác chung dila_id) → Admin quyết~~ → **T223 §3** (đã phân loại A/B/C/D kèm đề xuất);
  test hồi quy chứng minh tie-break deterministic (chạy 50 lần cùng kết quả);
  tasktodo + ROLLBACK + session + dashboard; npm run pipeline PASS.
risk: |
  - `LIMIT 1` không ORDER BY ⇒ SQLite trả dòng theo thứ tự quét (rowid/index), tức là NGẪU NHIÊN
    với mặt định của query planner ⇒ UI có thể hiện tên triều đình của người khác.
  - Thêm ORDER BY sai (vd ưu tiên `alias_*`) sẽ đẩy lỗi sang hướng tệ hơn ⇒ cần Admin chốt rule,
    không tự đoán.
  - 9/33 nhóm có cả dòng `alias_*` lẫn dòng non-alias ⇒ tie-break ảnh hưởng trực tiếp tên hiển thị.
---

> ⚠️ **Số liệu cũ:** file này còn các con số **33** — đó là mốc đo lúc T200 build
> (2026-09-30 → 2026-10-01). **Đo lại 2026-10-03: 29 nhóm / 61 row.**
> Phần phân loại + quyết định gộp/tách → **T223 §3**. Các số 33 còn lại bên dưới
> là **số đo lịch sử**, không phải số hiện tại.

# T200 — `vn_person_authority.dila_id` không unique + `LIMIT 1` không `ORDER BY`

> **Tách ra từ T199** (data-only). T199 chỉ đụng 1 người (A001984); phát hiện này rộng hơn 33 người
> và **bắt buộc sửa code** ⇒ tách task riêng.

## 1. Vấn đề (verify read-only 2026-09-30)

`vn_person_authority.dila_id` **không phải khoá duy nhất**:
- **1259** `dila_id` khác nhau
- **33** `dila_id` mang **2–3 dòng** ⇒ tổng 1.506 row
- **9/33** nhóm có **cả** dòng `alias_*` lẫn dòng non-alias

`app.py` đọc bảng này bằng `LIMIT 1` **không `ORDER BY`**:

| Call site | SQL |
|---|---|
| `app.py:5964` | `SELECT … FROM vn_person_authority WHERE dila_id=? LIMIT 1` |
| `app.py:12841` | `SELECT name_vi, name_zh FROM vn_person_authority WHERE dila_id=? LIMIT 1` |

⇒ với 33 người này, **dòng trả về phụ thuộc thứ tự quét của SQLite**, không xác định.

## 2. Vì sao nguy hiểm

Dòng `alias_*` mang tên **đầy đủ có tiền tố triều đình** (vd `Ngũ Tổ Pháp Diễn`), dòng non-alias
mang tên lõi/tên khác. Nếu dòng alias thắng `LIMIT 1` ⇒ UI hiển thị **tên của người khác**.

| `dila_id` | Các dòng trùng (verify) |
|---|---|
| **A021395** | `alias_A021395`=`Ngũ Tổ Pháp Diễn` (alias_vi_suffix) · `bao_an_phap_dien`=`Báo Ân Pháp Diễn` (pending) · `tu_to_phap_dien`=`Tứ Tổ Pháp Diễn` (pending) — **3 tên khác nhau** |
| **A026824** | `duong_chau_tue_giac`=`Dương Châu Tuệ Giác` · `lang_nha_tue_giac`=`Lang Nha Tuệ Giác` · `linh_thuu_tue_giac`=`Linh Thứu Tuệ Giác` — cùng gốc `Tuệ Giác`, khác tiền tố |
| **A047679** | `phu_son_duc_tuyen`=`Phù Sơn Đức Tuyên` (pending) · `quang_tue_duc_tuyen`=`Quảng Tuệ Đức Tuyên` (pending) — **2 người khác nhau, chung 1 `dila_id`** |
| **A010511** | `dam_chau_bao_cai_uoc`=`Nam Nhạc Huyền Thái` (auto_ttl) · `nam_nhac_huyen_thai`=`Nam Nhạc Huyền Thái` (pending, `name_zh` 12 ký tự) · `the_nham_ton_tho`=`Nam Nhạc Huyền Thái` (pending) |

`A047679` và `A021395` cho thấy đây **không chỉ là trùng kỹ thuật** — có thể là `dila_id` sai,
hoặc một DILA id gộp nhiều vị. Cần Admin phân xử, **không tự ý gộp/tách**.

Liên quan: T195 phát hiện `name_vi_map.id=4689` gán `Quy Sơn Linh Hựu` lên **A021462** (người sai) — cùng lớp lỗi "tên gắn nhầm người".

## 3. Đề xuất (chờ Admin chốt tie-break)

1. **Lập danh sách 33 nhóm** + phân loại: `alias-vs-alias` / `alias-vs-canonical` / `xung-đột-tên-thật`
2. **Chốt tie-break rule** cho `LIMIT 1` — đề xuất cân nhắc (Admin quyết, không tự chọn):
   - ưu tiên dòng **không** phải `alias_*` (tên lõi khớp `people.name_vi` hơn), **hoặc**
   - ưu tiên theo `verification_status`/`status` (`verified` > `pending` > `auto_ttl` > alias), **hoặc**
   - `ORDER BY (id LIKE 'alias_%'), id` — deterministic + ổn định khi ETL thêm dòng mới
3. Thêm `ORDER BY` +o **mọi** call site đọc `vn_person_authority` theo `dila_id` (rà toàn repo, không chỉ 2 dòng trên)
4. Đo `EXPLAIN QUERY PLAN` trước khi thêm index `idx_vnpa_dila_id_status(dila_id, status, id)`
5. Test hồi quy: chạy lại query 50 lần ⇒ kết quả phải **giống hệt** (trước khi fix sẽ lệch)


## 3b. Kết quả build (2026-10-01, Admin chốt tie-break)

Admin chốt: **ưu tiên theo status**. Đo trước để không đoán:

| status | rows | % khớp `people.name_vi` | lý do đặt ở |
|--------|------|--------------------------|------------|
| `pending` | 448 | **10.5%** | người nhập/duyệt tay, khớp tên lõi cao nhất |
| `auto_ttl` | 599 | 6.3% | tự sinh từ TTL |
| `alias_vi_suffix` | 450 | **2.7%** | row alias, tên đầy đủ có tiền tố |
| `alias_zh_match` | 7 | 0.0% | row alias, khớp qua tên Hán |

⇒ Thứ tự **khớp cả ngữ nghĩa lẫn dữ liệu**:
`verified` (0) > `pending` (1) > `auto_ttl` (2) > `alias_vi_suffix` (3) > `alias_zh_match` (4), `ELSE 5`.

**Đừng dùng "khớp `people.name_vi`" làm tiêu chí:** 29/33 nhóm trùng **không có dòng nào khớp `people.name_vi`**.

### Đã sửa

**File mới `vnpa_lookup.py`** (SSOT cho mọi tra cứu theo `dila_id`):
- `VNPA_STATUS_RANK` — SQL `CASE status` để tạo rank
- `VNPA_ORDER_BY` — `ORDER BY <case> ASC, id ASC` (`id` = tie-break cuối ⇒ **luôn deterministic**, ổn định khi ETL thêm dòng)
- `lookup_by_dila(conn, dila_id, extra_cols="")` — trả 1 dòng canonical nhất
- `map_dila_to_name(conn)` — dict `{dila_id: name_vi}` dùng `setdefault` + `ORDER BY`
- `has_duplicate_dila(conn)` — `(bool, số nhóm trùng)` cho audit/test

**3 call site thực sự sửa** (`app.py`):

| Line | Trước | Sau |
|------|-------|-----|
| 5974 | `SELECT … WHERE dila_id=? LIMIT 1` (không `ORDER BY`) | `_t200_vnpa_lookup_by_dila(conn, person_id, "generation_order, dharma_lineage, biographical_note_vi")` |
| 12852 | `SELECT name_vi, name_zh … LIMIT 1` (không `ORDER BY`) | `_t200_vnpa_lookup_by_dila(conn, vpa['dila_id'])` |
| 14352 | vòng `result[r[0]] = r[1]` (dòng sau đè dòng trước) | `_t200_vnpa_map_dila_to_name(conn)` |

**Không cần sửa** (quét đã kiểm định):
- `app.py:13843` subquery `UNION` ⇒ chỉ test membership, không chọn tên
- `app.py:14220` ⇒ `set` membership
- `canonical_lock.py:941` match theo `name_zh` (chỉ 2 row `verified`, không `LIMIT 1`) ⇒ không mơ hồ
- `scripts/etl_ttl_persons.py:178` / `etl_ttl_full_import.py:269` key theo `id` (unique) ⇒ không mơ hồ

### Verify
- `tests/test_t200_vnpa_tiebreak.py` **25/25 PASS** (thứ tự rank × 5 status · tie-break `id ASC` ·
  determinism 50 lần × 5 nhóm · `setdefault` bỏ dòng rỗng · biên edge input rỗng/bảng thiếu · DB thật read-only)
- Đã **wire vào `npm run test:translation`** + `package.json` `test:t200`
- Trên DB thật: chạy lookup 50 lần × 33 nhóm ⇒ **0 lần khác** đều
- So sánh cũ↔mới: **22/33 nhóm đổi dòng** — dòng cũ đều là `auto_ttl`/`alias_*`
  (tên sai), dòng mới đều là `pending`; 3/33 trùng khớp `people.name_vi`
- `py_compile app.py vnpa_lookup.py` OK
- **Pipeline:** guard PASS · lint PASS (7 blocks) · test PASS · **test:translation PASS**
  (T165/166/178/179/**200**/167/169/170/74) · test:uat 3/3 · test:compliance PASS ·
  test:gov 17 passed · audit:t166 PASS · e2e PASS

**0 DB change** — T200 **chỉ sửa code**, không ghi dữ liệu.

## 4. Nợ kỹ thuật liên quan

**4a — `canonical_decision` DEAD CODE (đã tách task riêng → T201, P0)**

`canonical_lock.py:871` dùng `pd.dila_id` nhưng `places_dila` PK = `id` ⇒ query nguồn #1 **luôn throw**
`_safe()` nuốt ⇒ trả `[]`. ⇒ nguồn cao nhất trong `SOURCE_PRIORITY` **chưa bao giờ chạy**.
Fix + canonical row A001984 ở **T201**.

**4b — `canonical_decision` thiếu entity class**

`canonical_lock.py:825` — `_ENTITY_TYPE_BY_SOURCE['canonical_decision'] = 'PLACE'` (hard-code).
Khi T201 chèn canonical row cho **PERSON** ⇒ dòng đó bị gom nhóm `PLACE` trong `allowed_vi_set`
(post_assert L309-356). Tác động nhỏ (chỉ nới `allowed_vi_set` khi 1 Hán vừa là người vừa là nơi),
không gây HARD fail, nhưng bảng `canonical_decision` **thiếu cột entity class** ⇒ cân nhắc
`ALTER TABLE canonical_decision ADD COLUMN entity_type` (additive) hoặc suy ra class từ
`places_dila.id` vs `people.id` khi join. **Để ở T200** (đụng code `canonical_lock`, cần test).

## 5. Ngoài phạm vi

❌ Không gộp/tách `dila_id` cho 33 nhóm — cần Admin duyệt từng nhóm
❌ Không sửa `canonical_lock` logic LOCK/CANDIDATE
❌ Không đụng BUG-025 / BUG-026 / T195

## Liên kết hiện hành 2026-10-11

[T357](T357-vnpa-etl-safety-remediation.md) giữ remediation atomic/preflight/rollback của report ETL former T223. Dependency quyết định định danh của T200 vẫn thuộc [T223 29 nhóm](T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md); không đóng blocker đó bằng approval an toàn ETL. Các số kiểm cũ giữ nhãn lịch sử, chưa query DB lại.
