# -*- coding: utf-8 -*-
"""scripts/t223_tasktodo_entry.py — chen muc T223 vao docs/tasktodo.md.

Dựng nội dung từ **blob HEAD** (không phải bản trên đĩa) rồi `hash-object` + cacheinfo,
nên WIP của session khác trong `tasktodo.md` không bị nuốt và không bị revert.
Chạy lại (đã có mục T223) sẽ báo SKIP — idempotent.
"""
import io
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(BASE, '..', '..'))
REL = 'Dai_Tang_Kinh/daoanh/docs/tasktodo.md'

ENTRY = u"""
### T223 — 2026-10-03 — DILA-ID 29 nhóm trùng: phân loại + quyết gộp/tách (chờ Admin)

**Task:** `tasks/T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md` ·
**Status:** `ready-for-admin-review` · **Priority:** critical

**Vì sao tách khỏi T200:** T200 build xong nhưng còn treo *"không gộp/tách `dila_id`
cho 33 nhóm — cần Admin duyệt từng nhóm"*. Đo lại 2026-10-03: **29 nhóm / 61 row**.

**Phát hiện quan trọng (đã verify):** **11/23** file L1/L2 của T209 nằm bên trong
các nhóm `dila_id` trùng ⇒ **L7 URI sai → L1/L2 nhãn sai → nhiều row chung 1
`dila_id`** là **một chuỗi hỏng duy nhất**.

> ⚠️ **Thứ tự sửa bắt buộc: L7 (URI) → L1/L2 (nhãn) → mới tới `dila_id`.** Sửa
> `dila_id` trước sẽ bị ETL tái tạo lại y hệt 29 nhóm từ nguồn TTL.

**Phân loại 29 nhóm:** A tách 1 · B-alias-đúng 3 (không làm gì) · B-trùng-dòng 3 (gộp)
· B-2-người 1 (tách) · C cần kiểm 7 · D tách 13.

**Blocker:** 13 file URI sai (T211) · 24 nhãn (T209) · 10 file TTL mất · 3 người hay 1
(`phong_huyet_dien_chieu`). Preflight **BLOCKING 29** ⇒ ETL chưa chạy được.

**Kèm 2 việc còn mở để Admin chốt một lần:**
- **T198** — `invalidate_cache_all_semantic` dùng `DELETE` (mất audit trail) trong khi
  endpoint admin dùng `UPDATE status='invalidated'` (soft). Đề xuất: **giữ soft**.
- **T98** (đã `done`, không chặn) — Q1 nút *"Đọc đầy đủ"* mở modal Hán văn gây nhầm
  (`app.py:2517`, `:2825`) ⇒ đổi label; Q2 ẩn warning *"⚠ phân phối tự động"* đã lỗi
  thời sau T96; Q3 giữ panel mở — để sau.

**Đã đóng trong phiên 2026-10-03:** `T197` (thêm §8 CORRECTION LOG vào absorb doc —
đủ 8/8 `done_when`; `blocked` trước đó là cũ) · `T18` (BDRC: kết luận 2026-08-23 "SKIP
hoàn toàn — đúng và có lý do") · `T196` · `T192` · `T65` `T66` `T62` `T63` `T64` `T64b`
`T67` `T68` `T69` (đưa từ `tasks/backup/` lên board).
"""


def main():
    r = subprocess.run(['git', 'show', 'HEAD:' + REL], capture_output=True, text=True,
                       cwd=REPO)
    s = r.stdout
    if not s:
        print('[FAIL] khong doc duoc HEAD:%s' % REL)
        return 1
    if 'T223' in s:
        print('[SKIP] HEAD da co muc T223')
        return 0
    m = re.search(r'^##\s*PENDING\s*[—-]\s*Ch\u1edd \u0111i\u1ec7n\s*$', s, re.M)
    if not m:
        m = re.search(r'^##\s*ACTIVE\s*[—-]\s*In Progress\s*$', s, re.M)
    if not m:
        print('[FAIL] khong tim thay muc ACTIVE / PENDING trong HEAD')
        return 1
    s2 = s[:m.end()] + u'\n' + ENTRY.strip('\n') + u'\n' + s[m.end():]
    assert s2 != s
    io.open(os.path.join(BASE, 'docs', 'tasktodo.md'), 'w',
            encoding='utf-8', newline='\n').write(s2)
    print('OK  chen muc T223 vao "%s"' % m.group(0).strip())
    return 0


if __name__ == '__main__':
    sys.exit(main())