# -*- coding: utf-8 -*-
"""Sửa banner T200 — thay khối bị hỏng (tôi viết tiếng Việt bằng escape sai).

Bài học đã ghi ở AGENTS.md: **viết chữ tiếng Việt trong script phải dùng file .py tạo
bằng tool, không dùng `\\uXXXX` trong heredoc của PowerShell** — hay sai mã.
"""
import io
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, 'tasks', 'T200-vnpa-dila-id-duplicate-limit1.md')

BAD_START = '⚠'  # ⚠
GOOD_BANNER = (
    '> ⚠️ **Số liệu cũ:** file này còn các con số **33** — đó là mốc đo lúc T200 build\n'
    '> (2026-09-30 → 2026-10-01). **Đo lại 2026-10-03: 29 nhóm / 61 row.**\n'
    '> Phần phân loại + quyết định gộp/tách → **T223 §3**. Các số 33 còn lại bên dưới\n'
    '> là **số đo lịch sử**, không phải số hiện tại.\n'
    '\n'
)

s = io.open(P, encoding='utf-8').read()

# 1) xoá khối banner hỏng (bắt đầu bằng ⚠, kết thúc trước "# T200")
m = re.search(r'^>\s*⚠.*?(?=^#\s*T200\b)', s, re.S | re.M)
if m:
    s = s[:m.start()] + s[m.end():]
    print('  xoa banner hong')

# 2) chen banner đúng trước "# T200"
m = re.search(r'^#\s*T200\b', s, re.M)
assert m, 'khong tim thay "# T200"'
if 'Số liệu cũ' not in s:
    s = s[:m.start()] + GOOD_BANNER + s[m.start():]
    print('  chen banner dung')

# 3) chuẩn hoá các chỗ còn lỗi chính tả do escape sai trước đó
FIX = [('đo ố tấi', 'đo ở thời điểm'),
       ('2026-09-30→2021', '2026-09-30 → 2026-10-01'),
       ('bên dữi', 'bên dưới'),
       ('CHờ T223', 'CHỜ T223')]
for a, b in FIX:
    if a in s:
        print('  fix %r -> %r (x%d)' % (a, b, s.count(a)))
        s = s.replace(a, b)

# 4) chuẩn hoá "người"
s = re.sub('ngư��ng', 'người', s)
s = re.sub('ngưối', 'người', s)
s = re.sub('Phân phân', 'Phần phân', s)

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)

print('\n=== kiem tra ===')
for tag in ['Số liệu cũ', '29 nhóm / 61 row', 'T223 §3', 'CHỜ T223',
            'người khác chung', 'Phần phân loại', 'đo ở thời điểm',
            '2026-09-30 → 2026-10-01', 'bên dưới']:
    print('   %-26s %s' % (tag, 'OK' if tag in s else 'THIEU'))
for bad in ['đo ố tấi', '2021', 'bên dữi', 'ngường', 'ngưối', 'CHỏ']:
    if bad in s:
        print('   CON LAI: %r' % bad)
i = s.find('Số liệu cũ')
print('\n' + s[max(0, i - 20):i + 300])