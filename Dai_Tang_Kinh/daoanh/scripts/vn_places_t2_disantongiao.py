# -*- coding: utf-8 -*-
"""T242 — Tầng 2: crawl CSDL Chùa Việt (disantongiao.vn) → raw JSON (chưa geocode).

Nguồn: https://disantongiao.vn/co-so-du-lieu-chua-viet.html
  robots.txt = `User-agent: * / Allow: /` → crawl hợp lệ.
  Bảng: cột TT (ID dạng c1…cN) + Pháp danh + Tên chùa + Địa chỉ.

Lưu ý khảo sát 07/10/2026:
  - Form lọc `cityid`/`districtid` là GET nhưng server trả về cùng bảng tĩnh
    cho mọi tổ hợp param (đã probe) → crawl bảng tĩnh trên trang entry.
  - Trang có các dòng tiêu đề nhóm Tỉnh (7 cột, Tên chùa rỗng) → bỏ qua.
  - Số lượng hiển thị trên trang là mẫu (29 dòng dữ liệu thật) — đủ để
    đáp ứng acceptance T2 raw ≥1 + ghép nguồn địa chỉ tiếng Việt thật.

Chạy:  python scripts/vn_places_t2_disantongiao.py
Output: data/vn_places_t2_disantongiao_raw.json
"""

import sys, io, os, json, time, argparse, re, html, urllib.request

if getattr(sys.stdout, 'encoding', 'utf-8').lower() != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'data', 'vn_places_t2_disantongiao_raw.json')
URL = 'https://disantongiao.vn/co-so-du-lieu-chua-viet.html'
UA = 'PTDA-BuddhistGIS-T242/1.0 (phatphaponline.org; namthien@gmail.com)'


def fetch_page(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        raise RuntimeError(f'Không tải được {url}: {e}')
    return raw


def parse_disantongiao_html(html_text):
    """Trích danh sách chùa từ bảng HTML của disantongiao.vn.

    Trả (records, skipped_province_rows). skip dòng nhóm tỉnh (Tên chùa rỗng).
    """
    records, skipped = [], 0
    tables = re.findall(r'<table[^>]*>.*?</table>', html_text, re.S | re.I)
    if not tables:
        raise RuntimeError('Không thấy <table> nào trên trang — cấu trúc đổi?')
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tables[0], re.S | re.I)
    for row in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S | re.I)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        cells = [html.unescape(c).replace('\xa0', ' ').strip() for c in cells]
        if not cells:
            continue
        tt_raw = cells[0]
        ten_chua = cells[2].strip() if len(cells) > 2 else ''
        dia_chi = cells[3].strip() if len(cells) > 3 else ''
        # Dòng tiêu đề bảng (TT / Pháp danh / Tên chùa / Địa chỉ)
        if tt_raw.lower() == 'tt' or 'tên chùa' in ten_chua.lower():
            continue
        # 7 cột + TT kiểu '31'/'36' + Tên chùa rỗng → dòng nhóm Tỉnh
        if tt_raw.isdigit() and len(cells) >= 6 and not ten_chua:
            skipped += 1
            continue
        disa_id = re.sub(r'\s+', '_', tt_raw or '').strip()
        phap_danh = cells[1].strip() if len(cells) > 1 else ''
        if not ten_chua:
            continue
        records.append({
            'source': 'disantongiao',
            'external_key': disa_id,
            'phap_danh': phap_danh,
            'ten_chua': ten_chua,
            'dia_chi': dia_chi,
            'source_url': URL,
        })
    return records, skipped


def main():
    ap = argparse.ArgumentParser(description='T242 Tầng 2 — crawl disantongiao.vn')
    ap.add_argument('--dry-run', action='store_true', help='Chỉ đếm, không ghi file')
    ap.add_argument('--output', default=OUT)
    args = ap.parse_args()

    print(f'tải {URL} ...')
    page_html = fetch_page(URL)
    records, skipped = parse_disantongiao_html(page_html)
    print(f'Chùa trích được: {len(records)} (bỏ {skipped} dòng nhóm Tỉnh)')
    if args.dry_run:
        return
    if not records:
        print('[LỖI] Không có record nào — không ghi file')
        sys.exit(1)
    for r in records[:3]:
        print('   mẫu:', r['ten_chua'], '→', r['dia_chi'])

    payload = {
        'source': 'disantongiao',
        'layer': 'T2',
        'count': len(records),
        'downloaded_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'records': records,
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f'Đã ghi {len(records)} record → {args.output}')


if __name__ == '__main__':
    main()