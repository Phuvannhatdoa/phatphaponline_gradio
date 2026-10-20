#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T428 Part 2 setup — Create AI tables for places + districts.
Tạo bảng ai_place_name và ai_district_name (tương tự ai_person_name).
"""

import sqlite3

DB_PATH = 'data/lineage.db'

def create_ai_place_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_place_name (
            dila_id     TEXT PRIMARY KEY,
            name_vi_ai  TEXT,
            model       TEXT DEFAULT 'gemini-3.1-flash-lite',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print('[OK] ai_place_name table created/verified')


def create_ai_district_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_district_name (
            dila_id     TEXT PRIMARY KEY,
            name_vi_ai  TEXT,
            model       TEXT DEFAULT 'gemini-3.1-flash-lite',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print('[OK] ai_district_name table created/verified')


def verify():
    conn = sqlite3.connect('file:data/lineage.db?mode=ro', uri=True)
    for t in ['ai_place_name', 'ai_district_name']:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: {cnt} rows')
    conn.close()


if __name__ == '__main__':
    create_ai_place_table()
    create_ai_district_table()
    verify()