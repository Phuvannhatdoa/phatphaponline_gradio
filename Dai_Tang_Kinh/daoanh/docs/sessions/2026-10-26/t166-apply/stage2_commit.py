# -*- coding: utf-8 -*-
"""T166 bước 5: commit 1 file docs/ROLLBACK.md qua index tạm, CAS thủ công, rồi đồng bộ index thật. KHÔNG push."""
import os
import shutil
import subprocess
import sys

R = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app'
D = 'Dai_Tang_Kinh/daoanh'
EV = D + '/docs/sessions/2026-10-26/t166-apply'
EVD = os.path.join(R, EV.replace('/', os.sep))
RPATH = D + '/docs/ROLLBACK.md'
TMP_INDEX = os.path.join(EVD, 'tmp.index')
REAL_INDEX = os.path.join(R, '.git', 'index')
REF = os.path.join(R, '.git', 'refs', 'heads', 'truyen-dang-the-pho-clean')
MSG = 'chore: T166 apply migration identity (4 cot + index, additive) + rollback row'


def git(*args, env=None):
    r = subprocess.run(['git', *args], cwd=R, capture_output=True, env=env)
    return r.returncode, r.stdout.decode('utf-8', 'replace').strip(), r.stderr.decode('utf-8', 'replace').strip()


def read_ref():
    return open(REF, encoding='ascii').read().strip()


new_blob = git('rev-parse', EV + '/ROLLBACK.new.bytes')  # chỉ kiểm tra; blob đã có từ bước 4
new_blob = subprocess.run(['git', 'hash-object', EV + '/ROLLBACK.new.bytes'], cwd=R, capture_output=True).stdout.decode().strip()
print('NEW_BLOB', new_blob)
env = dict(os.environ, GIT_INDEX_FILE=TMP_INDEX)

if not os.path.exists(REF):
    sys.exit('STOP: không thấy ref file ' + REF)

# Pre-check: index thật phải sạch (không có staged nào của phiên khác)
rc, staged, err = git('diff', '--cached', '--name-only')
print('REAL_INDEX_STAGED_BEFORE =', repr(staged), rc, err)
if staged:
    sys.exit('STOP: index thật đang có staged của phiên khác: ' + staged)

result = None
for attempt in range(1, 4):
    parent = git('rev-parse', 'HEAD')[1]
    print(f'ATTEMPT {attempt} PARENT', parent)
    if os.path.exists(TMP_INDEX):
        os.remove(TMP_INDEX)
    assert git('read-tree', parent, env=env)[0] == 0
    assert git('update-index', '--add', '--cacheinfo', f'100644,{new_blob},{RPATH}', env=env)[0] == 0
    rc, ns, _ = git('diff', '--cached', '--name-status', env=env)
    print('  STAGED(tmp) =', repr(ns))
    if ns != 'M\t' + RPATH:
        sys.exit('STOP: index tạm không đúng 1 dòng M ROLLBACK.md')
    rc, numstat, _ = git('diff', '--cached', '--numstat', env=env)
    print('  NUMSTAT =', numstat)
    tree = git('write-tree', env=env)[1]
    print('  TREE', tree)
    new = git('commit-tree', tree, '-p', parent, '-m', MSG)[1]
    print('  NEW', new)
    # CAS thủ công: ref còn == parent?
    if read_ref() != parent:
        print('  CAS: HEAD đã đổi, dựng lại')
        continue
    with open(REF, 'w', encoding='ascii', newline='') as f:
        f.write(new + '\n')
    if git('rev-parse', 'HEAD')[1] != new:
        sys.exit('STOP: sau ghi ref, HEAD != new')
    result = (parent, new)
    break

if result is None:
    sys.exit('STOP: CAS thất bại 3 lần')

parent, new = result
print('COMMITTED parent=', parent, 'new=', new)
print(git('show', '--stat', '--format=%H %s', new)[1])
print('DIFF parent..new names:', git('diff', '--name-status', parent, new)[1])

# Đồng bộ index thật về HEAD mới: backup byte gốc, rồi ghi byte index tạm vào .git/index (r+b + truncate)
shutil.copy2(REAL_INDEX, os.path.join(EVD, 'index.bak'))
print('INDEX_BAK_SIZE', os.path.getsize(os.path.join(EVD, 'index.bak')))
# Tạo index tạm đồng bộ với new (tree của commit)
if os.path.exists(TMP_INDEX):
    os.remove(TMP_INDEX)
assert git('read-tree', new, env=env)[0] == 0
data = open(TMP_INDEX, 'rb').read()
with open(REAL_INDEX, 'r+b') as f:
    f.write(data)
    f.truncate()
print('REAL_INDEX_WRITTEN', len(data))
print('DIFF-CACHED after sync =', repr(git('diff', '--cached', '--name-status')[1]))
os.remove(TMP_INDEX)
print('DONE')
