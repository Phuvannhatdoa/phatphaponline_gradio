# -*- coding: utf-8 -*-
r"""test_t216_dup_ids_guard.py — [T216] guard phát hiện task ID trùng.

Bối cảnh: bản gốc plan T180 (nay là T222) đổi ID `T180` → `T180` rồi mới phát hiện
ID đó đã bị task "Phase 7 GOLD exporter" chiếm. Không guard nào bắt được, nên
dashboard vẫn hiện "102 task" — sai lệch. Bản test này khóa hành vi của
`build_progress_data.py --check-dup-ids`.

Cần chứng minh:
  1) ID trùng thật (2 file đều không có tiền tố `X-`) → FAIL, exit 1
  2) Bản `X-` superseded chia sẻ ID với bản gốc → chỉ INFO, không FAIL
  3) `_book/` (mirror toàn bộ) bị loại trừ, không gây trùng giả
  4) Task thiếu `id:` trong frontmatter nhưng tên file có `T217` → vẫn bắt trùng
  5) BOM trước `---` làm `parse_frontmatter` trượt → guard đọc `utf-8-sig` nên vẫn thấy
  6) `docs/**` khai báo `task: tasks/<...>` là bản mở rộng của task, không phải task thứ hai
  7) File trong `docs/` chỉ đặt tên theo ID task → KHÔNG được suy ID
  8) File không phải task (tên không bắt đầu `T<so>`, không có `id:`) → bỏ qua
  9) ID của task này không trùng trong repo thật

Chạy: python -X utf8 tests/test_t216_dup_ids_guard.py
"""
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
for _p in (DAOANH, os.path.join(DAOANH, 'scripts')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_progress_data as B   # noqa: E402

_pass = 0
_fail = []


def check(label, cond, extra=''):
    global _pass
    if cond:
        _pass += 1
        print('   OK   %s' % label)
    else:
        _fail.append(label)
        print('   FAIL %s %s' % (label, extra))


def _fm(tid):
    return '---\nid: %s\ntitle: "t"\n---\n\nbody\n' % tid


def _write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)


def _run_case(name, files, expect_rc):
    """Dựng cây giả trong thư mục tạm, trỏ BASE_DIR/DOCS_DIR/TASKS_DIR vào đó, chạy guard."""
    root = tempfile.mkdtemp(prefix='t216_dup_')
    saved = (B.BASE_DIR, B.DOCS_DIR, B.TASKS_DIR)
    try:
        os.makedirs(os.path.join(root, 'docs'))
        os.makedirs(os.path.join(root, 'tasks'))
        for rel, text in files.items():
            _write(os.path.join(root, rel), text)
        B.BASE_DIR = root
        B.DOCS_DIR = os.path.join(root, 'docs')
        B.TASKS_DIR = os.path.join(root, 'tasks')
        rc = B.check_dup_ids()
        check('%s -> rc=%d' % (name, rc), rc == expect_rc, '(mong doi %d)' % expect_rc)
    finally:
        B.BASE_DIR, B.DOCS_DIR, B.TASKS_DIR = saved
        shutil.rmtree(root, ignore_errors=True)


def main():
    print('=' * 60)
    print('[T216] test guard trùng task ID (--check-dup-ids)')
    print('=' * 60)

    # 1) Hai file "sống" cùng id -> FAIL
    _run_case('trùng thật (2 file đều không X-)', {
        'tasks/T217-a.md': _fm('T217'),
        'tasks/T217-b.md': _fm('T217'),
    }, 1)

    # 2) Bản X- superseded chia sẻ id -> hợp lệ, không FAIL
    _run_case('X- superseded chung id -> INFO không FAIL', {
        'tasks/T177-dynamic-filter.md': _fm('T177'),
        'docs/Mimo-Flash/X-T177-dynamic-filter.md': _fm('T177'),
    }, 0)

    # 3) _book/ mirror không được tính
    _run_case('_book mirror bị loại trừ', {
        'tasks/T217-only.md': _fm('T217'),
        'docs/Mimo-Flash/_book/tasks/T217-only.md': _fm('T217'),
    }, 0)

    # 4) ID duy nhất -> OK
    _run_case('ID duy nhất -> OK', {
        'tasks/T217-x.md': _fm('T217'),
        'tasks/T217-y.md': _fm('T218'),
        'docs/Mimo-Flash/z.md': _fm('T219'),
    }, 0)

    # 5) Task thiếu frontmatter id nhưng tên file có T217 -> vẫn phải bắt trùng
    #    (bản đầu tôi cho case này là "không có id -> bỏ qua" (mong đợi rc=0); sau khi
    #    vá lỗ hổng "thiếu frontmatter thì lọt khỏi kiểm tra", kỳ vọng đổi thành FAIL)
    _run_case('thiếu frontmatter id, tên file có T217 -> bắt trùng', {
        'tasks/T217-co-frontmatter.md': '---\ntitle: "a"\n---\n\nbody\n',
        'tasks/T217-co-frontmatter-2.md': 'body khong co frontmatter\n',
    }, 1)

    # 6) BOM làm '---' mở frontmatter không khớp -> guard đọc utf-8-sig nên vẫn thấy id
    _run_case('BOM trước frontmatter -> vẫn đọc được id', {
        'tasks/T217-bom.md': u'﻿---\nid: T217\ntitle: "b"\n---\n\nbody\n',
        'tasks/T217-bom-2.md': u'﻿---\ntitle: "b"\n---\n\nbody\n',
    }, 1)

    # 7) Tên file không bắt đầu bằng T<số> và không có id -> bỏ qua
    _run_case('tên file không phải task id -> bỏ qua', {
        'tasks/README.md': 'x\n',
        'docs/Mimo-Flash/ghi-chu.md': 'y\n',
    }, 0)

    # 8) docs/ khai báo `task: tasks/...` là bản mở rộng của task -> không FAIL
    _run_case('docs/ gắn liền task -> không FAIL', {
        'tasks/T217-a.md': _fm('T217'),
        'docs/Mimo-Flash/T217-a-extended.md':
            '---\nid: T217\ntitle: "x"\ntask: tasks/T217-a.md\n---\n\nbody\n',
    }, 0)

    # 9) report trong docs/ đặt tên theo ID task (T222-D4-...-prep.md) -> KHÔNG suy ID
    _run_case('docs/ đặt tên theo ID task -> không suy ID', {
        'tasks/T217-a.md': _fm('T217'),
        'docs/Mimo-Flash/T217-D4-prep.md': 'body khong co frontmatter\n',
    }, 0)

    # 10) ID của task này không trùng trong repo thật
    seen, _att = B.collect_frontmatter_ids()
    check('T222 không trùng trong repo thật',
          len(seen.get('T222', [])) == 1,
          'thay %d file' % len(seen.get('T222', [])))

    print()
    print('=' * 60)
    print('  PASS %d/%d' % (_pass, _pass + len(_fail)))
    if _fail:
        for f in _fail:
            print('   FAIL: %s' % f)
        print('=' * 60)
        return 1
    print('  OK — guard trùng ID hoạt động đúng')
    print('=' * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())