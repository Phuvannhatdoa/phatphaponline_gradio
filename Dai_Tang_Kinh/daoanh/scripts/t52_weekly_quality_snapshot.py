"""
T52d — Weekly CBETA Quality Snapshot
Generates a weekly snapshot of CBETA data quality metrics and appends to
docs/cbeta_quality_log.jsonl for trend tracking.

Usage:
    python scripts/t52_weekly_quality_snapshot.py [--dry-run]
"""

import sqlite3
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "lineage.db"
LOG_PATH = Path(__file__).parent.parent / "docs" / "cbeta_quality_log.jsonl"


def snapshot(conn: sqlite3.Connection) -> dict:
    def q(sql, params=()):
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else 0

    catalog_total = q("SELECT COUNT(*) FROM cbeta_catalog_vn")
    passages_total = q("SELECT COUNT(*) FROM passage")
    passages_translated = q("SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL AND vi_text != ''")
    entity_links = q("SELECT COUNT(*) FROM passage_entity")
    sat_linked = q("SELECT COUNT(*) FROM cbeta_catalog_vn WHERE q_number IS NOT NULL AND q_number != '' AND q_number != '0'")
    toh_linked = q("SELECT COUNT(*) FROM toh_cbeta_crossref")
    fuzzy_total = q("SELECT COUNT(*) FROM fuzzy_match_candidates") if _table_exists(conn, "fuzzy_match_candidates") else 0
    fuzzy_approved = q("SELECT COUNT(*) FROM fuzzy_match_candidates WHERE status='approved'") if _table_exists(conn, "fuzzy_match_candidates") else 0
    place_stats_rows = q("SELECT COUNT(*) FROM cbeta_place_mention_stats") if _table_exists(conn, "cbeta_place_mention_stats") else 0

    # zqlocal_content confidence distribution
    vi_conf_rows = conn.execute(
        "SELECT content_type, confidence, COUNT(*) AS cnt FROM zqlocal_content "
        "WHERE content_type='VI_NAME' GROUP BY confidence ORDER BY confidence"
    ).fetchall()
    vi_dist = {str(row[1]): row[2] for row in vi_conf_rows}

    # dynasty distribution
    dynasty_rows = conn.execute(
        "SELECT dynasty_vi, COUNT(*) AS cnt FROM cbeta_catalog_vn "
        "WHERE dynasty_vi IS NOT NULL GROUP BY dynasty_vi ORDER BY cnt DESC LIMIT 8"
    ).fetchall()
    dynasty_dist = [{"dynasty": r[0], "count": r[1]} for r in dynasty_rows]

    sat_pct = round(sat_linked / catalog_total * 100, 1) if catalog_total else 0
    trans_pct = round(passages_translated / passages_total * 100, 1) if passages_total else 0

    return {
        "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "catalog": {"total": catalog_total},
        "import": {
            "passages_total": passages_total,
            "passages_translated": passages_translated,
            "translation_pct": trans_pct,
        },
        "entity": {
            "links_total": entity_links,
            "places_with_stats": place_stats_rows,
        },
        "crossref": {
            "sat": sat_linked,
            "sat_pct": sat_pct,
            "toh": toh_linked,
            "toh_pct": round(toh_linked / catalog_total * 100, 1) if catalog_total else 0,
        },
        "fuzzy": {
            "total": fuzzy_total,
            "approved": fuzzy_approved,
            "approval_pct": round(fuzzy_approved / fuzzy_total * 100, 1) if fuzzy_total else 0,
        },
        "vi_name_confidence": vi_dist,
        "dynasty_distribution": dynasty_dist,
    }


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def main():
    parser = argparse.ArgumentParser(description="Weekly CBETA quality snapshot")
    parser.add_argument("--dry-run", action="store_true", help="Print snapshot without saving")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    data = snapshot(conn)
    conn.close()

    print(json.dumps(data, ensure_ascii=False, indent=2))

    if args.dry_run:
        print("\n[DRY RUN] Không lưu snapshot.")
        return

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"\n[OK] Snapshot saved → {LOG_PATH}")


if __name__ == "__main__":
    main()
