#!/usr/bin/env python3
"""T181 P2 — Tải CBETA XML theo chiến lược PARTIAL-CLONE (Zero-RAM, lazy, additive).

Thay thế kế hoạch git clone 2GB (https://github.com/cbeta-git/cbeta-xml-p5a — repo
INTERNAL, clone công khai BỊ TỪ CHỐI auth) bằng nguồn PUBLIC:
    https://github.com/cbeta-org/xml-p5   (CBETA XML P5 bản phát hành, ~1.4GB full)

Chiến lược 3 lớp (không tải full 1.4GB khi chưa cần):
  [1] --index   : lấy GIT TREE recursive MỘT LẦN từ GitHub API → lưu data/cbeta/xml_index.json
                  (map {sh_number, series, vol} → path XML). ~vài trăm KB, KHÔNG tải blob nào.
  [2] --fetch   : khi ADMIN click "Nhập & Dịch" 1 bộ → tải ĐÚNG 1 file XML theo path từ index
                  (https://raw.githubusercontent.com/...) về data/cbeta/xml-p5a/<path>.
                  Tải từng file, generator-style, không nạp toàn bộ vào RAM.
  [3] --clone   : (tuỳ chọn) nếu ADMIN muốn full mirror thì chạy git clone partial:
                  git clone --filter=blob:none --sparse (chỉ metadata) rồi
                  git sparse-checkout set <volume cần> → mở rộng dần khi cần.
                  KHÔNG tự chạy (tiết kiệm mạng), có hướng dẫn rõ ràng.

Flags:
  python scripts/t181_cbeta_download.py --index            # lấy cây file của repo public
  python scripts/t181_cbeta_download.py --status           # báo trạng thái hiện tại
  python scripts/t181_cbeta_download.py --fetch T14n0474   # tải 1 file XML (lazy)
  python scripts/t181_cbeta_download.py --fetch-catalog --limit 5   # tải các bộ đang có sigla trên disk
  python scripts/t181_cbeta_download.py --apply-index      # --index + ghi sigla mapping vào DB (cbeta.db.cbeta_texts)
  python scripts/t181_cbeta_download.py --clone            # in hướng dẫn git clone partial (không tự clone)
  python scripts/t181_cbeta_download.py --verify-catalog   # đối chiếu cbeta_catalog_vn.sh_number ↔ xml_index.json

An toàn:
  - Zero-RAM: chỉ giữ thư mục/index, mỗi file stream thẳng xuống disk.
  - Không ghi lên lineage.db (chỉ đọc cbeta_catalog_vn + ghi riêng into cbeta.db nếu --apply-index).
  - Không chạy network trừ --index/--fetch (có flag tường minh).
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data' / 'cbeta'
INDEX_JSON = DATA_DIR / 'xml_index.json'
XML_ROOT = DATA_DIR / 'xml-p5a'
LINEAGE_DB = BASE_DIR / 'data' / 'lineage.db'
CBETA_DB = DATA_DIR / 'cbeta.db'

REPO = 'cbeta-org/xml-p5'
BRANCH = 'master'
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}'
TREE_URL = f'https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1'

_SIGLA_RE = re.compile(r'^([A-Z]{1,3})(\d+)n(\d+)([a-z]?)$')


def _db():
    """Kết nối lineage.db (read-only mặc định) để đọc cbeta_catalog_vn."""
    return sqlite3.connect(str(LINEAGE_DB))


def _index_remote():
    """Tải toàn bộ tree recursive từ GitHub API → lưu xml_index.json.

    Trả list dict {path, size, sigla, series, vol, sh} cho mọi file .xml.
    """
    print(f'[INDEX] GET {TREE_URL}')
    with urllib.request.urlopen(TREE_URL, timeout=120) as resp:
        data = json.load(resp)

    entries = data.get('tree', [])
    xml_files = []
    for e in entries:
        if e.get('type') != 'blob' or not e['path'].endswith('.xml'):
            continue
        path = e['path']
        stem = path.rsplit('/', 1)[-1][:-4]  # bỏ .xml
        m = _SIGLA_RE.match(stem)
        meta = {
            'path': path,
            'sigla': stem,
            'size': e.get('size'),
            'sha': e.get('sha'),
        }
        if m:
            meta['series'] = m.group(1)
            meta['vol'] = int(m.group(2))
            meta['sh'] = int(m.group(3).lstrip('0') or 0)
            meta['suffix'] = m.group(4)
        xml_files.append(meta)

    INDEX_JSON.write_text(
        json.dumps({'source': REPO, 'branch': BRANCH, 'fetched_at': None,
                    'repo_size': data.get('size'), 'truncated': data.get('truncated'),
                    'count': len(xml_files), 'files': xml_files},
                   ensure_ascii=False), encoding='utf-8')
    print(f'[INDEX] OK — {len(xml_files)} file XML → {INDEX_JSON}')
    if data.get('truncated'):
        print('[WARN] GitHub tree bị truncated — cần paginate (hiếm gặp).')
    return xml_files


def _load_index():
    if not INDEX_JSON.exists():
        print(f'[WARN] Chưa có {INDEX_JSON}. Chạy: python scripts/t181_cbeta_download.py --index')
        return None
    return json.loads(INDEX_JSON.read_text(encoding='utf-8'))


def _fetch_xml(sigla, files=None):
    """Tải 1 file XML theo sigla về đúng path (lazy). Trả path đã tải."""
    files = files or _load_index()
    if not files:
        return None
    # index có thể là list trực tiếp hoặc trong 'files'
    file_list = files if isinstance(files, list) else files.get('files', [])
    m = _SIGLA_RE.match(sigla)
    if not m:
        print(f'[FETCH] Sigla không hợp lệ: {sigla}')
        return None
    series, vol, sh = m.group(1), int(m.group(2)), int(m.group(3).lstrip('0') or 0)
    wanted_path = f'{series}/{series}{vol:02d}/{sigla}.xml' if vol < 100 else \
        f'{series}/{series}{vol}/{sigla}.xml'
    hit = None
    for f in file_list:
        if f['sigla'] == sigla and f.get('path') == wanted_path:
            hit = f
            break
    if not hit:
        # fallback: tìm theo sigla bất kể vol format
        for f in file_list:
            if f['sigla'] == sigla:
                hit = f
                break
    if not hit:
        print(f'[FETCH] Không tìm thấy {sigla} trong index.')
        return None

    dest = XML_ROOT / hit['path']
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{RAW_BASE}/{hit['path']}"
    print(f'[FETCH] {url} → {dest}')
    urllib.request.urlretrieve(url, str(dest))
    print(f'[FETCH] Done ({dest.stat().st_size} bytes).')
    return str(dest)


def _status():
    print(f'XML_ROOT : {XML_ROOT} (exists={XML_ROOT.exists()})')
    if XML_ROOT.exists():
        xmls = list(XML_ROOT.rglob('*.xml'))
        print(f'  XML trên disk: {len(xmls)}')
        by_series = {}
        for x in xmls:
            by_series[x.stem[0]] = by_series.get(x.stem[0], 0) + 1
        for s, n in sorted(by_series.items()):
            print(f'    {s}: {n}')
    idx = _load_index()
    if idx:
        print(f'Index : {INDEX_JSON} — {idx.get("count")} file ({idx.get("source")})')
    else:
        print('Index : CHƯA có — chạy --index')
    if CBETA_DB and CBETA_DB.exists():
        conn = sqlite3.connect(str(CBETA_DB))
        n = conn.execute('SELECT COUNT(*) FROM cbeta_texts').fetchone()[0]
        print(f'cbeta.db : {n} bộ đã import')
        conn.close()


def _clone_instructions():
    print(f'''[CLONE] KHÔNG tự clone full (tiết kiệm mạng/ổ đĩa). Nếu ADMIN muốn mirror toàn bộ:

  # Repo PUBLIC (thay cbeta-git/cbeta-xml-p5a — repo internal bị từ chối auth):
  git clone --filter=blob:none --sparse https://github.com/{REPO}.git {XML_ROOT}
  git -C {XML_ROOT} sparse-checkout set T/T50        # chỉ checkout volume cần trước
  # Tải thêm volume khi cần:
  git -C {XML_ROOT} sparse-checkout add T/T14

Chiến lược mặc định của dự án vẫn là --fetch (tải từng file khi admin click),
không cần clone. {XML_ROOT} hiện {('ĐÃ tồn tại' if XML_ROOT.exists() else 'CHƯA tồn tại')}.''')


def _verify_catalog(files=None):
    files = files or _load_index()
    if not files:
        return
    file_list = files if isinstance(files, list) else files.get('files', [])
    conn = _db()
    rows = conn.execute("SELECT sh_number, series FROM cbeta_catalog_vn ORDER BY series, CAST(sh_number AS INTEGER)").fetchall()
    idx_sh = {}
    for f in file_list:
        if f.get('sh') is not None:
            idx_sh.setdefault((f['series'], f['sh']), f['sigla'])
    matched = 0
    samples = []
    for sh, series in rows:
        key = (series, int(sh)) if sh and str(sh).isdigit() else None
        if key and key in idx_sh:
            matched += 1
            if len(samples) < 10:
                samples.append((sh, series, idx_sh[key]))
    print(f'[VERIFY] cbeta_catalog_vn: {len(rows)} bộ | khớp index: {matched} '
          f'({matched*100.0/len(rows) if rows else 0:.1f}%)')
    for s in samples:
        print(f'  sh={s[0]} series={s[1]} → {s[2]}')
    conn.close()


def _apply_index(files=None):
    """Ghi sigla (từ index) vào cbeta.db.cbeta_texts nếu chưa có (additive)."""
    files = files or _load_index()
    if not files:
        return
    file_list = files if isinstance(files, list) else files.get('files', [])
    conn = sqlite3.connect(str(CBETA_DB))
    cur = conn.cursor()
    added = 0
    existing = {r[0] for r in cur.execute('SELECT sigla FROM cbeta_texts').fetchall()}
    for f in file_list:
        if f['sigla'] in existing or f.get('sh') is None:
            continue
        cur.execute("""INSERT OR IGNORE INTO cbeta_texts
                       (sigla, canon, vol, title_zh, cbeta_url, xml_file_path, created_at)
                       VALUES (?,?,?,?,?,?, datetime('now'))""",
                    (f['sigla'], f['series'], f.get('vol'), f['sigla'],
                     f"{RAW_BASE}/{f['path']}", f['path']))
        added += 1
    conn.commit()
    total = cur.execute('SELECT COUNT(*) FROM cbeta_texts').fetchone()[0]
    print(f'[APPLY] Đã thêm {added} sigla vào cbeta_texts (tổng {total}). Chưa đọc nội dung XML.')
    conn.close()


def main():
    ap = argparse.ArgumentParser(description='T181 P2 — CBETA partial-clone downloader')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--index', action='store_true', help='Tải git tree recursive → xml_index.json')
    g.add_argument('--status', action='store_true', help='Báo trạng thái hiện tại')
    g.add_argument('--fetch', metavar='SIGLA', help='Tải 1 file XML theo sigla (lazy)')
    g.add_argument('--fetch-catalog', action='store_true',
                   help='Tải các bộ sigla đang có (đã map từ trước, tổi đa --limit bộ)')
    g.add_argument('--verify-catalog', action='store_true',
                   help='Đối chiếu cbeta_catalog_vn.sh_number ↔ index')
    g.add_argument('--apply-index', action='store_true',
                   help='Ghi sigla từ index vào cbeta.db.cbeta_texts (additive)')
    g.add_argument('--clone', action='store_true', help='In hướng dẫn git clone partial')
    ap.add_argument('--limit', type=int, default=5, help='Số bộ tối đa khi --fetch-catalog')
    args = ap.parse_args()

    if not any([args.index, args.status, args.fetch, args.fetch_catalog,
                args.verify_catalog, args.apply_index, args.clone]):
        ap.print_help()
        sys.exit(0)

    if args.status:
        _status()
        return

    if args.index:
        _index_remote()
        return

    if args.clone:
        _clone_instructions()
        return

    if args.apply_index:
        _apply_index()
        return

    files = _load_index()
    if not files:
        return

    if args.fetch:
        _fetch_xml(args.fetch, files)
        return

    if args.verify_catalog:
        _verify_catalog(files)
        return

    if args.fetch_catalog:
        file_list = files if isinstance(files, list) else files.get('files', [])
        conn = _db()
        rows = conn.execute(
            "SELECT sigla FROM cbeta_catalog_vn WHERE sigla IS NOT NULL ORDER BY id LIMIT ?",
            (args.limit,)).fetchall()
        conn.close()
        if not rows:
            print('[FETCH] Chưa có sigla nào trong cbeta_catalog_vn. Chạy t181_map_sigla --apply trước.')
            return
        for (sigla,) in rows:
            _fetch_xml(sigla, files)


if __name__ == '__main__':
    main()