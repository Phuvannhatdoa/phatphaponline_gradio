# -*- coding: utf-8 -*-
"""scripts/t229_add_undone_fields.py — thêm undone_reason/until/action cho task blocked.

Bảng Undone trên admin dashboard cần 3 trường cho mỗi task chưa xong:
  undone_reason  — tóm tắt VÌ SAO chưa Done
  undone_until   — KHI NÀO thì Done (điều kiện cụ thể, không mơ hồ)
  undone_action  — ai phải làm gì để mở khoá

Nguồn mỗi lý do đã đọc từ chính task file, không bịa.
Idempotent: chạy lại báo SKIP.
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA = {
    'tasks/T198-invalidate-soft-vs-hard.md': (
        u'invalidate_cache_for_rule và invalidate_cache_all_semantic dùng DELETE '
        u'(hard) nên mất audit trail, trong khi endpoint admin dùng '
        u"UPDATE status='invalidated' (soft). Hai hàm cùng mục đích nhưng "
        u'hành vi khác nhau; chưa chốt sẽ theo hướng nào.',
        u'Khi Admin chốt soft-vs-hard. Nếu chọn soft: ~10 dòng code + test hồi quy '
        u'thì đóng được ngay.',
        u'ADMIN quyết: giữ soft (đề xuất — xoá cứng khó truy vết lỗi dịch) '
        u'hay thêm migration/flag cho hard purge.',
    ),
    'tasks/T200-vnpa-dila-id-duplicate-limit1.md': (
        u'Build ĐÃ XONG (tie-break theo status, Admin chốt 2026-10-01, test hồi quy '
        u'deterministic, 0 DB change). Phần còn lại là quyết định gộp/tách dila_id '
        u'— đã chuyển sang T223.',
        u'Khi T223 xong. T223 lại cần L7 = 0 (13 file URI sai) và L1/L2 = 0 '
        u'(24 nhãn sai) trước, vì 11/23 file L1/L2 nằm trong chính các nhóm '
        u'dila_id trùng.',
        u'ADMIN duyệt 29 nhóm tại T223 §3 (tách 15 / gộp 3 / giữ nguyên 3 / kiểm 7).',
    ),
    'tasks/T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md': (
        u'29 nhóm / 61 row có dila_id trùng chưa quyết gộp hay tách. Đã phân loại '
        u'A/B/C/D kèm đề xuất, nhưng quyết định gộp/tách mang tính ontology '
        u'nên không tự ý làm.',
        u'Khi (a) Admin duyệt nhóm C — 7 nhóm và nhóm D — 13 nhóm, và '
        u'(b) L7/L1/L2 = 0. Hiện preflight BLOCKING 29 nên ETL chưa chạy được.',
        u'ADMIN duyệt nhóm C/D; sau đó mới áp dụng gộp/tách theo thứ tự '
        u'L7 → L1/L2 → dila_id.',
    ),
    'tasks/T27-source-neutral-entity-id.md': (
        u'Nợ kỹ thuật lớn nhất của Identity Hub: entity_id chưa source-neutral '
        u'(đang dùng mã DILA A0xxxxx). Đây là việc migrate lớn, cần chọn '
        u'thời điểm thích hợp.',
        u'Khi Admin quyết có migrate entity_id lúc này không. Nếu chưa đến hạn '
        u'thì đóng done với kết luận "deferred" thay vì để blocked mãi.',
        u'ADMIN: chọn (a) migrate bây giờ, hoặc (b) đóng deferred.',
    ),
    'tasks/T74b-claude-translate-person-bio-dila.md': (
        u'people.bio có 48.180 tiểu sử tiếng Hán từ DILA nhưng bio_vi = 0 rows — '
        u'người dùng Việt chưa đọc được tiểu sử nào. Cần chạy batch Haiku, '
        u'chưa có Admin duyệt quy mô/chi phí.',
        u'Khi Admin duyệt chạy batch cho N dòng đầu (nên thử nhỏ 200-500 dòng '
        u'để đo chất lượng trước).',
        u'ADMIN chốt số lượng + ngân sách; sau đó chạy batch và đo tỉ lệ HIT.',
    ),
}


def main():
    ok = True
    for rel, (reason, until, action) in DATA.items():
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            print('  [FAIL] không tồn tại: %s' % rel)
            ok = False
            continue
        s = io.open(p, encoding='utf-8').read()
        if 'undone_reason:' in s:
            print('  [SKIP] %-52s đã có undone_*' % os.path.basename(rel)[:52])
            continue
        m = re.search(r'^status:\s*\S+\n', s, re.M)
        if not m:
            print('  [FAIL] %s: không thấy status:' % rel)
            ok = False
            continue
        block = ('undone_reason: "%s"\n'
                 'undone_until: "%s"\n'
                 'undone_action: "%s"\n') % (reason, until, action)
        block = block.replace('"', '\\"') if False else block
        s = s[:m.end()] + block + s[m.end():]
        io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
        print('  OK  %-52s +3 trường' % os.path.basename(rel)[:52])

    print('')
    print('KẾT QUẢ:', 'OK' if ok else 'CÓ LỖI')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())