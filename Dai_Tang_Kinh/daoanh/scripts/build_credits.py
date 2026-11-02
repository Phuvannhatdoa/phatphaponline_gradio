#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T290 — Sinh trang ghi nguồn (credits.html) từ bảng `data_sources`.

Nguyên tắc
----------
1. CHỈ ĐỌC dữ liệu: không ghi DB, không sửa giấy phép, không tự xác nhận quyền.
2. Không gõ tay tên nguồn / giấy phép / tổ chức: mọi trường hiển thị lấy từ DB
   (`source_code`, `source_name`, `organization`, `license_spdx`, `data_license`,
   `license_verified`, `legal_status`, `integration_mode`, `origin_url`,
   `license_url`, `active`) + số claims đếm từ `entity_claims` + `authority_score`.
3. Giấy phép nào DB chưa xác minh (`license_verified = 0`) thì trang ghi rõ
   "Chưa xác minh" — KHÔNG tự khẳng định điều khoản (đúng chỉ đạo QA T290).
4. Ghi chú biên tập tách làm hai tầng:
   - `EDITORIAL_NOTES` — CHỈ mô tả vai trò/ngữ cảnh của nguồn, KHÔNG được nêu
     giấy phép / bản quyền / điều khoản (kể cả "share-alike", "phi thương mại").
   - `LICENSE_TERM_NOTES` — câu về điều khoản, CHỈ hiển thị khi nguồn có
     `license_verified = 1`. Nguồn chưa xác minh không bao giờ thấy các câu này.
   `--check` soi lại khối ghi chú của từng nguồn chưa xác minh và báo lỗi nếu
   thấy từ khóa giấy phép (bắt lỗi ghi chú cứng của bản trước).

Phân loại nguồn (hàm `select_groups`)
-------------------------------------
- "Đang dùng":  `active = 1` và `integration_mode <> 'BLOCKED'`
                (kể cả `local_dump`, `REFERENCE_ONLY`).
- "Chặn / chưa xác minh": các dòng còn lại (`active = 0` hoặc `BLOCKED`).
  M5 yêu cầu nguồn bị chặn vẫn "hiện dòng giải thích, không lỗi" → in dạng danh
  sách ngắn thay vì thẻ nguồn.

Dùng
----
  # sinh trang từ DB (ưu tiên; DB mở read-only)
  python -X utf8 scripts/build_credits.py --db data/lineage.db --out credits.html

  # máy không có DB thật (file 0 byte) — đọc danh sách nguồn qua API chỉ-đọc
  python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list

  # kiểm chứng: trang hiện tại có khớp DB không (exit 0 = khớp)
  python -X utf8 scripts/build_credits.py --check

  # xem dữ liệu đã chọn dạng JSON (audit)
  python -X utf8 scripts/build_credits.py --json

Revert: chỉ sinh lại file; bản cũ nằm ở
`docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder`.
"""
import argparse
import datetime
import html
import json
import os
import re
import sqlite3
import sys
import urllib.request

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ghi chú biên tập theo nguồn — CHỈ mô tả vai trò/ngữ cảnh của nguồn.
# TUYỆT ĐỐI không nêu giấy phép, bản quyền hay điều khoản ở đây: điều khoản chỉ
# được hiển thị từ DB (và từ LICENSE_TERM_NOTES khi DB đã xác minh giấy phép).
EDITORIAL_NOTES = {
    'DILA': 'Dữ liệu nhân vật, địa danh (authority). Dữ liệu DILA giữ tách biệt với '
            'tên tiếng Việt của ZQLOCAL.',
    'CBETA': 'Văn bản Đại Tạng Kinh (nội dung kinh điển).',
    'MARCUS': 'Quan hệ thầy trò trong bảng lineage_edge_consensus; ghi nguồn theo README của repo.',
    'Wikidata': 'ID liên kết (P1187/P1188 DILA, P2477 BDRC) — dùng như nguồn tham chiếu.',
    'ZQLOCAL': 'Tên tiếng Việt (phiên âm tự động, confidence 0.5), biên tập nội bộ. '
               'Không gán tên Việt của ZQLOCAL cho nguồn DILA hay nguồn khác.',
    'ZENLINEAGE': 'Dữ liệu kênh Zen Lineage (kênh bổ sung).',
    'TTL_LOCAL': 'TTL Thiền Sư Việt Nam (bản địa, nạp cục bộ local_dump).',
}

# Câu về điều khoản/giấy phép — CHỈ hiển thị khi `license_verified = 1`.
# Nguồn chưa xác minh (`license_verified = 0`) sẽ KHÔNG thấy các câu này trên
# trang; thay vào đó là badge + cảnh báo "chưa xác minh giấy phép".
LICENSE_TERM_NOTES = {
    'DILA': 'Bản phái sinh phân phối ra ngoài phải cùng giấy phép chia sẻ tương tự.',
    'CBETA': 'Chỉ dùng phi thương mại; giữ nguyên thông báo bản quyền, không sửa nội dung. '
             'Đầu ra thương mại không chứa văn bản CBETA.',
}

# Từ khóa nhận diện một câu đang KHẲNG ĐỊNH giấy phép/điều khoản (dùng cho --check).
LICENSE_CLAIM_PATTERNS = [
    ('giấy phép', r'giấy\s+phép'),
    ('license', r'\blicen[cs]e\b'),
    ('bản quyền', r'bản\s+quyền'),
    ('copyright', r'\bcopyright\b'),
    ('thương mại', r'thương\s+mại|non-?commercial'),
    ('share-alike', r'share-?alike|chia\s+sẻ\s+tương\s+tự'),
    ('mã CC', r'\bCC[- ]?(BY|0|SA|NC)'),
    ('public domain', r'public\s+domain|công\s+cộng'),
]

MARKER_RE = re.compile(r'<!--\s*t290:total=(\d+)\s+in_use=(\d+)\s+blocked=(\d+).*?-->')

# Khối ghi chú biên tập dạng `<div class="note">…</div>` (giữ cho tương thích test).
NOTE_BLOCK_RE = re.compile(r'<div class="note">(.*?)</div>', re.S)

# Khối ghi chú biên tập ở MỌI dạng: <div>/<p>/<span> có class chứa "note"
# (trừ `note unverified` — đó là khối cảnh báo chuẩn, không phải ghi chú cứng).
# Dùng để --check bắt ghi chú cứng nêu giấy phép cho nguồn chưa xác minh,
# bất kể class/tag khác (Tester T290 vòng 2, mục Sửa 2).
NOTE_LIKE_RE = re.compile(
    r'<([a-z][a-z0-9]*)\b[^>]*class=["\'][^"\']*\bnote\b[^"\']*["\'][^>]*>(.*?)</\1>',
    re.I | re.S)


def note_like_blocks(seg):
    """Trả danh sách inner-text của các khối ghi chú (trừ `note unverified`)."""
    out = []
    for m in NOTE_LIKE_RE.finditer(seg):
        opening = seg[m.start():m.start() + m.group(0).find('>') + 1]
        if 'unverified' in opening.lower():
            continue
        out.append(m.group(2))
    return out


def find_license_claims(text):
    """Trả danh sách từ khóa giấy phép/điều khoản xuất hiện trong `text`."""
    hits = []
    for label, pattern in LICENSE_CLAIM_PATTERNS:
        if re.search(pattern, text, re.I):
            hits.append(label)
    return hits


def card_segment(html_text, code):
    """Cắt đúng đoạn thẻ của 1 nguồn (dừng ở thẻ kế tiếp / tiêu đề mục / footer)."""
    marker = 'data-source-code="' + html.escape(code, quote=True) + '"'
    parts = html_text.split(marker, 1)
    if len(parts) < 2:
        return ''
    rest = parts[1]
    for stop in ('data-source-code="', '<h2 class="section"', '<footer>'):
        idx = rest.find(stop)
        if idx != -1:
            rest = rest[:idx]
    return rest



# --------------------------------------------------------------------------
# Nạp dữ liệu
# --------------------------------------------------------------------------
def db_looks_usable(path):
    """DB 0 byte / vài byte là placeholder trong worktree → coi như không có."""
    try:
        return os.path.getsize(path) > 8192
    except OSError:
        return False


def default_db_candidates():
    return [
        os.path.join(DAOANH, 'data', 'lineage.db'),
        os.path.join(os.path.dirname(DAOANH), 'data', 'lineage.db'),
    ]


def load_rows_from_db(path):
    """Đọc `data_sources` + claims + authority. Read-only, không tạo DB nếu thiếu."""
    if not db_looks_usable(path):
        raise RuntimeError(f'DB không dùng được (thiếu hoặc 0 byte): {path}')
    uri = 'file:' + os.path.abspath(path).replace('\\', '/') + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute('SELECT * FROM data_sources').fetchall()]
        claims = {}
        try:
            for sid, n in conn.execute(
                    'SELECT source_id, COUNT(*) FROM entity_claims GROUP BY source_id'):
                claims[sid] = n
        except sqlite3.Error:
            pass
        authority = {}
        try:
            for sid, score in conn.execute(
                    'SELECT source_id, MAX(authority_score) FROM source_authority '
                    'GROUP BY source_id'):
                authority[sid] = score
        except sqlite3.Error:
            pass
    finally:
        conn.close()
    for r in rows:
        sid = r.get('source_id')
        r['claims'] = claims.get(sid, 0)
        r['authority_score'] = authority.get(sid)
    return rows


def load_rows_from_api(url, timeout=20):
    """Fallback chỉ-đọc: lấy danh sách nguồn từ endpoint Source Hub của app đang chạy."""
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    rows = payload.get('sources') or []
    if not rows:
        raise RuntimeError(f'API không trả nguồn nào: {url}')
    return rows


def select_groups(rows):
    """Tách (đang dùng, chặn/chưa xác minh). Xem docstring đầu file."""
    def num(v, default=0):
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    in_use, blocked = [], []
    for r in sorted(rows, key=lambda x: num(x.get('source_id'), 999)):
        mode = str(r.get('integration_mode') or '').strip().upper()
        if num(r.get('active')) == 1 and mode != 'BLOCKED':
            in_use.append(r)
        else:
            blocked.append(r)
    return in_use, blocked


# --------------------------------------------------------------------------
# Sinh HTML
# --------------------------------------------------------------------------
def esc(value, empty='—'):
    if value is None:
        return empty
    text = str(value).strip()
    return html.escape(text, quote=True) if text else empty


def license_state(row):
    """(license_text, verified?) — chỉ đọc từ DB, không suy diễn."""
    lic = str(row.get('license_spdx') or row.get('data_license') or '').strip()
    verified = str(row.get('license_verified') or '0').strip().lower() in ('1', 'true')
    if lic and verified:
        return lic, True
    if lic:
        return lic, False
    return '', False


def license_badge_class(lic, verified):
    up = lic.upper()
    if not lic:
        return 'warn'
    if 'NC' in up:
        return 'nc'
    if 'SA' in up:
        return 'sa'
    if up.startswith('CC0') or 'PUBLIC DOMAIN' in up:
        return 'pub'
    return 'ok' if verified else 'warn'


def legal_badge_class(status):
    s = str(status or '').strip().upper()
    if s in ('ACTIVE', 'REFERENCE_ONLY'):
        return 'ok'
    if s == 'BLOCKED':
        return 'bad'
    if s == 'INTERNAL_USE':
        return 'internal'
    return 'warn'  # AUDITING / UNKNOWN / rỗng


def render_card(row):
    code = str(row.get('source_code') or '').strip()
    name = row.get('source_name') or code or '(không tên)'
    lic, verified = license_state(row)
    lic_text = lic if lic else 'Chưa xác minh giấy phép'
    if lic and not verified:
        lic_text = f'{lic} (chưa xác minh)'
    badge_lic = f'<span class="badge {license_badge_class(lic, verified)}">{esc(lic_text)}</span>'

    legal = str(row.get('legal_status') or '').strip()
    badge_legal = (f'<span class="badge {legal_badge_class(legal)}">legal: {esc(legal)}</span>'
                   if legal else '')

    mode = str(row.get('integration_mode') or '').strip()
    badge_mode = f'<span class="badge plain">mode: {esc(mode)}</span>' if mode else ''

    meta = []
    if row.get('organization'):
        meta.append(f'Tổ chức: {esc(row.get("organization"))}')
    claims = row.get('claims') or 0
    try:
        claims = int(claims)
    except (TypeError, ValueError):
        claims = 0
    meta.append(f'Claims trong hệ thống: {claims:,}'.replace(',', '.'))
    if row.get('authority_score') is not None:
        meta.append(f'Authority score: {esc(row.get("authority_score"))}')

    links = []
    for label, key in (('Nguồn gốc', 'origin_url'), ('Trang giấy phép', 'license_url'),
                       ('Repository', 'repository_url')):
        url = str(row.get(key) or '').strip()
        if url:
            links.append(f'{label}: <a href="{html.escape(url, quote=True)}" target="_blank" '
                         f'rel="noopener">{esc(url)}</a>')

    note = EDITORIAL_NOTES.get(code)
    note_html = f'<div class="note">{esc(note)}</div>' if note else ''
    if verified:
        # Điều khoản chỉ hiện khi DB đã xác minh giấy phép (không khẳng định khi chưa xác minh).
        term = LICENSE_TERM_NOTES.get(code)
        if term:
            note_html += f'<div class="note term">{esc(term)}</div>'
    else:
        note_html += ('<div class="note unverified">Giấy phép chưa xác minh trong DB '
                      '(<code>license_verified=0</code>) — không trích dẫn điều khoản cụ thể '
                      'cho tới khi có văn bản xác nhận.</div>')

    return f'''<div class="source-card" data-source-code="{html.escape(code, quote=True)}">
  <h3>{esc(name)}</h3>
  <div class="org">{esc(row.get('organization'), 'Chưa ghi tổ chức')} · <code>{esc(code)}</code></div>
  <div>{badge_lic}{badge_legal}{badge_mode}</div>
  <div class="meta">{'<br>'.join(meta)}</div>
  {('<div class="meta">' + '<br>'.join(links) + '</div>') if links else ''}
  {note_html}
</div>'''


def render_blocked_item(row):
    code = str(row.get('source_code') or '').strip()
    name = row.get('source_name') or code
    legal = str(row.get('legal_status') or '').strip() or 'không rõ'
    mode = str(row.get('integration_mode') or '').strip() or 'không rõ'
    active = 'bật' if str(row.get('active') or '').strip() in ('1', 'true') else 'tắt'
    return (f'<li data-source-code="{html.escape(code, quote=True)}"><code>{esc(code)}</code> — '
            f'{esc(name)} · <span class="dim">legal: {esc(legal)} · mode: {esc(mode)} · '
            f'active: {active} · chưa dùng để hiển thị công khai</span></li>')


TEMPLATE = '''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ghi nguồn dữ liệu — Phật Tổ Đạo Ảnh</title>
<link rel="stylesheet" href="/daoanh/admin/admin.css">
<style>
body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}
h1 {{ font-size: 1.4rem; margin-bottom: 0.4rem; }}
.subtitle {{ color: #666; margin-bottom: 1rem; font-size: 0.9rem; }}
.summary {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 0.8rem 1rem; font-size: 0.85rem; color: #334155; margin-bottom: 1.2rem; }}
h2.section {{ font-size: 1.05rem; margin: 1.8rem 0 0.8rem; padding-bottom: 0.3rem;
              border-bottom: 1px solid #e5e7eb; }}
.notes {{ margin: 0 0 0.6rem; font-size: 0.85rem; color: #64748b; }}
.source-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1.2rem 1.5rem; margin-bottom: 1.2rem; }}
.source-card h3 {{ font-size: 1.05rem; margin: 0 0 0.3rem; }}
.source-card .org {{ color: #555; font-size: 0.9rem; margin-bottom: 0.6rem; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem;
          font-weight: 600; background: #e8f0fe; color: #1a56db; margin: 0 6px 4px 0; }}
.badge.nc {{ background: #fef3c7; color: #92400e; }}
.badge.sa {{ background: #dcfce7; color: #166534; }}
.badge.pub {{ background: #e0f2fe; color: #075985; }}
.badge.internal {{ background: #ede9fe; color: #5b21b6; }}
.badge.warn {{ background: #fff7ed; color: #9a3412; }}
.badge.bad {{ background: #fee2e2; color: #991b1b; }}
.badge.plain {{ background: #f1f5f9; color: #475569; font-weight: 500; }}
.meta {{ font-size: 0.85rem; color: #666; margin-top: 0.6rem; }}
.meta a {{ color: #1a56db; }}
.note {{ font-size: 0.85rem; color: #475569; margin-top: 0.6rem; }}
.note.term {{ color: #166534; }}
.note.unverified {{ color: #9a3412; }}
.warning {{ background: #fff7ed; border: 1px solid #fdba74; border-radius: 6px;
            padding: 0.8rem 1rem; font-size: 0.85rem; color: #7c2d12; margin-bottom: 1.5rem; }}
ul.blocked {{ font-size: 0.85rem; color: #334155; padding-left: 1.2rem; }}
ul.blocked li {{ margin-bottom: 0.35rem; }}
.dim {{ color: #64748b; }}
footer {{ margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1rem;
          font-size: 0.8rem; color: #888; }}
</style>
</head>
<body>
<h1>Ghi nguồn dữ liệu</h1>
<p class="subtitle">Phật Tổ Đạo Ảnh sử dụng dữ liệu từ các tổ chức sau. Ghi nguồn theo điều khoản của từng nguồn.</p>

<div class="summary">
  Tổng <strong>{total}</strong> nguồn trong bảng <code>data_sources</code> ·
  <strong>{in_use_n}</strong> nguồn đang dùng · <strong>{blocked_n}</strong> nguồn đang chặn hoặc chưa xác minh.<br>
  Trang được sinh tự động bởi <code>scripts/build_credits.py</code> (chỉ đọc DB) — không sửa tay.
  Lần sinh: {generated_at}.
</div>
{blocked_warning}
<h2 class="section">Nguồn đang dùng ({in_use_n})</h2>
<p class="notes">Điều khoản và trạng thái lấy nguyên từ <code>data_sources</code>. Nguồn có
<code>license_verified=0</code> được ghi rõ là chưa xác minh.</p>
{cards}
<h2 class="section">Nguồn đang chặn hoặc chưa xác minh ({blocked_n})</h2>
<p class="notes">Danh sách này KHÔNG được dùng để hiển thị dữ liệu công khai. Chi tiết kiểm tra pháp lý tại
<a href="/daoanh/admin/source_check.html">Legal Check</a>.</p>
<ul class="blocked">
{blocked_items}
</ul>
<footer>
  Sinh từ bảng <code>data_sources</code> (chỉ đọc, M5/T290).
  Muốn cập nhật trang: chạy <code>python -X utf8 scripts/build_credits.py --out credits.html</code>.
  <br>Nguồn dữ liệu: {db_label}. Số dòng SQL = số mục trên trang = {total}.
</footer>
<!-- t290:total={total} in_use={in_use_n} blocked={blocked_n} db={db_label} at={generated_at} -->
</body>
</html>
'''


def render(rows, db_label='data_sources', generated_at=None):
    in_use, blocked = select_groups(rows)
    generated_at = generated_at or datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    cards = '\n'.join(render_card(r) for r in in_use) or '<p class="notes">(chưa có nguồn nào đang dùng)</p>'
    items = '\n'.join(render_blocked_item(r) for r in blocked) or '<li>(không có)</li>'
    unverified = [r for r in in_use if not license_state(r)[1]]
    if unverified:
        codes = ', '.join(str(r.get('source_code') or '?') for r in unverified)
        blocked_warning = (f'<div class="warning">\n  ⚠ {len(unverified)}/{len(in_use)} nguồn đang dùng '
                           f'chưa xác minh giấy phép trong DB: {esc(codes)}. '
                           f'Xem chi tiết tại <a href="/daoanh/admin/source_check.html">Legal Check</a>.\n</div>')
    else:
        blocked_warning = ''
    return TEMPLATE.format(
        total=len(rows), in_use_n=len(in_use), blocked_n=len(blocked),
        generated_at=esc(generated_at), db_label=esc(db_label),
        blocked_warning=blocked_warning, cards=cards, blocked_items=items)


# --------------------------------------------------------------------------
# Kiểm chứng (--check)
# --------------------------------------------------------------------------
def check_page(html_text, rows):
    """Trả danh sách lỗi; rỗng = trang khớp dữ liệu."""
    problems = []
    in_use, blocked = select_groups(rows)
    m = MARKER_RE.search(html_text)
    if not m:
        problems.append('Thiếu marker <!-- t290:total=… --> trong trang (trang có thể là bản gõ tay cũ).')
    else:
        total, iu, bl = (int(x) for x in m.groups())
        if total != len(rows):
            problems.append(f'Marker total={total} ≠ số dòng data_sources={len(rows)}.')
        if iu != len(in_use):
            problems.append(f'Marker in_use={iu} ≠ số nguồn đang dùng={len(in_use)}.')
        if bl != len(blocked):
            problems.append(f'Marker blocked={bl} ≠ số nguồn bị chặn={len(blocked)}.')

    codes = set()
    for r in rows:
        code = str(r.get('source_code') or '').strip()
        if not code:
            continue
        codes.add(code)
        n = len(re.findall(r'data-source-code="' + re.escape(code) + '"', html_text))
        if n == 0:
            problems.append(f'Thiếu nguồn {code} trên trang.')
        elif n > 1:
            problems.append(f'Nguồn {code} xuất hiện {n} lần (phải đúng 1).')

    extra = set(re.findall(r'data-source-code="([^"]+)"', html_text)) - codes
    if extra:
        problems.append('Trang có nguồn không còn trong DB: ' + ', '.join(sorted(extra)))

    # Không được khẳng định điều khoản cho nguồn chưa xác minh giấy phép
    for r in in_use:
        lic, verified = license_state(r)
        if verified:
            continue
        code = str(r.get('source_code') or '').strip()
        seg = card_segment(html_text, code)
        if not seg:
            continue
        if lic and 'chưa xác minh' not in seg.lower():
            problems.append(f'Nguồn {code}: giấy phép chưa xác minh nhưng trang không ghi rõ.')
        # Soi mọi khối ghi chú (mọi tag/class chứa "note", trừ khối cảnh báo chuẩn)
        # để bắt ghi chú cứng nêu giấy phép/điều khoản cho nguồn chưa xác minh.
        for note_text in note_like_blocks(seg):
            hits = find_license_claims(html.unescape(note_text))
            if hits:
                problems.append(
                    f'Nguồn {code}: giấy phép chưa xác minh nhưng ghi chú trên trang nêu '
                    f'điều khoản ({", ".join(hits)}) — phải bỏ câu đó hoặc xác minh giấy phép trong DB.')
    return problems


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description='Sinh/kiểm credits.html từ data_sources (read-only)')
    ap.add_argument('--db', help='đường dẫn lineage.db (mở read-only)')
    ap.add_argument('--api', help='fallback: URL /daoanh/api/admin/sources/list của app đang chạy')
    ap.add_argument('--out', default=os.path.join(DAOANH, 'credits.html'))
    ap.add_argument('--check', action='store_true', help='kiểm trang --out khớp dữ liệu, không ghi')
    ap.add_argument('--json', action='store_true', help='in dữ liệu nguồn đã chọn dạng JSON')
    ap.add_argument('--generated-at', help='mốc thời gian ghi trên trang (mặc định: bây giờ)')
    args = ap.parse_args(argv)

    db_label = 'data_sources'
    try:
        if args.api:
            rows = load_rows_from_api(args.api)
            db_label = 'Source Hub API (đọc từ data_sources)'
        else:
            path = args.db
            if not path:
                usable = [p for p in default_db_candidates() if db_looks_usable(p)]
                path = usable[0] if usable else None
            if not path:
                print('LỖI: không tìm thấy lineage.db thật (candidate: '
                      + ', '.join(default_db_candidates()) + ').\n'
                      '     Máy không có DB: dùng --db <path> hoặc --api <url> (chỉ đọc).',
                      file=sys.stderr)
                return 2
            rows = load_rows_from_db(path)
            db_label = 'lineage.db · data_sources'
    except Exception as exc:  # noqa: BLE001 — báo lỗi thân thiện
        print(f'LỖI đọc dữ liệu nguồn: {exc}', file=sys.stderr)
        return 2

    in_use, blocked = select_groups(rows)
    if args.json:
        print(json.dumps({'total': len(rows), 'in_use': in_use, 'blocked': blocked},
                         ensure_ascii=False, indent=2))
        return 0

    if args.check:
        if not os.path.exists(args.out):
            print(f'LỖI: không thấy trang {args.out}', file=sys.stderr)
            return 2
        with open(args.out, encoding='utf-8') as fh:
            html_text = fh.read()
        problems = check_page(html_text, rows)
        print(f'Dữ liệu: {len(rows)} nguồn · đang dùng {len(in_use)} · chặn/chưa xác minh {len(blocked)}')
        if problems:
            print('FAIL — trang không khớp DB:')
            for p in problems:
                print('  - ' + p)
            return 1
        print(f'PASS — {args.out} khớp {len(rows)} dòng data_sources (mỗi nguồn đúng 1 mục).')
        return 0

    html_text = render(rows, db_label=db_label, generated_at=args.generated_at)
    with open(args.out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(html_text)
    print(f'Đã sinh {args.out}: {len(rows)} nguồn · đang dùng {len(in_use)} · '
          f'chặn/chưa xác minh {len(blocked)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
