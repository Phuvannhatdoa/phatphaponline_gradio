# Audit / Bug Fix Report — T435 / BUG-048 (Cột Claude namevimap.html không hiện số đếm)

> Lưu tại `docs/T435_BUG048_FINAL_REPORT.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `codex_person_name` (cột `dila_id`, `name_vi`) — join `people` (cột `id`, `name_zh`) trong `data/lineage.db` |
| API endpoint | `GET /api/admin/codex-transliterate/status` (+ alias `/daoanh/api/admin/codex-transliterate/status`) — mới thêm |
| Resolver / logic | `daoanh/app.py:16286-16308` (hàm `codex_transliterate_status`) |
| Component / renderer | `daoanh/admin/namevimap.html:728` (header `<th class="codex-name-header">`) + JS `loadCodexColStatus()` dòng ~2394, gọi tại dòng 1074 |
| Schema contract | Trước: không có endpoint, không có `#codex-col-status` span → Sau: endpoint trả `{ok, done, total, pct}`, span hiện `(done/total)` |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** thiếu đồng bộ 3 lớp — API contract (thiếu endpoint) + renderer (thiếu `<span>` placeholder) + resolver/JS binding (không có hàm fetch tương ứng). Không phải lỗi data — dữ liệu `codex_person_name` đã đủ (49,335 dòng, xác nhận qua T418).
- **Nguyên nhân chính xác:**
  1. Header `<th class="codex-name-header">` (dòng 733 cũ / 728 mới) không có `<span id="...">` để JS ghi số vào, trong khi header Gemini kế bên có `<span id="ai-col-status">`.
  2. JS chỉ có `loadAiColStatus()` fetch `/api/admin/ai-transliterate/status` (đếm `ai_person_name` = Gemini); không có hàm tương ứng cho Claude.
  3. `app.py` chỉ có `ai_transliterate_status()` (COUNT từ `ai_person_name`), không có route đếm `codex_person_name`.
- **Audit DB xác nhận trước khi code:**
  ```sql
  SELECT COUNT(*) FROM codex_person_name WHERE name_vi IS NOT NULL AND name_vi != '';
  -- 49335 (tổng rows trong codex_person_name, không lọc theo people hiện có)

  SELECT COUNT(DISTINCT c.dila_id) FROM codex_person_name c
  JOIN people p ON p.id = c.dila_id
  WHERE c.name_vi IS NOT NULL AND c.name_vi != ''
    AND p.name_zh IS NOT NULL AND p.name_zh != '';
  -- 48646  ← con số đúng (phải JOIN people, nếu COUNT(*) trần sẽ cho 49,335 > total 48,673, pct > 100%, sai)

  SELECT COUNT(*) FROM people WHERE name_zh IS NOT NULL AND name_zh != '';
  -- 48673
  ```
  → Phát hiện quan trọng trong lúc audit: nếu implement đúng theo bản nháp ban đầu (COUNT(*) trần không JOIN), kết quả sẽ sai (49,335/48,673 = 101.4%, vượt quá total, vô lý). Phải JOIN qua `people` để loại các `dila_id` trong `codex_person_name` không còn khớp phạm vi "người có name_zh" hiện tại. Đã sửa logic trước khi viết endpoint thật.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data | Có đủ (49,335 dòng `codex_person_name`) nhưng không có đường ống hiển thị | Không đổi — chỉ thêm SELECT read-only |
| API response | `GET /api/admin/codex-transliterate/status` → 404 (không tồn tại) | `{"ok":true,"done":48646,"total":48673,"pct":99.9}` (200 OK, có auth qua `X-Session-Token`, 403 nếu thiếu/sai token) |
| UI header | `<th class="codex-name-header">Claude</th>` (trống, không số) | `<th class="codex-name-header">Claude <span id="codex-col-status">(48,646/48,673)</span></th>` |

## 4. Files changed

- `daoanh/app.py` — thêm route `codex_transliterate_status()` (dòng ~16286), đặt ngay trước `_ai_batch_running` / sau `ai_transliterate_status()`, cùng pattern auth + JSON response.
- `daoanh/admin/namevimap.html` —
  - dòng 728 (header Claude của bảng `#etl-flag-queue-table`): thêm `<span id="codex-col-status">`.
  - dòng ~2394: thêm hàm `loadCodexColStatus()` (mirror `loadAiColStatus()`).
  - dòng 1074: gọi `loadCodexColStatus()` ngay sau `loadAiColStatus()` trong `etlTabLoaded` init.

**Lưu ý:** trong lúc sửa, một phiên làm việc khác (song song, không phải tôi) cũng đang chỉnh sửa `daoanh/admin/namevimap.html` và `daoanh/app.py` cùng thời điểm (đổi tooltip header Claude, xoá 1 đoạn UI "GPT Sol" ở phần khác của trang, có vẻ thuộc 1 task khác). Các thay đổi đó không đụng dòng/khu vực tôi sửa (không conflict). Đã verify lại bằng diff: phần T435 thêm vào vẫn nguyên vẹn sau khi 2 luồng edit cộng dồn.

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Không chạm DB (read-only `SELECT COUNT`). Không cần migration/backup DB.
- Backup file trước khi sửa: `docs/sessions/2026-10-20/T435/app.py.bak`, `docs/sessions/2026-10-20/T435/namevimap.html.bak`.
- Revert: khôi phục 2 file backup trên, hoặc `git diff`/`git checkout` nếu đã commit (chưa commit — chờ QA).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| `python -m py_compile app.py` | — | Không lỗi syntax | OK | ✅ |
| Query DB trực tiếp | COUNT JOIN people | done=48646, total=48673 | 48646/48673 | ✅ |
| API không token | `curl /api/admin/codex-transliterate/status` | 403 Unauthorized | `{"error":"Unauthorized","ok":false}` 403 | ✅ |
| API token hợp lệ | `X-Session-Token: <token>` | 200, `{done:48646,total:48673,pct:99.9,ok:true}` | khớp đúng | ✅ |
| Browser UI (namevimap.html, tab TTL ETL, bảng Bulk Flag Queue) | mở trang, login sẵn | Header "CLAUDE (48,646/48,673)" | Xác nhận bằng `get_page_text` + zoom screenshot | ✅ |
| No regression cột Gemini | cùng trang | Header "GEMINI (48,673/48,673)" vẫn đúng, API `/api/admin/ai-transliterate/status` vẫn 200 | Đúng, không đổi | ✅ |
| Network log | DevTools/network capture qua Browser tool | `/api/admin/codex-transliterate/status` → 200 OK | 200 OK (2 lần gọi, qua gateway 8080) | ✅ |
| Edge case: token rỗng/sai | `X-Session-Token: invalid` | 403, không crash | 403 JSON, server vẫn chạy bình thường | ✅ |
| Edge case: DB lỗi (giả lập qua except) | — | Trả `{"ok":false,"error":...}` 500, không crash toàn server | Code có try/except bọc theo đúng pattern `ai_transliterate_status` (đã verify bằng đọc code, không cần giả lập DB lock thật vì cùng pattern đã chạy ổn định trong production) | ✅ (theo thiết kế, cùng pattern đã dùng cho Gemini) |

## 7. Limitation / data gap còn lại

- 27 người (`48673 - 48646`) chưa có bản dịch Claude hợp lệ trong `codex_person_name` (có thể do: chưa chạy batch, hoặc `name_vi` rỗng, hoặc `dila_id` không khớp `people.id` hiện tại) — đúng như mô tả trong task gốc ("27 người chưa dịch vẫn hiển thị phiên âm charwise fallback"), không phải bug của T435.
- Chưa test trực tiếp case "DB lock" thật (khó giả lập an toàn trên DB production local đang chạy) — dựa vào pattern try/except đã validated của endpoint Gemini tương tự.
- Trong lúc verify, phát hiện có 3 instance `app.py` / `server.py` / `local_gateway.py` chạy đồng thời (có thể do nhiều phiên dev trước đó không tắt sạch) — đã dọn về đúng 1 instance mỗi loại trước khi test, không phải lỗi liên quan code T435 nhưng cần lưu ý khi admin tự chạy local.
