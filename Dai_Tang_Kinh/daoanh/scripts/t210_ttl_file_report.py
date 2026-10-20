# -*- coding: utf-8 -*-
"""t210_ttl_file_report.py — [T210] sinh báo cáo trạng thái FILE TTL cho Admin.

Vì sao cần script (không gõ tay): corpus TTL bị nhiều session sửa song song,
số file / lỗi thay đổi liên tục. Báo cáo gõ tay sẽ nhanh chóng sai.

Báo cáo đầu ra: docs/TTL-FILE-STATUS-REPORT.md

Nhóm trạng thái:
  A. FILE ĐÃ MẤT      — DB còn tham chiếu, nhưng không còn file trên đĩa
  B. FILE RỖNG/HỎNG   — 0 byte hoặc không parse được (L6/L3)
  C. FILE URI SAI     — subject URI không khớp tên file + nhãn (L7)
  D. FILE NHÃN SAI    — nhãn lệch/không liên quan (L1/L2)
  E. FILE ĐÃ SỬA      — T205 (cú pháp) + T206 (mojibake)

Usage:
    python -X utf8 scripts/t210_ttl_file_report.py            # ghi report
    python -X utf8 scripts/t210_ttl_file_report.py --stdout   # chỉ in
"""
import argparse
import io
import os
import re
import sqlite3
import sys
import datetime
from collections import Counter, defaultdict

for _s in (sys.stdout, _e := sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
OUT = os.path.join(DAOANH, 'docs', 'TTL-FILE-STATUS-REPORT.md')

OWN = re.compile(r'^\s*<ex:(?:monk|person)/([\w\-]+)>\s+a\s+<bkg:Monk>', re.M)


def slug_of(fn):
    """TS-Bach-Van-Khong-Do.ttl → bach_van_khong_do"""
    m = re.match(r'^(?:TS|Cs|Bo-Tat)-(.+)\.ttl$', fn)
    if not m:
        return None
    return re.sub(r'[^a-z0-9]+', '_', m.group(1).lower()).strip('_')


def label_of(src, slug):
    m = re.search(
        r'<ex:monk/%s>\s+a\s+<bkg:Monk>\s*;\s*\n?\s*rdfs:label\s+"([^"]+)"@vi'
        % re.escape(slug), src)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stdout', action='store_true')
    args = ap.parse_args()

    sys.path.insert(0, os.path.join(DAOANH, 'scripts'))
    import t204_ttl_preflight as P

    L = []
    def w(s=''):
        L.append(s)

    have = {}
    for fn in sorted(os.listdir(TTL_DIR)):
        if fn.endswith('.ttl') and fn != '0-template.ttl':
            have[fn] = os.path.getsize(os.path.join(TTL_DIR, fn))

    blocking, warnings, _all = P.preflight()
    by_code = defaultdict(list)
    for f in blocking:
        by_code[f['code']].append(f)
    for f in warnings:
        by_code[f['code']].append(f)

    # ---------------------------------------------------------------- A
    con = sqlite3.connect('file:%s?mode=ro' % DB_PATH.replace('\\', '/'), uri=True)
    db_files = {r[0] for r in con.execute(
        'SELECT DISTINCT ttl_filename FROM vn_person_authority '
        'WHERE ttl_filename IS NOT NULL AND ttl_filename <> ""')}
    rows_per_file = defaultdict(int)
    for fn, n in con.execute(
            'SELECT ttl_filename, count(*) FROM vn_person_authority '
            'WHERE ttl_filename IS NOT NULL AND ttl_filename <> "" '
            'GROUP BY ttl_filename'):
        rows_per_file[fn] = n
    con.close()
    missing = sorted(f for f in db_files if (f + '.ttl') not in have)

    # ---------------------------------------------------------------- C
    own_subject = {}
    for fn in have:
        src = P._read(os.path.join(TTL_DIR, fn))
        m = OWN.search(src)
        if m:
            own_subject[fn] = (m.group(1), label_of(src, m.group(1)))
    slug_seen = defaultdict(list)
    for fn, (sl, _lab) in own_subject.items():
        slug_seen[sl].append(fn)
    collide = {s: fs for s, fs in slug_seen.items() if len(fs) > 1}
    wrong_uri = []
    for sl, fs in collide.items():
        for fn in fs:
            fs_slug = slug_of(fn)
            if fs_slug and fs_slug != sl:
                wrong_uri.append((fn, fs_slug, sl, own_subject[fn][1]))

    # ---------------------------------------------------------------- D
    l12 = sorted({f['file'] for f in by_code['L1'] + by_code['L2']})

    # ---------------------------------------------------------------- E
    t205_rep = ['TS-Ban-Son-Bao-Tich.ttl', 'TS-Dai-Hue-Tong-Cao.ttl',
                'TS-Dai-Xa-Nhu-Truong.ttl', 'TS-Minh-Hoang-Tu-Dung.ttl',
                'TS-Tin-Tuong-Tong-Hien.ttl', 'TS-Thanh-Dang-Minh-Luong.ttl',
                'TS-Tinh-Nhan-Ke-Thanh.ttl', 'TS-Tuyet-Giau-Chon-Phac.ttl',
                'TS-Van-Cai-Thu-Tri.ttl', 'TS-Van-Thu-Tuyen-Nang.ttl']

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    w('# Báo cáo trạng thái FILE TTL')
    w()
    w('> Sinh tự động bằng `scripts/t210_ttl_file_report.py` — **đừng sửa tay**,')
    w('> hãy chạy lại script để cập nhật.')
    w('>')
    w('> **Cập nhật:** %s · **Corpus:** %d file' % (now, len(have)))
    w()
    w('## Tóm tắt')
    w()
    w('| Nhóm | Số file | Mức độ | Cần Admin làm |')
    w('|---|---|---|---|')
    n_empty = len(by_code['L6']) + len(by_code['L3'])
    n_wrong = len(wrong_uri)
    n_fixed = len(t205_rep)
    w('| A. File đã **mất** (DB còn tham chiếu) | %d | 🔴 Cao | **Cấp lại bản gốc** |'
      % len(missing))
    w('| B. File **rỗng** / không parse được | %d | 🔴 Cao | Khôi phục backup |'
      % n_empty)
    w('| C. File **URI sai** (ghi đè lẫn nhau) | %d | 🟠 Trung bình | Duyệt sửa URI |'
      % n_wrong)
    w('| D. File **nhãn sai** | %d | 🟠 Trung bình | Sửa nhãn |' % len(l12))
    w('| E. File **đã sửa** xong (T205/T206) | %d | ✅ Đã xong | — |' % n_fixed)
    w()
    w('**Preflight hiện tại:** BLOCKING = %d (L1 %d · L2 %d · L3 %d · L6 %d · L7 %d) '
      '· WARNING = %d (L4 %d · L5 %d)'
      % (len(blocking), len(by_code['L1']), len(by_code['L2']),
         len(by_code['L3']), len(by_code['L6']), len(by_code['L7']),
         len(warnings), len(by_code['L4']), len(by_code['L5'])))
    w()

    # ---------------------------------------------------------------- A
    w('---')
    w()
    w('## A. 🔴 File đã MẤT — DB còn tham chiếu, không còn trên đĩa')
    w()
    if not missing:
        w('_Không có._')
    else:
        w('| # | Tên file (thiếu `.ttl`) | Số row DB còn trỏ tới |')
        w('|---|---|---|')
        for i, fn in enumerate(missing, 1):
            w('| %d | `%s.ttl` | %d |' % (i, fn, rows_per_file.get(fn, 0)))
        w()
        w('> **Không có backup** cho các file này (T205/T206 chỉ backup file đã sửa).')
        w('> Cần bản gốc từ Admin.')
    w()

    # ---------------------------------------------------------------- B
    w('---')
    w()
    w('## B. 🔴 File RỖNG hoặc không parse được')
    w()
    if not (by_code['L6'] or by_code['L3']):
        w('_Không có — toàn bộ %d file đều parse được._' % len(have))
    else:
        w('| File | Mã | Kích thước | Vấn đề |')
        w('|---|---|---|---|')
        for f in by_code['L6'] + by_code['L3']:
            w('| `%s` | %s | %s | %s |'
              % (f['file'], f['code'], have.get(f['file'], '?'), f['msg'][:70]))
    w()
    w('> **Đã xử lý 1 vụ:** `TS-Dai-Xa-Nhu-Truong.ttl` bị xoá rỗng (0 byte) ngày')
    w('> 2026-10-02, đã khôi phục từ backup `data/backups/t205_ttl_20261001_203559/`.')
    w()

    # ---------------------------------------------------------------- C
    w('---')
    w()
    w('## C. 🟠 File có URI sai — nhiều file dùng chung 1 subject')
    w()
    w('Nguyên nhân: lỗi copy-paste khi sinh TTL — **URI giữ từ người trước**,')
    w('còn **nhãn thì đúng**. Hậu quả: các file ghi đè lẫn nhau, ETL chỉ nạp')
    w('file cuối, **các file kia mất im lặng**.')
    w()
    if not wrong_uri:
        w('_Không có._')
    else:
        w('| File | URI đang khai báo | URI đúng (theo tên file) | Nhãn trong file |')
        w('|---|---|---|---|')
        for fn, fs_slug, sl, lab in sorted(wrong_uri):
            mark = ' ⚠️' if (lab and slug_words(lab) != slug_words(fs_slug)) else ''
            w('| `%s` | `%s` | `%s` | %s%s |'
              % (fn, sl, fs_slug, (lab or '—'), mark))
        w()
        w('> ⚠️ = cả **nhãn** cũng không khớp tên file ⇒ cần Admin xác nhận,')
        w('> không sửa cơ học được.')
    w()
    w('### Nhóm đặc biệt: 3 file cùng subject `phong_huyet_dien_chieu`')
    w()
    w('| File | generationOrder | hasTeacher | Nhãn |')
    w('|---|---|---|---|')
    for fn in ('TS-Tuyet-Giau-Chon-Phac.ttl', 'TS-Dai-Xa-Nhu-Truong.ttl',
               'TS-Minh-Hoang-Tu-Dung.ttl', 'TS-Phong-Huyet-Dien-Chieu.ttl'):
        if fn not in have:
            continue
        import rdflib
        g = rdflib.Graph()
        g.parse(os.path.join(TTL_DIR, fn), format='turtle')
        gen = [str(o) for s, p, o in g if str(p).endswith('generationOrder')]
        tea = [str(o).split('/')[-1] for s, p, o in g
               if str(p).endswith('hasTeacher')]
        lab = label_of(P._read(os.path.join(TTL_DIR, fn)),
                       'phong_huyet_dien_chieu')
        w('| `%s` | %s | %s | %s |'
          % (fn, ', '.join(gen[:2]) or '—', ', '.join(tea) or '—', lab or '—'))
    w()
    w('> 3 file này là **3 đời liên tiếp** (thầy → trò) nhưng dùng chung 1 URI.')
    w('> DB hiện chỉ có **1 row** (`phong_huyet_dien_chieu`). Cần Admin xác nhận:')
    w('> **3 người** (tách URI theo tên file) hay **1 người** (3 file trùng lặp)?')
    w()

    # ---------------------------------------------------------------- D
    w('---')
    w()
    w('## D. 🟠 File có NHÃN sai')
    w()
    if not l12:
        w('_Không có._')
    else:
        w('| # | File | Mã |')
        w('|---|---|---|')
        for i, fn in enumerate(l12, 1):
            code = 'L1' if any(x['file'] == fn for x in by_code['L1']) else 'L2'
            w('| %d | `%s` | %s |' % (i, fn, code))
        w()
        w('> Chi tiết nhãn chuẩn: `docs/Mimo-Flash/T203-ttl-quarantine-list.md`')
    w()

    # ---------------------------------------------------------------- E
    w('---')
    w()
    w('## E. ✅ File đã SỬA xong')
    w()
    w('| Nhóm | File | Việc đã làm |')
    w('|---|---|---|')
    for fn in t205_rep:
        if fn in have:
            w('| T205 — cú pháp | `%s` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, '
              'đóng statement |' % fn)
    w('| T206 — mojibake | %d file | `Ð` (U+00D0) → `Đ` (U+0110), 590 ký tự |'
      % 302)
    w('| T207 — DB | %d cột / 1.469 row | cùng loại lỗi trong DB + khôi phục tra cứu |'
      % 22)
    w()
    w('---')
    w()
    w('## Việc Admin cần làm (theo thứ tự ưu tiên)')
    w()
    w('1. **Cấp lại %d file TTL đã mất** (nhóm A) — không thể phục hồi bằng kỹ thuật.'
      % len(missing))
    w('2. **Quyết định 3 file `phong_huyet_dien_chieu`** — 3 người hay 1?')
    w('3. **Sửa %d file URI sai** (nhóm C) — duyệt trước vì đổi danh tính ontology.'
      % len(wrong_uri))
    w('4. **Sửa %d nhãn** (nhóm D) để ETL chạy được.' % len(l12))
    w()
    w('> ETL vẫn bị chặn cho tới khi L1/L2 = 0. Guard L6/L7 hiện đang **chặn**')
    w('> đúng — không phải lỗi.')
    w()

    text = '\n'.join(L)
    if args.stdout:
        print(text)
        return 0
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('[OK] Đã ghi %s' % OUT)
    print('     A mất=%d  B rỗng/hỏng=%d  C URI sai=%d  D nhãn sai=%d  E đã sửa=%d'
          % (len(missing), len(by_code['L6']) + len(by_code['L3']),
             len(wrong_uri), len(l12), len(t205_rep)))
    return 0


def slug_words(s):
    """'Bích Thiên Thanh Không' → chuỗi từ không dấu, để so với slug tên file."""
    import unicodedata
    t = unicodedata.normalize('NFD', s or '')
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return ' '.join(re.findall(r'[a-z0-9]+', t.lower()))


if __name__ == '__main__':
    sys.exit(main())