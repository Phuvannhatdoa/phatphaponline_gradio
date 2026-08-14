"""
ETL: Link Marcus term glossary nodes to DILA entities.

1. Populates marcus_reference table from marcus_nodes_mapped.json
2. Sets entity.marcus_id for DILA entities that have Marcus equivalents

Usage:
    python scripts/link_marcus_entities.py
"""

import json
import os
import sqlite3
import sys
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')
NODES_MAPPED = os.path.join(DATA_DIR, 'chinese_buddhism_sna', 'marcus_nodes_mapped.json')
EDGES_MAPPED = os.path.join(DATA_DIR, 'chinese_buddhism_sna', 'marcus_edges_mapped.json')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def main():
    conn = get_conn()
    
    # Load Marcus mapped data
    print("Loading marcus_nodes_mapped.json...")
    with open(NODES_MAPPED, encoding='utf-8') as f:
        nodes = json.load(f)
    print(f"  {len(nodes)} nodes loaded")
    
    with open(EDGES_MAPPED, encoding='utf-8') as f:
        edges = json.load(f)
    print(f"  {len(edges)} edges loaded")
    
    # --- Step 1: Populate marcus_reference ---
    print("\n--- Step 1: Populate marcus_reference ---")
    
    conn.execute("DELETE FROM marcus_reference")
    
    inserted = 0
    for node_id, node in nodes.items():
        try:
            birth = node.get('birth_year', '') or ''
            death = node.get('death_year', '') or ''
            birth_int = int(birth) if birth and birth.isdigit() else None
            death_int = int(death) if death and death.isdigit() else None
            
            conn.execute(
                """INSERT OR REPLACE INTO marcus_reference
                   (node_id, label, label_vi, birth_year, death_year)
                   VALUES (?, ?, ?, ?, ?)""",
                (node_id,
                 node.get('label', ''),
                 node.get('name_vi', ''),
                 birth_int,
                 death_int)
            )
            inserted += 1
        except Exception as e:
            print(f"  Error inserting {node_id}: {e}")
    
    conn.commit()
    print(f"  Inserted {inserted} marcus_reference rows")
    
    # --- Step 2: Link entity.marcus_id ---
    print("\n--- Step 2: Link entity.marcus_id ---")
    
    entity_count = 0
    marcus_ids_in_entity = set()
    
    for row in conn.execute(
        "SELECT entity_id, dila_id FROM entity WHERE dila_id IS NOT NULL"
    ).fetchall():
        dila_id = row['dila_id']
        if dila_id in nodes:
            conn.execute(
                "UPDATE entity SET marcus_id = ? WHERE entity_id = ?",
                (dila_id, row['entity_id'])
            )
            entity_count += 1
            marcus_ids_in_entity.add(dila_id)
    
    conn.commit()
    
    linked_ids = len(marcus_ids_in_entity)
    linked_entities = entity_count
    print(f"  Updated {linked_entities} entities with marcus_id")
    print(f"  Unique Marcus IDs linked: {linked_ids}")
    
    # --- Step 3: Update marcus_networks with DILA entity references ---
    print("\n--- Step 3: Ensure marcus_networks is consistent ---")
    
    net_count = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
    print(f"  marcus_networks has {net_count} rows (unchanged)")
    
    # --- Step 4: Stats ---
    print("\n--- Stats ---")
    
    ref_count = conn.execute("SELECT COUNT(*) FROM marcus_reference").fetchone()[0]
    ref_with_vi = conn.execute(
        "SELECT COUNT(*) FROM marcus_reference WHERE label_vi IS NOT NULL AND label_vi != ''"
    ).fetchone()[0]
    ref_with_birth = conn.execute(
        "SELECT COUNT(*) FROM marcus_reference WHERE birth_year IS NOT NULL"
    ).fetchone()[0]
    
    print(f"  marcus_reference: {ref_count} rows")
    print(f"    with label_vi: {ref_with_vi}")
    print(f"    with birth_year: {ref_with_birth}")
    
    ent_with_marcus = conn.execute(
        "SELECT COUNT(*) FROM entity WHERE marcus_id IS NOT NULL AND marcus_id != ''"
    ).fetchone()[0]
    ent_no_marcus = conn.execute(
        "SELECT COUNT(*) FROM entity WHERE (marcus_id IS NULL OR marcus_id = '')"
    ).fetchone()[0]
    print(f"  entity with marcus_id: {ent_with_marcus}")
    print(f"  entity without marcus_id: {ent_no_marcus}")
    
    # Sample verified links
    print("\n--- Sample Links ---")
    samples = conn.execute("""
        SELECT e.entity_id, e.alias_zh, e.alias_vi, e.marcus_id,
               m.label as marcus_label, m.label_vi as marcus_label_vi
        FROM entity e
        JOIN marcus_reference m ON m.node_id = e.marcus_id
        WHERE e.marcus_id IS NOT NULL
        LIMIT 5
    """).fetchall()
    for s in samples:
        print(f"  {s['entity_id']}: {s['alias_zh'] or '?'} / {s['alias_vi'] or '?'} ↔ marcus={s['marcus_label']} ({s['marcus_label_vi']})")
    
    conn.close()
    print("\nDone!")

if __name__ == '__main__':
    main()
