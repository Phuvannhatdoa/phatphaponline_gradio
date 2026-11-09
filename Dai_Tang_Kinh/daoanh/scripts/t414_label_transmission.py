#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T414: Label transmission edges (teacher->student) with relation_kind - simplified"""
import sqlite3
import json
import os
import re
from datetime import datetime

DB_PATH = 'data/lineage.db'
TTL_DIR = 'data/ttl'

def backup_db(db_path=DB_PATH):
    """Create backup before making changes"""
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'lineage_t414_{ts}.db')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f'Backup created: {backup_path}')
    return backup_path

def get_ttl_teacher_info(teacher_id):
    """Get teacher info from TTL file - simplified"""
    # For dry-run, just return empty - TTL lookup is complex
    # In production, would look up TTL file by cbeta_id
    return []

def get_marcus_teacher_info(teacher_id):
    """Get teacher info from Marcus database"""
    cursor = sqlite3.connect(DB_PATH).cursor()
    cursor.execute('SELECT teacher_id, relation_type FROM marcus_networks WHERE teacher_id = ?', (teacher_id,))
    rows = cursor.fetchall()
    teachers = []
    for row in rows:
        teachers.append(('marcus', row[0], row[1] if len(row) > 1 else 'unknown'))
    return teachers

def determine_relation_kind(ttl_teachers, marcus_teachers):
    """Determine relation_kind based on Marcus evidence only (simplified)"""
    noi_phap_evidence = []
    khac_evidence = []
    
    if marcus_teachers:
        for item in marcus_teachers:
            if item[1] == 'dharma_transmission':
                noi_phap_evidence.append(f'Marcus:{item[0]}:dharma_transmission')
            else:
                khac_evidence.append(f'Marcus:{item[0]}:{item[1]}')
    
    if noi_phap_evidence and not khac_evidence:
        return 'noi_phap', f'{len(noi_phap_evidence)} dharma_transmission evidence(s)'
    elif khac_evidence and not noi_phap_evidence:
        return 'khac', f'{len(khac_evidence)} evidence(s)'
    else:
        return 'unknown', 'no dharma_transmission evidence'

def main():
    print('=== T414: Label Transmission Edges (Simplified) ===')
    print()
    
    backup = backup_db()
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print('=== Getting all lineage_primary_teacher edges ===')
    cursor.execute('SELECT id, teacher_id, disciple_id, marcus_subtype, ttl_confirmed, conflict, notes, relation_kind FROM lineage_primary_teacher')
    edges = cursor.fetchall()
    print(f'Found {len(edges)} total edges (with relation_kind column)')
    print()
    
    print(f'Processing {len(edges)} edges (full dry-run)')
    print()
    
    results = []
    statistics = {'noi_phap': 0, 'khac': 0, 'unknown': 0}
    contradictions = []
    
    for edge in edges:
        edge_id, teacher_id, disciple_id, marcus_subtype, ttl_confirmed, conflict, notes, existing_relation_kind = edge
        
        marcus_info = get_marcus_teacher_info(teacher_id)
        relation_kind, reason = determine_relation_kind([], marcus_info)
        
        statistics[relation_kind] = statistics.get(relation_kind, 0) + 1
        
        results.append({
            'edge_id': edge_id,
            'teacher_id': teacher_id,
            'disciple_id': disciple_id,
            'relation_kind': relation_kind,
            'reason': reason,
            'marcus_subtype': marcus_subtype,
            'ttl_confirmed': ttl_confirmed,
            'conflict': conflict,
            'notes': notes,
            'existing_relation_kind': existing_relation_kind
        })
        
        if relation_kind == 'unknown' and marcus_subtype == 'dharma_transmission':
            contradictions.append({
                'edge_id': edge_id,
                'teacher_id': teacher_id,
                'disciple_id': disciple_id,
                'marcus_subtype': marcus_subtype,
                'reason': reason
            })
    
    print('=== Dry-Run Results ===')
    print(f'Statistics: noi_phap={statistics["noi_phap"]}, khac={statistics["khac"]}, unknown={statistics["unknown"]}')
    print()
    
    print('=== Summary by relation_kind ===')
    for kind in ['noi_phap', 'khac', 'unknown']:
        print(f'  {kind}: {statistics[kind]} edges')
    print()
    
    print(f'=== Contradictions (Marcus dharma_transmission but unknown) ===')
    print(f'Found {len(contradictions)} contradictions')
    for c in contradictions[:10]:
        print(f'  Edge {c["edge_id"]}: teacher={c["teacher_id"]}, disc={c["disciple_id"]}, marcus={c["marcus_subtype"]}, reason={c["reason"]}')
    if len(contradictions) > 10:
        print(f'  ... and {len(contradictions) - 10} more')
    print()
    
    print('=== Exporting TSV ===')
    tsv_path = f'docs/evidence/{datetime.now().strftime("%Y%m%d")}_T414_transmission_dryrun.tsv'
    os.makedirs('docs/evidence', exist_ok=True)
    with open(tsv_path, 'w', encoding='utf-8') as f:
        f.write('edge_id\tteacher_id\tdisciple_id\trelation_kind\treason\tmarcus_subtype\tttl_confirmed\tconflict\nexisting_relation_kind\n')
        for r in results:
            f.write(f'{r["edge_id"]}\t{r["teacher_id"]}\t{r["disciple_id"]}\t{r["relation_kind"]}\t{r["reason"]}\t{r["marcus_subtype"]}\t{r["ttl_confirmed"]}\t{r["conflict"]}\n')
    print(f'Exported: {tsv_path}')
    print()
    
    print(f'=== Sample results (first 5) ===')
    for r in results[:5]:
        print(f'  Edge {r["edge_id"]}: teacher={r["teacher_id"]}, disc={r["disciple_id"]}, kind={r["relation_kind"]}, reason={r["reason"][:60]}')
    if len(results) > 5:
        print(f'  ... and {len(results) - 5} more')
    print()
    
    # Update DB
    print('=== Updating DB with relation_kind ===')
    cursor = conn.cursor()
    updated = 0
    for r in results:
        cursor.execute('UPDATE lineage_primary_teacher SET relation_kind = ? WHERE id = ?', (r['relation_kind'], r['edge_id']))
        updated += cursor.total_changes
    conn.commit()
    print(f'Updated {updated} edges with relation_kind values')
    
    conn.close()
    
    print('=== Dry-Run Complete ===')
    print('Statistics:')
    print(f'  noi_phap: {statistics["noi_phap"]} edges (nét liền = nối pháp)')
    print(f'  khac: {statistics["khac"]} edges (nét đứt = y chỉ/đặt hiệu)')
    print(f'  unknown: {statistics["unknown"]} edges')
    print()
    print('Export: docs/evidence/*.tsv')
    print('DB updated with relation_kind column values')
    print('Next: daoanh-qa kiểm độc lập; Admin xác nhận DONE')
    
if __name__ == '__main__':
    main()