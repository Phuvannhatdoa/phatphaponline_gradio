# -*- coding: utf-8 -*-
"""scripts/t225_fix_t65_t66_board.py — gỡ mâu thuẫn ID T65/T66 trên board (bản 2).

Lần 1 dùng `os.remove` để dời file → bị WinError 5 (AV/backup giữ handle). Bản này
**không xoá file nào**, chỉ:
  1. Copy bản THẬT (`status: done`) từ `tasks/backup/` lên `tasks/` cho T65/T66.
  2. Sửa `id:` của 2 bản nháp cũ ở `tasks/T60`,`T61` cho khớp tên, và ghi chú trỏ
     tới bản thật. File nháp vẫn nằm ở `tasks/` — nhưng đã có `id` đúng nên
     không còn mạo danh T65/T66.

Kết quả mong muốn (dashboard chỉ quét `tasks/*.md` cấp 1):
  T60 pending (bản nháp, có ghi chú) · T61 pending (bản nháp, có ghi chú)
  T65 done (bản thật) · T66 done (bản thật)
Không còn ID nào hiện sai trạng thái.

Bản trùng trong `tasks/backup/` được đánh dấu "bản sao, xem tasks/" — không ảnh
hưởng board. Việc dọn vật lý để sau khi AV nhả handle.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(BASE, 'tasks')
B = os.path.join(T, 'backup')

PROMOTE = [('T65-bio-vi-lexicon-phase2.md', 'T65'),
           ('T66-place-desc-vi-dila-note.md', 'T66')]
FIX_ID = [('T60-bio-vi-lexicon-phase2.md', 'T65', 'T60'),
          ('T61-place-desc-vi-dila-note.md', 'T66', 'T61')]


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)


def main():
    ok = True
    print('[1] copy ban THAT (status done) len tasks/')
    for fname, tid in PROMOTE:
        src, dst = os.path.join(B, fname), os.path.join(T, fname)
        if os.path.exists(dst):
            s = read(dst)
            print('  [SKIP] tasks/%s da ton tai (id/len %d)' % (fname, len(s)))
        elif os.path.exists(src):
            write(dst, read(src))
            print('  OK  tasks/%s  <- backup/%s' % (fname, fname))
        else:
            print('  [FAIL] khong tim thay %s o ca hai noi' % fname)
            ok = False

    print('[2] danh dau ban trung trong tasks/backup/')
    for fname, tid in PROMOTE:
        src = os.path.join(B, fname)
        if not os.path.exists(src):
            continue
        s = read(src)
        mark = (u'\n> **2026-10-02 (T225):** đây là bản sao. Bản trên board nằm ở\n'
                u'> `tasks/%s` (`status: done`). File trong `backup/` không được\n'
                u'> dashboard quét nên không ảnh hưởng; giữ lại để lịch sử.\n' % fname)
        if 'T225):** đây là bản sao' not in s:
            write(src, s + mark)
            print('  OK  backup/%s  <- ghi chu "ban sao"' % fname)

    print('[3] sua id cua 2 ban nhap cu cho khop ten')
    for fname, old_id, new_id in FIX_ID:
        p = os.path.join(T, fname)
        if not os.path.exists(p):
            print('  [SKIP] khong ton tai: %s' % fname)
            continue
        s = read(p)
        if s.count('id: %s\n' % old_id) != 1:
            print('  [WARN] %s: khong co dung 1 lan `id: %s`' % (fname, old_id))
            continue
        s = s.replace('id: %s\n' % old_id, 'id: %s\n' % new_id, 1)
        s += (u'\n> **2026-10-02 (T225):** bản nháp cũ — trước đây mang nhầm\n'
              u'> `id: %s`, khiến board hiển thị sai trạng thái cho task %s.\n'
              u'> Bản thật của T%s nằm ở `tasks/T%s-*.md` với `status: done`.\n'
              % (old_id, old_id, new_id, new_id))
        write(p, s)
        print('  OK  tasks/%s  id %s -> %s' % (fname, old_id, new_id))

    print('')
    print('KET QUA:', 'OK' if ok else 'CO LOI')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())