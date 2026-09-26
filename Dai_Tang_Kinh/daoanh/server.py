#!/usr/bin/env python3
"""
Auth Gateway - Login Server
Chỉ xử lý login bằng Gmail.
Port: 5001 — bind 127.0.0.1 (chỉ nginx/gateway proxy tới đây, không expose ra ngoài)
"""

import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)

# CORS: chỉ allow origin từ chính domain — không wildcard
_ALLOWED_ORIGINS = [
    'https://phatphaponline.org',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]
CORS(app, resources={r"/*": {
    "origins": _ALLOWED_ORIGINS,
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ADMIN_DIR = os.path.join(BASE_DIR, 'admin')

SESSIONS = {}
ADMIN_EMAILS = []
ADMIN_EMAILS_FILE = os.path.join(DATA_DIR, 'admin_emails.txt')

# Session TTL: 24 giờ
SESSION_TTL = timedelta(hours=24)


def load_admin_emails():
    global ADMIN_EMAILS
    if os.path.exists(ADMIN_EMAILS_FILE):
        with open(ADMIN_EMAILS_FILE, 'r') as f:
            ADMIN_EMAILS = [line.strip().lower() for line in f if line.strip()]
    else:
        ADMIN_EMAILS = ['nhatdoaphuvan@gmail.com']
        save_admin_emails()


def save_admin_emails():
    with open(ADMIN_EMAILS_FILE, 'w') as f:
        for email in ADMIN_EMAILS:
            f.write(email + '\n')


def _purge_expired_sessions():
    """Xóa các session đã hết hạn khỏi bộ nhớ."""
    now = datetime.now()
    expired = [t for t, s in SESSIONS.items()
               if now - datetime.fromisoformat(s['created']) > SESSION_TTL]
    for t in expired:
        del SESSIONS[t]


load_admin_emails()


def check_session():
    """Kiểm tra Bearer token, trả về email nếu hợp lệ và chưa hết hạn."""
    _purge_expired_sessions()
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        session = SESSIONS.get(token)
        if session:
            age = datetime.now() - datetime.fromisoformat(session['created'])
            if age <= SESSION_TTL:
                return session.get('email')
            # Hết hạn — xóa luôn
            del SESSIONS[token]
    return None


def require_admin(fn):
    """Decorator: yêu cầu session admin hợp lệ."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        email = check_session()
        if not email:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        load_admin_emails()
        if email not in ADMIN_EMAILS:
            return jsonify({'success': False, 'message': 'Forbidden'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ==================== ROUTES ====================

@app.route('/daoanh/login.html')
def login_page():
    return send_from_directory(ADMIN_DIR, 'login.html')


@app.route('/daoanh/api/login/verify', methods=['POST'])
@app.route('/api/login/verify', methods=['POST'])
def login_verify():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').lower().strip()

    if not (email.endswith('@gmail.com') or email.endswith('@googlemail.com')):
        return jsonify({'success': False, 'message': 'Email không được phép'})

    load_admin_emails()

    if email in ADMIN_EMAILS:
        _purge_expired_sessions()
        token = secrets.token_urlsafe(32)
        SESSIONS[token] = {'email': email, 'created': datetime.now().isoformat()}
        return jsonify({'success': True, 'session_token': token, 'message': 'Đăng nhập thành công'})

    return jsonify({'success': False, 'message': 'Email không được phép đăng nhập'})


@app.route('/daoanh/api/login/check', methods=['POST'])
@app.route('/api/login/check', methods=['POST'])
def login_check():
    data = request.get_json(silent=True) or {}
    token = data.get('session_token', '')
    _purge_expired_sessions()
    session = SESSIONS.get(token)
    if session:
        age = datetime.now() - datetime.fromisoformat(session['created'])
        if age <= SESSION_TTL:
            return jsonify({'valid': True, 'email': session.get('email')})
    return jsonify({'valid': False})


@app.route('/api/admin/emails', methods=['GET'])
@require_admin
def admin_list_emails():
    load_admin_emails()
    return jsonify({'emails': ADMIN_EMAILS})


@app.route('/api/admin/emails/add', methods=['POST'])
@require_admin
def admin_add_email():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').lower().strip()

    if not (email.endswith('@gmail.com') or email.endswith('@googlemail.com')):
        return jsonify({'success': False, 'message': 'Phải là Gmail'})

    load_admin_emails()

    if email in ADMIN_EMAILS:
        return jsonify({'success': False, 'message': 'Email đã tồn tại'})

    ADMIN_EMAILS.append(email)
    save_admin_emails()
    return jsonify({'success': True, 'message': 'Đã thêm ' + email})


@app.route('/api/admin/emails/delete', methods=['POST'])
@require_admin
def admin_delete_email():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').lower().strip()

    load_admin_emails()

    if email in ADMIN_EMAILS:
        ADMIN_EMAILS.remove(email)
        save_admin_emails()
        return jsonify({'success': True, 'message': 'Đã xóa ' + email})

    return jsonify({'success': False, 'message': 'Email không tồn tại'})


if __name__ == '__main__':
    print("=" * 60)
    print("Auth Gateway (Login Server)")
    print("=" * 60)
    print(f"Admin dir: {ADMIN_DIR}")
    print(f"Data dir:  {DATA_DIR}")
    print("Bind: 127.0.0.1:5001 (nginx/gateway proxy only)")
    print("=" * 60)
    # Bind 127.0.0.1 — chỉ nginx trên cùng máy mới tới được
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
