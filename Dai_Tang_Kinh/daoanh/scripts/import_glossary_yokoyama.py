#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_glossary_yokoyama.py
===========================
Import Yokoyama-Hirosawa 1996 glossary (Sanskrit–Tibetan–Chinese) into bảng mới `glossary_term`.

Nguồn: mbingenheimer/buddhist_studies_glossaries (CC0)
  - chinese/yokoyama-hirosawa1996.zip →
    - Yokoyama.1996.瑜伽师地论汉藏梵索引_sanTibChin.gls  (San–Tib–Chi, 93,204 entries)
    - Yokoyama.1996.瑜珈师地论漢蔵梵索引_chinOnly.gls    (Chinese index)

Cấu trúc .gls (UTF-8 text, Babylon-style):
  header bắt đầu bằng "###"; dữ liệu bắt đầu sau "### Glossary section:"
  mỗi entry = 2 dòng:
    0: headword (tiếng Phạn)
    1: definition = headword<br/>CHINESE<br/>TIBETAN_UNICODE<br/>TIBETAN_WYLIE(transliteration)
  entry cách nhau bởi dòng trống.

Bảng đích (additive — KHÔNG đụng lexicon/term_glossaries/people):
  glossary_term(
      id INTEGER PK,
      term       TEXT NOT NULL,          -- từ (Phạn / Hán / Tạng-unicode / Tạng-Latin)
      language   TEXT NOT NULL,          -- 'san' | 'zho' | 'bod' | 'bo-Latn'
      definition TEXT,                   -- nghĩa ngôn ngữ tương ứng (san→zho, zho→san, ...)
      full_text  TEXT,                   -- chuỗi đa ngôn đầy đủ (để popup hiển thị)
      source_id  INTEGER,                -- FK dataset_sources.MB_GLOSSARY (id=6)
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(term, language)
  )

Chạy (từ root daoanh):
  python scripts/import_glossary_yokoyama.py
"""
import os
import re
import sqlite3
import sys
import urllib.request
import zipfile
import io

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')
GLOSSARY_DIR = os.path.join(DATA_DIR, 'glossary')

# Nguồn tải (nếu chưa có file .gls local) — dùng để tái lập (reproducible)
YOKOYAMA_ZIP_URL = (
    'https://github.com/mbingenheimer/buddhist_studies_glossaries/raw/master/'
    'chinese/yokoyama-hirosawa1996.zip'
)


def download_gls():
    """Tải + giải nén Yoyokama .gls về data/glossary/ nếu chưa có file .gls nào."""
    if not os.path.isdir(GLOSSARY_DIR):
        os.makedirs(GLOSSARY_DIR, exist_ok=True)
    if any(f.endswith('.gls') for f in os.listdir(GLOSSARY_DIR)):
        return
    print("⏬ Chưa có file .gls — tải từ repo MB (CC0)…")
    with urllib.request.urlopen(YOKOYAMA_ZIP_URL, timeout=120) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.lower().endswith('.gls'):
                target = os.path.join(GLOSSARY_DIR, os.path.basename(name))
                with z.open(name) as src, open(target, 'wb') as dst:
                    dst.write(src.read())
                print(f"   ✓ {target}")
    print("   Đã tải xong .gls.")

MB_SOURCE = 'MB_GLOSSARY'
MB_ORIGIN_URL = 'https://github.com/mbingenheimer/buddhist_studies_glossaries'
MB_ATTRIBUTION = (
    'Yokoyama, Koitsu & Takayuki Hirosawa, Index to the Yogacarabhumi '
    '(Yogacarabhumi_Index), Tokyo: Sankibo, 1996; re-rendered into a glossary by '
    'Marcus Bingenheimer (buddhist_studies_glossaries, CC0).'
)
MB_NOTES = 'Sanskrit-Tibetan-Chinese glossary (Yogacarabhumi index). Vietnamese unvailable yet — plant: can fu ban tieng Viet.'


def ensure_source(conn):
    """Đăng ký/kiểm tra nguồn MB_GLOSSARY trong dataset_sources."""
    row = conn.execute("SELECT id FROM dataset_sources WHERE name = ?", (MB_SOURCE,)).fetchone()
    if row:
        conn.execute(
            "UPDATE dataset_sources SET origin_url = ?, attribution_text = ?, notes = ? WHERE id = ?",
            (MB_ORIGIN_URL, MB_ATTRIBUTION, MB_NOTES, row['id']),
        )
        return row['id']
    cur = conn.execute(
        "INSERT INTO dataset_sources (name, source_type, origin_url, license, usage_level, attribution_text, notes) "
        "VALUES (?, ?, ?, 'CC0', 'GREEN', ?, ?)",
        (MB_SOURCE, 'glossary', MB_ORIGIN_URL, MB_ATTRIBUTION, MB_NOTES),
    )
    return cur.lastrowid


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS glossary_term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            language TEXT NOT NULL,
            definition TEXT,
            full_text TEXT,
            source_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term, language)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_glossary_term ON glossary_term(term)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_glossary_lang ON glossary_term(language)")
    conn.commit()


def parse_gls(filepath):
    """Generator — đọc từng entry từ file .gls (zero full-file trong RAM).

    Yields (headword:str, parts:list[str]) trong đó parts = definition tách bởi <br/>.
    Bỏ qua header đến dòng '### Glossary section:'.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        in_data = False
        cur_head = None
        cur_def_lines = []
        for raw in f:
            line = raw.rstrip('\n').rstrip('\r')
            if not in_data:
                if line.startswith('### Glossary section:'):
                    in_data = True
                continue
            if line.strip() == '':
                if cur_head is not None:
                    yield cur_head, cur_def_lines
                    cur_head = None
                    cur_def_lines = []
                continue
            if cur_head is None:
                cur_head = line.strip()
            else:
                cur_def_lines = [line]
        if cur_head is not None:
            yield cur_head, cur_def_lines


def split_def(def_line):
    """Tách definition theo <br/> → list parts (term, zho, tib_unicode, tib_wylie...)."""
    return [p.strip() for p in def_line.split('<br/>')]


def rows_for_entry(head, parts):
    """Trả list (term, language, definition, full_text).

    sanTibChin: [san, zho, tib_unicode, tib_wylie]
    chinOnly:   [zho] (head = zho)
    """
    # full_text luôn là toàn bộ parts join (đa ngôn).
    full = ' | '.join(p for p in parts if p)
    out = []
    # parts[0] thường = head (san). Nếu head là tiếng Phạn (tiếng Latin), gán san.
    # Phân biệt: đầu chữ Latin (san/wylie) vs CJK (zho) vs Tibetan unicode (U+0F00-U+0FFF).
    def is_tib_uni(s):
        return bool(re.search(r'[\u0F00-\u0FFF]', s))

    def is_cjk(s):
        return bool(re.search(r'[\u4E00-\u9FFF]', s))

    def is_latin(s):
        return bool(re.search(r'[A-Za-z\u00C0-\u024F]', s)) and not is_cjk(s) and not is_tib_uni(s)

    if not parts:
        return out
    # head (dòng 0) — dùng làm gốc
    head0 = head.strip()
    if is_cjk(head0):
        out.append((head0, 'zho', parts[1] if len(parts) > 1 else '', full))
    elif is_tib_uni(head0):
        out.append((head0, 'bod', parts[1] if len(parts) > 1 else '', full))
    else:
        out.append((head0, 'san', parts[1] if len(parts) > 1 else '', full))

    # các phần còn lại: gán ngôn ngữ
    for i, p in enumerate(parts[1:], start=1):
        if not p:
            continue
        if is_cjk(p):
            out.append((p, 'zho', head0, full))
        elif is_tib_uni(p):
            out.append((p, 'bod', head0, full))
        elif is_latin(p):
            out.append((p, 'bo-Latn', head0, full))
        else:
            # phần không nhận diện: bỏ qua (thường là ký tự đặc biệt)
            pass
    return out


def main():
    download_gls()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        source_id = ensure_source(conn)
        ensure_table(conn)
        existing = {row['term'] + '|' + row['language']
                    for row in conn.execute("SELECT term, language FROM glossary_term")}
        print(f"✓ Nguồn MB_GLOSSARY id={source_id}, {len(existing)} rows đã có (skip sẽ bỏ qua nếu trùng)")

        files = sorted(os.listdir(GLOSSARY_DIR))
        gls_files = [f for f in files if f.endswith('.gls')]
        if not gls_files:
            print("❌ Không tìm thấy file .gls trong data/glossary/.")
            return
        total_new = 0
        for fname in gls_files:
            fpath = os.path.join(GLOSSARY_DIR, fname)
            n = 0
            for head, def_lines in parse_gls(fpath):
                if not def_lines:
                    continue
                parts = split_def(def_lines[0])
                for term, lang, definition, full in rows_for_entry(head, parts):
                    key = term + '|' + lang
                    if key in existing:
                        continue
                    conn.execute(
                        "INSERT INTO glossary_term (term, language, definition, full_text, source_id) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (term, lang, definition, full, source_id),
                    )
                    existing.add(key)
                    n += 1
                    if n % 5000 == 0:
                        conn.commit()
                        print(f"   ... {fname}: {n} rows ...")
            conn.commit()
            total_new += n
            print(f"✓ {fname}: +{n} rows mới")
        print(f"\n✅ HOÀN TẤT: thêm {total_new} rows vào glossary_term")
        print(f"   Tổng glossary_term hiện tại: "
              f"{conn.execute('SELECT COUNT(*) FROM glossary_term').fetchone()[0]}")
        print(f"   Theo ngôn ngữ: "
              f"{[tuple(r) for r in conn.execute('SELECT language, COUNT(*) FROM glossary_term GROUP BY language')]}")
    except Exception as e:
        print(f"❌ LỖI: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
