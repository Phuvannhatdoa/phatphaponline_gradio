"""Áp dụng lại lô housekeeping T374–T378 SAU KHI worktree được khôi phục về master.

Bối cảnh: 2026-10-13 ~12:57–13:00 một phiên khác chuyển worktree sang nhánh orphan `data-authority-lightweight`,
làm mất khỏi đĩa mọi file tracked của master — gồm phần sửa (chưa commit) của T374/T376/T378 trong
app.py, AGENTS.md, CLAUDE.md, docs/tasktodo.md. File untracked (task T374–T378, _archive/, api_zenlineage.py,
script/log) vẫn còn. Khi master được checkout lại, các file đã chuyển vào _archive (T375/T377) sẽ xuất hiện
lại ở chỗ cũ.

Script này idempotent — chạy lại nhiều lần không sao. Chạy từ daoanh/ :
  python -X utf8 docs/sessions/2026-10-13/housekeeping/reapply_after_restore.py --check   # chỉ báo trạng thái
  python -X utf8 docs/sessions/2026-10-13/housekeeping/reapply_after_restore.py --apply
Không chạy lệnh git nào.
"""
import hashlib
import importlib.util
import io
import os
import subprocess
import sys

H = 'docs/sessions/2026-10-13/housekeeping'
APPLY = '--apply' in sys.argv


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def need(path):
    if not os.path.exists(path):
        sys.exit('THIẾU %s — worktree chưa được khôi phục về master. Dừng.' % path)


def append_once(path, marker, text):
    raw = open(path, 'rb').read()
    if marker.encode('utf-8') in raw:
        return 'đã có'
    if not APPLY:
        return 'CẦN nối'
    nl = b'\r\n' if b'\r\n' in raw[:5000] else b'\n'
    data = text.replace('\n', nl.decode()).encode('utf-8')
    if not raw.endswith(nl):
        data = nl + data
    open(path, 'ab').write(data)
    return 'đã nối'


def rearchive(pairs, label):
    """pairs: list (src, dst). src xuất hiện lại sau checkout master; dst = bản đã lưu trữ."""
    out = []
    for src, dst in pairs:
        if not os.path.exists(src):
            out.append('ok      ' + src)
            continue
        if not os.path.exists(dst):
            out.append('KHÔNG có bản lưu trữ ' + dst)
            continue
        if sha(src) != sha(dst):
            out.append('LỆCH NỘI DUNG (giữ nguyên, Admin xem) ' + src)
            continue
        if APPLY:
            os.replace(src, dst)  # nội dung giống hệt -> chỉ bỏ bản trùng ở chỗ cũ
            out.append('đã chuyển ' + src)
        else:
            out.append('CẦN chuyển ' + src)
    print('[%s]' % label)
    for line in out:
        print('   ', line)


def main():
    for p in ('app.py', 'AGENTS.md', 'CLAUDE.md', 'docs/tasktodo.md', 'docs/ROLLBACK.md', 'scripts/build_progress_data.py'):
        need(p)

    # T374 — mục trỏ trong AGENTS.md / CLAUDE.md
    a = ("\n\n## 19. HOÀN TÁC MỘT BẢN SỬA (T374, 2026-10-13)\n\nQuy trình chuẩn: [`docs/process/REVERT_ONE_FIX.md`]"
         "(docs/process/REVERT_ONE_FIX.md) — một việc = một commit có tiền tố ID,\nstage theo đường dẫn tường minh "
         "(`git add -- <file>`), kiểm `git diff --cached --name-status`, hoàn tác bằng\n`git revert --no-edit <sha>`. "
         "Không commit được thì sao lưu `*.bak-before-T<id>` + MANIFEST + lệnh commit soạn sẵn.\n")
    c = ("\n## Hoàn tác một bản sửa\n\nXem `docs/process/REVERT_ONE_FIX.md` (T374): một việc = một commit có tiền tố ID, "
         "stage theo đường dẫn tường minh,\nhoàn tác bằng `git revert --no-edit <sha>`. Tình trạng git đo ngày 2026-10-13: "
         "`docs/sessions/2026-10-13/git-health.md`.\n")
    print('[T374] AGENTS.md:', append_once('AGENTS.md', '## 19. HOÀN TÁC MỘT BẢN SỬA (T374', a))
    print('[T374] CLAUDE.md:', append_once('CLAUDE.md', '## Hoàn tác một bản sửa', c))

    # Đăng ký T374–T378 trong tasktodo.md (trước T376 để T376 thấy đúng file)
    entries = [
        ('T374', 'Kiểm tra sức khỏe git + quy trình chuẩn hoàn tác một bản sửa', 'tasks/T374-git-health-and-revert-procedure.md'),
        ('T375', 'Gỡ 9 task ID trùng (npm run dup:ids)', 'tasks/T375-resolve-duplicate-task-ids.md'),
        ('T376', 'Thu gọn tasktodo.md: chuyển mục DONE sang docs/archive/tasktodo-done-2026.md', 'tasks/T376-tasktodo-archive-done.md'),
        ('T377', 'Dọn thư mục gốc daoanh vào _archive/2026-10-13-root-cleanup/', 'tasks/T377-root-cleanup-archive.md'),
        ('T378', 'Tách app.py bước 1: nhóm route zenlineage sang blueprint (con của T364)', 'tasks/T378-app-split-zenlineage-blueprint.md'),
    ]
    reg = ''
    for tid, title, path in entries:
        reg += ('\n<!-- %s:START -->\n> **[2026-10-13 · %s — %s] ⏳ IN_PROGRESS (housekeeping, Admin duyệt qua chat; '
                'chờ Admin ✔ Done).** Task: `%s`. Bàn giao: `docs/Handoff-2026-10-13-housekeeping.md`.\n<!-- %s:END -->\n'
                % (tid, tid, title, path, tid))
    print('[đăng ký] tasktodo.md:', append_once('docs/tasktodo.md', '<!-- T374:START -->', reg))

    # T375 / T377 — bỏ bản trùng xuất hiện lại sau checkout master
    t375 = load('t375', os.path.join(H, 't375_archive_dup_ids.py'))
    rearchive([(s, t375.ARCHIVE + '/' + s) for _i, s, _k in t375.PAIRS], 'T375')
    t377 = load('t377', os.path.join(H, 't377_root_cleanup.py'))
    rearchive([(n, t377.ARCHIVE + '/' + n) for n, _w in t377.ITEMS], 'T377')

    # T376 — chạy lại script (tự dừng nếu đã có dòng trỏ)
    todo = io.open('docs/tasktodo.md', encoding='utf-8').read()
    if '> 📦 **Mục DONE đã chuyển sang' in todo:
        print('[T376] đã áp dụng')
    else:
        args = [sys.executable, '-X', 'utf8', 'scripts/t376_archive_tasktodo_done.py', '--apply' if APPLY else '--dry-run']
        if not os.path.exists('scripts/t376_archive_tasktodo_done.py'):
            print('[T376] THIẾU scripts/t376_archive_tasktodo_done.py (untracked, phải còn) — dừng T376')
        else:
            if APPLY:
                # commit_plan.sh (C0) dùng file này làm nội dung tasktodo "sau đăng ký, trước T376"
                with open('docs/tasktodo.md', 'rb') as f_in, open(os.path.join(H, 'tasktodo.md.bak-before-T376'), 'wb') as f_out:
                    f_out.write(f_in.read())
            r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
            print('[T376]', (r.stdout.strip().splitlines() or ['?'])[0], '...', (r.stdout.strip().splitlines() or ['?'])[-1], r.stderr.strip()[-300:])

    # T378 — tách khối zenlineage nếu app.py còn khối đó
    app_txt = io.open('app.py', encoding='utf-8').read()
    if "@app.route('/daoanh/api/admin/zenlineage/candidates')" not in app_txt:
        print('[T378] đã áp dụng (app.py không còn route zenlineage)')
    elif APPLY:
        r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(H, 't378_extract_zenlineage.py')],
                           capture_output=True, text=True, encoding='utf-8')
        print('[T378]', r.stdout.strip(), r.stderr.strip()[-300:])
    else:
        print('[T378] CẦN tách (chạy với --apply)')

    # ROLLBACK.md — 5 dòng đầu bảng mục 1 (SHA điền sau bởi commit_plan.sh)
    rb = open('docs/ROLLBACK.md', 'rb').read().decode('utf-8')
    if '**T378 — tách 5 route zenlineage' in rb:
        print('[ROLLBACK] đã có')
    elif APPLY:
        with open(os.path.join(H, 'ROLLBACK.md.bak-before-T374-T378'), 'wb') as f:
            f.write(rb.encode('utf-8'))
        nl = '\r\n' if '\r\n' in rb else '\n'
        lines = rb.split(nl)
        i = next(k for k, l in enumerate(lines) if l.startswith('|------|------|'))
        lines[i + 1:i + 1] = ROLLBACK_ROWS
        open('docs/ROLLBACK.md', 'wb').write(nl.join(lines).encode('utf-8'))
        print('[ROLLBACK] đã chèn 5 dòng')
    else:
        print('[ROLLBACK] CẦN chèn 5 dòng')

    print('\nSau --apply: chạy npm run guard, npm run dup:ids, python -X utf8 scripts/build_progress_data.py,')
    print('và so route map: xem lệnh trong docs/Handoff-2026-10-13-housekeeping.md mục 9.')


ROLLBACK_ROWS = [
    "| 2026-10-13 | `<sha_T378>` (code, 0 DB) | **T378 — tách 5 route zenlineage sang blueprint `api_zenlineage.py`.** Route map 363=363. **Revert:** `git revert --no-edit <sha_T378>` (hoặc chép `docs/sessions/2026-10-13/housekeeping/app.py.bak-before-T378` + xoá `api_zenlineage.py`), restart app.py. |",
    "| 2026-10-13 | `<sha_T377>` (di chuyển file, 0 DB) | **T377 — dọn gốc daoanh: 60 file vào `_archive/2026-10-13-root-cleanup/`.** **Revert:** `git revert --no-edit <sha_T377>` (38 file git) + `python -X utf8 docs/sessions/2026-10-13/housekeeping/t377_root_cleanup.py --restore` (22 file bị .gitignore). |",
    "| 2026-10-13 | `<sha_T376>` (docs-only) | **T376 — mục DONE từ `tasktodo.md` sang `docs/archive/tasktodo-done-2026.md`.** **Revert:** `git revert --no-edit <sha_T376>` (hoặc chép `docs/sessions/2026-10-13/housekeeping/tasktodo.md.bak-before-T376`). |",
    "| 2026-10-13 | `<sha_T375>` (di chuyển file .md) | **T375 — 13 bản cũ trùng ID vào `_archive/2026-10-13-dup-ids/`; dup:ids 9→1 (T274 chờ Admin).** **Revert:** `git revert --no-edit <sha_T375>` (hoặc `t375_archive_dup_ids.py --restore`). |",
    "| 2026-10-13 | `<sha_T374>` (docs-only) | **T374 — git health + `docs/process/REVERT_ONE_FIX.md` + mục trỏ trong AGENTS/CLAUDE.** **Revert:** `git revert --no-edit <sha_T374>`. |",
]


if __name__ == '__main__':
    main()
