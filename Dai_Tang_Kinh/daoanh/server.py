#!/usr/bin/env python3
"""
Auth Gateway - Login Server
Ch? x? lý login b?ng Gmail (gi? l?p).
Port: 5001
"""

import os
import secrets
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["*"]}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ADMIN_DIR = os.path.join(BASE_DIR, 'admin')

SESSIONS = {}
ADMIN_EMAILS = []
ADMIN_EMAILS_FILE = os.path.join(DATA_DIR, 'admin_emails.txt')

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

load_admin_emails()

def check_session():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token in SESSIONS:
            return SESSIONS[token].get('email')
    return None

# ==================== ROUTES ====================

@app.route('/daoanh/login.html')
def login_page():
    return send_from_directory(ADMIN_DIR, 'login.html')

@app.route('/daoanh/api/login/verify', methods=['POST'])
@app.route('/api/login/verify', methods=['POST'])
def login_verify():
    data = request.get_json()
    email = data.get('email', '').lower().strip()

    if not email.endswith('@gmail.com') and not email.endswith('@googlemail.com'):
        return jsonify({'success': False, 'message': 'Email khong duoc phep'})

    load_admin_emails()

    if email in ADMIN_EMAILS:
        token = secrets.token_urlsafe(32)
        SESSIONS[token] = {'email': email, 'created': datetime.now().isoformat()}
        return jsonify({'success': True, 'session_token': token, 'message': 'Dang nhap thanh cong'})

    return jsonify({'success': False, 'message': 'Email khong duoc phep dang nhap'})

@app.route('/daoanh/api/login/check', methods=['POST'])
@app.route('/api/login/check', methods=['POST'])
def login_check():
    data = request.get_json()
    token = data.get('session_token', '')
    if token in SESSIONS:
        return jsonify({'valid': True, 'email': SESSIONS[token].get('email')})
    return jsonify({'valid': False})

@app.route('/api/admin/emails', methods=['GET'])
def admin_list_emails():
    load_admin_emails()
    return jsonify({'emails': ADMIN_EMAILS})

@app.route('/api/admin/emails/add', methods=['POST'])
def admin_add_email():
    data = request.get_json()
    email = data.get('email', '').lower().strip()

    if not email.endswith('@gmail.com') and not email.endswith('@googlemail.com'):
        return jsonify({'success': False, 'message': 'Phai la Gmail'})

    load_admin_emails()

    if email in ADMIN_EMAILS:
        return jsonify({'success': False, 'message': 'Email da ton tai'})

    ADMIN_EMAILS.append(email)
    save_admin_emails()
    return jsonify({'success': True, 'message': 'Da them ' + email})

@app.route('/api/admin/emails/delete', methods=['POST'])
def admin_delete_email():
    data = request.get_json()
    email = data.get('email', '').lower().strip()

    load_admin_emails()

    if email in ADMIN_EMAILS:
        ADMIN_EMAILS.remove(email)
        save_admin_emails()
        return jsonify({'success': True, 'message': 'Da xoa ' + email})

    return jsonify({'success': False, 'message': 'Email khong ton tai'})

if __name__ == '__main__':
    print("=" * 60)
    print("Auth Gateway (Login Server)")
    print("=" * 60)
    print(f"Admin dir: {ADMIN_DIR}")
    print(f"Data dir: {DATA_DIR}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
