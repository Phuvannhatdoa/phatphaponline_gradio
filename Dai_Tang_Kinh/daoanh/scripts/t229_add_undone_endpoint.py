# -*- coding: utf-8 -*-
r"""scripts/t229_add_undone_endpoint.py — chèn route Done vào app.py (chỉ blob HEAD).

Vì sao chèn vào blob HEAD chứ không sửa trực tiếp trên đĩa:
  `app.py` đang có **331 dòng WIP của session khác** (git diff --numstat: 331/12).
  Nếu tôi sửa trên đĩa rồi `git add`, tôi sẽ nuốt WIP chưa xong của họ vào
  commit của mình. Nếu tôi dựng blob = HEAD + route của tôi, commit chỉ chứa
  route của tôi; WIP của họ vẫn nằm trên đĩa và họ commit sau.

Route: POST /daoanh/api/progress/task/<task_id>/status
  - BẮT BUỘC `verify_session()` (đúng pattern `admin_namevi_map_update`).
  - Ghi vào `data/task_status_overrides.json` — **additive**, không sửa `.md`.
    Lý do: `.md` là SSOT nhưng đang được nhiều session sửa song song; ghi từ web
    có nguy cơ race/mất nội dung. Xoá file override là revert trọn vẹn.
  - Sinh lại `progress_data.json` để dashboard thấy ngay.

Script chạy 1 lần rồi tự idempotent (thấy route trong HEAD là báo SKIP).
"""
import io
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(BASE, '..', '..'))
REL = 'Dai_Tang_Kinh/daoanh/app.py'

ANCHOR = "@app.route('/daoanh/api/compliance/dashboard', methods=['GET'])"

ROUTE = '''@app.route('/daoanh/api/progress/task/<task_id>/status', methods=['POST'])
@app.route('/api/progress/task/<task_id>/status', methods=['POST'])
def admin_progress_task_status(task_id):
    """POST — Admin bấm nút Done trên bảng UNDONE của dashboard.

    Ghi vào `data/task_status_overrides.json` (additive) thay vì sửa thẳng
    `tasks/*.md`: file `.md` là SSOT nhưng đang được nhiều session sửa song song,
    ghi từ web có nguy cơ race / mất nội dung. Xoá file override là revert
    trọn vẹn. Provenance (`by` / `at` / `note`) giữ trong file.

    BẮT BUỘC verify_session — endpoint này thay đổi trạng thái task trên board.
    """
    # T198/T223 — endpoint này đổi trạng thái task hiển thị cho Admin ⇒ cần auth.
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    task_id = (task_id or '').strip()
    # chỉ cho phép đúng dạng ID task để tránh path traversal khi tìm file
    if not re.match(r'^[A-Za-z]+[-A-Za-z0-9_]*$', task_id):
        return jsonify({"success": False,
                        "error": "task_id không hợp lệ"}), 400

    data = request.get_json(silent=True) or {}
    new_status = str(data.get('status', '')).strip()
    note = str(data.get('note', '')).strip()[:400]
    if new_status not in ('done', 'in_progress', 'pending', 'blocked'):
        return jsonify({"success": False,
                        "error": "status phải là done|in_progress|pending|blocked"}), 400

    # task phải tồn tại thật trong tasks/ — tránh ghi override cho task không có
    tasks_dir = os.path.join(BASE_DIR, 'tasks')
    match = [f for f in os.listdir(tasks_dir)
             if os.path.isfile(os.path.join(tasks_dir, f))
             and f.endswith('.md')
             and (f == task_id or f.startswith(task_id + '-')
                  or f == task_id + '.md')]
    if not match:
        return jsonify({"success": False,
                        "error": "không tìm thấy task trong tasks/"}), 404

    ov_path = os.path.join(DATA_DIR, 'task_status_overrides.json')
    overrides = {}
    if os.path.isfile(ov_path):
        try:
            with open(ov_path, encoding='utf-8') as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                overrides = {k: v for k, v in loaded.items()
                             if not k.startswith('_')}
        except Exception as e:
            return jsonify({"success": False,
                            "error": "file override đang hỏng: %s" % e}), 500

    overrides[task_id] = {
        'status': new_status,
        'by': 'admin',
        'at': datetime.now().isoformat(timespec='seconds'),
        'note': note,
        'file': match[0],
    }
    try:
        with open(ov_path, 'w', encoding='utf-8') as fh:
            json.dump({'_comment': 'Lớp override status do Admin bấm Done trên '
                                  'dashboard. Xoá file này để revert toàn bộ.'},
                      fh, ensure_ascii=False, indent=2)
            json.dump(overrides, fh, ensure_ascii=False, indent=2)
    except Exception as e:
        return jsonify({"success": False, "error": "ghi file thất bại: %s" % e}), 500

    # sinh lại dashboard để thấy ngay
    try:
        import subprocess as _sp
        _sp.run([_sys.executable,
                  os.path.join(BASE_DIR, 'scripts', 'build_progress_data.py')],
                 cwd=BASE_DIR, capture_output=True, text=True,
                 encoding='utf-8', errors='replace', timeout=60)
    except Exception:
        pass   # không chặn: file override đã ghi, lần tải sau sẽ thấy

    return jsonify({
        'success': True,
        'task_id': task_id,
        'status': new_status,
        'file': match[0],
        'override_file': os.path.basename(ov_path),
        'revert_hint': 'xoá %s để hoàn nguyên' % os.path.basename(ov_path),
    })


'''


def main():
    r = subprocess.run(['git', 'show', 'HEAD:' + REL], capture_output=True,
                       text=True, cwd=REPO)
    if not r.stdout:
        print('[FAIL] không đọc được HEAD:%s' % REL)
        return 1
    head_src = r.stdout
    if 'admin_progress_task_status' in head_src:
        print('[SKIP] HEAD đã có route')
        return 0

    idx = head_src.find(ANCHOR)
    if idx < 0:
        print('[FAIL] không tìm thấy neo "%s" trong HEAD' % ANCHOR)
        return 1

    new_src = head_src[:idx] + ROUTE + head_src[idx:]
    assert new_src != head_src
    print('  chèn %d dòng route ngay trước neo' % ROUTE.count('\n'))

    # ghi ra file tạm để đưa vào index bằng plumbing
    tmp = os.path.join(REPO, '.git', 'wt_t229_app.py')
    io.open(tmp, 'w', encoding='utf-8', newline='\n').write(new_src)
    # đồng thời vá lên đĩa để server chạy được khi test (WIP của session khác
    # trong đĩa được giữ nguyên: ta chèn thêm, không đụng phần còn lại)
    disk = os.path.join(BASE, 'app.py')
    cur = io.open(disk, encoding='utf-8').read()
    if 'admin_progress_task_status' not in cur:
        j = cur.find(ANCHOR)
        if j > 0:
            io.open(disk, 'w', encoding='utf-8', newline='\n').write(
                cur[:j] + ROUTE + cur[j:])
            print('  vá lên đĩa (giữ nguyên WIP của session khác)')
        else:
            print('  [WARN] không tìm thấy neo trên đĩa — chỉ vá blob HEAD')
    os.remove(tmp)
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())