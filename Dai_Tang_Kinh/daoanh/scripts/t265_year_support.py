"""
T265 — Kế hoạch H3 year-support (phê chuẩn 2026-10-08).

Các lệnh (chạy ở thư mục daoanh/):
    python -X utf8 scripts/t265_year_support.py sample   # Bước 0: lấy mẫu, CHỈ ĐỌC
    python -X utf8 scripts/t265_year_support.py backup   # sao lưu DB trước khi ghi
    python -X utf8 scripts/t265_year_support.py apply-b  # tạo bảng + gắn era_range cho nhóm B
    python -X utf8 scripts/t265_year_support.py status   # đếm trạng thái, CHỈ ĐỌC

Quy tắc:
- Bảng mới `timeline_year_support` là bổ sung (additive). Không sửa bảng `place_timeline_events`.
- Hoàn tác: `DROP TABLE timeline_year_support` hoặc khôi phục từ file backup.
- `apply-b` ghi trong MỘT transaction: lỗi giữa chừng thì rollback toàn bộ.
- Không đổi cột `year` và không chạy git.
"""
import csv
import random
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent            # daoanh/
DB = ROOT / "data" / "lineage.db"
TSV = ROOT / "docs" / "evidence" / "2026-10-08_T263_h3_conflicts.tsv"
SAMPLE_OUT = ROOT / "docs" / "evidence" / "2026-10-08_T265_sample_step0.tsv"
BACKUP_DIR = ROOT / "data" / "backups"
DECIDED_BY = "admin-phe-chuan-T265-2026-10-08"
STATUSES = ("era_range", "corrected", "review")

DDL = """
CREATE TABLE IF NOT EXISTS timeline_year_support (
    event_id    INTEGER PRIMARY KEY,           -- place_timeline_events.id
    dila_id     TEXT NOT NULL,
    year        INTEGER,                        -- năm đang lưu tại thời điểm quyết định
    status      TEXT NOT NULL CHECK (status IN ('era_range','corrected','review')),
    reason      TEXT NOT NULL,
    decided_by  TEXT NOT NULL,
    decided_at  TEXT NOT NULL
);
"""


def read_conflicts():
    with TSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def ro_conn():
    return sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)


def match_events(con, rows):
    """
    Gắn mỗi cặp (dila_id, year) của TSV với mọi id trong place_timeline_events.

    Một cặp có thể khớp nhiều id khi cùng một sự kiện được lưu từ nhiều nguồn
    (ví dụ wikidata và wikidata_p571). Đó là CÙNG một khẳng định, nên quyết định
    áp dụng cho tất cả id, không chọn một. TSV cũng có thể lặp cùng cặp, nên gom lại.
    """
    pairs = {}
    for r in rows:
        pairs.setdefault((r["dila_id"], int(r["year"])), r)
    matched, missing = [], []
    for (dila_id, year), r in pairs.items():
        ids = [i[0] for i in con.execute(
            "SELECT id FROM place_timeline_events WHERE dila_id = ? AND year = ? ORDER BY id",
            (dila_id, year),
        ).fetchall()]
        if not ids:
            missing.append(r)
        for event_id in ids:
            matched.append((event_id, r))
    return matched, missing


def cmd_sample():
    rows = read_conflicts()
    random.seed(20261008)  # cố định để có thể lặp lại
    out = []
    with ro_conn() as con:
        for g in ("B", "C", "A"):
            pool = [r for r in rows if r["group"] == g]
            for r in random.sample(pool, min(10, len(pool))):
                ev = con.execute(
                    "SELECT id, event_type, label_vi, label_zh, source, source_ref FROM place_timeline_events "
                    "WHERE dila_id = ? AND year = ? LIMIT 1",
                    (r["dila_id"], int(r["year"])),
                ).fetchone()
                out.append({
                    "group": g,
                    "dila_id": r["dila_id"],
                    "year": r["year"],
                    "r_derived": r["r_derived"],
                    "era_name": r["era_name"],
                    "ghi_chu": r["ghi_chu"],
                    "event_id": ev[0] if ev else "",
                    "event_type": ev[1] if ev else "",
                    "label_vi": ev[2] if ev else "",
                    "label_zh": ev[3] if ev else "",
                    "source": ev[4] if ev else "",
                    "source_ref": ev[5] if ev else "",
                    "kiem_tra_thu_cong": "",  # người rà điền: ĐÚNG / SAI / CẦN_NGUỒN
                })
    with SAMPLE_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(out)
    print(f"Bước 0: {len(out)} dòng mẫu (10/nhóm) -> {SAMPLE_OUT}")
    return 0


def cmd_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = BACKUP_DIR / f"lineage.T265-pre-support-{stamp}.db"
    src = sqlite3.connect(DB)
    dest = sqlite3.connect(dst)
    with dest:
        src.backup(dest)  # sao lưu nhất quán, an toàn với DB đang mở
    dest.close()
    src.close()
    print(f"Backup: {dst} ({dst.stat().st_size:,} bytes)")
    return 0


def apply_group(group, status, reason_fn):
    """Ghi quyết định `status` cho mọi id khớp của một nhóm, trong MỘT transaction."""
    rows = [r for r in read_conflicts() if r["group"] == group]
    con = ro_conn()
    matched, missing = match_events(con, rows)
    con.close()
    pairs = len({(r["dila_id"], r["year"]) for r in rows})
    print(f"Nhóm {group}: {len(rows)} dòng TSV · {pairs} cặp (dila_id, năm) · {len(matched)} id trong DB")
    if missing:
        print(f"DỪNG: {len(missing)} cặp không tìm thấy trong DB. Không ghi gì.")
        for r in missing[:5]:
            print("  thiếu:", r["dila_id"], r["year"])
        return 2

    now = datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(DB)
    try:
        con.execute("BEGIN")
        con.execute(DDL)
        for event_id, r in matched:
            con.execute(
                "INSERT OR REPLACE INTO timeline_year_support "
                "(event_id, dila_id, year, status, reason, decided_by, decided_at) VALUES (?,?,?,?,?,?,?)",
                (event_id, r["dila_id"], int(r["year"]), status, reason_fn(r), DECIDED_BY, now),
            )
        con.execute("COMMIT")
    except Exception as e:
        con.execute("ROLLBACK")
        print("LỖI, đã rollback toàn bộ:", e)
        return 1
    finally:
        con.close()
    print(f"Đã ghi {len(matched)} dòng {status} (nhóm {group}) vào timeline_year_support (1 transaction).")
    return cmd_status()


def cmd_apply_b():
    return apply_group(
        "B", "era_range",
        lambda r: f"Năm {r['year']} nằm trong niên hiệu {r['era_name']} {r['era_span']} mà ghi chú nêu; "
                  f"chỉ chứng minh niên hiệu, không chứng minh đúng năm (T265 lô B).",
    )


def cmd_apply_a():
    """Lô A: không dòng nào có nguồn độc lập để sửa năm nên toàn bộ gắn `review`."""
    def reason(r):
        return (f"Năm {r['year']} nằm ngoài mọi niên hiệu đã biết (ghi chú suy ra {r['r_derived']}, "
                f"niên hiệu {r['era_name']} {r['era_span']}). Không có nguồn độc lập để sửa năm; "
                f"năm lưu có thể là điểm giữa triều đại (T265 lô A, review).")
    return apply_group("A", "review", reason)


def cmd_apply_c():
    return apply_group(
        "C", "review",
        lambda r: f"Năm {r['year']} thuộc niên hiệu khác {r['era_name']} ({r['era_span']}); ghi chú có thể gộp "
                  f"nhiều sự kiện. Cần người rà và tách, không sửa năm tự động (T265 lô C, duyệt theo hướng review).",
    )


def cmd_status():
    con = ro_conn()
    tbl = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timeline_year_support'").fetchone()
    if not tbl:
        print("Bảng timeline_year_support: CHƯA CÓ")
        con.close()
        return 0
    rows = con.execute(
        "SELECT status, COUNT(*) FROM timeline_year_support GROUP BY status ORDER BY status"
    ).fetchall()
    con.close()
    print("timeline_year_support:", rows or "(rỗng)")
    return 0


def main(argv):
    cmds = {"sample": cmd_sample, "backup": cmd_backup, "apply-b": cmd_apply_b,
            "apply-c": cmd_apply_c, "apply-a": cmd_apply_a, "status": cmd_status}
    if len(argv) != 2 or argv[1] not in cmds:
        print(__doc__)
        return 1
    return cmds[argv[1]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
