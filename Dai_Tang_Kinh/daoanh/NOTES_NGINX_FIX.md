# Nginx Config Fix - POST 400 Error

## Issue
- ** Symptom: ** POST /api/entity/link returns 400 Bad Request
- **Nguyên nhân:** nginx config rewrite issue

## Fix Required (on VPS)

### Option 1: Remove rewrite for API
```nginx
# Trong /etc/nginx/sites-enabled/phatphaponline.org
location /daoanh/api/ {
    proxy_pass http://127.0.0.1:5000;
    # XÓA dòng rewrite
    proxy_http_version 1.1;
}
```

### Option 2: Use exact location
```nginx
location = /daoanh/api/entity/link {
    proxy_pass http://127.0.0.1:5000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Test
```bash
curl -X POST http://localhost:5000/api/entity/link \
  -H "Content-Type: application/json" \
  -d '{"text":"Test"}'
```

## VPS Commands
```bash
# SSH to VPS
ssh root@158.220.106.183

# Backup config
cp /etc/nginx/sites-enabled/phatphaponline.org /root/

# Edit config
nano /etc/nginx/sites-enabled/phatphaponline.org

# Test config
nginx -t

# Reload
systemctl reload nginx
```