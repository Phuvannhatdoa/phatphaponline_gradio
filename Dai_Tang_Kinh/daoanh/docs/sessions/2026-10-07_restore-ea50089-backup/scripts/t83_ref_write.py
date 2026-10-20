#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t83_ref_write.py — An toàn ghi/verify/rollback SHA commit vào refs/heads/master
(hoàn thành commit TAB_DAI_TANG trên volume E:\\Backup 2025 bị chặn rename/unlink git).

BỐI CẢNH (T83):
  Volume host repo là folder "Backup" có backup/sync agent CHẶN rename/unlink trên
  file git (.git/index, refs/heads/master) nên `git add`/`git commit` thất bại với
  "fatal: unable to write new index file" / "couldn't set 'refs/heads/master'".
  Đã xác minh: ghi-đè BYTE trực tiếp vào file ref (giữ nguyên inode) HOẠT ĐỘNG.

  Cách dùng an toàn (Admin "vô não"):
    python scripts/t83_ref_write.py --status                      # in trạng thái HEAD/ref/backup
    python scripts/t83_ref_write.py --dry-run --target <sha>      # xem sẽ làm gì (không ghi)
    python scripts/t83_ref_write.py --apply    --target <sha>     # ghi SHA commit vào master (guard+backup+verify)
    python scripts/t83_ref_write.py --verify   --target <sha>     # so ref vs git rev-parse HEAD
    python scripts/t83_ref_write.py --restore                     # ghi lại SHA backup (rollback 1-lệnh)

Quy ước an toàn vĩnh viễn: guard HEAD -> backup -> ghi BYTE -> verify -> (restore nếu lỗi).
KHÔNG BAO GIỜ rename/delete/probe ghi lên refs/heads/master ngoài cơ chế này.
"""

import argparse
import os
import subprocess
import sys

# Ép stdout UTF-8 (tiếng Việt / ký tự đặc biệt trên Windows console cp1252)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- Đường dẫn (độc lập với cwd) ---
# script: <visjs-app>/Dai_Tang_Kinh/daoanh/scripts/t83_ref_write.py
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DAOANH_DIR  = os.path.dirname(SCRIPTS_DIR)          # .../daoanh
REPO_ROOT   = os.path.dirname(os.path.dirname(DAOANH_DIR))   # .../visjs-app

REF_PATH   = os.path.join(REPO_ROOT, '.git', 'refs', 'heads', 'master')
BACKUP_REL = os.path.join(REPO_ROOT, '.git', 'daitang_master_backup')
BACKUP_ALT = os.path.join(REPO_ROOT, '.git', 'refs', 'heads', 'master.bak_t83')


def git(*args):
    """Chạy git tại REPO_ROOT, trả stdout trim."""
    out = subprocess.run(['git', '-C', REPO_ROOT] + list(args),
                         capture_output=True, text=True, encoding='utf-8',
                         errors='replace')
    return (out.stdout or '').strip()


def read_ref(path):
    try:
        with open(path, 'r', encoding='ascii') as f:
            return f.read().strip()
    except OSError:
        return None


def write_ref_byte(path, sha):
    """Ghi SHA (40 ký tự, không có trailing newline) theo cơ chế byte-write (giữ inode)."""
    with open(path, 'wb') as f:
        f.write(sha.encode('ascii'))


def do_status():
    head = git('rev-parse', 'HEAD')
    ref = read_ref(REF_PATH)
    bak = read_ref(BACKUP_REL)
    print('[STATUS]')
    print(f'  git rev-parse HEAD : {head}')
    print(f'  refs/heads/master  : {ref}')
    print(f'  backup (.git\\daitang_master_backup): {bak}')
    if head != ref:
        print('  [!] HEAD != ref file — có overwrite chỉ HEAD? kiểm tra.')


def do_dry_run(target, backup_too=None):
    head = git('rev-parse', 'HEAD')
    ref = read_ref(REF_PATH)
    print('[DRY-RUN] sẽ ghi refs/heads/master:')
    print(f'  từ   : {ref} (HEAD={head})')
    print(f'  tới  : {target}')
    if backup_too:
        print(f'  backup phụ: {BACKUP_ALT} = {backup_too}')
    print('  (chưa thực hiện ghi — dùng --apply để ghi)')


def do_apply(target, expected_parent=None):
    """Guard HEAD -> backup -> ghi byte -> verify."""
    head = git('rev-parse', 'HEAD')
    ref = read_ref(REF_PATH)
    if expected_parent and head != expected_parent:
        print(f'[ABORT] HEAD ({head}) != expected_parent ({expected_parent}). Không ghi đè.')
        return 2
    if not target or len(target) != 40:
        print(f'[ABORT] target không phải SHA 40 ký tự: {target!r}')
        return 2
    # backup (cả 2 chỗ — refs/...bak_t83 để tìm lại dễ, + file gốc backup)
    saved = []
    for bak in (BACKUP_ALT, BACKUP_REL):
        try:
            write_ref_byte(bak, ref)
            saved.append(bak)
        except OSError as e:
            print(f'  [WARN] không backup {bak}: {e}')
    print(f'  backup SHA {ref} -> {", ".join(saved)}')
    # ghi byte
    try:
        write_ref_byte(REF_PATH, target)
    except OSError as e:
        print(f'[ERR] ghi ref thất bại: {e}')
        return 1
    print(f'  đã ghi refs/heads/master = {target}')
    # verify
    after = git('rev-parse', 'HEAD')
    if after == target:
        print(f'  [OK] git rev-parse HEAD = {after}')
        return 0
    print(f'  [!!] HEAD sau ghi = {after} (khác target {target}). Xem --verify.')
    return 1


def do_verify(target):
    ref = read_ref(REF_PATH)
    head = git('rev-parse', 'HEAD')
    ok = (ref == head == target)
    print(f'  ref file = {ref}')
    print(f'  HEAD     = {head}')
    print(f'  expect   = {target}')
    print('  VERIFY: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


def do_restore():
    bak = read_ref(BACKUP_ALT) or read_ref(BACKUP_REL)
    if not bak:
        print('[ERR] không có backup để restore.')
        return 1
    try:
        write_ref_byte(REF_PATH, bak)
    except OSError as e:
        print(f'[ERR] restore thất bại: {e}')
        return 1
    head = git('rev-parse', 'HEAD')
    print(f'  đã restore ref = {bak}; HEAD = {head}')
    print('  RESTORE: ' + ('OK' if head == bak else 'LỆCH — kiểm tra HEAD symbolic'))
    return 0 if head == bak else 1


def main():
    p = argparse.ArgumentParser(description='An toàn ghi/verify/rollback refs/heads/master (T83).')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--status', action='store_true', help='in trạng thái HEAD/ref/backup')
    g.add_argument('--dry-run', action='store_true', help='xem sẽ làm gì (không ghi)')
    g.add_argument('--apply', action='store_true', help='ghi SHA commit vào master (guard+backup+verify)')
    g.add_argument('--verify', action='store_true', help='so ref vs git HEAD')
    g.add_argument('--restore', action='store_true', help='ghi lại SHA backup (rollback 1-lệnh)')
    p.add_argument('--target', help='SHA commit 40 ký tự (dùng cho --dry-run/--apply/--verify)')
    p.add_argument('--parent', help='expected parent HEAD (thường để trống = tự đọc)')
    a = p.parse_args()

    if a.status:
        return do_status()
    if a.dry_run:
        return do_dry_run(a.target)
    if a.apply:
        return do_apply(a.target, a.parent)
    if a.verify:
        return do_verify(a.target)
    if a.restore:
        return do_restore()
    return 0


if __name__ == '__main__':
    sys.exit(main())
