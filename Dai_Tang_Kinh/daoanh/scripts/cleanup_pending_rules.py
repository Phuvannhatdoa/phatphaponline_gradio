"""Backfill cleanup: run GlossaryResolver against pending translation_rules.
Rules whose zh_terms are db_verified are auto-dismissed (DB already has the answer).
Run: python scripts/cleanup_pending_rules.py [--dry-run]
"""
import sys, sqlite3, re
from pathlib import Path

DB = str(Path(__file__).parent.parent / 'data' / 'lineage.db')
DRY_RUN = '--dry-run' in sys.argv


def _glossary_resolver(conn, source_text, max_ngrams=400):
    if not source_text:
        return {'resolved': {}, 'unresolved': []}
    runs = re.findall(r'[一-鿿㐀-䶿]+', source_text)
    seen, ngrams = set(), []
    for run in runs:
        for n in (2, 3, 4, 5):
            for i in range(len(run) - n + 1):
                g = run[i:i + n]
                if g not in seen:
                    seen.add(g)
                    ngrams.append(g)
        if len(ngrams) >= max_ngrams:
            break
    if not ngrams:
        return {'resolved': {}, 'unresolved': []}
    resolved = {}
    ng_set = set(ngrams)
    ph = ','.join('?' * len(ngrams))

    def _bulk(sql, args, src, status):
        try:
            for row in conn.execute(sql, args).fetchall():
                zh, vi = row[0], row[1]
                if zh in ng_set and vi and zh not in resolved:
                    resolved[zh] = {'term_vi': vi, 'source': src, 'status': status}
        except Exception:
            pass

    _bulk(f"SELECT term_zh, term_vi FROM translation_glossary WHERE term_zh IN ({ph}) AND is_locked=1", ngrams, 'translation_glossary', 'db_verified')
    _bulk(f"SELECT display_name_zh, display_name_vi FROM person_display_names WHERE display_name_zh IN ({ph}) AND display_name_vi IS NOT NULL AND display_name_vi!=''", ngrams, 'person_display_names', 'db_verified')
    _bulk(f"SELECT name_zh, name_vi FROM vn_person_authority WHERE name_zh IN ({ph}) AND status='verified' AND name_vi IS NOT NULL AND name_vi!=''", ngrams, 'vn_person_authority', 'db_verified')
    _bulk(f"SELECT entity_ref, canonical_name_vi FROM canonical_decision WHERE entity_ref IN ({ph}) AND canonical_name_vi IS NOT NULL AND canonical_name_vi!=''", ngrams, 'canonical_decision', 'db_verified')
    _bulk(f"SELECT name_zh, name_vi_final FROM name_vi_map WHERE name_zh IN ({ph}) AND name_vi_final IS NOT NULL AND name_vi_final!=''", ngrams, 'name_vi_map', 'db_verified')
    _bulk(f"SELECT name_zh, proposed_vi FROM person_name_correction WHERE name_zh IN ({ph}) AND status='approved' AND proposed_vi IS NOT NULL AND proposed_vi!=''", ngrams, 'person_name_correction', 'db_verified')
    _bulk(f"SELECT term_zh, term_vi FROM term_glossaries WHERE term_zh IN ({ph}) AND term_vi IS NOT NULL AND term_vi!='' AND term_vi!=term_zh", ngrams, 'term_glossaries', 'db_verified')
    _bulk(f"SELECT label, label_vi FROM marcus_reference WHERE label IN ({ph}) AND label_vi IS NOT NULL AND label_vi!='' AND label_vi!=label", ngrams, 'marcus_reference', 'db_verified')
    _bulk(f"SELECT name_zh, name_vi FROM namevi_map_places WHERE name_zh IN ({ph}) AND (vn_name_status='reviewed' OR confidence>=0.8) AND name_vi IS NOT NULL AND name_vi!=''", ngrams, 'namevi_map_places_hq', 'db_verified')
    _bulk(f"SELECT title_zh, title_vi FROM cbeta_catalog_vn WHERE title_zh IN ({ph}) AND title_vi IS NOT NULL AND title_vi!=''", ngrams, 'cbeta_catalog_vn', 'db_verified')
    _bulk(f"SELECT name_zh, name_vi FROM doctrine_concept WHERE name_zh IN ({ph}) AND name_vi IS NOT NULL AND name_vi!=''", ngrams, 'doctrine_concept', 'db_verified')
    _bulk(f"SELECT han_name, vn_name FROM monk_dict WHERE han_name IN ({ph}) AND vn_name IS NOT NULL AND vn_name!=''", ngrams, 'monk_dict', 'db_verified')
    try:
        tr_rows = conn.execute("SELECT rule_text FROM translation_rules WHERE status='active'").fetchall()
        for row in tr_rows:
            rtext = (row[0] or '').strip()
            m = re.search(r'^([^一-鿿（(]+?)\s*[（(]([一-鿿]{2,})[）)]', rtext)
            if m:
                vi_part, zh_part = m.group(1).strip(), m.group(2)
                if zh_part in ng_set and vi_part and zh_part not in resolved:
                    resolved[zh_part] = {'term_vi': vi_part, 'source': 'translation_rules_active', 'status': 'db_verified'}
    except Exception:
        pass

    return {'resolved': resolved, 'unresolved': [zh for zh in ngrams if zh not in resolved]}


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    pending = conn.execute(
        "SELECT id, rule_code, rule_text FROM translation_rules WHERE status='pending'"
    ).fetchall()

    print(f"Found {len(pending)} pending rules.")
    if DRY_RUN:
        print("[DRY RUN — no changes will be made]")
    print()

    to_dismiss = []
    keep = []

    for row in pending:
        rid, code, rtext = row['id'], row['rule_code'], row['rule_text'] or ''
        # Extract zh terms from rule_text
        zh_terms = re.findall(r'[一-鿿]{2,}', rtext)
        if not zh_terms:
            keep.append((code, rtext[:60], 'no zh terms — keep'))
            continue

        resolver = _glossary_resolver(conn, ' '.join(zh_terms))
        db_verified_matches = [
            (zh, resolver['resolved'][zh]['term_vi'], resolver['resolved'][zh]['source'])
            for zh in zh_terms
            if resolver['resolved'].get(zh, {}).get('status') == 'db_verified'
        ]

        if db_verified_matches:
            reason = f"zh_terms {[m[0] for m in db_verified_matches]} db_verified: " + \
                     ", ".join(f"{m[0]}→{m[1]} ({m[2]})" for m in db_verified_matches)
            to_dismiss.append((rid, code, reason))
        else:
            keep.append((code, rtext[:60], 'no db_verified match — keep'))

    print(f"=== TO DISMISS ({len(to_dismiss)}) — already in DB ===")
    for rid, code, reason in to_dismiss:
        print(f"  [{rid}] {code}: {reason}")

    print()
    print(f"=== TO KEEP ({len(keep)}) ===")
    for code, snippet, reason in keep:
        print(f"  {code}: {reason}")
        print(f"    text: {snippet}")

    if not DRY_RUN and to_dismiss:
        print()
        answer = input(f"\nDismiss {len(to_dismiss)} rules? [y/N] ")
        if answer.strip().lower() == 'y':
            from datetime import datetime
            now = datetime.now().isoformat()
            for rid, code, reason in to_dismiss:
                conn.execute(
                    "UPDATE translation_rules SET status='dismissed', updated_at=? WHERE id=?",
                    (now, rid)
                )
            conn.commit()
            print(f"Dismissed {len(to_dismiss)} pending rules.")
        else:
            print("Aborted.")
    elif DRY_RUN:
        print(f"\n[DRY RUN] Would dismiss {len(to_dismiss)} rules.")

    conn.close()


if __name__ == '__main__':
    main()
