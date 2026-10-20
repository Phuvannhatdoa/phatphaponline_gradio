# 2026-08-18 — T08: Missing hanzi admin view

## Mô tả ngắn task

T08 — "Missing hanzi admin view": bảng `missing_hanzi` (tự động ghi khi `_ensure_vietnamese()` gặp
ký tự Hán chưa có Hán-Việt) đã tồn tại nhưng chưa có UI/API admin để xem và bổ sung override.
Chọn task này sau khi T04 (Marcus people link) bị gián đoạn bởi 1 phiên Claude Code khác đang dev
song song trên cùng project — T08 được chọn vì phần lớn là code mới/độc lập (bảng DB mới, 2 route
mới, 1 trang admin mới), không sửa route/logic hiện có nào.

## Phân tích

- `missing_hanzi(char PK, count, last_seen_at)` đã có sẵn (tạo bởi `_ensure_missing_hanzi_table()`,
  ghi bởi `_log_missing_hanzi()` mỗi khi `_ensure_vietnamese()` gặp ký tự không có trong
  `CUSTOM_HANVIET` (dict literal trong `app.py`) lẫn `hanviet_fallback` (bảng DB).
- `CUSTOM_HANVIET` là dict Python cứng trong source — không thể ghi an toàn lúc runtime (sửa file
  .py đang chạy). Cần một lớp gián tiếp: bảng DB override + merge vào RAM dict lúc khởi động và mỗi
  lần admin lưu mới.
- Tại thời điểm build: 351 ký tự đang thiếu bản dịch trong `missing_hanzi` (dữ liệu thật, không
  phải test).

## Thiết kế/giải pháp đã chọn (additive, không sửa/xoá dữ liệu cũ)

1. Bảng mới `custom_hanviet_override(char PK, hanviet, added_by, created_at)`.
2. `_load_custom_hanviet_overrides()` — nạp toàn bộ override vào dict `CUSTOM_HANVIET` (RAM), gọi
   từ `_init_hv_cache()` (lazy-init có sẵn, không đổi thời điểm gọi hiện tại).
3. API `GET /daoanh/api/admin/missing-hanzi?page=&limit=&search=` — danh sách phân trang từ
   `missing_hanzi`, kèm cột `override` (giá trị hiện có trong `custom_hanviet_override` nếu có).
4. API `POST /daoanh/api/admin/missing-hanzi/override` body `{char, hanviet}` — upsert
   `custom_hanviet_override`, xoá dòng khỏi `missing_hanzi` (coi như đã resolved), cập nhật
   `CUSTOM_HANVIET[char]` trong RAM ngay lập tức (không cần restart server để bản dịch mới dùng
   override).
5. Trang mới `admin/missing_hanzi.html` — bảng + ô tìm + input override + nút Lưu. Dùng token
   `styles/daoanh-design.css` theo Design Standard 2026-08-17 (`.da-body`, `.da-chip`, `.da-btn`...).
   Không cần route Flask riêng: route tĩnh sẵn có `/daoanh/admin/<path:path>` (app.py dòng ~1701)
   tự động serve mọi file trong thư mục `admin/`.

## Danh sách file đã tạo/sửa

- `app.py` — thêm `_ensure_custom_hanviet_override_table()`, `_load_custom_hanviet_overrides()`
  (gọi trong `_init_hv_cache()`), 2 route mới `api_admin_missing_hanzi`,
  `api_admin_missing_hanzi_override`. Không sửa dòng code hiện có nào ngoài 1 dòng gọi thêm hàm mới
  trong `_init_hv_cache()`.
- `admin/missing_hanzi.html` (mới)
- `data/lineage.db` — bảng mới `custom_hanviet_override` (0 dòng sau khi dọn dữ liệu test, sẵn sàng
  cho admin dùng thật)
- `tasks/T08-missing-hanzi-admin.md` — cập nhật status `done`, checklist đủ 4/4
- `docs/tasktodo.md` — cập nhật dòng Task 8
- `docs/sessions/2026-08-18_t08_missing_hanzi_admin.md` — session log này

## Cách chạy/test

```bash
# API list (port 5000 trực tiếp)
curl "http://localhost:5000/daoanh/api/admin/missing-hanzi?limit=3"
# -> 3 dòng thật, total=351

# API lưu override (dùng file JSON UTF-8 để tránh lỗi encode của curl trên Windows khi
# truyền ký tự Hán trực tiếp qua -d)
curl -X POST "http://localhost:5000/daoanh/api/admin/missing-hanzi/override" \
  -H "Content-Type: application/json; charset=utf-8" --data-binary @override.json
# -> {"ok":true,"char":"翊","hanviet":"Dực"}, ký tự biến mất khỏi missing-hanzi list ngay
```

UI thật: mở `http://localhost:8080/daoanh/admin/missing_hanzi.html`, nhập override cho ký tự `罕`
qua form, bấm "Lưu" → dòng biến mất khỏi bảng sau khi trang tự reload — xác nhận luồng
UI → API → DB → reload hoạt động đúng đầu-cuối (test bằng Claude Browser tool, không phải chỉ curl).

## Kết quả test

- ✅ `GET .../missing-hanzi` — phân trang, search hoạt động đúng, dữ liệu thật từ DB.
- ✅ `POST .../missing-hanzi/override` — lưu đúng, xoá khỏi `missing_hanzi`, merge vào RAM ngay
  (verify bằng cách gọi lại GET list, không thấy ký tự nữa mà không cần restart server).
- ✅ UI end-to-end qua browser thật (không chỉ curl) — khác với T04 trước đó (chỉ verify được API,
  chưa verify được UI do race condition với phiên khác lúc đó).
- Dữ liệu test (`翊`, `罕`, và 1 dòng `?` do lỗi encode ở lần curl đầu tiên trên Windows) đã được dọn
  sạch khỏi `custom_hanviet_override` và trả `missing_hanzi` về đúng trạng thái ban đầu sau khi
  verify xong — không để lại dữ liệu test/rác trong DB thật.

## Ghi chú vận hành phiên dev song song

- Trước khi test phải restart process `app.py` (port 5000) để nạp route mới — process đang chạy
  lúc bắt đầu task (PID 12328, khởi động 21:33) thuộc về phiên nào không xác định được, nhưng vì
  thay đổi trong `app.py` là additive (không sửa route/logic cũ), restart được coi là an toàn và
  không làm mất code của phiên khác (cùng đọc từ 1 file trên đĩa).
- Không chạy `git add/commit` cho task này — `CLAUDE.md` (đã được phiên kia cập nhật) hiện ghi rõ
  "Git index đang có anomaly... Không chạy git add/commit/reset khi chưa có lệnh rõ ràng từ user."
  Khác với T04 (user đã cho lệnh rõ ràng "gitcommit" ngay trong yêu cầu ban đầu), T08 không có lệnh
  git tương tự nên toàn bộ thay đổi được để ở trạng thái working-tree, chờ user xác nhận trước khi
  commit.

## Liên hệ ROADMAP

- Nguồn liên quan: Hán-Việt / Khoá 1 — Xong core Hán → Việt
- Việc còn lại ngoài scope T08: chưa có audit log riêng cho các lần admin sửa override (mới lưu
  `added_by`/`created_at`, chưa có UI xem lịch sử) — có thể tách task riêng nếu cần sau này.
