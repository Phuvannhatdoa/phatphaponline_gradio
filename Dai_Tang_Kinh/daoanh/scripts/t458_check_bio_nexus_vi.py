#!/usr/bin/env python3
"""
T458 — QA bản dịch Cloud của điểm sự kiện Cao Tăng Truyện (chỉ đọc, không ghi DB).

So từng <NAME>.vi.xml trong vn_bio_nexus/ với <NAME>.nexus.xml nguồn (nexus_src_parts/ hoặc nexus_src/):
số nexus, id/thuộc tính, person/place/time, text_zh giống hệt; text_vi/summary_vi không trống, không "/";
event_type hợp lệ; text_vi không còn quá nhiều chữ Hán. In vài mẫu để Admin đọc chất lượng.

Usage
-----
  python -X utf8 scripts/t458_check_bio_nexus_vi.py [--name Mingsengzhuanchao] [--samples 8]
"""
import argparse
import glob
import os
import random
import re
import sys
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, 'data', 'dila_import', 'biographies.2024-01')
SRC_DIRS = [os.path.join(ROOT, 'nexus_src_parts'), os.path.join(ROOT, 'nexus_src')]
VI_DIR = os.path.join(ROOT, 'vn_bio_nexus')
EVENT_TYPES = {'birth', 'origin', 'ordination', 'study', 'teaching', 'translation', 'residence', 'travel',
               'imperial', 'meeting', 'miracle', 'writing', 'death', 'other'}
HAN = re.compile(r'[㐀-鿿\U00020000-\U0002ffff]')


def sig(n):
    """Phần không được đổi của một <nexus>: thuộc tính, person/place/time, text_zh."""
    return (tuple(sorted(n.attrib.items())),
            tuple((e.tag, tuple(sorted(e.attrib.items()))) for e in n if e.tag in ('person', 'place', 'time')),
            (n.findtext('text_zh') or ''))


def check(name, samples):
    vi_path = os.path.join(VI_DIR, f'{name}.vi.xml')
    src_path = next((p for p in (os.path.join(d, f'{name}.nexus.xml') for d in SRC_DIRS) if os.path.exists(p)), None)
    errs = []
    if not src_path:
        return [f'{name}: không tìm thấy file nguồn .nexus.xml'], 0
    try:
        vi_root = ET.parse(vi_path).getroot()
    except ET.ParseError as e:
        return [f'{name}: XML lỗi — {e}'], 0
    src = ET.parse(src_path).getroot().findall('nexus')
    vi = vi_root.findall('nexus')
    if len(src) != len(vi):
        errs.append(f'{name}: số nexus nguồn {len(src)} ≠ bản dịch {len(vi)}')
    vmap = {n.get('id'): n for n in vi}
    for s in src:
        v = vmap.get(s.get('id'))
        if v is None:
            errs.append(f'{s.get("id")}: thiếu trong bản dịch')
            continue
        if sig(s) != sig(v):
            errs.append(f'{s.get("id")}: thuộc tính / person / place / time / text_zh bị đổi')
        tv, sv, et = (v.findtext('text_vi') or '').strip(), (v.findtext('summary_vi') or '').strip(), (v.findtext('event_type') or '').strip()
        if not tv:
            errs.append(f'{s.get("id")}: text_vi trống')
        if not sv:
            errs.append(f'{s.get("id")}: summary_vi trống')
        if '/' in tv or '/' in sv:
            errs.append(f'{s.get("id")}: có "/" trong bản dịch')
        if et not in EVENT_TYPES:
            errs.append(f'{s.get("id")}: event_type "{et}" không hợp lệ')
        han = len(HAN.findall(tv))
        if tv and han > 3 and v.find('note') is None:
            errs.append(f'{s.get("id")}: text_vi còn {han} chữ Hán mà không có <note>')
    print(f'== {name}: nguồn {len(src)} · dịch {len(vi)} · lỗi {len(errs)} · license={vi_root.get("license")}')
    for n in random.Random(1).sample(vi, min(samples, len(vi))):
        print(f'\n[{n.get("id")}] ({n.findtext("event_type")})')
        print('  ZH :', (n.findtext('text_zh') or '')[:160])
        print('  VI :', (n.findtext('text_vi') or '')[:300])
        print('  TÓM:', n.findtext('summary_vi'))
    return errs, len(vi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', help='vd. Mingsengzhuanchao hoặc Song_GSZ.part03; bỏ trống = mọi file trong vn_bio_nexus/')
    ap.add_argument('--samples', type=int, default=5)
    args = ap.parse_args()
    names = [args.name] if args.name else sorted(
        os.path.basename(p)[:-len('.vi.xml')] for p in glob.glob(os.path.join(VI_DIR, '*.vi.xml')))
    if not names:
        print('Chưa có file .vi.xml trong', VI_DIR)
        return 1
    total_err = total = 0
    for nm in names:
        errs, n = check(nm, args.samples)
        total += n
        total_err += len(errs)
        for e in errs[:20]:
            print('   -', e)
    print(f'\nTỔNG: {len(names)} file · {total} nexus · lỗi {total_err} → QA {"ĐẠT" if not total_err else "CHƯA ĐẠT"}')
    return 0 if not total_err else 1


if __name__ == '__main__':
    sys.exit(main())
