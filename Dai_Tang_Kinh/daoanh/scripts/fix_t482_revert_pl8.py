# -*- coding: utf-8 -*-
"""
T482 QA reject fix (2026-10-28) — hoan tac dung du lieu test cua lan bam nut Pass
tren PL000000000008 luc 15:06:52 (chua duoc revert dung sau test truoc).

So voi backup data/backups/lineage_2026-10-28_catalog.db (tao TRUOC --apply t482),
3 diem lech duy nhat can sua cho DUNG 1 place_id PL000000000008:
  1. namevi_map_places.needs_review: hien tai=1 -> backup=0
  2. en_audit_log: xoa dong log_id=44054 (action='approve', editor=
     'nhatdoaphuvan@gmail.com', verification_status='verified') - dau vet phe duyet
     gia mang ten admin thuc, KHONG ton tai trong backup.
  3. entity_hub (entity_id=159167): status hien tai='verified' -> backup='active';
     updated_at hien tai='2026-10-28T15:06:52' -> backup='2026-08-16 15:24:45'

canonical_decision va vn_name_status: QA xac nhan da dung/sach, KHONG dong vao.

Chay trong 1 transaction (BEGIN/COMMIT, rollback neu loi). Co --dry-run (default)
va --apply. Khong dong vao gi khac ngoai 3 diem tren, chi cho PL000000000008 /
log_id=44054 / entity_id=159167.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "lineage.db"
BACKUP_PATH = BASE_DIR / "data" / "backups" / "lineage_2026-10-28_catalog.db"

PLACE_ID = "PL000000000008"
AUDIT_LOG_ID = 44054
ENTITY_ID = 159167

EXPECTED = {
    "namevi_map_places.needs_review": {"before": 1, "after": 0},
    "en_audit_log.log_id=44054": {"before": "EXISTS", "after": "DELETED"},
    "entity_hub.status": {"before": "verified", "after": "active"},
    "entity_hub.updated_at": {"before": "2026-10-28T15:06:52", "after": "2026-08-16 15:24:45"},
}


def fetch_state(conn):
    nv = conn.execute(
        "SELECT needs_review, vn_name_status FROM namevi_map_places WHERE dila_id=?",
        (PLACE_ID,),
    ).fetchone()
    audit = conn.execute(
        "SELECT log_id, action, editor, verification_status FROM en_audit_log WHERE log_id=?",
        (AUDIT_LOG_ID,),
    ).fetchone()
    hub = conn.execute(
        "SELECT entity_id, status, updated_at FROM entity_hub WHERE entity_id=?",
        (ENTITY_ID,),
    ).fetchone()
    return nv, audit, hub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Ghi thật (mac dinh la dry-run)")
    ap.add_argument("--revert", action="store_true",
                     help="Hoan tac fix nay (dua du lieu TRO LAI trang thai sai da bi sua) -- khong khuyen nghi")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"LOI: khong thay DB tai {DB_PATH}")
        sys.exit(1)
    if not BACKUP_PATH.exists():
        print(f"LOI: khong thay backup tai {BACKUP_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    print(f"== Trang thai TRUOC khi sua (PL={PLACE_ID}, log_id={AUDIT_LOG_ID}, entity_id={ENTITY_ID}) ==")
    nv, audit, hub = fetch_state(conn)
    print("namevi_map_places:", dict(nv) if nv else None)
    print("en_audit_log:", dict(audit) if audit else None)
    print("entity_hub:", dict(hub) if hub else None)

    if args.revert:
        print("\n--revert: dua du lieu TRO LAI trang thai sai (khong khuyen nghi) -- chua implement, dung lai.")
        conn.close()
        sys.exit(1)

    # Kiem tra truoc khi sua: dung dung 3 diem QA da neu, khong dong vao gi khac.
    problems = []
    if not nv or nv["needs_review"] != 1:
        problems.append(f"namevi_map_places.needs_review hien tai != 1 (la {nv['needs_review'] if nv else None}) -- co the da duoc sua roi, dung lai de tranh ghi de nham.")
    if not audit:
        problems.append(f"en_audit_log log_id={AUDIT_LOG_ID} KHONG ton tai -- co the da xoa roi, dung lai.")
    if not hub or hub["status"] != "verified":
        problems.append(f"entity_hub.status hien tai != 'verified' (la {hub['status'] if hub else None}) -- co the da duoc sua roi, dung lai.")

    if problems:
        print("\nCANH BAO - trang thai hien tai khong khop gia dinh ban dau:")
        for p in problems:
            print(" -", p)
        print("Dung lai, KHONG sua gi de tranh ghi nham. Kiem tra lai thu cong.")
        conn.close()
        sys.exit(1)

    print("\n== Se sua (before -> after) ==")
    print(f"namevi_map_places.needs_review [{PLACE_ID}]: {nv['needs_review']} -> 0")
    print(f"en_audit_log.log_id={AUDIT_LOG_ID}: EXISTS -> DELETED")
    print(f"entity_hub.status [{ENTITY_ID}]: '{hub['status']}' -> 'active'")
    print(f"entity_hub.updated_at [{ENTITY_ID}]: '{hub['updated_at']}' -> '2026-08-16 15:24:45'")

    if not args.apply:
        print("\n(DRY-RUN -- khong ghi gi. Chay lai voi --apply de ghi thuc su.)")
        conn.close()
        return

    try:
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE namevi_map_places SET needs_review=0 WHERE dila_id=? AND needs_review=1",
            (PLACE_ID,),
        )
        conn.execute(
            "DELETE FROM en_audit_log WHERE log_id=? AND entity_ref=? AND action='approve' AND editor='nhatdoaphuvan@gmail.com'",
            (AUDIT_LOG_ID, PLACE_ID),
        )
        conn.execute(
            "UPDATE entity_hub SET status='active', updated_at='2026-08-16 15:24:45' WHERE entity_id=? AND status='verified'",
            (ENTITY_ID,),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"\nLOI khi ghi, da ROLLBACK: {e}")
        conn.close()
        sys.exit(1)

    print("\n== Trang thai SAU khi sua ==")
    nv2, audit2, hub2 = fetch_state(conn)
    print("namevi_map_places:", dict(nv2) if nv2 else None)
    print("en_audit_log:", dict(audit2) if audit2 else None)
    print("entity_hub:", dict(hub2) if hub2 else None)

    ok = (
        nv2 and nv2["needs_review"] == 0
        and audit2 is None
        and hub2 and hub2["status"] == "active" and hub2["updated_at"] == "2026-08-16 15:24:45"
    )
    print("\nKET QUA:", "OK - khop backup 100%" if ok else "CANH BAO - CHUA khop backup, kiem tra lai!")
    conn.close()


if __name__ == "__main__":
    main()
