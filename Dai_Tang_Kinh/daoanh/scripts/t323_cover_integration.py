# -*- coding: utf-8 -*-
"""
T323+ — Sinh task phủ toàn bộ docs/integration và KIỂM PHỦ tự động.

Quy tắc phủ: mỗi file trong docs/integration (gốc, Cline/, _archive/M-series/, _archive/Uu-Tien/)
phải được nhắc tên (basename) trong ít nhất một file tasks/*.md. Script in danh sách file chưa phủ.

Chạy (ở thư mục daoanh/):
    python -X utf8 scripts/t323_cover_integration.py            # sinh task mới (không ghi đè)
    python -X utf8 scripts/t323_cover_integration.py --check    # chỉ kiểm phủ
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEG = ROOT / 'docs' / 'integration'
ARCH_M = INTEG / '_archive' / 'M-series'
ARCH_U = INTEG / '_archive' / 'Uu-Tien'
TASKS = ROOT / 'tasks'

FIRST = 323


def all_files():
    out = []
    for p in sorted(INTEG.iterdir()):
        if p.is_file():
            out.append(p)
    out += [INTEG / 'Cline' / f for f in sorted(p.name for p in (INTEG / 'Cline').iterdir())]
    out += sorted(ARCH_M.iterdir())
    out += sorted(ARCH_U.iterdir())
    return [p for p in out if p.name not in ('README.md', 'MANIFEST.tsv')]


def covered_names():
    text = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in TASKS.glob('*.md'))
    return text


def uncovered():
    text = covered_names()
    return [p for p in all_files() if p.name not in text]


# (slug, title, module, [basename...], nội dung hành động)
GROUPS = [
 ('m17-search-optimization', 'M17 — Tối ưu tìm kiếm: đối chiếu code hiện có', 'Search',
  ['M17-search-optimization.md'],
  'FTS5 (places_search_fts, lexicon_fts) và /daoanh/api/admin/search_all đã có một phần. Đối chiếu từng tiêu chí M17 (fuzzy 90%, cache 70%, top-3 80%, API 200ms) với đo thật. File T260 mà M17 tham chiếu không tồn tại: tạo lại hoặc bỏ tham chiếu.'),
 ('m136-m137-tu-si-chua-viet-nam', 'M136 + M137 — Dữ liệu tu sĩ và chùa Việt Nam: viết lại theo SQLite và cổng license', 'Lineage / VN data',
  ['M136-buddhist-temple-data-extraction-consolidated.md', 'M137-vietnamese-monk-data-extraction-consolidated.md'],
  'Hai spec đề xuất PostgreSQL/MySQL (dự án dùng SQLite) và scrape nguồn không qua cổng license. Viết một spec gộp mới: nguồn đã qua M1, ghi vào bảng có sẵn, nối T170 và T275. Không cào dữ liệu khi chưa có giấy phép.'),
 ('viphu-tu-ca-t189-t190', 'Viphu tu ca T189 + T190 — Ví dụ tra cứu Cử nhân và Tiến sĩ (5 ví dụ mỗi bên)', 'Search examples',
  ['T189-viphu-tu-ca-cuu-tri.md', 'T190-viphu-tu-ca-tri.md'],
  'Đã có kết quả thực tế cho 5 truy vấn mỗi bên (ví dụ 404 cho /daoanh/api/search). Admin xác nhận trạng thái PENDING của hai file; sau đó tạo bảng kết quả đo lại trên server hiện tại.'),
 ('viphu-tu-ca-t197-t200', 'Viphu tu ca T197–T200 — Mở rộng ví dụ 11–20', 'Search examples',
  ['T197-viphu-tu-ca-cuu-tri-moi.md', 'T198-viphu-tu-ca-tri-moi.md', 'T199-viphu-tu-ca-cuu-tri-moi.md', 'T200-viphu-tu-ca-tri-moi.md'],
  'Bốn file PENDING (Admin đã phê chuẩn hướng, chưa có nội dung đủ). Hoàn thiện nội dung tiêu chí, sau đó đo thật như T189/T190. Ghi rõ tiêu đề T199 đang ghi "16-15" (sai số), sửa thành 16–20.'),
 ('t255-canonical-reference', 'T255 — Canonical Reference Integration: hoàn tất phần còn lại', 'Canonical reference',
  ['T255-canonical-reference-integration.md'],
  'Task IN-PROGRESS từ 2026-10-02. Đối chiếu từng bước với trạng thái hiện tại, liệt kê phần đã làm, phần còn lại, và lập kế hoạch từng bước nhỏ.'),
 ('cline-audit-t253', 'Cline audit T253 — Tham chiếu person import (đã xong)', 'Person import',
  ['2026-10-06-person-import-phase0-audit.md'],
  'Đã DONE theo T253. Chỉ giữ làm tham chiếu. Kiểm lại hai blocker P0-1 và P0-2 đã được Admin chốt chưa; nếu chưa thì mở task riêng.'),
]


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def archive_groups():
    """Chia file archive chưa được nhắc ở nhóm trên thành lô 10 file (theo thứ tự tên)."""
    named = set()
    for _, _, _, names, _ in GROUPS:
        named.update(names)
    m_rest = [p.name for p in sorted(ARCH_M.iterdir()) if p.name not in named and p.name != 'README.md']
    u_rest = [p.name for p in sorted(ARCH_U.iterdir()) if p.name not in named]
    out = []
    for i, lot in enumerate(chunks(m_rest, 10), 1):
        out.append((f'arch-m-lo-{i:02d}', f'Archive M-series — lô {i:02d}: rà soát và phân loại ({len(lot)} file)', 'Archive review',
                    lot, 'Với từng file: đọc tiêu đề và mục đích; ghi nhãn GIỮ-TÍCH-HỢP (kèm module đích) / VIẾT-LẠI / XÓA-ĐỀ-XUẤT. Không xóa; chỉ ghi nhãn vào bảng trong task này.'))
    for i, lot in enumerate(chunks(u_rest, 10), 1):
        out.append((f'arch-uu-tien-lo-{i:02d}', f'Archive Uu-Tien — lô {i:02d}: rà soát và phân loại ({len(lot)} file)', 'Archive review',
                    lot, 'Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.'))
    return out


def write_task(idx, slug, title, module, names, action):
    tid = f'T{idx}'
    path = TASKS / f'{tid}-{slug}.md'
    if path.exists():
        return None
    file_list = '\n'.join(f'- `docs/integration/{n}`' if not n.startswith(('T', 'M', 'Uu', '20')) or True else '' for n in names)
    text = f'''---
id: {tid}
title: "{title}"
module: {module}
priority: p3
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phủ toàn bộ, T323+)
depends_on: []
done_when: |
  Mọi file trong danh sách được rà soát và có nhãn; Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Task chỉ đọc và ghi nhãn trong tài liệu; không xóa file, không đổi DB.
outcome: >
  2026-10-10: tạo task phủ folder docs/integration. Chưa bắt đầu.
---

# {tid} — {title}

## 1. Danh sách file phủ bởi task này

{file_list}

## 2. Việc cần làm

{action}

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
'''
    path.write_text(text, encoding='utf-8')
    return path.name


def main():
    if '--check' in sys.argv:
        miss = uncovered()
        print(f'Chưa phủ: {len(miss)} file')
        for p in miss[:50]:
            print('  -', p.relative_to(INTEG).as_posix())
        return 0 if not miss else 1
    idx = FIRST
    made = []
    for slug, title, module, names, action in GROUPS + archive_groups():
        name = write_task(idx, slug, title, module, names, action)
        if name:
            made.append(name)
        idx += 1
    print(f'Đã tạo {len(made)} task (T{FIRST}–T{idx - 1}).')
    miss = uncovered()
    print(f'Kiểm phủ sau khi tạo: còn {len(miss)} file chưa phủ.')
    for p in miss[:20]:
        print('  -', p.relative_to(INTEG).as_posix())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
