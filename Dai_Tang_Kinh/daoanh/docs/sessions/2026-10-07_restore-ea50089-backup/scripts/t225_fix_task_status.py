# -*- coding: utf-8 -*-
"""scripts/t225_fix_task_status.py — sửa 5 lỗi sổ sách task (T225).

Phát hiện từ `build_progress_data.scan_tasks()` + đối chiếu quy ước của chính repo
(task bàn giao Admin mà ĐÃ xong → `done`: T199/T201; còn CHỜ Admin → `blocked`:
T196/T197/T198). Dashboard chỉ có CSS cho 4 status {done, in_progress, pending,
blocked} nên status lạ sẽ không được tô màu.

Sửa (mỗi dòng đều có cơ sở kiểm chứng được):
  T192  thiếu hẳn frontmatter      -> thêm `status: done`  (body đã ghi "Trạng thái: DONE")
  T200  build_done_admin_review    -> `blocked`           (status không hợp lệ; chờ Admin)
  T27   blocked_until_needed       -> `blocked`           (status không hợp lệ; nợ kỹ thuật dài hạn)
  T167  pending                    -> `in_progress`       (tasktodo.md ghi IN_PROGRESS)
  T196  blocked                    -> `done`              (đã tìm ra cách vượt, ghi AGENTS.md §17)

KHÔNG đụng T198: `plan_approved_at` ghi rõ "chờ Admin duyệt" và cần quyết định
soft-invalidate vs hard purge — để nguyên `blocked`.

Idempotent: chạy lại sẽ báo SKIP.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rd(rel):
    return io.open(os.path.join(BASE, rel), encoding='utf-8').read()


def wr(rel, s):
    io.open(os.path.join(BASE, rel), 'w', encoding='utf-8', newline='\n').write(s)


def set_status(rel, old, new, extra_lines=(), note=None):
    """Đổi `status:` trong frontmatter. `old` = None nghĩa là thêm mới."""
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print('  [SKIP] khong ton tai: %s' % rel)
        return True
    s = rd(rel)
    target = 'status: %s\n' % new
    if target in s:
        print('  [SKIP] %s da co status: %s' % (os.path.basename(rel), new))
        return True
    if old is None:
        # T192: chua co frontmatter block
        assert not s.lstrip('\ufeff').startswith('---'), \
            '%s da co frontmatter roi' % rel
        fm = ['---', 'id: %s' % os.path.basename(rel).split('-')[0],
              'title: "%s"' % _title_of(s), 'module: Docs / Task Governance',
              'priority: high', target.rstrip('\n'),
              'owner: mimo-flash', 'created: 2026-09-29',
              'updated: 2026-10-02',
              'commit: "%s"' % _commit_hint(),
              'revert: "git revert --no-edit <sha>"',
              '---', '']
        s = '\ufeff' + '\n'.join(fm) + s.lstrip('\ufeff')
        wr(rel, s)
        print('  OK  %-46s -> them frontmatter, status: done' % os.path.basename(rel))
        return True
    src = 'status: %s\n' % old
    if src not in s:
        print('  [FAIL] %s khong co `status: %s`' % (rel, old))
        return False
    block = src
    if note:
        block = src + 'note: "%s"\n' % note
    for ln in extra_lines:
        block += ln + '\n'
    s = s.replace(src, block, 1)
    wr(rel, s)
    print('  OK  %-46s status: %s -> %s' % (os.path.basename(rel), old, new))
    return True


def _title_of(s):
    import re
    m = re.search(r'^#\s+(.+)$', s, re.M)
    t = m.group(1).strip() if m else ''
    return t.replace('"', "'")[:120]


def _commit_hint():
    import subprocess
    r = subprocess.run(['git', 'log', '-1', '--format=%h',
                        '--', 'Dai_Tang_Kinh/daoanh/tasks'],
                       capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.dirname(
                           os.path.dirname(os.path.abspath(__file__)))))
    return r.stdout.strip() or 'TBD'


def main():
    ok = True
    print('[1] T192 — thieu frontmatter -> status: done')
    ok &= set_status('tasks/T192-t173-plan-doc-correction.md', None, 'done')

    print('[2] T200 — status khong hop le -> blocked (cho Admin duyet)')
    ok &= set_status(
        'tasks/T200-vnpa-dila-id-duplicate-limit1.md',
        'build_done_admin_review', 'blocked',
        note='build da xong, da ban giao Admin; dung status blocked de '
             'dashboard hien thi dung (CSS chi ho tro 4 status)')

    print('[3] T27 — status khong hop le -> blocked')
    ok &= set_status('tasks/T27-source-neutral-entity-id.md',
                     'blocked_until_needed', 'blocked',
                     note='no ky thuat dai han; migrate entity_id khi can')

    print('[4] T167 — pending -> in_progress (theo tasktodo.md)')
    ok &= set_status(
        'tasks/T167-rules-constrained-buddhist-translation-engine.md',
        'pending', 'in_progress',
        note='tasktodo.md ghi IN_PROGRESS tu 2026-09-24; frontmatter chua cap nhat')

    print('[5] T196 — blocked -> done (da tim ra duong vuot bien)')
    ok &= set_status(
        'tasks/T196-git-update-ref-master-blocked.md', 'blocked', 'done',
        note='da giai quyet 2026-10-02: os.replace bi WinError 5; dung ghi file '
             'ref truc tiep co kiem CAS thu cong. Quy trinh ghi o AGENTS.md '
             '§17, dung 6 lan trong phien 2026-10-02')

    print('')
    print('KET QUA:', 'OK' if ok else 'CO LOI')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())