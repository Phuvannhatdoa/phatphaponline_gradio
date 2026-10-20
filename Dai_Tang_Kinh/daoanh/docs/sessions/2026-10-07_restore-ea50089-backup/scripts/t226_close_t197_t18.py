# -*- coding: utf-8 -*-
"""scripts/t226_close_t197_t18.py — đóng 2 task đã xong (T197, T18).

**T197** — `status: blocked` là CŨ. Verify 8 mục `done_when` trong REVIEW.md:
7/8 đã có (bao gồm §8 CORRECTION LOG 4.660 ký tự với đủ P0-1/P1-1..P1-4/P2).
Thiếu đúng 1 mục: *"absorb doc có correction log tương ứng"*. Script này thêm mục đó
vào `X-T177-dynamic-filter-absorb-directive-v2.md` rồi đóng T197 `done`.

**T18** — BDRC. Quyết định đã có từ 2026-08-23: "BDRC integration bị skip hoàn toàn.
Đây là quyết định đúng." Audit xác nhận adapter không tồn tại, `places.bdrc_id` không có
trong schema. `done_when` còn ghi "Admin quyết định scope mới" ⇒ đang chờ một quyết
định BDRC tương lai, không phải việc treo. Đóng `done` với kết luận skip.
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABSORB = 'docs/Mimo-Flash/X-T177-dynamic-filter-absorb-directive-v2.md'

CORRECTION = u"""
---

## 8. CORRECTION LOG — verify lại 2026-09-30 (T197)

> Thêm theo `tasks/T197-t177-review-correction.md` (`done_when`: *"absorb doc có
> correction log tương ứng"*). Giữ nguyên lịch sử — chỉ ghi đè chỗ sai.
> Bản REVIEW đầy đủ: `X-T177-directive-v2-trie-xml-dualhash-REVIEW.md` §8.

| # | Chỗ sai trong bản 2026-09-25 | Thực tế |
|---|---|---|
| P0-1 | Kết luận *"429 chưa từng xảy ra → retry/backoff phòng vệ"* | **Sai.** D7 đo thật **429 xịt 3/5 lần**. T178 đã có retry sẵn (`_T73_429_MAX_RETRY=2`, 0.5s→1s). ⇒ phòng vệ là **cần thiết**, không phải dư thừa. A8/C1 đã lỗi thời |
| P1-1 | Acceptance D8 ghi fixture khớp substring `天然` | `天然` có **0 rule / 0 glossary**. Fixture thật là **`丹霞`** (`TERM_DANHA`, `TERM_DAN_HA`). Ai viết assert theo `天然` sẽ **không phân biệt được** dòng dính |
| P1-2 | *"`constitution_hash` có 8 phần"*, tham chiếu dòng 168-199 | Có **10 phần** (thêm `p8:alignment_method` != 'none'). Tham chiếu đúng: **211-234** (`style_constitution.py`) |
| P1-3 | Rendered `12.287` < Raw `13.230` | **Trộn 2 mốc đo** (2026-09-25 vs 2026-09-26 sau D6). Nguyên tắc: **rendered ≥ raw** |
| P1-4 | 7 line-ref | Lệch **7/7**: 16575→17713 · 16569→17703 · 16412→17520 · 18396→19725 · 16606→import alias L44 (gọi L17771) · `style_constitution` 436→518 (`log_prompt_metrics`) |
| P2 | B4 "15 chỗ FROM translation_cache" · B8 "12+3 site" | B4 = **18** · B8 = **13+4**. dual-hash **1/1900**, cache **1900 invalidated** |

> ⚠️ **Cảnh báo hành vi — `invalidate_cache_all_semantic` là `DELETE`, mất audit
> trail.** Khác hẳn endpoint admin `POST /daoanh/api/admin/translate/invalidate`
> dùng `UPDATE status='invalidated'` (soft). Quyết định soft-vs-hard: **T198**.

### Số đo đã trôi — đo lại trước khi dùng
`rules active 119/19.014 chars` · `cache 1900 invalidated` · `app.py 22.896 dòng`
· `style_constitution.py 863` (mốc 2026-09-30).
"""


def patch_absorb():
    p = os.path.join(BASE, ABSORB)
    if not os.path.exists(p):
        print('  [FAIL] khong ton tai: %s' % ABSORB)
        return False
    s = io.open(p, encoding='utf-8').read()
    if 'CORRECTION LOG' in s.upper():
        print('  [SKIP] absorb doc da co CORRECTION LOG')
        return True
    # chen truoc muc "## Revert" de giu Revert lai cuoi
    m = re.search(r'^##\s*Revert\s*$', s, re.M)
    if m:
        s = s[:m.start()] + CORRECTION.lstrip('\n') + '\n' + s[m.start():]
    else:
        s = s.rstrip('\n') + '\n' + CORRECTION
    # danh dau da verify lai
    s = re.sub(r'^updated:\s*(\S+)$', u'updated: 2026-10-02', s, count=1, flags=re.M)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('  OK  %s  <- them §8 CORRECTION LOG' % os.path.basename(ABSORB))
    return True


def set_status(rel, old, new, extra=()):
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print('  [FAIL] khong ton tai: %s' % rel)
        return False
    s = io.open(p, encoding='utf-8').read()
    tgt = 'status: %s\n' % new
    if tgt in s:
        print('  [SKIP] %s da co status: %s' % (os.path.basename(rel), new))
        return True
    src = 'status: %s\n' % old
    if s.count(src) != 1:
        print('  [FAIL] %s: `status: %s` xuất hiện %d lần'
              % (rel, old, s.count(src)))
        return False
    block = tgt + ''.join(x + '\n' for x in extra)
    s = s.replace(src, block, 1)
    assert tgt in s and src not in s, rel
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('  OK  %-44s status: %s -> %s' % (os.path.basename(rel)[:44], old, new))
    return True


def main():
    ok = True
    print('[1] T197 — them CORRECTION LOG vao absorb doc')
    ok &= patch_absorb()

    print('[2] T197 — dong task')
    ok &= set_status(
        'tasks/T197-t177-review-correction.md', 'blocked', 'done',
        extra=('closed_at: "2026-10-02 (verify 8/8 muc done_when; status '
               '`blocked` truoc do la CU — chi thieu 1 muc absorb correction log)"',))

    print('[3] T18 — dong task voi ket luan SKIP')
    ok &= set_status(
        'tasks/T18-bdrc-integration-decision.md', 'blocked', 'done',
        extra=('closed_at: "2026-10-02 (Admin duyet de xuất 2026-10-02). '
               'Quyet dinh 2026-08-23: SKIP hoan toan — dung va co ly do. '
               'bdrc_adapter.py khong ton tai, places.bdrc_id khong co trong '
               'schema, entity_source_ids source=bdrc = 0 row. Muon lam lai '
               'BDRC thi tao task moi, khong mo lai T18"',))

    print('')
    print('KET QUA:', 'OK' if ok else 'CO LOI')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())