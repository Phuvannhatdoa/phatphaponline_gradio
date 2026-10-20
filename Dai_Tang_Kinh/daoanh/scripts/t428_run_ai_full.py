#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T428 Part 2 — chạy nền: places toàn bộ, sau đó districts toàn bộ.
Resumable: chạy lại script là tiếp tục từ chỗ đã lưu trong ai_place_name / ai_district_name.
"""
import subprocess
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE_DIR, 'scripts', 'ai_batch_transliterate_places_districts.py')

for el in ('place', 'district'):
    print(f'[wrapper] >>> bắt đầu {el} {time.strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    rc = subprocess.call([sys.executable, '-X', 'utf8', SCRIPT, '--element', el], cwd=BASE_DIR)
    print(f'[wrapper] <<< kết thúc {el} rc={rc} {time.strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    if rc != 0:
        print(f'[wrapper] {el} lỗi rc={rc} — vẫn tiếp tục element kế tiếp', flush=True)
print('[wrapper] DONE', flush=True)