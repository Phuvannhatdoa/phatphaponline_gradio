# -*- coding: utf-8 -*-
"""scripts/t225_promote_done_7.py — đưa 7 task `done` từ tasks/backup/ lên board.

Bối cảnh: `tasks/backup/` chứa 80 task `status: done`, nhưng dashboard chỉ quét
`tasks/*.md` cấp 1 (`os.listdir`) nên **7 task T6x bị giấu khỏi board** dù đã xong:
T62, T63, T64, T64b, T67, T68, T69.

Phạm vi: CHỈ 7 task này (nhóm T6x bị lẫn). 73 task legacy T01–T99 còn lại trong
backup giữ nguyên — đó là quyết định kiến trúc, không tự ý đụng.

Không `os.remove` (bị WinError 5 do AV giữ handle — đã gặp ở T65/T66). Thay vào đó
copy lên `tasks/` và ghi chú "đã nâng lên board" vào bản trong `backup/`.
Idempotent: chạy lại sẽ báo SKIP.
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(BASE, 'tasks')
B = os.path.join(T, 'backup')

PROMOTE = [
    ('T62-person-name-bulk-pattern-fix.md', 'T62'),
    ('T63-bio-vi-lexicon-phase1.md', 'T63'),
    ('T64-wikidata-timeline-import.md', 'T64'),
    ('T64b-wikidata-name-match.md', 'T64b'),
    ('T67-hitl-canonical-decision-provenance.md', 'T67'),
    ('T68-source-authority-conflict.md', 'T68'),
    ('T69-wire-evidence-entity-claims.md', 'T69'),
]

MARK = u'\n> **2026-10-02 (T225):** đã nâng lên board ở `tasks/%s`.\n'


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)


def main():
    ok = True
    print('[1] copy 7 task done len tasks/')
    for fname, tid in PROMOTE:
        src, dst = os.path.join(B, fname), os.path.join(T, fname)
        if os.path.exists(dst):
            s = read(dst)
            m = re.search(r'^status:\s*(\S+)', s, re.M)
            print('  [SKIP] tasks/%-44s status=%s' % (fname[:44],
                                                      m.group(1) if m else '?'))
            if not m or m.group(1) != 'done':
                ok = False
            continue
        if not os.path.exists(src):
            print('  [FAIL] thieu backup/%s' % fname)
            ok = False
            continue
        s = read(src)
        write(dst, s)
        st = re.search(r'^status:\s*(\S+)', s, re.M)
        print('  OK  tasks/%-44s id=%-5s status=%s (%d char)'
              % (fname[:44], tid, st.group(1) if st else '?', len(s)))

    print('[2] ghi chu "da nang len board" vao ban trong tasks/backup/')
    for fname, tid in PROMOTE:
        src = os.path.join(B, fname)
        if not os.path.exists(src):
            continue
        s = read(src)
        if 'T225):**' in s:
            print('  [SKIP] backup/%-44s da ghi chu' % fname[:44])
            continue
        write(src, s + (MARK % fname))
        print('  OK  backup/%-44s <- ghi chu' % fname[:44])

    print('[3] xac nhan 7 task tren board deu done')
    for fname, tid in PROMOTE:
        dst = os.path.join(T, fname)
        if not os.path.exists(dst):
            print('  [FAIL] thieu tasks/%s' % fname)
            ok = False
            continue
        s = read(dst)
        m = re.search(r'^status:\s*(\S+)', s, re.M)
        got = m.group(1) if m else '(khong co)'
        good = got == 'done'
        if not good:
            ok = False
        print('  %-46s %-9s %s' % (fname[:46], got,
                                   'OK' if good else 'SAI (mong doi done)'))

    print('')
    print('KET QUA:', 'OK' if ok else 'CO LOI')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())