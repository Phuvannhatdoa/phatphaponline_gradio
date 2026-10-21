# Session 2026-10-20 — BUG-placevn-baseurl: placevn.html gọi nhầm prod URL khi test local

## Thông tin nhanh

| Mục | Giá trị |
|---|---|
| Triệu chứng (Admin báo) | "Lỗi CORS hoặc VPS bị chặn!" — console khi mở placevn tại 127.0.0.1:8080 |
| Console nguyên văn | `GET https://phatphaponline.org/daoanh/api/admin/places_pending?limit=100&offset=0&cate=admin_place net::ERR_CONNECTION_REFUSED` |
| Root cause | `placevn.html:113` chỉ branch `hostname === 'localhost'`; test theo CLAUDE.md dùng `127.0.0.1` → rơi nhánh prod `https://phatphaponline.org` |
| Vì sao ERR_CONNECTION_REFUSED (không phải CORS) | `phatphaponline.org` → 158.220.106.183 (VPS); port 443 **refused** (nginx down/chưa mở) — đo bằng socket + HTTPS fetch |
| Phạm vi sửa | 1 dòng: `admin/placevn.html` — 0 DB, 0 backend |
| Backup | `docs/sessions/2026-10-20/BUG-placevn-baseurl/placevn.html.bak-before-baseurl` |
| Trạng thái | FIX XONG + verify qua HTTP/parse; chờ Admin click test trình duyệt |

## Sửa

```js
// TRƯỚC
const [baseUrl, setBaseUrl] = useState(window.location.hostname === 'localhost' ? '' : 'https://phatphaponline.org');
// SAU (cùng convention namevimap.html:961: protocol-based, không hostname-based)
const isHttpProto = window.location.protocol === 'http:' || window.location.protocol === 'https:';
const [baseUrl, setBaseUrl] = useState(isHttpProto ? '' : 'https://phatphaponline.org');
```

Bảng hành vi: mọi origin http/https (127.0.0.1 / localhost / domain prod) → `''` same-origin;
`file://` mới fallback prod URL. Đúng theo convention `namevimap.html` (API const, dòng 960-962).

## Verify đã chạy

1. Diff so backup: **chẵn 1 hunk** đúng thay đổi trên.
2. Serve qua gateway: `GET 127.0.0.1:8080/daoanh/admin/placevn.html` → 200, chứa `isHttpProto`, không còn check cũ.
3. API mà page sẽ gọi (relative): `GET 127.0.0.1:8080/daoanh/api/admin/places_pending?limit=1&offset=0&cate=admin_place` → **200** (queue 42.653 dòng, trùng số liệu QA BUG-pl-id-404).
4. Vỗi nguyên nhân: DNS `phatphaponline.org` = 158.220.106.183; socket 443 refused (không phải DNS sai).

## Cảnh báo / việc chưa xong

1. **VPS 443 vẫn refused** — đây là issue phía VPS (nginx/443), ngoài phạm vi local fix. Page web công khai hiện không truy cập được bằng https. Cần session/VPS riêng xử lý (nginx start, firewall).
2. **Cùng pattern prod hard-code còn tồn ở 3 file khác** (đã quét, chưa sửa — đề xuất task sau):
   - `admin/places.html:55` — `useBaseUrl('https://phatphaponline.org')` vô điều kiện
   - `admin/keyword_import.html:100` — `baseUrl = 'https://phatphaponline.org'` vô điều kiện
   - `admin/panorama.html:639` — chỉ là TTL prefix string trong template, KHÔNG phải fetch → vô hại
3. Stack local bị tắt giữa phiên (gateway/app/server port 5000/5001/8080 đều chết) — đã khởi động lại theo CLAUDE.md (server_local.log / app_local.log / gateway_local.log).

## Revert

```powershell
Copy-Item -LiteralPath "docs/sessions/2026-10-20/BUG-placevn-baseurl/placevn.html.bak-before-baseurl" -Destination "admin/placevn.html" -Force
```

Không mất dữ liệu (0 DB).

## File tạo/sửa

| File | Thao tác |
|---|---|
| `admin/placevn.html` | sửa dòng 113 (1 hunk) |
| `docs/sessions/2026-10-20/BUG-placevn-baseurl/placevn.html.bak-before-baseurl` | backup |
| `docs/ROLLBACK.md` | entry BUG-placevn-baseurl |
| `docs/sessions/2026-10-20_BUG-placevn-baseurl.md` | log này |
