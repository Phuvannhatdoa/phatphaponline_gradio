# Gunicorn configuration for Phật Tổ Đạo Ảnh
# Usage: gunicorn -c gunicorn_config.py app:app

import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/daoanh/access.log"
errorlog = "/var/log/daoanh/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "daoanh-server"

# Server mechanics
daemon = False
pidfile = "/var/run/daoanh.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/etc/ssl/private/server.key"
# certfile = "/etc/ssl/certs/server.crt"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Preload app for memory efficiency
preload_app = True

# Environment
raw_env = [
    'PYTHONUNBUFFERED=1',
]