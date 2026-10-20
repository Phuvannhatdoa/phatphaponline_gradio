# Session 2026-09-27 — T166 Phase 5: Security Fix + TaskDone Closure

**Task:** T166 Canonical Identity Hard Guard  
**Phase:** 5 (final)  
**Status after session:** ✅ DONE

---

## Công việc thực hiện

### 1. Security fix — `admin_namevi_map_delete` (STOP #4)

**Bug:** `POST /daoanh/api/admin/namevi-map/delete` không có auth check → bất kỳ request không xác thực cũng có thể xóa rows `name_vi_map` (LOCKED authority source).

**Fix áp dụng** vào `app.py` trước `data = request.get_json()`:

```python
def admin_namevi_map_delete():
    # T166 §7.1 — BẮT BUỘC verify_session (xóa LOCKED authority source).
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.get_json()
```

`admin_namevi_map_update` (route cùng nhóm) đã có `verify_session` từ Phase 2+3 — nay `admin_namevi_map_delete` đồng bộ.

### 2. Verify sau fix

- `pytest` (daoanh/): **117/117 PASS** (174s)
- `npm run audit:t166`: **PASS 0 FAIL** (1 WARN pre-existing inline Gemini key)
- `npm run guard`: PASS

### 3. TaskDone closure

| File | Thay đổi |
|------|----------|
| `docs/Mimo-Flash/X-T166-canonical-identity-guard.md` | `status: in_progress → done`; session log Phase 5 thêm vào |
| `docs/tasktodo.md` | T166-build `🚧 IN_PROGRESS (2026-09-25→26` → `✅ DONE (2026-09-25→27`; "Còn (Phase 4/5)" cập nhật completion note |
| `docs/ROLLBACK.md` | Thêm row security fix (placeholder SHA → hash-fill sau commit) |
| `data/progress_data.json` | Regen qua `python scripts/build_progress_data.py` |
| `docs/sessions/2026-09-27_t166-security-taskdone.md` | File này |

---

## Scope giới hạn

- **Không** commit `app.py` riêng (CẤM theo T166 spec — `app.py` WIP 21.232 dòng, admin decision riêng).
- E2E live + `admin/app.py` mirror = VPS-only, verify trên next deploy.
- BUG-016 fix (places.html `dtHighlightSurface`) = task riêng, agent a668c31e (hoàn thành cùng session).

---

## Revert

```
git revert --no-edit aaf32529ef3a0de139d22621fe9409d2f3738ae0
```

Khôi phục docs closure (ROW ROLLBACK + X-T166 status + session log). Lưu ý: **code fix `verify_session` ĐÃ commit trong `6b82ced` (T181 cuốn theo WIP security)** — không có commit code riêng; revert code riêng = `git revert --no-edit 6b82ced` (sẽ cuốn cả T181).
