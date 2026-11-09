# Bàn giao 2026-10-28 — T479 tách app.py

## 1. Đọc trong 2 phút
- `app.py` đã tách xong ở local và đã deploy code lên VPS (service `daoanh-api` active, không restart lại).
- `app.py` cũ (1,25 MB) không còn; logic nằm ở các module dưới. CodeGraph index được toàn bộ route.
- Việc còn lại trước khi báo DONE: QA chưa đạt hoàn toàn (xem mục 4), và Admin xác nhận DONE.

## 2. Cấu trúc mới (đều ở thư mục `daoanh/`)
| File | Vai trò | Kích thước |
|---|---|---|
| `app.py` | Bootstrap: import `core`, import các `routes_*`, đăng ký blueprint T265, `__main__` | ~4 KB |
| `core.py` | Cấu hình, helper, cache, `app = Flask(...)`, CORS, lệnh chạy lúc import | ~358 KB |
| `routes_lineage.py` | Route lineage/monk/person/dila/nexus | ~246 KB |
| `routes_places.py` | Route places | ~177 KB |
| `routes_translate.py` | Route dịch, cbeta, passage | ~237 KB |
| `routes_namevi.py` | Route namevi/lexicon/hanviet | ~51 KB |
| `routes_ttl.py` | Route TTL/ontology | ~12 KB |
| `routes_misc.py` | Route khác | ~142 KB |
| `routes_pages.py` | Trang HTML/dashboard | ~15 KB |
| `t265_routes.py` | Blueprint T265 (import CSV) | nhỏ |
| `db_core.py` | `get_db_connection()` (import vòng nếu để trong core) | nhỏ |

## 3. Quy tắc cho agent dev tiếp
- **Thêm route mới:** viết trong `routes_<nhóm>.py` tương ứng, dùng `@app.route` (import `app` từ `core`). Không thêm route vào `app.py`.
- **Sửa helper/cache dùng chung:** sửa trong `core.py`. Không gán lại biến toàn cục từ module khác: mọi `global` phải nằm trong `core.py`.
- **Import từ module khác:** dùng `import core` hoặc `from core import X`. Không dùng `import app` để lấy thuộc tính (thuộc tính đã chuyển sang `core`).
- **Không sửa tay file sinh ra từ tách:** nếu cần đổi cấu trúc, xem `docs/sessions/2026-10-27/split-app/split.py` và bản gốc `app.py.pilot-state`.

## 4. Đã kiểm chứng và còn lại
Đã kiểm chứng:
- Bảng route tĩnh: 352 = 352 (không thiếu, không thừa).
- URL map runtime: 381 rule khớp baseline.
- 159/163 response GET giống hệt; 4 khác do dữ liệu động (`/api/health`, `ttl_v2/schema`, `public/counter`, `missing-hanzi`).
- `python app.py` khởi động sạch trên local và VPS; lineage 200, health 200.
- Test: t100, t235, t236, t237, t243, t165, t158, t178 pass (101 + 23 + 20 test trong các nhóm).

Còn lại (chưa sửa):
- Một số script vẫn đọc văn bản `app.py` để tìm route/hàm, kết quả có thể sai mà không báo lỗi: `scripts/build_progress_data.py` (ảnh hưởng số liệu dashboard), `scripts/t166_identity_audit.py`, `scripts/t130_t131_audit.py`, `scripts/t172_build_charmap.py`, `scripts/t50_passage_vi_backfill.py`, `scripts/fix_t162_namevi.py`, `scripts/t207_fix_db_mojibake.py`, `scripts/build_tab_readiness.py`, cùng một số file gốc.
- Test `test_t259`, `test_t260`, `test_t261`, `test_t262`, `test_t238`, `test_t207` vẫn đọc `app.py` văn bản; chưa chạy lại.
- Chưa restart server 5000 trên local (đã restart; nếu có lỗi thì kiểm tra lại).
- Lỗi có sẵn từ bản gốc, chưa sửa (cần sửa riêng): các tên chưa định nghĩa `_j`, `bio`, `lineage_master`, `lineage_source`, `name_vi`, `new_code` ở một số nhánh code (xem pyflakes).
- `test:gov` và `dup:ids` đang fail vì lý do khác (dữ liệu DB, ID trùng), không liên quan tách.

## 5. Lệnh kiểm tra nhanh
```bash
cd daoanh
python -X utf8 -m py_compile app.py core.py routes_*.py t265_routes.py db_core.py
python -X utf8 -c "import app; print(len(list(app.app.url_map.iter_rules())))"   # kỳ vọng 381
python -X utf8 -m pytest tests/test_t165_phase8_pilot_gate.py tests/test_t158_consensus.py tests/test_t178_gap_d3.py -q
```

## 6. Revert
- Bản gốc trước tách: `docs/sessions/2026-10-27/split-app/app.py.pilot-state` (trạng thái sau pilot T265) và `app.py.bak-before-split` (trước pilot).
- Để quay lại: chép bản gốc đè `app.py`, xóa `core.py`, `routes_*.py`, `db_core.py` (giữ `t265_routes.py` nếu muốn), restart `app.py`.

## 7. Ghi chú
- Task: `tasks/T479-split-app-py-blueprints.md`, trạng thái `in_progress` cho đến khi Admin xác nhận DONE.
- Snapshot và công cụ kiểm chứng nằm trong `docs/sessions/2026-10-27/split-app/` (`snapshot.py`, `route_inventory.py`, `baseline_pilot.json`, `after_split.json`).
- Các lần kiểm tra GET có thể làm tăng `data/counter.dat` và tạo profile trong `ttl_v2/schema`.
