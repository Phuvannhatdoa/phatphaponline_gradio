"""T29 — Re-derive name_vi from name_zh for every row in `people` and the places
tables (namevi_map_places / places_pending) that still contains a raw, untranslated
Han character, after scripts/expand_hanviet_dictionary.py has grown
custom_hanviet_override. Idempotent: only issues an UPDATE when the freshly
translated value actually differs from what's stored, and characters this script
still can't resolve are left as their raw Han character (logged to missing_hanzi
for the T08 admin page) rather than dropped or guessed.

IMPORTANT: run this with app.py's own server process stopped first — importing
app.py here runs its module-level DB migrations, and SQLite will raise "database
is locked" if another process (the live server) already holds a write lock on
data/lineage.db. Restart the server after this script finishes.

Usage:
    python scripts/retranslate_residual_hanzi.py
"""
import sys, os, sqlite3, re

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)
import app as APP_MODULE

DB_PATH = os.path.join(PROJECT_ROOT, "data", "lineage.db")
HAN = re.compile(r'[一-鿿]')


def translate_name(name_zh: str) -> str:
    """Same spaced/title-cased convention as name_vi_map's own auto-translations
    (e.g. "Đại Huệ Thiền Sư"), not app.py's _ensure_vietnamese()'s raw concatenation
    when called on a whole string. Any character still unmapped is kept as its raw
    Han character (matching the existing name_vi_map convention, e.g. "Nhân 叟" for
    仁叟) and logged to missing_hanzi instead of being silently dropped."""
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


def fix_people(conn):
    rows = conn.execute("SELECT id, name_zh, name_vi FROM people WHERE name_vi IS NOT NULL AND name_vi != ''").fetchall()
    updated = 0
    for pid, name_zh, name_vi in rows:
        if not HAN.search(name_vi):
            continue
        new_vi = translate_name(name_zh)
        if new_vi != name_vi:
            conn.execute("UPDATE people SET name_vi = ? WHERE id = ?", (new_vi, pid))
            updated += 1
    conn.commit()
    return updated


def fix_places(conn):
    """Mirrors the COALESCE(m.name_vi, p.name_vi) read path used by the admin
    API/UI (places_pending): if namevi_map_places has a row for this place, that's
    the value shown and the one to update; otherwise update places_pending.name_vi
    (also fills the rare rows that were never processed at all, i.e. NULL on both
    sides — not just ones with a raw-Han remnant)."""
    rows = conn.execute("""
        SELECT p.id, p.name_zh, COALESCE(m.name_vi, p.name_vi) AS name_vi, (m.id IS NOT NULL) AS has_nvm
        FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
        WHERE p.id IS NOT NULL AND p.id != '' AND p.name_zh IS NOT NULL AND p.name_zh != ''
          AND p.note IS NOT NULL AND p.note != ''
    """).fetchall()
    updated_nvm = 0
    updated_pp = 0
    for pid, name_zh, name_vi, has_nvm in rows:
        if name_vi and not HAN.search(name_vi):
            continue
        new_vi = translate_name(name_zh)
        if new_vi == name_vi:
            continue
        if has_nvm:
            conn.execute("UPDATE namevi_map_places SET name_vi = ? WHERE dila_id = ?", (new_vi, pid))
            updated_nvm += 1
        else:
            conn.execute("UPDATE places_pending SET name_vi = ? WHERE id = ?", (new_vi, pid))
            updated_pp += 1
    conn.commit()
    return updated_nvm, updated_pp


def main():
    conn = sqlite3.connect(DB_PATH)
    print("Fixing people.name_vi ...")
    print(f"  updated: {fix_people(conn)}")

    print("Fixing places (namevi_map_places / places_pending) ...")
    nvm_updated, pp_updated = fix_places(conn)
    print(f"  namevi_map_places updated: {nvm_updated}")
    print(f"  places_pending updated: {pp_updated}")

    people_total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    people_rows = conn.execute("SELECT name_vi FROM people WHERE name_vi IS NOT NULL AND name_vi != ''").fetchall()
    people_raw = sum(1 for (v,) in people_rows if HAN.search(v))

    place_rows = conn.execute("""
        SELECT COALESCE(m.name_vi, p.name_vi) AS name_vi
        FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
        WHERE p.id IS NOT NULL AND p.id != '' AND p.name_zh IS NOT NULL AND p.name_zh != '' AND p.note IS NOT NULL AND p.note != ''
    """).fetchall()
    place_total = len(place_rows)
    place_empty = sum(1 for (v,) in place_rows if not v)
    place_raw = sum(1 for (v,) in place_rows if v and HAN.search(v))

    print("\n=== FINAL VERIFICATION ===")
    print(f"people: {len(people_rows)}/{people_total} filled, {people_raw} still have raw Han char(s)")
    print(f"places: {place_total - place_empty}/{place_total} filled, {place_empty} empty, {place_raw} still have raw Han char(s)")
    conn.close()


if __name__ == "__main__":
    main()
