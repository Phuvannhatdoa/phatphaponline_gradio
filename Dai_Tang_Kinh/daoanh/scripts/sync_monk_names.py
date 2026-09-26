#!/usr/bin/env python3
"""
ETL: Sync monk_dict → monk_name_index
Reads all approved monk_dict records, extracts every name form,
normalizes (remove diacritics + lowercase), and inserts into monk_name_index.
"""

import sqlite3
import json
import unicodedata
import re
import sys
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'lineage.db')


def normalize(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()


def insert_name(conn, monk_id, lang, name_form, name_type):
    norm = normalize(name_form)
    if not norm:
        return
    conn.execute("""
        INSERT OR IGNORE INTO monk_name_index
            (monk_id, lang, name_form, name_type, normalized)
        VALUES (?, ?, ?, ?, ?)
    """, (monk_id, lang, name_form, name_type, norm))


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Read all approved monks
    rows = cur.execute(
        "SELECT id, han_name, vn_name, pinyin, alt_han_names, vn_aliases FROM monk_dict WHERE status = 'approved'"
    ).fetchall()

    total_names = 0
    for row in rows:
        monk_id = row['id']
        # Clear existing index for this monk
        cur.execute("DELETE FROM monk_name_index WHERE monk_id = ?", (monk_id,))

        # zh: han_name (official)
        if row['han_name']:
            insert_name(conn, monk_id, 'zh', row['han_name'], 'official')

        # vi: vn_name (official)
        if row['vn_name']:
            insert_name(conn, monk_id, 'vi', row['vn_name'], 'official')

        # pinyin
        if row['pinyin']:
            insert_name(conn, monk_id, 'pinyin', row['pinyin'], 'official')

        # alt_han_names (alias)
        alt_han = json.loads(row['alt_han_names'] or '[]')
        for name in alt_han:
            if name.strip():
                insert_name(conn, monk_id, 'zh', name.strip(), 'alias')

        # vn_aliases (alias)
        vn_aliases = json.loads(row['vn_aliases'] or '[]')
        for name in vn_aliases:
            if name.strip():
                insert_name(conn, monk_id, 'vi', name.strip(), 'alias')

        # Count inserted
        count = cur.execute(
            "SELECT COUNT(*) as c FROM monk_name_index WHERE monk_id = ?",
            (monk_id,)
        ).fetchone()['c']
        total_names += count
        print(f"  [{monk_id}] {row['han_name']}: {count} names indexed")

    conn.commit()
    conn.close()
    print(f"\n✅ Done: {len(rows)} monks, {total_names} names indexed")


if __name__ == '__main__':
    main()
