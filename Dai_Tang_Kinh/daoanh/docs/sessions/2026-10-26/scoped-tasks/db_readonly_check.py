import sqlite3

# READ-ONLY check: chi SELECT sqlite_master + dem dong, mo DB bang mode=ro
con = sqlite3.connect('file:data/lineage.db?mode=ro', uri=True)
cur = con.cursor()
print('tables:', cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
    "('codex_place_name','ai_place_name','lexicon','namevi_map_places','places_dila')").fetchall())
print('codex_place_name cols:', [r[1] for r in cur.execute('PRAGMA table_info(codex_place_name)')])
print('codex rows/distinct dila_id:', cur.execute(
    'SELECT COUNT(*), COUNT(DISTINCT dila_id) FROM codex_place_name').fetchone())
print('PL000000000009/19/168 in codex:', cur.execute(
    "SELECT dila_id, name_vi FROM codex_place_name WHERE dila_id IN "
    "('PL000000000009','PL000000000019','PL000000000168')").fetchall())
con.close()
