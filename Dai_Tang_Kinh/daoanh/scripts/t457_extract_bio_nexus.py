#!/usr/bin/env python3
"""
T457 — Trích điểm sự kiện (nexus) từ DILA biographies (高僧傳 TEI) thành file nguồn cho Cloud dịch (T458).

Chỉ đọc repo đã snapshot; KHÔNG ghi DB. Mỗi sách → <BOOK>.nexus.xml cùng định dạng đầu ra của
prompt T458 (thiếu text_vi/summary_vi/event_type — Cloud điền), để Cloud không phải tự parse TEI.

Usage
-----
  python -X utf8 scripts/t457_extract_bio_nexus.py --src <thư mục biographies-master> --out <thư mục> [--book Mingsengzhuanchao]
"""
import argparse
import glob
import os
import re
import sys
from xml.sax.saxutils import escape, quoteattr

SKIP_DIRS = {'bin', 'Schema'}
LB = re.compile(r'<lb[^>]*\bn="([^"]+)"[^>]*/>')
LINKGRP = re.compile(r'<linkGrp>(.*?)</linkGrp>', re.S)


def jd_to_year(jd):
    """Ngày Julian → năm dương lịch (lịch Julian trước 1582-10-15, Gregorian sau)."""
    if jd >= 2299161:  # 1582-10-15 Gregorian
        a = jd + 32044
        b = (4 * a + 3) // 146097
        c = a - 146097 * b // 4
    else:
        b = 0
        c = jd + 32082
    d = (4 * c + 3) // 1461
    e = c - 1461 * d // 4
    m = (5 * e + 2) // 153
    return 100 * b + d - 4800 + m // 10


def clean(fragment):
    fragment = re.sub(r'<note.*?</note>', '', fragment, flags=re.S)
    return re.sub(r'<[^>]+>', '', fragment).replace('\n', '').strip()


def names_by_key(s, tag):
    out = {}
    for m in re.finditer(rf'<{tag}[^>]*\bkey="([^"]+)"[^>]*>(.*?)</{tag}>', s, re.S):
        out.setdefault(m.group(1), clean(m.group(2)))
    return out


def extract_file(path, book):
    s = open(path, encoding='utf-8').read()
    parts = LB.split(s)
    order = parts[1::2]
    text = {n: clean(t) for n, t in zip(parts[1::2], parts[2::2])}
    pos = {n: i for i, n in enumerate(order)}
    persons = names_by_key(s, 'persName')
    places = names_by_key(s, 'placeName')
    rel = f'{book}/{os.path.basename(path)}'
    rows, problems = [], []
    for seq, m in enumerate(LINKGRP.finditer(s), 1):
        g = m.group(1)
        t = re.search(r'targets="#(\S+)\s+#(\S+)"', g)
        if not t:
            problems.append(f'{rel}#{seq}: thiếu <link targets>')
            continue
        a, b = t.groups()
        if a not in pos or b not in pos:
            problems.append(f'{rel}#{seq}: anchor {a}/{b} không có trong văn bản')
            continue
        i, j = sorted((pos[a], pos[b]))
        rows.append({
            'id': f'{rel}#{seq}', 'file': rel, 'seq': seq, 'from': a, 'to': b,
            'persons': [(p, persons.get(p, '')) for p in re.findall(r'#(A\d+)"\s+type="person"', g)],
            'places': [(p, places.get(p, '')) for p in re.findall(r'#(PL\d+)"\s+type="place"', g)],
            'times': [(int(x), int(y)) for x, y in re.findall(r'#j(\d{7})(\d{7})"\s+type="time"', g)],
            'text_zh': ''.join(text[order[k]] for k in range(i, j + 1)),
        })
    return rows, problems


def split_parts(rows, part_size):
    """Chia theo truyện (không cắt đôi một truyện), mỗi phần ~part_size nexus."""
    parts, cur, cur_file = [], [], None
    for r in rows:
        if cur and len(cur) >= part_size and r['file'] != cur_file:
            parts.append(cur)
            cur = []
        cur.append(r)
        cur_file = r['file']
    if cur:
        parts.append(cur)
    return parts


def write_book(book, rows, out_dir, commit, name=None):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'{name or book}.nexus.xml')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<bio_nexus_src source="DILA-edu/biographies" commit={quoteattr(commit)} book={quoteattr(book)} '
                f'license="CBETA CC BY-NC-SA 4.0 (văn bản) · DILA markup" count="{len(rows)}">\n')
        for r in rows:
            f.write(f'  <nexus id={quoteattr(r["id"])} file={quoteattr(r["file"])} seq="{r["seq"]}" '
                    f'from={quoteattr(r["from"])} to={quoteattr(r["to"])}>\n')
            for pid, name in r['persons']:
                f.write(f'    <person id="{pid}" name_zh={quoteattr(name)}/>\n')
            for pid, name in r['places']:
                f.write(f'    <place id="{pid}" name_zh={quoteattr(name)}/>\n')
            for jf, jt in r['times']:
                f.write(f'    <time jd_from="{jf}" jd_to="{jt}" year_from="{jd_to_year(jf)}" year_to="{jd_to_year(jt)}"/>\n')
            f.write(f'    <text_zh>{escape(r["text_zh"])}</text_zh>\n  </nexus>\n')
        f.write('</bio_nexus_src>\n')
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--book', help='chỉ một sách (vd. Mingsengzhuanchao)')
    ap.add_argument('--commit', default='4e82453')
    ap.add_argument('--part-size', type=int, default=0,
                    help='>0: sách lớn chia thành <BOOK>.partNN.nexus.xml (~N nexus, không cắt đôi truyện)')
    args = ap.parse_args()
    books = [args.book] if args.book else sorted(
        d for d in os.listdir(args.src) if os.path.isdir(os.path.join(args.src, d)) and d not in SKIP_DIRS)
    total = 0
    for book in books:
        rows, problems = [], []
        for f in sorted(glob.glob(os.path.join(args.src, book, '*.xml'))):
            r, p = extract_file(f, book)
            rows += r
            problems += p
        if args.part_size and len(rows) > args.part_size:
            parts = split_parts(rows, args.part_size)
            for k, part in enumerate(parts, 1):
                write_book(book, part, args.out, args.commit, name=f'{book}.part{k:02d}')
            path = f'{len(parts)} phần {book}.partNN.nexus.xml'
        else:
            path = write_book(book, rows, args.out, args.commit)
        total += len(rows)
        print(f'{book}: {len(rows)} nexus · có năm {sum(1 for r in rows if r["times"])} · '
              f'{sum(len(r["text_zh"]) for r in rows)} ký tự · lỗi {len(problems)} → {path}')
        for p in problems[:5]:
            print('   -', p)
    print('TỔNG nexus:', total)


if __name__ == '__main__':
    sys.exit(main())
