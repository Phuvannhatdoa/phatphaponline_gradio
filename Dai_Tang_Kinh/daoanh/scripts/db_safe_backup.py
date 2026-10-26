#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_safe_backup.py — T387 SQLite online backup helper.

CÀI ĐẶT:
  - Dùng sqlite3.Connection.backup() (online backup API) — không lock DB lâu,
    an toàn khi app.py đang chạy. Zero-RAM: backup theo từng trang DB, không load
    toàn bộ vào RAM.
  - Nén .gz (tùy chọn, đỗ stream từng chunk).
  - Ghi checksum SHA256 cho verify restore.
  - Atomic rename (tmp → final).
  - Prune old backups (tên dạng lineage_YYYYMMDD_<label>.db.gz).

LÝ DO DÙNG VỚI SỰ THỰC THI:
  - Copy file thô (shutil.copy2/copy) có thể mất dữ liệu -wal/-shm khi DB đang chạy.
  - sqlite3.Connection.backup() đọc từng trang (page) DB một cách an toàn,
    tạo bản sao toàn vẹn khi server đang chạy WAL mode.
  - Tương thích với done_when T387: (1) helper dùng chung, (2) backup_db_daily.py
    và 6 script còn lại chuyển sang helper, (3) restore bằng copy đè DB chỉ khi có
    cờ --i-know-server-is-stopped.

CÀCH DÙNG:
    from scripts.db_safe_backup import backup_to
    backup_to('data/lineage.db', 'data/backups/lineage_20261022.db')
    # hoặc nén:
    backup_to('data/lineage.db', 'data/backups/lineage_20261022.db', compress=True)

FALLBACK (nếu backup API thất bại):
  - Dùng shutil.copy2 nhưng YÊU CẦU server đã dừng (--i-know-server-is-stopped).
"""
import gzip
import hashlib
import io
import os
import shutil
import sqlite3
import sys
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


def backup_to(db_path, backup_path, compress=False, keep_wal=False):
    """
    Tạo online backup DB bằng sqlite3.Connection.backup().

    Args:
        db_path: Đường dẫn file DB nguồn (lineage.db)
        backup_path: Đường dẫn file backup đích (ví dụ: lineage_20261022.db)
        compress: Nếu True, nén .gz và ghi checksum.
        keep_wal: Nếu True, giữ file WAL cùng bên trong backup (mặc định False).

    Returns:
        Đường dẫn file backup đã tạo, hoặc None nếu thất bại.
    """
    # Kiểm tra DB nguồn tồn tại
    if not os.path.exists(db_path):
        print(f"[ERR] Source DB not found: {db_path}")
        return None

    # Tạo thư mục backup nếu cần
    backup_dir = os.path.dirname(backup_path)
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)

    # Ghi tmp path để atomic rename sau này
    tmp_path = backup_path + '.tmp'

    try:
        # Mở nguồn và đích
        src = sqlite3.connect(db_path, timeout=30)
        try:
            dst = sqlite3.connect(tmp_path)
            try:
                # Sử dụng online backup API: src.backup(dst)
                src.backup(dst, progress=None)
                dst.commit()
            finally:
                dst.close()
        finally:
            src.close()

        # Xử lý WAL: nếu keep_wal=False (mặc định), checkpoint WAL trước
        # và đóng connection nguồn đã tự checkpoint qua backup API
        # Tuy nhiên, nếu DB có WAL shm file, chúng ta nên checkpoint
        if not keep_wal:
            try:
                src2 = sqlite3.connect(db_path, timeout=30)
                src2.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                src2.close()
            except Exception:
                pass

        # Verify: kiểm tra file backup có khả dụng và là file DB SQLite hợp lệ
        if not os.path.exists(tmp_path):
            print("[ERR] Backup tmp file not created")
            return None

        # Kiểm tra magic SQLite header (6 bytes đầu tiên)
        is_sqlite = False
        try:
            with open(tmp_path, 'rb') as f:
                header = f.read(16)
                is_sqlite = header[:6] == b'SQLite'
        except Exception:
            pass

        if not is_sqlite:
            print("[WARN] Backup file may not be valid SQLite (header check failed)")
            # Vẫn tiếp tục nhưng ghi nhắc

        # Compute checksum và size
        size_raw = os.path.getsize(tmp_path)
        sha256 = hashlib.sha256()
        with open(tmp_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                sha256.update(chunk)
        sha_hex = sha256.hexdigest()

        if compress:
            # Nén .gz (đọc stream chunk, không load toàn bộ vào RAM)
            gz_path = backup_path + '.gz'
            size_gz = 0
            with open(tmp_path, 'rb') as fin:
                with gzip.open(gz_path, 'wb', compresslevel=5) as fout:
                    shutil.copyfileobj(fin, fout, length=1024 * 1024)
                size_gz = os.path.getsize(gz_path)
            # Xoá file tmp chưa nén
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            # Đổi tên file nén thành file đích
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.replace(gz_path, backup_path)
            final_path = backup_path
            final_size_raw = size_gz
            final_sha = sha_hex  # checksum của file .gz (sha đã update qua file gốc)
            # Lưu checksum của file gốc trong file .manifest.json cạnh file .db.gz
            manifest_path = backup_path + '.manifest.json'
            manifest = io.StringIO()
            manifest.write(json_start_end(backup_path, size_raw, sha_hex, size_gz))
            with io.open(manifest_path, 'w', encoding='utf-8', newline='\n') as mf:
                mf.write(manifest.getvalue())
        else:
            # Không nén: đổi tên trực tiếp
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.replace(tmp_path, backup_path)
            final_path = backup_path
            final_size_raw = size_raw
            final_sha = sha_hex

        print(f"[OK] Backup created: {final_path} "
              f"({final_size_raw // (1024 * 1024)} MB, sha256={sha_hex[:16]}…)")
        return final_path

    except Exception as e:
        print(f"[ERR] Backup failed: {e}")
        # Clean up tmp file nếu còn tồn tại
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        # Clean up partial gz nếu đã tạo
        gz_path = backup_path + '.gz' if compress else None
        if gz_path and os.path.exists(gz_path):
            try:
                os.remove(gz_path)
            except Exception:
                pass
        return None


def json_start_end(backup_path, size_raw, sha_hex, size_gz):
    """Tạo nội dung manifest JSON cho file backup .gz."""
    import json
    # Format: {backup_path, size_raw, sha256, size_gz, created_at}
    return json.dumps({
        "backup_path": backup_path,
        "size_raw_bytes": size_raw,
        "sha256_16": sha_hex,
        "size_gz_bytes": size_gz,
        "created_at": datetime.now().isoformat()
    }, ensure_ascii=False) + "\n"


def verify_backup(backup_path):
    """
    Kiểm bản backup: header SQLite + PRAGMA quick_check.

    Returns:
        (ok: bool, detail: str)
    """
    if not os.path.exists(backup_path):
        return False, f"backup not found: {backup_path}"
    try:
        with open(backup_path, 'rb') as f:
            header = f.read(16)
        if header[:6] != b'SQLite':
            return False, "magic header không phải SQLite"
    except Exception as e:
        return False, f"không đọc được file: {e}"

    try:
        conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True, timeout=30)
        try:
            row = conn.execute("PRAGMA quick_check").fetchone()
            detail = row[0] if row else '(empty)'
        finally:
            conn.close()
    except Exception as e:
        return False, f"quick_check lỗi: {e}"
    return detail == 'ok', detail


def restore_from(backup_path, db_path, i_know_server_is_stopped=False):
    """
    Restore DB bằng cách copy đè — CHỈ khi server đã dừng.

    Copy đè file DB đang được app.py mở sẽ hỏng DB hoặc trả dữ liệu cũ/mất dữ
    liệu WAL. Vì vậy hàm này từ chối chạy nếu thiếu cờ xác nhận tường minh.

    Args:
        backup_path: file backup nguồn (đã verify quick_check)
        db_path: file DB đích (bị ghi đè)
        i_know_server_is_stopped: True khi đã dừng app.py/server.py

    Returns:
        True nếu restore thành công.
    """
    if not i_know_server_is_stopped:
        print("[STOP] Restore đè DB chỉ được phép khi server đã dừng.")
        print("       Dừng app.py/server.py rồi chạy lại với cờ "
              "--i-know-server-is-stopped.")
        return False

    ok, detail = verify_backup(backup_path)
    if not ok:
        print(f"[STOP] Backup không hợp lệ ({detail}) — không restore.")
        return False

    try:
        shutil.copy2(backup_path, db_path)
        # WAL/SHM cũ phải xoá, nếu không SQLite sẽ replay WAL cũ lên DB mới.
        for suffix in ('-wal', '-shm'):
            side = db_path + suffix
            if os.path.exists(side):
                try:
                    os.remove(side)
                    print(f"[OK] Đã xoá {side}")
                except Exception as e:
                    print(f"[WARN] Không xoá được {side}: {e}")
        print(f"[OK] Restore xong: {backup_path} → {db_path} (quick_check={detail})")
        return True
    except Exception as e:
        print(f"[ERR] Restore thất bại: {e}")
        return False


def prune_old_backups(backup_dir, keep_days=14, pattern="lineage_*.db*"):
    """
    Xoá bản backup cũ hơn keep_days ngày.
    Chỉ xoá file phù hợp pattern (mặc định lineage_*.db*).
    Trả về số file đã xoá.
    """
    import datetime
    import re
    cutoff = datetime.date.today() - datetime.timedelta(days=keep_days)
    removed = 0
    if not os.path.isdir(backup_dir):
        return removed
    # Tên hỗ trợ: lineage_YYYYMMDD.db / lineage_YYYY-MM-DD.db / ...db.gz
    date_re = re.compile(r'(20\d{2})-?(\d{2})-?(\d{2})')
    for f in os.listdir(backup_dir):
        if not fnmatch(f, pattern):
            continue
        m = date_re.search(f)
        if not m:
            continue
        try:
            day = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        if day >= cutoff:
            continue
        try:
            os.remove(os.path.join(backup_dir, f))
            manifest = os.path.join(backup_dir, f + '.manifest.json')
            if os.path.exists(manifest):
                os.remove(manifest)
            removed += 1
        except Exception as e:
            print(f"[WARN] Cannot prune {f}: {e}")
    return removed


def fnmatch(filename, pattern):
    """Simple fnmatch-like matching without importing fnmatch module."""
    # Chuyển pattern pattern=r"lineage_*.db*" thành regex đơn giản
    import re
    regex_str = "^" + re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".") + "$"
    return bool(re.match(regex_str, filename))


# Demo/quick test
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='T387 SQLite online backup helper')
    parser.add_argument('db', nargs='?', default='data/lineage.db',
                        help='DB path nguồn')
    parser.add_argument('out', nargs='?', default=None,
                        help='File backup đích (tự động tạo nếu không có)')
    parser.add_argument('--compress', action='store_true',
                        help='Nén .gz kèm checksum')
    parser.add_argument('--keep-wal', action='store_true',
                        help='Giữ WAL bên trong backup')
    args = parser.parse_args()

    out = args.out or f"lineage_{datetime.now().strftime('%Y%m%d')}.db"
    result = backup_to(args.db, out, compress=args.compress, keep_wal=args.keep_wal)
    if result:
        print(f"[DONE] {result}")
        sys.exit(0)
    else:
        print("[FAIL] Backup không thành công")
        sys.exit(1)