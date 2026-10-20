# Session 2026-09-22 — SSL Renewal & Nginx Config Cleanup

## Vấn đề

Cert `phatphaponline.org` hết hạn Sep 23 2026. Certbot renewal tự động thất bại do:
1. Nginx bị stop → webroot authenticator không serve challenge → CA trả 404
2. Nginx process cũ (PID 1522872, start trực tiếp không qua systemd) vẫn chiếm port 80/443 → `bind() failed`
3. 3 file backup nginx config (`.bak2`, `.bak3`, `.bak_*`) trong `/etc/nginx/sites-enabled/` → "conflicting server name" warnings khi nginx test

## Fix thực hiện

### 1. Kill all nginx processes
```bash
pkill -f nginx
```
Nginx process cũ không được quản lý bởi systemd → `systemctl stop` không đủ.

### 2. Certbot standalone renewal
```bash
certbot certonly --standalone --force-renewal \
  --cert-name phatphaponline.org \
  -d phatphaponline.org -d www.phatphaponline.org \
  --agree-tos --non-interactive
```
Cert mới: **Dec 20, 2026** (90 ngày)

### 3. Dọn nginx sites-enabled
Chuyển 4 file backup gây conflict ra `/etc/nginx/sites-backup/`:
- `phatphaponline.org.disabled.bak2`
- `phatphaponline.org.disabled.bak3`
- `phatphaponline.org.disabled.bak_20260920_125327`
- `zenq-phatphaponline.disabled`

Sites-enabled còn lại (clean):
- `phatphaponline.org.disabled` — main config (port 80 redirect + 443 SSL)
- `zenq-phatphaponline-80` — zenq subdomain

### 4. Start nginx
```bash
nginx -t && systemctl start nginx
```
nginx: OK, active

## Kết quả

| Item | Trước | Sau |
|------|-------|-----|
| Cert expiry | Sep 23, 2026 | Dec 20, 2026 |
| nginx status | failed (systemd) | active |
| HTTPS response | N/A | HTTP 200 |
| nginx config warnings | 12 conflicting server_name | 0 |

## Ghi chú kỹ thuật

- Nginx trên VPS đôi khi được khởi động trực tiếp (không qua systemd), dẫn đến `systemctl stop` không kill được process. Dùng `pkill -f nginx` khi cần dừng hoàn toàn.
- Để tránh lặp lại: certbot auto-renewal cần nginx đang chạy (webroot) hoặc dùng `--nginx` plugin (tự quản lý reload).
- Certbot đã setup scheduled task tự động renew trước khi hết hạn.
