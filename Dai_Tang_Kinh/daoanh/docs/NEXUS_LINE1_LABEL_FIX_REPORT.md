# Audit / Bug Fix Report — NEXUS Line-1 Label Việt (PL000000023255)

> Báo cáo fix bug label Nexus theo skill `daoanh-data-ui-debug` (audit trước, fix sau — đúng qui trình).
> Slug: `nexus_line1_label_fix` — lưu tại `docs/NEXUS_LINE1_LABEL_FIX_REPORT.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db` — `places_dila`, `namevi_map_places`, `people`, `marcus_reference`, `marcus_networks`, `event_text_link` |
| API endpoint | `GET /daoanh/api/nexus/<entity_id>?type=person|place` (`app.py:5101`) |
| Resolver / logic | `app.py:5101-5311` (api_nexus) — center label, event loop, node fill, marcus branch |
| Component / renderer | `daoanh/places.html` — `_renderVisGraph` (3394), `_nexusRenderGrouped` (5334), detail drawer (5567), header (5250) |
| Schema contract | trước: node `{id,label,label_zh,group,navigable}` — không có `label_vi`; sau: thêm `label_vi` |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** resolver (API contract phụ trợ — thiếu kênh `label_vi`).
- **Nguyên nhân chính xác:**
  1. Với root = **người**, node Line-1 "Truyền thừa Marcus" được thêm bằng
     `_add_node(oid, olbl, olbl, 'person', navigable=True)` (`app.py:5264`, `olbl` = `teacher_label`/`student_label`
     — **Hán thô từ marcus_networks**). Nhánh này chạy **SAU** vòng fill label (5209-5226) nên không bao giờ tra
     `people.name_vi` (đã **100% filled** — 48.673/48.673; docs cũ ghi 0% là lỗi thời) hay `marcus_reference.label_vi`
     (18.127 dòng filled) → Line 1 hiện Hán dù DB có Việt (22.335 row marcus đối chiếu được Việt).
  2. API không gửi kênh `label_vi` → UI header `nmp-name-vi` dùng `c.label_vi || c.label` (`places.html:5250`)
     luôn phải fallback; không có kênh "tên Việt ưu tiên" để renderer chọn đúng chuỗi quyết định.
- **Minh chứng:** API cũ trả Line-1 A001897 với `label='懷海'` (Hán) trong khi DB có
  `people.name_vi='Bách Trượng Hải'`, `marcus_reference.label_vi='Bách Trượng Hải'`.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data | Không đổi (0 ghi DB; read-only) | Không đổi |
| API response node | `{id,label,label_zh,group,navigable}` | `{..., label_vi}` — Việt ưu tiên: `people.name_vi` / `marcus_reference.label_vi` (person), `namevi_map_places.name_vi` (place) |
| API response center | `{id,label,label_zh}` | `{id,label,label_vi,label_zh}` |
| Line-1 Marcus (person root) | `label='懷海'` (Hán) | `label='Bách Trượng Hải'`, `label_vi='Bách Trượng Hải'`, `label_zh='懷海'` |
| UI fallback | `n.label || n.label_zh || n.id` | `_nexusSafeLabel(n)` = `label_vi || label || label_zh || id` (không bao giờ rỗng; text node giữ fallback sigla) |

## 4. Files changed

- `daoanh/app.py` — `api_nexus` (5101-5311):
  - center person/place: thêm `label_vi`.
  - `_add_node`: thêm tham số `label_vi` (default None, backward-compatible).
  - vòng fill place + person: ghi `label_vi` (person: `people.name_vi` → `marcus_reference.label_vi`).
  - nhánh marcus Line-1: lookup Việt qua `people LEFT JOIN marcus_reference`, label_vi ưu tiên, label_zh giữ gốc;
    node không có people row → giữ label gốc (synthetic `pers-*` không đổi — không có ID canonical).
- `daoanh/places.html` — thêm `_nexusSafeLabel(n)`; thay 7 điểm dùng fallback
  (raw center 3397, raw nodes 3403, grouped DILA/marcus/dynasty person 5382/5394/5470, text 5448 giữ sigla,
  detail title 5574); header 5250 giờ nhận `label_vi` thật từ API.
- `daoanh/docs/NEXUS_LINE1_LABEL_FIX_REPORT.md` — report này.
- `daoanh/docs/sessions/2026-09-06_nexus_line1_label_fix.md` — session log.
- `daoanh/docs/tasktodo.md` + `docs/progress.md` — cập nhật trạng thái.
- `daoanh/docs/rules/naming-and-identity.md` — sửa số liệu lỗi thời: `people.name_vi` = **100% filled** (2026-09-06).
- `daoanh/docs/ROLLBACK.md` — mục revert + ghi chú khôi phục ViQa bị revert vô tình ở T99.

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- **Không chạm DB** — fix thuần resolver + UI (read-only SQL trên `data/lineage.db`).
- Revert: `git revert <commitB>` (Nexus fix) — xem `docs/ROLLBACK.md`.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu — place root | `GET /daoanh/api/nexus/PL000000023255?type=place` | center `label_vi='Thiếu Lâm Tự'`, 24 person node label Việt + `label_vi`, groups = 3/24 | 17/17 assert (test_client, DB thật, read-only) | ✅ |
| Fallback — person root Line-1 Marcus | `GET /daoanh/api/nexus/A003623?type=person` (marcus teacher, DB thật) | Line-1 hiện Việt: `label_vi='Bách Trượng Hải'`, `label_zh='懷海'`; không node label rỗng | 8/8 assert — `A001897 → Bách Trượng Hải`, `A012760 → Vân Tú Thần Giám`, … | ✅ |
| Fallback — node không có people row / synthetic | `pers-{ev_id}` (entity_id NULL) | giữ `label` gốc (Hán), `label_vi=None`, navigable=false | đúng (không canonical ID → không tự dịch) | ✅ |
| Fallback — label rỗng (guard) | node thiếu label + label_zh | `_nexusSafeLabel` → canonical ID, không rỗng | ✓ (id cuối cùng; JS guard 5281 giữ nguyên) | ✅ |
| Kỹ thuật | py_compile / node --check / e2e / npm test | tất cả PASS | PY_COMPILE OK · NODE-CHECK OK (357.248 chars) · E2E ✅ · npm test ✅ | ✅ |

## 7. Limitation / data gap còn lại

- `people.name_vi` có 1 số giá trị chứa ký tự Hán hiếm (vd `Mã 𥳽 Kia`) — hiển thị như dữ liệu gốc, không tự dịch (đúng rule).
- `marcus_reference.label_vi` chỉ filled 18.127/… → node nào thiếu sẽ rơi về `people.name_vi`/Hán (đúng chuỗi fallback).
- Dynasty subgroup label vẫn dùng `_DYNASTY_VI` 8 triều (陳/北齊/五代十國/北宋/印度 chưa map) — ngoài scope tên node;
  riêng 1 dynasty bẩn `'北宋\n    五代十國'` (data) cần clean riêng nếu admin duyệt.
- Server :5000 bị chiếm → chưa chụp ảnh live UI; verify qua logic + test client + node.