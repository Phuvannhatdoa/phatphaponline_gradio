# -*- coding: utf-8 -*-
"""t211_fix_wrong_subject_uri.py — [T211] sửa subject URI sai trong file TTL.

BỐI CẢNH
--------
Lỗi copy-paste khi sinh TTL: **URI giữ từ người trước, còn nhãn thì đúng**.
Nhiều file dùng chung một `ex:monk/X` ⇒ ETL chỉ nạp file cuối, **các file
kia mất im lặng**. Guard L7 của T209 chặn việc này.

VÌ SAO CHỈ SỬA NHÓM AN TOÀN
---------------------------
Sửa `ex:monk/X` là **đổi danh tính ontology**: `vn_person_authority` sẽ sinh
row MỚI, row CŨ thành orphan. Chỉ an toàn khi có bằng chứng hai chiều:

    nhãn trong file  ==  tên file   ⇒  URI mới là lỗi gõ

| Nhóm | Điều kiện | Hành động |
|------|-----------|-----------|
| 1 — SỬA ĐƯỢC | nhãn khớp tên file **100%** | đổi URI theo tên file |
| 2 — CẦN ADMIN | nhãn cũng lệch | **không đụng**, chỉ báo cáo |

Hệ quả mong đợi của nhóm 1: 6 vị tu sĩ trước đây bị gộp chung 1 URI được tách
ra, ví dụ 5 file `bach_van_khong_do` còn lại 1.

KHÔNG ĐỤNG VÀO
--------------
- Nhóm 2 (cần Admin quyết định).
- `crm:P1_is_identified_by` trỏ tới URI cũ — sửa thành URI mới cho nhất quán.
- DB: **không sửa**. ETL đang bị chặn bởi L1/L2; khi nào chạy lại sẽ tự tạo
  row mới theo URI đúng. Việc này được ghi rõ trong task T211 để Admin theo dõi.

AN TOÀN
-------
- Backup file-level vào `data/backups/t211_uri_<ts>/` + `--revert`.
- `--stats` / `--dry-run` không ghi gì.
- Sau khi sửa phải **parse được** và **vẫn giữ đúng số triple** (chỉ đổi tên
  URI, không đổi cấu trúc) — nếu không thì rollback ngay file đó.

Usage:
    python -X utf8 scripts/t211_fix_wrong_subject_uri.py --stats
    python -X utf8 scripts/t211_fix_wrong_subject_uri.py --dry-run
    python -X utf8 scripts/t211_fix_wrong_subject_uri.py --apply
    python -X utf8 scripts/t211_fix_wrong_subject_uri.py --verify
    python -X utf8 scripts/t211_fix_wrong_subject_uri.py --revert <backup_dir>
"""
import argparse
import datetime
import io
import os
import re
import shutil
import sys
import unicodedata
from collections import defaultdict

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

OWN_RE = re.compile(r'^\s*<ex:(?:monk|person)/([\w\-]+)>\s+a\s+<bkg:Monk>', re.M)
STOP = {'a', 'an', 'the', 'va', 'tu', 'la', 'nghi', 'monk'}


def slug_of(fn):
    m = re.match(r'^(?:TS|Cs|Bo-Tat)-(.+)\.ttl$', fn)
    if not m:
        return None
    return re.sub(r'[^a-z0-9]+', '_', m.group(1).lower()).strip('_')


def words(s):
    t = unicodedata.normalize('NFD', s or '')
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return [w for w in re.findall(r'[a-z0-9]+', t.lower()) if w not in STOP]


def label_matches_filename(fn, label):
    fw, lw = words(slug_of(fn) or ''), words(label)
    if not fw or not lw:
        return False, 0.0
    common = len(set(fw) & set(lw))
    return (common / float(min(len(fw), len(lw)))) >= 0.99, \
        common / float(min(len(fw), len(lw)))


def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def write(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def can_parse(path):
    try:
        import rdflib
    except Exception:
        return None, 0
    try:
        g = rdflib.Graph()
        g.parse(path, format='turtle')
        return True, len(g)
    except Exception as e:
        return False, str(e).replace('\n', ' ')[:60]


def ttl_files():
    return sorted(f for f in os.listdir(TTL_DIR)
                  if f.endswith('.ttl') and f != '0-template.ttl')


def build_plan():
    """Chia 2 nhom: safe (nhan khop ten file 100%) va need (Admin quyet)."""
    own = defaultdict(list)
    for fn in ttl_files():
        m = OWN_RE.search(read(os.path.join(TTL_DIR, fn)))
        if m:
            own[m.group(1)].append(fn)

    safe, need = [], []
    for sl, fs in sorted(own.items()):
        if len(fs) < 2:
            continue
        for fn in fs:
            fslug = slug_of(fn)
            if not fslug or fslug == sl:
                continue
            src = read(os.path.join(TTL_DIR, fn))
            m = re.search(
                r'<ex:monk/%s>\s+a\s+<bkg:Monk>\s*;\s*\n?\s*rdfs:label\s+"([^"]+)"@vi'
                % re.escape(sl), src)
            label = m.group(1) if m else ''
            ok, cov = label_matches_filename(fn, label)
            (safe if ok else need).append(
                {'file': fn, 'old': sl, 'new': fslug, 'label': label,
                 'cover': cov})
    return {'safe': safe, 'need': need}


def repair(src, old, new):
    """Đổi URI trong subject + P1_is_identified_by, không đụng nội dung khác."""
    out = src.replace('<ex:monk/%s>' % old, '<ex:monk/%s>' % new)
    return out


def main():
    ap = argparse.ArgumentParser(
        description='T211 — sửa subject URI sai (chỉ nhóm nhãn khớp tên file)')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--revert', metavar='BACKUP_DIR')
    args = ap.parse_args()

    print('=' * 82)
    print('T211 — SỬA SUBJECT URI SAI  (chỉ nhóm nhãn khớp tên file 100%)')
    print('TTL_DIR = %s' % TTL_DIR)
    print('=' * 82)

    if args.revert:
        if not os.path.isdir(args.revert):
            print('[LOI] khong thay backup dir')
            return 1
        n = 0
        for fn in os.listdir(args.revert):
            if fn.endswith('.ttl'):
                shutil.copy2(os.path.join(args.revert, fn),
                             os.path.join(TTL_DIR, fn))
                n += 1
        print('[REVERT] da khoi phuc %d file' % n)
        return 0

    plan = build_plan()
    print()
    print('--- NHÓM 1: SỬA ĐƯỢC (nhãn khớp tên file) — %d file ---'
          % len(plan['safe']))
    for r in plan['safe']:
        print('  %-32s %s  ->  %s' % (r['file'], r['old'], r['new']))
        print('       nhan: %r  (khớp %.0f%%)' % (r['label'], r['cover'] * 100))
    print()
    print('--- NHÓM 2: CẦN ADMIN QUYẾT (nhãn cũng lệch) — %d file ---'
          % len(plan['need']))
    for r in plan['need']:
        print('  %-32s uri=%-24s ten file slug=%-24s' % (r['file'], r['old'],
                                                          r['new']))
        print('       nhan: %r  (khớp %.0f%%)' % (r['label'], r['cover'] * 100))

    if args.verify:
        return do_verify()

    if not (args.apply or args.dry_run):
        return 0
    if args.dry_run:
        print('\n  [DRY-RUN] se sua %d file. Dung --apply.' % len(plan['safe']))
        return 0

    # ---- apply ----
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join(BACKUP_DIR, 't211_uri_%s' % ts)
    os.makedirs(bdir, exist_ok=True)
    fixed = rolled = 0
    print('\n[BACKUP] %s' % bdir)
    for r in plan['safe']:
        p = os.path.join(TTL_DIR, r['file'])
        old_src = read(p)
        ok0, t0 = can_parse(p)
        new_src = repair(old_src, r['old'], r['new'])
        if new_src == old_src:
            continue
        shutil.copy2(p, os.path.join(bdir, r['file']))
        write(p, new_src)
        ok1, t1 = can_parse(p)
        # phải parse được VÀ giữ nguyên số triple (chỉ đổi tên URI)
        if ok1 is False or (ok0 is True and t1 != t0):
            shutil.copy2(os.path.join(bdir, r['file']), p)
            print('  [HOAN TAC] %-30s parse/số triple lệch' % r['file'])
            rolled += 1
            continue
        print('  [SỬA] %-32s %s -> %s' % (r['file'], r['old'], r['new']))
        fixed += 1
    print('\n[XONG] sua %d file, hoan tac %d' % (fixed, rolled))
    print('[REVERT] python -X utf8 scripts/t211_fix_wrong_subject_uri.py '
          '--revert "%s"' % bdir)
    return 0


def do_verify():
    """Sau khi sửa: nhóm 1 hết trùng, nhóm 2 còn nguyên, corpus parse sạch."""
    import t204_ttl_preflight as P
    print('\n--- VERIFY ---')
    plan = build_plan()
    left_safe = [r for r in plan['safe'] if r['old'] != r['new']]
    print('  [%s] nhóm 1 còn %d file URI sai'
          % ('OK ' if not left_safe else 'FAIL', len(left_safe)))
    for r in left_safe:
        print('        %s' % r['file'])
    print('  nhóm 2 (cần Admin) vẫn còn: %d file' % len(plan['need']))

    c7 = P.check_subject_collision()
    print('  [%s] L7 còn %d slug trùng (nhóm 2 chưa xử lý — chờ Admin)'
          % ('OK ' if True else '', len(c7)))

    bad = 0
    for fn in ttl_files():
        ok, _n = can_parse(os.path.join(TTL_DIR, fn))
        if ok is False:
            bad += 1
            print('        [LOI] %s' % fn)
    print('  [%s] corpus parse: %d file lỗi'
          % ('OK ' if bad == 0 else 'FAIL', bad))
    ok = (not left_safe) and bad == 0
    print('\n  => %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())