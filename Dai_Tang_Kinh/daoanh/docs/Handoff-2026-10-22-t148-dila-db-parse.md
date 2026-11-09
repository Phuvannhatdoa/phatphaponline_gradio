# Handoff 2026-10-22 — T148: đọc DILA XML từ DB thay vì file đĩa

## 1. Bảng đọc nhanh
| Mục | Giá trị |
|---|---|
| Ngày | 2026-10-22 |
| Trạng thái | **Code đã sửa, chưa commit, chưa có task ID, chờ Admin xác nhận DONE** |
| Git | `git log` báo `current branch appears to be broken` — chưa commit được, cần xử lý riêng |
| File sửa | `app.py` — hàm `_t148_load_dila_extra()` (~dòng 5733–5957) |
| DB | 0 mutation (chỉ SELECT) |

## 2. Đọc trong 2 phút
- **Lỗi gốc:** `_t148_load_dila_extra()` parse file `data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml`. File không tồn tại → hàm return rỗng → `/daoanh/api/person/<id>/dila_full` trả `has_extra: false` → trang admin thiếu thầy/trò/tác phẩm/CBETA.
- **Sửa:** đọc XML từ `ttl_v2_source_records.raw_text` (`kind='DILA_XML'`, 49,361 bản ghi) bằng `ET.fromstring()`; gộp (merge) khi cùng một person có nhiều bản ghi.
- **Kết quả đo được (log app):** `Queried 49361 DILA_XML records from DB` và `Đã index 49361 persons trong 25.4s`.
- **API (qua gateway 8080):** `A000001`, `A004511`, `A020661`, `A002290` đều `has_extra=True`.

## 3. Việc CHƯA xong
1. **Chưa kiểm trên UI:** trang `admin/person.html` đòi đăng nhập qua gateway, chưa xem được giao diện thật.
2. **Còn 2 dòng debug** trong code: `print(f'[T148] Queried ...')` (~dòng 5752) và `print(f'[T148] Parse error ...')` (~dòng 5762). Cần quyết định giữ hay xoá.
3. **Chưa có task file** `tasks/T<id>-*.md`. Theo `AGENTS.md` §16, phải chạy `npm run dup:ids` + grep prose trước khi cấp ID mới. `T148` cũ đã nằm trong `tasks/archive_done/` và không tái dùng được.
4. **Chưa chạy `npm run pipeline`** — bắt buộc trước khi xin duyệt (AGENTS §Workflow 2).
5. **Chưa có `docs/ROLLBACK.md` row** cho thay đổi này (code-only, revert bằng `git revert` khi git sửa được, hoặc khôi phục bản trước sửa).

## 4. Cảnh báo
- **Đã có session khác sửa `app.py` trong lúc làm**: số dòng `_t148_load_dila_extra` dịch từ ~5651 sang ~5733. Trước khi sửa tiếp, đọc lại file, không dựa số dòng trong handoff này.
- Đã dùng `DB_PATH` (không phải `DATABASE` — biến này không tồn tại).

## 5. Lệnh kiểm tra nhanh (1 phút)
```bash
# từ Dai_Tang_Kinh/daoanh
python -X utf8 -c "import ast;ast.parse(open('app.py',encoding='utf-8').read());print('ok')"
# app đang chạy? (gateway 8080 → backend 5000)
curl -s http://127.0.0.1:8080/daoanh/api/person/A004511/dila_full | head -c 200
```
Kỳ vọng: `has_extra` là `true`.

## 6. Ghi chú cho agent kế tiếp
1. Đọc block mới nhất trong `docs/tasktodo.md` và file Handoff này.
2. Quyết định 2 việc: xoá 2 dòng debug; cấp task ID mới rồi viết `tasks/T<id>-dila-xml-from-db.md`.
3. Xin Admin duyệt trước khi commit. Không `git commit` nếu chưa có lệnh rõ ràng.
