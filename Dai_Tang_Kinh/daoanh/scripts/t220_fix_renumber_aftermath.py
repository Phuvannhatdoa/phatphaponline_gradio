# -*- coding: utf-8 -*-
r"""Vá hậu quả của t220_renumber_dup_ids.py.

Lỗi: hàm full_renumber() chèn `former_ids: [<old>]` rồi mới thay token toàn cục,
nên chính giá trị trong former_ids cũng bị đổi theo (T180,T216 -> T180,T217).
Ở đây vá lại + đổi T215 -> T220 trong report doc (giữ nguyên T216) + sửa 3 tham chiếu.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REFS = ['docs/Mimo-Flash/X-T165-rules-constrained-translation-engine-SPEC.md',
        'docs/Mimo-Flash/X-T168-rule-resolver-context-compiler-PLAN.md',
        'docs/sessions/2026-09-24_t167-rules-constrained-translation-engine.md']
RENAME = 'T158-glossary-resolver-pre-translation-lookup'
RENAME_NEW = 'T218-glossary-resolver-pre-translation-lookup'


def patch(rel, pairs):
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print('  [SKIP] không tồn tại: %s' % rel)
        return True
    s = io.open(p, encoding='utf-8').read()
    orig = s
    for a, b in pairs:
        if s.count(a) == 0:
            print('  [FAIL] %s: không có %r' % (rel, a[:60]))
            return False
        s = s.replace(a, b)
    if s == orig:
        print('  [----] %s: không đổi' % rel)
        return True
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('  OK  %s (%d cặp thay)' % (rel, len(pairs)))
    return True


ok = True

print('[1] vá lại former_ids bị global-replace làm hỏng')
ok &= patch('docs/Mimo-Flash/T217-cloud-session-chain-c1-c6-plan.md',
            [('former_ids: [T180, T217]', 'former_ids: [T180, T216]')])
ok &= patch('tasks/T220-vnpa-dila-id-recovery.md',
            [('former_ids: [T220]', 'former_ids: [T215]')])
ok &= patch('tasks/T218-glossary-resolver-pre-translation-lookup.md',
            [('former_id: T158', 'former_ids: [T158]')])
ok &= patch('tasks/T219-pl-corrupt-canonical-name-vi-fix.md',
            [('former_id: T206', 'former_ids: [T206]')])

print('[2] report doc: T215 -> T220 (T216 giữ nguyên)')
ok &= patch('docs/Mimo-Flash/T220-VNPA-DILA-ID-RECOVERY-01.md',
            [('T215', 'T220')])

print('[3] 3 tham chiếu của task glossary-resolver')
for rel in REFS:
    ok &= patch(rel, [(RENAME, RENAME_NEW)])

print('')
print('KẾT QUẢ:', 'OK' if ok else 'CÓ LỖI')
sys.exit(0 if ok else 1)