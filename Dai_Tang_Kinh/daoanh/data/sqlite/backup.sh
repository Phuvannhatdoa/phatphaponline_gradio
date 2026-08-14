#!/bin/bash
# Daily Backup Script for Buddhist SQLite Database
# Run via cron: 0 2 * * * /opt/.../backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
SOURCE="/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"
BACKUP_DIR="/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/backup"
LOG_DIR="/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite"

# Create backup
mkdir -p "$BACKUP_DIR"
cp "$SOURCE" "$BACKUP_DIR/buddhist_db_$DATE.sqlite"

# Keep only last 7 backups
cd "$BACKUP_DIR"
ls -t buddhist_db_*.sqlite | tail -n +8 | xargs -r rm

# Log
echo "[$(date)] Backup: buddhist_db_$DATE.sqlite" >> "$LOG_DIR/backup.log"

# Stats
SIZE=$(du -h "$BACKUP_DIR/buddhist_db_$DATE.sqlite" | cut -f1)
echo "[$(date)] Size: $SIZE" >> "$LOG_DIR/backup.log"