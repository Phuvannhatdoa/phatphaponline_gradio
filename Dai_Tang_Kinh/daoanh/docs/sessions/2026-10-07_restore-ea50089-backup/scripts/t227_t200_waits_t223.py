# -*- coding: utf-8 -*-
"""scripts/t227_t200_waits_t223.py — T200 -> `blocked`, lý do "chờ T223" (Admin 2026-10-03).

T200 **build đã xong** (tie-break theo status Admin đã chốt 2026-10-01, test hồi quy
deterministic, 0 DB change). Phần còn lại là **quyết định gộp/tách `dila_id`** — việc
này đã tách sang **T223** (29 nhóm / 61 row, phân loại A/B/C/D kèm đề xuất) vì số "33
nhóm" của T200 đã trôi.

Ghi rõ quan hệ hai chiều để không ai tưởng T200 bị bỏ:
  T200 (build)  ──chờ──▶  T223 (quyết định dữ liệu)  ──cần──▶  T209 (L7/L1/L2 trước)

Sửa thêm `done_when` để phản ánh số đo thật (29 nhóm, không phải 33) và bỏ phần đã
chuyển sang T223, tránh hai task cùng đòi một việc.
Idempotent: chạy lại sẽ báo SKIP.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = 'tasks/T200-vnpa-dila-id-duplicate-limit1.md'

NEW_NOTE = (u'note: "build da xong, da ban giao Admin; dung status blocked de dashboard '
            u'hien thi dung (CSS chi ho tro 4 status)"\n')
REPLACE_NOTE = (u'blocked_by: T223\n'
                u'note: "BUILD XONG — phan con lai CH\u1ece T223 (2026-10-03, Admin ph\u00ea '
                u'chu\u1ea5n). T223 lo ph\u1ea7n quy\u1ebft g\u1ed9p/t\u00e1ch dila_id cho 29 '
                u'nh\u00f3m / 61 row (\u0111o l\u1ea1i 2026-10-03; con so 33 nhuoc ban ghi l\u1ea1i). '
                u'L\u00fd do ch\u1edd: 11/23 file L1/L2 cua T209 n\u1eb1m trong c\u00e1c nh\u00f3m '
                u'nay \u21d2 L7 URI sai \u2192 L1/L2 nh\u00e3n sai \u2192 nhi\u1ec1u row chung 1 '
                u'dila_id. Ph\u1ea3i s\u1eeba L7 \u2192 L1/L2 \u2192 m\u1edbi t\u1edbi dila_id."\n')


def main():
    p = os.path.join(BASE, REL)
    if not os.path.exists(p):
        print('  [FAIL] khong ton tai: %s' % REL)
        return 1
    s = io.open(p, encoding='utf-8').read()
    ok = True

    if 'blocked_by: T223' in s:
        print('  [SKIP] T200 da co blocked_by: T223')
        return 0

    # 1) note -> blocked_by + note moi
    if NEW_NOTE in s:
        s = s.replace(NEW_NOTE, REPLACE_NOTE, 1)
        print('  OK  them blocked_by: T223 + note moi')
    else:
        print('  [WARN] khong tim thay `note:` de thay — kiem tra thu cong')
        ok = False

    # 2) done_when: 33 -> 29, va chuyen phan quyet dinh sang T223
    old_33 = u'      33 nh\u00f3m tr\u00f9ng \u0111\u01b0\u1ee3c l\u1eabp danh s\u00e1ch + ph\u00e2n lo\u1ea1i (alias vs canonical vs xung \u0111\u1ed9t t\u00ean th\u1eadt);'
    new_29 = u'      ~~33 nh\u00f3m~~ \u2192 **29 nh\u00f3m / 61 row** (\u0111o l\u1ea1i 2026-10-03). Ph\u00e2n ph\u00e2n lo\u1ea1i +\u2026 **chuy\u1ec3n sang T223**;'
    if old_33 in s:
        s = s.replace(old_33, new_29, 1)
        print('  OK  done_when: 33 nhom -> 29 nhom (do that)')
    else:
        print('  [WARN] khong tim thay dong "33 nhom trung" trong done_when')
        ok = False

    old_dec = (u'      A021395 (3 t\u00ean kh\u00e1c: Ng\u0169 T\u1ed5/B\u00e1o \u00c2n/T\u1ee9 T\u1ed5 '
               u'Ph\u00e1p Di\u1ec5n) + A047679 (2 ng\u01b0\u1eddng kh\u00e1c chung dila_id)\n'
               u'        \u2192 Admin quy\u1ebft \u0111\u1ecbnh: t\u00e1ch dila_id hay g\u1ed9p d\u00f2ng;')
    new_dec = u'      ~~A021395 + A047679 \u2192 Admin quy\u1ebft~~ \u2192 **T223 \u00a73** (\u0111\u00e3 ph\u00e2n lo\u1ea1i 29 nh\u00f3m A/B/C/D);'
    if old_dec in s:
        s = s.replace(old_dec, new_dec, 1)
        print('  OK  done_when: phan quyet dinh A021395 chuyen sang T223')
    else:
        print('  [WARN] khong tim thay khoi A021395 trong done_when')
        ok = False

    s = s.replace('updated: 2026-09-30', 'updated: 2026-10-03', 1)

    assert 'blocked_by: T223' in s
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('  OK  %s' % REL)
    print('')
    print('KET QUA:', 'OK' if ok else 'CO CAN KIEM LAI THU CONG')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())