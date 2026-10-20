# -*- coding: utf-8 -*-
"""Viết lại `note` của T200 bằng tiếng Việt chuẩn.

Phiên này tôi dùng `\\uXXXX` trong heredoc PowerShell quá nhiều và tạo ra nhiều
chuỗi thiếu dấu (`phan con lai`, `cón lại`, `con so`, `nhuoc`, `cua`, `CHỏ`...).
Script này thay nguyên giá trị `note:` bằng chuỗi viết literal trong file .py
(tạo bằng tool ⇒ UTF-8 chuẩn), rồi verify không còn lỗi.
"""
import io
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, 'tasks', 'T200-vnpa-dila-id-duplicate-limit1.md')

GOOD_NOTE = (
    'note: "BUILD ĐÃ XONG — phần còn lại CHỜ T223 (2026-10-03, Admin phê chuẩn). '
    'T223 giữ quyết định gộp/tách `dila_id` cho 29 nhóm / 61 row '
    '(đo lại 2026-10-03; con số 33 của bản gốc là mốc đo cũ). '
    'Lý do chờ: 11/23 file L1/L2 của T209 nằm trong các nhóm này '
    '⇒ L7 URI sai → L1/L2 nhãn sai → nhiều row chung 1 `dila_id`. '
    'Phải sửa L7 → L1/L2 → rồi mới tới `dila_id`."\n'
)

s = io.open(P, encoding='utf-8').read()

m = re.search(r'^note:\s*".*?"\n', s, re.S | re.M)
if not m:
    print('[FAIL] khong tim thay truong note')
    raise SystemExit(1)
print('  xoa note cu (do dai %d)' % len(m.group(0)))
s = s[:m.start()] + GOOD_NOTE + s[m.end():]
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)

# verify
s2 = io.open(P, encoding='utf-8').read()
m2 = re.search(r'^note:\s*(.+)$', s2, re.M)
print()
print('=== note moi ===')
print('  ' + m2.group(1))
print()
print('=== con loi thieu dau? ===')
BAD = ['phan con lai', 'cón lại', 'con so', 'nhuoc', 'cua T209', 'CHỏ',
       'đo ố tấi', 'ngường', 'ngưối', 'Phân phân', 'bên dữi']
bad = [b for b in BAD if b in s2]
print('  ' + ('KHONG con' if not bad else 'CON: %r' % bad))
# so trong phan frontmatter
fm = re.match(r'^---\n(.*?)\n---', s2, re.S).group(1)
susp = [l for l in fm.split('\n')
        if re.search(r'\b[a-z]+ [a-z]+ [a-z]+\b', l)
        and re.search(r'(phan|chon|con so|nhuoc|cua|giai)', l)]
print('  frontmatter nghi van thieu dau: %r' % (susp or 'KHONG'))