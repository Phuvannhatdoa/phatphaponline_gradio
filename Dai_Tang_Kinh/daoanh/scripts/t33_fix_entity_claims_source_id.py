"""
T33 - Fix entity_claims.source_id

Bug: etl_entity_claims.py ghi entity_source_ids.id vao source_id thay vi
data_sources.source_id (FK that). Ket qua: 118K+ gia tri source_id tuy tien
thay vi 1-5 (DILA/BDRC/CBETA/MARCUS/ZQLOCAL).

Fix: UPDATE theo claim_type/predicate ve dung FK.
Idempotent: chay lai se UPDATE -> same values, an toan.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')


def main():
    conn = sqlite3.connect(DB_PATH)

    # Lay source_id that tu data_sources
    src = {row[0]: row[1] for row in conn.execute(
        "SELECT source_code, source_id FROM data_sources"
    ).fetchall()}
    dila_id = src.get('DILA')
    zq_id = src.get('ZQLOCAL')

    if not dila_id or not zq_id:
        print(f"[FAIL] data_sources thieu: DILA={dila_id}, ZQLOCAL={zq_id}")
        print("       Cac source_code co san:", list(src.keys()))
        conn.close()
        return

    print(f"[INFO] data_sources: DILA={dila_id}, ZQLOCAL={zq_id}")

    before = conn.execute(
        "SELECT COUNT(DISTINCT source_id) FROM entity_claims"
    ).fetchone()[0]
    print(f"[INFO] source_id distinct (truoc fix): {before}")

    conn.execute("BEGIN")

    # Buoc 1: COORDINATE + ADMIN_UNIT + canonicalNameZh → DILA
    cur1 = conn.execute("""
        UPDATE entity_claims
        SET source_id = ?
        WHERE claim_type IN ('COORDINATE', 'ADMIN_UNIT')
           OR (claim_type = 'NAME' AND predicate = 'canonicalNameZh')
    """, (dila_id,))
    print(f"[OK] DILA claims updated: {cur1.rowcount} rows")

    # Buoc 2: vietnameseName → ZQLOCAL (ten Viet do ZQ tu-phien-am)
    cur2 = conn.execute("""
        UPDATE entity_claims
        SET source_id = ?
        WHERE claim_type = 'NAME' AND predicate = 'vietnameseName'
    """, (zq_id,))
    print(f"[OK] ZQLOCAL claims updated: {cur2.rowcount} rows")

    conn.execute("COMMIT")

    # Verify
    after = conn.execute(
        "SELECT source_id, COUNT(*) c FROM entity_claims GROUP BY source_id ORDER BY source_id"
    ).fetchall()
    print(f"\n[VERIFY] source_id distribution sau fix:")
    for sid, cnt in after:
        src_name = next((k for k, v in src.items() if v == sid), f"id={sid}")
        ok = "OK" if sid in src.values() else "UNKNOWN-ID"
        print(f"  source_id={sid} ({src_name}): {cnt} rows [{ok}]")

    # Spot-check Thieu Lam Tu
    sample = conn.execute("""
        SELECT ec.claim_type, ec.predicate, ec.source_id, ec.object_text
        FROM entity_claims ec
        JOIN entity e ON e.entity_id = ec.entity_id
        WHERE e.dila_id = 'PL023255'
        ORDER BY ec.claim_type
        LIMIT 10
    """).fetchall()
    print(f"\n[SPOT-CHECK] Thieu Lam Tu (PL023255):")
    for row in sample:
        sid = row[2]
        src_name = next((k for k, v in src.items() if v == sid), f"id={sid}")
        print(f"  {row[0]} / {row[1]}: source={src_name} val={str(row[3])[:40]}")

    conn.close()
    print("\n[DONE] Fix hoan thanh.")


if __name__ == '__main__':
    main()
