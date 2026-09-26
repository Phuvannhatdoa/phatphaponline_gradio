#!/usr/bin/env python3
"""
Import Mục Lục Đại Chánh Tân Tu (Nguyễn Minh Tiến) vào cbeta_catalog_vn.
- strip ● bullets
- parse 5 lines per record (same logic as parse_muc_luc.py)
- set source/license fields
"""
import re, sqlite3, os

DOC_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/muc_luc_dtk/5-Muc-Luc-Dai-Chanh-Tan-Tu-Dai-Tang-Kinh-Nguyen-Minh-Tien-Soan.doc'
DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
TXT_FILE = '/tmp/muc_luc_catalog.txt'

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cbeta_catalog_vn (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  text_code        TEXT,
  sigla            TEXT,
  title_vi         TEXT,
  juans            INTEGER DEFAULT 1,
  dynasty_vi       TEXT,
  translator_vi    TEXT,
  note_vi          TEXT,
  q_number         TEXT,
  page             TEXT,
  sh_number        TEXT,
  title_zh         TEXT,
  juans_zh         INTEGER DEFAULT 1,
  dynasty_zh       TEXT,
  author_zh        TEXT,
  source_name       TEXT,
  source_full_title TEXT,
  source_url        TEXT,
  license_name      TEXT,
  license_url       TEXT,
  source_note       TEXT,
  created_at        TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def extract_doc():
    os.system(f'catdoc "{DOC_FILE}" 2>/dev/null > "{TXT_FILE}"')
    with open(TXT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        return [l.rstrip('\n') for l in f.readlines()]

def parse_records(lines):
    works = []
    i = 0
    cur = {}
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('● Tên kinh sách:'):
            if cur and 'title_vi' in cur:
                works.append(cur)
            title = s.replace('● Tên kinh sách:', '').strip().strip('"')
            if '(' in title and ')' not in title:
                while i + 1 < len(lines) and ')' not in lines[i + 1].strip():
                    i += 1
                    title += ' ' + lines[i].strip()
                title = title.rstrip('"')
            cur = {'title_vi': title}
        elif s.startswith('● Thông tin niên đại:') or s.startswith('● Thông tin niên đại :'):
            cur['dynasty_vi'] = s.split(':', 1)[1].strip().strip('"')
        elif s.startswith('● Tên dịch giả:') or s.startswith('● Tên dịch giả :'):
            cur['translator_vi'] = s.split(':', 1)[1].strip().strip('"')
        elif s.startswith('● Số thứ tự, trang và số hiệu:') or s.startswith('● Số thứ tự, trang và số hiệu :'):
            loc = s.split(':', 1)[1].strip().strip('"')
            cur['location_text'] = loc
            m_q = re.search(r'Q\.\s*([\d\-]+)', loc)
            m_p = re.search(r'Tr\.\s*([\d\-]+)', loc)
            m_sh = re.search(r'Sh\.\s*([\d\-]+)', loc)
            if m_q: cur['q_number'] = m_q.group(1)
            if m_p: cur['page'] = m_p.group(1)
            if m_sh: cur['sh_number'] = m_sh.group(1)
        elif s.startswith('● Tên tiếng Hoa:') or s.startswith('● Tên tiếng Hoa :'):
            raw = s.split(':', 1)[1].strip().strip('"')
            cur['title_zh'] = raw
            m_j = re.search(r'\((\d+)\s*卷\)', raw)
            if m_j: cur['juans_zh'] = int(m_j.group(1))
        i += 1
    if cur and 'title_vi' in cur:
        works.append(cur)
    return works

def clean_records(works):
    for r in works:
        tv = r.get('title_vi', '') or ''
        m_j = re.search(r'\((\d+)\s*quyển\)', tv)
        if m_j:
            r['juans'] = int(m_j.group(1))
        r['title_vi'] = re.sub(r'\s*\(\d+\s*quyển[^)]*\)', '', tv).strip()
        tr = r.get('translator_vi', '') or ''
        r['translator_vi'] = tr.replace(' dịch', '').replace(' soạn', '').replace(' thuật', '').replace(' thuyết', '').replace(' biên', '').strip()
        r['source_name'] = 'Nguyễn Minh Tiến'
        r['source_full_title'] = 'Mục lục Đại Tạng Kinh (Nguyễn Minh Tiến)'
        r['source_url'] = 'http://www.hoavouu.com'
        r['license_name'] = 'CC BY-SA 4.0 – dùng cho mục đích học thuật'
        r['license_url'] = 'https://creativecommons.org/licenses/by-sa/4.0/'
        r['source_note'] = 'Tham khảo từ sách mục lục Đại Tạng Kinh, nguồn Phật giáo Việt Nam.'
    return works

def save_to_db(records):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(SCHEMA_SQL)
    inserted = 0
    for r in records:
        conn.execute("""
            INSERT INTO cbeta_catalog_vn (
                text_code, sigla,
                title_vi, juans, dynasty_vi, translator_vi,
                q_number, page, sh_number,
                title_zh, juans_zh, dynasty_zh, author_zh,
                source_name, source_full_title, source_url,
                license_name, license_url, source_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r.get('text_code'), r.get('sigla'),
            r.get('title_vi'), r.get('juans', 1), r.get('dynasty_vi'), r.get('translator_vi'),
            r.get('q_number'), r.get('page'), r.get('sh_number'),
            r.get('title_zh'), r.get('juans_zh', 1),
            r.get('dynasty_zh'), r.get('author_zh'),
            r.get('source_name'), r.get('source_full_title'), r.get('source_url'),
            r.get('license_name'), r.get('license_url'), r.get('source_note')
        ))
        inserted += 1
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]
    conn.close()
    return count, inserted

def main():
    print("=" * 60)
    print("Import Mục Lục Đại Chánh Tân Tu → cbeta_catalog_vn")
    print("=" * 60)
    lines = extract_doc()
    print(f"Extracted {len(lines)} lines from .doc")
    records = parse_records(lines)
    print(f"Parsed {len(records)} records")
    records = clean_records(records)
    total, inserted = save_to_db(records)
    print(f"\n✅ Saved {inserted} records to cbeta_catalog_vn")
    print(f"   Total in table: {total}")
    return inserted

if __name__ == '__main__':
    main()
