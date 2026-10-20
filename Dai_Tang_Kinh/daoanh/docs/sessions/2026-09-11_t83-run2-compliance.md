# Session — T83 Run 2 + Compliance Update (2026-09-11)

> Build: tiếp nối commit `0938c253` (T83 run 1 — 5,000 claims = 1.12%).
> Mục tiêu run 2: nâng `claims_reviewed`/`claims_verified` lên ≥2% (dứt khỏi WARN),
> chạy lại compliance meter, đồng bộ tasktodo + dashboard. **Zero-ALTER, additive, revertible.**

## 0. Prologue — Run 3 (2026-09-11, giải pháp tối ưu)

**Quyết định:** đẩy bootstrap lên **9.82% (44,000 claims)** — dư buffer gấp ~10× goal 1%,
ưu tiên NAME/COORDINATE/ADMIN_UNIT của mọi entity multi-source. Compliance 7 pass / 1 warn /
1 fail, `--revert` xác minh "Would revert 44000 claims". Tạo recovery tag `t83-complete-20260911`
(chống staged deletions agent ngoài trong index).

**Đính chính docs:** `assertion_level` KHÔNG phải "invented" (note cũ sai) — SCHEMA_DESIGN M2.2
định nghĩa Enum học hàm người review `cu_nhan/cao_hoc/tien_si` (T100); bot bootstrap không có
học hàm → metric này **HITL-by-design** (chỉ nạp khi Admin review qua UI). Đã sửa task file T83.

## 1. Chạy T83 run 2 (4000 claims)

```bash
python scripts/t83_bootstrap_review.py --auto --review --limit 4000
```

| Metric | Run 1 (0938c253) | Run 2 (sau) |
|---|---|---|
| Verified | 5,000 (1.12%) | **9,000 (2.01%)** |
| Reviewed | 5,000 (1.12%) | **9,000 (2.01%)** |
| Unverified | 442,885 | 438,885 |
| T83_auto reviewed | 5,000 | 9,000 |
| Audit log (review) | 5,000 | 9,000 |

`--revert` xác minh hoạt động (dry-run "Would revert 9000 claims").

## 2. Compliance meter (T113) — `scripts/verify_design_compliance.py`

```
[OK] data/design_compliance.json — 9 metric (pass=7 · warn=1 · fail=1) · 136 bảng
claims_with_source      100.00%  pass   (goal>=100.0)
claims_with_confidence  100.00%  pass   (goal>=100.0)
claims_reviewed           2.01%  pass   (goal>=1.0)    ← WARN→PASS (trước 0%)
claims_verified           2.01%  pass   (goal>=1.0)    ← WARN→PASS (trước 0%)
claims_assertion_level    0.00%  fail   (goal>=1.0)    (chưa fill — hiện trạng thật)
claims_with_audit       100.00%  pass   (goal>=100.0)
events_provenance       100.00%  pass   (goal>=100.0)
conflicts_resolved        0.01%  warn   (goal>=1.0)
glossary_vi_coverage     75.54%  pass   (goal>=75.5)
```

**So với baseline T108 (0% reviewed/verified):** 2 fail → pass. Alert #4 (claims 100%
unverified, T100) đã đóng. Còn 1 fail = `assertion_level` (0% — cần design quyết định,
KHÔNG fill tự động). Conflicts warn 0.01% — chờ admin review (T83 Lớp 3).

## 3. Files thay đổi session này

- `scripts/t83_bootstrap_review.py` (fixed source_id JOIN từ run 1 — numeric id)
- `docs/sessions/2026-09-11_t83-run2-compliance.md` (file này)
- `docs/tasktodo.md` (đồng bộ T83/T113/T116 trạng thái thật)
- `docs/SCHEMA_FREEZE.md` (§5 entity_claims — từ run 1)
- `dashboard/dashboard_process.html` (regen)

## 4. Revert

- **Code:** `git revert <build hash>` (nếu build commit chưa pushed) — hoặc revert commit đơn lẻ.
- **DB:** `python scripts/t83_bootstrap_review.py --revert` → trả 9,000 claims về `unverified` + xóa audit log tương ứng.
- **Compliance JSON:** regen lại bằng `verify_design_compliance.py`.

## 5. Việc kế tiếp (đề xuất)

1. 🔴 **Cần Lee quyết định:** index đang có staged deletions của agent ngoài
   (SCHEMA_FREEZE.md, t83_bootstrap_review.py, t55a_topic_clusters.py, 7 session docs, app.py revert T55c).
   Nếu agent ngoài commit → các file này biến mất khỏi master. Đề xuất agent ngoài `git reset` staged trước khi build thêm.
2. T113 `assertion_level` fail — chưa có design cho auto-fill; task riêng khi Lee duyệt.
3. Conflicts 40,321 open — chờ admin review (UI admin/conflicts.html đã có từ T109).
4. Blocked tasks vẫn chờ key: T74 (Gemini), T74b (Claude), T50 (Groq).