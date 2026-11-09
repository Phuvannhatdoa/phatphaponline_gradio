# -*- coding: utf-8 -*-
"""T456 - Implementation script."""
import os, shutil, sys

# Reconfigure stdout for proper encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Define paths
BASE = r'E:\\Backup 2025\\QuaiTieuTu\\Anan Son\\phatphaponline_gradio\\truyenthua\\visjs-app\\Dai_Tang_Kinh\\daoanh'
DEST = os.path.join(BASE, 'docs', 'sessions', '2026-10-30-t456')

# Backup files exist in DEST, now read and modify them

# 1. Modify core.py: _get_work_suggest_cache and add new cache functions

def edit_core_py():
    core_path = os.path.join(BASE, 'core.py')
    with open(core_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Add _get_work_suggest_cache function (replacing cbeta_catalog_vn with dila_catalog_works)
    # Find where _get_work_suggest_cache is defined
    start = content.find('def _get_work_suggest_cache():')
    if start == -1:
        print("ERROR: _get_work_suggest_cache not found in core.py")
        return False
        
    # Find end of function - next def or class or end of file
    next_def = content.find('def ', start+1)
    if next_def == -1:
        end = len(content)
    else:
        end = next_def
    
    # Replace the function body
    new_func = '''def _get_work_suggest_cache():
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
    return _WORK_SUGGEST_CACHE'''

    # Replace the function
    content = content[:start] + new_func + content[end:]
    
    # Add _get_place_suggest_cache function
    new_place_cache = '''
def _get_place_suggest_cache():
    \"\"\"Truy vấn dữ liệu địa danh từ namevi_map_places.\"\"\"
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

'''

    # Insert after _get_work_suggest_cache
    work_start = content.find('def _get_work_suggest_cache():')
    work_end = content.find('def ', work_start+1)
    if work_end == -1:
        work_end = len(content)
    content = content[:work_end] + new_place_cache + content[work_end:]
    
    # Add _get_person_with_contribution_cache function
    new_contributor_cache = '''
def _get_person_with_contribution_cache():
    \"\"\"Set of person IDs that appear in dila_catalog_contributors → ưu tiên.\"\"\"
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

    # Insert after _get_work_suggest_cache
    work_start = content.find('def _get_work_suggest_cache():')
    work_end = content.find('def ', work_start+1)
    if work_end == -1:
        work_end = len(content)
    content = content[:work_end] + new_contributor_cache + content[work_end:]
    
    # Update _get_person_suggest_cache to prioritize contributors
    person_start = content.find('def _get_person_suggest_cache():')
    if person_start == -1:
        print("ERROR: _get_person_suggest_cache not found in core.py")
        return False
    
    person_end = content.find('def ', person_start+1)
    if person_end == -1:
        person_end = len(content)
    
    # Read the current function
    person_func = content[person_start:person_end]
    
    # Add reordering logic
    reorder_logic = '''    # Reorder to prioritize people with contributions
    contrib_ids = _get_person_with_contribution_cache() if _PERSON_CONTRIBUTOR_IDS is not None else set()
    # Create list of items sorted by priority: contributors first
    prioritized = []
    non_prioritized = []
    for item in cache:
        item_id = str(item['id'])
        if item_id in contrib_ids:
            prioritized.append(item)
        else:
            non_prioritized.append(item)
    # Combine: prioritized first, then non-prioritized
    cache = prioritized + non_prioritized'''

    # Replace the function body
    content = content[:person_start] + reorder_logic + content[person_end:]

    # Write back
    with open(core_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    
    print("✓ core.py updated")
    return True

# 2. Modify routes_lineage.py: api_search_suggest and add places group

def edit_routes_lineage_py():
    route_path = os.path.join(BASE, 'routes_lineage.py')
    with open(route_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Find api_search_suggest function
    start = content.find('def api_search_suggest():')
    if start == -1:
        print("ERROR: api_search_suggest not found in routes_lineage.py")
        return False
        
    # Find end of function
    next_def = content.find('def ', start+1)
    if next_def == -1:
        end = len(content)
    else:
        end = next_def
    
    # Read current function body
    func_body = content[start:end]
    
    # Update docstring to mention places group
    new_docstring = '''    """GET /daoanh/api/search/suggest?q=<text> — T469: homepage autocomplete, grouped by entity type. NEW endpoint, additive — does NOT change /daoanh/api/search's response shape (that one is still consumed elsewhere, see its docstring above).

    Trả 3 nhóm:
      persons -> people.id/name_vi/name_zh/dynasty/birth_year/death_year (bảng people, cùng nguồn "monks" mà api_global_search() dùng) — kèm dynasty/birth_year/death_year làm phụ chú phân biệt tên trùng (vd Huyền Trang có 4 id A000294/A002949/A009306/A014708).
      works   -> dila_catalog_works.title_vi/title_zh/translator_vi/dynasty_vi (đã kiểm schema bằng sqlite_master.sql: cột translator_vi tồn tại, và api_global_search() ở trên cũng SELECT nó làm w.author) — KHÔNG cần JOIN dila_catalog_contributors/dila_catalog_works.
      places  -> dila_catalog_places.name_vi/name_zh/cbeta_id (tái dùng route /daoanh/api/public/autocomplete — T416/T450).
    
    Nhận diện có dấu/không dấu: tái dùng normalize_text() (định nghĩa ở đầu file, dòng ~102, đã dùng cho lexicon/TTL) để chuẩn hoá cả câu query và tên/tiêu đề trong cache — không viết lại thuật toán bỏ dấu.'''
    
    # Replace docstring
    new_start = content.find('"""', start) + 3
    new_end = content.find('"""', new_start)
    new_content = content[:new_start] + new_docstring + content[new_end+3:]
    
    # Add places group to the response
    places_logic = '''
        # Add places group
        places_cache = _get_place_suggest_cache()
        places = []
        if places_cache:
            for p in places_cache[:5]:  # limit to 5 places
                places.append({
                    'id': p['id'], 'value': p['value'], 'name_zh': p['name_zh'],
                    'source': p['source']
                })
        
        return jsonify({
            "success": True,
            "persons": persons,
            "works": works,
            "places": places,
            "_timing_ms": {"persons": round(t_persons_ms, 1), "works": round(t_works_ms, 1), "places": round(t_places_ms, 1)},
        })
'''
    
    # Replace the entire function body
    content = content[:start] + new_docstring + new_content
    
    # Write back
    with open(route_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    
    print("✓ routes_lineage.py updated")
    return True

# 3. Modify index.html: renderSuggest to add places group

def edit_index_html():
    html_path = os.path.join(BASE, 'index.html')
    with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Find renderSuggest function
    start = content.find('function renderSuggest')
    if start == -1:
        print("ERROR: renderSuggest not found in index.html")
        return False
        
    end = content.find('function ', start+10)
    if end == -1:
        end = len(content)
    
    # Read current function
    func_body = content[start:end]
    
    # Add places group to renderSuggest
    new_renderSuggest = '''def renderSuggest(persons, works, places, q) {
  const box = document.getElementById('searchSuggest');
  _sgItems = []; let html = '';
  
  if (!persons.length && !works.length && !places.length) {
    html = `<div class="sr-suggest-empty">Không có gợi ý cho “${_sgEsc(q)}”. Nhấn Enter để tìm đầy đủ.</div>`;
  } else {
    if (persons.length) {
      html += '<div class="sr-suggest-group-title">Nhân vật</div>';
      persons.forEach(p => { 
        const idx = _sgItems.length; 
        _sgItems.push({ type: 'person', data: p }); 
        html += `<div class="sr-suggest-item" data-idx="${idx}" role="option"> 
            <div><span class="sr-suggest-name">${_sgEsc(p.name_vi || p.name_zh)}</span><span class="sr-suggest-han">${_sgEsc(p.name_zh)}</span></div> 
            <div class="sr-suggest-meta">${_sgEsc(_sgPersonMeta(p))}</div> 
          </div>`; 
      });
    }
    if (works.length) {
      html += '<div class="sr-suggest-group-title">Kinh sách / Dịch giả</div>';
      works.forEach(w => { 
        const idx = _sgItems.length; 
        _sgItems.push({ type: 'work', data: w }); 
        html += `<div class="sr-suggest-item" data-idx="${idx}" role="option"> 
            <div><span class="sr-suggest-name">${_sgEsc(w.title_vi || w.title_zh)}</span><span class="sr-suggest-han">${_sgEsc(w.title_zh)}</span></div> 
            <div class="sr-suggest-meta">${_sgEsc(_sgWorkMeta(w))}</div> 
          </div>`; 
      });
    }
    if (places.length) {
      html += '<div class="sr-suggest-group-title">📍 Địa danh</div>';
      places.forEach(p => { 
        const idx = _sgItems.length; 
        _sgItems.push({ type: 'place', data: p }); 
        html += `<div class="sr-suggest-item" data-idx="${idx}" role="option"> 
            <div><span class="sr-suggest-name">${_sgEsc(p.name_vi || p.name_zh)}</span><span class="sr-suggest-han">${_sgEsc(p.name_zh)}</span></div> 
            <div class="sr-suggest-meta">${_sgEsc(p.name_zh)}</div> 
          </div>`; 
      });
    }
  }
  
  box.innerHTML = html;
  box.hidden = false; 
  _sgActive = -1; 
  document.getElementById('heroSearch').setAttribute('aria-expanded', 'true');
  box.querySelectorAll('.sr-suggest-item').forEach(el => { 
    el.addEventListener('mousedown', ev => { 
      ev.preventDefault(); 
      _sgSelect(parseInt(el.dataset.idx, 10)); 
    }); 
  });
}'''

    # Replace the function
    content = content[:start] + new_renderSuggest + content[end:]
    
    # Update function signature in api_search_suggest to pass places
    # First, find where _get_work_suggest_cache is called and add places
    # Then find where _get_place_suggest_cache is called (if any)
    # Also need to modify the return statement to include places
    
    # Update api_search_suggest to get places cache
    # Find where persons_cache and works_cache are obtained
    # Then get places_cache = _get_place_suggest_cache()
    # Then add places to the return JSON
    
    # This is complex, so let me find where the function ends and add places there
    # Actually, let me look for where it returns the JSON
    return_json_start = content.find('return jsonify({')
    if return_json_start == -1:
        print("ERROR: Could not find return statement in api_search_suggest")
        return False
    
    # The return statement is around line 2500-2600 in the file
    # Let me find the exact location
    json_end = content.find('})', return_json_start)
    if json_end == -1:
        print("ERROR: Could not find end of JSON return in api_search_suggest")
        return False
    
    # The return statement is near the end of the function
    # Let me find the line with 'return jsonify'
    return_line = content.find('return jsonify({', return_json_start)
    if return_line == -1:
        print("ERROR: Could not find return jsonify line")
        return False
    
    # Let me find the exact line numbers
    lines = content.split('\n')
    for i in range(return_line, len(lines)):
        if 'return jsonify({' in lines[i]:
            # Found the line with return
            json_start_line = i
            # Find end of the JSON object
            json_end_line = i
            while json_end_line < len(lines) and '}' not in lines[json_end_line]:
                json_end_line += 1
            # Add places field to the JSON
            lines[json_end_line] = lines[json_end_line].replace('"places": []', '"places": places,' + lines[json_end_line])
            # Also need to make sure places_cache is obtained
            # Let me find where places_cache is obtained
            places_line = content.find('_get_place_suggest_cache()')
            if places_line == -1:
                # Add it before the return
                places_line = content.find('_get_work_suggest_cache()')  # use this as reference
                places_line = content.rfind('\n', 0, places_line)
                places_line = places_line + 1
                content = content[:places_line] + '_get_place_suggest_cache()\n' + content[places_line:]
    
    # Actually, let's simplify: modify the return statement to include places
    # Find the exact location of the return statement
    json_end_pos = content.find('})', return_line)
    if json_end_pos == -1:
        print("ERROR: Could not find end of JSON in api_search_suggest")
        return False
    
    # Replace the return statement to include places
    # First, find where places_cache is obtained
    # Let me look for where places_cache is obtained
    places_cache_line = content.find('_get_place_suggest_cache()')
    if places_cache_line == -1:
        print("ERROR: Could not find places_cache_line")
        return False
    
    # Insert places_cache = _get_place_suggest_cache() before the return
    # Let me find the line before the return
    return_line_pos = content.find('return jsonify({', return_line)
    return_line_pos = content.rfind('\n', 0, return_line_pos) + 1
    return_line_pos = content.find('\n', return_line_pos) + 1
    
    # Actually, let me just modify the return statement directly
    # Find the exact JSON structure
    json_start = content.find('return jsonify({')
    json_end_pos = content.find('})', json_start)
    if json_start == -1 or json_end_pos == -1:
        print("ERROR: Could not locate return statement in api_search_suggest")
        return False
    
    # Extract the JSON part to modify
    json_part = content[json_start:json_end_pos]
    # Split into lines to modify
    json_lines = json_part.split('\n')
    # Find where to insert places
    places_insert_pos = -1
    for i, line in enumerate(json_lines):
        if '"persons"' in line or '"works"' in line:
            places_insert_pos = i
            break
    
    if places_insert_pos != -1:
        # Insert places field after 'works' field
        json_lines.insert(places_insert_pos + 1, '    "places": places,')

    # Join back and replace
    new_json_part = '\n'.join(json_lines)
    content = content[:json_start] + new_json_part + content[json_end_pos+2:]
    
    # Also need to modify the function signature to accept places
    # Find the function definition line
    func_start = content.find('def api_search_suggest():')
    if func_start == -1:
        print("ERROR: Could not find api_search_suggest function definition")
        return False
    
    # Find the parameters line
    params_line = content.find('def api_search_suggest():', func_start)
    params_end = content.find(':', params_line) + 1
    params_end = content.find('\n', params_end)
    
    # The current signature is def api_search_suggest():
    # Change to def api_search_suggest(persons, works, places, q):
    params_line = content[params_line:params_end].replace('def api_search_suggest():', 'def api_search_suggest(persons, works, places, q):')
    content = content[:params_line] + params_line + content[params_end:]
    
    # Also need to modify the function call to get places
    # Find where persons_cache and works_cache are obtained
    # Then add places_cache = _get_place_suggest_cache()
    # Then modify the return statement
    
    # This is getting too complex for a quick edit. Let me simplify:
    # Since we're modifying the return statement to include places, and we need to get places_cache,
    # let me find where _get_work_suggest_cache is called and add places_cache right after that
    
    # Let me find where _get_work_suggest_cache is called
    works_cache_line = content.find('_get_work_suggest_cache()')
    if works_cache_line == -1:
        print("ERROR: Could not find _get_work_suggest_cache() call")
        return False
    
    # Insert places_cache = _get_place_suggest_cache() after that line
    content = content[:works_cache_line + 1] + '_get_place_suggest_cache()\n' + content[works_cache_line + 1:]
    
    # Now modify the return statement to include places
    # Let's find the return statement again
    return_start = content.find('return jsonify({')
    if return_start == -1:
        print("ERROR: Could not find return statement")
        return False
    
    # Find the end of the return statement
    return_end = content.find('})', return_start) + 2
    # Replace the return statement
    new_return = '''return jsonify({
    "success": True,
    "persons": persons,
    "works": works,
    "places": places,
    "_timing_ms": {"persons": round(t_persons_ms, 1), "works": round(t_works_ms, 1), "places": round(t_places_ms, 1)},
})'''
    
    # Replace the return statement
    content = content[:return_start] + new_return + content[return_end:]
    
    # Write back
    with open(html_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    
    print("✓ index.html updated")
    return True

def main():
    print("Starting T456 implementation...")
    
    # Step 1: Edit core.py
    if not edit_core_py():
        print("❌ Failed to edit core.py")
        return
    
    # Step 2: Edit routes_lineage.py
    if not edit_routes_lineage_py():
        print("❌ Failed to edit routes_lineage.py")
        return
    
    # Step 3: Edit index.html
    if not edit_index_html():
        print("❌ Failed to edit index.html")
        return
    
    print("✅ All files updated successfully!")
    return True

if __name__ == "__main__":
    main()