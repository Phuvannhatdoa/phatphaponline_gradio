# Session 2026-09-22

## T158 — Lineage Consensus Layer (đã commit d6b9154 session trước)

Xem task: `tasks/T158-lineage-consensus.md`

---

## BUG-025 — Fix search "Quy Sơn Linh Hựu" zoom sai về A021462

### Triệu chứng
Gõ "Quy Sơn Linh Hựu" trong global search → trả A021462 (鏡堂覺圓 = Kính Đường Giác Viên) → load lineage → hiện "Pháp hệ · Kính Đường Giác Viên" thay vì đúng người.

### Root cause
Bảng `people` (SQLite `lineage.db`) có dữ liệu sai:
- A021462 (鏡堂覺圓): `name_vi = "Quy Sơn Linh Hựu"` — SAI
- A001984 (靈祐): `name_vi = "Đại Viên Thiền Sư"` — tên thụy hiệu, không phải tên thông dụng

`/daoanh/api/search` query: `SELECT id, name_vi, name_zh FROM people WHERE name_vi LIKE ? ...`
→ trả A021462 vì `name_vi` của nó khớp "Quy Sơn Linh Hựu".

### Fix (data-only, không đổi code)
```sql
UPDATE people SET name_vi='Kính Đường Giác Viên' WHERE id='A021462' AND name_vi='Quy Sơn Linh Hựu';
UPDATE people SET name_vi='Quy Sơn Linh Hựu' WHERE id='A001984' AND name_vi='Đại Viên Thiền Sư';
```

### Verify
- API `/daoanh/api/search?q=Quy+Sơn+Linh+Hựu` → trả A001984 ✓
- UI: gõ "Quy Sơn Linh Hựu" → load lineage A001984 → sidebar "Pháp hệ · Linh Hựu" ✓
- Screenshot: session 2026-09-22 (sidebar hiện "Pháp hệ · Linh Hựu" đúng)

### Status
FIX APPLIED (DB thay đổi trực tiếp, không có code diff) — chờ user confirm → đánh Done

---

## BUG-026 — Fix search "Thạch Đầu Hy Thiên" trả 2 người (2026-09-23)

### Triệu chứng
Search "Thạch Đầu Hy Thiên" → trả cả A010291 (希遷, ĐÚNG) lẫn A001744 (慧辯, SAI). Verify: `/daoanh/api/search?q=Thạch+Đầu+Hy+Thiên` → `monks: [A001744, A010291]` cả hai cùng `name_vi`.

### Root cause
A001744 (慧辯, Bắc Tống): `name_vi = "Thạch Đầu Hy Thiên"` — SAI. Đây là tăng nhân Bắc Tống (hiệu 無際大師, trụ 衢州靈祐山秀峰寺, nối pháp 圓照宗本), không phải Thạch Đầu Hy Thiên (A010291, 石頭希遷, Đường 700-790).

### Fix (data-only)
```sql
UPDATE people SET name_vi='Tuệ Biện' WHERE id='A001744' AND name_vi='Thạch Đầu Hy Thiên';
```
(慧辯 → Sino-Vietnamese: Tuệ Biện)

### Status
FIX APPLIED (2026-09-23) — chờ DB write lock release (app server đang giữ connection), chờ user confirm → đánh Done

### Revert
```sql
UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE id='A001744';
```
