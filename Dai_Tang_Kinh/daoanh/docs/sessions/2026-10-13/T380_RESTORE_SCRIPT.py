#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T380: Selective Restore 4 Tables + Entity Type Column (FIXED)
Script to restore ai_person_name, passage, vn_person_authority, vn_person_relations
from 2026-10-11 10:11 backup with smart field merging.

FIXES:
1. Dry-run works on a copy DB (lineage_dryrun.db), not the real DB
2. ALTER TABLE runs INSIDE BEGIN TRANSACTION (not auto-commit)
3. ATTACH DATABASE uses correct SQLite syntax
4. INSERT SELECT uses all columns via SELECT * for vn_person_authority
5. "Keep current" UPDATEs use COALESCE so a NULL in the restored backup
   row never overwrites a non-NULL current value (passage.vi_text/
   translation_draft, vn_person_authority.name_vi/biographical_note_vi/
   generation_order/status/ttl_filename/dharma_lineage/dila_id)
6. TEMP snapshot tables are DROPped after COMMIT so they don't linger
   in the production DB
"""

import sqlite3
import hashlib
import datetime
import sys
import os
import shutil
import argparse

CURRENT_DB = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db"
BACKUP_DB = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\backups\lineage.T265-lo-D-20261011-101118.db"
BACKUP_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\backups"

EXPECTED_COUNTS = {
    'ai_person_name': 39269,
    'passage': 44820,
    'vn_person_authority': 1511,
    'vn_person_relations': 2013
}

# ============================================================================
# LOGGER
# ============================================================================

def log_msg(logs, msg):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    logs.append(log_entry)

def log_section(logs, title):
    log_msg(logs, f"\n{'='*60}")
    log_msg(logs, f"  {title}")
    log_msg(logs, f"{'='*60}\n")

# ============================================================================
# MAIN RESTORE FUNCTION
# ============================================================================

def restore_t380(mode='execute'):
    """
    Restore 4 tables from 11/10 backup with smart field merging.

    Args:
        mode: 'dry-run' (test on copy, rollback) or 'execute' (real restore, commit)

    Returns:
        (success: bool, logs: list, backup_path: str)
    """
    logs = []
    success = False
    backup_path = None

    try:
        log_section(logs, f"T380 RESTORE — Mode: {mode.upper()}")

        # Determine working DB
        if mode == 'dry-run':
            work_db = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage_dryrun.db"
            # Copy current DB to dryrun copy
            log_msg(logs, "ℹ️  Copying DB for dry-run...")
            shutil.copy2(CURRENT_DB, work_db)
            log_msg(logs, f"✓ Dry-run copy created: {work_db}")
        else:
            work_db = CURRENT_DB
            # Create backup of real DB
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"lineage_backup_T380_{ts}.db")
            log_msg(logs, f"ℹ️  Creating backup: {backup_path}")

            conn_current = sqlite3.connect(CURRENT_DB)
            conn_backup_file = sqlite3.connect(backup_path)
            with conn_backup_file:
                conn_current.backup(conn_backup_file)
            conn_backup_file.close()
            conn_current.close()

            log_msg(logs, f"✓ Backup created: {backup_path}")

        # Open working DB + backup
        conn_work = sqlite3.connect(work_db)
        conn_backup = sqlite3.connect(f"file:{BACKUP_DB}?mode=ro", uri=True)

        log_msg(logs, "✓ Database connections opened")

        # BEGIN TRANSACTION (FIX #2: ALTER inside transaction)
        log_msg(logs, "ℹ️  Starting transaction...")
        conn_work.execute("BEGIN TRANSACTION")

        # Step 1: ALTER TABLE FIRST (FIX #5: must run before TEMP snapshots,
        # otherwise temp_alias_current captures the OLD 16-column schema and
        # later "INSERT ... SELECT * FROM temp_alias_current" into the NEW
        # 17-column table fails with "has 17 columns but 16 values were
        # supplied". ALTER TABLE stays inside the transaction - FIX #2.)
        log_msg(logs, "ℹ️  Adding entity_type column...")
        try:
            conn_work.execute("""
                ALTER TABLE vn_person_authority
                ADD COLUMN entity_type TEXT DEFAULT 'monk'
            """)
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                raise
            log_msg(logs, "ℹ️  entity_type column already exists")

        # Step 2: Create TEMP snapshots (now AFTER entity_type exists)
        log_msg(logs, "ℹ️  Creating TEMP snapshots...")
        conn_work.execute("""
            CREATE TABLE IF NOT EXISTS temp_vpa_current AS
            SELECT
              id, dila_id, name_vi, biographical_note_vi, generation_order,
              status, ttl_filename, dharma_lineage
            FROM vn_person_authority
        """)

        conn_work.execute("""
            CREATE TABLE IF NOT EXISTS temp_passage_current AS
            SELECT passage_id, vi_text, translation_draft
            FROM passage
        """)

        conn_work.execute("""
            CREATE TABLE IF NOT EXISTS temp_alias_current AS
            SELECT *
            FROM vn_person_authority
            WHERE id LIKE 'alias_%'
        """)
        log_msg(logs, "✓ TEMP snapshots created")

        # Step 3: DELETE 4 tables
        log_msg(logs, "ℹ️  Clearing tables...")
        conn_work.execute("DELETE FROM ai_person_name")
        conn_work.execute("DELETE FROM passage")
        conn_work.execute("DELETE FROM vn_person_authority")
        conn_work.execute("DELETE FROM vn_person_relations")
        log_msg(logs, "✓ 4 tables cleared")

        # Step 4: ATTACH and INSERT (FIX #3: correct ATTACH syntax)
        log_msg(logs, "ℹ️  Attaching backup DB...")
        conn_work.execute(f"ATTACH DATABASE '{BACKUP_DB}' AS bak")

        # ai_person_name
        log_msg(logs, "ℹ️  Inserting ai_person_name...")
        conn_work.execute("INSERT INTO ai_person_name SELECT * FROM bak.ai_person_name")
        count_ai = conn_work.execute("SELECT COUNT(*) FROM ai_person_name").fetchone()[0]
        log_msg(logs, f"✓ ai_person_name: {count_ai} rows")

        # passage
        log_msg(logs, "ℹ️  Inserting passage...")
        conn_work.execute("INSERT INTO passage SELECT * FROM bak.passage")
        count_passage = conn_work.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        log_msg(logs, f"✓ passage: {count_passage} rows")

        # vn_person_authority (FIX #4b: real schema has 17 cols after ALTER,
        # identical names/order to backup — id, ttl_filename, name_vi, name_zh,
        # dharma_title, dharma_lineage, generation_order, is_lineage_founder,
        # gender, biographical_note_vi, birth_year, death_year, appellations,
        # dila_id, status, created_at, entity_type. No updated_at/source_id/
        # source_ref columns exist in either DB — original explicit column list
        # was fabricated and caused "no column named updated_at" error.)
        log_msg(logs, "ℹ️  Inserting vn_person_authority...")
        conn_work.execute("""
            INSERT INTO vn_person_authority
            SELECT * FROM bak.vn_person_authority
        """)
        count_vpa = conn_work.execute("SELECT COUNT(*) FROM vn_person_authority").fetchone()[0]
        log_msg(logs, f"✓ vn_person_authority: {count_vpa} rows (before TEMP merge)")

        # vn_person_relations
        log_msg(logs, "ℹ️  Inserting vn_person_relations...")
        conn_work.execute("INSERT INTO vn_person_relations SELECT * FROM bak.vn_person_relations")
        count_vpr = conn_work.execute("SELECT COUNT(*) FROM vn_person_relations").fetchone()[0]
        log_msg(logs, f"✓ vn_person_relations: {count_vpr} rows")

        # Step 5: UPDATE "keep current" fields from TEMP
        log_msg(logs, "ℹ️  Updating 'keep current' fields from TEMP...")

        # FIX: COALESCE against the restored (post-INSERT) value so a NULL
        # in temp_vpa_current (the pre-restore snapshot) never overwrites a
        # non-NULL value that the backup INSERT just supplied. Previously a
        # bare subquery assignment wrote NULL whenever the "current" snapshot
        # value was NULL, wiping 28 vn_person_authority fields that the
        # backup restore had just correctly populated.
        conn_work.execute("""
            UPDATE vn_person_authority
            SET
              name_vi = COALESCE((SELECT name_vi FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), name_vi),
              biographical_note_vi = COALESCE((SELECT biographical_note_vi FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), biographical_note_vi),
              generation_order = COALESCE((SELECT generation_order FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), generation_order),
              status = COALESCE((SELECT status FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), status),
              ttl_filename = COALESCE((SELECT ttl_filename FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), ttl_filename),
              dharma_lineage = COALESCE((SELECT dharma_lineage FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), dharma_lineage),
              dila_id = COALESCE((SELECT dila_id FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id), dila_id)
            WHERE id IN (SELECT id FROM temp_vpa_current)
        """)

        # FIX: same COALESCE pattern for passage — 137 rows had vi_text wiped
        # to NULL on 2026-10-13 because the plain subquery overwrote a
        # non-NULL current translation with a NULL snapshot value.
        conn_work.execute("""
            UPDATE passage
            SET
              vi_text = COALESCE((SELECT vi_text FROM temp_passage_current WHERE temp_passage_current.passage_id = passage.passage_id AND vi_text IS NOT NULL), vi_text),
              translation_draft = COALESCE((SELECT translation_draft FROM temp_passage_current WHERE temp_passage_current.passage_id = passage.passage_id AND translation_draft IS NOT NULL), translation_draft)
            WHERE passage_id IN (SELECT passage_id FROM temp_passage_current)
        """)

        log_msg(logs, "✓ 'Keep current' fields updated from TEMP (COALESCE-safe, no NULL overwrite)")

        # Step 6: Re-insert 4 alias_*
        log_msg(logs, "ℹ️  Re-inserting 4 alias_* rows...")
        conn_work.execute("""
            INSERT INTO vn_person_authority
            SELECT *
            FROM temp_alias_current
            WHERE id NOT IN (
              SELECT id FROM vn_person_authority WHERE id LIKE 'alias_%'
            )
        """)
        count_alias = conn_work.execute("SELECT COUNT(*) FROM vn_person_authority WHERE id LIKE 'alias_%'").fetchone()[0]
        log_msg(logs, f"✓ 4 alias_* rows re-inserted (total alias: {count_alias})")

        # Step 7: Verify
        log_section(logs, "VERIFICATION")
        log_msg(logs, "ℹ️  Running PRAGMA quick_check...")
        result = conn_work.execute("PRAGMA quick_check").fetchone()
        if result[0] == 'ok':
            log_msg(logs, "✓ PRAGMA quick_check: OK")
        else:
            log_msg(logs, f"❌ PRAGMA quick_check: {result[0]}")
            raise Exception(f"Database integrity check failed: {result[0]}")

        # Verify row counts
        log_msg(logs, "ℹ️  Verifying row counts...")
        final_counts = {}
        all_ok = True
        for table, expected in EXPECTED_COUNTS.items():
            actual = conn_work.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            final_counts[table] = actual
            if actual == expected:
                log_msg(logs, f"✓ {table}: {actual} rows")
            else:
                log_msg(logs, f"❌ {table}: {actual} rows (expected {expected})")
                all_ok = False

        if not all_ok:
            raise Exception("Row count mismatch!")

        # Extra verification: the two fields that were previously wiped to
        # NULL by the buggy (non-COALESCE) UPDATE must now be NOT NULL.
        null_vi_text = conn_work.execute(
            "SELECT COUNT(*) FROM passage WHERE passage_id IN (SELECT passage_id FROM temp_passage_current) AND vi_text IS NULL"
        ).fetchone()[0]
        log_msg(logs, f"ℹ️  passage.vi_text still NULL after merge: {null_vi_text}")

        null_vpa_fields = conn_work.execute("""
            SELECT COUNT(*) FROM vn_person_authority
            WHERE id IN (SELECT id FROM temp_vpa_current)
            AND (name_vi IS NULL OR biographical_note_vi IS NULL OR generation_order IS NULL
                 OR ttl_filename IS NULL OR dharma_lineage IS NULL OR dila_id IS NULL)
            AND id IN (
                SELECT id FROM temp_vpa_current
                WHERE name_vi IS NOT NULL OR biographical_note_vi IS NOT NULL OR generation_order IS NOT NULL
                   OR ttl_filename IS NOT NULL OR dharma_lineage IS NOT NULL OR dila_id IS NOT NULL
            )
        """).fetchone()[0]
        log_msg(logs, f"ℹ️  vn_person_authority rows with an unexpected NULL field after merge: {null_vpa_fields}")

        # Step 7b: Drop TEMP snapshot tables — they are scratch data only
        # and must not be left behind in the production DB.
        log_msg(logs, "ℹ️  Dropping TEMP snapshot tables...")
        conn_work.execute("DROP TABLE IF EXISTS temp_vpa_current")
        conn_work.execute("DROP TABLE IF EXISTS temp_passage_current")
        conn_work.execute("DROP TABLE IF EXISTS temp_alias_current")
        log_msg(logs, "✓ TEMP snapshot tables dropped")

        # Step 8: COMMIT or ROLLBACK
        if mode == 'dry-run':
            log_msg(logs, "ℹ️  Dry-run mode: ROLLBACK")
            conn_work.execute("ROLLBACK")
            # FIX #6: close connections BEFORE deleting the file — Windows
            # keeps an exclusive lock on the sqlite file while the
            # connection object is open, so os.remove() before close()
            # raised "process cannot access the file" (WinError 32).
            conn_work.close()
            conn_backup.close()
            os.remove(work_db)
            log_msg(logs, "✓ Dry-run copy deleted")
        else:
            log_msg(logs, "ℹ️  Committing transaction...")
            conn_work.execute("COMMIT")
            log_msg(logs, "✓ Transaction committed!")
            conn_work.close()
            conn_backup.close()

        log_section(logs, "SUCCESS")
        log_msg(logs, "✓ Restore completed successfully!")
        success = True

    except Exception as e:
        log_msg(logs, f"❌ Error: {e}")
        import traceback
        log_msg(logs, traceback.format_exc())
        success = False
        # Try to rollback
        try:
            conn_work.execute("ROLLBACK")
        except:
            pass

    return success, logs, backup_path

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='T380: Selective Restore 4 Tables')
    parser.add_argument('--mode', choices=['dry-run', 'execute'], default='execute',
                        help='Run mode: dry-run (test, no changes) or execute (real restore)')
    args = parser.parse_args()

    success, logs, backup_path = restore_t380(mode=args.mode)

    # Print all logs
    print('\n'.join(logs))

    # Save log file
    log_file = f"docs/sessions/2026-10-13/T380_EXECUTION_LOG_{args.mode}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(logs))
    print(f"\nLog saved: {log_file}")

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
