# Security Audit — 2026-09-15

## Tóm tắt

Rà soát và fix các lỗi bảo mật theo checklist:
> Không expose database/internal services ra internet · Set resource limit · Chỉ mở port cần thiết ·
> Update dependency · Theo dõi CVE · Rate limiting/reverse proxy/WAF · Giả định bot scan mọi thứ public

---

## Lỗi đã fix

### #1 CRITICAL — `lineage.db` exposed qua nginx `/data/`
- **Triệu chứng**: nginx.conf có `location /data/ { alias .../data/; }` → `lineage.db` (664MB) và `admin_emails.txt` tải được tự do
- **Fix**: Thêm deny rules trong nginx.conf:
  ```nginx
  location ~* ^/daoanh/data/.*\.(db|sqlite|sqlite3|log|txt|bak|py|json)$ { deny all; return 403; }
  location = /daoanh/data/admin_emails.txt { deny all; return 403; }
  ```
  Chỉ expose `/daoanh/data/ttl/` (TTL files, không nhạy cảm).

### #2 CRITICAL — Admin routes không có auth (`server.py`)
- **Triệu chứng**: `/api/admin/emails` GET/POST/DELETE không check token → ai cũng thêm/xóa admin
- **Fix**: Thêm decorator `@require_admin` cho cả 3 routes. Decorator check Bearer token + session + admin list.

### #3 HIGH — `limit_req_zone` đặt sai nginx context
- **Triệu chứng**: Directive trong `server {}` block → nginx syntax error, rate limiting không hoạt động
- **Fix**: Di chuyển lên trên `server {}` block (http context) trong file sites-available.

### #4 HIGH — `/api/` location thiếu `proxy_pass`
- **Triệu chứng**: `/api/` chỉ có CORS headers, không có `proxy_pass` → nginx trả 404 cho API routes
- **Fix**: Tách thành 2 location blocks với `proxy_pass` đúng endpoint.

### #5 HIGH — Flask bind `0.0.0.0` — port 5000/5001 exposed trực tiếp
- **Triệu chứng**: Nếu VPS firewall không block, bypass nginx hoàn toàn
- **Fix**:
  - `app.py`: `host='0.0.0.0'` → `host='127.0.0.1'`
  - `server.py`: `host='0.0.0.0'` → `host='127.0.0.1'`
  - `local_gateway.py`: default `127.0.0.1`, thêm flag `--lan` nếu cần test LAN

### #6 MEDIUM — Session không có expiry
- **Triệu chứng**: `SESSIONS = {}` — token không bao giờ hết hạn, mất khi restart
- **Fix**: Thêm `SESSION_TTL = timedelta(hours=24)`, hàm `_purge_expired_sessions()`, check TTL trong `check_session()` và `login_check()`

### #7 MEDIUM — CORS wildcard quá rộng
- **Triệu chứng**: `origins: "*"` trên mọi route kể cả write endpoints
- **Fix**:
  - `app.py`: chỉ allow `phatphaponline.org` + localhost, chỉ GET/POST/OPTIONS
  - `server.py`: tương tự, restrict origins list
  - Nginx: CORS response header chỉ echo origin nếu match whitelist

### #8 HIGH — SSL commented out
- **Triệu chứng**: Toàn bộ traffic HTTP, session token truyền unencrypted
- **Fix trong nginx.conf**: Enable SSL block (TLS 1.2+1.3), HSTS header, HTTP→HTTPS redirect. VPS cần `certbot --nginx` để lấy cert.

---

## Còn lại — cần làm trên VPS

| Việc | Lệnh / Ghi chú |
|------|----------------|
| Cấp SSL cert | `certbot --nginx -d phatphaponline.org` |
| Block port 5000/5001 từ ngoài | `ufw deny 5000; ufw deny 5001` |
| Reload nginx sau khi update conf | `nginx -t && systemctl reload nginx` |
| Restart Flask servers | `systemctl restart daoanh-app daoanh-auth` |
| Kiểm tra firewall | `ufw status` — chỉ 22/80/443 được mở |
| Cài thêm deps | `pip install flask-limiter flask-cors` |

---

## File đã thay đổi

| File | Thay đổi |
|------|---------|
| `deploy/nginx.conf` | limit_req_zone fix, proxy_pass, block db/txt, CSP, SSL, HSTS, HTTP→HTTPS redirect |
| `server.py` | `@require_admin` decorator, session TTL 24h, CORS restrict, bind 127.0.0.1 |
| `app.py` | bind 127.0.0.1, CORS restrict origins |
| `local_gateway.py` | default bind 127.0.0.1, flag --lan cho LAN mode |
| `requirements.txt` | Thêm flask-limiter>=3.5.0, flask-cors>=4.0.0 |

---

## CVE theo dõi (framework quan trọng)

| Package | CVE tracking |
|---------|-------------|
| Flask | https://nvd.nist.gov/vuln/search/results?query=flask |
| Jinja2 | https://nvd.nist.gov/vuln/search/results?query=jinja2 |
| requests | https://nvd.nist.gov/vuln/search/results?query=requests+python |
| lxml | https://nvd.nist.gov/vuln/search/results?query=lxml |
| nginx | https://nginx.org/en/security_advisories.html |

Recommendation: Dùng `pip-audit` hoặc `safety check` trong CI để tự động check CVE.
