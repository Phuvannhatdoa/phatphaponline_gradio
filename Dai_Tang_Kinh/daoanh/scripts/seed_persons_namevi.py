"""Seed monk persons: populate people.name_vi from name_vi_map + local transliteration.

This script implements Task T01: Seed monk từ persons.json (48K records).

Two phases:
  Phase 1: Copy existing auto-translations from name_vi_map to people.name_vi (fast, one SQL UPDATE).
  Phase 2: For the remaining records with no auto-translation, generate using the
           real Han-Viet transliteration app.py itself uses (CUSTOM_HANVIET +
           hanviet_fallback DB table), any still-unmapped character logged to
           missing_hanzi (admin can add a reading via the T08 admin page).

Usage:
    python scripts/seed_persons_namevi.py        # Full run (Phase 1 + Phase 2)
    python scripts/seed_persons_namevi.py --limit 50  # Test with 50 records
    python scripts/seed_persons_namevi.py --verify-only  # Only verification (Phase 3)
"""

import sys
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)

# Add project root to path so `import app` (the real translator, CUSTOM_HANVIET +
# hanviet_fallback DB table) works — the previous version of this script referenced
# a CUSTOM_HANVIET name that was never imported/defined anywhere in this file, which
# made Phase 2 crash with NameError on the first row and get silently swallowed by
# the broad except in phase2_generate_missing(), leaving 2,735 rows empty despite the
# script reporting success. Fixed 2026-08-20 (see tasks/T01-* investigation).
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)
import app as APP_MODULE

# Configuration
DB_PATH = os.path.join(PROJECT_ROOT, "data", "lineage.db")
NAME_VI_MAP_TABLE = "name_vi_map"
PEOPLE_TABLE = "people"

# Progress logging interval
LOG_INTERVAL = 100


# Helper: Han-Viet transliteration using the real CUSTOM_HANVIET + hanviet_fallback
# (DB table) lookup app.py itself uses, spaced/title-cased to match the formatting
# already present in the 45,938 rows Phase 1 fills from name_vi_map.name_vi_auto
# (e.g. "Đại Huệ Thiền Sư", not a spaceless concatenation). Any character still
# unmapped is left as its raw Han character (matching name_vi_map's own convention,
# e.g. "Nhân 叟" for 仁叟) rather than a '?' marker, and logged via
# app._log_missing_hanzi so it surfaces on the admin "Missing Hán Tự" page (T08)
# for future curation instead of silently failing again.
def ensure_vietnamese(name_zh: str) -> str:
    if not name_zh:
        return ""
    APP_MODULE._init_hv_cache()
    out = []
    for c in name_zh:
        if '一' <= c <= '鿿':
            hv = APP_MODULE.CUSTOM_HANVIET.get(c) or (APP_MODULE._HV_CACHE.get(c) if APP_MODULE._HV_CACHE else None)
            if hv:
                out.append(hv)
            else:
                APP_MODULE._log_missing_hanzi(c)
                out.append(c)
        else:
            out.append(c)
    spaced = []
    for i, tok in enumerate(out):
        if i > 0 and ('一' <= name_zh[i - 1] <= '鿿') and ('一' <= name_zh[i] <= '鿿'):
            spaced.append(' ')
        spaced.append(tok)
    result = ''.join(spaced)
    titled = []
    for w in result.split(' '):
        if w and ('一' <= w[0] <= '鿿'):
            titled.append(w)
        elif w:
            titled.append(w[0].upper() + w[1:] if len(w) > 1 else w.upper())
        else:
            titled.append(w)
    return ' '.join(titled)


# ── Phase 1: Copy existing auto-translations ───────────────────────────
def phase1_copy_existing():
    """Copy name_vi_auto from name_vi_map to people.name_vi.

    One SQL UPDATE fills all 45,937 records that already have auto-translations.
    """
    print("=" * 60)
    print("PHASE 1: Copy existing auto-translations from name_vi_map to people.name_vi")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        sql = f"""
            UPDATE {PEOPLE_TABLE}
            SET name_vi = (
                SELECT name_vi_auto FROM {NAME_VI_MAP_TABLE}
                WHERE {NAME_VI_MAP_TABLE}.dila_id = {PEOPLE_TABLE}.id
            )
            WHERE (name_vi IS NULL OR name_vi = '')
              AND id IN (SELECT dila_id FROM {NAME_VI_MAP_TABLE} WHERE name_vi_auto IS NOT NULL AND name_vi_auto != '')
        """

        cursor.execute(sql)
        updated = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"[OK] Phase 1 complete: updated {updated} records")
        print(f"   These records already had auto-translations in name_vi_map")
        return updated
    except Exception as e:
        print(f"[X] Phase 1 error: {e}")
        import traceback
        traceback.print_exc()
        return 0


# ── Phase 2: Generate missing translations ─────────────────────────────
def phase2_generate_missing(limit=None):
    """Generate name_vi for records still missing after Phase 1.

    Uses local transliteration (CUSTOM_HANVIET), with Gemini fallback for
    any characters not in the dictionary.
    """
    print("\n" + "=" * 60)
    print("PHASE 2: Generate missing translations (local + Gemini fallback)")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Select records still missing name_vi after Phase 1
        if limit:
            sql = f"""
                SELECT id, name_zh FROM {PEOPLE_TABLE}
                WHERE (name_vi IS NULL OR name_vi = '')
                ORDER BY id
                LIMIT ?
            """
            cursor.execute(sql, (limit,))
        else:
            sql = f"""
                SELECT id, name_zh FROM {PEOPLE_TABLE}
                WHERE (name_vi IS NULL OR name_vi = '')
                ORDER BY id
            """
            cursor.execute(sql)

        rows = cursor.fetchall()
        total = len(rows)
        print(f" Records to process: {total}")

        if total == 0:
            print("[OK] No records need processing (Phase 1 filled all)")
            conn.close()
            return 0

        updated = 0

        for idx, (person_id, name_zh) in enumerate(rows, 1):
            # ensure_vietnamese() now uses the real CUSTOM_HANVIET + hanviet_fallback
            # lookup (app.py) with raw-char fallback + missing_hanzi logging for any
            # still-unmapped character — no Gemini call needed for this path.
            name_vi = ensure_vietnamese(name_zh)

            if name_vi:
                cursor.execute(
                    f"UPDATE {PEOPLE_TABLE} SET name_vi = ? WHERE id = ?",
                    (name_vi, person_id),
                )
                updated += 1

            # Progress logging
            if idx % LOG_INTERVAL == 0 or idx == total:
                pct = idx / total * 100
                print(f"   Progress: {idx}/{total} ({pct:.1f}%) — Updated so far: {updated}")

        conn.commit()
        conn.close()

        print(f"\n[OK] Phase 2 complete: updated {updated}/{total} records")
        return updated
    except Exception as e:
        print(f"[X] Phase 2 error: {e}")
        import traceback
        traceback.print_exc()
        return 0


# ── Phase 3: Verification ──────────────────────────────────────────────
def phase3_verify():
    """Verify coverage after both phases and report statistics."""
    print("\n" + "=" * 60)
    print("PHASE 3: Verify coverage")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total persons
        cursor.execute(f"SELECT COUNT(*) FROM {PEOPLE_TABLE}")
        total_persons = cursor.fetchone()[0]

        # Persons with name_vi filled (non-null, non-empty)
        cursor.execute(
            f"SELECT COUNT(*) FROM {PEOPLE_TABLE} WHERE name_vi IS NOT NULL AND name_vi != ''"
        )
        filled = cursor.fetchone()[0]

        # Persons still empty
        cursor.execute(
            f"SELECT COUNT(*) FROM {PEOPLE_TABLE} WHERE name_vi IS NULL OR name_vi = ''"
        )
        empty = cursor.fetchone()[0]

        pct_filled = filled / total_persons * 100 if total_persons else 0
        pct_empty = empty / total_persons * 100 if total_persons else 0

        print(f"\n Overall coverage after script:")
        print(f"   Total persons:        {total_persons}")
        print(f"   name_vi filled:       {filled} ({pct_filled:.1f}%)")
        print(f"   name_vi empty/missing: {empty} ({pct_empty:.1f}%)")

        print(f"\n Breakdown:")
        print(f"   • Phase 1 (copy from name_vi_map): fills records with existing auto-translations")
        print(f"   • Phase 2 (local + Gemini): generates new translations for remaining records")

        conn.close()
        return filled, empty, total_persons, pct_filled
    except Exception as e:
        print(f"[X] Phase 3 error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0, 0


# ── Main ───────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("T01: Seed monk persons — populate people.name_vi")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print()

    # Phase 1: Copy existing auto-translations (one-shot SQL UPDATE)
    phase1_count = phase1_copy_existing()

    # Phase 2: Generate missing translations
    # After Phase 1, only records with no name_vi_auto in name_vi_map remain
    phase2_count = phase2_generate_missing(limit=None)

    # Phase 3: Verification
    filled, empty, total, pct = phase3_verify()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  • Phase 1 (copy auto):          {phase1_count} records")
    print(f"  • Phase 2 (generate new):       {phase2_count} records")
    print(f"  • Final coverage:           {filled}/{total} ({pct:.1f}%)")
    print(f"  • Still empty/missing:        {empty}")
    print("=" * 60)

    if pct >= 90:
        print("[OK] TARGET ACHIEVED: >= 90% persons have name_vi")
    else:
        print("️  TARGET NOT ACHIEVED: < 90% persons have name_vi")


if __name__ == "__main__":
    main()