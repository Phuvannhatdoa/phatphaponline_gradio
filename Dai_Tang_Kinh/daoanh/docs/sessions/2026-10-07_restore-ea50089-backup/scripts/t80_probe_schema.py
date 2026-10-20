#!/usr/bin/env python3
"""T80 probe: temple coverage + realistic founding-date ceiling from local sources."""
import sqlite3, re, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# existing founded dila_ids
c.execute("SELECT DISTINCT dila_id FROM place_timeline_events")
existing = set(r[0] for r in c.fetchall())
print("places with timeline event:", len(existing))

# temple-category places
c.execute("""SELECT id, note FROM places_dila WHERE note_category LIKE '%寺廟、佛塔、佛教文化地點%'""")
temple_rows = c.fetchall()
temple_ids = set(r[0] for r in temple_rows)
print("temple-category places:", len(temple_ids))
print("  of which already have timeline event:", len(temple_ids & existing))
print("  temple coverage:", f"{(len(temple_ids & existing)/len(temple_ids)*100):.1f}%")

# For all places (total), current distinct coverage
print("\nAll-place coverage:", f"{(len(existing)/59161*100):.2f}% (of 59161)")

# How many temple notes have founding keyword that are NOT yet covered
FOUNDING_KW = re.compile(r'建寺|創建|始建|開山|建廟|建塔|建於|所建|敕建|創立|建立|興建|起建|肇建|始創|創建於|建')
PAREN_YEAR = re.compile(r'[（(]\s*(\d{3,4})\s*(?:[-–至]\s*(\d{3,4}))?\s*[）)]')

added = 0
for pid, note in temple_rows:
    if pid in existing:
        continue
    if not note:
        continue
    m = FOUNDING_KW.search(note)
    if not m:
        continue
    # paren year near founding kw
    got = False
    for pm in PAREN_YEAR.finditer(note):
        if pm.start() < m.end():
            continue  # only founding-kw before year
        if abs(pm.start() - m.end()) <= 90:
            try:
                y = int(pm.group(1))
            except:
                continue
            if 100 <= y <= 2000:
                added += 1
                got = True
                break
    if got:
        pass

print("\nNEW temple founding events (founding-kw + year, uncovered):", added)

conn.close()
