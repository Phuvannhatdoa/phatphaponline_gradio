# TESTER REPORT — T445 (Wizard UI B0–B9) — Second Verification

Người kiểm: Tester (Claude Code, chỉ đọc + sandbox). Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t445\Dai_Tang_Kinh\daoanh`.
Không sửa code/task/status, không ghi DB, không chạy `--apply`, không commit.

## Kết luận tổng

**FAIL — chưa đủ điều kiện chuyển sang DONE (Admin quyết).**
Các mục **core** (route naming, B2 dry-run, 501 stubs, WebSocket deviation doc) đã **PASS**.
Các mục **integration** (B1, B3, B4, B5/B8 real-time, B7, B9, resume, CSV HOME) **FAIL** vì phụ thuộc T444 backend chưa sẵn sàng và UI chưa hoàn thiện handler.

| # | Mục | Kết quả |
|---|-----|---------|
| 1 | Phạm vi diff | PASS (chỉ `app.py`, `placevn.html` trong phạm vi) |
| 2 | 11 route theo spec | **PASS** (2 tên chính + 2 alias đúng) |
| 3 | Ghi DB / dry-run | **PASS** (B2 dry-run mặc định, không auto-ALTER) |
| 4 | Giữ mã cũ | PASS (0 dòng xoá) |
| 5 | Cú pháp | PASS (app.py AST OK; placevn.html JS OK, JSX chưa kiểm offline) |
| 6 | Chạy sandbox API | PASS (tất cả route trả đúng mã, B2 dry-run/apply hoạt động) |
| 7 | done_when / phụ thuộc T444 | FAIL (7/11 checklist chưa tick; T444 pending) |
| 8 | Tester pipeline (lint/test/e2e) | PARTIAL (lint✓ e2e-static✓; test✗ e2e-runtime✗ — infra missing) |

---

## 1. Phạm vi diff — PASS

```
 M admin/placevn.html
 M app.py
```

Chỉ 2 file trong phạm vi task (`admin/placevn.html`, `app.py`, `docs/plans/...` — plan file đã có từ trước). Không có thay đổi ngoài phạm vi như lần trước (`tasks/T445...md`, `.opencode/agents/coder.md`, backup files).

---

## 2. Đếm route mới — PASS

| Spec (yêu cầu) | Route trong app.py | Dòng | Method | Ghi chú |
|---|---|---|---|---|
| backup | `/daoanh/api/admin/backup` | 25964 | POST | OK |
| fix-ids | `/daoanh/api/admin/fix-ids` | 25977 | POST | 501 stub |
| **load-schema** | `/daoanh/api/admin/load-schema` | 25983 | POST | **Primary** ✅ |
| (alias) | `/daoanh/api/admin/add-columns` | 25984 | POST | Alias cũ ✅ |
| load-dictionary | `/daoanh/api/admin/load-dictionary` | 26015 | POST | 501 stub |
| update-rules | `/daoanh/api/admin/update-rules` | 26020 | POST | 501 stub |
| approve-sample | `/daoanh/api/admin/approve-sample` | 26025 | POST | 501 stub |
| report | `/daoanh/api/admin/report` | 26030 | POST | 501 stub |
| export-csv | `/daoanh/api/admin/export-csv` | 26035 | GET | 501 stub |
| **batch-monitor** | `/daoanh/api/admin/batch-monitor` | 26041 | GET | **Primary** ✅ |
| (alias) | `/daoanh/api/admin/batch-status` | 26042 | GET | Alias cũ ✅ |

**Tổng 11 route** (9 logic + 2 alias). Đúng spec: `load-schema` và `batch-monitor` là tên chính; `add-columns`/`batch-status` giữ alias để UI cũ không vỡ.

---

## 3. Ghi DB / dry-run — PASS

### B2 `load-schema` (dòng 25983–26013)
- **Mặc định dry-run**: `apply = bool(data.get('apply'))` → `False` khi không truyền `apply=true`.
- **Không ALTER khi dry-run**: chỉ trả `action: "would_add"` cho cột chưa có.
- **Chỉ ALTER khi `apply=true`**: dòng 26000–26005, commit dòng 26008–26009.
- **Idempotent**: cột đã tồn tại → `action: "exists"`.
- **Trả chi tiết**: `{apply: false, columns: [{column, type, action: "would_add|exists|added|error"}]}`.

### Các route khác
- `backup`: ghi file backup (không ghi bảng) — OK.
- `fix-ids`, `load-dictionary`, `update-rules`, `approve-sample`, `report`, `export-csv`: **trả 501**, **không ghi DB**.
- `batch-monitor`: trả idle state, không ghi DB.

### Không có `--apply` global, không tự động ghi DB khi UI gọi B2 auto (UI B2 **không** auto-run, có 2 nút Dry-run/Apply do user click).

---

## 4. Giữ mã cũ — PASS

```
admin/placevn.html: +107 lines, -0 lines
app.py: +88 lines, -0 lines
```

Không xoá dòng nào (`git diff HEAD -- admin/placevn.html app.py | grep -c '^-[^-]'` = 0).

---

## 5. Kiểm cú pháp — PASS

| File | Kiểm tra | Kết quả |
|---|---|---|
| `app.py` | `python -X utf8 -c "import ast; ast.parse(...)"` | ✅ PASS (no syntax errors) |
| `admin/placevn.html` | `node -e "new vm.Script(js)"` cho 7 khối plain JS | ✅ PASS (7/7 OK) |
| `admin/placevn.html` | Khối `type="text/babel"` (JSX) | ⚠️ **Chưa kiểm offline** (cần E2E trình duyệt) |

---

## 6. Chạy sandbox API — PASS

Tạo Flask test client với DB tạm (`namevi_map_places` chỉ có `id, name_zh`):

```
POST /daoanh/api/admin/backup            -> 200 {"success":true, "backup_path":...}
POST /daoanh/api/admin/fix-ids           -> 501 {"success":false, "message":"chưa triển khai"}
POST /daoanh/api/admin/load-schema       -> 200 {"success":true, "apply":false, "columns":[{"column":"source","action":"would_add"},...]}
POST /daoanh/api/admin/load-schema?apply=true -> 200 {"success":true, "apply":true, "columns":[{"column":"source","action":"added"},...]}
POST /daoanh/api/admin/add-columns       -> 200 (alias, same behavior)
POST /daoanh/api/admin/load-dictionary   -> 501 {"success":false, "message":"chưa triển khai"}
POST /daoanh/api/admin/update-rules      -> 501 {"success":false, "message":"chưa triển khai"}
POST /daoanh/api/admin/approve-sample    -> 501 {"success":false, "message":"chưa triển khai"}
POST /daoanh/api/admin/report            -> 501 {"success":false, "message":"chưa triển khai"}
GET  /daoanh/api/admin/export-csv        -> 501 {"success":false, "message":"chưa triển khai"}
GET  /daoanh/api/admin/batch-monitor     -> 200 {"success":true, "step":"idle", "progress":0, ...}
GET  /daoanh/api/admin/batch-status      -> 200 (alias, same response)
```

Kết luận: 11 route tồn tại, method đúng, hành vi đúng spec.

---

## 7. done_when và phụ thuộc T444 — FAIL (không tự đánh đạt)

Checklist trong task (Verification Checklist, dòng 220–233):

| # | Mục | Trạng thái | Bằng chứng |
|---|-----|-----------|------------|
| 1 | Wizard modal render step 1/9 | ❓ **Chưa E2E** | Cần trình duyệt |
| 2 | Navigation Back/Next | ❓ **Chưa E2E** | Cần trình duyệt |
| 3 | B0 Backup → POST /backup | ✅ **Route OK** | Sandbox 200 |
| 4 | B1 Fix ID preview + CSV | ❌ **Stub 501** | Route trả 501; UI chỉ có nút "Run Fix IDs" không có preview/checkbox/CSV |
| 5 | B2/B3 auto-progress | ❌ **Không auto** | UI B2 có 2 nút Dry-run/Apply (user click); B3 nút "Auto Run" gọi 501 |
| 6 | B4 Rules form editable + save | ❌ **UI chỉ textarea** | Không có handler save; route 501 |
| 7 | B5 WebSocket real-time | ⚠️ **Polling thay WebSocket** | Spec: WebSocket; Thực tế: nút "Poll Status" gọi `/batch-monitor` GET; deviation đã doc |
| 8 | B7 Sample grid + Approve | ❌ **Stub 501** | UI chỉ nút "Approve Selected"; route 501 |
| 9 | B9 Report + CSV | ❌ **Stub 501** | UI chỉ link download; route 501; không có stats |
| 10 | Resume (localStorage) | ❌ **Chưa làm** | CODER-REPORT ghi "chưa làm" |
| 11 | CSV cho HOME team | ❌ **Chưa có data** | Cần B9 xong mới có |

**Phụ thuộc T444** (backend Gemini batch): `fix-ids`, `load-dictionary`, `batch-monitor` (data thật), `report`, `export-csv`, phần ghi thật của `update-rules`/`approve-sample` đều chờ T444. Các mục B1, B3, B5, B7, B8, B9 **không thể hoàn thiện** ở trạng thái hiện tại.

---

## 8. Tester Pipeline (lint/test/e2e) — PARTIAL

Chạy `node scripts/tester-agent.mjs`:

| Bước | Kết quả | Ghi chú |
|------|---------|---------|
| LINT | ✅ PASS | `npm run lint` → 0 lỗi |
| TEST | ❌ FAIL | `tests/run-tests.js` **không tồn tại** (infra missing) |
| E2E Static | ✅ PASS | `npm run e2e` → check HTML/JS static OK |
| E2E Runtime | ❌ FAIL | Playwright **chưa cài** (`@playwright/test` missing) |

> Lưu ý: 2 fail là **thiếu infra test** (file test runner, Playwright), không phải lỗi code T445. Nếu team có test infra, sẽ pass.

---

## 9. Đề nghị cho Admin (không tự thực hiện)

1. **Quyết định WebSocket vs Polling**: Spec yêu cầu WebSocket real-time (<100ms). Coder dùng polling + doc deviation. Admin cần quyết: (a) chấp nhận polling + cập nhật spec, (b) yêu cầu cài `flask-sock` làm WebSocket thật.
2. **T444 Backend**: 6/9 bước wizard (B1, B3, B5, B7, B8, B9) chờ T444. Cần ưu tiên T444 hoặc chấp nhận wizard chỉ có khung (scaffold) cho đến khi T444 xong.
3. **Resume (localStorage)**: Chưa làm. Cần add `localStorage.setItem('wizardStep', ...)` + restore on load.
4. **Test Infrastructure**: Cần tạo `tests/run-tests.js` (có thể placeholder) và `npm install @playwright/test` để pipeline xanh.
5. **E2E trình duyệt**: Khối JSX `type="text/babel"` cần kiểm trên browser thật trước khi Admin review.

---

## 10. Tóm tắt cho Admin review

| Việc đã xong (PASS) | Việc CHƯA xong (FAIL/Deferred) |
|---------------------|--------------------------------|
| ✅ Route naming đúng spec (load-schema, batch-monitor + aliases) | ❌ B1 Fix ID: preview, checkbox, CSV export |
| ✅ B2 dry-run mặc định, Apply tường minh | ❌ B3 Load Dictionary: auto-run nạp 2.446 từ |
| ✅ 6 stub trả 501 "chưa triển khai" (không success giả) | ❌ B4 Rules: form edit + save inline |
| ✅ WebSocket deviation doc trong code | ❌ B5/B8: WebSocket real-time (đang dùng polling) |
| ✅ Syntax check pass | ❌ B7: Sample 100 grid + filter + approve |
| ✅ UI B2: 2 nút Dry-run/Apply | ❌ B9: Stats + 3 CSV download |
| ✅ UI B5/B8: nút Poll Status + progress bar + log | ❌ Resume localStorage |
| | ❌ CSV cho HOME team |
| | ❌ E2E browser validation (JSX) |

**Khuyến nghị**: Task T445 ở trạng thái **"Scaffold Ready"** — khung xương sống sẵn sàng, sạch, không bug syntax, route đúng spec. Phần "thịt" (logic thật) chờ T444. Admin có thể:
- **Chuyển DONE phần scaffold** (nếu tách task: T445a = scaffold, T445b = integration T444), HOẶC
- **Giữ testing** chờ T444 xong rồi integrate end-to-end.

---

**Không đánh DONE.** Trạng thái do Admin quyết.