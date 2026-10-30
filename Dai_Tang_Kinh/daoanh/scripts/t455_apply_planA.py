#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T455 — phương án A: chuẩn hoá 259 tên (lô A 23 + lô C 236) + ghi chú 534 alias (lô B).

Usage:
  python -X utf8 scripts/t455_apply_planA.py --dry-run
  python -X utf8 scripts/t455_apply_planA.py --apply
  python -X utf8 scripts/t455_apply_planA.py --revert

Nguyên tắc:
- Additive: bảng lịch sử `people_name_vi_history` (mới) + UPDATE people.name_vi
- KHÔNG sửa people.name_zh ; KHÔNG đổi source_id
- Backup DB trước khi ghi ; idempotent (chạy lại không nhân bản)
"""
import argparse, csv, datetime, os, re, shutil, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
DB = os.path.join(DAO, "data", "lineage.db")
BACKUP_DIR = os.path.join(DAO, "data", "backups")
PROP = os.path.join(DAO, "docs", "sessions", "2026-10-30-t455-apply", "t455_proposal_planA.csv")
BATCH_ID = "T455-planA-20261030"

# 1 dòng phải tra tay: Cloud để nguyên chữ Hán + bỏ mất phần đầu tên
HAND_CURATED = {
    "A000142": {
        "name_vi_new": "Chân Tĩnh Thiên Trác",
        "reason": "Cloud con chu Han (Thien 頙) va mat phan 'Chan Tinh' - sua tay: giu ZQ + 頙 doc 'Trac'",
    },
}


def to_title(s):
    s = s.replace("-", " ").replace("–", " ").replace("—", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return " ".join((w[0].upper() + w[1:]) for w in s.split(" ") if w)


def load_plan():
    rows = []
    with open(PROP, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            lot, pid = r["lot"], r["person_id"]
            action, reason = r["action"], r["reason"]
            new = r["name_vi_new"]
            if pid in HAND_CURATED:
                h = HAND_CURATED[pid]
                new, reason, action = h["name_vi_new"], h["reason"], "updated"
            rows.append({
                "lot": lot, "person_id": pid, "old": r["name_vi_old_ZQ"],
                "new": new, "action": action, "reason": reason,
            })
    return rows


def open_db(readonly=False):
    if readonly:
        return sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    return sqlite3.connect(DB)


def dry_run():
    rows = load_plan()
    conn = open_db(True)
    print("=== DRY-RUN T455 phương án A ===")
    print("tổng dòng kế hoạch:", len(rows))
    by = {}
    for r in rows:
        by[r["action"]] = by.get(r["action"], 0) + 1
    for k, v in sorted(by.items()):
        print("   %-12s : %d" % (k, v))

    print()
    print("=== kiểm tra tồn tại trong people ===")
    missing = []
    for r in rows:
        got = conn.execute("SELECT name_vi FROM people WHERE id = ?", (r["person_id"],)).fetchone()
        if got is None:
            missing.append(r["person_id"])
        elif r["action"] == "updated" and got[0] != r["old"]:
            print("   ⚠ %-9s name_vi DB khác CSV: DB=%r CSV=%r" % (r["person_id"], got[0], r["old"]))
    print("   không tìm thấy trong people:", len(missing), missing[:5])

    print()
    print("=== entity_claims NAME source_id=5 cho các person này ===")
    n_claim = 0
    for r in rows:
        n = conn.execute(
            "SELECT COUNT(*) FROM entity_claims WHERE entity_id = ? AND claim_type = 'NAME' AND source_id = 5",
            (r["person_id"],)).fetchone()[0]
        n_claim += n
    print("   tổng claim NAME (source_id=5) liên quan:", n_claim,
          "→ không cần cập nhật claim" if n_claim == 0 else "→ CẦN cập nhật claim")

    print()
    print("=== trigger trên bảng people ===")
    tr = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='people'").fetchall()
    print("   ", tr if tr else "(không có trigger)")

    print()
    print("=== bảng lịch sử đã tồn tại? ===")
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    print("   people_name_vi_history:", "people_name_vi_history" in tables)

    print()
    print("=== 20 dòng sẽ UPDATE (mẫu) ===")
    n = 0
    for r in rows:
        if r["action"] == "updated":
            print("   %-9s %-24s → %s" % (r["person_id"], r["old"][:24], r["new"]))
            n += 1
            if n >= 20:
                break
    conn.close()
    print()
    print("DRY-RUN xong. Chưa ghi DB.")


def apply():
    rows = load_plan()
    upd = [r for r in rows if r["action"] == "updated"]
    keep = [r for r in rows if r["action"] != "updated"]

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bkp = os.path.join(BACKUP_DIR, "lineage_t455_%s.db" % ts)
    print("BACKUP:", bkp)
    shutil.copy2(DB, bkp)
    print("  size:", os.path.getsize(bkp))

    conn = open_db()
    conn.execute("PRAGMA foreign_keys=ON")
    print()
    print("=== CREATE bảng lịch sử (additive) ===")
    conn.execute("""CREATE TABLE IF NOT EXISTS people_name_vi_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NOT NULL,
        name_vi_old TEXT,
        name_vi_new TEXT,
        lot TEXT,
        action TEXT,
        reason TEXT,
        source_id INTEGER DEFAULT 5,
        batch_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pnvh_person ON people_name_vi_history(person_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pnvh_batch ON people_name_vi_history(batch_id)")
    print("   people_name_vi_history + 2 index OK")

    print()
    print("=== UPDATE people.name_vi (%d dòng) ===" % len(upd))
    changed = 0
    skipped = []
    for r in upd:
        cur = conn.execute(
            "UPDATE people SET name_vi = ? WHERE id = ? AND name_vi = ?",
            (r["new"], r["person_id"], r["old"]))
        if cur.rowcount:
            changed += cur.rowcount
        else:
            cur2 = conn.execute("SELECT name_vi FROM people WHERE id = ?", (r["person_id"],)).fetchone()
            skipped.append((r["person_id"], cur2[0] if cur2 else None))
    print("   UPDATE thực sự:", changed, "/", len(upd))
    if skipped:
        print("   BỎ QUA %d dòng (name_vi trong DB đã khác CSV — không ghi đè thay đổi của phiên khác):" % len(skipped))
        for pid, cur_v in skipped:
            print("      %s — DB hiện = %r" % (pid, cur_v))

    print()
    print("=== INSERT lịch sử (%d dòng) ===" % len(rows))
    ins = 0
    for r in rows:
        cur = conn.execute(
            "INSERT INTO people_name_vi_history "
            "(person_id, name_vi_old, name_vi_new, lot, action, reason, source_id, batch_id) "
            "VALUES (?,?,?,?,?,?,5,?)",
            (r["person_id"], r["old"], r["new"], r["lot"], r["action"], r["reason"], BATCH_ID))
        ins += cur.rowcount
    print("   INSERT:", ins)

    conn.commit()
    conn.close()
    print()
    print("APPLY xong. Batch:", BATCH_ID)
    print("Rollback: python -X utf8 scripts/t455_apply_planA.py --revert")
    print("Backup:", bkp)


def revert():
    conn = open_db()
    n = conn.execute("SELECT COUNT(*) FROM people_name_vi_history WHERE batch_id = ?", (BATCH_ID,)).fetchone()[0]
    print("=== REVERT batch", BATCH_ID, "===")
    print("số dòng lịch sử của batch:", n)
    rows = conn.execute(
        "SELECT person_id, name_vi_old FROM people_name_vi_history WHERE batch_id = ? AND action = 'updated'",
        (BATCH_ID,)).fetchall()
    restored = 0
    for pid, old in rows:
        cur = conn.execute("UPDATE people SET name_vi = ? WHERE id = ?", (old, pid))
        restored += cur.rowcount
    print("khôi phục name_vi:", restored)
    conn.execute("DELETE FROM people_name_vi_history WHERE batch_id = ?", (BATCH_ID,))
    conn.commit()
    conn.close()
    print("REVERT xong.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        dry_run()
    elif a.apply:
        apply()
    elif a.revert:
        revert()
    else:
        ap.print_help()
