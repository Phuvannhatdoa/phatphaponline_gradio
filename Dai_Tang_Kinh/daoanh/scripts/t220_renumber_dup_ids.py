# -*- coding: utf-8 -*-
r"""Đổi số 4 task/file để gỡ trùng ID + trả T216 cho ETL follow-up đã đặt chỗ.

Gánh nặng:
  T216 -> giữ cho "ETL UPSERT guard" (đã đặt chỗ bằng prose ở 4 file, task thật chờ Admin)
  T216 -> T217  docs/Mimo-Flash/plan cloud-session-chain (plan doc của tôi)
  T158 -> T218  tasks/...glossary-resolver-pre-translation-lookup
  T206 -> T219  tasks/...pl-corrupt-canonical-name-vi-fix
  T215 -> T220  tasks/...vnpa-dila-id-recovery
Mỗi file ghi `former_ids:` để ID cũ vẫn grep được.

Script idempotent: chạy lại sẽ báo SKIP thay vì sửa đè.
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EM = u'—'
OLD = 'docs/Mimo-Flash/T216-cloud-session-chain-c1-c6-plan.md'
NEW = 'docs/Mimo-Flash/T217-cloud-session-chain-c1-c6-plan.md'


def rd(p):
    return io.open(p, encoding='utf-8').read()


def full_renumber(old_rel, new_rel, old_id, new_id, former):
    """Thay toàn cục token ID (mọi xuất hiện đều tự tham chiếu) + ghi former_ids."""
    op = os.path.join(BASE, old_rel)
    np_ = os.path.join(BASE, new_rel)
    if not os.path.exists(op):
        if os.path.exists(np_):
            print('  [SKIP] đã đổi rồi: %s' % os.path.basename(new_rel))
            return True
        print('  [FAIL] không tồn tại: %s' % old_rel)
        return False
    s = rd(op)
    head = 'id: %s\n' % old_id
    if s.count(head) != 1:
        print('  [FAIL] id không khớp duy nhất (%d lần)' % s.count(head))
        return False
    s = s.replace(head, 'id: %s\nformer_ids: [%s]\n' % (new_id, former))
    s = s.replace(old_id, new_id)
    io.open(np_, 'w', encoding='utf-8', newline='\n').write(s)
    os.remove(op)
    print('  OK  %s  ->  %s   (%s -> %s)'
          % (os.path.basename(old_rel), os.path.basename(new_rel), old_id, new_id))
    return True


ok = True

print('[1] glossary-resolver: T158 -> T218')
ok &= full_renumber(
    'tasks/T158-glossary-resolver-pre-translation-lookup.md',
    'tasks/T218-glossary-resolver-pre-translation-lookup.md',
    'T158', 'T218', 'T158')

print('[2] pl-corrupt: T206 -> T219')
ok &= full_renumber(
    'tasks/T206-pl-corrupt-canonical-name-vi-fix.md',
    'tasks/T219-pl-corrupt-canonical-name-vi-fix.md',
    'T206', 'T219', 'T206')

print('[3] vnpa-dila-id-recovery: T215 -> T220')
ok &= full_renumber(
    'tasks/T215-vnpa-dila-id-recovery.md',
    'tasks/T220-vnpa-dila-id-recovery.md',
    'T215', 'T220', 'T215')

print('[4] report doc: T215-VNPA-DILA-ID-RECOVERY-01 -> T220-...')
old_rel = 'docs/Mimo-Flash/T215-VNPA-DILA-ID-RECOVERY-01.md'
new_rel = 'docs/Mimo-Flash/T220-VNPA-DILA-ID-RECOVERY-01.md'
op = os.path.join(BASE, old_rel)
if os.path.exists(op):
    s = rd(op)
    s = s.replace('# T215 ' + EM + ' VNPA DILA-ID Recovery',
                  '# T220 ' + EM + ' VNPA DILA-ID Recovery')
    s = s.replace('**Task ID:** T215-VNPA-DILA-ID-RECOVERY-01',
                  '**Task ID:** T220-VNPA-DILA-ID-RECOVERY-01')
    io.open(os.path.join(BASE, new_rel), 'w', encoding='utf-8',
            newline='\n').write(s)
    os.remove(op)
    print('  OK  report doc -> %s' % os.path.basename(new_rel))
else:
    print('  [SKIP] không tồn tại')
    ok = False

print('')
print('KẾT QUẢ:', 'OK' if ok else 'CÓ LỖI - cần xem lại')
sys.exit(0 if ok else 1)