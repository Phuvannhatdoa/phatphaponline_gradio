# -*- coding: utf-8 -*-
"""T449 — guard `scripts/audit_h3_conflicts.py` (T263 evidence).

Kiểm: (1) chặn ghi khi số dòng mới < 50% file cũ (giữ nguyên SHA256, KHÔNG ghi),
(2) `--force` bỏ qua guard, (3) ghi atomic (không để file nửa vời / không sót .tmp),
(4) tên file giữ nguyên DATE hard-code, (5) không ghi DB.

Chạy: python -X utf8 tests/test_t449_audit_h3_guard.py   (không cần API key)
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT = os.path.join(ROOT, 'scripts', 'audit_h3_conflicts.py')
DB = os.path.join(ROOT, 'data', 'lineage.db')
DATE = '2026-10-08'
TSV_NAME = '%s_T263_h3_conflicts.tsv' % DATE
SUM_NAME = '%s_T263_h3_conflicts_summary.tsv' % DATE

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print('  OK. %s' % name)
    else:
        FAIL += 1
        print('  FAIL. %s%s' % (name, (' — ' + str(detail)) if detail else ''))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def run(out_dir, *extra):
    cmd = [sys.executable, '-X', 'utf8', SCRIPT, '--out', out_dir] + list(extra)
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def seed_old_evidence(out_dir, rows=400):
    """File evidence cũ 'tốt' (407 dòng thật ~ 400 dòng fake) + summary."""
    os.makedirs(out_dir, exist_ok=True)
    tsv = os.path.join(out_dir, TSV_NAME)
    with open(tsv, 'w', encoding='utf-8', newline='\n') as f:
        f.write('dila_id\tyear\tr_derived\tera_name\tn\tera_span\tgroup\tghi_chu\n')
        for i in range(rows):
            f.write('FAKE%04d\t1000\t1000\tX\t1\t-\tA\tfake\n' % i)
    summ = os.path.join(out_dir, SUM_NAME)
    with open(summ, 'w', encoding='utf-8', newline='\n') as f:
        f.write('group\tcount\tmo_ta\nB\t47\tx\nC\t79\tx\nA\t280\tx\n')
    return tsv, summ


def data_rows(path):
    with open(path, 'r', encoding='utf-8') as f:
        return max(0, len(f.read().strip().split('\n')) - 1)


def main():
    tmp = tempfile.mkdtemp(prefix='t449_')
    try:
        db_before = sha256(DB) if os.path.exists(DB) else None

        # --- A) guard: dữ liệu mới (0 dòng) < 50% file cũ (400 dòng) -> KHÔNG ghi
        guard_dir = os.path.join(tmp, 'guard')
        tsv, summ = seed_old_evidence(guard_dir)
        tsv_sha, sum_sha = sha256(tsv), sha256(summ)
        r = run(guard_dir)
        check('A1 exit 0 (WARN, không fail pipeline)', r.returncode == 0, r.returncode)
        check('A2 in canh bao [GUARD]', '[GUARD]' in (r.stdout or ''), (r.stdout or '')[-200:])
        check('A3 khong ghi de tsv (SHA256 giu nguyen)', sha256(tsv) == tsv_sha)
        check('A4 khong ghi de summary (SHA256 giu nguyen)', sha256(summ) == sum_sha)
        check('A5 khong sot file .tmp', not [n for n in os.listdir(guard_dir) if n.endswith('.tmp')],
              os.listdir(guard_dir))

        # --- B) --force: bỏ guard, ghi lại đúng dữ liệu thật
        r = run(guard_dir, '--force')
        check('B1 exit 0', r.returncode == 0, r.returncode)
        check('B2 khong in [GUARD]', '[GUARD]' not in (r.stdout or ''))
        check('B3 tsv duoc ghi lai (khac file fake 400 dong)', data_rows(tsv) != 400, data_rows(tsv))
        check('B4 khong con .tmp', not [n for n in os.listdir(guard_dir) if n.endswith('.tmp')])
        with open(summ, 'r', encoding='utf-8') as f:
            body = f.read()
        check('B5 summary ghi lai theo so lieu that', 'count' in body and '280' not in body, body[:80])

        # --- C) chạy lần đầu ở thư mục trống -> ghi được, tên file giữ nguyên DATE
        fresh = os.path.join(tmp, 'fresh')
        r = run(fresh)
        check('C1 exit 0', r.returncode == 0, r.returncode)
        check('C2 tao tsv dung ten DATE hard-code', os.path.exists(os.path.join(fresh, TSV_NAME)))
        check('C3 tao summary dung ten', os.path.exists(os.path.join(fresh, SUM_NAME)))
        check('C4 khong co .tmp', not [n for n in os.listdir(fresh) if n.endswith('.tmp')])

        # --- D) không ghi DB
        if db_before:
            check('D1 DB khong bi ghi (SHA256 giu nguyen)', sha256(DB) == db_before)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('\nT449 guard tests: %d PASS / %d FAIL' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
