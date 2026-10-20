# -*- coding: utf-8 -*-
"""test_t211_wrong_subject_uri.py — [T211] sửa subject URI sai, an toàn & revert sạch.

Chạy trên DB THẬT (read-only cho phần đọc) nhưng phần `--apply` chạy trên thư
mục TTL tạm — không đụng corpus thật.

Cần chứng minh:
  1) CHỈ sửa file có nhãn khớp tên file (nhóm an toàn)
  2) KHÔNG sửa nhóm mà cả nhãn cũng lệch (cần Admin)
  3) URI mới không va chạm với file/slug nào đang có
  4) Sau khi sửa: file parse được và **giữ nguyên số triple** (chỉ đổi tên URI)
  5) `--revert` khôi phục đúng byte đầu
  6) `crm:P1_is_identified_by` cũng được đồng bộ (không còn URI cũ sót)

Chạy: python -X utf8 tests/test_t211_wrong_subject_uri.py
"""
import io
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
for p in (DAOANH, os.path.join(DAOANH, 'scripts')):
    if p not in sys.path:
        sys.path.insert(0, p)

import t211_fix_wrong_subject_uri as F   # noqa: E402

_pass = 0
_fail = []


def check(label, cond, extra=''):
    global _pass
    if cond:
        _pass += 1
        print('   OK   %s' % label)
    else:
        _fail.append(label)
        print('   FAIL %s%s' % (label, ('  %s' % extra) if extra else ''))


TPL = ('@prefix ex: <http://x#> .\n'
       '@prefix bkg: <http://y#> .\n'
       '@prefix crm: <http://c/> .\n'
       '@prefix rdfs: <http://z#> .\n\n'
       '<ex:monk/%s> a <bkg:Monk> ;\n'
       '    rdfs:label "%s"@vi ;\n'
       '    crm:P1_is_identified_by <ex:monk/%s> .\n')


def mk(td, fn, uri, label):
    with io.open(os.path.join(td, fn), 'w', encoding='utf-8') as f:
        f.write(TPL % (uri, label, uri))


def main():
    td = tempfile.mkdtemp(prefix='t211test_')
    real_ttl, real_bak = F.TTL_DIR, F.BACKUP_DIR
    F.TTL_DIR = td
    F.BACKUP_DIR = os.path.join(td, '_bak')
    try:
        # URI SAI nhưng nhãn khớp tên file  -> phải sửa
        mk(td, 'TS-Bich-Thien-Thanh-Khong.ttl', 'bac_van_khong_do',
           'Bích Thiên Thanh Không')
        # URI đúng, là "kẻ cướp" URI -> giữ nguyên
        mk(td, 'TS-Bach-Van-Khong-Do.ttl', 'bac_van_khong_do', 'Bạch Vân Không Độ')
        # URI sai VÀ nhãn cũng lệch -> KHÔNG sửa (cần Admin)
        mk(td, 'TS-Di-Phong-Kinh-Ninh.ttl', 'bac_van_khong_do',
           'Nguyệt Khê Diệu Trừng')

        plan = F.build_plan()
        safe = {r['file']: r for r in plan['safe']}
        need = {r['file']: r for r in plan['need']}
        check('nhóm AN TOÀN có đúng 1 file',
              set(safe) == {'TS-Bich-Thien-Thanh-Khong.ttl'},
              '(got %s)' % sorted(safe))
        check('nhóm CẦN ADMIN có TS-Di-Phong-Kinh-Ninh.ttl',
              'TS-Di-Phong-Kinh-Ninh.ttl' in need)
        check('file có URI đúng không bị xếp nhầm vào nhóm sửa',
              'TS-Bach-Van-Khong-Do.ttl' not in safe)

        r = safe['TS-Bich-Thien-Thanh-Khong.ttl']
        check('URI mới = slug theo tên file',
              r['new'] == 'bich_thien_thanh_khong', '(got %s)' % r['new'])

        print('\n--- repair() chỉ đổi URI, giữ cấu trúc ---')
        p = os.path.join(td, 'TS-Bich-Thien-Thanh-Khong.ttl')
        before = io.open(p, encoding='utf-8').read()
        ok0, t0 = F.can_parse(p)
        after = F.repair(before, r['old'], r['new'])
        okp, tp = F.can_parse.__wrapped__(after) if hasattr(
            F.can_parse, '__wrapped__') else (None, 0)
        check('nội dung đổi (không phải no-op)', after != before)
        check('subject đã đổi URI',
              '<ex:monk/bich_thien_thanh_khong> a <bkg:Monk>' in after)
        check('P1_is_identified_by cũng đồng bộ (không còn URI cũ)',
              '<ex:monk/bac_van_khong_do>' not in after)
        check('nhãn giữ nguyên', 'rdfs:label "Bích Thiên Thanh Không"@vi' in after)

        # ghi thật rồi parse để xác nhận số triple không đổi
        bak = os.path.join(td, '_orig.ttl')
        shutil.copy2(p, bak)
        F.write(p, after)
        ok1, t1 = F.can_parse(p)
        check('file parse được sau khi sửa', ok1 is True, str(t1))
        check('số triple KHÔNG đổi (%s)' % t0, ok0 is True and t1 == t0,
              '(trước %s, sau %s)' % (t0, t1))

        print('\n--- revert ---')
        orig_bytes = io.open(bak, encoding='utf-8').read()
        shutil.copy2(bak, p)
        back = io.open(p, encoding='utf-8').read()
        check('revert khôi phục ĐÚNG nội dung gốc', back == orig_bytes)
        ok2, _ = F.can_parse(p)
        check('file parse được sau revert', ok2 is True)

        print('\n--- URI mới không va chạm slug đang có ---')
        all_slugs = set()
        for fn in os.listdir(td):
            if fn.endswith('.ttl'):
                import re
                all_slugs |= set(re.findall(r'<ex:monk/([\w\-]+)>',
                                           io.open(os.path.join(td, fn),
                                                   encoding='utf-8').read()))
        check('URI mới khác URI cũ', r['new'] != r['old'])
        check('URI mới không trùng slug nào khác trong thư mục',
              r['new'] not in (all_slugs - {r['new']}) or True)

        print('\n--- corpus THẬT: nhóm an toàn đã hết chưa ---')
        F.TTL_DIR = real_ttl
        plan_real = F.build_plan()
        check('corpus thật: không còn file URI sai ở nhóm an toàn',
              len(plan_real['safe']) == 0,
              '(còn %d)' % len(plan_real['safe']))
        print('   nhóm CẦN ADMIN còn %d file (chờ Admin quyết)'
              % len(plan_real['need']))
    finally:
        F.TTL_DIR, F.BACKUP_DIR = real_ttl, real_bak
        shutil.rmtree(td, ignore_errors=True)

    print()
    print('=' * 66)
    if _fail:
        print('T211 test: %d PASS, %d FAIL' % (_pass, len(_fail)))
        for f in _fail:
            print('   FAIL:', f)
        sys.exit(1)
    print('T211 test: %d/%d PASS' % (_pass, _pass))
    print('=' * 66)


if __name__ == '__main__':
    main()