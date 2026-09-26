#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T82 — Step 1: Merge & normalize `vn_person_events` legacy (source=NULL) rows.

Hiện trạng: có 45 rows legacy (curated TTL, person_id dạng slug như `bach_van_thu_doan`)
với source=NULL, confidence=NULL, event_type dùng hoa thư `Birth`/`Death` (trùng nghĩa với
`birth`/`death` lowercase từ T79) và các type ngữ nghĩa `KeyLifeEvent`/`Contribution`/`PhilosophicalStance`.

Việc làm (--apply):
  1. Backup 45 rows -> data/t82_legacy_backup.json (snapshot theo id)
  2. UPDATE source=NULL   -> 'legacy_ttl'
  3. UPDATE confidence=NULL -> 1.0 (curated TTL thủ công)
  4. UPDATE event_type    -> 'birth' (Birth), 'death' (Death)
     (Giữ nguyên KeyLifeEvent/Contribution/PhilosophicalStance — type ngữ nghĩa riêng,
      KHÔNG flatten vào birth/death/active/floruit để không mất thông tin.)
  5. UPDATE source_ref    -> ttl_filename (lưu provenance rõ ràng)

Revert (--revert): khôi phục đúng giá trị gốc từ snapshot (rollback thuận tiện 1 lệnh).

Usage:
  python t82_merge_events.py            # dry-run
  python t82_merge_events.py --apply    # backup + update
  python t82_merge_events.py --revert   # restore từ backup
  python t82_merge_events.py --stats    # thống kê
"""

import sys
import os
import json
import argparse
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
BACKUP_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\t82_legacy_backup.json'
LOG_PATH = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\t82_merge_log.json'
EVENTS_TABLE = 'vn_person_events'

# event_type normalization map (uppercase legacy -> lowercase chuẩn với T79/T81)
TYPE_MAP = {'Birth': 'birth', 'Death': 'death'}
# Các type ngữ nghĩa GIỮ NGUYÊN (không flatten)
KEEP_TYPES = {'KeyLifeEvent', 'Contribution', 'PhilosophicalStance'}

LEGACY_SOURCE = 'legacy_ttl'


def fetch_legacy(conn):
    c = conn.cursor()
    c.execute(f"SELECT id, person_id, event_type, event_id, event_label_vi, event_year, ttl_filename, source, confidence, source_ref FROM {EVENTS_TABLE} WHERE source IS NULL")
    rows = c.fetchall()
    cols = ['id', 'person_id', 'event_type', 'event_id', 'event_label_vi', 'event_year', 'ttl_filename', 'source', 'confidence', 'source_ref']
    return [dict(zip(cols, r)) for r in rows]


def main(arguments):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ---- STATS ----
    if arguments.stats:
        print("=== vn_person_events by source ===")
        for r in c.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source"):
            print(f"  {r[0]!r}: {r[1]}")
        print("\n=== distinct event_type ===")
        for r in c.execute("SELECT DISTINCT event_type FROM vn_person_events"):
            print(" ", r[0])
        conn.close()
        return

    legacy = fetch_legacy(conn)
    print(f"Legacy (source=NULL) rows: {len(legacy)}")

    # ---- REVERT ----
    if arguments.revert:
        if not os.path.isfile(BACKUP_PATH):
            print(f"[ERR] Backup không tồn tại: {BACKUP_PATH}")
            conn.close()
            return 1
        with open(BACKUP_PATH, encoding='utf-8') as f:
            backup = json.load(f)
        restored = 0
        for ev in backup:
            c.execute(f"""
                UPDATE {EVENTS_TABLE} SET person_id=?, event_type=?, event_id=?, event_label_vi=?,
                       event_year=?, ttl_filename=?, source=?, confidence=?, source_ref=?
                WHERE id=?
            """, (ev['person_id'], ev['event_type'], ev['event_id'], ev['event_label_vi'],
                  ev['event_year'], ev['ttl_filename'], ev['source'], ev['confidence'], ev['source_ref'],
                  ev['id']))
            restored += 1
        conn.commit()
        print(f"Reverted: {restored} rows restored từ backup (source=NULL như cũ).")
        conn.close()
        return 0

    # ---- DRY-RUN / APPLY ----
    # Phân tích thay đổi
    changes = []
    for ev in legacy:
        new_type = TYPE_MAP.get(ev['event_type'], ev['event_type'])
        if (ev['source'] != LEGACY_SOURCE or ev['confidence'] != 1.0 or new_type != ev['event_type']):
            changes.append({'id': ev['id'], 'person_id': ev['person_id'],
                            'old_type': ev['event_type'], 'new_type': new_type})

    print(f"Rows cần chỉnh: {len(changes)} (source->legacy_ttl, confidence->1.0, Birth/Death->lowercase)")
    print(f"Rows giữ nguyên type ngữ nghĩa (KeyLifeEvent/Contribution/PhilosophicalStance): "
          f"{sum(1 for ev in legacy if ev['event_type'] in KEEP_TYPES)}")

    if not arguments.apply:
        print("\n=== SAMPLE changes (first 12) ===")
        for ch in changes[:12]:
            print(f"  id={ch['id']} {ch['person_id']}: {ch['old_type']!r} -> {ch['new_type']!r}")
        log = {'date': datetime.now().isoformat(), 'action': 'dry-run',
               'legacy_rows': len(legacy), 'rows_to_change': len(changes)}
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        conn.close()
        return 0

    # ---- APPLY ----
    # 1) Backup trước khi đổi
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(legacy, f, ensure_ascii=False, indent=2)
    print(f"Backup đã lưu: {BACKUP_PATH} ({len(legacy)} rows)")

    # 2) Thực hiện UPDATE
    updated = 0
    for ev in legacy:
        new_type = TYPE_MAP.get(ev['event_type'], ev['event_type'])
        c.execute(f"""
            UPDATE {EVENTS_TABLE}
            SET source=?, confidence=?, event_type=?, source_ref=?
            WHERE id=?
        """, (LEGACY_SOURCE, 1.0, new_type, ev['ttl_filename'], ev['id']))
        updated += 1
    conn.commit()
    print(f"Updated: {updated} legacy rows (source='{LEGACY_SOURCE}', confidence=1.0, type chuẩn hoá)")

    # 3) Verify
    c.execute(f"SELECT COUNT(*) FROM {EVENTS_TABLE} WHERE source IS NULL")
    still_null = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM {EVENTS_TABLE} WHERE source='{LEGACY_SOURCE}'")
    merged = c.fetchone()[0]
    print(f"Sau apply: source=NULL còn lại = {still_null}; source='{LEGACY_SOURCE}' = {merged}")
    c.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source")
    print("Phân bố theo source:")
    for s, n in c.fetchall():
        print(f"  {s!r}: {n}")

    log = {'date': datetime.now().isoformat(), 'action': 'apply',
           'legacy_rows': len(legacy), 'backup': BACKUP_PATH,
           'source': LEGACY_SOURCE, 'rows_merged': merged,
           'source_null_remaining': still_null}
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nLog: {LOG_PATH}")
    conn.close()
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='T82 Step1: Merge legacy vn_person_events')
    parser.add_argument('--apply', action='store_true', help='Backup + normalize legacy rows')
    parser.add_argument('--revert', action='store_true', help='Restore từ backup')
    parser.add_argument('--stats', action='store_true', help='Thống kê và thoát')
    args = parser.parse_args()
    sys.exit(main(args))
