"""T377 — chuyển file nháp/log/backup ở gốc daoanh/ vào _archive/2026-10-13-root-cleanup/ + MANIFEST.md.

Chạy từ thư mục daoanh/:
  python -X utf8 docs/sessions/2026-10-13/housekeeping/t377_root_cleanup.py            # chuyển
  python -X utf8 docs/sessions/2026-10-13/housekeeping/t377_root_cleanup.py --restore  # chuyển ngược
Danh sách đã lọc: không file nào được code tham chiếu (trừ cặp script nháp + file nó đọc, chuyển cùng nhau),
không log server đang ghi (sửa đổi hôm nay), không .env/config.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

ARCHIVE = '_archive/2026-10-13-root-cleanup'

# (file, lý do)
ITEMS = [
    # output nháp (2026-10-11)
    *[('scratchpad_out%s.txt' % s, 'output nháp một lần (scratchpad), không code nào đọc') for s in ('', '2', '3', '4', '5', '6', '7', '8')],
    # script sửa một lần (2026-08-22), không ai gọi
    ('fix_css.py', 'script sửa CSS chạy một lần (08-22), không code nào gọi'),
    ('fix_arrays.py', 'script sửa một lần (08-22), không code nào gọi'),
    ('fix_original_css.py', 'script sửa CSS chạy một lần (08-22); đọc original_style_block.txt (chuyển cùng)'),
    ('original_style_block.txt', 'dữ liệu nháp chỉ fix_original_css.py đọc (chuyển cùng)'),
    ('dark_theme_css.txt', 'đoạn CSS nháp (08-22), không code nào đọc'),
    ('insert_css.py', 'script chèn CSS chạy một lần (08-22), không code nào gọi'),
    ('fix_home_search.py', 'script sửa một lần (08-22), không code nào gọi'),
    ('fix_home.py', 'script sửa một lần (08-22), không code nào gọi'),
    ('add_home_search.py', 'script chèn một lần (08-22), không code nào gọi'),
    ('find_search.py', 'script dò nháp (08-22), không code nào gọi'),
    ('read_search.py', 'script dò nháp (08-22), không code nào gọi'),
    ('search_lines.py', 'script dò nháp (08-22), không code nào gọi'),
    ('find_fetches.py', 'script dò nháp (08-22), không code nào gọi'),
    ('find_entity.py', 'script dò nháp (08-17); ghi entity_search_result.txt (chuyển cùng)'),
    ('entity_search_result.txt', 'output của find_entity.py (chuyển cùng)'),
    ('home_dump.txt', 'output nháp (08-22)'),
    ('phase_b_20.txt', 'output nháp (08-21)'),
    ('phase_b_100.txt', 'output nháp (08-21)'),
    ('deploy_test.txt', 'file thử deploy (09-21, 34 byte)'),
    ('GET', 'file rỗng 0 byte tạo nhầm (05-14)'),
    # bản sao lưu cũ
    ('app.py.backup_t130_s1', 'bản sao lưu app.py trước T130 S1 (09-23); git đã giữ lịch sử'),
    ('places.html.backup_t130_s2', 'bản sao lưu places.html trước T130 S2 (09-23); git đã giữ lịch sử'),
    ('index.bak-20260830.html', 'bản sao lưu index.html (08-30)'),
    # log cũ, không còn tiến trình ghi (không sửa hôm nay), không tài liệu nào trỏ tới
    ('gateway_local.err', 'log cũ (09-13)'),
    ('gateway_backend.err', 'log cũ (09-13)'),
    ('gateway_backend.out', 'log cũ (09-13)'),
    ('app_5002.log.err', 'log cũ (10-01)'),
    ('app_local2.err', 'log rỗng 0 byte (08-20)'),
    ('app_local.log.err', 'log cũ (10-07)'),
    ('gateway_local.log.err', 'log cũ (10-07)'),
    ('server_local.err', 'log cũ (10-07)'),
    ('app_err.log', 'log cũ (10-04)'),
    ('app_local_err.log', 'log cũ (10-07)'),
    ('app_test.log', 'log cũ (10-08)'),
    ('app_restart.log', 'log cũ (10-11)'),
    ('app_restart_err.log', 'log cũ (10-11)'),
    ('_test_output.log', 'log cũ (10-09)'),
    # output tính toán/khảo sát nháp (2026-10-11), bị .gitignore
    ('A001984_calc.json', 'output tính số đời nháp (10-11)'),
    ('A001984_calc.json.summary.json', 'tóm tắt output nháp (10-11)'),
    ('A027028_calc.json', 'output tính số đời nháp (10-11)'),
    ('A027028_calc.json.summary.json', 'tóm tắt output nháp (10-11)'),
    ('A027242_calc.json', 'output tính số đời nháp (10-11)'),
    ('A027242_calc.json.summary.json', 'tóm tắt output nháp (10-11)'),
    ('chan_ca_diep_1_A027028_issues.json', 'output khảo sát nháp (10-11)'),
    ('guiyang_A027028_issues.json', 'output khảo sát nháp (10-11)'),
    ('edges_A027028.json', 'output khảo sát nháp (10-11)'),
    ('edges_A027242.json', 'output khảo sát nháp (10-11)'),
    ('marcus_search1.json', 'output tra Marcus nháp (10-11)'),
    ('marcus_search2.json', 'output tra Marcus nháp (10-11)'),
    ('marcus_search3.json', 'output tra Marcus nháp (10-11)'),
    ('marcus_search4.json', 'output tra Marcus nháp (10-11)'),
    ('marcus_out_scratch.json', 'output tra Marcus nháp (10-11)'),
]


def tracked(path):
    r = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', path], capture_output=True)
    return r.returncode == 0


def sha16(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def restore():
    for name, _ in ITEMS:
        dst = ARCHIVE + '/' + name
        if os.path.isfile(dst) and not os.path.exists(name):
            shutil.move(dst, name)
            print('restored', name)


def main():
    os.makedirs(ARCHIVE, exist_ok=True)
    rows, skipped = [], []
    for name, why in ITEMS:
        if not os.path.isfile(name):
            skipped.append((name, 'không tồn tại'))
            continue
        size = os.path.getsize(name)
        h = sha16(name)
        tr = 'git' if tracked(name) else 'không (ignored/untracked)'
        try:
            shutil.move(name, ARCHIVE + '/' + name)
        except OSError as e:  # file đang bị tiến trình giữ -> bỏ qua
            skipped.append((name, 'không chuyển được: %s' % e))
            continue
        rows.append((name, ARCHIVE + '/' + name, why, size, tr, h))
    out = io.StringIO()
    out.write('# MANIFEST — T377 dọn thư mục gốc daoanh (2026-10-13)\n\n')
    out.write('Chỉ chuyển, không xoá. Đường dẫn gốc là tương đối với `Dai_Tang_Kinh/daoanh/`.\n\n')
    out.write('Khôi phục tất cả: `python -X utf8 docs/sessions/2026-10-13/housekeeping/t377_root_cleanup.py --restore`.\n')
    out.write('Khôi phục một file: chuyển ngược `_archive/2026-10-13-root-cleanup/<file>` → `<file>`.\n')
    out.write('File cột "git" = được git theo dõi: sau khi commit T377 thì `git revert <sha_T377>` cũng khôi phục.\n')
    out.write('File "không" = bị .gitignore → chỉ khôi phục được bằng cách chuyển ngược (git không giữ).\n\n')
    out.write('| Đường dẫn gốc | Đường dẫn mới | Lý do | Byte | Git theo dõi | sha256[:16] |\n|---|---|---|---:|---|---|\n')
    for r in rows:
        out.write('| `%s` | `%s` | %s | %d | %s | `%s` |\n' % r)
    if skipped:
        out.write('\n## Không chuyển\n\n')
        for n, why in skipped:
            out.write('- `%s` — %s\n' % (n, why))
    out.write('\n## Cố ý để lại (được tham chiếu hoặc chưa chắc)\n\n')
    for n, why in KEEP:
        out.write('- `%s` — %s\n' % (n, why))
    with open(ARCHIVE + '/MANIFEST.md', 'w', encoding='utf-8', newline='\n') as f:
        f.write(out.getvalue())
    print('đã chuyển %d file, bỏ qua %d' % (len(rows), len(skipped)))
    for n, why in skipped:
        print('  bỏ qua', n, '-', why)


KEEP = [
    ('fix_all.py', 'được scripts/build_progress_data.py nêu tên (SKIP_FILES)'),
    ('fix_tabs.js', 'được scripts/build_tab_readiness.py tham chiếu'),
    ('sync_to_vps.log', 'do sync_to_vps.ps1 ghi'),
    ('app_local.log, app_local.err, gateway_local.log, server_local.log', 'server local đang chạy ghi (sửa đổi 2026-10-13)'),
    ('app_local_t360.log, app_local_t360.err', 'được docs/T360_VIETNAMESE_SOURCE_BADGES_REPORT.md dẫn làm bằng chứng'),
    ('compute_hash.py, create_waiver.py', 'vừa sửa 2026-10-13 (phiên khác) — không đụng'),
    ('add_tasks.py, add_route.py, list_tables.py, qa_report.json, schema_places.txt, places_PL000000023255.json, monk_names_vn.json',
     'chưa chắc là nháp — để Admin quyết'),
    ('.env, config/, *.db, các file .md tài liệu gốc', 'cấu hình / dữ liệu / tài liệu'),
]


if __name__ == '__main__':
    if '--restore' in sys.argv:
        restore()
    else:
        main()
