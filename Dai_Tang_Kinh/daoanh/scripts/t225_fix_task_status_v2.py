# -*- coding: utf-8 -*-
"""scripts/t225_fix_task_status_v2.py — SỬA LỖI CỦA BẢN V1.

Bản v1 (`t225_fix_task_status.py`) chỉ THÊM dòng `note:` mà KHÔNG thay giá trị
`status` — biến `block = src` rồi `block = src + note`, nên `replace(src, block)`
là no-op khi có note. Hậu quả: T196/T200/T27 vẫn giữ status cũ (kể cả 2 status
không hợp lệ), dù script in "OK" và commit ghi vào 1 dòng.

Bản này thay ĐÚNG `status: <old>` -> `status: <new>` và kiểm chứng bằng assert.

Ngoài ra: cây `tasks/T167-*.md` đã đúng (`in_progress`) nên bản v1 báo SKIP — giữ nguyên.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIX = [
    ('tasks/T196-git-update-ref-master-blocked.md', 'blocked', 'done'),
    ('tasks/T200-vnpa-dila-id-duplicate-limit1.md', 'build_done_admin_review', 'blocked'),
    ('tasks/T27-source-neutral-entity-id.md', 'blocked_until_needed', 'blocked'),
]


def main():
    ok = True
    print('[1] thay THAT gia tri status (v1 chi them note nen status chua doi)')
    for rel, old, new in FIX:
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            print('  [SKIP] khong ton tai: %s' % rel)
            continue
        s = io.open(p, encoding='utf-8').read()
        tgt = 'status: %s\n' % new
        if tgt in s:
            print('  [SKIP] %-44s da co status: %s' % (os.path.basename(rel)[:44], new))
            continue
        src = 'status: %s\n' % old
        n = s.count(src)
        if n != 1:
            print('  [FAIL] %s: so lan `status: %s` = %d (can 1)'
                  % (rel, old, n))
            ok = False
            continue
        s = s.replace(src, tgt, 1)
        # xac chung ngay tren chuoi vua ghi
        assert 'status: %s\n' % new in s, rel
        assert 'status: %s\n' % old not in s, rel
        io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
        print('  OK  %-44s status: %s -> %s' % (os.path.basename(rel)[:44], old, new))

    print('')
    print('[2] xac nhan T192 + T60/T61/T65/T66 van dung')
    CHECK = [
        ('tasks/T192-t173-plan-doc-correction.md', 'done'),
        ('tasks/T60-bio-vi-lexicon-phase2.md', 'pending'),
        ('tasks/T61-place-desc-vi-lexicon-diadanh.md', 'pending'),
        ('tasks/T65-bio-vi-lexicon-phase2.md', 'done'),
        ('tasks/T66-place-desc-vi-dila-note.md', 'done'),
    ]
    import re
    for rel, want in CHECK:
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            print('  [FAIL] thieu %s' % rel)
            ok = False
            continue
        s = io.open(p, encoding='utf-8').read()
        m = re.search(r'^status:\s*(\S+)', s, re.M)
        got = m.group(1) if m else '(khong co)'
        print('  %-46s %-9s %s' % (os.path.basename(rel)[:46], got,
                                  'OK' if got == want else 'SAI (mong doi %s)' % want))
        if got != want:
            ok = False

    print('')
    print('KET QUA:', 'OK' if ok else 'CO LOI')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())