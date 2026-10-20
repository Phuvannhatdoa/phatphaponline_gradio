# -*- coding: utf-8 -*-
"""t203_quarantine_ttl.py — T203: danh sách + move file TTL sai nhãn ra khỏi TTL_DIR.

BỔ SUNG so với `t203_fix_ttl_labels.py`:
  - Phân loại TIER (chỉ TIER-1/2 mới move; TIER-3 là danh xưng hợp lệ → giữ)
  - **Move** file ra `data/ttl_quarantine/` kèm manifest (TTL không git track ⇒ cần manifest)
  - `--revert` trả file về chỗ cũ
  - Kiểm chứng phần CÒN LẠI trước khi move

Usage:
    python -X utf8 scripts/t203_quarantine_ttl.py --stats      # phân loại + kiểm chứng
    python -X utf8 scripts/t203_quarantine_ttl.py --dry-run    # xem danh sách sẽ move
    python -X utf8 scripts/t203_quarantine_ttl.py --apply      # move + manifest
    python -X utf8 scripts/t203_quarantine_ttl.py --revert     # trả lại
    python -X utf8 scripts/t203_quarantine_ttl.py --include-tier3   # move cả TIER-3
"""
import argparse
import datetime
import io
import json
import os
import re
import shutil
import sys
import unicodedata

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
Q_DIR = os.path.join(DAOANH, 'data', 'ttl_quarantine')
MANIFEST = os.path.join(Q_DIR, 'manifest.json')

# tiền tố hợp lệ (Cư Sĩ = am tháp, Bồ Tát = bậc) — không tính là sai
LEGIT_PREFIX = ('cư sĩ ', 'cư sĩ ', 'bồ tát ', 'ngài ', 'đại ')


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("Ð", "Đ").replace("đ", "Đ")
    return s.lower().strip()


def flat(s):
    """Bỏ hết dấu + ký tự phụ, gộp space — để so khớp tên.

    LƯU Ý: `Đ` (U+0110) là một ký tự đơn, KHÔNG tách được qua NFD ⇒ phải quy đổi
    `Đ`→`D` TRƯỚC khi lọc `[^a-z0-9]` (nếu không, chữ 'Đ' bị xoá hoàn toàn và mọi
    tên chứa Đ đều lệch ⇒ 335 false positive).
    """
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = (s.replace("Ð", "D").replace("đ", "d").replace("Đ", "D")
          .replace("_", " "))
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return " ".join(s.split())


def fname_key(fn):
    return flat(re.sub(r"^(TS|Cs|Bo-Tat)-", "", fn, flags=re.I))


def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def own_label(src):
    for m in re.finditer(r'rdfs:label\s+"([^"]+)"@vi', src):
        tail = src[max(0, m.start() - 200):m.start()].rsplit("<", 1)[-1]
        if tail.startswith("ex:monk/") or tail.startswith("ex:person/"):
            continue
        return m.group(1)
    return None


def authoritative_index():
    """{flat_slug: {label: count}} từ triple <ex:monk/SLUG> rdfs:label."""
    idx = {}
    if not os.path.isdir(TTL_DIR):
        return idx
    for fn in sorted(os.listdir(TTL_DIR)):
        if not fn.endswith('.ttl'):
            continue
        try:
            src = read(os.path.join(TTL_DIR, fn))
        except Exception:
            continue
        for m in re.finditer(
                r'<ex:monk/([a-z0-9_]+)>\s*rdfs:label\s+"([^"]+)"@vi', src):
            k = m.group(1).replace('-', '_').lower()
            idx.setdefault(k, {})
            lab = m.group(2)
            idx[k][lab] = idx[k].get(lab, 0) + 1
    return idx


def classify(include_tier3=False, ttl_dir=None):
    """Trả (tier1, tier2, tier3).

    ttl_dir: Nếu truyền, chỉ kiểm tra files trong thư mục đó.
             authoritative_index() vẫn quét corpus đầy đủ (TTL_DIR) để xác định
             nhãn chuẩn — việc giới hạn scan_dir chỉ ảnh hưởng đến danh sách
             file NÀO được kiểm tra, không ảnh hưởng đến nhãn tham chiếu.
    """
    idx = authoritative_index()
    t1, t2, t3 = [], [], []
    # [T222] Scope alignment: scan_dir = ttl_dir khi được truyền vào,
    # giúp preflight chỉ báo lỗi cho các file thuộc phạm vi ETL write scope.
    scan_dir = ttl_dir if (ttl_dir and os.path.isdir(ttl_dir)) else TTL_DIR
    for fn in sorted(os.listdir(scan_dir)):
        if not fn.endswith('.ttl'):
            continue
        try:
            src = read(os.path.join(scan_dir, fn))
        except Exception:
            continue
        cur = own_label(src)
        if not cur:
            continue
        key = re.sub(r"^(TS|Cs|Bo-Tat)-", "", fn[:-4], flags=re.I)
        key = key.replace('-', '_').lower()
        cands = idx.get(key)
        if not cands:
            continue
        corr, n = max(cands.items(), key=lambda kv: kv[1])
        if flat(corr) == flat(cur):
            continue

        # các monk KHÁC (khác chính file) mà file khai báo
        own = key
        others = set()
        for m in re.finditer(r'<ex:monk/([a-z0-9_]+)>\s*rdfs:label\s+"([^"]+)"@vi', src):
            ok = m.group(1).replace('-', '_').lower()
            if ok == own:
                continue
            others.add(flat(m.group(2)))
            others.add(ok)

        rec = {'file': fn, 'cur': cur, 'corr': corr, 'evidence': n}
        fc, fk = flat(cur), flat(corr)
        if fc in others:
            rec['why'] = 'nhãn trùng tên 1 người KHÁC trong file'
            t1.append(rec)
        elif fc in fk or fk in fc or norm(cur).startswith(LEGIT_PREFIX) \
                or flat(re.sub(r"^(cư sĩ|bồ tát|ngài|đại)\s+", "", norm(cur))) == fk:
            rec['why'] = 'danh xưng / tiền tố hợp lệ'
            t3.append(rec)
        else:
            words_c, words_k = set(fc.split()), set(fk.split())
            sim = (len(words_c & words_k) / len(words_c | words_k)
                   if words_c and words_k else 0.0)
            rec['sim'] = round(sim, 2)
            if sim >= 0.5:
                rec['why'] = 'gần giống — có thể là pháp danh'
                t3.append(rec)
            else:
                rec['why'] = 'không liên quan tới nhãn đúng'
                t2.append(rec)
    return t1, t2, t3


def validate_remainder(remove, t1, t2, t3):
    print()
    print('=' * 94)
    print('KIỂM CHỨNG PHẦN CÒN LẠI (giả lập sau khi move %d file)' % len(remove))
    print('=' * 94)
    rem = set(remove)
    keep_files = [f for f in sorted(os.listdir(TTL_DIR))
                  if f.endswith('.ttl') and f not in rem]
    print('  Số file còn lại: %d (đã loại %d)' % (len(keep_files), len(remove)))

    idx = authoritative_index()
    keepidx = {}
    for fn in keep_files:
        try:
            src = read(os.path.join(TTL_DIR, fn))
        except Exception:
            continue
        for m in re.finditer(
                r'<ex:monk/([a-z0-9_]+)>\s*rdfs:label\s+"([^"]+)"@vi', src):
            k = m.group(1).replace('-', '_').lower()
            keepidx.setdefault(k, {})
            keepidx[k][m.group(2)] = keepidx[k].get(m.group(2), 0) + 1

    # 1) nhãn đúng của file bị move còn nguồn ở file GIỮ LẠI không
    lost = []
    for r in (t1 + t2):
        key = re.sub(r"^(TS|Cs|Bo-Tat)-", "", r['file'][:-4], flags=re.I)
        key = key.replace('-', '_').lower()
        if key not in keepidx:          # không còn triple <ex:monk/SLUG> nào ở file giữ lại
            lost.append(r['file'])
    print('  [1] file bị move mà triple nhãn-chuẩn KHÔNG còn ở file giữ lại: %d  %s'
          % (len(lost), '(OK — không mất nhãn chuẩn)' if not lost else lost[:6]))
    gone_person = [(r['file'], r['corr']) for r in (t1 + t2)
                   if re.sub(r"^(TS|Cs|Bo-Tat)-", "", r['file'][:-4],
                             flags=re.I).replace('-', '_').lower() not in keepidx]
    if gone_person:
        print('      ⚠ %d vị sẽ mất BẢN THAM CHIẾU nhãn chuẩn nếu move:'
              % len(gone_person))
        for f, c in gone_person[:10]:
            print('         %-32s (chuẩn %r)' % (f, c))

    # 2) file còn lại: label của chính nó có khớp tên file / có tiền tố hợp lệ?
    mism = []
    for fn in keep_files:
        try:
            src = read(os.path.join(TTL_DIR, fn))
        except Exception:
            continue
        cur = own_label(src)
        if not cur:
            continue
        fc, fk = flat(cur), flat(fname_key(fn[:-4]))
        if fc == fk:
            continue
        # hợp lệ nếu: slug nằm ở CUỐI label (danh xưng có tiền tố: "Am Chủ …"),
        # hoặc slug nằm ở ĐẦU (bị bỏ tiền tố: "Cư Sĩ …"), hoặc là substring
        if fk and (fc.endswith(fk) or fc.startswith(fk) or fk in fc):
            continue
        mism.append((fn, cur))
    print('  [2] file còn lại có nhãn KHÔNG khớp tên (sau khi bỏ tiền tố hợp lệ): %d'
          % len(mism))
    for fn, cur in mism[:10]:
        print('        %-34s %r' % (fn, cur))

    # 3) rdflib parse được không
    print('  [3] rdflib parse (file hỏng sẽ bị ETL bỏ qua im lặng):')
    try:
        import rdflib
    except Exception:
        print('        (không có rdflib — bỏ qua)')
        rdflib = None
    if rdflib:
        broken = []
        for fn in keep_files:
            try:
                g = rdflib.Graph()
                g.parse(os.path.join(TTL_DIR, fn), format='turtle')
            except Exception:
                broken.append(fn)
        print('        file KHÔNG parse được: %d' % len(broken))
        for fn in broken:
            print('          ⚠ %s' % fn)

    # 4) tham chiếu tới monk đã bị move
    move_keys = {}
    for f in rem:
        k = re.sub(r"^(TS|Cs|Bo-Tat)-", "", f[:-4], flags=re.I)
        move_keys[k.replace('-', '_').lower()] = f
    dangle = {}
    for fn in keep_files:
        try:
            src = read(os.path.join(TTL_DIR, fn))
        except Exception:
            continue
        for m in re.finditer(r'<ex:monk/([a-z0-9_]+)>', src):
            k = m.group(1).replace('-', '_').lower()
            if k in move_keys:
                dangle.setdefault(move_keys[k], set()).add(fn)
    print('  [4] file bị move vẫn được file còn lại tham chiếu (vai thầy/trò): %d/%d'
          % (len(dangle), len(rem)))
    print('        ⇒ các triple quan hệ VẪN CÒN trong file khác (không mất dữ liệu quan hệ),')
    print('        nhưng vị đó sẽ KHÔNG có file riêng ⇒ mất dòng vn_person_authority ở lần ETL kế.')
    print('=' * 94)


def do_stats(args):
    t1, t2, t3 = classify()
    print('=' * 94)
    print('T203 — PHÂN LOẠI FILE TTL   (TTL_DIR = %s)' % TTL_DIR)
    print('=' * 94)
    for title, arr in (('TIER-1  SAI ĐẢO (nhãn của người KHÁC)', t1),
                       ('TIER-2  SAI KHÁC (không liên quan)', t2),
                       ('TIER-3  HỢP LỆ — GIỮ LẠI', t3)):
        print()
        print('%s : %d file' % (title, len(arr)))
        for r in arr:
            print('   %-34s %r' % (r['file'], r['cur']))
            print('       chuẩn : %r (x%d)  [%s]' % (r['corr'], r['evidence'],
                                                    r['why']))
    print()
    print('  CẦN MOVE = %d   |   GIỮ LẠI = %d' % (len(t1) + len(t2), len(t3)))
    validate_remainder([r['file'] for r in t1] + [r['file'] for r in t2], t1, t2, t3)


def do_dry_run(args):
    t1, t2, t3 = classify(args.include_tier3)
    mv = [r['file'] for r in t1] + [r['file'] for r in t2]
    if args.include_tier3:
        mv += [r['file'] for r in t3]
    print('=' * 94)
    print('T203 — DRY RUN: sẽ MOVE %d file' % len(mv))
    print('  từ : %s' % TTL_DIR)
    print('  sang: %s' % Q_DIR)
    print('=' * 94)
    for f in mv:
        print('   %s' % os.path.join(TTL_DIR, f))
    print()
    print('GIỮ LẠI (TIER-3): %d file' % (len(t3) - (len(t3) if args.include_tier3 else 0)))
    for r in t3:
        if not args.include_tier3:
            print('   %s' % os.path.join(TTL_DIR, r['file']))


def do_apply(args):
    t1, t2, t3 = classify(args.include_tier3)
    mv = [r['file'] for r in t1] + [r['file'] for r in t2]
    if args.include_tier3:
        mv += [r['file'] for r in t3]
    if not mv:
        print('[KHÔNG CÓ GÌ]')
        return 0
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(Q_DIR, ts)
    os.makedirs(dest, exist_ok=True)
    moved = []
    for f in mv:
        src = os.path.join(TTL_DIR, f)
        if not os.path.exists(src):
            print('[BỎ QUA] %s không còn' % f)
            continue
        shutil.move(src, os.path.join(dest, f))
        moved.append(f)
        print('[MOVE] %s' % f)
    with io.open(os.path.join(dest, 'manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump({
            'ts': ts,
            'ttl_dir': TTL_DIR,
            'quarantine_dir': dest,
            'count': len(moved),
            'tier1': [{'file': r['file'], 'current_label': r['cur'],
                       'correct_label': r['corr'], 'evidence': r['evidence']}
                      for r in t1],
            'tier2': [{'file': r['file'], 'current_label': r['cur'],
                       'correct_label': r['corr'], 'evidence': r['evidence']}
                      for r in t2],
            'tier3_kept': [{'file': r['file'], 'label': r['cur'],
                            'authoritative': r['corr'], 'why': r['why']}
                           for r in t3],
            'moved': moved,
        }, fh, ensure_ascii=False, indent=1)
    print()
    print('[XONG] đã move %d file sang %s' % (len(moved), dest))
    print('[REVERT] python -X utf8 scripts/t203_quarantine_ttl.py --revert "%s"' % dest)
    return 0


def do_revert(args):
    d = args.quarantine or (Q_DIR)
    if not os.path.isdir(d):
        print('[LỖI] không có thư mục %s' % d)
        return 1
    mpath = os.path.join(d, 'manifest.json')
    if not os.path.exists(mpath):
        print('[LỖI] không có manifest.json trong %s' % d)
        return 1
    with io.open(mpath, encoding='utf-8') as fh:
        man = json.load(fh)
    n = 0
    for f in man.get('moved', []):
        s = os.path.join(d, f)
        if os.path.exists(s):
            shutil.move(s, os.path.join(TTL_DIR, f))
            n += 1
            print('[KHÔI PHỤC] %s' % f)
    print('[XONG] trả %d file về %s' % (n, TTL_DIR))
    return 0


def main():
    p = argparse.ArgumentParser(description='T203 — quarantine file TTL sai nhãn')
    p.add_argument('--stats', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--revert', nargs='?', const='', default=None)
    p.add_argument('--include-tier3', action='store_true',
                   help='move cả TIER-3 (danh xưng hợp lệ) — MẶC ĐỊNH KHÔNG')
    args = p.parse_args()

    if not os.path.isdir(TTL_DIR):
        print('[LỖI] Không có %s' % TTL_DIR)
        sys.exit(1)
    if args.revert is not None:
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