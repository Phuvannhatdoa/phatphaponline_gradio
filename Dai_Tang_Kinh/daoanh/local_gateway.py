"""
local_gateway.py - nginx thay thế cho dev local (port 8080)

Trên VPS, nginx đóng 2 vai:
  1. Trả file tĩnh trực tiếp (places.html, admin/*.html, static/*, ...)
  2. Proxy request API sang đúng server Python đang chạy ngầm:
     - /daoanh/api/login/*, /api/login/*, /daoanh/login.html, /api/admin/emails*
         -> server.py (port 5001, auth gateway)
     - /daoanh/api/*, /api/*  (mọi API khác)
         -> app.py (port 5000, business logic)

Máy dev Windows không có nginx, nên script này giả lập đúng 2 vai trò trên.
Không dùng cho production - chỉ để chạy `python local_gateway.py` lúc dev local.
"""
import os
from flask import Flask, request, Response, send_from_directory, abort
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PORT = 5000
AUTH_PORT = 5001
GATEWAY_PORT = 8080

app = Flask(__name__)

AUTH_PREFIXES = (
    "/daoanh/api/login",
    "/api/login",
    "/daoanh/login.html",
    "/api/admin/emails",
)


def is_api_path(path: str) -> bool:
    return path.startswith("/daoanh/api/") or path.startswith("/api/")


def target_port(path: str) -> int:
    if any(path.startswith(p) for p in AUTH_PREFIXES):
        return AUTH_PORT
    return APP_PORT


def proxy(port: int):
    """Forward the current request to the given local port and relay the response."""
    url = f"http://127.0.0.1:{port}{request.full_path}"
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != "host"},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=60,
        )
    except requests.exceptions.ConnectionError:
        return Response(
            f'{{"error":"backend on port {port} is not running"}}',
            status=502,
            mimetype="application/json",
        )
    excluded = {"content-encoding", "transfer-encoding", "connection"}
    headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded]
    return Response(resp.content, status=resp.status_code, headers=headers)


def try_serve_static(path: str):
    """
    Mimic nginx's static-file serving for root-level pages like /daoanh/places
    (backed by places.html) and any other .html/.js/.css/asset in the daoanh tree.
    Returns a Flask response if a matching file is found, else None.
    """
    rel = path
    if rel.startswith("/daoanh/"):
        rel = rel[len("/daoanh/"):]
    elif rel == "/daoanh":
        rel = ""
    rel = rel.lstrip("/")

    candidates = [rel, f"{rel}.html", f"{rel}/index.html"] if rel else ["index.html"]
    for candidate in candidates:
        full = os.path.normpath(os.path.join(BASE_DIR, candidate))
        if not full.startswith(BASE_DIR):
            continue  # path traversal guard
        if os.path.isfile(full):
            directory, filename = os.path.split(full)
            return send_from_directory(directory, filename)
    return None


METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]

@app.route("/", defaults={"path": ""}, methods=METHODS)
@app.route("/<path:path>", methods=METHODS)
def gateway(path):
    full_path = "/" + path

    if is_api_path(full_path):
        return proxy(target_port(full_path))

    static_resp = try_serve_static(full_path)
    if static_resp is not None:
        return static_resp

    # Fallback: let app.py try (it owns a few specific HTML routes, e.g. /daoanh/admin/)
    return proxy(APP_PORT)


if __name__ == "__main__":
    print("=" * 60)
    print(f"local_gateway.py - dev nginx replacement on port {GATEWAY_PORT}")
    print(f"  static files served directly from: {BASE_DIR}")
    print(f"  /daoanh/api/login/*, /api/login/*  -> 127.0.0.1:{AUTH_PORT} (server.py)")
    print(f"  /daoanh/api/*, /api/*  (other)     -> 127.0.0.1:{APP_PORT} (app.py)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=GATEWAY_PORT, debug=False, threaded=True)
