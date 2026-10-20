# -*- coding: utf-8 -*-
r"""T217 -> T222: session khác vừa tạo tasks/T217-vnpa-etl-preservation-guard.md.

T217 đã bị chiếm trong lúc đang xử lý. T222 là ID trống hoàn toàn (0 task file,
0 file prose tham chiếu). Thay tiền tố 217 -> 222 trong toàn file + viết lại
khối giải thích vì sao ID phải nhảy.
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EM = u'—'
OLD = 'docs/Mimo-Flash/T216-cloud-session-chain-c1-c6-plan.md'
NEW = 'docs/Mimo-Flash/T222-cloud-session-chain-c1-c6-plan.md'

BLOCK = re.compile(
    r'^> \*\*Đổi ID 2026-10-02 \(Admin chốt\):\*\*.*?'
    r'(?=^> \*\*Cảnh báo mirror:\*\*)',
    re.S | re.M)

NOTE = (
    '> **Đổi ID 2026-10-02 (Admin chốt):** `T180` → **`T222`**.\n'
    '>\n'
    '> Chuỗi cấp ID (cả 3 lần, mỗi lần do máy khác):\n'
    '>\n'
    '> | Bước | Lý do |\n'
    '> |---|---|\n'
    '> | `T180` | đã bị *"T180 — Phase 7 GOLD exporter"* chiếm |\n'
    '> | `T216` | đã bị đặt chỗ bằng **prose** cho follow-up '
    '*ETL UPSERT guard* (task thật, đang chờ Admin) |\n'
    '> | `T217` | session khác tạo `tasks/T217-vnpa-etl-preservation-guard.md` '
    'trong lúc đang xử lý |\n'
    '> | `T218`-`T221` | đã cấp cho 3 task gỡ trùng ID (xem ROLLBACK) '
    '/ `T221` đã bị đặt chỗ |\n'
    '>\n'
    '> `T222` trống hoàn toàn: 0 task file, 0 tham chiếu prose.\n'
    '>\n'
    '> **Bài học:** `build_progress_data.py --check-dup-ids` chỉ thấy ID\n'
    '> trùng ở mức file. Reservation bằng **prose** (như T216 đã từng\n'
    '> vậy) không tạo file task nên guard file-scan nhìn không thấy. '
    'Quy tắc: trước khi cấp\n'
    '> ID mới, **grep `T\\d+` trong `docs/tasktodo.md` + `docs/Mimo-Flash/`** '
    '(AGENTS.md §16).\n'
    '>\n'
)


def main():
    op = os.path.join(BASE, OLD)
    np_ = os.path.join(BASE, NEW)
    if not os.path.exists(op):
        if os.path.exists(np_):
            print('[SKIP] đã đổi rồi sang T222')
            return 0
        print('[FAIL] không tồn tại: %s' % OLD)
        return 1

    s = io.open(op, encoding='utf-8').read()

    head = 'id: T217\n'
    if s.count(head) != 1:
        print('[FAIL] id: T217 không khớp duy nhất (%d)' % s.count(head))
        return 1
    s = s.replace(head, 'id: T222\nformer_ids: [T180, T216, T217]\n')

    s2 = BLOCK.sub(lambda m: NOTE, s, count=1)
    if s2 == s:
        print('[FAIL] không khớp khối giải thích')
        return 1
    s = s2

    s = s.replace('T217', 'T222')

    io.open(np_, 'w', encoding='utf-8', newline='\n').write(s)
    os.remove(op)
    print('OK  %s\n -> %s' % (os.path.basename(OLD), os.path.basename(NEW)))

    left = [l for l in s.split('\n') if 'T217' in l]
    if left:
        print('[WARN] còn %d dòng chưa T217:' % len(left))
        for l in left[:5]:
            print('      ', l.strip()[:100])
        return 1
    print('    sạch T217')
    return 0


if __name__ == '__main__':
    sys.exit(main())