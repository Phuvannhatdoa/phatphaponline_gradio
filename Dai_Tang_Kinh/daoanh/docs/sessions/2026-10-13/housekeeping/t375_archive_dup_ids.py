"""T375 — chuyển bản cũ bị hồi sinh (trùng task ID) vào _archive/2026-10-13-dup-ids/ + MANIFEST.

Chạy từ thư mục daoanh/:  python -X utf8 docs/sessions/2026-10-13/housekeeping/t375_archive_dup_ids.py [--restore]
--restore: chuyển ngược theo danh sách PAIRS (khi chưa commit; đã commit thì dùng git revert).
"""
import hashlib
import io
import os
import shutil
import sys

ARCHIVE = '_archive/2026-10-13-dup-ids'

# (ID, bản cũ bị hồi sinh -> lưu trữ, bản hiện hành được giữ)
PAIRS = [
    ('T158', 'tasks/T158-glossary-resolver-pre-translation-lookup.md', 'tasks/T218-glossary-resolver-pre-translation-lookup.md'),
    ('T206', 'tasks/T206-pl-corrupt-canonical-name-vi-fix.md', 'tasks/T219-pl-corrupt-canonical-name-vi-fix.md'),
    ('T215', 'tasks/T215-vnpa-dila-id-recovery.md', 'tasks/X-T220-vnpa-dila-id-recovery.md'),
    ('T215', 'docs/Mimo-Flash/T215-VNPA-DILA-ID-RECOVERY-01.md', 'docs/Mimo-Flash/X-T220-VNPA-DILA-ID-RECOVERY-01.md'),
    ('T168', 'docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md', 'docs/Mimo-Flash/X-T168-rule-resolver-context-compiler-PLAN.md'),
    ('T169', 'docs/Mimo-Flash/T169-groq-place-verify-pipeline.md', 'docs/Mimo-Flash/X-T169-groq-place-verify-pipeline.md'),
    ('T169', 'docs/Mimo-Flash/T169-groq-place-verify-pipeline-SPEC.md', 'docs/Mimo-Flash/X-T169-groq-place-verify-pipeline-SPEC.md'),
    ('T170', 'docs/Mimo-Flash/XX-T170-dila-place-person-v41-verify.md', 'docs/Mimo-Flash/X-T170-dila-place-person-v41-verify.md'),
    ('T170', 'docs/Mimo-Flash/XX-T170-dila-place-person-v41-verify-SPEC.md', 'docs/Mimo-Flash/X-T170-dila-place-person-v41-verify-SPEC.md'),
    ('T171', 'docs/Mimo-Flash/T171-person-name-standard.md', 'docs/Mimo-Flash/X-T171-person-name-standard.md'),
    ('T171', 'docs/Mimo-Flash/T171-person-name-standard-SPEC.md', 'docs/Mimo-Flash/X-T171-person-name-standard-SPEC.md'),
    ('T177', 'docs/Mimo-Flash/T177-directive-v2-trie-xml-dualhash-REVIEW.md', 'docs/Mimo-Flash/X-T177-directive-v2-trie-xml-dualhash-REVIEW.md'),
    ('T177', 'docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md', 'docs/Mimo-Flash/X-T177-dynamic-filter-absorb-directive-v2.md'),
]


def sha16(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def archived(src):
    return ARCHIVE + '/' + src


def restore():
    for _tid, src, _keep in PAIRS:
        dst = archived(src)
        if os.path.isfile(dst) and not os.path.exists(src):
            shutil.move(dst, src)
            print('restored', src)


def main():
    for _tid, src, keep in PAIRS:
        if not os.path.isfile(src):
            sys.exit('thiếu file nguồn: ' + src)
        if not os.path.isfile(keep):
            sys.exit('thiếu bản hiện hành: ' + keep)
    rows = []
    for tid, src, keep in PAIRS:
        dst = archived(src)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        h = sha16(src)
        shutil.move(src, dst)
        if sha16(dst) != h:
            sys.exit('hash lệch sau khi chuyển: ' + dst)
        rows.append((tid, src, dst, keep, h))
    out = io.StringIO()
    out.write('# MANIFEST — T375 gỡ task ID trùng (2026-10-13)\n\n')
    out.write('Các file dưới đây là **bản cũ bị hồi sinh** của file đã được đổi số / đổi tên `X-` trong đợt T222\n')
    out.write('(2026-10-02, `docs/Handoff-2026-10-02-T222-id-hygiene.md`). Bản giữ lại (cột "Bản hiện hành") có nội dung\n')
    out.write('mới hơn (`former_ids`, status/updated mới hơn, các sửa đổi T188/T189/T190). Không xoá — chỉ chuyển vào đây.\n\n')
    out.write('Khôi phục: `python -X utf8 docs/sessions/2026-10-13/housekeeping/t375_archive_dup_ids.py --restore`\n')
    out.write('(trước khi commit) hoặc `git revert --no-edit <sha_T375>` (sau khi commit).\n\n')
    out.write('| ID | Đường dẫn gốc | Đường dẫn lưu trữ | Bản hiện hành (giữ) | sha256[:16] |\n')
    out.write('|---|---|---|---|---|\n')
    for r in rows:
        out.write('| %s | `%s` | `%s` | `%s` | `%s` |\n' % r)
    with open(ARCHIVE + '/MANIFEST.md', 'w', encoding='utf-8', newline='\n') as f:
        f.write(out.getvalue())
    print(len(rows), 'file đã chuyển vào', ARCHIVE)


if __name__ == '__main__':
    if '--restore' in sys.argv:
        restore()
    else:
        main()
