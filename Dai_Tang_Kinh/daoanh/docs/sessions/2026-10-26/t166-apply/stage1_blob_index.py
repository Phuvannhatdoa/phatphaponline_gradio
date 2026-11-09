# -*- coding: utf-8 -*-
"""T166 bước 4-5a: dựng blob ROLLBACK.md mới + index tạm (KHÔNG chạm worktree / index thật)."""
import os
import subprocess
import sys

R = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app'
D = 'Dai_Tang_Kinh/daoanh'
EV = D + '/docs/sessions/2026-10-26/t166-apply'
RPATH = D + '/docs/ROLLBACK.md'
TMP_INDEX = os.path.join(R, EV.replace('/', os.sep), 'tmp.index')


def git(*args, env=None):
    r = subprocess.run(['git', *args], cwd=R, capture_output=True, env=env)
    return r.returncode, r.stdout.decode('utf-8', 'replace').strip(), r.stderr.decode('utf-8', 'replace').strip()


parent = git('rev-parse', 'HEAD')[1]
print('PARENT', parent)
rc, ls, _ = git('ls-tree', parent, RPATH)
print('LS-TREE', ls)
mode, _typ, head_blob_sha = ls.split()[0], ls.split()[1], ls.split()[2].split('\t')[0]

head_bytes = open(os.path.join(R, EV.replace('/', os.sep), 'ROLLBACK.head.bytes'), 'rb').read()
head_sha_from_bytes = subprocess.run(['git', 'hash-object', os.path.join(R, EV.replace('/', os.sep), 'ROLLBACK.head.bytes')],
                                     cwd=R, capture_output=True).stdout.decode().strip()
print('HEAD_BLOB', head_blob_sha, 'SAVED_BYTES_SHA', head_sha_from_bytes, 'MATCH' if head_sha_from_bytes == head_blob_sha else 'MISMATCH')
if head_sha_from_bytes != head_blob_sha:
    sys.exit('STOP: bản lưu không khớp blob HEAD')

app_bytes = open(os.path.join(R, EV.replace('/', os.sep), 'append.md'), 'rb').read()
new_bytes = head_bytes + app_bytes
assert new_bytes.startswith(head_bytes)
new_file = os.path.join(R, EV.replace('/', os.sep), 'ROLLBACK.new.bytes')
open(new_file, 'wb').write(new_bytes)
rc, new_blob, err = git('hash-object', '-w', EV + '/ROLLBACK.new.bytes')
print('NEW_BLOB', new_blob, rc, err)

env = dict(os.environ, GIT_INDEX_FILE=TMP_INDEX)
if os.path.exists(TMP_INDEX):
    os.remove(TMP_INDEX)
print('READ-TREE', git('read-tree', parent, env=env))
print('UPDATE-INDEX', git('update-index', '--add', '--cacheinfo', f'{mode},{new_blob},{RPATH}', env=env))
print('DIFF-CACHED-NAME-STATUS', git('diff', '--cached', '--name-status', env=env))
print('DIFF-CACHED-NUMSTAT', git('diff', '--cached', '--numstat', env=env))
