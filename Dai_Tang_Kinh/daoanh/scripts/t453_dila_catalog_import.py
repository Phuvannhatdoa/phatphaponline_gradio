#!/usr/bin/env python3
"""
T453 — Import DILA authority_catalog (經錄規範資料庫) + lớp dịch Việt vào lineage.db.

Additive: chỉ tạo 3 bảng mới dila_catalog_works / _contributors / _places và
1 dòng data_sources 'DILA_CATALOG'. Không sửa bảng cũ.

Ghép người/địa danh CHỈ theo DILA ID (people.id, places_dila.id), không theo tên
(ví dụ A001713: catalog 慧菀 vs people 慧苑).

Usage
-----
  python -X utf8 scripts/t453_dila_catalog_import.py --stats
  python -X utf8 scripts/t453_dila_catalog_import.py --dry-run [--canon A]
  python -X utf8 scripts/t453_dila_catalog_import.py --apply   [--canon A]
  python -X utf8 scripts/t453_dila_catalog_import.py --revert
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, 'data', 'lineage.db')
SRC_DIR = os.path.join(BASE, 'data', 'dila_import', 'authority_catalog.2026-10', 'json')
# Thư mục bản dịch do Admin chốt (Cloud session trả về); fallback thư mục session T453.
VI_DIRS = (os.path.join(BASE, 'data', 'dila_import', 'authority_catalog.2026-10', 'vn_dila_authority_catalog'),
           os.path.join(BASE, 'docs', 'sessions', '2026-10-22', 'T453'))
BACKUP_DIR = os.path.join(BASE, 'data', 'backups')
SOURCE_CODE = 'DILA_CATALOG'

# Khung triều đại dùng để nhận ra time_from/time_to chỉ là năm đầu/cuối triều đại.
DYNASTY_RANGES = {'唐': (618, 907), '宋': (960, 1279)}

# Cụm Phật học có cách đọc cố định — Cloud từng "chọn cách đọc đầu" máy móc (般若 → Ban Nhược).
TERM_READINGS = {
    '般若': ('Bát-nhã', 'Bát Nhã'), '波羅蜜': ('Ba-la-mật', 'Ba La Mật'), '三藏': ('Tam Tạng',),
    '大藏': ('Đại Tạng',), '藏經': ('Tạng Kinh',), '長部': ('Trường Bộ',), '長阿含': ('Trường A-hàm', 'Trường A Hàm'),
    '法句': ('Pháp Cú',), '涅槃': ('Niết-bàn', 'Niết Bàn'), '菩薩': ('Bồ-tát', 'Bồ Tát'),
    '比丘': ('Tỳ-kheo', 'Tỳ Kheo', 'Tỉ-khâu', 'Tỷ Khâu', 'Tỳ Khưu'), '毘奈耶': ('Tỳ-nại-da', 'Tỳ Nại Da'),
    '阿含': ('A-hàm', 'A Hàm'), '華嚴': ('Hoa Nghiêm',), '法華': ('Pháp Hoa',), '瑜伽': ('Du-già', 'Du Già'),
    '彌陀': ('Di-đà', 'Di Đà'), '念佛': ('Niệm Phật',), '經疏': ('Kinh Sớ',),
}


def _fold(s):
    """So khớp không phân biệt hoa/thường, gạch nối/khoảng trắng, và i/y (Tì = Tỳ)."""
    s = re.sub(r'[\s\-]+', ' ', (s or '').lower()).strip()
    return s.translate(str.maketrans('yỳýỷỹỵ', 'iìíỉĩị'))

SCHEMA = """
CREATE TABLE IF NOT EXISTS dila_catalog_works (
  cbeta_id TEXT PRIMARY KEY,
  authority_id TEXT UNIQUE,
  canon TEXT, vol TEXT, type TEXT, orig_category TEXT, category TEXT,
  title_zh TEXT, alt TEXT, juans INTEGER, cjk_chars INTEGER, en_words INTEGER,
  byline_zh TEXT, dynasty_zh TEXT, time_from INTEGER, time_to INTEGER, fulltext INTEGER,
  year_precision TEXT,
  title_vi TEXT, title_vi_gloss TEXT, category_vi TEXT, dynasty_vi TEXT, byline_vi TEXT,
  vi_source TEXT, vi_status TEXT, vi_json TEXT,
  raw_json TEXT, source_file TEXT, source_sha256 TEXT, imported_at TEXT
);
CREATE TABLE IF NOT EXISTS dila_catalog_contributors (
  cbeta_id TEXT, seq INTEGER, person_id TEXT, name_zh TEXT, name_vi TEXT, name_vi_src TEXT,
  role_vi TEXT, note TEXT, PRIMARY KEY (cbeta_id, seq)
);
CREATE TABLE IF NOT EXISTS dila_catalog_places (
  cbeta_id TEXT, seq INTEGER, place_id TEXT, name_zh TEXT, lat REAL, long REAL,
  PRIMARY KEY (cbeta_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_dcc_person ON dila_catalog_contributors(person_id);
CREATE INDEX IF NOT EXISTS idx_dcp_place ON dila_catalog_places(place_id);
CREATE INDEX IF NOT EXISTS idx_dcw_title_zh ON dila_catalog_works(title_zh);
CREATE INDEX IF NOT EXISTS idx_dcw_title_vi ON dila_catalog_works(title_vi);
"""
TABLES = ('dila_catalog_places', 'dila_catalog_contributors', 'dila_catalog_works')


def sha256(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def year_precision(r):
    rng = DYNASTY_RANGES.get(r.get('dynasty'))
    if r.get('time_from') is None:
        return None
    if rng and (r.get('time_from'), r.get('time_to')) == rng:
        return 'dynasty_range'
    return 'specific'


def load(canon):
    src = os.path.join(SRC_DIR, f'{canon}.json')
    with open(src, encoding='utf-8') as f:
        recs = json.load(f)
    # Một file <tạng>.vi.json, hoặc nhiều phần <tạng>.part1.vi.json, <tạng>.part2.vi.json … (tạng lớn dịch theo lô).
    vi_dir = next((d for d in VI_DIRS if glob.glob(os.path.join(d, f'{canon}.vi.json'))
                   or glob.glob(os.path.join(d, f'{canon}.part*.vi.json'))), None)
    paths = sorted(glob.glob(os.path.join(vi_dir, f'{canon}.vi.json'))
                   + glob.glob(os.path.join(vi_dir, f'{canon}.part*.vi.json'))) if vi_dir else []
    print('bản dịch:', ', '.join(os.path.relpath(p, BASE) for p in paths) or 'KHÔNG CÓ')
    vi = {}
    for p in paths:
        with open(p, encoding='utf-8') as f:
            # Bản dịch Cloud session: cùng khóa CBETA với file gốc, thêm *_vi/*_src/*_status/*_note.
            vi.update({k: v for k, v in json.load(f).items() if k in recs and isinstance(v, dict)})
    return src, recs, vi


def normalize_title_vi(title_zh, title_vi):
    """Sửa máy móc các lỗi lặp lại của bản dịch Cloud, để khỏi phải prompt lại:
    viết hoa chữ đầu mỗi từ; 疏 trong tên sách là 'Sớ' (chú giải), không phải 'Sơ'."""
    if not title_vi:
        return title_vi
    if '疏' in (title_zh or ''):
        title_vi = re.sub(r'\b[Ss]ơ\b', 'Sớ', title_vi)
    return ' '.join(w[:1].upper() + w[1:] if w else w for w in title_vi.split(' '))


def vi_fields(v):
    """Giữ lại phần lớp dịch (không lặp trường Hán gốc) để lưu vi_json."""
    keep = {k: x for k, x in v.items() if k.endswith(('_vi', '_src', '_status', '_note'))}
    keep['contributors'] = [{k: x for k, x in c.items() if k == 'id' or k.startswith('name_')}
                            for c in v.get('contributors', [])]
    return keep


def build_rows(canon, conn):
    src, recs, vi = load(canon)
    digest = sha256(src)
    now = datetime.now().isoformat(timespec='seconds')
    # Tên người: DB thắng (people.name_vi, ZQ). Tên trong bản dịch chỉ để tham khảo.
    people = {r[0]: r[1] for r in conn.execute('SELECT id, name_vi FROM people')}
    places = {r[0] for r in conn.execute('SELECT id FROM places_dila')}
    works, contribs, plcs, issues = [], [], [], []
    for cid, r in recs.items():
        v = dict(vi.get(cid, {}))
        if v.get('title_vi'):
            v['title_vi'] = normalize_title_vi(r.get('title'), v['title_vi'])
        if v and (v.get('authorityID'), v.get('title')) != (r.get('authorityID'), r.get('title')):
            issues.append(f'{cid}: authorityID/title lệch giữa file gốc và bản dịch')
        byline_vi = v.get('byline_vi')
        vc = {c.get('id'): c for c in v.get('contributors', [])}
        for c in r.get('contributors') or []:
            ref = vc.get(c.get('id'), {}).get('name_vi')
            db_name = people.get(c.get('id'))
            if byline_vi and ref and db_name and ref != db_name:
                byline_vi = byline_vi.replace(ref, db_name)
        works.append((
            cid, r.get('authorityID'), canon, r.get('vol'), r.get('type'), r.get('orig_category'),
            r.get('category'), r.get('title'), r.get('alt'), r.get('juans'), r.get('cjk_chars'),
            r.get('en_words'), r.get('byline'), r.get('dynasty'), r.get('time_from'), r.get('time_to'),
            None if r.get('fulltext') is None else int(bool(r.get('fulltext'))),
            year_precision(r),
            v.get('title_vi'), v.get('title_vi_gloss'), v.get('category_vi'), v.get('dynasty_vi'),
            byline_vi, 'cloud_session' if v else None, v.get('title_status') if v else None,
            json.dumps(vi_fields(v), ensure_ascii=False) if v else None,
            json.dumps(r, ensure_ascii=False), os.path.relpath(src, BASE).replace('\\', '/'), digest, now))
        for i, c in enumerate(r.get('contributors') or []):
            pid = c.get('id')
            if pid and pid not in people:
                issues.append(f'{cid}: person {pid} không có trong people')
            t = vc.get(pid, {})
            ref, db_name = t.get('name_vi'), people.get(pid)
            # Cloud trả 2 kiểu khóa: name_note hoặc name_vi_note.
            note = t.get('name_note') or t.get('name_vi_note')
            if ref and db_name and ref != db_name:
                note = f'Bản dịch ghi "{ref}", DB ghi "{db_name}" (dùng DB). ' + (note or '')
                issues.append(f'{cid}: {pid} bản dịch "{ref}" ≠ DB "{db_name}" → dùng DB')
            contribs.append((cid, i, pid, c.get('name'), db_name or ref,
                             'ZQLOCAL' if db_name else ('cloud_session' if ref else None),
                             None, note))
        for i, p in enumerate(r.get('places') or []):
            pid = p.get('id')
            if pid and pid not in places:
                issues.append(f'{cid}: place {pid} không có trong places_dila')
            plcs.append((cid, i, pid, p.get('name'),
                         float(p['lat']) if p.get('lat') else None,
                         float(p['long']) if p.get('long') else None))
        if not v:
            issues.append(f'{cid}: chưa có bản dịch Việt')
        else:
            # Cổng chất lượng bản dịch Cloud (lỗi đã gặp ở B: "Trường/trưởng", byline trống).
            if not v.get('title_vi'):
                issues.append(f'{cid}: QA title_vi trống')
            elif '/' in v['title_vi']:
                issues.append(f'{cid}: QA title_vi còn 2 cách đọc "{v["title_vi"]}"')
            else:
                tv = _fold(v['title_vi'])
                for zh, vi_ok in TERM_READINGS.items():
                    if zh in (r.get('title') or '') and not any(_fold(x) in tv for x in vi_ok):
                        issues.append(f'{cid}: QA {zh} phải đọc "{vi_ok[0]}" — "{v["title_vi"]}"')
            # Byline trống chỉ chấp nhận khi Cloud ghi rõ lý do (chữ cực hiếm).
            if r.get('byline') and not v.get('byline_vi') and not v.get('byline_note'):
                issues.append(f'{cid}: QA byline_vi trống ({r["byline"]})')
            for f in r:
                if f != 'contributors' and v.get(f) != r[f]:
                    issues.append(f'{cid}: QA trường gốc "{f}" bị đổi')
    return works, contribs, plcs, issues


def report(works, contribs, plcs, issues):
    print(f'works={len(works)} contributors={len(contribs)} places={len(plcs)}')
    print(f'  có title_vi: {sum(1 for w in works if w[18])}/{len(works)}')
    print(f'  contributor có name_vi: {sum(1 for c in contribs if c[4])}/{len(contribs)}')
    print(f'  year_precision: ' + ', '.join(
        f'{k}={sum(1 for w in works if w[17] == k)}' for k in ('dynasty_range', 'specific', None)))
    qa = [s for s in issues if ': QA ' in s]
    print(f'  QA bản dịch: {"ĐẠT" if not qa else f"CHƯA ĐẠT ({len(qa)} lỗi)"}')
    print(f'  issues: {len(issues)}')
    for s in issues[:30]:
        print('   -', s)
    if len(issues) > 30:
        print(f'   … và {len(issues) - 30} dòng nữa')


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for a in ('--stats', '--dry-run', '--apply', '--revert'):
        g.add_argument(a, action='store_true')
    ap.add_argument('--canon', default='A', help="A | A,B,C | ALL (mọi tạng có file bản dịch)")
    ap.add_argument('--db', default=DB_PATH)
    args = ap.parse_args()
    if args.canon.upper() == 'ALL':
        names = set()
        for d in VI_DIRS:
            for p in glob.glob(os.path.join(d, '*.vi.json')):
                names.add(os.path.basename(p).split('.')[0])
        canons = sorted(names)
    else:
        canons = [c.strip() for c in args.canon.split(',') if c.strip()]

    def build_all(conn):
        acc = ([], [], [], [])
        summary = []
        for c in canons:
            print(f'--- tạng {c}')
            part = build_rows(c, conn)
            qa = sum(1 for s in part[3] if ': QA ' in s)
            summary.append((c, len(part[0]), sum(1 for w in part[0] if w[18]), len(part[1]), len(part[2]), qa))
            for a, b in zip(acc, part):
                a.extend(b)
        print('\nTạng | bộ | có title_vi | contributors | places | lỗi QA')
        for s in summary:
            print(' | '.join(str(x) for x in s))
        return acc

    if args.stats or args.dry_run:
        conn = sqlite3.connect(f'file:{args.db}?mode=ro', uri=True)
        have = [t for t in TABLES if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone()]
        print('bảng T453 đã có:', have or 'chưa')
        for t in have:
            print(f'  {t}: {conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]}')
        if args.dry_run:
            report(*build_all(conn))
            print('DRY-RUN: không ghi gì.')
        return

    if args.revert:
        conn = sqlite3.connect(args.db)
        for t in TABLES:
            conn.execute(f'DROP TABLE IF EXISTS {t}')
        conn.execute('DELETE FROM data_sources WHERE source_code=?', (SOURCE_CODE,))
        conn.commit()
        print('REVERT xong: đã DROP', ', '.join(TABLES))
        return

    # --apply
    os.makedirs(BACKUP_DIR, exist_ok=True)
    bak = os.path.join(BACKUP_DIR, f'lineage_t453_{datetime.now():%Y%m%d_%H%M%S}.db')
    src = sqlite3.connect(args.db)
    dst = sqlite3.connect(bak)
    src.backup(dst)
    dst.close()
    print('backup:', bak)
    conn = src
    works, contribs, plcs, issues = build_all(conn)
    report(works, contribs, plcs, issues)
    if any(': QA ' in s for s in issues):
        print('DỪNG: còn lỗi QA bản dịch — không ghi DB.')
        return 1
    conn.executescript(SCHEMA)
    conn.executemany(f'INSERT OR REPLACE INTO dila_catalog_works VALUES ({",".join("?" * 30)})', works)
    conn.executemany('INSERT OR REPLACE INTO dila_catalog_contributors VALUES (?,?,?,?,?,?,?,?)', contribs)
    conn.executemany('INSERT OR REPLACE INTO dila_catalog_places VALUES (?,?,?,?,?,?)', plcs)
    if not conn.execute('SELECT 1 FROM data_sources WHERE source_code=?', (SOURCE_CODE,)).fetchone():
        conn.execute(
            "INSERT INTO data_sources (source_code, source_name, source_type, authority_scope, license_note,"
            " active, created_at, source_version, attribution_required, repository_url, legal_status,"
            " canonical_name, short_name, organization) VALUES (?,?,?,?,?,1,?,?,1,?,?,?,?,?)",
            (SOURCE_CODE, 'DILA Catalog Authority (經錄規範資料庫)', 'catalog', 'global', 'CC BY-SA 3.0',
             datetime.now().isoformat(timespec='seconds'), '2026-08-31',
             'https://github.com/DILA-edu/Authority-Databases/tree/master/authority_catalog',
             'AUDITING', 'DILA Catalog Authority', 'DILA_CAT', 'DILA (Dharma Drum)'))
    conn.commit()
    print('APPLY xong.')


if __name__ == '__main__':
    sys.exit(main())
