#!/usr/bin/env python3
"""
ETL script: Import DILA Time Authority data from MySQL dump into SQLite time_periods table.

Reads: data/dila_import/Authority-Databases/authority_time/SQL/authority_time.sql
Writes: data/lineage.db time_periods table

Maps MySQL tables:
- t_month  -> period_name='lunar_month', era_name=lunar month name
- t_era    -> period_name='era', era_name=era name
- t_dynasty-> period_name='dynasty', era_name=dynasty name
- t_emperor-> period_name='emperor', era_name=emperor name

Uses generator/iterator for zero-RAM processing.
"""

import re
import sqlite3
import os
from datetime import datetime


SQL_DUMP_PATH = r'data\dila_import\Authority-Databases\authority_time\SQL\authority_time.sql'
DB_PATH = r'data\lineage.db'

# SQLite time_periods schema:
# id TEXT PRIMARY KEY,
# period_name TEXT NOT NULL,   -- 'lunar_month', 'era', 'dynasty', 'emperor'
# period_name_zh TEXT,       -- Chinese name
# period_name_vi TEXT,       -- Vietnamese name (empty for now)
# start_year INTEGER,
# end_year INTEGER,
# era_name TEXT,             -- dynasty/era emperor name
# source_origin TEXT DEFAULT 'DILA',
# created_at TEXT DEFAULT CURRENT_TIMESTAMP


def parse_sql_inserts(sql_path):
    """Generator that yields (table_name, values_tuple) from MySQL dump."""
    with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Find all INSERT INTO ... VALUES (...) statements
    # Pattern: INSERT INTO `table` VALUES (...),(...),...
    insert_pattern = re.compile(
        r"INSERT\s+INTO\s+`(\w+)`\s+VALUES\s+\(([^;]+)\)",
        re.IGNORECASE | re.DOTALL
    )

    for match in insert_pattern.finditer(content):
        table_name = match.group(1)
        values_str = match.group(2)

        # Parse individual value groups
        # Split on ),( to get individual rows
        value_groups = re.split(r'\)\,\s*\(', values_str)

        for vg in value_groups:
            vg = vg.strip()
            if not vg:
                continue
            # Remove surrounding parentheses
            if vg.startswith('(') and vg.endswith(')'):
                vg = vg[1:-1]
            vals = [val.strip().strip("'").strip('"') for val in vg.split(',')]
            yield table_name, tuple(vals)


def map_to_time_periods(table_name, values):
    """Map MySQL row data to time_periods SQLite schema."""
    if table_name == 't_month':
        if len(values) < 7:
            return None
        
        period_id = str(values[0])  # id
        year = int(values[1]) if values[1] else None
        month_num = int(values[2]) if values[2] else None
        lunar_name_zho = values[3] if len(values) > 3 else ''
        
        # JD values at positions 5 and 6
        start_jd = int(values[5]) if len(values) > 5 and values[5] else None
        end_jd = int(values[6]) if len(values) > 6 and values[6] else None
        
        # Convert JD to approximate year
        if start_jd:
            start_year = int((start_jd - 1721119) / 365.25) + 1970
        else:
            start_year = year
        if end_jd:
            end_year = int((end_jd - 1721119) / 365.25) + 1970
        else:
            end_year = year
        
        era_id = values[8] if len(values) > 8 else ''
        
        return {
            'id': period_id,
            'period_name': 'lunar_month',
            'period_name_zh': lunar_name_zho if lunar_name_zho else f'Tháng {month_num}',
            'period_name_vi': '',
            'start_year': start_year,
            'end_year': end_year,
            'era_name': str(era_id) if era_id else '',
            'source_origin': 'DILA',
        }
    
    elif table_name == 't_era':
        if len(values) < 2:
            return None
        
        period_id = str(values[0])
        era_name = str(values[1]) if len(values) > 1 else ''
        
        return {
            'id': period_id,
            'period_name': 'era',
            'period_name_zh': era_name,
            'period_name_vi': '',
            'start_year': None,
            'end_year': None,
            'era_name': era_name,
            'source_origin': 'DILA',
        }
    
    elif table_name == 't_dynasty':
        if len(values) < 2:
            return None
        
        period_id = str(values[0])
        dtype = values[1] if len(values) > 1 else ''
        
        return {
            'id': period_id,
            'period_name': 'dynasty',
            'period_name_zh': dtype,
            'period_name_vi': '',
            'start_year': None,
            'end_year': None,
            'era_name': dtype,
            'source_origin': 'DILA',
        }
    
    elif table_name == 't_emperor':
        if len(values) < 2:
            return None
        
        period_id = str(values[0])
        dynasty_id = str(values[1]) if len(values) > 1 else ''
        
        return {
            'id': period_id,
            'period_name': 'emperor',
            'period_name_zh': dynasty_id,
            'period_name_vi': '',
            'start_year': None,
            'end_year': None,
            'era_name': dynasty_id,
            'source_origin': 'DILA',
        }
    
    return None


def import_time_authority():
    """Main ETL function: import DILA time authority data into SQLite."""
    if not os.path.exists(SQL_DUMP_PATH):
        print(f'SQL dump not found: {SQL_DUMP_PATH}')
        return False
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    
    # Ensure time_periods table exists with correct schema
    conn.execute('''
        CREATE TABLE IF NOT EXISTS time_periods (
            id TEXT PRIMARY KEY,
            period_name TEXT NOT NULL,
            period_name_zh TEXT,
            period_name_vi TEXT,
            start_year INTEGER,
            end_year INTEGER,
            era_name TEXT,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    records_inserted = 0
    records_skipped = 0
    
    print('=' * 60)
    print('T14: Import DILA Time Authority')
    print('=' * 60)
    print(f'Source: {SQL_DUMP_PATH}')
    print(f'Target: {DB_PATH} -> time_periods table')
    print()
    
    # Process using generator (zero-RAM pattern)
    batch = []
    BATCH_SIZE = 100
    
    for table_name, values in parse_sql_inserts(SQL_DUMP_PATH):
        mapped = map_to_time_periods(table_name, values)
        if mapped is None:
            records_skipped += 1
            continue
        
        # Check if already exists (use INSERT OR IGNORE for idempotency)
        existing = conn.execute(
            'SELECT id FROM time_periods WHERE id = ?', 
            (mapped['id'],)
        ).fetchone()
        
        # Use INSERT OR IGNORE for idempotency - skip if id already exists
        existing = conn.execute(
            'SELECT id FROM time_periods WHERE id = ?', 
            (mapped['id'],)
        ).fetchone()
        
        if existing:
            records_skipped += 1
            continue
        
        mapped['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        batch.append((
            mapped['id'],
            mapped['period_name'],
            mapped['period_name_zh'],
            mapped['period_name_vi'],
            mapped['start_year'],
            mapped['end_year'],
            mapped['era_name'],
            mapped['source_origin'],
            mapped['created_at']
        ))
        
        if len(batch) >= BATCH_SIZE:
            conn.executemany(
                '''INSERT OR IGNORE INTO time_periods 
                   (id, period_name, period_name_zh, period_name_vi, 
                    start_year, end_year, era_name, source_origin, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                batch
            )
            conn.commit()
            records_inserted += len(batch)
            batch = []
            
            if records_inserted % 1000 == 0:
                print(f'  Progress: {records_inserted} records inserted...')
    
    # Insert remaining batch
    if batch:
        conn.executemany(
            '''INSERT INTO time_periods 
               (id, period_name, period_name_zh, period_name_vi, 
                start_year, end_year, era_name, source_origin, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            batch
        )
        conn.commit()
        records_inserted += len(batch)
    
    # Print final stats
    total_rows = conn.execute('SELECT COUNT(*) FROM time_periods').fetchone()[0]
    print()
    print('=' * 60)
    print(f'Import complete!')
    print(f'  Records inserted: {records_inserted}')
    print(f'  Records skipped (already exist): {records_skipped}')
    print(f'  Total rows in time_periods: {total_rows}')
    print('=' * 60)
    
    conn.close()
    return True


if __name__ == '__main__':
    success = import_time_authority()
    exit(0 if success else 1)