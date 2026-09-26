#!/usr/bin/env python3
"""
T69 — Wire Evidence into entity_claims (backfill từ dữ liệu thật, đa-nguồn)
============================================================================
Nối các nguồn dữ liệu đã có trong DB vào entity_claims / entity_source_ids:
  - CBETA:    place_person_bibl  → TEXT_EVIDENCE cho địa danh
  - Marcus:   marcus_networks    → NETWORK_EVIDENCE cho người (via marcus_networks edges)
  - Wikidata: geo_cross_ref      → EXTERNAL_ID cho địa danh

KHÔNG tạo fake data. KHÔNG import mới. Idempotent (delete-then-insert).
verification_status = 'unverified' — chỉ admin HITL mới set 'verified' (T67).

Usage:
    python scripts/wire_evidence_into_entity_claims.py [--dry-run]
"""
import sys, sqlite3, json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()
DB_PATH = ROOT / 'data' / 'lineage.db'
LOG_PATH = ROOT / 'data' / 't69_wire_log.json'

DRY_RUN = '--dry-run' in sys.argv

# data_sources.source_id
SRC_CBETA  = 3
SRC_MARCUS = 4


def run():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # ── Verify entity_hub types present ──────────────────────────────────
    types = [r[0] for r in conn.execute("SELECT DISTINCT entity_type FROM entity_hub").fetchall()]
    print(f'[T69] entity_hub types: {types}')
    hub_total = conn.execute("SELECT COUNT(*) FROM entity_hub").fetchone()[0]
    print(f'      {hub_total:,} total entity_hub rows')

    stats = {'cbeta': 0, 'marcus': 0, 'wikidata': 0, 'src_ids': 0}

    # ── Idempotent: delete previous T69 wire ──────────────────────────────
    if not DRY_RUN:
        d1 = conn.execute(
            "DELETE FROM entity_claims WHERE source_reference LIKE 'T69:%'"
        ).rowcount
        d2 = conn.execute(
            "DELETE FROM entity_source_ids WHERE verification_note LIKE 'T69%'"
        ).rowcount
        conn.commit()
        print(f'[T69] Cleared: {d1} claims, {d2} source_ids (idempotent)')

    # ─────────────────────────────────────────────────────────────────────
    # 1. CBETA → TEXT_EVIDENCE for PLACE entities
    #    place_person_bibl.place_id → entity_hub.canonical_label (same format)
    # ─────────────────────────────────────────────────────────────────────
    print('\n[T69] Wiring CBETA TEXT_EVIDENCE...')
    cbeta_rows = conn.execute("""
        SELECT b.place_id, b.cbeta_ref, b.person_name_raw, b.source_book, b.confidence,
               h.entity_id
        FROM place_person_bibl b
        JOIN entity_hub h ON h.canonical_label = b.place_id
        WHERE b.cbeta_ref IS NOT NULL
        ORDER BY b.place_id, b.cbeta_ref
    """).fetchall()
    print(f'      {len(cbeta_rows):,} joined rows (place_person_bibl × entity_hub)')

    # Deduplicate by (entity_id, cbeta_ref)
    seen = set()
    cbeta_claims = []
    cbeta_src_ids = []
    for r in cbeta_rows:
        key = (r['entity_id'], r['cbeta_ref'])
        if key in seen:
            continue
        seen.add(key)
        snippet = f"{r['person_name_raw'] or ''} 《{r['source_book'] or r['cbeta_ref']}》"
        cbeta_claims.append((
            r['entity_id'], SRC_CBETA,
            'TEXT_EVIDENCE',
            r['place_id'],           # subject (entity_ref)
            'mentioned_in',          # predicate
            snippet[:255],           # object_text
            r['place_id'],           # source_record_id
            f"T69:{r['cbeta_ref']}", # source_reference
            'PRIMARY',               # authority_role
            float(r['confidence'] or 0.7),
            'unverified',
        ))
        cbeta_src_ids.append((
            r['entity_id'], 'CBETA', r['place_id'], r['place_id'],
            'candidate', float(r['confidence'] or 0.7), 0, 'T69:cbeta_wire',
        ))
        stats['cbeta'] += 1

    print(f'      {stats["cbeta"]:,} unique CBETA claims')

    # ─────────────────────────────────────────────────────────────────────
    # 2. Marcus → NETWORK_EVIDENCE
    #    marcus_networks.teacher_id / student_id → people.id → entity_hub
    #    Only works if PERSON entity_hub entries exist; otherwise best-effort
    #    using source_record_id = DILA person ID.
    # ─────────────────────────────────────────────────────────────────────
    print('\n[T69] Wiring Marcus NETWORK_EVIDENCE...')
    has_person_hub = 'PERSON' in types
    if has_person_hub:
        marc_join = """
            SELECT DISTINCT n.teacher_id, n.student_id, n.ref, n.source_data,
                   ht.entity_id AS teacher_eid, hs.entity_id AS student_eid
            FROM marcus_networks n
            JOIN entity_hub ht ON ht.canonical_label = n.teacher_id AND ht.entity_type = 'PERSON'
            JOIN entity_hub hs ON hs.canonical_label = n.student_id AND hs.entity_type = 'PERSON'
            LIMIT 15000
        """
    else:
        # Fallback: JOIN via people.id (DILA person authority)
        marc_join = """
            SELECT DISTINCT n.teacher_id, n.student_id, n.ref, n.source_data,
                   h_t.entity_id AS teacher_eid, h_s.entity_id AS student_eid
            FROM marcus_networks n
            LEFT JOIN people p_t ON p_t.id = n.teacher_id
            LEFT JOIN entity_hub h_t ON h_t.canonical_label = p_t.id
            LEFT JOIN people p_s ON p_s.id = n.student_id
            LEFT JOIN entity_hub h_s ON h_s.canonical_label = p_s.id
            WHERE h_t.entity_id IS NOT NULL OR h_s.entity_id IS NOT NULL
            LIMIT 15000
        """
    marc_rows = conn.execute(marc_join).fetchall()
    print(f'      {len(marc_rows):,} Marcus edges with entity_hub links')

    seen_marc = set()
    marc_claims = []
    marc_src_ids = set()
    for r in marc_rows:
        ref_str = (r['ref'] or r['source_data'] or '')[:120]
        for role, node_id, eid in [('teacher', r['teacher_id'], r['teacher_eid']),
                                   ('student', r['student_id'], r['student_eid'])]:
            if eid is None:
                continue
            other = r['student_id'] if role == 'teacher' else r['teacher_id']
            key = (eid, other, role)
            if key in seen_marc:
                continue
            seen_marc.add(key)
            marc_claims.append((
                eid, SRC_MARCUS,
                'NETWORK_EVIDENCE',
                node_id,
                f'lineage_{role}',
                f"Marcus: {role} of {other} | {ref_str}"[:255],
                node_id,
                f'T69:marcus:{node_id}:{other}',
                'PRIMARY', 0.8, 'unverified',
            ))
            marc_src_ids.add((eid, node_id))
            stats['marcus'] += 1

    marc_src_id_rows = [(eid, 'MARCUS', nid, nid, 'candidate', 0.8, 0, 'T69:marcus_wire')
                        for eid, nid in marc_src_ids]
    print(f'      {stats["marcus"]:,} Marcus NETWORK_EVIDENCE claims')

    # ─────────────────────────────────────────────────────────────────────
    # 3. Wikidata → EXTERNAL_ID for PLACE entities
    # ─────────────────────────────────────────────────────────────────────
    print('\n[T69] Wiring Wikidata EXTERNAL_ID...')
    wiki_rows = conn.execute("""
        SELECT g.dila_id, g.wikidata_qid, h.entity_id
        FROM geo_cross_ref g
        JOIN entity_hub h ON h.canonical_label = g.dila_id
        WHERE g.wikidata_qid IS NOT NULL AND g.wikidata_qid != ''
    """).fetchall()
    print(f'      {len(wiki_rows):,} Wikidata QIDs joined to entity_hub')

    # Resolve Wikidata source_id từ data_sources (Build 2 A2) — fallback 6,
    # tránh source_id=None làm mất EXTERNAL_ID claims (lỗi phát hiện trong audit T69).
    wiki_src_row = conn.execute(
        "SELECT source_id FROM data_sources WHERE source_code = 'Wikidata' LIMIT 1"
    ).fetchone()
    wiki_src = wiki_src_row['source_id'] if wiki_src_row else 6

    wiki_claims = []
    for r in wiki_rows:
        wiki_claims.append((
            r['entity_id'], wiki_src,   # source_id=Wikidata (data_sources), không còn None
            'EXTERNAL_ID',
            r['dila_id'],
            'same_as',
            f"Q:{r['wikidata_qid']}",
            r['dila_id'],
            f"T69:wikidata:{r['wikidata_qid']}",
            'CORROBORATING', 0.85, 'unverified',
        ))
        stats['wikidata'] += 1

    print(f'      {stats["wikidata"]:,} Wikidata EXTERNAL_ID claims')

    # ─────────────────────────────────────────────────────────────────────
    # INSERT
    # ─────────────────────────────────────────────────────────────────────
    all_claims = cbeta_claims + marc_claims + wiki_claims
    all_src_ids = cbeta_src_ids + marc_src_id_rows
    stats['src_ids'] = len(all_src_ids)

    print(f'\n[T69] Total: {len(all_claims):,} claims, {len(all_src_ids):,} entity_source_ids')

    if DRY_RUN:
        print('\n[DRY-RUN] No DB changes.')
    else:
        print('[T69] Inserting...')
        conn.executemany("""
            INSERT OR IGNORE INTO entity_claims
              (entity_id, source_id, claim_type, subject, predicate,
               object_text, source_record_id, source_reference, authority_role,
               confidence, verification_status)
            VALUES (?,?,?,?,?, ?,?,?,?,?,?)
        """, all_claims)
        claims_inserted = conn.total_changes
        print(f'      {claims_inserted:,} entity_claims inserted')

        conn.executemany("""
            INSERT OR IGNORE INTO entity_source_ids
              (entity_id, source, source_entity_id, source_label,
               match_status, confidence, verified, verification_note)
            VALUES (?,?,?,?,?,?,?,?)
        """, all_src_ids)
        src_inserted = conn.total_changes - claims_inserted
        print(f'      {src_inserted:,} entity_source_ids inserted')

        conn.commit()
        print('[T69] Commit OK')

        # Verify
        print('\n[T69] Post-run verification:')
        for ct in ('TEXT_EVIDENCE', 'NETWORK_EVIDENCE', 'EXTERNAL_ID', 'NAME', 'COORDINATE', 'ADMIN_UNIT'):
            cnt = conn.execute("SELECT COUNT(*) FROM entity_claims WHERE claim_type = ?", (ct,)).fetchone()[0]
            print(f'  entity_claims [{ct}]: {cnt:,}')
        for src in ('DILA', 'CBETA', 'MARCUS', 'ZQLOCAL'):
            cnt = conn.execute("SELECT COUNT(*) FROM entity_source_ids WHERE source = ?", (src,)).fetchone()[0]
            print(f'  entity_source_ids [source={src}]: {cnt:,}')

    log = {
        'run_at': datetime.now().isoformat(), 'dry_run': DRY_RUN, 'stats': stats,
    }
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n[LOG] {LOG_PATH}')
    print(f'[T69] Stats: {stats}')
    conn.close()


if __name__ == '__main__':
    run()
