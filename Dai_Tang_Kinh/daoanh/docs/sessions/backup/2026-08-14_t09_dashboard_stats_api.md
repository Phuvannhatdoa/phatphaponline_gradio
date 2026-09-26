# Session: T09 — Dashboard stats API 404 fix

**Ngày:** 2026-08-14
**Module:** Hạ tầng / Docs
**Task:** `tasks/T09-dashboard-stats-api.md` (tasktodo #9)

---

## Mô tả ngắn task

Docs/tasktodo ghi trang `/daoanh/admin/` gọi `/api/admin/dashboard/stats` nhưng trả **404**.
Yêu cầu: `GET /daoanh/api/admin/dashboard/stats` trả **200 JSON thật** (counts từ DB).

## Điều tra (root cause)

- `app.py:6057` đã có route `/api/dashboard/stats` + `/daoanh/api/dashboard/stats`
  → `GET /daoanh/api/dashboard/stats` vốn đã **200** (dữ liệu thật).
- UI thật (`admin/index.html:566`) gọi `${API_BASE}/api/dashboard/stats` với `API_BASE='/daoanh'`
  → UI thực tế hoạt động, không phải nguồn 404.
- **Thiếu** alias có segment `/admin/` mà docs claim: `/api/admin/dashboard/stats` + `/daoanh/api/admin/dashboard/stats` → **404**.

## Thiết kế / giải pháp đã chọn

Giữ nguyên logic cũ (Code Preservation — không đổi schema, không thêm bảng, không đụng pipeline).
Chỉ thêm **2 alias route decorator** vào hàm `api_dashboard_stats()` hiện có:

```python
@app.route('/api/dashboard/stats', methods=['GET'])
@app.route('/daoanh/api/dashboard/stats', methods=['GET'])
@app.route('/api/admin/dashboard/stats', methods=['GET'])          # alias mới
@app.route('/daoanh/api/admin/dashboard/stats', methods=['GET'])   # alias mới
def api_dashboard_stats():
```

Hàm trả counts thật từ `lineage.db`: people, marcus_networks, name_vi_map, namevi_map_places, places_pending, TTL queue/master.

## File đã tạo / sửa

| File | Thay đổi |
|------|----------|
| `app.py` (line ~6057) | Thêm 2 alias route decorator |
| `docs/sessions/2026-08-14_t09_dashboard_stats_api.md` | Tạo (file này) |
| `docs/tasktodo.md` | Đánh dấu Task #9 ✅, đổi 404 → 200 |
| `tasks/T09-dashboard-stats-api.md` | Tick toàn bộ acceptance criteria, `status: pending → done` |
| `docs/progress.md` | Cập nhật dòng Dashboard `/daoanh/admin/` |
| `dashboard/handoff.md` | Thêm log phiên |

## Cách chạy / test

```powershell
# Khởi động stack
python app.py            # :5000
python server.py         # :5001
python local_gateway.py  # :8080

# Verify
Invoke-WebRequest 'http://localhost:5000/daoanh/api/admin/dashboard/stats'  # 200
Invoke-WebRequest 'http://localhost:5000/daoanh/api/dashboard/stats'        # 200
Invoke-WebRequest 'http://localhost:8080/daoanh/api/admin/dashboard/stats'  # 200 (qua gateway)
Invoke-WebRequest 'http://localhost:8080/daoanh/api/dashboard/stats'        # 200 (qua gateway)
```

## Kết quả test

- ✅ 5/5 path trả **200**: `/api/admin/dashboard/stats`, `/daoanh/api/admin/dashboard/stats`, `/daoanh/api/dashboard/stats` trên cả :5000 và :8080.
- ✅ JSON thật (qua gateway:8080):
  ```json
  {"dila_total":48673,"marcus_coverage":23.2,"marcus_edges":11169,"marcus_in_dila":11297,
   "marcus_monks":11300,"namevi_auto":2,"namevi_coverage":105.1,"namevi_places_total":176783,
   "namevi_reviewed":1,"namevi_total":51141,"namevi_with_dila":46272,"namevi_with_marcus":271,
   "ttl_master":0,"ttl_queue":16}
  ```
- ✅ Syntax check app.py: `python -c "import ast; ast.parse(...)"` → OK
- ✅ E2E: `node scripts/e2e-test.js` → PASS

## Ghi chú

- Toàn bộ stack (5000/5001/8080) đã restart lại (các tiến trình cũ chết bất ngờ trong phiên).
- `namevi_coverage` = 105.1% (name_vi_map 51,141 / people 48,673 > 100%) — do nguồn data khác nhau, không phải lỗi route; giữ nguyên behavior cũ.
- Không có thay đổi schema DB / pipeline → không cần cập nhật `db_schema.md`, `pipelines.md`, `translation_workflow.md`.
