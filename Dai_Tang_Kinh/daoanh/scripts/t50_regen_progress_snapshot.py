#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T50-canon-id-fix — regenerate data/t50_progress_snapshot.json từ DB thật.

BỐI CẢNH (2026-11-06):
Tab "Tiến độ theo bộ kinh" (admin/translation_progress.html#t50) fallback về
file snapshot tĩnh `data/t50_progress_snapshot.json` mỗi khi gọi
`/daoanh/api/admin/t50-progress` thất bại (backend port 5000 không chạy).
File snapshot đó được tạo thủ công ngày 2026-09-27 và đang chứa tên kinh SAI
cho 5 mã: mỗi dòng bị lệch 1 vị trí so với mapping đúng hiện có trong
`dila_catalog_works` (đã verify bằng DB thật 2026-11-06, xem báo cáo verify
bug T50 canon-id):

    sigla        snapshot cũ (SAI)                 DB thật / live API (ĐÚNG)
    T51n2076     Chỉ Nguyệt Lục (指月錄)             Cảnh Đức Truyền Đăng Lục (景德傳燈錄)
    T50n2061     Cảnh Đức Truyền Đăng Lục (景德傳燈錄) Tống Cao Tăng Truyện (宋高僧傳)
    T50n2060     Tổ Đường Tập (祖堂集)               Tục Cao Tăng Truyện (續高僧傳)
    X77n1524     Ngũ Đăng Hội Nguyên (五燈會元)       Bổ Tục Cao Tăng Truyện (補續高僧傳)
    T50n2062     Thiên Thánh Quảng Đăng Lục (天聖廣燈錄) Đại Minh Cao Tăng Truyện (大明高僧傳)

Route `/daoanh/api/admin/t50-progress` (app.py) và bảng `dila_catalog_works`
hiện ĐÚNG — đã verify trực tiếp bằng DB + browser khi backend đang chạy.
KHÔNG có bug trong code mapping (app.py dùng text-number toàn cục, bỏ số tập
là đúng theo quy ước Taishō/Tục Tạng — mỗi text number là duy nhất toàn Đại
Tạng, không phụ thuộc tập). Script này chỉ regenerate lại file snapshot tĩnh
cho khớp với route thật — KHÔNG đổi schema, KHÔNG đổi app.py, KHÔNG đổi
`dila_catalog_works`.

Dùng:
    python scripts/t50_regen_progress_snapshot.py --dry-run   # chỉ in, 0 ghi
    python scripts/t50_regen_progress_snapshot.py --apply     # ghi file, có backup
    python scripts/t50_regen_progress_snapshot.py --revert    # khôi phục backup gần nhất

An toàn: chỉ đọc DB (SELECT), không ghi DB. Chỉ ghi đúng 1 file
`data/t50_progress_snapshot.json`. Backup bản cũ vào
`data/backups/t50_progress_snapshot_<UTC timestamp>.json` trước khi ghi đè.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.environ.get('T50_DB_PATH') or os.path.join(DAOANH, 'data', 'lineage.db')
SNAP_PATH = os.path.join(DAOANH, 'data', 't50_progress_snapshot.json')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')


def _connect():
    if not os.path.exists(DB_PATH):
        print('[LOI] Khong tim thay DB: %s' % DB_PATH)
        sys.exit(1)
    conn = sqlite3.connect('file:' + DB_PATH + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def build_snapshot(conn):
    """Y HET logic route t50_translation_progress() trong app.py (10670+).
    Doc-only; khong goi app.py de tranh phu thuoc Flask khi chay script roi."""
    total_all = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
    translated_all = conn.execute("SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL").fetchone()[0]
    draft_all = conn.execute("SELECT COUNT(*) FROM passage WHERE translation_draft=1").fetchone()[0]
    cache_all = conn.execute("SELECT COUNT(*) FROM translation_cache WHERE source_type='passage'").fetchone()[0]
    reported_all = conn.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE source_type='passage' AND status='reported'"
    ).fetchone()[0]

    place_total = conn.execute(
        "SELECT COUNT(DISTINCT p.passage_id) FROM passage p JOIN passage_entity pe ON pe.passage_id=p.passage_id"
    ).fetchone()[0]
    place_translated = conn.execute(
        "SELECT COUNT(DISTINCT p.passage_id) FROM passage p JOIN passage_entity pe ON pe.passage_id=p.passage_id WHERE p.vi_text IS NOT NULL"
    ).fetchone()[0]

    rows = conn.execute("""
        SELECT text_id,
               COUNT(*) as total,
               SUM(CASE WHEN vi_text IS NOT NULL THEN 1 ELSE 0 END) as translated,
               SUM(CASE WHEN translation_draft=1 THEN 1 ELSE 0 END) as draft_ai
        FROM passage
        GROUP BY text_id
        ORDER BY total DESC
    """).fetchall()

    dila_names = {
        r['cbeta_id']: (r['title_zh'] or '', r['title_vi'] or '')
        for r in conn.execute("SELECT cbeta_id, title_zh, title_vi FROM dila_catalog_works")
    }

    sigla_list = []
    for r in rows:
        tid = r['text_id'] or 'unknown'
        total = r['total'] or 0
        translated = r['translated'] or 0
        draft = r['draft_ai'] or 0
        remaining = total - translated
        pct = round(translated / total * 100, 1) if total else 0
        m = re.match(r'^([A-Z])(\d+)n(\d+)([A-Za-z]?)$', tid)
        dila_id = ('%s%04d%s' % (m.group(1), int(m.group(3)), m.group(4))) if m else None
        name_zh, name_vi = dila_names.get(dila_id, ('', ''))
        if name_vi:
            display = name_vi + (' (' + name_zh + ')' if name_zh else '')
        else:
            display = tid
        sigla_list.append({
            'sigla': tid,
            'dila_id': dila_id,
            'name': display,
            'name_zh': name_zh,
            'name_vi': name_vi,
            'total': total,
            'translated': translated,
            'draft_ai': draft,
            'remaining': remaining,
            'pct': pct,
        })

    recent = conn.execute("""
        SELECT p.passage_id, p.text_id, p.loc_ref,
               SUBSTR(p.raw_text,1,80) as raw_preview,
               SUBSTR(p.vi_text,1,100) as vi_preview,
               p.translation_draft
        FROM passage p
        WHERE p.vi_text IS NOT NULL
        ORDER BY p.passage_id DESC
        LIMIT 5
    """).fetchall()

    return {
        'ok': True,
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'summary': {
            'total_all': total_all,
            'translated_all': translated_all,
            'draft_ai': draft_all,
            'remaining_all': total_all - translated_all,
            'pct_all': round(translated_all / total_all * 100, 1) if total_all else 0,
            'place_total': place_total,
            'place_translated': place_translated,
            'place_remaining': place_total - place_translated,
            'place_pct': round(place_translated / place_total * 100, 1) if place_total else 0,
            'translation_cache': cache_all,
            'reported': reported_all,
        },
        'by_sigla': sigla_list,
        'recent_translated': [dict(r) for r in recent],
    }


def _backup_path():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return os.path.join(BACKUP_DIR, 't50_progress_snapshot_%s.json' % ts)


def do_dry_run():
    conn = _connect()
    try:
        snap = build_snapshot(conn)
    finally:
        conn.close()
    targets = {'T51n2076', 'T50n2061', 'T50n2060', 'X77n1524', 'T50n2062'}
    print('=== T50 regen snapshot — DRY RUN (0 ghi) ===')
    print('DB: %s' % DB_PATH)
    print('File dich: %s' % SNAP_PATH)
    print('File cu ton tai: %s' % os.path.exists(SNAP_PATH))
    print('\n5 ma bi bao cao sai (so sanh voi file snapshot cu):')
    for r in snap['by_sigla']:
        if r['sigla'] in targets:
            print('  %-10s dila_id=%-7s -> %s' % (r['sigla'], r['dila_id'], r['name']))
    print('\nTong quan se ghi:')
    print(json.dumps(snap['summary'], ensure_ascii=False, indent=2))
    print('\n[SQL/IO plan] ghi de %s, backup truoc vao %s/' % (SNAP_PATH, BACKUP_DIR))


def do_apply():
    conn = _connect()
    try:
        snap = build_snapshot(conn)
    finally:
        conn.close()
    if os.path.exists(SNAP_PATH):
        bkp = _backup_path()
        shutil.copy2(SNAP_PATH, bkp)
        print('[BACKUP] %s' % bkp)
    with open(SNAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print('[OK] Da ghi %s (%d bo kinh)' % (SNAP_PATH, len(snap['by_sigla'])))


def do_revert():
    if not os.path.isdir(BACKUP_DIR):
        print('[LOI] Khong co thu muc backup: %s' % BACKUP_DIR)
        sys.exit(1)
    snaps = sorted(
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith('t50_progress_snapshot_') and f.endswith('.json')
    )
    if not snaps:
        print('[LOI] Khong co backup nao de revert.')
        sys.exit(1)
    latest = os.path.join(BACKUP_DIR, snaps[-1])
    shutil.copy2(latest, SNAP_PATH)
    print('[REVERT] Da khoi phuc %s tu %s' % (SNAP_PATH, latest))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true', help='Chi in, khong ghi gi (mac dinh an toan)')
    g.add_argument('--apply', action='store_true', help='Ghi de file snapshot, co backup truoc')
    g.add_argument('--revert', action='store_true', help='Khoi phuc backup gan nhat')
    args = ap.parse_args()
    if args.dry_run:
        do_dry_run()
    elif args.apply:
        do_apply()
    elif args.revert:
        do_revert()


if __name__ == '__main__':
    main()
