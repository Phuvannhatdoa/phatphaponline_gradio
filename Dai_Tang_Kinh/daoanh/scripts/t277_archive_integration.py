# -*- coding: utf-8 -*-
"""
T277 — Chuyển nhóm file bỏ/hoãn trong docs/integration vào docs/integration/_archive/.

Không xóa file. Mỗi file chuyển đi được ghi vào _archive/MANIFEST.tsv (đường dẫn cũ → mới),
để hoàn tác bằng --restore.

Usage (chạy ở thư mục daoanh/):
    python -X utf8 scripts/t277_archive_integration.py --dry-run   # chỉ đếm, không chuyển
    python -X utf8 scripts/t277_archive_integration.py --apply     # chuyển + ghi manifest
    python -X utf8 scripts/t277_archive_integration.py --restore   # đưa mọi file trong manifest về chỗ cũ
"""
import csv
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEG = ROOT / 'docs' / 'integration'
ARCH = INTEG / '_archive'
MANIFEST = ARCH / 'MANIFEST.tsv'

# Giữ tại chỗ (đang dùng hoặc là đầu vào của task đang làm)
KEEP = {
    '00_PLAN_OVERVIEW.md', 'REALITY_CHECK.md',
    'M0_nen_dev_an_toan.md', 'M1_source_hub_license_gate.md', 'M2_dong_bo_authority.md',
    'M3_dia_ly_gps_crossref.md', 'M4_doi_chieu_kinh_dien.md', 'M5_ghi_nguon_tuan_thu.md',
    'M17-search-optimization.md',
    'M136-buddhist-temple-data-extraction-consolidated.md',
    'M137-vietnamese-monk-data-extraction-consolidated.md',
    'T189-viphu-tu-ca-cuu-tri.md', 'T190-viphu-tu-ca-tri.md',
    'T197-viphu-tu-ca-cuu-tri-moi.md', 'T198-viphu-tu-ca-tri-moi.md',
    'T199-viphu-tu-ca-cuu-tri-moi.md', 'T200-viphu-tu-ca-tri-moi.md',
    'T255-canonical-reference-integration.md',
}
KEEP_DIRS = {'Cline', '_archive'}


def plan():
    """Trả về danh sách (nguồn, đích) cần chuyển."""
    moves = []
    for p in sorted(INTEG.iterdir()):
        if p.name in KEEP_DIRS:
            continue
        if p.is_dir():
            continue
        if p.name in KEEP:
            continue
        if p.name.startswith('Uu-Tien-'):
            sub = 'Uu-Tien'
        else:
            sub = 'M-series'
        moves.append((p, ARCH / sub / p.name))
    return moves


def dry_run():
    moves = plan()
    uu = sum(1 for _, d in moves if 'Uu-Tien' in d.parts)
    print(f'Sẽ chuyển: {len(moves)} file (Uu-Tien: {uu}, M-series: {len(moves) - uu})')
    print(f'Giữ tại chỗ: {len(KEEP)} file + thư mục Cline/')
    return 0


def apply():
    moves = plan()
    ARCH.mkdir(exist_ok=True)
    new = not MANIFEST.exists()
    rows = []
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            print(f'BỎ QUA (đã có đích): {dst.name}')
            continue
        shutil.move(str(src), str(dst))
        rows.append((str(src.relative_to(ROOT)).replace('\\', '/'), str(dst.relative_to(ROOT)).replace('\\', '/')))
    with MANIFEST.open('a', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        if new:
            w.writerow(['cu', 'moi'])
        w.writerows(rows)
    print(f'Đã chuyển {len(rows)} file. Manifest: {MANIFEST}')
    return 0


def restore():
    if not MANIFEST.exists():
        print('Không có manifest để khôi phục.')
        return 1
    n = 0
    with MANIFEST.open(encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            src = ROOT / row['moi']
            dst = ROOT / row['cu']
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                n += 1
    print(f'Đã khôi phục {n} file về vị trí cũ.')
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--apply' in args:
        sys.exit(apply())
    if '--restore' in args:
        sys.exit(restore())
    sys.exit(dry_run())
