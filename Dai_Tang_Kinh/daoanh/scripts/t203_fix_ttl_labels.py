# -*- coding: utf-8 -*-
"""t203_fix_ttl_labels.py — [T203] sửa `rdfs:label` SAI trong file TTL gốc.

VÌ SAO
------
`vn_person_authority.dila_id` KHÔNG unique (33 nhóm 2–3 dòng). Truy nguồn (T202) cho thấy
17/33 nhóm do **file TTL có `rdfs:label` của người KHÁC** — ví dụ
`TS-Nguyet-Chuong-Tri-Uyen.ttl` mang `rdfs:label "Bảo Ninh Nhân Dũng"` và khai báo chính
Bảo Ninh Nhân Dũng là **thầy** mình ⇒ nhãn bị đảo.

CÁCH SỬA (không đoán)
---------------------
Nhãn đúng **đã tồn tại trong corpus TTL** dưới dạng triple
`<ex:monk/SLUG> rdfs:label "TÊN ĐÚNG"@vi` (SLUG lấy từ tên file, bỏ prefix `TS-`/`Cs-`).
Script **chỉ sửa** khi tìm được nhãn đó và nó KHÁC `rdfs:label` hiện tại.
Không tự chế nhãn từ tên file ⇒ không suy đoán chính tả Hán-Việt.

AN TOÀN
-------
- **KHÔNG** dùng chung `dila_id` cho file sai; chỉ sửa nhãn trong file.
- File TTL **KHÔNG được git track** (`.gitignore` có `data/`) ⇒ KHÔNG có git revert.
  Script backup **file-level** vào `data/backups/t203_ttl_<ts>/` trước khi ghi.
- `--revert` khôi phục từ backup.

Usage:
    python -X utf8 scripts/t203_fix_ttl_labels.py --stats
    python -X utf8 scripts/t203_fix_ttl_labels.py --dry-run
    python -X utf8 scripts/t203_fix_ttl_labels.py --apply
    python -X utf8 scripts/t203_fix_ttl_labels.py --revert
"""
import argparse
import datetime
import json
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

REPORT = os.path.join(BACKUP_DIR, 't203_ttl_label_fix.json')


# ---------------------------------------------------------------------------
def slugify(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def norm_key(k):
    """Chuẩn hoá slug: TTL triple dùng `_` (vd `nguyet_chuong_tri_uyen`),
    tên file dùng `-` (vd `TS-Nguyet-Chuong-Tri-Uyen`) ⇒ về cùng một dạng."""
    return (k or "").strip().lower().replace("-", "_")


def fname_slug(fn):
    """Bỏ prefix TS-/Cs- rồi chuẩn hoá (dạng `ex:monk/...` dùng dấu `_`)."""
    return norm_key(re.sub(r"^(TS|Cs|TSCs)-", "", fn or "", flags=re.I))


def read(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def own_label(src):
    """Nhãn của CHÍNH file này (rdfs:label gốc, không phải triple `<ex:monk/...>`)."""
    for m in re.finditer(r'rdfs:label\s+"([^"]+)"@vi', src):
        line = src[max(0, m.start() - 200):m.start()]
        # bỏ qua nếu nhãn nằm sau một `<ex:monk/...>` (nghĩa là nhãn của người khác)
        tail = line.rsplit("<", 1)[-1]
        if tail.startswith("ex:monk/") or tail.startswith("ex:person/"):
            continue
        return m.group(1)
    return None


def index_authoritative_labels():
    """{slug: Counter(label)} — gom mọi `<ex:monk/SLUG> rdfs:label "X"@vi` trong corpus."""
    idx = defaultdict(lambda: defaultdict(int))
    if not os.path.isdir(TTL_DIR):
        return idx
    for fn in os.listdir(TTL_DIR):
        if not fn.endswith('.ttl'):
            continue
        try:
            src = read(os.path.join(TTL_DIR, fn))
        except Exception:
            continue
        for m in re.finditer(
                r'<ex:monk/([a-z0-9_]+)>\s*rdfs:label\s+"([^"]+)"@vi', src):
            idx[norm_key(m.group(1))][m.group(2)] += 1
    return idx


def scan():
    """Trả (fixes, mojibake_files) — fixes = danh sách dict mô tả sửa."""
    idx = index_authoritative_labels()
    fixes = []
    for fn in sorted(os.listdir(TTL_DIR)):
        if not fn.endswith('.ttl'):
            continue
        path = os.path.join(TTL_DIR, fn)
        try:
            src = read(path)
        except Exception:
            continue
        cur = own_label(src)
        if not cur:
            continue
        sl = fname_slug(fn[:-4])
        cands = idx.get(sl)
        if not cands:
            continue
        label, n = max(cands.items(), key=lambda kv: kv[1])
        # chỉ sửa khi: nhãn hiện tại khác nhãn có căn cứ
        # VÀ nhãn hiện tại KHÔNG tự khớp tên file
        if label.strip() != cur.strip() and norm_key(slugify(cur)) != sl:
            fixes.append({
                'file': fn,
                'slug': sl,
                'current_label': cur,
                'correct_label': label,
                'evidence_count': n,
            })
    return fixes


def mojibake_scan():
    out = []
    for fn in sorted(os.listdir(TTL_DIR)):
        if not fn.endswith('.ttl'):
            continue
        try:
            src = read(os.path.join(TTL_DIR, fn))
        except Exception:
            continue
        n_e = src.count('Ð')      # Ð sai
        n_d = src.count('Đ')      # Đ đúng
        if n_e:
            out.append({'file': fn, 'eth_D': n_e, 'viet_D': n_d})
    return out


# ---------------------------------------------------------------------------
def do_stats(args):
    fixes = scan()
    mo = mojibake_scan()
    print('=' * 78)
    print('T203 — THỐNG KÊ (read-only, 0 ghi)')
    print('=' * 78)
    print('TTL_DIR: %s' % TTL_DIR)
    print('Số file .ttl: %d' % len([f for f in os.listdir(TTL_DIR)
                                   if f.endswith('.ttl')]))
    print()
    print('[1] File có rdfs:label KHÔNG khớp tên file, nhưng có nhãn đúng')
    print('    trong corpus (dạng <ex:monk/SLUG> rdfs:label) => SỬA ĐƯỢC: %d file'
          % len(fixes))
    for f in fixes:
        print('      %-36s' % f['file'])
        print('          hiện tại : %r' % f['current_label'])
        print('          đúng     : %r  (x%d nguồn)' % (f['correct_label'],
                                                      f['evidence_count']))
    print()
    print('[2] ⚠ File chứa ký tự Ð (U+00D0) thay cho Đ (U+0110): %d file' % len(mo))
    tot_e = sum(m['eth_D'] for m in mo)
    print('    tổng số ký tự Ð sai: %d' % tot_e)
    print('    (ghi riêng — KHÔNG sửa tự động vì cần rà từng file)')
    print('=' * 78)


def do_dry_run(args):
    fixes = scan()
    print('=' * 78)
    print('T203 — DRY RUN (0 ghi)')
    print('=' * 78)
    print('Sẽ sửa %d file:' % len(fixes))
    for f in fixes:
        print()
        print('  FILE : %s' % f['file'])
        print('  TỪ   : rdfs:label "%s"@vi' % f['current_label'])
        print('  SANG : rdfs:label "%s"@vi' % f['correct_label'])
        print('  CĂN CỨ: <ex:monk/%s> trong %d file khác' % (f['slug'],
                                                        f['evidence_count']))
    print()
    print('BACKUP sẽ ghi: data/backups/t203_ttl_<YYYYmmdd_HHMMSS>/')
    print('=' * 78)


def do_apply(args):
    fixes = scan()
    if not fixes:
        print('[KHÔNG CÓ GÌ] không tìm thấy file nào cần sửa.')
        return 0
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join(BACKUP_DIR, 't203_ttl_%s' % ts)
    os.makedirs(bdir, exist_ok=True)

    done = []
    for f in fixes:
        path = os.path.join(TTL_DIR, f['file'])
        if not os.path.exists(path):
            print('[BỎ QUA] %s không còn' % f['file'])
            continue
        src = read(path)
        if f['current_label'] not in src:
            print('[BỎ QUA] %s: không còn tìm thấy nhãn cũ' % f['file'])
            continue
        shutil.copy2(path, os.path.join(bdir, f['file']))
        # chỉ thay nhãn của CHÍNH file (dùng own_label để định vị chính xác)
        new_src = _replace_own_label(src, f['current_label'], f['correct_label'])
        if new_src == src:
            print('[BỎ QUA] %s: thay không đổi gì' % f['file'])
            continue
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            fh.write(new_src)
        done.append(f)
        print('[SỬA] %-36s %r -> %r' % (f['file'], f['current_label'],
                                        f['correct_label']))

    with open(REPORT, 'w', encoding='utf-8') as fh:
        json.dump({'ts': ts, 'backup_dir': bdir, 'applied': done},
                  fh, ensure_ascii=False, indent=1)
    print()
    print('[XONG] đã sửa %d file' % len(done))
    print('[BACKUP] %s' % bdir)
    print('[REVERT] python -X utf8 scripts/t203_fix_ttl_labels.py --revert')
    print('   hoặc copy lại từ: %s' % bdir)
    return 0


def _replace_own_label(src, old, new):
    """Thay `rdfs:label "OLD"@vi` của CHÍNH file (bỏ qua triple `<ex:monk/...>`)."""
    out = []
    pos = 0
    for m in re.finditer(r'rdfs:label\s+"([^"]+)"@vi', src):
        seg_start = src.rfind('<', 0, m.start())
        tail = src[seg_start:m.start()] if seg_start >= 0 else ''
        is_other = (tail.startswith('<ex:monk/') or tail.startswith('<ex:person/'))
        if not is_other and m.group(1) == old:
            out.append(src[pos:m.start(1)])
            out.append(new)
            pos = m.end(1)
    out.append(src[pos:])
    return ''.join(out)


def do_revert(args):
    if not os.path.exists(REPORT):
        print('[LỖI] Không có %s — chưa chạy --apply?' % REPORT)
        return 1
    with open(REPORT, encoding='utf-8') as f:
        rep = json.load(f)
    bdir = rep['backup_dir']
    if not os.path.isdir(bdir):
        print('[LỖI] Không còn thư mục backup: %s' % bdir)
        return 1
    n = 0
    for f in rep['applied']:
        src = os.path.join(bdir, f['file'])
        dst = os.path.join(TTL_DIR, f['file'])
        if os.path.exists(src):
            shutil.copy2(src, dst)
            n += 1
            print('[KHÔI PHỤC] %s' % f['file'])
    print('[XONG] khôi phục %d file từ %s' % (n, bdir))
    return 0


def main():
    p = argparse.ArgumentParser(
        description='T203 — sửa rdfs:label sai trong file TTL (có backup file-level)')
    p.add_argument('--stats', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--revert', action='store_true')
    args = p.parse_args()

    if not os.path.isdir(TTL_DIR):
        print('[LỖI] Không có %s' % TTL_DIR)
        sys.exit(1)
    if args.revert:
        sys.exit(do_revert(args))
    if args.apply:
        sys.exit(do_apply(args))
    if args.dry_run:
        do_dry_run(args)
    else:
        do_stats(args)
    sys.exit(0)


if __name__ == '__main__':
    main()