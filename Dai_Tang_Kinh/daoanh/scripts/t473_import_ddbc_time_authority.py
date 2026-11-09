#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T473: Import DDBC Time Authority into SQLite with ddbc_ prefix
Author: T473 Task
Date: 2026-10-28

Source: data/dila_import/Authority-Databases-master/Authority-Databases-master/authority_time/SQL/authority_time.sql
Target: data/lineage.db with tables prefixed ddbc_
"""

import re
import sqlite3
import hashlib
import os
import sys
from typing import Dict, List, Tuple, Optional

# ============================================================
# CONFIGURATION
# ============================================================
SQL_FILE = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL\authority_time.sql'
DB_FILE = r'data\lineage.db'
TABLE_PREFIX = 'ddbc_'

# Tables to import (in dependency order)
TABLES = [
    'c_languages',
    't_dynasty',
    't_dynasty_names',
    't_dynasty_comments',
    't_emperor',
    't_emperor_names',
    't_emperor_comments',
    't_era',
    't_era_names',
    't_era_comments',
    't_month',
    't_month_comments',
    't_month_names',  # may not exist
    't_day_comments',
]

# ============================================================
# SHA256 of source files (for verification)
# ============================================================
SOURCE_HASHES = {
    'authority_time.sql': '7183a770c7ebb05c19704beb338db53f3d09b75f75df5f284370d0bce6c902f7',
    'authority_time_chinese.sql': '423bd0b2126011275c354307cf5416a3952e23f3a88f017f97b2c11ca36d5974',
    'authority_time_japanese.sql': '172a09c0672ed98ca494beb8bab2ce6cc66308dca1cb8d46a5cf3eb7463bfbb8',
    'authority_time_korean.sql': '5ee1178e142c758b3913d79f867401e9b5aeb5099e20a0257cb1ae91a01c4059',
}


def verify_source_file(fpath: str, expected_hash: str) -> bool:
    """Verify SHA256 of source file"""
    with open(fpath, 'rb') as f:
        content = f.read()
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash == expected_hash:
        print("  OK: {}: SHA256 verified".format(os.path.basename(fpath)))
        return True
    else:
        print("  ERROR: {}: SHA256 MISMATCH!".format(os.path.basename(fpath)))
        print("    Expected: {}".format(expected_hash))
        print("    Actual:   {}".format(actual_hash))
        return False


def parse_create_table(sql_content: str, table_name: str) -> Optional[str]:
    """Extract CREATE TABLE statement for a specific table"""
    pattern = 'CREATE TABLE `' + table_name + '`'
    pos = sql_content.find(pattern)
    if pos < 0:
        return None
    
    # Find the closing ) ENGINE...; or );
    # First try to find ) ENGINE which is more specific to CREATE TABLE
    end = sql_content.find(') ENGINE', pos)
    if end >= 0:
        # Find the ; after ENGINE
        end = sql_content.find(';', end)
        if end >= 0:
            return sql_content[pos:end+1]
    
    # Fallback: find );
    end = sql_content.find(');', pos)
    if end >= 0:
        return sql_content[pos:end+2]
    
    # Fallback: find the first ; after CREATE TABLE that's not in a comment
    end = sql_content.find(';', pos)
    if end >= 0:
        # Verify this is the end of CREATE TABLE by checking for next CREATE TABLE
        next_create = sql_content.find('CREATE TABLE', pos + 1)
        if next_create > 0 and next_create < end:
            # The ; we found is before the next CREATE TABLE, which is wrong
            # Search for the next ;
            end2 = sql_content.find(';', end + 1)
            if end2 >= 0:
                end = end2
        return sql_content[pos:end+1]
    
    return None


def parse_insert_statements(sql_content: str, table_name: str) -> List[str]:
    """Extract all INSERT INTO statements for a table, return list of value tuples"""
    insert_pattern = 'INSERT INTO `' + table_name + '` VALUES '
    pos = sql_content.find(insert_pattern)
    if pos < 0:
        return []
    
    end = sql_content.find(';', pos)
    if end < 0:
        return []
    
    insert_text = sql_content[pos:end]
    
    # Remove the INSERT INTO ... VALUES part
    values_start = insert_text.find('VALUES ') + 7
    values_text = insert_text[values_start:].strip()
    
    # Split by ),( to get individual rows
    # Handle the case where there's only one row (no ),( )
    if '),(' in values_text:
        rows = values_text.split('),(')
        # Fix first and last
        rows[0] = rows[0].lstrip('(')
        rows[-1] = rows[-1].rstrip(')')
        return rows
    else:
        # Single row
        row = values_text.strip()
        if row.startswith('(') and row.endswith(')'):
            row = row[1:-1]
        return [row]


def parse_sql_row(row_text: str) -> List:
    """Parse a single SQL row into Python values"""
    # Simple parser for MySQL VALUES format
    # Handles: NULL, numbers, 'strings', 'strings with \'quotes\''
    values = []
    current = ''
    in_string = False
    escape_next = False
    
    for char in row_text:
        if escape_next:
            current += char
            escape_next = False
        elif char == '\\' and in_string:
            escape_next = True
            current += char
        elif char == "'" and not escape_next:
            in_string = not in_string
            current += char
        elif char == ',' and not in_string:
            values.append(current.strip())
            current = ''
        else:
            current += char
    
    if current:
        values.append(current.strip())
    
    # Convert values
    result = []
    for v in values:
        v = v.strip()
        if v == 'NULL' or v == '':
            result.append(None)
        elif v.startswith("'") and v.endswith("'"):
            # String value - unescape
            s = v[1:-1]
            s = s.replace("''", "'").replace("\\'", "'").replace("\\\\", "\\")
            result.append(s)
        else:
            # Number
            try:
                if '.' in v:
                    result.append(float(v))
                else:
                    result.append(int(v))
            except ValueError:
                result.append(v)
    
    return result


def mysql_type_to_sqlite(mysql_type: str) -> str:
    """Convert MySQL column type to SQLite type"""
    mysql_type = mysql_type.upper()
    if 'TINYINT' in mysql_type or 'SMALLINT' in mysql_type or 'MEDIUMINT' in mysql_type or 'INT' in mysql_type:
        return 'INTEGER'
    elif 'BIGINT' in mysql_type:
        return 'INTEGER'
    elif 'CHAR' in mysql_type or 'TEXT' in mysql_type or 'ENUM' in mysql_type:
        return 'TEXT'
    elif 'FLOAT' in mysql_type or 'DOUBLE' in mysql_type or 'DECIMAL' in mysql_type:
        return 'REAL'
    elif 'DATE' in mysql_type or 'TIME' in mysql_type or 'DATETIME' in mysql_type:
        return 'TEXT'
    elif 'BLOB' in mysql_type:
        return 'BLOB'
    else:
        return 'TEXT'


def convert_create_table(mysql_ddl: str, table_name: str, prefix: str) -> str:
    """Convert MySQL CREATE TABLE to SQLite CREATE TABLE with prefix"""
    # Extract column definitions
    start = mysql_ddl.find('(')
    end = mysql_ddl.rfind(')')
    if start < 0 or end < 0:
        return ''
    
    columns_text = mysql_ddl[start+1:end]
    
    # Parse columns
    lines = [l.strip() for l in columns_text.split('\n') if l.strip()]
    columns = []
    primary_keys = []
    has_auto_increment_pk = False
    
    for line in lines:
        line = line.rstrip(',')
        upper_line = line.upper()
        
        # Skip table-level constraints and indexes
        if (upper_line.startswith('PRIMARY KEY') or 
            upper_line.startswith('KEY ') or 
            upper_line.startswith('INDEX ') or 
            upper_line.startswith('UNIQUE ') or
            upper_line.startswith('CONSTRAINT') or
            upper_line.startswith('FOREIGN KEY') or
            upper_line.startswith('CHECK ')):
            # Extract primary key columns if PRIMARY KEY
            if upper_line.startswith('PRIMARY KEY'):
                pk_match = re.search(r'PRIMARY KEY\s*\(([^)]+)\)', line, re.IGNORECASE)
                if pk_match:
                    pk_cols = [c.strip('` ') for c in pk_match.group(1).split(',')]
                    primary_keys.extend(pk_cols)
            continue
        
        # Column definition: `name` type [NOT NULL] [AUTO_INCREMENT] [DEFAULT ...]
        match = re.match(r'`(\w+)`\s+([^,\s]+)', line)
        if match:
            col_name = match.group(1)
            col_type = match.group(2)
            sqlite_type = mysql_type_to_sqlite(col_type)
            
            col_def = '`{}` {}'.format(col_name, sqlite_type)
            if 'NOT NULL' in upper_line:
                col_def += ' NOT NULL'
            if 'AUTO_INCREMENT' in upper_line:
                # Check if this column is also in PRIMARY KEY
                if col_name in primary_keys:
                    col_def += ' PRIMARY KEY'
                else:
                    col_def += ' PRIMARY KEY'  # SQLite uses PRIMARY KEY for auto increment
                    has_auto_increment_pk = True
            columns.append(col_def)
    
    # Build SQLite CREATE TABLE
    new_table_name = '{}{}'.format(prefix, table_name)
    col_defs = ',\n  '.join(columns)
    
    # Only add PRIMARY KEY if not already handled by AUTO_INCREMENT
    if primary_keys and not has_auto_increment_pk:
        pk_cols = ', '.join(['`{}`'.format(c) for c in primary_keys])
        col_defs += ',\n  PRIMARY KEY ({})'.format(pk_cols)
    
    return 'CREATE TABLE IF NOT EXISTS `{}` (\n  {}\n);'.format(new_table_name, col_defs)


def import_table(conn: sqlite3.Connection, table_name: str, create_sql: str, insert_rows: List[str], prefix: str) -> int:
    """Import a single table"""
    new_table_name = '{}{}'.format(prefix, table_name)
    
    # Create table
    sqlite_ddl = convert_create_table(create_sql, table_name, prefix)
    if not sqlite_ddl:
        print("    WARNING: Could not convert CREATE TABLE for {}".format(table_name))
        return 0
    
    try:
        conn.execute('DROP TABLE IF EXISTS `{}`'.format(new_table_name))
        conn.execute(sqlite_ddl)
    except Exception as e:
        print("    ERROR: Error creating table {}: {}".format(new_table_name, e))
        return 0
    
    # Insert data
    if not insert_rows:
        print("    {}: created (no data)".format(new_table_name))
        return 0
    
    # Parse first row to get column count
    first_row = parse_sql_row(insert_rows[0])
    col_count = len(first_row)
    placeholders = ', '.join(['?'] * col_count)
    
    insert_sql = 'INSERT INTO `{}` VALUES ({})'.format(new_table_name, placeholders)
    
    imported = 0
    for row_text in insert_rows:
        try:
            values = parse_sql_row(row_text)
            if len(values) == col_count:
                conn.execute(insert_sql, values)
                imported += 1
            else:
                print("    WARNING: Row column mismatch: expected {}, got {}".format(col_count, len(values)))
        except Exception as e:
            print("    ERROR: Error inserting row: {}".format(e))
            print("      Row: {}...".format(row_text[:100]))
    
    return imported


def main():
    print("=" * 60)
    print("T473: DDBC Time Authority Import")
    print("=" * 60)
    
    # Verify source files
    print("\nVerifying source files...")
    base_dir = r'data\dila_import\Authority-Databases-master\Authority-Databases-master\authority_time\SQL'
    all_ok = True
    for fname, expected_hash in SOURCE_HASHES.items():
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            if not verify_source_file(fpath, expected_hash):
                all_ok = False
        else:
            print("  WARNING: {}: NOT FOUND at {}".format(fname, fpath))
            all_ok = False
    
    if not all_ok:
        print("\nERROR: Source verification failed. Aborting.")
        return 1
    
    # Read main SQL file
    print("\nReading {}...".format(SQL_FILE))
    with open(SQL_FILE, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    print("  File size: {:,} chars, {:,} lines".format(len(content), len(content.splitlines())))
    
    # Connect to SQLite
    print("\nConnecting to {}...".format(DB_FILE))
    conn = sqlite3.connect(DB_FILE)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    
    try:
        # Process each table
        print("\nImporting tables...")
        total_rows = 0
        
        for table_name in TABLES:
            print("\n  {}".format(table_name))
            
            # Get CREATE TABLE
            create_sql = parse_create_table(content, table_name)
            if not create_sql:
                print("    WARNING: CREATE TABLE not found, skipping")
                continue
            
            # Get INSERT rows
            insert_rows = parse_insert_statements(content, table_name)
            print("    Found {} rows to import".format(len(insert_rows)))
            
            # Import
            imported = import_table(conn, table_name, create_sql, insert_rows, TABLE_PREFIX)
            print("    OK: Imported {} rows".format(imported))
            total_rows += imported
        
        conn.commit()
        print("\nImport complete! Total rows: {:,}".format(total_rows))
        
        # Verify
        print("\nVerification:")
        cursor = conn.cursor()
        for table_name in TABLES:
            new_name = '{}{}'.format(TABLE_PREFIX, table_name)
            try:
                cursor.execute('SELECT COUNT(*) FROM `{}`'.format(new_name))
                count = cursor.fetchone()[0]
                print("  {}: {:,} rows".format(new_name, count))
            except sqlite3.OperationalError:
                print("  {}: NOT CREATED (no CREATE TABLE in source)".format(new_name))
        
    finally:
        conn.close()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())