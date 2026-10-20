---
id: T195
title: "T176 re-review lần 3 — phát hiện P0 thật (name_vi_map id=4689), cấm revert BUG-025, thêm §2b–§2i"
module: Docs / Plan Review
priority: high
status: done
owner: claudecode
depends_on: [T194, T176]
created: 2026-09-30
updated: 2026-09-30
designed_by: claudecode
handoff_to: Claude Code Agent (đã xong — docs-only, 0 code/0 DB)
plan_approved_at: "2026-09-30 (Admin duyệt scope: T195 docs-only fix T176; name_vi_map A021462 chỉ tài liệu hóa, KHÔNG ghi lineage.db)"
done_when: |
  P0 thật = name_vi_map id=4689 được ghi rõ · revert BUG-025 bị đánh dấu CẤM ·
  3 lớp nhiễu phân biệt được · sai thanh + khoảng trắng + đồng âm + Izan Reiyū
  đều có bằng chứng SQL · 12 safety rules trỏ đúng X-T166 SPEC · 0 code/0 DB ·
  guard/lint/test PASS · 2-pass revertible.
---

# T195 — Re-review T176 (Phase0C rev2) lần 3: P0 thật + cấm revert BUG-025

> **Bối cảnh:** T194 đã sửa 4 fact + 6 line-ref của T176. Lần này re-review sâu
> hơn (đọc **full row** thay vì `SELECT COUNT(*)`) → lộ P0 mà T194 **không** thấy.

## 0. Kết luận quan trọng: P0 cũ của T176/T194 là SAI framing

T194 (và T176 cũ) đặt P0 là **"B+C collapse trong `people[A001984].name_vi`"**.
Verify thực tế: `people` **đã sạch** — BUG-025 đã sửa đúng 2026-09-22.

| id | `people.name_zh` | `people.name_vi` | trạng thái |
|---|---|---|---|
| A001984 | `靈祐` | `Quy Sơn Linh Hựu` | ✅ đúng (display) |
| A021462 | `鏡堂覺圓` | `Kính Đường Giác Viên` | ✅ đúng |

**P0 thật nằm ở bảng khác** — `name_vi_map` (search path #2), row `id=4689`.

## 1. P0 thật — `name_vi_map.id=4689` (verify 2026-09-30)

```sql
SELECT * FROM name_vi_map WHERE id=4689;
```

| cột | giá trị | vấn đề |
|---|---|---|
| `name_vi` / `name_vi_final` | `Quy Sơn Linh Hựu` | tên của **A001984** gán lên **A021462** |
| `confidence` | **`1.0`** | **cao nhất hệ thống** |
| `approved_by` / `approved_at` | `NULL` / `NULL` | ⇒ **không** thuộc tier A |
| `name_zh` | `香嚴智閑` | sai — `people[A021462].name_zh` = `鏡堂覺圓` |
| `dila_id` | `A021462` | **người sai** |
| `marcus_ids` | **`A027031`** | ⚠ A027031 = 法端 *Duyên Khánh Pháp Đoan* — **vị khác hoàn toàn** |
| `birth_year`/`death_year` | `NULL`/`NULL` | dù `bio_snippet` có `771-853` |
| `bio_snippet` | `(潙山靈祐, Izan Reiyū, 771-853): h…` | chứa 3 dữ kiện mới |
| `source` | `daoanh_dict` | nhập tay, không phải auto |

**Tác động:** search path #1 (`people.name_vi LIKE`) đã đúng, nhưng path #2
(`name_vi_map.name_vi LIKE`) vẫn trả **A021462** ở `confidence=1.0`, đè mọi
tầng thấp hơn. Đây là lý do audit còn "đường resolve sai còn sốt".

**T194 đã ghi đúng phần tier-gap** (`name_vi_final` + `conf=1.0` + `approved_by=NULL`)
nhưng **thiếu** `confidence=1.0` là mức cao nhất, `marcus_ids` sai, và
`birth/death_year` NULL.

## 2. ⚠ P0 mới — revert của BUG-025 **ĐẢO NGƯỢC**, cấm dùng làm rollback

`docs/bugs.md:411` (nguyên văn):

```sql
-- FIX (đúng):
UPDATE people SET name_vi='Kính Đường Giác Viên' WHERE id='A021462' AND name_vi='Quy Son Linh Huu';
UPDATE people SET name_vi='Quy Sơn Linh Hựu'    WHERE id='A001984' AND name_vi='Đại Viễn Thiền Sư';
-- REVERT (SAI):
UPDATE people SET name_vi='Quy Sơn Linh Hựu'  WHERE id='A021462';   -- tái tạo bug
UPDATE people SET name_vi='Đại Viễn Thiền Sư' WHERE id='A001984';   -- mất searchable
```

3 lỗi: **đảo người** · **mất điều kiện `AND`** (ghi đè không chặn) ·
**đẩy A001984 về thụy hiệu**. ⇒ Rollback đúng cho audit này là
`git revert <pass-1 SHA>` (docs-only), **không** phải SQL trong bugs.md.

## 3. Ba lớp nhiễu — phải phân biệt, không gộp

| lớp | đặc trưng | row | conf |
|---|---|---|---|
| (i) **neo sai người** | `dila_id` trỏ người khác | `4689` → A021462 | **1.0** |
| (ii) **không neo** | `dila_id`/`name_zh`/`marcus_ids` = `NULL` | `1300`(`Linh Huấn`) `1301`(`Linh Hựu`) `2270` `2271` `3522` | 0.5 |
| (iii) **neo đúng** | — | **chưa có row nào cho A001984** (0 row) | — |

Lớp (ii) gồm **tên sách** vẫn khớp `LIKE '%Quy Sơn Linh Hựu%'`:
`2271` = `Quy Sơn Linh Hựu Thiền Sư Ngữ Lục` (Ngữ Lục = 語錄) ·
`2270` = `Quy Sơn Cảnh Sách của Thiền Sư Linh Hựu ghi:` ·
`3522` = đoạn mô tả *Cổ Kim Tiệp Lục*.

⇒ Sửa (i) **không đủ** — search vẫn trả (ii).

## 4. Sai thanh + cụm "Linh H*"

**Sai thanh `Hữu` (Lữu) vs đúng `Hựu` (ực)** — cùng Hán 靈祐:

| nơi | id | `name_vi` | conf | source |
|---|---|---|---|---|
| `marcus_reference` | **A001984** | `Linh Hựu` ✅ | **1.0** | `curated_T51g` |
| `marcus_reference` | A023322 | `Linh Hữu` ❌ | 0.5 | `auto_hanviet_T51f` |
| `marcus_reference` | A023362 | `Linh Hữu` ❌ | 0.5 | `auto_hanviet_T51f` |
| `name_vi_map` | A032868 | `Linh Hữu` ❌ | 0.7 | `auto_transliterate` |

⇒ "đa số là `Linh Hữu`" là **sai**; curated T51g mới là chuẩn âm.

**6 người tên `Linh H*`** (mọi `LIKE 'Linh H%'` đều fan-out):
`令休` Linh Hưu (A010280) · `靈暉` Linh Huy (A024899) ·
`令翬` Linh Huy (A035457) · `靈訓` Linh Huấn (A019949) ·
`靈祐` Linh Hữu (A032868) · 靈祐 `Linh Hựu` (**A001984**).

⇒ Test **bắt buộc** exact match `Linh Hựu` + `name_zh='靈祐'`; **cấm** prefix match.

## 5. Khoảng trắng thừa trong `name_zh`

`靈祐 ` (**space cuối**) ở `marcus_reference.label` (A001984) **và**
`vn_person_authority.name_zh` (`alias_A001984`). A023322/A023362 **không** thừa
⇒ 3 node cùng Hán không đồng nhất ⇒ exact-join rơi fallback. Gốc rễ: raw slice
từ TTL header `靈祐 (Izan Reiyū, …)`. Phải `TRIM()` toàn read path.

## 6. Đồng âm `Quy` + âm Nhật

- `潙山` **Quy Sơn** = **địa danh** (núi, Phúc Kiến) → tiền tố hiệu danh A001984.
- `圭仰宗` **Quy Ngưỡng Tông** = **tông phái** Trung Hoa → **khác người**,
  đã lan vào `name_vi_map` id=3522.
- ⇒ Normalizer khử dấu sẽ gộp `Quy Ngưỡng` với `Quy Sơn`. Cần test chặn.
- `bio_snippet` chứa **`Izan Reiyū`** = on'yomi của 靈祐 → họ alias **mới**,
  không thuộc họ Hán-Việt; read path chỉ index tiếng Việt sẽ miss.

## 7. Quy tắc suy ra `canonical` — có tiền lệ, nhưng KHÔNG nhất quán

TTL tự tách: `Quy Sơn (潙山)` + **"pháp danh Linh Hựu"** ⇒ B=`Linh Hựu`, C=`Quy Sơn Linh Hựu`.

**Tiền lệ 8 row `person_display_names`** (bằng chứng mạnh nhất cho hướng B/C):

| `person_id` | display (C) | authority (B) | xử lý prefix |
|---|---|---|---|
| A038686 | Đại Huệ Tông Cảo | Đại Đức Tông Cảo | Huệ→Đức |
| A036842 | Ngũ Tổ Pháp Diễn | **Pháp Diễn** | bỏ trọn `Ngũ Tổ` |
| A000453 | Viên Ngộ Khắc Cần | **Khắc Cần** | bỏ trọn `Viên Ngộ` |
| A004146 | Dương Kì Phương Hội | Dương Kỳ Hội | bỏ `Phương` |
| A033489 | Bạch Vân Thủ Đoan | Vân Tụ Thú Đoan | ⚠ **giữ** `Vân Tụ` |

⚠ **Không có thuật toá suy ra `authority`** (A004146 bỏ `Phương` còn A033489
giữ `Vân Tụ`) → phải **ghi tường minh** từng case. Riêng A001984 sạch vì
潙山 là tên **núi/tông**, không thuộc pháp danh. `person_display_names`
**0 row** cho A001984 → chỗ fix sẽ map vào.

## 8. Ngày `771-853` không nguồn

Chỉ là claim trong text từ điển Việt; `vn_person_authority.birth_year/death_year`
= `NULL`. TTL tự mâu thuẫn: header `771-853` vs thân "hoảng dương Thiền tông
khoảng 40 năm". ⇒ **Không** trình bày như fact authority.

## 9. Sửa trỏ 12 safety rules (lỗi tham chiếu)

- ✅ Nguồn chuẩn: `docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md`
  (code hiện hành `canonical_lock.py`).
- ❌ **KHÔNG** phải `X-T171` §12 — X-T171 §12 tên là **"Quan hệ"**, không có
  safety rules.
- CONFLICT cần Admin: X-T171 §3.2 muốn `person_name_alias` (đầy đủ) vs DB thực
  tế dùng `person_display_names` (8 row, thiếu alias đầy đủ).

## 10. Files

- Sửa: `docs/Mimo-Flash/T176-phase0c-rev2-canonical-person-identity-audit.md`
  (thêm §2b–§2i, sửa §2 bảng, §5 prompt block, §12b, §14 TEST-08…14, front-matter)
- Task này: `tasks/T195-t176-p0-correction.md`
- Session: `docs/sessions/2026-09-30_t195-t176-p0-correction.md`
- **Không đụng**: `T175-…md` (giữ nguyên theo chốt Admin T194) ·
  `lineage.db` (chỉ đọc `mode=ro`) · `app.py` · `T194`/`X-T174`

## 11. Remediation — tài liệu tham chiếu, KHÔNG thực thi

SQL nằm ở **T176 §2i**. Toàn bộ là `UPDATE` **có điều kiện** ⇒ idempotent,
không `DELETE`. R0 = `SELECT` preview bắt buộc chạy trước.
Admin chốt 2026-09-30: **chỉ tài liệu hóa, KHÔNG ghi `lineage.db`.**

## 12. Revert

Docs-only, 2-pass:
`git revert --no-edit a0aad7185b64064dac624839723b9a3fe0709b6a`.
Không DB/cache/code. Nếu cần rollback data → restore `lineage.db` từ backup,
**tuyệt đối không** chạy "Revert:" trong `docs/bugs.md:411`.