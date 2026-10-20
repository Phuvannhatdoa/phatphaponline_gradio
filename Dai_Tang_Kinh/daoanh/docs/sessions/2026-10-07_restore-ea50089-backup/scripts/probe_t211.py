# -*- coding: utf-8 -*-
"""probe_t211.py — phân loại file URI sai: sửa được cơ học hay cần Admin quyết.

Vì sao phân loại:
  Sửa `ex:monk/X` cũng là ĐỔI DANH TÍNH ONTOLOGY. Chỉ an toàn khi có bằng
  chứng mạnh rằng chữ `X` là lỗi gõ, tức là **NÃN trong file khớp tên file**
  (nhãn do người viết ra, URI bị copy-paste sót).

  - Nhãn khớp tên file  → URI sai → SỬA ĐƯỢC (bằng chứng 2 chiều)
  - Nhãn cũng lệch      → file đặt tên sai HOẶC nội dung sai → CẦN ADMIN

Viet bang escape \\uXXXX de khong phu thuoc encoding cua shell.
"""
import io
import os
import re
import sys
import unicodedata
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t204_ttl_preflight as P   # noqa: E402
import t210_ttl_file_report as R  # noqa: E402


def words(s):
    t = unicodedata.normalize('NFD', s or '')
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return [w for w in re.findall(r'[a-z0-9]+', t.lower()) if w]


def label_matches_filename(fn, label):
    """Nhãn có khớp tên file không? So tập từ, bỏ qua từ chức năng."""
    STOP = {'a', 'an', 'the', 'va', 'tu', 'la', 'la', 'nghi', 'monk'}
    fw = [w for w in words(R.slug_of(fn) or '') if w not in STOP]
    lw = [w for w in words(label) if w not in STOP]
    if not fw or not lw:
        return False, 0.0
    common = len(set(fw) & set(lw))
    # bao phu: moi tu trong file-slug deu xuat hien trong nhan (hoac nguoc lai)
    cover = common / float(min(len(fw), len(lw)))
    return cover >= 0.99, cover


def main():
    have = {f for f in os.listdir(P.TTL_DIR)
            if f.endswith('.ttl') and f != '0-template.ttl'}
    own = defaultdict(list)
    for fn in sorted(have):
        src = P._read(os.path.join(P.TTL_DIR, fn))
        m = P.OWN.search(src) if hasattr(P, 'OWN') else None
        if m is None:
            m = re.compile(r'^\s*<ex:(?:monk|person)/([\w\-]+)>\s+a\s+<bkg:Monk>',
                           re.M).search(src)
        if m:
            own[m.group(1)].append(fn)

    collide = {s: fs for s, fs in own.items() if len(fs) > 1}
    safe, need = [], []
    for sl, fs in sorted(collide.items()):
        for fn in fs:
            fslug = R.slug_of(fn)
            if not fslug or fslug == sl:
                continue
            src = P._read(os.path.join(P.TTL_DIR, fn))
            lab = R.label_of(src, sl)
            ok, cover = label_matches_filename(fn, lab)
            (safe if ok else need).append((fn, fslug, sl, lab, cover))

    print('=' * 82)
    print('T211 — phan loai file URI sai')
    print('=' * 82)
    print('tong slug trung        : %d' % len(collide))
    print('file co URI sai        : %d' % (len(safe) + len(need)))
    print('  -> SỬA ĐƯỢC (nhãn khớp tên file): %d' % len(safe))
    print('  -> CẦN ADMIN (nhãn cũng lệch)     : %d' % len(need))
    print()
    print('=== NHÓM 1: SỬA ĐƯỢC (URI ← slug theo tên file) ===')
    for fn, fs, sl, lab, cov in safe:
        print('  %-32s %s -> %s' % (fn, sl, fs))
        print('       nhan: %r  (khop %.0f%%)' % (lab, cov * 100))
    print()
    print('=== NHÓM 2: CẦN ADMIN QUYẾT ===')
    for fn, fs, sl, lab, cov in need:
        print('  %-32s %s (file slug %s)' % (fn, sl, fs))
        print('       nhan: %r  (khop %.0f%%)' % (lab, cov * 100))
    print()
    print('LƯU Ý: sửa URI ⇒ vn_person_authority sinh row MỚI, row CŨ thành orphan.')
    print('       Cần ETL nạp lại, mà ETL đang bị chặn bởi L1/L2.')


if __name__ == '__main__':
    main()