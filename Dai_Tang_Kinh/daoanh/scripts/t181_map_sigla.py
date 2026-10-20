#!/usr/bin/env python3
"""T181 P1 — Mapping sh_number → CBETA sigla từ file XML trên disk.

Quét toàn bộ data/cbeta/xml-p5a/**/*.xml, trích sigla từ tên file
(ví dụ T50n2060.xml → sigla="T50n2060", sh_number=2060, series="T"),
rồi UPDATE cbeta_catalog_vn.sigla cho các bộ khớp.

Cách dùng:
  python scripts/t181_map_sigla.py --stats
  python scripts/t181_map_sigla.py --dry-run
  python scripts/t181_map_sigla.py --apply
  python scripts/t181_map_sigla.py --verify
  python scripts/t181_map_sigla.py --revert   # đặt lại sigla=NULL
"""

import argparse, re, sqlite3, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LINEAGE_DB = str(BASE_DIR / 'data' / 'lineage.db')
XML_ROOT   = BASE_DIR / 'data' / 'cbeta' / 'xml-p5a'


def _scan_xml_files():
    """Quét tất cả *.xml trong xml-p5a/, trả list (sigla, series, sh_int)."""
    if not XML_ROOT.exists():
        print(f'[WARN] Chưa có thư mục {XML_ROOT}')
        print(f'       Chạy lệnh: git clone --depth=1 https://github.com/cbeta-git/cbeta-xml-p5a.git data/cbeta/xml-p5a')
        return []
    results = []
    for xml in XML_ROOT.rglob('*.xml'):
        stem = xml.stem  # ví dụ T50n2060, X77n1524
        m = re.match(r'^([A-Z])(\d+)n(\d+)([a-z]?)$', stem)
        if not m:
            continue
        series = m.group(1)
        sh_str = m.group(3)  # ví dụ "2060", "0474"
        sh_num_str_clean = sh_str.lstrip('0') or '0'  # bỏ leading zero
        try:
            sh_int = int(sh_num_str_clean)
        except ValueError:
            continue
        results.append((stem, series, sh_int))
    return results


def _build_mapping(xml_files):
    """Từ list (sigla, series, sh_int) → dict (series, sh_int) → sigla.
    Nếu cùng (series, sh_int) có nhiều file (ví dụ T14n0474a, T14n0474b),
    giữ cái không có hậu tố chữ cái (a-z) trước.
    """
    mapping = {}
    for sigla, series, sh_int in xml_files:
        key = (series, sh_int)
        if key not in mapping:
            mapping[key] = sigla
        else:
            # Ưu tiên sigla không có hậu tố chữ (T14n0474 > T14n0474a)
            m_cur = re.match(r'^[A-Z]\d+n\d+([a-z]?)$', mapping[key])
            m_new = re.match(r'^[A-Z]\d+n\d+([a-z]?)$', sigla)
            if m_new and not m_new.group(1) and m_cur and m_cur.group(1):
                mapping[key] = sigla
    return mapping


def run(dry_run=False, verify=False, revert=False, stats=False):
    conn = sqlite3.connect(LINEAGE_DB)
    c = conn.cursor()

    if stats:
        total = c.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]
        has_sigla = c.execute("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE sigla IS NOT NULL").fetchone()[0]
        xml_count = len(list(XML_ROOT.rglob('*.xml'))) if XML_ROOT.exists() else 0
        print(f'cbeta_catalog_vn: {total} bộ, có sigla: {has_sigla}, còn NULL: {total-has_sigla}')
        print(f'XML trên disk: {xml_count} file trong {XML_ROOT}')
        conn.close()
        return

    if revert:
        c.execute("UPDATE cbeta_catalog_vn SET sigla=NULL")
        conn.commit()
        total = c.execute("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE sigla IS NULL").fetchone()[0]
        print(f'[REVERT] Đã đặt lại sigla=NULL cho {total} bộ')
        conn.close()
        return

    if verify:
        total = c.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]
        has = c.execute("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE sigla IS NOT NULL").fetchone()[0]
        pct = has * 100 / total if total else 0
        print(f'[VERIFY] {has}/{total} bộ có sigla ({pct:.1f}%)')
        rows = c.execute("SELECT sigla, title_vi FROM cbeta_catalog_vn WHERE sigla IS NOT NULL LIMIT 10").fetchall()
        for r in rows:
            print(f'  {r[0]} → {r[1]}')
        conn.close()
        return

    xml_files = _scan_xml_files()
    if not xml_files:
        print('Không tìm thấy XML file. Chạy git clone trước.')
        conn.close()
        return

    mapping = _build_mapping(xml_files)
    print(f'[INFO] Đọc được {len(xml_files)} file XML, {len(mapping)} sigla duy nhất')

    updated = 0
    not_found = 0
    for (series, sh_int), sigla in mapping.items():
        # Tìm hàng trong catalog khớp series và sh_number (so sánh int để bỏ leading zero)
        row = c.execute(
            "SELECT id FROM cbeta_catalog_vn WHERE series=? AND CAST(sh_number AS INTEGER)=?",
            (series, sh_int)
        ).fetchone()
        if row:
            if not dry_run:
                c.execute("UPDATE cbeta_catalog_vn SET sigla=? WHERE id=?", (sigla, row[0]))
            updated += 1
        else:
            not_found += 1

    if not dry_run:
        conn.commit()
        print(f'[APPLY] Đã cập nhật sigla: {updated} bộ | Không khớp catalog: {not_found}')
    else:
        print(f'[DRY-RUN] Sẽ cập nhật: {updated} bộ | Không khớp catalog: {not_found}')

    conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='T181 P1 — map sh_number → CBETA sigla')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--stats',    action='store_true', help='Hiện thống kê nhanh')
    g.add_argument('--dry-run',  action='store_true', help='Xem sẽ update gì, không ghi DB')
    g.add_argument('--apply',    action='store_true', help='Thực sự ghi sigla vào DB')
    g.add_argument('--verify',   action='store_true', help='Kiểm tra kết quả sau --apply')
    g.add_argument('--revert',   action='store_true', help='Đặt lại sigla=NULL (rollback)')
    args = ap.parse_args()

    if not any([args.stats, args.dry_run, args.apply, args.verify, args.revert]):
        ap.print_help()
        sys.exit(0)

    run(dry_run=args.dry_run, verify=args.verify, revert=args.revert, stats=args.stats)
