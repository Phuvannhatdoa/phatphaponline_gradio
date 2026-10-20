#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_backup.py — T116 D-Ops O1 (ráspec6 2026-09-09).

Sao lưu daily database snapshot của lineage.db cho lớp Bảo mật/Disaster Recovery.

Cơ chế (bài học T58 — KHÔNG dùng wal_checkpoint khi server đang chạy):
  - Dùng sqlite3.Connection.backup() (online backup API): đọc-ghi an toàn, KHÔNG lock DB lâu,
    an toàn kể cả khi app.py đang chạy. Zero-RAM: backup theo từng trang DB, không load toàn bộ.
  - Nén .gz.
  - Giữ N=14 ngày gần nhất (mặc định), tự xoá snapshot cũ hơn.
  - Ghi 1 dòng append-only vào docs/OPS_LOG.md (provenance: kích thước, trang, checksum).

Idempotent. An toàn chạy nhiều lần trong ngày (ghi đè cùng tên file).
Read-only đối với lineage.db: không nên mở connection mới tới DB này để ghi.

Cron (đêm 0 giờ):
  0 2 * * * cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh && python scripts/daily_backup.py >> data/backup.log 2>&1
"""
import gzip
import hashlib
import io
import os
import shutil
import sqlite3
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
SNAP_DIR = os.path.join(BASE_DIR, 'data', 'snap')
OPS_LOG = os.path.join(BASE_DIR, 'docs', 'OPS_LOG.md')

KEEP_DAYS = 14


def _prune_old_snapshots(keep_days):
    """Xoá snapshot .db.gz cũ hơn keep_days ngày (tên dạng lineage_YYYYMMDD.db.gz)."""
    import datetime
    cutoff = datetime.date.today() - datetime.timedelta(days=keep_days)
    removed = []
    if not os.path.isdir(SNAP_DIR):
        return removed
    for f in os.listdir(SNAP_DIR):
        if not f.startswith('lineage_') or not f.endswith('.db.gz'):
            continue
        try:
            day = datetime.datetime.strptime(f[len('lineage_'):len('lineage_') + 8], '%Y%m%d').date()
            if day < cutoff:
                os.remove(os.path.join(SNAP_DIR, f))
                removed.append(f)
        except (ValueError, OSError):
            continue
    return removed


def main():
    if not os.path.isfile(DB_PATH):
        print(f"[ERR] Không tìm thấy DB: {DB_PATH}")
        sys.exit(1)
    os.makedirs(SNAP_DIR, exist_ok=True)

    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    tmp_gz = os.path.join(SNAP_DIR, f'lineage_{today}.db.gz.tmp')
    final_gz = os.path.join(SNAP_DIR, f'lineage_{today}.db.gz')

    # 1) online backup vào file tạm (không nén)
    tmp_db = os.path.join(SNAP_DIR, f'_tmp_{today}.db')
    src = sqlite3.connect(DB_PATH, timeout=30)
    try:
        dst = sqlite3.connect(tmp_db)
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()

    # 2) nén .gz (đọc stream từng chunk, không load toàn bộ vào RAM)
    size_raw = os.path.getsize(tmp_db)
    with open(tmp_db, 'rb') as fin:
        with gzip.open(tmp_gz, 'wb', compresslevel=5) as fout:
            shutil.copyfileobj(fin, fout, length=1024 * 1024)
    size_gz = os.path.getsize(tmp_gz)

    # 3) checksum sha256 để verify restore
    h = hashlib.sha256()
    with open(tmp_gz, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    sha = h.hexdigest()

    # 4) atomic rename
    if os.path.exists(final_gz):
        os.remove(final_gz)
    os.replace(tmp_gz, final_gz)
    os.remove(tmp_db)

    # 5) prune các snapshot cũ
    removed = _prune_old_snapshots(KEEP_DAYS)

    # 6) verify: magic gzip (raw bytes) + nội dung giải nén mở đầu bằng header SQLite
    with open(final_gz, 'rb') as f:
        raw_head = f.read(4)
    ok_gzip = raw_head[:2] == b'\x1f\x8b' and len(raw_head) == 4
    ok_db = False
    with gzip.open(final_gz, 'rb') as f:
        dec = f.read(16)
        ok_db = dec[:6] == b'SQLite'
    ok = ok_gzip and ok_db

    # 7) append OPS_LOG.md
    date_iso = datetime.date.today().isoformat()
    line = (f"| {date_iso} | {os.path.basename(final_gz)} | {size_raw} | {size_gz} | "
            f"`{sha[:16]}~` | {'OK' if ok else 'FAIL'} | prune={','.join(removed) if removed else '-'} |")
    if os.path.isfile(OPS_LOG):
        with io.open(OPS_LOG, encoding='utf-8') as f:
            content = f.read()
    else:
        content = ("# OPS_LOG — Vận hành Đạo Ảnh (T116 D-Ops)\n\n"
                   "Append-only. Bảng: Ngày | Snapshot | Bytes raw | Bytes gz | SHA256 | Verify | Prune:\n\n"
                   "| Ngày | Snapshot | Raw bytes | Gz bytes | SHA256 | Verify | Prune |\n"
                   "|---|---|---|---|---|---|---|\n")
    if line not in content:
        content = content.rstrip() + "\n" + line + "\n"
        with io.open(OPS_LOG, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

    status = 'OK' if ok else 'FAIL'
    print(f"[OK] backup {final_gz} ({size_raw} -> {size_gz} bytes, sha256={sha[:16]}…) verify={status}, prune={len(removed)} file")
    if not ok:
        sys.exit(2)


if __name__ == '__main__':
    main()