#!/usr/bin/env python3
"""CBETA XML → SQLite Importer (Đạo Ảnh)

Usage:
  python import_cbeta.py --canon T --start-vol 51 --end-vol 51
  python import_cbeta.py --canon T
  python import_cbeta.py --file path/to/file.xml
"""

import sqlite3, xml.etree.ElementTree as ET, re, argparse, sys, os
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
CBETA_DB = str(SCRIPT_DIR / 'cbeta.db')
LINEAGE_DB = str(SCRIPT_DIR.parent / 'lineage.db')
XML_ROOT = SCRIPT_DIR / 'xml-p5a'
LOG_DIR = SCRIPT_DIR / 'logs'
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {msg}\n')
    print(f'[{ts}] {msg}')

def extract_text(el):
    return ''.join(el.itertext()).strip() if el is not None else ''

def parse_page_ref(s):
    if not s: return None, None, None
    m = re.match(r'p?(\d+)([abc])(\d*)', s)
    if m: return int(m.group(1)), m.group(2), int(m.group(3)) if m.group(3) else None
    return None, None, None

def parse_xml(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        log(f'  PARSE FAIL: {e}')
        return None, [], [], []
    tei = root
    title_el = tei.find('.//tei:titleStmt/tei:title', NS)
    author_el = tei.find('.//tei:titleStmt/tei:author', NS)
    resp_stmts = tei.findall('.//tei:respStmt', NS)
    translator = ''
    for rs in resp_stmts:
        n = rs.find('tei:name', NS)
        if n is not None and n.get('role') == 'translator':
            translator = extract_text(n)
    sigla = path.stem
    canon = sigla[0] if sigla else 'T'
    m_vol = re.match(r'[A-Z](\d+)', sigla)
    vol = int(m_vol.group(1)) if m_vol else None
    metadata = {
        'sigla': sigla, 'canon': canon, 'vol': vol,
        'title_zh': extract_text(title_el),
        'author_zh': extract_text(author_el),
        'translator_zh': translator,
        'xml_file_path': str(path.relative_to(SCRIPT_DIR)),
        'cbeta_url': f'https://cbetaonline.dila.edu.tw/zh/{sigla}'
    }
    content_list, place_mentions, person_mentions = [], [], []
    bodies = tei.findall('.//tei:body', NS)
    body = bodies[0] if bodies else tei
    divs = body.findall('.//tei:div', NS)
    if not divs:
        divs = [body]
    seen_places, seen_persons = set(), set()
    for div in divs:
        juan_el = div.find('tei:juan', NS) if div.find('tei:juan', NS) is not None else div
        juan_num = int(juan_el.get('n', 0)) if juan_el is not None else 0
        # Collect all text-bearing elements: p, head, item, lg/l
        text_elements = (juan_el.findall('.//tei:p', NS) if juan_el is not None else []) + \
                        (juan_el.findall('.//tei:head', NS) if juan_el is not None else []) + \
                        (juan_el.findall('.//tei:item', NS) if juan_el is not None else [])
        dedup = set()
        for el in text_elements:
            txt = extract_text(el).strip()
            if not txt or len(txt) < 5 or txt in dedup:
                continue
            dedup.add(txt)
            pb = el.find('.//tei:pb', NS)
            page_ref = pb.get('n') if pb is not None else None
            content_list.append({'juan': juan_num, 'page': page_ref, 'content_zh': txt})
            for pe in el.findall('.//tei:placeName', NS):
                pn = extract_text(pe)
                if pn and pn not in seen_places:
                    seen_places.add(pn)
                    place_mentions.append({
                        'place_name_zh': pn, 'dila_place_id': pe.get('key'),
                        'juan': juan_num, 'page': page_ref, 'context_snippet': txt[:200]
                    })
            for pe in el.findall('.//tei:persName', NS):
                pn = extract_text(pe)
                if pn and pn not in seen_persons:
                    seen_persons.add(pn)
                    person_mentions.append({
                        'person_name_zh': pn, 'dila_person_id': pe.get('key'),
                        'juan': juan_num, 'page': page_ref, 'context_snippet': txt[:200]
                    })
    return metadata, content_list, place_mentions, person_mentions

def get_imported(cursor):
    return set(r[0] for r in cursor.execute(
        "SELECT xml_file_path FROM cbeta_import_log WHERE status='success'").fetchall())

def run(xml_files, batch=50):
    conn = sqlite3.connect(CBETA_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS cbeta_import_log (xml_file_path TEXT PRIMARY KEY, imported_at DATETIME DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'success')")
    conn.commit()
    imported = get_imported(c)
    remaining = [f for f in xml_files if str(f.relative_to(SCRIPT_DIR)) not in imported]
    log(f'Found {len(xml_files)} XML files, {len(imported)} already imported, {len(remaining)} remaining')
    if not remaining:
        log('Nothing to import.')
        conn.close()
        return
    conn_l = sqlite3.connect(LINEAGE_DB)
    cl = conn_l.cursor()
    succ, fail = 0, 0
    for idx, xf in enumerate(remaining, 1):
        rel = str(xf.relative_to(SCRIPT_DIR))
        log(f'[{idx}/{len(remaining)}] {xf.name}')
        meta, content, places, persons = parse_xml(xf)
        if meta is None:
            c.execute("INSERT OR REPLACE INTO cbeta_import_log (xml_file_path,status) VALUES (?,?)", (rel, 'failed'))
            fail += 1
            if idx % batch == 0: conn.commit()
            continue
        try:
            c.execute("""INSERT OR REPLACE INTO cbeta_texts
                (sigla,canon,vol,title_zh,author_zh,translator_zh,juan_count,cbeta_url,xml_file_path)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (meta['sigla'], meta['canon'], meta['vol'], meta['title_zh'],
                 meta['author_zh'], meta['translator_zh'],
                 len(set(c['juan'] for c in content)), meta['cbeta_url'], meta['xml_file_path']))
            tid = c.lastrowid
            for ci in content:
                c.execute("INSERT INTO cbeta_content_index (text_id,juan,page,content_zh) VALUES (?,?,?,?)",
                          (tid, ci['juan'], ci['page'], ci['content_zh']))
            for pm in places:
                cl.execute("""INSERT INTO cbeta_place_mentions
                    (cbeta_text_sigla,dila_place_id,place_name_zh,juan,page,context_snippet)
                    VALUES (?,?,?,?,?,?)""",
                    (meta['sigla'], pm['dila_place_id'], pm['place_name_zh'],
                     pm['juan'], pm['page'], pm['context_snippet']))
            for pm in persons:
                cl.execute("""INSERT INTO cbeta_person_mentions
                    (cbeta_text_sigla,dila_person_id,person_name_zh,juan,page,context_snippet)
                    VALUES (?,?,?,?,?,?)""",
                    (meta['sigla'], pm['dila_person_id'], pm['person_name_zh'],
                     pm['juan'], pm['page'], pm['context_snippet']))
            c.execute("INSERT OR REPLACE INTO cbeta_import_log (xml_file_path,status) VALUES (?,?)", (rel, 'success'))
            succ += 1
        except Exception as e:
            log(f'  ERROR: {e}')
            c.execute("INSERT OR REPLACE INTO cbeta_import_log (xml_file_path,status) VALUES (?,?)", (rel, 'failed'))
            fail += 1
        if idx % batch == 0:
            conn.commit()
            conn_l.commit()
            log(f'  Checkpoint: {idx}/{len(remaining)}')
    conn.commit()
    conn_l.commit()
    conn.close()
    conn_l.close()
    log(f'Done: {succ} success, {fail} failed, log={log_file}')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--canon', default='T')
    ap.add_argument('--start-vol', type=int)
    ap.add_argument('--end-vol', type=int)
    ap.add_argument('--file')
    args = ap.parse_args()
    if args.file:
        files = [Path(args.file)]
    else:
        canon_dir = XML_ROOT / args.canon
        if not canon_dir.exists():
            log(f'Canon dir not found: {canon_dir}')
            sys.exit(1)
        files = []
        if args.start_vol and args.end_vol:
            for v in range(args.start_vol, args.end_vol + 1):
                vd = canon_dir / f'{args.canon}{v:02d}'
                if vd.exists(): files.extend(vd.glob('*.xml'))
        else:
            files = list(canon_dir.rglob('*.xml'))
    if not files:
        log('No XML files found')
        sys.exit(0)
    run(files)
