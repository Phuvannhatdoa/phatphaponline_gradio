"""T376 — chuyển mục DONE của docs/tasktodo.md sang docs/archive/tasktodo-done-2026.md.

Chỉ chuyển khi CẢ HAI điều kiện đúng (bảo thủ, mơ hồ thì giữ lại):
  1. Dòng trạng thái của mục ghi DONE và không có IN_PROGRESS/BLOCKED/PENDING/OPEN/TREO.
  2. Mọi file tasks/*.md (bỏ bản X-) mang ID đó đều có frontmatter `status: done`.

Đơn vị được xét:
  - Khối marker `<!-- Txxx:START --> ... <!-- Txxx:END -->` (kể cả dải `T243-T250`): xét dòng `> **[` cuối cùng.
  - Dòng rời `> **[YYYY-MM-DD · Txxx...` nằm ngoài khối marker.
  - Đoạn bắt đầu `**Txxx ✅ DONE` (một mục duy nhất, chỉ kèm dòng `- ` con).
Không đụng: tiêu đề, phần ACTIVE/PENDING dạng văn xuôi, BUG-*, mục không có task file.

Chạy từ thư mục daoanh/:
  python -X utf8 scripts/t376_archive_tasktodo_done.py --dry-run
  python -X utf8 scripts/t376_archive_tasktodo_done.py --apply
Hoàn tác: git revert <sha_T376>, hoặc chép lại docs/sessions/2026-10-13/housekeeping/tasktodo.md.bak-before-T376.
"""
import glob
import io
import os
import re
import sys

TODO = 'docs/tasktodo.md'
ARCHIVE = 'docs/archive/tasktodo-done-2026.md'
POINTER = ('> 📦 **Mục DONE đã chuyển sang [archive/tasktodo-done-2026.md](archive/tasktodo-done-2026.md)** '
           '(T376, 2026-10-13; điều kiện: task file `status: done` + dòng trạng thái ghi DONE). '
           'Lưu trữ cũ hơn: [taskdone.md](taskdone.md).')

NOT_DONE = re.compile(r'IN_PROGRESS|in_progress|BLOCKED|blocked|PENDING|pending|\bOPEN\b|TREO|chưa DONE|CHƯA DONE|KHÔNG đánh DONE')
START = re.compile(r'^\s*<!--\s*([A-Za-z0-9_.\-]+):START\s*-->\s*$')
END = re.compile(r'^\s*<!--\s*([A-Za-z0-9_.\-]+):END\s*-->\s*$')
LINE_ENTRY = re.compile(r'^> \*\*\[\d{4}-\d{2}-\d{2}[^·\]]*·\s*(T\d+[a-z]?)(?:[-\s—]|\])')
PARA_ENTRY = re.compile(r'^\*\*(T\d+[a-z]?)\s+✅\s*DONE')


def load_task_status():
    status = {}
    for path in glob.glob('tasks/*.md'):
        name = os.path.basename(path)
        if name.startswith('X-'):
            continue
        with io.open(path, encoding='utf-8-sig') as f:
            head = f.read(4000)
        tid = None
        st = None
        if head.startswith('---'):
            fm = head.split('---', 2)[1] if head.count('---') >= 2 else ''
            m = re.search(r'^id:\s*["\']?([^"\'\s]+)', fm, re.M)
            tid = m.group(1) if m else None
            m = re.search(r'^status:\s*["\']?([A-Za-z_\-]+)', fm, re.M)
            st = m.group(1).lower() if m else None
        if not tid:
            m = re.match(r'(T\d+[a-z]?)', name)
            tid = m.group(1) if m else None
        if tid:
            status.setdefault(tid, []).append((path, st))
    return status


def ids_of_marker(name):
    m = re.fullmatch(r'T(\d+)-T(\d+)', name)
    if m:
        return ['T%d' % n for n in range(int(m.group(1)), int(m.group(2)) + 1)]
    if re.fullmatch(r'T\d+[a-z]?', name):
        return [name]
    return None


def all_done(ids, status):
    for tid in ids:
        files = status.get(tid)
        if not files or any(st != 'done' for _p, st in files):
            return False
    return True


def header_of(line):
    # phần trạng thái: tới hết cụm **...** đầu tiên, tối đa 260 ký tự
    m = re.match(r'^>?\s*\*\*(.*?)\*\*', line)
    return (m.group(1) if m else line)[:260]


def text_done(line):
    h = header_of(line)
    return 'DONE' in h and not NOT_DONE.search(h)


def plan(lines, status):
    """Trả về list (start, end_exclusive, label) các đơn vị sẽ chuyển."""
    units = []
    n = len(lines)
    in_block = [False] * n
    i = 0
    seen_markers = {}
    while i < n:
        m = START.match(lines[i])
        if m:
            name = m.group(1)
            j = i + 1
            while j < n and not END.match(lines[j]):
                j += 1
            for k in range(i, min(j + 1, n)):
                in_block[k] = True
            seen_markers[name] = seen_markers.get(name, 0) + 1
            ids = ids_of_marker(name)
            entries = [l for l in lines[i + 1:j] if l.startswith('> **[')]
            if (j < n and END.match(lines[j]).group(1) == name and ids and entries
                    and text_done(entries[-1]) and all_done(ids, status)):
                units.append((i, j + 1, 'block ' + name))
            i = j + 1
            continue
        i += 1
    # duplicate marker (vd T366 xuất hiện 2 lần) -> không chuyển khối đó
    units = [u for u in units if seen_markers.get(u[2].split(' ', 1)[1], 0) == 1]

    i = 0
    while i < n:
        if in_block[i] or not lines[i].strip():
            i += 1
            continue
        j = i
        while j < n and lines[j].strip() and not in_block[j]:
            j += 1
        para = lines[i:j]
        if all(l.startswith('> **[') for l in para):
            for k, l in enumerate(para):
                m = LINE_ENTRY.match(l)
                if m and text_done(l) and all_done([m.group(1)], status):
                    units.append((i + k, i + k + 1, 'line ' + m.group(1)))
        else:
            m = PARA_ENTRY.match(para[0])
            others = [l for l in para[1:] if l.startswith('**') or l.startswith('>')]
            if m and not others and text_done(para[0]) and all_done([m.group(1)], status):
                units.append((i, j, 'para ' + m.group(1)))
        i = j
    units.sort()
    return units


def squash(text):
    return re.sub(r'\s+', '', text)


def main():
    apply = '--apply' in sys.argv
    with open(TODO, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    if any(l.startswith('> 📦 **Mục DONE đã chuyển sang') for l in lines):
        sys.exit('tasktodo.md đã có dòng trỏ T376 — đã chạy rồi, dừng.')
    status = load_task_status()
    units = plan(lines, status)
    moved = set()
    for s, e, _ in units:
        moved.update(range(s, e))
    print('Đơn vị sẽ chuyển: %d (%d dòng / %d dòng)' % (len(units), len(moved), len(lines)))
    for s, e, label in units:
        print('  L%-4d-%-4d %-14s %s' % (s + 1, e, label, lines[s][:110] if not lines[s].startswith('<!--') else lines[s + 1][:110]))
    if not apply:
        return

    kept = []
    for idx, l in enumerate(lines):
        if idx in moved:
            continue
        # gỡ dòng trống thừa ngay sau mục vừa chuyển (tránh 3+ dòng trống)
        if not l.strip() and kept and not kept[-1].strip() and idx - 1 in moved:
            continue
        kept.append(l)
    kept.insert(1, '')
    kept.insert(2, POINTER)

    arch = ['# TASKTODO — Mục DONE đã lưu trữ (2026)', '',
            '> Chuyển nguyên văn từ `docs/tasktodo.md` bởi `scripts/t376_archive_tasktodo_done.py` (T376, 2026-10-13).',
            '> Điều kiện: task file `status: done` + dòng trạng thái ghi DONE. Thứ tự giữ như trong tasktodo.md.',
            '> Lưu trữ cũ hơn (trước 2026-10-02): `docs/taskdone.md`. Hoàn tác: `git revert <sha_T376>`.', '']
    for s, e, label in units:
        arch.append('<!-- T376 từ tasktodo.md L%d-%d (%s) -->' % (s + 1, e, label))
        arch.extend(lines[s:e])
        arch.append('')

    before = squash(text)
    after = squash(nl.join(kept).replace(POINTER, ''))
    moved_txt = squash(''.join(lines[k] for k in sorted(moved)))
    if len(after) + len(moved_txt) != len(before):
        sys.exit('KIỂM BẢO TOÀN THẤT BẠI: %d + %d != %d' % (len(after), len(moved_txt), len(before)))
    os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
    with open(ARCHIVE, 'w', encoding='utf-8', newline='') as f:
        f.write(nl.join(arch) + nl)
    with open(TODO, 'wb') as f:
        f.write(nl.join(kept).encode('utf-8'))
    print('Bảo toàn nội dung OK: %d = %d + %d ký tự (không tính khoảng trắng)' % (len(before), len(after), len(moved_txt)))
    print('Đã ghi', TODO, '(%d dòng) và' % len(kept), ARCHIVE)


if __name__ == '__main__':
    main()
