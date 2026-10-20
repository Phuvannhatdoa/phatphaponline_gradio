# -*- coding: utf-8 -*-
r"""scripts/t228_scan_missing_diacritics.py — quét lỗi chính tả do tôi gây ra.

Bài học từ lần quét đầu: danh sách từ "thiếu dấu" phải **rất hẹp**. Tiếng Việt có
nhiều từ hợp lệ khi không dấu: `cho`, `sau`, `theo`, `sai`, `thu`, `ra`, `mo`,
`dung`, `do`, `de`... dùng chúng làm tín hiệu sẽ thành báo động giả hàng loạt.

Vì vậy bộ detector chỉ gồm:
  A. CỤM SAI CHẮC CHẮN — chuỗi nhiều từ không bao giờ đúng khi thiếu dấu
     (`phan con lai`, `con so`, `nhuoc ban`, `cua T209`, ...).
  B. TỪ KHÔNG BAO GIỜ ĐÚNG KHÔNG DẤU — nhóm rất hẹp (`khong`, `duoc`, `nguoi`, ...).
  C. SAI DẤU / LẶP ÂM — mẫu cụ thể tôi đã mắc (`CHo`, `Phân phân`, `ngường`...).

Chỉ soi **dòng tôi thêm** so với HEAD (tránh báo lỗi có sẵn từ trước).
Dùng: python -X utf8 scripts/t228_scan_missing_diacritics.py
"""
import io
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(BASE, '..', '..'))
P = 'Dai_Tang_Kinh/daoanh/'

TARGETS = [
    'docs/Mimo-Flash/X-T177-dynamic-filter-absorb-directive-v2.md',
    'docs/Mimo-Flash/T222-cloud-session-chain-c1-c6-plan.md',
    'docs/Handoff-2026-10-02-T222-id-hygiene.md',
    'docs/tasktodo.md',
    'docs/ROLLBACK.md',
    'docs/TTL-FILE-STATUS-REPORT.md',
    'docs/TTL-FILE-NAMES-T209.txt',
    'AGENTS.md',
    'tasks/T18-bdrc-integration-decision.md',
    'tasks/T27-source-neutral-entity-id.md',
    'tasks/T192-t173-plan-doc-correction.md',
    'tasks/T196-git-update-ref-master-blocked.md',
    'tasks/T197-t177-review-correction.md',
    'tasks/T200-vnpa-dila-id-duplicate-limit1.md',
    'tasks/T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md',
    'scripts/t209_export_file_names.py',
    'scripts/t209_hashfill_and_refresh.py',
    'scripts/t220_renumber_dup_ids.py',
    'scripts/t220_fix_renumber_aftermath.py',
    'scripts/t220_plan_doc_t222.py',
    'scripts/t225_fix_task_status.py',
    'scripts/t225_fix_task_status_v2.py',
    'scripts/t225_fix_t65_t66_board.py',
    'scripts/t225_promote_done_7.py',
    'scripts/t226_close_t197_t18.py',
    'scripts/t227_t200_waits_t223.py',
    'scripts/t227_fix_t200_banner.py',
    'scripts/t227_fix_t200_note.py',
    'scripts/build_progress_data.py',
    'tests/test_t216_dup_ids_guard.py',
]

# A. CỤM SAI CHẮC CHẮN
PHRASES = [
    'phan con lai', 'con lai CH', 'con so ', 'con so\n', 'nhuoc ban',
    'cua T2', 'cua Admin', 'do lai', 'gia tri', 'chua duoc', 'khong duoc',
    'se thuc hien', 'thu tu sua', 'quet dinh', 'vao tai cho', 'quet ref',
]

# B. TỪ KHÔNG BAO GIỜ ĐÚNG KHÔNG DẤU (hẹp)
WORDS = ['khong', 'duoc', 'nguoi', 'nhom', 'chua', 'nhieu', 'thieu',
         'lien', 'quet', 'bien', 'viet', 'them', 'xoa', 'chay', 'thuoc',
         'nguon', 'kiem', 'dinh', 'hien', 'chuc', 'phai con', 'mo ta',
         'giai thich', 'sai lam', 'nghi sai']

# C. SAI DẤU / LẶP ÂM (mẫu chắc chắn)
WRONG = [
    (u'phan phân', u'phan phân -> phần phân'),
    (u'Phân phân', u'Phân phân -> Phần phân'),
    (u'ngường', u'ngường -> người'),
    (u'ngưống', u'ngưống -> người'),
    (u'ngư���i', u'người sai dấu'),
    (u'CHỏ', u'CHỏ -> CHỜ'),
    (u'CHở', u'CHở -> CHỜ'),
    (u'do ố tấi', u'do ố tấi'),
    (u'bên d��i', u'bên d��i'),
    (u'\ufffd', u'ky tu thay the U+FFFD'),
]


def strip_code(line):
    s = re.sub(r'`[^`]*`', ' ', line)
    s = re.sub(r'https?://\S+', ' ', s)
    s = re.sub(r'\b[\w./\\-]+\.(py|md|json|db|txt|csv|html|js)\b', ' ', s)
    s = re.sub(r'\b\d[\d.,/%]*\b', ' ', s)
    s = re.sub(r'^[\s>#\-*|+=]+', ' ', s)
    return s


def main():
    total = 0
    for rel in TARGETS:
        disk = os.path.join(BASE, rel)
        if not os.path.exists(disk):
            print('[MISSING] %s' % rel)
            continue
        r = subprocess.run(['git', 'show', 'HEAD:' + P + rel], capture_output=True,
                           text=True, cwd=REPO)
        cur = io.open(disk, encoding='utf-8', errors='replace').read().split('\n')
        if r.stdout:
            old = set(r.stdout.split('\n'))
            adds = [(i, l) for i, l in enumerate(cur, 1) if l.strip() and l not in old]
        else:
            adds = list(enumerate(cur, 1))
        hits = []
        for ln, line in adds:
            why = None
            for pat, desc in WRONG:
                if pat in line:
                    why = 'SAI DAU: ' + desc
                    break
            if not why:
                prose = strip_code(line)
                low = prose.lower()
                for ph in PHRASES:
                    if ph in low:
                        why = 'CUM SAI: %r' % ph
                        break
            if not why:
                prose = strip_code(line)
                for w in WORDS:
                    if re.search(r'(?<![A-Za-z])' + re.escape(w) + r'(?![A-Za-z])',
                                 prose, re.I):
                        why = 'THIEU DAU: %r' % w
                        break
            if why:
                hits.append((ln, why, line))
        if hits:
            total += len(hits)
            print()
            print('=== %s (%d) ===' % (rel, len(hits)))
            seen = set()
            for ln, why, line in hits:
                if ln in seen:
                    continue
                seen.add(ln)
                print('  L%-5d %s' % (ln, why))
                print('        %s' % line.strip()[:118])
    print()
    print('TONG DONG NGHI:', total)
    return 0


if __name__ == '__main__':
    sys.exit(main())