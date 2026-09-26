#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T165 Coverage Dry-Run — chạy select_rules trên toàn bộ 1762 source_text,
in stats: số rule bị loại TB/row, số row nhận <5 rule, list rule chưa từng match lần nào."""
import os
import sys
import sqlite3
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from style_constitution import select_rules  # noqa: E402

DB_PATH = os.path.join(BASE, 'data', 'lineage.db')

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Get all cache rows with source_text
        rows = conn.execute("""
            SELECT source_hash, source_type, entity_id, source_text
            FROM translation_cache
            WHERE source_text IS NOT NULL AND source_text != ''
        """).fetchall()
        
        print(f"Total cache rows with source_text: {len(rows)}")
        
        rule_match_count = Counter()  # rule_code -> number of rows it matched
        row_rule_counts = []  # list of rule counts per row
        rules_never_matched = set()
        
        # Get all active rule codes
        all_rules = conn.execute("""
            SELECT rule_code FROM translation_rules
            WHERE status='active' AND is_active=1
        """).fetchall()
        all_rule_codes = {r['rule_code'] for r in all_rules}
        rules_never_matched = set(all_rule_codes)
        
        for row in rows:
            source_text = row['source_text']
            sel = select_rules(conn, source_text)
            matched_codes = [r['rule_code'] for r in sel['rules']]
            row_rule_counts.append(len(matched_codes))
            for code in matched_codes:
                rule_match_count[code] += 1
                rules_never_matched.discard(code)
        
        # Stats
        if row_rule_counts:
            avg_rules = sum(row_rule_counts) / len(row_rule_counts)
            min_rules = min(row_rule_counts)
            max_rules = max(row_rule_counts)
            under_5 = sum(1 for c in row_rule_counts if c < 5)
            print(f"\n--- Rule selection stats per row ---")
            print(f"  Avg rules/row: {avg_rules:.2f}")
            print(f"  Min rules/row: {min_rules}")
            print(f"  Max rules/row: {max_rules}")
            print(f"  Rows with <5 rules: {under_5} / {len(row_rule_counts)} ({under_5/len(row_rule_counts)*100:.1f}%)")
        
        print(f"\n--- Rule match frequency ---")
        for code, count in sorted(rule_match_count.items(), key=lambda x: -x[1]):
            pct = count / len(rows) * 100
            print(f"  {code}: {count} rows ({pct:.1f}%)")
        
        print(f"\n--- Rules NEVER matched (candidates for review) ---")
        if rules_never_matched:
            for code in sorted(rules_never_matched):
                # Get rule details
                r = conn.execute("SELECT rule_type, rule_text FROM translation_rules WHERE rule_code=?", (code,)).fetchone()
                if r:
                    print(f"  {code} ({r['rule_type']}): {r['rule_text'][:80]}...")
        else:
            print("  (none)")
        
        # Distribution of match_scope
        scope_dist = conn.execute("""
            SELECT match_scope, COUNT(*) as cnt
            FROM translation_rules
            WHERE status='active' AND is_active=1
            GROUP BY match_scope
        """).fetchall()
        print(f"\n--- match_scope distribution (active rules) ---")
        for r in scope_dist:
            print(f"  {r['match_scope']}: {r['cnt']}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()