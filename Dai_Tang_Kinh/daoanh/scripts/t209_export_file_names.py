# -*- coding: utf-8 -*-
"""scripts/t209_export_file_names.py — xuất DANH SÁCH TÊN FILE của báo cáo T209.

Mọi danh sách đều **sinh từ dữ liệu thật** bằng cách gọi lại các hàm guard của
`scripts/t204_ttl_preflight.py` — không hardcode tên file, không đọc lại từ report
cũ. Nhờ vậy báo cáo không bao giờ lệch với trạng thái đĩa.

Xuất 2 file:
  docs/TTL-FILE-NAMES-T209.csv   — để mở bằng Excel, kiểm tra từng dòng
  docs/TTL-FILE-NAMES-T209.txt   — bản đọc nhanh, gom theo nhóm

Chạy:  python -X utf8 scripts/t209_export_file_names.py
       python -X utf8 scripts/t209_export_file_names.py --print
"""
import argparse
import collections
import csv
import glob
import io
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
for _p in (DAOANH, os.path.join(DAOANH, 'scripts')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import t204_ttl_preflight as PF   # noqa: E402

TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
OUT_CSV = os.path.join(DAOANH, 'docs', 'TTL-FILE-NAMES-T209.csv')
OUT_TXT = os.path.join(DAOANH, 'docs', 'TTL-FILE-NAMES-T209.txt')

EM = u'\u2014'


def _first_subject(text):
    """Slug khai báo ĐẦU TIÊN trong file (xem §3 của T209: khối phụ không phải chủ đề)."""
    m = re.search(r'<ex:monk/([a-z0-9_]+)>\s+a\s+<bkg:Monk>', text)
    return m.group(1) if m else None


def _label(text):
    """Nhãn của CHÍNH chủ thể file — dùng lại `_own_label` của preflight (nguồn SSOT,
    tránh viết lại regex rồi lệch với L1/L2)."""
    return PF._own_label(text) or ''


def _slug_of(fname):
    """Slug kỳ vọng từ tên file: bỏ tiền tố `TS-` (vd `TS-Bach-Van-Khong-Do.ttl`
    -> `bach_van_khong_do`). Bỏ tiền tố là bắt buộc, nếu không mọi file đều bị
    coi là sai URI."""
    stem = os.path.splitext(fname)[0]
    stem = re.sub(r'^TS[-_]', '', stem, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')


def collect():
    rows = []
    files = sorted(glob.glob(os.path.join(TTL_DIR, '*.ttl')))
    data = [f for f in files if 'template' not in os.path.basename(f).lower()]
    stem_present = {os.path.splitext(os.path.basename(f))[0] for f in files}

    def add(group, prio, fname, note='', ghi_cu='', ghi_dung=''):
        rows.append({
            'nhom': group, 'uu_tien': prio,
            'ten_file': fname, 'note': note,
            'ghi_cu': ghi_cu, 'ghi_dung': ghi_dung,
        })

    # --- A. file mất: DB còn ttl_filename trỏ tới, không có trên đĩa ---
    con = sqlite3.connect('file:' + DB_PATH.replace('\\', '/') + '?mode=ro', uri=True)
    db_ref = {}
    try:
        for fn, n in con.execute(
                "SELECT ttl_filename, COUNT(*) FROM vn_person_authority "
                "WHERE ttl_filename IS NOT NULL AND ttl_filename<>'' "
                "GROUP BY ttl_filename"):
            db_ref[os.path.splitext(os.path.basename(fn))[0]] = n
    except Exception as e:
        sys.stderr.write('[WARN] khong doc duoc vn_person_authority.ttl_filename: %s\n' % e)
    con.close()
    for stem in sorted(db_ref):
        if stem not in stem_present:
            add('A_mat', 1, stem + '.ttl',
                u'DB còn %d row trỏ tới; KHÔNG có trên đĩa' % db_ref[stem])

    # --- B. file rong / khong parse ---
    for f in data:
        if os.path.getsize(f) == 0:
            add('B_rong', 1, os.path.basename(f), u'0 byte')
    for f in data:
        if os.path.getsize(f) == 0:
            continue
        txt = io.open(f, encoding='utf-8', errors='replace').read()
        if not re.search(r'\s[a-zA-Z:]+[a-zA-Z0-9:_-]*\s+[\w:#/.\-]+', txt):
            add('B_rong', 1, os.path.basename(f),
                u'parse được nhưng không có triple nào')

    # --- C. URI sai (L7): slug bi nhieu file cung khai ---
    by = collections.defaultdict(list)
    meta = {}
    for f in data:
        txt = io.open(f, encoding='utf-8', errors='replace').read()
        sl = _first_subject(txt)
        if not sl:
            continue
        by[sl].append(os.path.basename(f))
        meta[os.path.basename(f)] = (sl, _label(txt))
    for sl in sorted(by):
        group = by[sl]
        if len(group) < 2:
            continue
        for fname in sorted(group):
            declared, label = meta[fname]
            expect = _slug_of(fname)
            if declared != expect:
                note = u'người khác chiếm URI %r' % declared
                if label and label != expect.replace('_', ' '):
                    note += u'; NHÃN trong file không khớp tên file = %r' % label
                add('C_uri_sai', 2, fname, note,
                    ghi_cu=declared, ghi_dung=expect)
            else:
                add('C_uri_chu_so_hu', 2, fname,
                    u'chủ sở hữu đúng của slug %r (bị %d file khác áp cảo)'
                    % (declared, len(group) - 1),
                    ghi_cu=declared, ghi_dung=expect)

    # --- D. nhan sai (L1/L2) ---
    # check_labels() tra list[{code, file, current, expected, evidence, msg}]
    for it in (PF.check_labels(TTL_DIR) or []):
        code = it.get('code', 'L?')
        add('D_%s' % code, 3, it.get('file', '?'),
            it.get('why', it.get('msg', '')) or '',
            ghi_cu=it.get('current', ''), ghi_dung=it.get('expected', ''))

    return rows, len(data), len(files)


def write_txt(rows, n_data, n_all):
    cnt = collections.Counter(r['nhom'] for r in rows)
    titles = {
        'A_mat': u'A. ĐÃ MẤT — DB còn trỏ, không còn trên đĩa — cần Admin cấp lại',
        'B_rong': u'B. File RỖNG / không parse — khôi phục backup',
        'C_uri_sai': u'C1. URI SAI — %d file kẻ áp cảo, cần Admin duyệt' % cnt['C_uri_sai'],
        'C_uri_chu_so_hu': u'C2. Chủ sở hữu đúng — %d file, đối chiếu với C1'
                           % cnt['C_uri_chu_so_hu'],
        'D_L1': u'D1. NHÃN SAI (L1) — %d file' % cnt['D_L1'],
        'D_L2': u'D2. NHÃN SAI (L2) — %d file' % cnt['D_L2'],
    }
    out = []
    out.append(u'=' * 78)
    out.append(u'DANH SÁCH TÊN FILE — BÁO CÁO T209')
    out.append(u'=' * 78)
    out.append(u'Sinh tự động từ dữ liệu TTL/DB hiện tại — không hardcode tên file.')
    out.append(u'Lệnh:  python -X utf8 scripts/t209_export_file_names.py')
    out.append(u'')
    out.append(u'Corpus: %d file data (%d file *.ttl tổng cộng)' % (n_data, n_all))
    out.append(u'Tổng %d dòng: A %d · B %d · C1 %d · C2 %d · D-L1 %d · D-L2 %d'
               % (len(rows), cnt['A_mat'], cnt['B_rong'], cnt['C_uri_sai'],
                  cnt['C_uri_chu_so_hu'], cnt['D_L1'], cnt['D_L2']))
    out.append('')
    for g in ('A_mat', 'B_rong', 'C_uri_sai', 'C_uri_chu_so_hu', 'D_L1', 'D_L2'):
        items = [r for r in rows if r['nhom'] == g]
        if not items:
            continue
        out.append(titles.get(g, g))
        out.append(u'-' * 78)
        for i, r in enumerate(items, 1):
            out.append(u'%2d. %-38s %s' % (i, r['ten_file'], r['note']))
            if r['ghi_dung'] and r['ghi_dung'] != r['ghi_cu']:
                out.append(u'      hiện tại: %-30s → nên: %s'
                           % (r['ghi_cu'], r['ghi_dung']))
        out.append('')
    out.append(u'=' * 78)
    out.append(u'TỔNG: %d dòng' % len(rows))
    out.append(u'=' * 78)
    return u'\n'.join(out) + u'\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', action='store_true', help='chi in, khong ghi file')
    args = ap.parse_args()

    rows, n_data, n_all = collect()

    if not args.print:
        with io.open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=['nhom', 'uu_tien', 'ten_file',
                                               'note', 'ghi_cu', 'ghi_dung'])
            w.writeheader()
            for r in sorted(rows, key=lambda x: (x['nhom'], x['ten_file'])):
                w.writerow(r)
        io.open(OUT_TXT, 'w', encoding='utf-8', newline='\n').write(
            write_txt(rows, n_data, n_all))
        print('[OK] CSV :', OUT_CSV)
        print('[OK] TXT :', OUT_TXT)

    print(write_txt(rows, n_data, n_all))
    return 0


if __name__ == '__main__':
    sys.exit(main())
