import shutil, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh'
BACKUP = os.path.join(BASE, 'docs', 'sessions', '2026-10-30-t456', 'core.py')
TARGET = os.path.join(BASE, 'core.py')

# Read backup and add the 4 new functions
restored = open(BACKUP, encoding='utf-8', errors='replace').read()

# Define the new functions to add
NEW_FUNCTIONS = '''

def _get_work_suggest_cache():
    global _WORK_SUGGEST_CACHE
    if _WORK_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT cbeta_id, title_vi, title_zh, byline_vi AS translator, dynasty_vi AS era
                FROM dila_catalog_works
            """).fetchall()
        finally:
            conn.close()
        cache = []
        for r in rows:
            title_vi = r['title_vi'] or ''
            title_zh = r['title_zh'] or ''
            cache.append({
                'id': r['cbeta_id'], 'title_vi': title_vi, 'title_zh': title_zh,
                'translator': r['translator'], 'era': r['era'],
                '_norm_vi': normalize_text(title_vi), '_norm_zh': title_zh.lower(),
            })
        _WORK_SUGGEST_CACHE = cache
    return _WORK_SUGGEST_CACHE


def _get_place_suggest_cache():
    """Truy van du lieu dia danh tu namevi_map_places."""
    global _PLACE_SUGGEST_CACHE
    if _PLACE_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT DISTINCT dila_id AS id, name_vi AS value, name_zh AS name_zh, source
                FROM namevi_map_places
            """).fetchall()
        finally:
            conn.close()
        seen = set()
        unique = []
        for r in rows:
            if r['value'] in seen:
                continue
            seen.add(r['value'])
            unique.append(dict(r))
        _PLACE_SUGGEST_CACHE = unique
    return _PLACE_SUGGEST_CACHE


def _get_person_with_contribution_cache():
    """Set of person IDs that appear in dila_catalog_contributors."""
    global _PERSON_CONTRIBUTOR_IDS
    if _PERSON_CONTRIBUTOR_IDS is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT DISTINCT person_id FROM dila_catalog_contributors
            """).fetchall()
        finally:
            conn.close()
        _PERSON_CONTRIBUTOR_IDS = {str(row[0]) for row in rows}
    return _PERSON_CONTRIBUTOR_IDS
'''

# Find where to insert the new functions (after normalize_text function)
insert_point = restored.find('\n\ndef ', restored.find('def normalize_text'))
if insert_point == -1:
    insert_point = len(restored)

# Insert new functions
restored = restored[:insert_point] + NEW_FUNCTIONS + restored[insert_point:]

# Now update _get_person_suggest_cache to add reorder logic
person_start = restored.find('def _get_person_suggest_cache():')
person_end = restored.find('def _get_work_suggest_cache():')
person_func = restored[person_start:person_end]

# Add reorder logic before _PERSON_SUGGEST_CACHE = cache
old_line = '        _PERSON_SUGGEST_CACHE = cache'
new_lines = '''        # Reorder: contributors first
        contrib_ids = _get_person_with_contribution_cache()
        contrib_set = contrib_ids if contrib_ids else set()
        prioritized = [item for item in cache if str(item['id']) in contrib_set]
        non_prioritized = [item for item in cache if str(item['id']) not in contrib_set]
        cache = prioritized + non_prioritized
        _PERSON_SUGGEST_CACHE = cache'''

person_func = person_func.replace(old_line, new_lines)
restored = restored[:person_start] + person_func + restored[person_end:]

# Write the updated file
with open(TARGET, 'w', encoding='utf-8', errors='replace') as f:
    f.write(restored)

print('core.py updated with all 4 functions')