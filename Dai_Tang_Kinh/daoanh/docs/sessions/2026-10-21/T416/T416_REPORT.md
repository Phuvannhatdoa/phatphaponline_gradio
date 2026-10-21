# T416 — Tối ưu backend `/daoanh/api/public/autocomplete` (BÁO CÁO)

**Ngày:** 2026-10-21 · **Người làm:** coordinator (opencode) — *không giao được `daoanh-debugger`
qua Task tool (abort 2 lần), nên tự làm; ghi rõ lý do theo HARNESS_WORKFLOW.md.*
**Phạm vi:** chỉ sửa CODE `app.py` (route autocomplete). KHÔNG ghi DB.

## 1. Root cause (đo lại, xác nhận)

Profile cũ (2026-10-19) nói `sqlite_stat1` không tồn tại; **hiện đã tồn tại** (ANALYZE đã chạy),
nhưng planner vẫn chọn full-table SCAN cho `places_pending` khi LIKE `%q%`.

Đo từng query (chuỗi chậm `'Thiếu L'`, `'Nghĩa Huyền'`):

| Query | Không hint | Có `INDEXED BY idx_places_pending_name_zh` |
|---|---|---|
| `places_pending WHERE name_zh LIKE '%Thiếu L%'` | **1312 ms** | **137 ms** |
| `places_pending WHERE name_zh LIKE '%Nghĩa Huyền%'` | **1338 ms** | **75 ms** |
| `namevi_map_places WHERE name_vi LIKE ?` | 176–274 ms | (không có index trên `name_vi`) |
| `marcus_reference` | 24–118 ms | — |
| `lexicon WHERE term LIKE ?` | 203–218 ms | — |

→ Nút nghẽn chính = `places_pending` (176.783 dòng) bị SCAN.

## 2. Sửa (đề xuất B — code-only)

`app.py` route `public_autocomplete()`:
- Thêm helper `_t416_pending_index_hint(conn)` — kiểm `idx_places_pending_name_zh` tồn tại
  (cache 1 lần/process) để **an toàn khi DB khác thiếu index** (VPS) → không hint nếu thiếu.
- Chèn ` INDEXED BY idx_places_pending_name_zh` vào query `places_pending` khi index tồn tại.

Không đụng: query `namevi_map_places`/`marcus_reference`/`lexicon` (chưa có index phù hợp —
thêm index là DB write, cần Admin duyệt).

## 3. Kết quả đo (Flask test client, min–max 3 lần)

| Chuỗi | Trước | Sau |
|---|---|---|
| `'Thiếu L'` | 1695–9338 ms | **278–347 ms** |
| `'Nghĩa Huyền'` | 1545–1948 ms | **305–496 ms** |
| `'Thiếu'` | 171–213 ms | 123–228 ms |
| `'Lâm Tế'` | 53–77 ms | 63–78 ms |
| `'Thi'` | 15–22 ms | 13–49 ms |

Số kết quả trả về **không đổi** (8/8/10/10/10) → không regression hành vi.

## 4. Còn lại để đạt <200 ms (cần Admin duyệt — DB write)

`namevi_map_places.name_vi` và `lexicon.term` chưa có index cho LIKE; thêm index sẽ là
**DB write** (an toàn, `DROP INDEX` để revert). Đề xuất:
- `CREATE INDEX idx_namevi_places_name_vi ON namevi_map_places(name_vi);`
- (tuỳ) `CREATE INDEX idx_lexicon_term ON lexicon(term);`
- Hoặc hướng bền vững: FTS5 cho autocomplete (phạm vi lớn hơn, tách task riêng).

## 5. Verify

- `python -m py_compile app.py` → OK.
- Endpoint trả đúng số kết quả như trước.
- Revert: `git revert <sha>` (code-only); không có thay đổi DB.

## 6. Limitation

- Mốc <200 ms chưa đạt (đang 278–496 ms) — cần thêm index (DB write) hoặc FTS5.
- `app.py` trong working tree đang **trộn WIP của session khác** (T412/T440/T445/T446) →
  commit chỉ phần T416 bằng blob dựng từ HEAD + sửa T416 (§17), KHÔNG sweep WIP session khác.
