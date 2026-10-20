#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T110 (Zero-ALTER · Zero-RAM · Lean) — Glossary Vietnamese Pipeline
=======================================================================
Việt hóa `glossary_term` (Yokoyama 1996, 248,095 row) bằng CÁC TỪ ĐIỂN SẴN CÓ
(no bulk LLM — trung thực, deterministic, rẻ, tái kiểm được).

Tính chất (tuân điều lệnh check07)
-----------------------------------
- ZERO-ALTER: KHÔNG DROP/ALTER bảng gốc (glossary_term/lexicon/...). Chỉ tạo bảng
  DẪN XUẤT mới `glossary_vi` (mirror đầy đủ mọi row + cột Việt hóa). Revert = 1 lệnh
  DROP bảng dẫn xuất.
- Zero-RAM: duyệt glossary_term/lexicon theo chunk (fetchmany) — không bao giờ nạp
  248,095 row cùng lúc. Dict ánh xạ ký tự Hán→HV chỉ ~11k (nhỏ).
- DETERMINISTIC: cùng dữ liệu → cùng output (idempotent, INSERT OR REPLACE theo PK).

Đường Việt hóa (3 pha, ưu tiên chất lượng cao nhất)
---------------------------------------------------
- Pass 0 — MIRROR    : sao toàn bộ glm_vocabulary row vào `glossary_vi` (term_vi=NULL,
  để metric coverage đo được = COUNT(term_vi)/COUNT(*)).
- Pass A — EXACT-DICT: match NGUYÊN chuỗi term Hán (zho) với từ điển theo ưu tiên:
      1) doctrine_concept.name_zh→name_vi   (12 thuật ngữ cốt lõi)
      2) data/glossaries/vi-buddhist.json   (13 thuật ngữ style-lock)
      3) lexicon (166k, nguồn "Phat Hoc - Chua Van Hanh - Phap") — Hán trích từ
         definition (chuỗi CJK cuối, dài ≥2 ký tự) → term_vi
      4) namevi_map_places.name_zh→name_vi   (địa danh)
      5) name_vi_map.name_zh→name_vi         (nhân danh — done_when yêu cầu tái dùng)
    → match_type='exact_dict', vi_confidence=1.0.
- Pass B — CHAR-HV    : các term zho chưa match → phiên âm Hán-Việt TỪNG KÝ TỰ
  (custom_hanviet_override + hanviet_fallback, ~11k ký tự). Ký tự chưa biết giữ nguyên.
  → match_type='char_hv', vi_confidence = tỉ lệ ký tự tìm được (minh bạch).
    Bỏ qua nếu confidence=0 (không phiên được) — trung thực, không bịa.
- Pass C — VIA-SIBLING: row san/bod/bo-Latn KHÔNG có Việt trực tiếp → kế thừa term_vi
  của row zho CÙNG full_text (cùng khái niệm) → match_type='via_zho_sibling'.

Metric compliance
-----------------
  glossary_vi_coverage = COUNT(term_vi IS NOT NULL) / COUNT(*)  (per language + global)
  Lưu trong bảng dẫn xuất; báo cáo ở cuối `--apply`.

Cách dùng
---------
    python scripts/etl_t110_glossary_vi.py --dry-run   # kế hoạch + ước lượng
    python scripts/etl_t110_glossary_vi.py --apply     # tạo bảng + 3 pha (có backup)
    python scripts/etl_t110_glossary_vi.py --revert    # DROP bảng dẫn xuất (giữ backup)

API (app.py) sau khi ETL: /daoanh/api/glossary?term=... sẽ trả thêm `term_vi`.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')
VI_BUDDHIST_JSON = os.path.join(BASE_DIR, 'data', 'glossaries', 'vi-buddhist.json')

TS = time.strftime('%Y%m%d_%H%M%S')
BUILT_AT = time.strftime('%Y-%m-%dT%H:%M:%S')

CJK = re.compile(r'[\u4e00-\u9fff]')
CJK_RUN = re.compile(r'[\u4e00-\u9fff]{2,}')  # chuỗi Hán dài >=2 (chống nhiễu ký tự đơn)
JUNK_VI = re.compile(r'^[0-9(\[]')  # term_vi nghi là prose → loại

CREATE_GLOSSARY_VI = """
CREATE TABLE IF NOT EXISTS glossary_vi (
    glossary_id        INTEGER PRIMARY KEY,
    term               TEXT NOT NULL,
    language           TEXT NOT NULL,
    term_vi            TEXT,
    match_type         TEXT,
    match_source       TEXT,
    vi_confidence      REAL,
    source_glossary_id INTEGER,
    created_at         TEXT
)
"""


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f'lineage_t110_{TS}.db')
    if not os.path.exists(DB_PATH):
        print(f'[backup] KHÔNG tìm thấy {DB_PATH} — bỏ qua backup')
        return None
    src = sqlite3.connect(DB_PATH, timeout=60)
    try:
        dest = sqlite3.connect(dst, timeout=60)
        try:
            src.backup(dest)
        finally:
            dest.close()
    finally:
        src.close()
    print(f'[backup] Đã backup → {dst} ({os.path.getsize(dst):,} bytes)')
    return dst


def load_charhv(conn):
    """~11k ký tự Hán → âm Hán-Việt (override ưu tiên hơn fallback)."""
    override = {r['char']: r['hanviet'] for r in
                conn.execute('SELECT char, hanviet FROM custom_hanviet_override')}
    fallback = {r['ch']: r['hv'] for r in
                conn.execute('SELECT ch, hv FROM hanviet_fallback')}
    for c, v in fallback.items():
        override.setdefault(c, v)
    print(f'[charhv] {len(override)} ký tự Hán→HV (override ưu tiên hơn fallback)')
    return override


def extract_lexicon_pairs(conn):
    """Trích (han, vi) từ lexicon lang='vi': chuỗi CJK CUỐI trong definition, dài >=2.

    Filter chống nhiễu: term_vi KHÔNG bắt đầu bằng số/'('/'[' và dài <= 60.
    Zero-RAM: duyệt chunk fetchmany.
    """
    pairs = {}
    cur = conn.execute(
        "SELECT term, definition FROM lexicon WHERE lang='vi' ORDER BY id")
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            vi = (r['term'] or '').strip()
            if not vi or len(vi) > 60 or JUNK_VI.match(vi):
                continue
            runs = CJK_RUN.findall(r['definition'] or '')
            if not runs:
                continue
            han = runs[-1].strip('()，。、')
            if len(han) < 2:  # chống nhiễu ký tự đơn (律→Ngũ Bộ Luật,…)
                continue
            # chống nhiễu: số ký tự Hán ≈ số âm tiết Việt (±1) — term thật thường 1:1
            syl = len(vi.split())
            if abs(len(han) - syl) > 1:
                continue
            pairs.setdefault(han, vi)
    print(f'[lexicon] trích {len(pairs):,} cặp Hán→Việt (chuỗi CJK cuối, dài ≥2)')
    return pairs


def load_vi_buddhist():
    """vi-buddhist.json (13 thuật ngữ style-lock) → dict han→vi."""
    if not os.path.exists(VI_BUDDHIST_JSON):
        print('[vi-buddhist.json] KHÔNG thấy file — bỏ qua nguồn này')
        return {}
    with open(VI_BUDDHIST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    terms = data.get('terms', {}) or {}
    print(f'[vi-buddhist.json] {len(terms)} thuật ngữ')
    return terms


def pass0_mirror(conn, dry_run):
    """Sao toàn bộ glossary_term → glossary_vi (term_vi=NULL)."""
    total = conn.execute('SELECT COUNT(*) FROM glossary_term').fetchone()[0]
    if dry_run:
        print(f'[pass0 mirror][dry-run] Sẽ mirror {total:,} row vào glossary_vi')
        return
    if not has_table(conn, 'glossary_vi'):
        conn.execute(CREATE_GLOSSARY_VI)
    conn.execute(
        """INSERT OR REPLACE INTO glossary_vi (glossary_id, term, language, created_at)
           SELECT id, term, language, ? FROM glossary_term""", (BUILT_AT,))
    print(f'[pass0 mirror] {total:,} row (term_vi=NULL) — đã mirror.')


def passA_exact_dict(conn, dry_run, vi_buddhist, lexicon_pairs):
    """Match nguyên chuỗi Hán theo ưu tiên từ điển. Zero-RAM (SQL JOIN)."""
    # temp tables chứa dict (session-local, không đụng schema base) — tạo CẢ khi dry-run
    conn.execute('CREATE TEMP TABLE IF NOT EXISTS _t110_vi_buddhist (han TEXT PRIMARY KEY, vi TEXT)')
    conn.execute('CREATE TEMP TABLE IF NOT EXISTS _t110_lexicon_hanvi (han TEXT PRIMARY KEY, vi TEXT)')
    conn.executemany('INSERT OR IGNORE INTO _t110_vi_buddhist (han, vi) VALUES (?,?)', list(vi_buddhist.items()))
    conn.executemany('INSERT OR IGNORE INTO _t110_lexicon_hanvi (han, vi) VALUES (?,?)', list(lexicon_pairs.items()))
    if dry_run:
        n_dc = conn.execute(
            """SELECT COUNT(*) FROM glossary_term g
               JOIN doctrine_concept d ON d.name_zh = g.term
               WHERE g.language='zho'""").fetchone()[0]
        n_vb = conn.execute(
            """SELECT COUNT(*) FROM glossary_term g
               WHERE g.language='zho' AND g.term IN (SELECT han FROM _t110_vi_buddhist)""").fetchone()[0]
        n_lx = conn.execute(
            """SELECT COUNT(*) FROM glossary_term g
               WHERE g.language='zho' AND g.term IN (SELECT han FROM _t110_lexicon_hanvi)""").fetchone()[0]
        n_np = conn.execute(
            """SELECT COUNT(*) FROM glossary_term g
               JOIN (SELECT name_zh FROM namevi_map_places WHERE name_zh IS NOT NULL GROUP BY name_zh) np
                 ON np.name_zh = g.term
               WHERE g.language='zho'""").fetchone()[0]
        n_nv = conn.execute(
            """SELECT COUNT(*) FROM glossary_term g
               JOIN (SELECT name_zh FROM name_vi_map WHERE name_zh IS NOT NULL GROUP BY name_zh) nv
                 ON nv.name_zh = g.term
               WHERE g.language='zho'""").fetchone()[0]
        print(f'[passA exact-dict][dry-run] doctrine_concept={n_dc} · vi-buddhist.json={n_vb} · '
              f'lexicon={n_lx} · places={n_np} · name_vi_map={n_nv} (có thể trùng chữ — landmark không cộng)')
        return
    conn.execute(
        """INSERT OR REPLACE INTO glossary_vi
               (glossary_id, term, language, term_vi, match_type, match_source, vi_confidence, source_glossary_id, created_at)
           SELECT g.id, g.term, g.language,
                  COALESCE(dc.name_vi, vb.vi, lx.vi, np.name_vi, nv.name_vi, NULL),
                  CASE WHEN dc.name_zh IS NOT NULL OR vb.han IS NOT NULL OR lx.han IS NOT NULL
                            OR np.name_zh IS NOT NULL OR nv.name_zh IS NOT NULL THEN 'exact_dict'
                       ELSE NULL END,
                  CASE WHEN dc.name_zh IS NOT NULL THEN 'doctrine_concept'
                       WHEN vb.han IS NOT NULL THEN 'vi_buddhist_json'
                       WHEN lx.han IS NOT NULL THEN 'lexicon'
                       WHEN np.name_zh IS NOT NULL THEN 'namevi_map_places'
                       WHEN nv.name_zh IS NOT NULL THEN 'name_vi_map'
                       ELSE NULL END,
                  1.0,
                  g.id,
                  ?
           FROM glossary_term g
           LEFT JOIN doctrine_concept dc ON dc.name_zh = g.term
           LEFT JOIN _t110_vi_buddhist vb  ON vb.han = g.term
           LEFT JOIN _t110_lexicon_hanvi lx ON lx.han = g.term
           LEFT JOIN (SELECT name_zh, MIN(name_vi) name_vi FROM namevi_map_places
                      WHERE name_zh IS NOT NULL GROUP BY name_zh) np ON np.name_zh = g.term
           LEFT JOIN (SELECT name_zh, MIN(name_vi) name_vi FROM name_vi_map
                      WHERE name_zh IS NOT NULL GROUP BY name_zh) nv ON nv.name_zh = g.term
           WHERE g.language='zho'
             AND (dc.name_zh IS NOT NULL OR vb.han IS NOT NULL OR lx.han IS NOT NULL
                  OR np.name_zh IS NOT NULL OR nv.name_zh IS NOT NULL)""",
        (BUILT_AT,))
    n = conn.execute("SELECT COUNT(*) FROM glossary_vi WHERE match_type='exact_dict'").fetchone()[0]
    srcs = [tuple(r) for r in conn.execute(
        """SELECT match_source, COUNT(*) FROM glossary_vi
           WHERE match_type='exact_dict' GROUP BY match_source ORDER BY COUNT(*) DESC""")]
    print(f'[passA exact-dict] {n:,} zho — theo nguồn: {srcs}')


def passB_char_hv(conn, dry_run, charhv):
    """Zho chưa có → phiên âm từng ký tự (deterministic). Zero-RAM chunked."""
    if dry_run:
        print('[passB char-HV][dry-run] Sẽ phiên âm zho còn trống (dự kiến ~43,7k full)')
        return
    cur = conn.execute(
        """SELECT g.id, g.term FROM glossary_term g
           JOIN glossary_vi v ON v.glossary_id = g.id
           WHERE g.language='zho' AND v.term_vi IS NULL
           ORDER BY g.id""")
    batch = []
    ins = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            t = (r['term'] or '').strip()
            chars = CJK.findall(t)
            if not chars:
                continue
            found = sum(1 for c in chars if c in charhv)
            if not found:
                continue  # confidence=0 → bỏ qua (không bịa)
            # dịch từng CỤM Hán, giữ phân cách (;/、/khoảng trắng…), nối âm bằng ' '
            parts = []
            for seg in re.split(r'([\u4e00-\u9fff]+)', t):
                if seg and re.fullmatch(r'[\u4e00-\u9fff]+', seg):
                    parts.append(' '.join(charhv.get(c, c) for c in seg))
                elif seg:
                    parts.append(seg)
            reading = ''.join(parts).strip()
            conf = found / len(chars)
            batch.append((r['id'], t, 'zho', reading, 'char_hv', 'char_hv', round(conf, 3), r['id'], BUILT_AT))
            if len(batch) >= 5000:
                conn.executemany(
                    """INSERT OR REPLACE INTO glossary_vi
                       (glossary_id, term, language, term_vi, match_type, match_source, vi_confidence, source_glossary_id, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?)""", batch)
                ins += len(batch)
                batch = []
        if batch:
            conn.executemany(
                """INSERT OR REPLACE INTO glossary_vi
                   (glossary_id, term, language, term_vi, match_type, match_source, vi_confidence, source_glossary_id, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""", batch)
            ins += len(batch)
            batch = []
    full = conn.execute(
        """SELECT COUNT(*) FROM glossary_vi WHERE match_type='char_hv' AND vi_confidence=1.0""").fetchone()[0]
    print(f'[passB char-HV] {ins:,} zho; trong đó phiên đủ 100%: {full:,}')


def passC_via_sibling(conn, dry_run):
    """san/bod/bo-Latn: chưa có Việt → kế thừa row zho CÙNG full_text (cùng khái niệm)."""
    if dry_run:
        print('[passC via-sibling][dry-run] Sẽ kế thừa term_vi từ row zho cùng full_text')
        return
    # dict full_text → meta từ zho đã Việt hóa (giá trị nằm trong memory nhỏ ~67k)
    full2meta = {}
    for r in conn.execute(
            """SELECT g.full_text, v.term_vi, v.match_type, v.match_source, v.vi_confidence, v.glossary_id
               FROM glossary_vi v JOIN glossary_term g ON g.id = v.glossary_id
               WHERE v.language='zho' AND v.term_vi IS NOT NULL"""):
        ft = r['full_text']
        if ft:
            full2meta[ft] = (r['term_vi'], r['match_type'], r['match_source'], r['vi_confidence'], r['glossary_id'])
    print(f'[passC via-sibling] {len(full2meta):,} khái niệm (full_text) có zho đã Việt hóa')

    cur = conn.execute(
        """SELECT g.id, g.term, g.language, g.full_text FROM glossary_term g
           JOIN glossary_vi v ON v.glossary_id = g.id
           WHERE v.term_vi IS NULL
           ORDER BY g.id""")
    batch = []
    ins = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            meta = full2meta.get(r['full_text'])
            if not meta:
                continue
            term_vi, mtype, msrc, conf, sibling = meta
            batch.append((r['id'], r['term'], r['language'], term_vi, 'via_zho_sibling', msrc, conf, sibling, BUILT_AT))
            if len(batch) >= 5000:
                conn.executemany(
                    """INSERT OR REPLACE INTO glossary_vi
                       (glossary_id, term, language, term_vi, match_type, match_source, vi_confidence, source_glossary_id, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?)""", batch)
                ins += len(batch)
                batch = []
        if batch:
            conn.executemany(
                """INSERT OR REPLACE INTO glossary_vi
                   (glossary_id, term, language, term_vi, match_type, match_source, vi_confidence, source_glossary_id, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""", batch)
            ins += len(batch)
            batch = []
    print(f'[passC via-sibling] {ins:,} row san/bod/bo-Latn kế thừa term_vi.')


def report(conn):
    total = conn.execute('SELECT COUNT(*) FROM glossary_term').fetchone()[0]
    with_vi = conn.execute('SELECT COUNT(*) FROM glossary_vi WHERE term_vi IS NOT NULL').fetchone()[0]
    print('\n===== METRIC glossary_vi_coverage =====')
    print(f'glossary_term           : {total:,}')
    print(f'glossary_vi có term_vi  : {with_vi:,}  →  COVERAGE {with_vi/total*100:.2f}%')
    print('— theo ngôn ngữ:')
    for r in conn.execute(
            """SELECT g.language, COUNT(*) rows_all,
                      SUM(CASE WHEN v.term_vi IS NOT NULL THEN 1 ELSE 0 END) rows_vi,
                      ROUND(100.0*SUM(CASE WHEN v.term_vi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*), 1) pct
               FROM glossary_term g JOIN glossary_vi v ON v.glossary_id=g.id
               GROUP BY g.language ORDER BY rows_all DESC"""):
        print(f'   {r["language"]:<8} {r["rows_all"]:>7,} row → {r["rows_vi"]:>7,} có Việt ({r["pct"]}%)')
    print('— theo match_type:')
    for r in conn.execute(
            """SELECT match_type, COUNT(*) FROM glossary_vi WHERE term_vi IS NOT NULL
               GROUP BY match_type ORDER BY COUNT(*) DESC"""):
        print(f'   {r["match_type"]:<18} {r[1]:>7,}')
    print('— mẫu chất lượng (exact_dict):')
    for r in conn.execute(
            """SELECT term, term_vi, match_source FROM glossary_vi
               WHERE match_type='exact_dict' ORDER BY length(term) DESC LIMIT 8"""):
        print(f'   {r["term"]}  →  {r["term_vi"]}   [{r["match_source"]}]')
    print('— mẫu char_hv:')
    for r in conn.execute(
            """SELECT term, term_vi, vi_confidence FROM glossary_vi
               WHERE match_type='char_hv' AND length(term)>=4 ORDER BY vi_confidence DESC, length(term) DESC LIMIT 6"""):
        print(f'   {r["term"]}  →  {r["term_vi"]}   (conf {r["vi_confidence"]})')


def cmd_dry_run():
    print('── DRY-RUN T110 Glossary Vietnamese Pipeline ──')
    conn = connect()
    try:
        print(f'DB   : {DB_PATH}')
        total = conn.execute('SELECT COUNT(*) FROM glossary_term').fetchone()[0]
        print(f'glossary_term: {total:,} row')
        pass0_mirror(conn, True)
        vb = load_vi_buddhist()
        lp = extract_lexicon_pairs(conn)
        passA_exact_dict(conn, True, vb, lp)
        passB_char_hv(conn, True, load_charhv(conn))
        passC_via_sibling(conn, True)
        print('Backup sẽ tạo: data/backups/lineage_t110_<ts>.db (SQLite backup API, Zero-RAM)')
    finally:
        conn.close()


def cmd_apply():
    print('── APPLY T110 Glossary Vietnamese Pipeline ──')
    backup = make_backup()
    conn = connect()
    try:
        total = conn.execute('SELECT COUNT(*) FROM glossary_term').fetchone()[0]
        print(f'glossary_term: {total:,} row')
        pass0_mirror(conn, False)
        vb = load_vi_buddhist()
        lp = extract_lexicon_pairs(conn)
        passA_exact_dict(conn, False, vb, lp)
        passB_char_hv(conn, False, load_charhv(conn))
        passC_via_sibling(conn, False)
        conn.commit()
        report(conn)
        print(f'\n[apply] OK — backup: {backup}')
    finally:
        conn.close()


def cmd_revert():
    print('── REVERT T110 Glossary Vietnamese Pipeline ──')
    conn = connect()
    try:
        if not has_table(conn, 'glossary_vi'):
            print('[revert] bảng glossary_vi KHÔNG tồn tại — không có gì để revert.')
        else:
            conn.execute('DROP TABLE IF EXISTS glossary_vi')
            conn.commit()
            print('[revert] Đã DROP bảng dẫn xuất glossary_vi.')
        base = conn.execute('SELECT COUNT(*) FROM glossary_term').fetchone()[0]
        print(f'[revert] Base không đổi: glossary_term = {base:,}')
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description='ETL T110 — Glossary Vietnamese Pipeline (Zero-ALTER · Zero-RAM)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    args = ap.parse_args()
    if args.dry_run:
        cmd_dry_run()
    elif args.apply:
        cmd_apply()
    else:
        cmd_revert()


if __name__ == '__main__':
    main()