# Audit / Bug Fix Report — T381_YFORK_LEGEND_API_404_FIX

> Follow-up fix cho T381 (dharma lineage 3-source Y-fork), mục LỖI 1 + LỖI 3
> trong `daoanh/tasks/T381-build-dharma-lineage-3sources.md`
> (phần "## FOLLOW-UP FIX (2026-10-14) — 3 lỗi từ daoanh-qa report").
> LỖI 2 (chiều lên chỉ hiện 1 thầy) KHÔNG đụng vào — deferred theo quyết định admin.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| LỖI 1 — Data | `daoanh/places.html` — legend tĩnh HTML (dòng 565-607 vùng cũ) |
| LỖI 1 — Renderer | `_t381RenderYForkLegend(treeStatus)` — `places.html` ~dòng 6501-6515 |
| LỖI 3 — API endpoint | `GET /daoanh/api/monk/<dila_id>/lineage-tree` |
| LỖI 3 — Resolver | `app.py`, hàm `api_monk_lineage_tree`, ~dòng 6549-6564 |
| Schema contract | Trả 404 JSON khi không tìm thấy, 200 JSON khi tìm thấy — không có `ttl_persons` table trong `data/lineage.db` thực tế |

## 2. Root cause (đã xác minh)

### LỖI 1 — renderer + nội dung tĩnh sai
- **Lớp gây lỗi:** renderer (hiện/ẩn) + data tĩnh (nội dung chú thích sai trong HTML).
- **Trạng thái khi bắt đầu:** hàm JS `_t381RenderYForkLegend` đã có sẵn `box.style.display = 'block'` không điều kiện (đã được sửa từ một lượt trước, không rõ do ai) — phần này **đã đúng**, không cần sửa thêm.
- **Phần còn sai, đã xác minh và sửa:**
  1. Thẻ HTML tĩnh `<div id="lineage-yfork-legend" style="display:none" ...>` (dòng 586 cũ) vẫn còn `display:none` — khiến legend bị ẩn ngay cả khi JS set `'block'` nếu có CSS specificity/race-condition nào đó, và rõ ràng sai với ý đồ "luôn hiện". Đã xóa inline style này.
  2. 2 dòng chú thích tĩnh cũ "Nét liền vàng — ≥2 nguồn xác nhận" và "Nét đứt cam — 1 nguồn" (dòng 568-574 cũ) không khớp bảng màu T381 thực tế (vàng = Marcus-only DASHED chứ không phải liền; không có màu "cam" nào trong 4 màu Y-fork thật: xanh lá/tím/vàng đứt/xanh dương đứt). Đã xóa 2 dòng này.

### LỖI 3 — crash 500 khi bảng không tồn tại
- **Lớp gây lỗi:** resolver (thiếu try/except quanh fallback query).
- **Nguyên nhân chính xác:** code gốc gọi `conn.execute("SELECT 1 FROM ttl_persons WHERE id=?", ...)` làm fallback khi không tìm thấy trong `people`, không bọc try/except riêng. Đã xác minh bằng query trực tiếp: bảng `ttl_persons` **không tồn tại** trong `data/lineage.db` thực tế (`sqlite3.operationalerror: no such table` nếu gọi thẳng). Không bắt riêng lỗi này sẽ rơi xuống `except Exception` chung cuối hàm → trả 500 kèm lộ message nội bộ, thay vì 404 đúng ngữ nghĩa "không tìm thấy".
- **Trạng thái khi bắt đầu:** code try/except đã có sẵn trong file (bọc `sqlite3.OperationalError`, bắt đúng chuỗi "no such table", trả 404 JSON sạch) — đã đúng theo yêu cầu, không cần sửa thêm. Chỉ xác minh lại bằng test thực tế (xem mục 6).

## 3. Data/API contract trước → sau

| | Trước (mô tả trong task, lỗi) | Sau (đã xác minh bằng test) |
|--|-------|-----|
| Legend `places.html` | `display:none` tĩnh + 2 dòng chú thích sai (vàng liền/cam đứt) | Không còn `display:none`; chỉ còn 2 dòng chú thích đúng cho "Chú thích màu nét" (ancestor spine, candidate) + legend Y-fork riêng luôn hiện với 4 màu đúng |
| `GET /daoanh/api/monk/zzz-not-exist/lineage-tree` | 500 Internal Server Error (nếu không bắt `sqlite3.OperationalError`) | **404**, body `{"error": "Không tìm thấy tăng nhân (person not found)", "ok": false}` |
| `GET /daoanh/api/monk/A000005/lineage-tree` | 200 (không đổi) | **200**, `ok:true, nodes:10, edges:9, tree_status:{divergence_count:0, has_divergence:false}` — không regression |

## 4. Files changed

- `daoanh/places.html`
  - Xóa `style="display:none"` khỏi `<div id="lineage-yfork-legend" ...>`.
  - Xóa 2 dòng chú thích sai ("Nét liền vàng — ≥2 nguồn xác nhận", "Nét đứt cam — 1 nguồn") trong block "Chú thích màu nét", thêm comment giải thích lý do xóa.
  - Hàm `_t381RenderYForkLegend` — không sửa (đã đúng sẵn: `box.style.display = 'block'` không điều kiện theo `hasDiv`).
- `daoanh/app.py`
  - Hàm `api_monk_lineage_tree` — không sửa thêm (try/except `sqlite3.OperationalError` quanh query `ttl_persons` đã có sẵn và đúng theo yêu cầu). Chỉ xác minh lại bằng test thực tế.

## 5. Migration / import / dry-run / rollback

- Không chạm DB/schema. Không cần migration.
- File `places.html` đã backup sẵn tại `daoanh/docs/sessions/2026-10-14/places.html.before_t381_revised` (có sẵn từ trước, không tạo lại).
- `app.py` không có thay đổi mới trong lượt này (code đã đúng sẵn) nên không phát sinh thêm bản backup.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| `python -m py_compile app.py` | — | Không lỗi | Không lỗi | ✅ |
| Kiểm tra cú pháp JS trong `places.html` | parse từng `<script>` block bằng `new Function()` | Không lỗi | `ALL_SCRIPTS_OK` | ✅ |
| API — ID rác | `GET /daoanh/api/monk/zzz-not-exist/lineage-tree` (qua HTTP thật, server local `python app.py` + `local_gateway.py` + `server.py`, 127.0.0.1) | HTTP 404, JSON `{ok:false, error:...}` | `HTTP_404`, `{"error":"Không tìm thấy tăng nhân (person not found)","ok":false}` | ✅ |
| API — ID hợp lệ (regression) | `GET /daoanh/api/monk/A000005/lineage-tree` (HTTP thật) | HTTP 200, dữ liệu cây như cũ | `HTTP_200`, trả đủ `center`, `nodes`, `edges`, `tree_status` | ✅ |
| Xác minh bảng `ttl_persons` thật sự không tồn tại | `SELECT name FROM sqlite_master WHERE name='ttl_persons'` trên `data/lineage.db` | Không có bảng (chứng minh bug có thật) | `False` | ✅ |
| Browser thật — legend case có divergence | Mở `places.html` qua `http://127.0.0.1:8080`, chọn tăng nhân `A038890` (Mã Tổ Đạo Nhất) qua `selectPerson()`, vào tab 🌳 Truyền Thừa | Legend Y-fork hiện sẵn, đủ 4 màu, có dòng cảnh báo "⚠ Y-fork: N cạnh phân kỳ..." | Legend hiện đúng; cảnh báo "Y-fork: 2 cạnh phân kỳ nguồn trong pháp hệ đang xem..." hiện đúng; "Chú thích màu nét" chỉ còn 2 dòng đúng (không còn "vàng liền"/"cam đứt") | ✅ |
| Browser thật — legend case KHÔNG divergence | Chọn tăng nhân `A000005` (toàn cạnh consensus, `has_divergence=false` theo API) | Legend vẫn hiện (không bị ẩn dù không có phân kỳ) | Legend hiện đủ 4 màu, không có dòng cảnh báo (đúng vì không divergence) | ✅ |
| Regression route khác | Trang chính `places.html` load bình thường, tab Nhân Vật, tìm kiếm, bản đồ GIS | Không vỡ layout/chức năng khác | Không phát hiện vỡ layout trong quá trình test tay (ảnh chụp kèm) | ✅ (quan sát thủ công, chưa chạy full regression suite) |

**Ghi chú môi trường:** server local khởi động lần đầu mất ~394s cho `_build_cate_ids_map()` + ~56s cho lexicon load (do ổ đĩa backup E: chậm) — không liên quan đến 2 bug này, chỉ là đặc thù môi trường dev local.

## 7. Limitation / data gap còn lại

- LỖI 2 (chiều lên chỉ hiện 1 thầy) vẫn giữ `deferred`, không đụng theo đúng phạm vi đã xác nhận.
- Dòng 6714 (ancestor-spine) và 6780 (root-ancestor) trong `app.py` có lỗi tương tự LỖI 3 (thiếu try/except quanh query có thể lỗi "no such table") nhưng **ngoài phạm vi lần fix này** — chưa sửa, cần task riêng.
- Chưa chạy full regression suite tự động (nếu có) cho toàn bộ `places.html` — chỉ test tay các luồng liên quan trực tiếp đến 2 bug.
- Việc phụ "cập nhật số liệu trong `docs/sessions/2026-10-14/T381_EXECUTION_LOG.md`" (phần "Việc phụ" trong task) **chưa làm** trong lượt này — nằm ngoài yêu cầu rõ ràng của prompt (chỉ yêu cầu LỖI 1 + LỖI 3).
