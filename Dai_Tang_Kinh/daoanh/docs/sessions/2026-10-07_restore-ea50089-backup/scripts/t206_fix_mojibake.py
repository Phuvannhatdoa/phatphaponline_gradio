# -*- coding: utf-8 -*-
"""t206_fix_mojibake.py — [T206] sửa lỗi mojibake `Ð` (U+00D0) trong TTL.

LỖI GỐC
-------
Chữ Đ tiếng Việt là U+0110 (LATIN CAPITAL LETTER D WITH STROKE). Một số file TTL
bị ghi bằng **U+00D0 (LATIN CAPITAL LETTER ETH)** — ký tự không tồn tại trong
tiếng Việt, chỉ dùng cho tiếng Iceland. Kết quả: hiển thị "Ðại sư" thay vì
"Đại sư", "Ðề Hình" thay vì "Đề Hình".

Quy mô: 302 file / 590 ký tự (preflight T204 mã L4).

VÌ SAO SỬA HÀNG LOẠT AN TOÀN
--------------------------
Đã kiểm chứng trên corpus thật (1.038 file):
- **0** occurrence trong URI `<...>` ⇒ không đụng định danh ontology.
- **0** occurrence trong `@prefix` ⇒ không đụng khai báo namespace.
- **0** occurrence trong slug `ex:monk/...` ⇒ không đụng khóa/identity.
- **0** occurrence trong `rdfs:label@"zh"` ⇒ không đụng Hán tự.
- Chỉ nằm trong text tiếng Việt: `rdfs:label@"vi"` và `bkg:biographicalNote`.
- Token nhiều ký tự duy nhất: `Ðoan` ×38 (= "Đoàn") và `Ðam` ×1
  (= "Đàm", Pháp danh "Đàm Nguyên Ứng Chân") — đều là tiếng Việt.
- Corpus đã có sẵn **11.087** chữ `Đ` (U+0110) đúng ⇒ `Ð` chắc chắn là biến thể sai.

Script VẪN tự phòng vệ: nếu phát hiện `Ð` ở vị trí cấu trúc (URI/prefix/slug/zh)
thì **từ chối ghi** và báo lại, không âm thầm sửa.

AN TOÀN FILE
-------------
TTL không git track ⇒ backup file-level vào `data/backups/t206_mojibake_<ts>/`.
Chỉ ghi khi rdflib parse được TRƯỚC và SAU khi sửa; không sửa file làm hỏng.
`--revert <backup_dir>` khôi phục nguyên trạng.

Usage:
    python -X utf8 scripts/t206_fix_mojibake.py --stats
    python -X utf8 scripts/t206_fix_mojibake.py --dry-run
    python -X utf8 scripts/t206_fix_mojibake.py --apply
    python -X utf8 scripts/t206_fix_mojibake.py --verify
    python -X utf8 scripts/t206_fix_mojibake.py --revert data/backups/t206_mojibake_<ts>
"""
import argparse
import datetime
import io
import os
import re
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

# U+00D0 LATIN CAPITAL LETTER ETH  ->  U+0110 LATIN CAPITAL LETTER D WITH STROKE
BAD = '\u00d0'
GOOD = '\u0110'

# Vị trí KHÔNG được chứa ký tự lỗi (nếu phát hiện ⇒ abort, không sửa)
STRUCT_PATTERNS = (
    ('URI <>', re.compile(r'<[^>]*%s[^>]*>' % BAD)),
    ('@prefix', re.compile(r'@prefix[^.]*%s[^.]*\.' % BAD)),
    ('slug ex:monk/', re.compile(r'ex:(?:monk|person)/\S*%s' % BAD)),
    ('label @zh', re.compile(r'rdfs:label\s*"[^"]*%s[^"]*"@zh' % BAD)),
    ('label @sa', re.compile(r'rdfs:label\s*"[^"]*%s[^"]*"@(?:sa|jp|san)' % BAD)),
)


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
        return False, str(e).replace('\n', ' ')[:70]


def ttl_files():
    if not os.path.isdir(TTL_DIR):
        return []
    return sorted(f for f in os.listdir(TTL_DIR)
                  if f.endswith('.ttl') and f != '0-template.ttl')


def scan():
    """Trả [(file, path, n_bad, struct_violations)] cho file có ký tự lỗi."""
    out = []
    for fn in ttl_files():
        p = os.path.join(TTL_DIR, fn)
        s = read(p)
        n = s.count(BAD)
        if not n:
            continue
        bad_struct = [name for name, rx in STRUCT_PATTERNS if rx.search(s)]
        out.append((fn, p, n, bad_struct))
    return out


def show(rows, limit=12):
    rows_desc = sorted(rows, key=lambda r: -r[2])
    for fn, _p, n, st in rows_desc[:limit]:
        flag = ('  <== VI TRI CAU TRUC: %s' % ', '.join(st)) if st else ''
        print('   %-34s %3d%s' % (fn, n, flag))
    if len(rows) > limit:
        print('   ... va %d file khac' % (len(rows) - limit))
    tot = sum(r[2] for r in rows)
    viol = [r for r in rows if r[3]]
    print('   %-34s %3d ky tu / %d file' % ('TONG', tot, len(rows)))
    if viol:
        print('   [CHAN] %d file co %s o vi tri cau truc — KHONG sua'
              % (len(viol), ','.join(sorted({x for r in viol
                                            for x in r[3]}))))
    return tot, viol


def main():
    ap = argparse.ArgumentParser(
        description='T206 — sua mojibake Ð (U+00D0) -> Đ (U+0110) trong TTL')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--revert', metavar='BACKUP_DIR')
    args = ap.parse_args()

    if args.revert:
        bdir = args.revert
        if not os.path.isdir(bdir):
            print('[LOI] khong thay backup dir: %s' % bdir)
            return 1
        n = 0
        for fn in os.listdir(bdir):
            if not fn.endswith('.ttl'):
                continue
            shutil.copy2(os.path.join(bdir, fn), os.path.join(TTL_DIR, fn))
            n += 1
        print('[REVERT] da khoi phuc %d file tu %s' % (n, bdir))
        return 0

    print('=' * 84)
    print('T206 — SỬA MOJIBAKE  %s (U+00D0) → %s (U+0110)' % (BAD, GOOD))
    print('TTL_DIR = %s' % TTL_DIR)
    print('=' * 84)

    rows = scan()
    if not rows:
        print('  ✅ Không còn ký tự lỗi nào.')
        if args.verify:
            okc = _corpus_check()
            return 0 if okc else 1
        return 0
    print()
    tot, viol = show(rows)

    if args.verify:
        print()
        return 0 if _corpus_check() else 1

    if not (args.apply or args.dry_run):
        print('=' * 84)
        return 0

    if viol:
        print()
        print('[DUNG] Co %d file lon nguoi bien doi. Can Admin xem lai truoc.' % len(viol))
        print('=' * 84)
        return 1

    if args.dry_run:
        print()
        print('  [DRY-RUN] se sua %d ky tu trong %d file. Dung --apply de ghi.'
              % (tot, len(rows)))
        print('=' * 84)
        return 0

    # --- apply: backup rồi ghi, chỉ ghi file parse được cả trước lẫn sau ---
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join(BACKUP_DIR, 't206_mojibake_%s' % ts)
    os.makedirs(bdir, exist_ok=True)

    fixed = skipped = fixed_chars = 0
    for fn, p, n, _st in rows:
        old = read(p)
        new = old.replace(BAD, GOOD)
        if new == old:
            continue
        ok0, _t0 = can_parse(p)
        if ok0 is False:
            print('  [BO QUA] %-32s file goc da hong' % fn)
            skipped += 1
            continue
        shutil.copy2(p, os.path.join(bdir, fn))          # backup
        write(p, new)
        ok1, _t1 = can_parse(p)
        if ok1 is False:
            shutil.copy2(os.path.join(bdir, fn), p)      # rollback ngay
            print('  [HOAN TAC] %-28s sua xong khong parse duoc' % fn)
            skipped += 1
            continue
        fixed += 1
        fixed_chars += n

    print()
    print('[XONG] sua %d file (%d ky tu), bo qua %d · backup %s'
          % (fixed, fixed_chars, skipped, bdir))
    print('[REVERT] python -X utf8 scripts/t206_fix_mojibake.py --revert "%s"' % bdir)
    print('=' * 84)
    return 0


def _corpus_check():
    """Verify: 0 ký tự lỗi + toàn corpus vẫn parse được."""
    import rdflib
    print('--- VERIFY ---')
    left = 0
    for fn in ttl_files():
        left += read(os.path.join(TTL_DIR, fn)).count(BAD)
    print('   con %s : %d' % (BAD, left))
    ok = bad = 0
    for fn in ttl_files():
        p = os.path.join(TTL_DIR, fn)
        try:
            rdflib.Graph().parse(p, format='turtle')
            ok += 1
        except Exception:
            bad += 1
            if bad <= 5:
                print('   [LOI] %s' % fn)
    print('   corpus parse: %d OK / %d loi' % (ok, bad))
    good = (left == 0 and bad == 0)
    print('   => %s' % ('PASS' if good else 'FAIL'))
    return good


if __name__ == '__main__':
    sys.exit(main())