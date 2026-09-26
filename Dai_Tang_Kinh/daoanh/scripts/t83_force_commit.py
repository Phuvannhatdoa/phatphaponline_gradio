#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t83_force_commit.py — Commit docs T150b TRÊN volume E:\\Backup 2025 bị block rename/unlink.
(Workaround T83: dành riêng cho index + refs + object=> dùng GIT_INDEX_FILE tạm + byte-write.)

BỐI CẢNH:
  git add / git commit thất bại "unable to write new index file"
  vì backup/sync agent CHẶN rename/unlink file (.git/index.lock -> .git/index).
  Ghi-đè BYTE trực tiếp (giữ inode) HOẠT ĐỘNG.

GIẢI PHÁP (commit qua plumbing, không chạm .git/index bằng rename):
  1) Dùng GIT_INDEX_FILE=<temp> + git read-tree/add/write-tree => tạo tree object mới.
  2) git commit-tree => tạo commit object (parent = HEAD).
  3) Ghi index tạm byte-wise vào .git/index (giữ inode).
  4) Ghi SHA commit byte-wise vào .git/refs/heads/master (keep inode).
  Kết quả: HEAD trỏ commit mới, index đồng bộ, git status sạch (chỉ còn file khác).

Cách dùng (Admin "vô não"):
  python scripts/t83_force_commit.py                 # tự commit (dry-run trước)
  python scripts/t83_force_commit.py --apply         # thực hiện thật
  python scripts/t83_force_commit.py --status        # in trạng thái HEAD/index/ref
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DAOANH_DIR = os.path.dirname(SCRIPTS_DIR)
REPO_ROOT = os.path.dirname(os.path.dirname(DAOANH_DIR))  # .../visjs-app

INDEX_PATH = os.path.join(REPO_ROOT, '.git', 'index')
REF_PATH = os.path.join(REPO_ROOT, '.git', 'refs', 'heads', 'master')

# Files thuộc commit T150b (repo-relative, cần `-f` cho data/ bị gitignore)
FILES = [
    'Dai_Tang_Kinh/daoanh/tasks/T150b-reseed-namevi-post-t149.md',
    'Dai_Tang_Kinh/daoanh/docs/tasktodo.md',
    'Dai_Tang_Kinh/daoanh/docs/progress.md',
    'Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md',
    'Dai_Tang_Kinh/daoanh/data/progress_data.json',
]
MESSAGE = 'docs: T150b closure - reseed name_vi post T149 (T162 implemented 2026-09-22) + docs'

COMMIT_FILES = FILES
COMMIT_MESSAGE = MESSAGE


def git(*args, cwd=REPO_ROOT, env=None):
    out = subprocess.run(['git', '-c', 'safe.directory=*', '-C', cwd] + list(args),
                         capture_output=True, text=True, encoding='utf-8',
                         errors='replace', env=env)
    if out.returncode != 0:
        sys.stderr.write('[GIT ERR] ' + ' '.join(args) + '\n' + out.stderr)
        sys.exit(1)
    return out.stdout.strip()


def author_env():
    """Lấy author từ commit cuối (~/.gitconfig của repo) => env GIT_AUTHOR/COMMITTER."""
    who = git('log', '-1', '--format=%an|%ae')
    if '|' not in who:
        return dict(os.environ)
    name, email = who.split('|', 1)
    env = dict(os.environ)
    for k, v in (('GIT_AUTHOR_NAME', name), ('GIT_AUTHOR_EMAIL', email),
                 ('GIT_COMMITTER_NAME', name), ('GIT_COMMITTER_EMAIL', email)):
        env[k] = v
    return env


def read_file(path):
    try:
        with open(path, 'rb') as f:
            return f.read()
    except OSError:
        return None


def write_bytes(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def do_status():
    head = git('rev-parse', 'HEAD')
    ref = (read_file(REF_PATH) or b'').decode('ascii', 'replace').strip()
    idx = (read_file(INDEX_PATH) or b'')
    print('[STATUS]')
    print(f'  HEAD         : {head}')
    print(f'  refs/HEAD    : {ref}')
    print(f'  .git/index   : {len(idx)} bytes')
    if head != ref:
        print('  [!] HEAD != ref file — kiểm tra.')


def build_commit():
    """Tạo tree+commit qua index tạm; trả (tree, commit)."""
    tmpdir = tempfile.mkdtemp(prefix='t83_idx_')
    tmp_index = os.path.join(tmpdir, 'index')
    env = dict(os.environ, GIT_INDEX_FILE=tmp_index)
    aenv = author_env()
    def g(*a):
        out = subprocess.run(['git', '-c', 'safe.directory=*', '-C', REPO_ROOT] + list(a),
                             capture_output=True, text=True, encoding='utf-8',
                             errors='replace', env=env)
        if out.returncode != 0:
            sys.stderr.write('[GIT ERR] ' + ' '.join(a) + '\n' + out.stderr)
            sys.exit(1)
        return out.stdout.strip()
    g('read-tree', 'HEAD')
    for f in COMMIT_FILES:
        g('add', '-f', f)
    tree = g('write-tree')
    commit = git('commit-tree', tree, '-p', 'HEAD', '-m', COMMIT_MESSAGE, env=aenv)
    shutil.rmtree(tmpdir, ignore_errors=True)
    return tree, commit


def do_apply(message=None, files=None):
    global COMMIT_FILES, COMMIT_MESSAGE
    COMMIT_FILES = list(files) if files else FILES
    COMMIT_MESSAGE = message if message else MESSAGE
    tree, commit = build_commit()
    head_before = git('rev-parse', 'HEAD')
    print(f'  parent HEAD  : {head_before}')
    print(f'  tree         : {tree}')
    print(f'  commit mới   : {commit}')
    git('cat-file', '-t', commit)  # verify object tồn tại đọc được
    tmpdir = tempfile.mkdtemp(prefix='t83_idx_')
    tmp_index = os.path.join(tmpdir, 'index')
    env = dict(os.environ, GIT_INDEX_FILE=tmp_index)
    subprocess.run(['git', '-c', 'safe.directory=*', '-C', REPO_ROOT, 'read-tree', 'HEAD'],
                   env=env, capture_output=True)
    for f in COMMIT_FILES:
        subprocess.run(['git', '-c', 'safe.directory=*', '-C', REPO_ROOT, 'add', '-f', f],
                       env=env, capture_output=True, text=True)
    index_new = read_file(tmp_index)
    shutil.rmtree(tmpdir, ignore_errors=True)
    if index_new is None:
        print('[ERR] không đọc được index tạm.')
        return 1
    # byte-write index (keep inode)
    if os.path.exists(INDEX_PATH):
        write_bytes(INDEX_PATH, index_new)
        print(f'  index byte-write: {len(index_new)} -> .git/index')
    # byte-write ref (keep inode)
    write_bytes(REF_PATH, commit.encode('ascii'))
    print(f'  ref byte-write  : refs/heads/master = {commit}')
    head_after = git('rev-parse', 'HEAD')
    print(f'  HEAD sau        : {head_after}')
    if head_after == commit:
        print('  [OK] commit xong. HEAD = ' + commit)
        return 0
    print('  [!!] HEAD lệch commit — kiểm tra lại.')
    return 1


def main():
    p = argparse.ArgumentParser(description='Force commit (byte-write, T83).')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--status', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--dry-run', action='store_true')
    p.add_argument('--message', default=MESSAGE, help='commit message')
    p.add_argument('--files', nargs='*', default=FILES, help='files (repo-relative)')
    a = p.parse_args()
    if a.status:
        return do_status()
    if a.dry_run:
        print('[DRY-RUN] sẽ:')
        for f in a.files:
            print(f'   add -f {f}')
        print(f'   commit -m "{a.message}"')
        print('  (byte-write index + refs/heads/master — chạy --apply để thực hiện)')
        return 0
    return do_apply(a.message, a.files)


if __name__ == '__main__':
    sys.exit(main())