#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Database Backup Script
- Backup lineage.db to daoanh/data/backups/ at 21:00 daily
- Auto-cleanup: Delete backups older than 15 days
- Naming: lineage_YYYY-MM-DD.db (overwrite if exists same day)
"""

import shutil
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Config
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUPS_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "lineage.db"
RETENTION_DAYS = 15

print("[BACKUP] Daily Database Backup Script")
print("[CFG] Source DB: %s" % DB_PATH)
print("[CFG] Backup Dir: %s" % BACKUPS_DIR)
print("[CFG] Retention: %d days" % RETENTION_DAYS)

# === PHASE 1: Check if backup exists today ===
today = datetime.now().strftime("%Y-%m-%d")
backup_filename = "lineage_%s.db" % today
backup_path = BACKUPS_DIR / backup_filename

print("\n[PHASE1] Check existing backup")
print("[DATE] Today: %s" % today)

if backup_path.exists():
    print("[SKIP] Backup already exists: %s" % backup_filename)
    print("[INFO] Skipping backup (one per day rule)")
else:
    # === PHASE 2: Create backup directory ===
    print("\n[PHASE2] Create backup directory")
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        print("[OK] Backup directory ready: %s" % BACKUPS_DIR)
    except Exception as e:
        print("[ERR] Cannot create backup dir: %s" % str(e))
        sys.exit(1)

    # === PHASE 3: Create online backup using T387 helper ===
    print("\n[PHASE3] Online backup database (T387 safe)")
    try:
        if not DB_PATH.exists():
            print("[ERR] Source DB not found: %s" % DB_PATH)
            sys.exit(1)

        # Use T387 safe online backup helper instead of shutil.copy2
        from scripts.db_safe_backup import backup_to
        today = datetime.now().strftime("%Y-%m-%d")
        backup_filename = "lineage_%s.db" % today
        backup_path = BACKUPS_DIR / backup_filename

        # Online backup (không lock DB, Zero-RAM)
        print("[COPY] Creating online backup via sqlite3.Connection.backup()...")
        start_time = time.time()
        result = backup_to(str(DB_PATH), str(backup_path), compress=False)
        elapsed = time.time() - start_time

        if result:
            # Verify
            if backup_path.exists():
                backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
                print("[OK] Online backup created: %.1f MB (%.1f seconds)" % (backup_size_mb, elapsed))
            else:
                print("[ERR] Backup file not created after helper call")
                sys.exit(1)
        elif '--i-know-server-is-stopped' in sys.argv:
            print("[WARN] Online backup failed → legacy copy (server stopped confirmed)")
            shutil.copy2(str(DB_PATH), str(backup_path))
            elapsed = time.time() - start_time
            if backup_path.exists():
                backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
                print("[OK] Legacy backup created: %.1f MB (%.1f seconds)" % (backup_size_mb, elapsed))
            else:
                print("[ERR] Legacy backup also failed")
                sys.exit(1)
        else:
            print("[ERR] Online backup failed. Không copy file thô khi server còn chạy — "
                  "dừng app.py rồi thêm --i-know-server-is-stopped.")
            sys.exit(1)
    except Exception as e:
        print("[ERR] Backup failed: %s" % str(e))
        sys.exit(1)

# === PHASE 4: Cleanup old backups ===
print("\n[PHASE4] Cleanup old backups (>%d days)" % RETENTION_DAYS)
try:
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    cutoff_timestamp = cutoff_date.timestamp()

    deleted_count = 0
    deleted_size_mb = 0

    for backup_file in sorted(BACKUPS_DIR.glob("lineage_*.db")):
        file_mtime = backup_file.stat().st_mtime
        file_age_days = (datetime.now() - datetime.fromtimestamp(file_mtime)).days

        if file_mtime < cutoff_timestamp:
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            try:
                backup_file.unlink()
                print("[DELETE] %s (%d days old, %.1f MB)" %
                      (backup_file.name, file_age_days, file_size_mb))
                deleted_count += 1
                deleted_size_mb += file_size_mb
            except Exception as e:
                print("[WARN] Cannot delete %s: %s" % (backup_file.name, str(e)))

    if deleted_count > 0:
        print("[OK] Deleted %d old backups (%.1f MB freed)" % (deleted_count, deleted_size_mb))
    else:
        print("[INFO] No backups older than %d days" % RETENTION_DAYS)
except Exception as e:
    print("[WARN] Cleanup error: %s" % str(e))

# === PHASE 5: Summary ===
print("\n[PHASE5] Summary")
try:
    # List recent backups
    backups = sorted(BACKUPS_DIR.glob("lineage_*.db"), reverse=True)[:5]
    print("[RECENT] Latest %d backups:" % len(backups))
    for bf in backups:
        size_mb = bf.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(bf.stat().st_mtime)
        print("  - %s (%.1f MB, %s)" % (bf.name, size_mb, mtime.strftime("%Y-%m-%d %H:%M")))

    total_backups = len(list(BACKUPS_DIR.glob("lineage_*.db")))
    total_size_mb = sum(bf.stat().st_size for bf in BACKUPS_DIR.glob("lineage_*.db")) / (1024 * 1024)
    print("[TOTAL] %d backups, %.1f MB" % (total_backups, total_size_mb))
except Exception as e:
    print("[WARN] Summary error: %s" % str(e))

print("\n[DONE] Backup complete")
print("[TIME] %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
