"""
================================================================================
📜 THIỀN TÔNG NIÊNẤN - VERSION 4.5.0
================================================================================
UPDATED (2026-03-27):
- [Backend returns TREE]: New API /api/get_tree returns nested children[]
- [Frontend just renders]: No more graph-to-tree conversion in JS
- [New API]: /api/monk_uri - get RDF URI from monk name
- [Max depth]: 10 levels for full lineage tree
- [Uses bkg:hasDisciple]: Forward relationship for tree building
================================================================================
"""

import os, requests, json, re, unicodedata
from flask import Flask, request, jsonify, send_file, send_from_directory

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
GRAPHDB_URL = "http://localhost:7200/repositories/buddhist"

# Load monk names for autocomplete
MONK_NAMES_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/data/processed/monk_names.json'
monk_names_cache = []
try:
    with open(MONK_NAMES_FILE, 'r', encoding='utf-8') as f:
        monk_names_cache = json.load(f)
except:
    pass

# Load lineage_tree.json for offline fallback
LINEAGE_TREE_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/data/lineage_tree.json'
lineage_tree_data = {}
try:
    with open(LINEAGE_TREE_FILE, 'r', encoding='utf-8') as f:
        lineage_tree_data = json.load(f)
except:
    pass

# LINEAGE_DATA mapping for finding phap phai founders
# Key = dharmaLineageName pattern, Value = founder name (vi)
LINEAGE_FOUNDERS = {
    # Vietnamese phap phai
    "Dòng Lâm Tế Chúc Thánh Việt Nam": "Minh Hải Pháp Bảo",  # gen=71
    "Dòng Lâm Tế Liễu Quán Việt Nam": "Thiệt Diệu Liễu Quán",  # gen=72
    "Dòng Lâm Tế Nguyên Thiều Việt Nam": "Nguyên Thiều Siêu Bạch",  # gen=? (not in DB)
    "Dòng Lâm Tế Gia Phổ Việt Nam": "Phật Ý Linh Nhạc",  # gen=72
    "Dòng Lâm Tế Hoàng Long": "Minh Hải Pháp Bảo",  # same founder as Chuc Thanh
    "Tỳ Ni Đa Lưu Chi Tông Việt Nam": "Trần Nhân Tông",  # gen=? (not in DB)
    "Tông Tào Động Việt Nam": "Động Sơn Lương Giới",  # gen=38
    
    # Chinese/Sanskrit branches
    "Dòng Lâm Tế Dương Kỳ": "Dương Kỳ Phương Hội",  # gen=45
    "Phái Dương Kì thuộc Lâm Tế Tông Trung Quốc": "Dương Kỳ Phương Hội",
    "Tông Lâm Tế Trung Hoa": "Lâm Tế Nghĩa Huyền",  # gen=38
    "Tông Tào Động Trung Hoa": "Động Sơn Lương Giới",  # gen=38
    "Tông Tào Động Hàn Quốc": "Động Sơn Lương Giới",
    "Tông Tào Động Nhật Bản": "Động Sơn Lương Giới",
    "Tông Thạch Đầu Trung Hoa": "Thạch Đầu Hy Thiên",  # gen=35
    "Thiền Tông Trung Hoa - Nam Tông": "Mã Tổ Đạo Nhất",  # gen=35
    "Thiền Tông Trung Hoa - Bắc Tông": "Bồ Đề Đạt Ma",  # gen=? (not in DB)
    "Thiền Tông Trung Hoa - Hà Trạch Tông": "Mã Tổ Đạo Nhất",
    "Thiền Tông Trung Hoa": "Bồ Đề Đạt Ma",  # fallback
    "Thiền Tông Ấn Độ": "Ma Ha Ca Diếp",  # gen=1
    "Ngưu Đầu Tông Trung Hoa": "Thạch Đầu Hy Thiên",
    "Phái Bách Trượng": "Thạch Đầu Hy Thiên",
    "Phái Nam Nhạc": "Mã Tổ Đạo Nhất",
    "Phái Trung Quán": "Bồ Đề Đạt Ma",
    "Tam Luận Tông": "Bồ Đề Đạt Ma",
    "Tông Pháp Nhãn Trung Hoa": "Bồ Đề Đạt Ma",
    "Tông Quy Ngưỡng Trung Hoa": "Thạch Đầu Hy Thiên",
    "Tông Vân Môn Trung Hoa": "Mã Tổ Đạo Nhất",
    "Bát Tông": "Ma Ha Ca Diếp",
    "Kinh Lượng Bộ": "Ma Ha Ca Diếp",
    "Tịnh Độ Tông": "Ma Ha Ca Diếp",
    "Đại thừa": "Ma Ha Ca Diếp",
}

def get_monk_generation(monk_name):
    """Query generationOrder của một thiền sư từ GraphDB"""
    monk_name_nfd = unicodedata.normalize('NFD', monk_name)
    query = '''PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?actualLabel ?g WHERE {
        ?s rdfs:label ?actualLabel .
        FILTER(lang(?actualLabel) = "vi")
        OPTIONAL { ?s bkg:generationOrder ?g }
    }'''
    try:
        r = requests.get(GRAPHDB_URL, params={'query': query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r['results']['bindings']
        for b in bindings:
            label = b.get('actualLabel', {}).get('value', '')
            if label:
                label_nfd = unicodedata.normalize('NFD', label)
                if label_nfd == monk_name_nfd or label == monk_name:
                    if 'g' in b:
                        return int(b['g']['value'])
                    break
    except:
        pass
    return None

def get_phap_phai_doi(ln, g):
    """Tính đời pháp phái: G(hiện tại) - G(founder) + 1"""
    if not ln:
        return g
    
    founder_name = None
    for key, founder in LINEAGE_FOUNDERS.items():
        if key in ln or ln in key:
            founder_name = founder
            break
    
    if founder_name:
        founder_g = get_monk_generation(founder_name)
        if founder_g:
            return g - founder_g + 1
    
    return g

@app.route('/api/monk_names')
def get_monk_names():
    """Return all monk names for autocomplete"""
    return jsonify(monk_names_cache)

@app.route('/api/search_monk')
def search_monk():
    """Search monk by name and return lineage data"""
    name = request.args.get('q', '').strip()
    if not name:
        return jsonify([])
    
    # Search in monk names
    matches = [n for n in monk_names_cache if name.lower() in n.lower()][:20]
    return jsonify(matches)

@app.route('/api/monk_uri')
def get_monk_uri():
    """Get RDF URI for a monk by name"""
    try:
        name = request.args.get('name', '').strip()
        print(f"[monk_uri] name: {repr(name)}", flush=True)
        
        if not name:
            return jsonify({"error": "no name"})
        
        # Try to decode UTF-8
        import urllib.parse
        try:
            name = urllib.parse.unquote(name)
        except:
            pass
        
        print(f"[monk_uri] after unquote: {repr(name)}", flush=True)
        
        name_lower = name.lower()
        
        # First try exact match from cache (most reliable)
        matching_names = [n for n in monk_names_cache if name_lower == n.lower()]
        
        # Then try partial match
        if not matching_names:
            matching_names = [n for n in monk_names_cache if name_lower in n.lower()]
        
        if matching_names:
            exact_name = matching_names[0]
            
            # Use lineage_tree.json as lookup - keys are names, 'id' is URI
            if lineage_tree_data and 'monks' in lineage_tree_data:
                monks = lineage_tree_data.get('monks', {})
                
                # Search by exact name first
                if exact_name in monks:
                    info = monks[exact_name]
                    uri = info.get('id') if isinstance(info, dict) else None
                    if uri:
                        return jsonify({"name": exact_name, "uri": uri})
                
                # Try case-insensitive match in monks
                for monk_name, info in monks.items():
                    if monk_name.lower() == name_lower:
                        uri = info.get('id') if isinstance(info, dict) else None
                        if uri:
                            return jsonify({"name": monk_name, "uri": uri})
                
                # Then try partial
                for monk_name, info in monks.items():
                    if isinstance(info, dict) and name_lower in monk_name.lower():
                        uri = info.get('id')
                        if uri:
                            return jsonify({"name": monk_name, "uri": uri})
            
            # Fallback to GraphDB
            try:
                query1 = f'''
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                
                SELECT ?s WHERE {{
                  ?s rdfs:label "{exact_name}"@vi .
                }} LIMIT 5
                '''
                
                r1 = requests.get(GRAPHDB_URL, params={'query': query1}, headers={'Accept': 'application/sparql-results+json'})
                data1 = r1.json()
                bindings1 = data1.get('results', {}).get('bindings', [])
                
                for b in bindings1:
                    uri = b.get('s', {}).get('value')
                    if uri:
                        query2 = f'''
                        PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
                        
                        ASK WHERE {{
                          <{uri}> a bkg:Monk .
                        }}
                        '''
                        
                        r2 = requests.get(GRAPHDB_URL, params={'query': query2}, headers={'Accept': 'application/sparql-results+json'})
                        if r2.json().get('boolean', False):
                            return jsonify({"name": name, "uri": uri})
            except Exception as e:
                return jsonify({"error": f"GraphDB error: {str(e)}"})
        
        return jsonify({"error": "monk not found"})
    except Exception as e:
        import traceback
        return jsonify({"error": f"Server error: {traceback.format_exc()}"})

@app.route('/api/get_lineage')
def get_lineage():
    """Get lineage data: teacher and students for a monk"""
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({"error": "no name"})
    
    # Handle UTF-8 encoding from browser (may come as encoded or decoded)
    import urllib.parse
    import unicodedata
    try:
        # Try to decode if it looks encoded (contains % or looks garbled)
        if '%' in name or 'Ã' in name:
            name = urllib.parse.unquote(name)
    except:
        pass
    
    # Normalize name for matching
    name_normalized = unicodedata.normalize('NFC', name)
    name_lower = name_normalized.lower()
    
    # Helper to remove diacritics for fuzzy matching
    def remove_diacritics(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')
    name_nodiac = remove_diacritics(name_normalized).lower()
    
    # Query GraphDB for teacher - 1 đời lên
    teacher_query = f'''
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?teacher ?label WHERE {{
        ?s rdfs:label ?actualLabel .
        FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{name}")))
        ?s bkg:hasTeacher ?t .
        ?t rdfs:label ?label .
        FILTER(lang(?label) = "vi")
    }}
    '''
    
    # Query GraphDB for grandTeacher (teacher's teacher) - 2 đời lên
    grand_teacher_query = f'''
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?grandTeacher ?label WHERE {{
        ?s rdfs:label ?actualLabel .
        FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{name}")))
        ?s bkg:hasTeacher ?t .
        ?t bkg:hasTeacher ?gt .
        ?gt rdfs:label ?label .
        FILTER(lang(?label) = "vi")
    }}
    '''
    
    # Query for great_teacher (3 đời lên từ monk) - for reference
    great_teacher_query = f'''
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?gt ?label WHERE {{
        ?s rdfs:label ?actualLabel .
        FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{name}")))
        ?s bkg:hasTeacher ?t1 .
        ?t1 bkg:hasTeacher ?t2 .
        ?t2 bkg:hasTeacher ?gt .
        ?gt rdfs:label ?label .
        FILTER(lang(?label) = "vi")
    }}
    '''
    
    # Query GraphDB for students - find monks who have this monk as teacher
    students_query = f'''
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?student ?label WHERE {{
        ?student bkg:hasTeacher ?s .
        ?s rdfs:label ?actualLabel .
        FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{name}")))
        ?student rdfs:label ?label .
        FILTER(lang(?label) = "vi")
    }}
    '''
    
    # Query GraphDB for students - find monks who have this monk as teacher
    students_query = f'''
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?student ?label WHERE {{
        ?student bkg:hasTeacher ?s .
        ?s rdfs:label ?actualLabel .
        FILTER(LCASE(STR(?actualLabel)) = LCASE("{name}"))
        ?student rdfs:label ?label .
        FILTER(lang(?label) = "vi")
    }}
    '''
    
    try:
        teachers = []
        grand_teacher = None
        great_teacher = None
        students = []
        
        # Get ALL teachers (might be multiple)
        r = requests.get(GRAPHDB_URL, params={'query': teacher_query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r.get('results', {}).get('bindings', [])
        for b in bindings:
            t = b.get('label', {}).get('value')
            if t:
                teachers.append(t)
        
        # FALLBACK: If no teacher in GraphDB, try lineage_tree.json
        if not teachers and lineage_tree_data and 'monks' in lineage_tree_data:
            monks = lineage_tree_data.get('monks', {})
            # Try exact match with normalized name first
            if name_normalized in monks:
                teacher = monks[name_normalized].get('teacher')
                if teacher:
                    teachers = [teacher]
            else:
                # Try case-insensitive match with normalized
                for monk_key, monk_data in monks.items():
                    if unicodedata.normalize('NFC', monk_key).lower() == name_lower:
                        teacher = monk_data.get('teacher')
                        if teacher:
                            teachers = [teacher]
                        break
                # Last resort: use diacritics-free match to handle Nhật vs Nhất issue
                if not teachers:
                    for monk_key, monk_data in monks.items():
                        norm_key = unicodedata.normalize('NFC', monk_key)
                        key_nodiac = remove_diacritics(norm_key).lower()
                        # Check if base letters match (Mã Tổ Đạo Nhật vs Mã Tổ Đạo Nhất)
                        if key_nodiac == name_nodiac:
                            teacher = monk_data.get('teacher')
                            if teacher:
                                teachers = [teacher]
                                break
        
        # Get grandTeacher (teacher's teacher) - 2 levels up
        r = requests.get(GRAPHDB_URL, params={'query': grand_teacher_query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r.get('results', {}).get('bindings', [])
        if bindings:
            grand_teacher = bindings[0].get('label', {}).get('value')
        
        # Get great_teacher (true 1 đời lên từ monk) - 4 levels up
        r = requests.get(GRAPHDB_URL, params={'query': great_teacher_query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r.get('results', {}).get('bindings', [])
        if bindings:
            great_teacher = bindings[0].get('label', {}).get('value')
        
        # Get students
        r = requests.get(GRAPHDB_URL, params={'query': students_query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r.get('results', {}).get('bindings', [])
        for b in bindings:
            student_name = b.get('label', {}).get('value')
            if student_name:
                students.append(student_name)
        
        return jsonify({
            "name": name_normalized,
            "teachers": teachers,  # All teachers (for choosing main branch)
            "teacher": teachers[0] if teachers else None,  # Keep backward compat
            "grand_teacher": grand_teacher,  # Teacher's teacher for expandUp
            "great_teacher": great_teacher,  # True 1 đời lên - for expandUp by 1 generation
            "students": students[:50]  # Increased limit to 50 students
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/get_tree')
def get_tree():
    """Get nested tree structure - returns tree not graph"""
    monk_id = request.args.get('id', '').strip()
    monk_name = request.args.get('name', '').strip()
    
    # Handle UTF-8 encoding from browser (may come as encoded or decoded)
    import urllib.parse
    try:
        # Try to decode if it looks encoded (contains % or looks garbled)
        if '%' in monk_name or 'Ã' in monk_name:
            monk_name = urllib.parse.unquote(monk_name)
    except:
        pass
    
    with open('/tmp/debug_tree.log', 'a') as f:
        f.write(f"[get_tree] id={repr(monk_id)}, name={repr(monk_name)}\n")
    
    # If name provided, look up URI from lineage_tree.json
    if monk_name and not monk_id:
        import urllib.parse
        import unicodedata
        # Handle double-encoded UTF-8 - decode multiple times until proper
        original_name = monk_name
        for _ in range(3):
            try:
                decoded = urllib.parse.unquote(monk_name)
                if decoded == monk_name:
                    break
                monk_name = decoded
            except:
                break
        # If still has garbled chars, try bytes approach
        if 'Ã' in monk_name or 'â' in monk_name:
            try:
                monk_name = urllib.parse.unquote(original_name.encode('latin1').decode('utf8'))
            except:
                pass
        name_normalized = unicodedata.normalize('NFC', monk_name)
        name_lower = name_normalized.lower()
        
        # Try exact match from lineage_tree.json (case-insensitive)
        if lineage_tree_data and 'monks' in lineage_tree_data:
            monks = lineage_tree_data.get('monks', {})
            
            # First: Try exact match
            for mname, minfo in monks.items():
                if unicodedata.normalize('NFC', mname).lower() == name_lower:
                    monk_id = minfo.get('id') if isinstance(minfo, dict) else None
                    if monk_id:
                        break
            
            # Second: If no exact match, try partial match with LONGEST match priority
            if not monk_id:
                best_match = None
                best_len = 0
                for mname, minfo in monks.items():
                    if isinstance(minfo, dict):
                        # Check if search term is contained in monk name
                        if name_lower in mname.lower():
                            # Prefer longer matches
                            if len(mname) > best_len:
                                best_len = len(mname)
                                best_match = minfo.get('id')
                monk_id = best_match
    
    if not monk_id:
        return jsonify({"error": "no id or name"})
    
    max_depth = 1  # Return 2 levels: depth 0 (current), depth 1 (students only)
    
    try:
        visited = set()
        tree = build_tree_recursive(monk_id, visited, 0, max_depth)
        if not tree:
            return jsonify({"error": "monk not found"})
        return jsonify(tree)
    except Exception as e:
        return jsonify({"error": str(e)})

def calculate_depth(monk_key, monks, visited):
    """Calculate the depth of a monk's lineage (how many generations down)"""
    if not monk_key or monk_key in visited:
        return 0
    visited.add(monk_key)
    
    info = monks.get(monk_key, {})
    student_names = info.get('students', []) if isinstance(info, dict) else []
    
    if not student_names:
        return 1
    
    max_child_depth = 0
    for student_name in student_names:
        if student_name in monks:
            child_depth = calculate_depth(student_name, monks, visited.copy())
            max_child_depth = max(max_child_depth, child_depth)
    
    return max_child_depth + 1

def build_tree_recursive(monk_uri, visited, depth, max_depth):
    """Recursively build nested tree using lineage_tree.json as primary source"""
    if depth > max_depth or monk_uri in visited:
        return None
    
    visited.add(monk_uri)
    
    # Get monk name from lineage_tree.json using URI
    monk_name = None
    monks = lineage_tree_data.get('monks', {})
    monk_key = None
    for name, info in monks.items():
        if isinstance(info, dict) and info.get('id') == monk_uri:
            monk_name = name
            monk_key = name
            break
    
    if not monk_name:
        # Try to find by name in URI
        uri_name = monk_uri.replace('ex:monk/', '').replace('_', ' ')
        for name, info in monks.items():
            if isinstance(info, dict):
                label = info.get('label', '').lower()
                if uri_name.replace('-', ' ').lower() in label or label in uri_name.replace('-', ' ').lower():
                    monk_name = name
                    monk_key = name
                    break
    
    if not monk_key:
        # Fallback: query GraphDB for label
        query = f'''
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?label WHERE {{
          <{monk_uri}> rdfs:label ?label .
          FILTER(lang(?label) = "vi")
        }} LIMIT 1
        '''
        try:
            r = requests.get(GRAPHDB_URL, params={'query': query}, headers={'Accept': 'application/sparql-results+json'}).json()
            bindings = r.get('results', {}).get('bindings', [])
            if bindings:
                monk_name = bindings[0].get('label', {}).get('value', monk_uri)
                monk_key = monk_name
        except:
            pass
    
    if not monk_key:
        return None
    
    # Get students from lineage_tree.json
    info = monks.get(monk_key, {})
    student_names = info.get('students', []) if isinstance(info, dict) else []
    
    # Build node
    node = {
        "name": monk_key,
        "id": monk_uri,
        "children": []
    }
    
    # Recursively build children from lineage_tree.json
    for student_name in student_names:
        student_info = monks.get(student_name, {})
        if isinstance(student_info, dict):
            student_uri = student_info.get('id', f'ex:monk/{student_name.replace(" ", "_").lower()}')
            child_node = build_tree_recursive(student_uri, visited, depth + 1, max_depth)
            if child_node:
                node["children"].append(child_node)
    
    # If this is the root (depth=0), sort children by depth - main tree in center
    if depth == 0 and node.get('children'):
        # Calculate depth for each child
        for child in node['children']:
            child_name = child.get('name')
            if child_name:
                child['depth'] = calculate_depth(child_name, monks, set())
        
        # Sort by depth descending
        node['children'].sort(key=lambda x: x.get('depth', 0), reverse=True)
        
        # Mark the first one (deepest) as mainTree
        if node['children']:
            node['children'][0]['mainTree'] = True
    
    return node

@app.route('/api/trace_lineage')
def trace_lineage():
    """Trace lineage from current monk back to Sơ Tổ (Bồ Đề Đạt Ma)"""
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({"error": "no name"})
    
    chain = []
    current_name = name
    max_depth = 50
    
    try:
        # First, check if the starting monk has dharmaLineageName (they founded a lineage)
        start_query = f'''
        PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?lineageLabel WHERE {{
            ?s rdfs:label ?actualLabel .
            FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{name}")))
            OPTIONAL {{ ?s bkg:dharmaLineageName ?lineageLabel . FILTER(lang(?lineageLabel) = "vi") }}
        }}
        '''
        
        r = requests.get(GRAPHDB_URL, params={'query': start_query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r.get('results', {}).get('bindings', [])
        
        if bindings and bindings[0].get('lineageLabel'):
            lineage_name = bindings[0].get('lineageLabel', {}).get('value')
            chain.append(name)
            chain.append(f"[{lineage_name}]")
        else:
            chain.append(name)
        
        # Now trace up through teachers - try multiple predicates
        for i in range(max_depth):
            # Try different predicates to find teacher
            teacher = None
            
            # Method 1: hasTeacher
            query1 = f'''
            PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?teacher WHERE {{
                ?s rdfs:label ?actualLabel .
                FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{current_name}")))
                ?s bkg:hasTeacher ?t .
                ?t rdfs:label ?teacher .
                FILTER(lang(?teacher) = "vi")
            }}
            '''
            r1 = requests.get(GRAPHDB_URL, params={'query': query1}, headers={'Accept': 'application/sparql-results+json'}).json()
            bindings1 = r1.get('results', {}).get('bindings', [])
            if bindings1:
                teacher = bindings1[0].get('teacher', {}).get('value')
            
            # Method 2: greatTeacher (1 đời lên)
            if not teacher:
                query2 = f'''
                PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?teacher WHERE {{
                    ?s rdfs:label ?actualLabel .
                    FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{current_name}")))
                    ?s bkg:greatTeacher ?t .
                    ?t rdfs:label ?teacher .
                    FILTER(lang(?teacher) = "vi")
                }}
                '''
                r2 = requests.get(GRAPHDB_URL, params={'query': query2}, headers={'Accept': 'application/sparql-results+json'}).json()
                bindings2 = r2.get('results', {}).get('bindings', [])
                if bindings2:
                    teacher = bindings2[0].get('teacher', {}).get('value')
            
            # Method 3: Find by reverse hasDisciple (teacher có hasDisciple → student)
            if not teacher:
                query3 = f'''
                PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?teacher WHERE {{
                    ?t rdfs:label ?teacher .
                    FILTER(lang(?teacher) = "vi")
                    ?t bkg:hasDisciple ?s .
                    ?s rdfs:label ?actualLabel .
                    FILTER(CONTAINS(LCASE(?actualLabel), LCASE("{current_name}")))
                }}
                '''
                r3 = requests.get(GRAPHDB_URL, params={'query': query3}, headers={'Accept': 'application/sparql-results+json'}).json()
                bindings3 = r3.get('results', {}).get('bindings', [])
                if bindings3:
                    teacher = bindings3[0].get('teacher', {}).get('value')
            
            # FALLBACK: If not found in GraphDB, try lineage_tree.json
            if not teacher and lineage_tree_data and 'monks' in lineage_tree_data:
                monks = lineage_tree_data.get('monks', {})
                # Try exact match first
                if current_name in monks:
                    teacher = monks[current_name].get('teacher')
                else:
                    # Try case-insensitive match
                    for monk_key, monk_data in monks.items():
                        if monk_key.lower() == current_name.lower():
                            teacher = monk_data.get('teacher')
                            break
            
            if not teacher:
                break
            
            # Detect infinite loop - teacher same as current (duplicate)
            if teacher == current_name:
                break
            
            chain.append(teacher)
            current_name = teacher
            
            # Stop at Bồ Đề Đạt Ma (Bodhidharma - Sơ Tổ Thiền Tông)
            if teacher == "Bồ Đề Đạt Ma" or teacher == "Tôn Giả Bồ Đề Đạt Ma":
                break
        
        # Check if we reached the root
        reached_root = current_name == "Bồ Đề Đạt Ma" or current_name == "Tôn Giả Bồ Đề Đạt Ma"
        
        # Add stop reason
        stop_reason = None
        if reached_root:
            stop_reason = "Đã về Sơ Tổ Bồ Đề Đạt Ma"
        elif len(chain) > 0:
            last_monk = chain[-1]
            # Check if last monk is a known founder/root of a lineage
            known_roots = ["Phần Dương Thiện Chiêu", "Nam Nhạc Hoài Nhượng", "Mã Tổ Đạo Nhất", 
                          "Vô Ngôn Thông", "Thiền Sư Bồ Đề Đạt Ma"]
            if last_monk in known_roots:
                stop_reason = f"Đã về Sơ Tổ dòng: {last_monk}"
            else:
                stop_reason = "Không tìm thấy thầy tiếp theo trong dữ liệu"
        
        return jsonify({
            "chain": chain,
            "total": len(chain),
            "reached_root": reached_root,
            "stop_reason": stop_reason
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/get_founders')
def get_founders():
    """Check which monks are lineage founders"""
    names_json = request.args.get('names', '[]')
    try:
        names = json.loads(names_json)
    except:
        names = []
    
    result = {}
    if not names:
        return jsonify(result)
    
    # Limit names to prevent query timeout
    names = names[:50]  # Max 50 names at once
    
    # Build filter for all names - multiple OR conditions
    try:
        filters = " || ".join([f'LCASE(STR(?label)) = LCASE("{n.replace('"', '\\\"')}")' for n in names])
    except:
        filters = ""
    
    if not filters:
        return jsonify(result)
    
    query = f'''
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label ?isFounder WHERE {{
        ?s rdfs:label ?label .
        ?s bkg:isLineageFounder ?isFounder .
        FILTER({filters})
    }}
    '''
    
    try:
        r = requests.get(GRAPHDB_URL, params={'query': query}, headers={'Accept': 'application/sparql-results+json'}, timeout=10)
        if r.status_code != 200:
            return jsonify({"error": f"HTTP {r.status_code}"})
        r = r.json()
        bindings = r.get('results', {}).get('bindings', [])
        for b in bindings:
            label = b.get('label', {}).get('value')
            isFounder = b.get('isFounder', {}).get('value')
            if label:
                result[label] = (str(isFounder).lower() == 'true')
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

# [BLOCK 2: DỮ LIỆU GỐC - TỪ JSON-LD]
LINEAGE_GRAPH_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/data/lineage_graph.jsonld'

# Load monks for founder lookup
MONK_LOOKUP = {}
try:
    import json
    with open('/opt/phatphaponline_gradio/truyenthua/visjs-app/data/lineage_tree.json', 'r', encoding='utf-8') as f:
        monk_data = json.load(f)
        for name, info in monk_data.get('monks', {}).items():
            monk_id = info.get('id', '')
            if monk_id:
                MONK_LOOKUP[monk_id] = name
except:
    pass

def load_lineage_data():
    """Load 13 tông phái from JSON-LD file"""
    try:
        import json
        with open(LINEAGE_GRAPH_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = data.get('@graph', [])
        lineages = {}
        
        # First pass: create all lineage nodes
        for item in graph:
            lid = item.get('@id', '').replace('ex:', '')
            label = item.get('rdfs:label', {}).get('value', lid)
            founder_uri = item.get('bkg:hasFounder', {}).get('@id', '')
            # Look up founder name from MONK_LOOKUP
            founder = ""
            if founder_uri:
                founder = MONK_LOOKUP.get(founder_uri, '')
                if not founder:
                    founder = founder_uri.replace('ex:monk/', '').replace('_', ' ').title()
            lineages[lid] = {
                'id': lid,
                'label': label,
                'founder': founder,
                'children': [],
                'parent': None
            }
        
        # Second pass: build parent-child relationships
        for item in graph:
            lid = item.get('@id', '').replace('ex:', '')
            subs = item.get('bkg:hasSubLineage', [])
            if subs:
                if isinstance(subs, list):
                    for sub in subs:
                        sub_id = sub.get('@id', '').replace('ex:', '')
                        if sub_id in lineages:
                            lineages[sub_id]['parent'] = lid
                            lineages[lid]['children'].append(sub_id)
                else:
                    sub_id = subs.get('@id', '').replace('ex:', '')
                    if sub_id in lineages:
                        lineages[sub_id]['parent'] = lid
                        lineages[lid]['children'].append(sub_id)
            
            # Check isSubLineageOf
            parent = item.get('bkg:isSubLineageOf', {})
            if parent:
                parent_id = parent.get('@id', '').replace('ex:', '')
                if parent_id in lineages and not lineages[lid]['parent']:
                    lineages[lid]['parent'] = parent_id
                    lineages[parent_id]['children'].append(lid)
        
        # Convert to flat list for D3 stratify
        result = []
        for lid, info in lineages.items():
            result.append({
                'id': info['id'],
                'label': info['label'],
                'parent': info['parent'],
                'founder': info['founder']
            })
        
        return result
    except Exception as e:
        print(f"Error loading lineage graph: {e}")
        return []

LINEAGE_DATA = load_lineage_data()

def format_zen_bio(text):
    """Xử lý ngắt dòng hội thoại theo chuẩn kinh sách"""
    if not text: return "Đang cập nhật..."
    
    # Chuẩn hóa xuống dòng
    text = text.strip()
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    
    # Thay thế separator
    text = text.replace('---o0o---', '<br><hr class="zen-separator">')
    text = re.sub(r'\n\*\n', '<br><hr class="zen-separator"><br>', text)
    text = re.sub(r'\n\*\*\*\n', '<br><hr class="zen-separator"><br>', text)
    text = re.sub(r'\n\*\*\n', '<br><hr class="zen-separator"><br>', text)
    
    # Tách theo dấu xuống dòng tự nhiên
    lines = re.split(r'\r?\n', text)
    html_parts = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Bỏ dấu * đầu dòng
        if line.startswith('*'):
            line = line[1:].strip()
        
        # Xử lý sau khi tách dòng: bỏ khoảng trắng thừa
        line = re.sub(r'\s+', ' ', line)
        
        # Kiểm tra speaker
        # Ví dụ: "Sư đáp:", "Sư hỏi:", "Sư hỏi lại:"
        speaker_match = re.match(r'^(Sư\s+(đáp|hỏi|bảo|nói|dạy|khai|pháp|lại|hỏi lại):)', line)
        
        if speaker_match:
            speaker = speaker_match.group(1)
            content = line[len(speaker):].strip()
            html_parts.append(f'<div class="bio-dialogue"><span class="zen-speaker">{speaker}</span> {content}</div>')
        else:
            # Check for other speakers (Đáp:, Hỏi:)
            other_match = re.match(r'^(Đáp:|Hỏi:|Tăng\s+hỏi:)', line)
            if other_match:
                speaker = other_match.group(1)
                content = line[len(speaker):].strip()
                html_parts.append(f'<div class="bio-dialogue"><span class="zen-speaker">{speaker}</span> {content}</div>')
            else:
                # Đoạn trần thuật
                html_parts.append(f'<div class="bio-narrative">{line}</div>')
    
    return "".join(html_parts)

@app.route('/api/get_details')
def get_details():
    name = request.args.get('name', '').strip()
    name_nfd = unicodedata.normalize('NFD', name)
    
    query = '''PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    SELECT ?s ?actualLabel (SAMPLE(?gen) AS ?g) (SAMPLE(?ln) AS ?lineage) WHERE { 
        ?s rdfs:label ?actualLabel .
        FILTER(lang(?actualLabel) = "vi")
        OPTIONAL { ?s bkg:generationOrder ?gen }
        OPTIONAL { ?s bkg:dharmaLineageName ?ln }
    } GROUP BY ?s ?actualLabel'''
    
    try:
        r = requests.get(GRAPHDB_URL, params={'query': query}, headers={'Accept': 'application/sparql-results+json'}).json()
        bindings = r['results']['bindings']
        
        found = None
        for b in bindings:
            label = b.get('actualLabel', {})
            if isinstance(label, dict):
                label_val = label.get('value', '')
            else:
                label_val = str(label)
            
            if label_val:
                label_nfd = unicodedata.normalize('NFD', label_val)
                name_nfd = unicodedata.normalize('NFD', name)
                if label_val == name:
                    found = b
                    break
                if label_nfd == name_nfd:
                    found = b
                    break
        
        if not found:
            import sys
            sys.stderr.write(f"DEBUG: Not found. name={repr(name)}, total={len(bindings)}\n")
            sys.stderr.flush()
            return jsonify({"error": "notfound"})
        s_uri = found['s']['value']
        g = int(found['g']['value']) if 'g' in found else 0
        ln = found['lineage']['value'] if 'lineage' in found else ""
        
        note_query = f'''PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?note WHERE {{
            <{s_uri}> bkg:biographicalNote ?note .
        }} LIMIT 1'''
        
        note_content = ""
        try:
            nr = requests.get(GRAPHDB_URL, params={'query': note_query}, headers={'Accept': 'application/sparql-results+json'}).json()
            nbindings = nr['results']['bindings']
            if nbindings:
                note_content = format_zen_bio(nbindings[0].get('note', {}).get('value', ""))
        except:
            pass
        
        phap_phai_doi = get_phap_phai_doi(ln, g)
        gens = {
            "l1": f"Thiền Tông Truyền Thừa: Đời thứ {g}",
            "l2": f"Tông Tào Động Trung Hoa: Đời thứ {g-33+1}" if ("Tào Động" in ln and g >= 33) else (f"Tông Lâm Tế Trung Hoa: Đời thứ {g-37}" if ("Lâm Tế" in ln and g >= 38) else ""),
            "l3_tag": f"Pháp Phái {ln}" if ln else "Pháp Phái", "l3_val": phap_phai_doi
        }
        if "Đạo Giai" in name: gens["l2"] = "Tông Tào Động Trung Hoa: Đời thứ 43"

        return jsonify({"name": name, "note": note_content, "gens": gens})
    except Exception as e:
        import traceback
        import sys
        sys.stderr.write(f"ERROR: {str(e)}\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return jsonify({"error": str(e)})

@app.route('/data/<path:filename>')
def serve_data(filename):
    """Serve data files"""
    data_dir = '/opt/phatphaponline_gradio/truyenthua/visjs-app/data'
    return send_from_directory(data_dir, filename)

@app.route('/cyto')
def cyto_index():
    """Serve Cytoscape version"""
    try:
        with open('/opt/phatphaponline_gradio/truyenthua/visjs-app/thientong_cyto.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading cyto version: {e}", 500

@app.route('/daoanh')
def daoanh_index():
    """Serve Phật Tổ Đạo Ảnh Map Interface"""
    try:
        with open('/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading daoanh: {e}", 500

@app.route('/daoanh/<path:filename>')
def daoanh_static(filename):
    """Serve static files for daoanh"""
    daoanh_dir = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh'
    return send_from_directory(daoanh_dir, filename)

@app.route('/')
def index():
    """Simple D3.js Tree with Search - 13 lineages + search"""
    import json
    return r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Thiền Tông - Cây Phả Hệ</title>
    <script src="https://d3js.org/d3.v7.min.js" onerror="this.onerror=null; this.src='https://cdn.jsdelivr.net/npm/d3@7'"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { margin: 0; display: flex; font-family: 'Times New Roman', serif; background: #fdf5e6; height: 100vh; overflow: hidden; }
        #sidebar { width: 60px; background: #4e342e; z-index: 1000; color: white; flex-shrink: 0; }
        .side-icon { padding: 20px; cursor: pointer; text-align: center; font-size: 22px; }
        #search-container { position: absolute; left: 60px; top: 60px; width: 250px; padding: 10px; background: #4e342e; z-index: 1001; display: none; }
        #search-container.show { display: block; }
        #inp { width: 100%; max-width: 100%; padding: 10px; border: none; box-sizing: border-box; }
        #sug { background: white; color: black; max-height: 300px; overflow-y: auto; }
        #sug div { padding: 8px; cursor: pointer; }
        #sug div:hover { background: #eee; }
        #tree-area { flex-grow: 1; position: relative; background: #fff; overflow: visible !important; }
        #tree-area svg { width: 100%; height: 100%; overflow: visible !important; }
        
        /* Node styles from AGENTS.md */
        .node rect { stroke-width: 2px; rx: 8; fill: #fffde7; stroke: #8d6e63; cursor: pointer; }
        .node-main rect { stroke: #d4af37; stroke-width: 3px; }
        .node-founder rect { stroke: #9e9e9e; stroke-width: 2px; fill: #f5f5f5; }
        .node text { font-weight: bold; text-anchor: middle; font-size: 13px; fill: #4e342e; pointer-events: none; }
        .node .founder-text { font-size: 10px; fill: #888; font-weight: normal; }
        .link { fill: none; stroke: #8d6e63; stroke-width: 2px; }
        
        /* Node buttons */
        .expand-up-btn-bg, .trace-btn-bg, .expand-btn-bg { cursor: pointer; }
        
        .lineage-node rect { fill: #fffde7; stroke: #8d6e63; stroke-width: 2px; }
        .lineage-node.main rect { stroke: #d4af37; stroke-width: 4px; fill: #fff9c4; }
        .lineage-node text { font-size: 12px; text-anchor: middle; fill: #4e342e; pointer-events: none; }
        .lineage-link { fill: none; stroke: #8d6e63; stroke-width: 2px; pointer-events: none; }
        
        /* Bio Panel - Fixed as per AGENTS.md */
        #bio-panel { position: fixed; right: -460px; width: 450px; height: 100vh; background: #fffcf5; transition: 0.5s; z-index: 2000; box-shadow: -5px 0 20px rgba(0,0,0,0.15); }
        #bio-panel.open { right: 0; }
        .bio-header { background: linear-gradient(135deg, #5d4037 0%, #3e2723 100%); color: white; padding: 25px 20px; text-align: center; position: relative; border-bottom: 3px solid #d4af37; }
        .bio-close { position: absolute; right: 15px; top: 50%; transform: translateY(-50%); cursor: pointer; font-size: 22px; padding: 5px 10px; border-radius: 5px; }
        .bio-close:hover { background: rgba(255,255,255,0.2); }
        .bio-gens { background: linear-gradient(90deg, #efe4d1 0%, #f5ebd8 100%); padding: 15px 25px; border-bottom: 1px solid #d4c4a8; font-weight: bold; font-size: 14px; line-height: 1.6; }
        .bio-content { padding: 25px 30px; font-size: 17px; line-height: 2.0; color: #2b1d1a; height: 100%; overflow-y: auto; text-align: justify; white-space: pre-line; word-break: keep-all; overflow-wrap: break-word; border-left: none; box-sizing: border-box; }
        .bio-content::-webkit-scrollbar { width: 6px; }
        .bio-content::-webkit-scrollbar-thumb { background: #d4c4a8; border-radius: 3px; }
        .bio-content::-webkit-scrollbar-track { background: #f5ebd8; }
        .bio-content p { margin-bottom: 1em; word-break: keep-all; }
        
        /* Dialogue formatting */
        .bio-narrative { margin-bottom: 4px; text-indent: 24px; text-align: justify; line-height: 1.6; }
        .bio-dialogue { margin-bottom: 4px; padding: 8px 12px; background: #fffdf5; margin-left: 0px; }
        .zen-speaker { color: #5d4037; font-weight: bold; display: inline; margin-right: 8px; font-style: italic; }
        .zen-content { color: #2b1d1a; display: inline; }
        .zen-separator { border: none; border-top: 1px solid #d4c4a8; margin: 16px 0; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="side-icon" onclick="initHome()" title="Home"><i class="fas fa-home"></i></div>
        <div class="side-icon" onclick="toggleSearch()" title="Search"><i class="fas fa-search"></i></div>
    </div>
    <div id="search-container">
        <input type="text" id="inp" placeholder="Tìm Tổ sư..." oninput="searchMonk(this.value)">
        <div id="sug"></div>
    </div>
    <div id="tree-area"><svg id="canvas" style="width:100%; height:100%; overflow:visible;"><g id="viewport"></g></svg></div>
    <div id="bio-panel">
        <div class="bio-header"><b id="bio-title"></b><span class="bio-close" onclick="closeBio()">✕</span></div>
        <div id="bio-gens" class="bio-gens"></div>
        <div id="bio-content" class="bio-content"></div>
    </div>

    <script>
        const lineageData = ''' + json.dumps(LINEAGE_DATA) + ''';
        
        const width = window.innerWidth - 60;
        const height = window.innerHeight;
        // Parameters from AGENTS.md: nodeSize [280, 180]
        const NODE_HORIZONTAL_SPACING = 380; // increased to prevent label overlap
        const NODE_VERTICAL_SPACING = 180;
        const NODE_WIDTH = 200;
        const NODE_HEIGHT = 60;
        const MAX_INITIAL_DEPTH = 2; // Show depth 0,1,2 = 3 generations (teacher-current-students), collapse depth 3+

        let currentMode = 'home';
        let monkNames = [];
        let searchedMonkName = null; // Store the searched monk name for highlighting
        
        const svg = d3.select("#canvas");
        const container = d3.select("#viewport");
        svg.call(d3.zoom().scaleExtent([0.3, 2]).on("zoom", (e) => container.attr("transform", e.transform)));
        // Vertical tree layout: d.x = horizontal, d.y = vertical - from AGENTS.md
        const treeLayout = d3.tree().nodeSize([NODE_HORIZONTAL_SPACING, NODE_VERTICAL_SPACING]);
        let root;
        let initialCenterDone = false;

        // Custom layout: main tree in center, subtrees on sides, even spacing for home
        function customSearchLayout(rootData) {
            // Clone the data to avoid modifying original
            const data = JSON.parse(JSON.stringify(rootData.data));
            
            // Apply tree layout first
            const rootNode = d3.hierarchy(data);
            const layout = treeLayout(rootNode);
            
            // Always apply dynamic spacing adjustment - recursively adjust ALL children positions
            adjustAllPositions(layout, 0);
            
            return layout;
            
            function adjustAllPositions(node, level) {
                if (!node.children || node.children.length === 0) return;
                
                const childCount = node.children.length;
                
                // Ultra large spacing to prevent overlap
                let baseSpacing = 600;
                if (level === 0) baseSpacing = 600;
                else if (level === 1) baseSpacing = 700;
                else if (level === 2) baseSpacing = 850;
                else baseSpacing = 1000;
                
                // Calculate max label width among children
                let maxLabelWidth = 300;
                node.children.forEach(child => {
                    const labelLen = (child.data.name || "").length;
                    // Vietnamese chars can be wide, use larger multiplier
                    maxLabelWidth = Math.max(maxLabelWidth, labelLen * 14 + 60);
                });
                
                // Use larger of: maxLabelWidth OR baseSpacing
                const spacing = Math.max(maxLabelWidth, baseSpacing);
                const totalWidth = (childCount - 1) * spacing;
                let startX = node.x - totalWidth / 2;
                
                // Reposition children
                node.children.forEach((child, idx) => {
                    child.x = startX + idx * spacing;
                    // More vertical spacing for deeper levels
                    child.y = node.y + 200; 
                    adjustAllPositions(child, level + 1);
                });
            }
        }

        // Distribute children evenly (for home mode with 13 lineages)
        function distributeEvenly(rootNode) {
            const layout = treeLayout(rootNode);
            
            // Always adjust positions - for all levels
            if (layout.children) {
                const childCount = layout.children.length;
                const totalWidth = (childCount - 1) * 600;
                let startX = -totalWidth / 2;
                
                layout.children.forEach((child, idx) => {
                    child.x = startX + idx * 600;
                    adjustPositions(child, child.x, 1);
                });
            }
            
            function adjustPositions(node, parentX, level) {
                if (!node.children || node.children.length === 0) return;
                
                const count = node.children.length;
                
                // Ultra large spacing
                let baseSpacing = 600;
                if (level === 1) baseSpacing = 700;
                else if (level === 2) baseSpacing = 850;
                else baseSpacing = 1000;
                
                // Calculate max label width
                let maxLabelWidth = 300;
                node.children.forEach(child => {
                    const labelLen = (child.data.name || "").length;
                    maxLabelWidth = Math.max(maxLabelWidth, labelLen * 14 + 60);
                });
                
                const spacing = Math.max(maxLabelWidth, baseSpacing);
                const width = (count - 1) * spacing;
                let start = parentX - width / 2;
                
                node.children.forEach((child, idx) => {
                    child.x = start + idx * spacing;
                    // More vertical spacing for deeper levels
                    child.y = node.y + 200;
                    adjustPositions(child, child.x, level + 1);
                });
            }
            
            return layout;
        }

        // Custom search layout that PRESERVES collapsed state (_children)
        function customSearchLayoutWithCollapsed(rootData) {
            // Use the original root hierarchy - d3.tree() will only layout visible children
            // and _children will be preserved on the nodes
            const layout = treeLayout(rootData);
            
            // Apply position adjustments for visible children only
            adjustPositionsWithCollapsed(layout, 0);
            
            return layout;
            
            function adjustPositionsWithCollapsed(node, level) {
                // Only adjust positions for VISIBLE children (not _children)
                if (!node.children || node.children.length === 0) return;
                
                const children = node.children;
                const childCount = children.length;
                let baseSpacing = 600;
                if (level === 0) baseSpacing = 600;
                else if (level === 1) baseSpacing = 700;
                else if (level === 2) baseSpacing = 850;
                else baseSpacing = 1000;
                
                let maxLabelWidth = 300;
                children.forEach(child => {
                    const labelLen = (child.data.name || "").length;
                    maxLabelWidth = Math.max(maxLabelWidth, labelLen * 14 + 60);
                });
                
                const spacing = Math.max(maxLabelWidth, baseSpacing);
                const totalWidth = (childCount - 1) * spacing;
                let startX = node.x - totalWidth / 2;
                
                children.forEach((child, idx) => {
                    child.x = startX + idx * spacing;
                    child.y = node.y + 200;
                    adjustPositionsWithCollapsed(child, level + 1);
                });
            }
        }

        function buildHierarchy(data) {
            const root = d3.stratify().id(d => d.id).parentId(d => d.parent)(data);
            return root;
        }

        async function initHome() {
            currentMode = 'home';
            searchedMonkName = null;
            initialCenterDone = false;
            container.selectAll("*").remove();
            d3.select("#search-container").classed("show", false);
            
            const treeData = { id: "root", name: "Thiền Tông", children: [] };
            const map = {};
            lineageData.forEach(d => { map[d.id] = { ...d, children: [] }; });
            lineageData.forEach(d => {
                if (d.parent && map[d.parent]) map[d.parent].children.push(map[d.id]);
                else if (!d.parent) treeData.children.push(map[d.id]);
            });
            
            // Calculate depth for each top-level lineage to find the longest one
            function calcDepth(node) {
                if (!node.children || node.children.length === 0) return 1;
                let max = 0;
                node.children.forEach(c => { max = Math.max(max, calcDepth(c)); });
                return max + 1;
            }
            
            // Find the longest lineage
            let maxDepth = 0;
            let mainLineage = null;
            treeData.children.forEach(child => {
                const d = calcDepth(child);
                if (d > maxDepth) {
                    maxDepth = d;
                    mainLineage = child.id;
                }
            });
            
            // Mark the longest lineage as mainTree
            if (mainLineage) {
                treeData.children.forEach(child => {
                    child.mainTree = (child.id === mainLineage);
                });
            }
            
            root = d3.hierarchy(treeData, d => d.children);
            root.x0 = 0; root.y0 = 0;
            
            // Home mode: show all expanded (no collapse)
            update(root);
            centerTree();
        }

        async function searchRoot(name) {
            currentMode = 'search';
            searchedMonkName = name;
            initialCenterDone = false;
            container.selectAll("*").remove();
            d3.select("#search-container").classed("show", false);
            
            // First get the monk's tree data (students = đời 2)
            const params = new URLSearchParams({name: name});
            const data = await fetch(`/api/get_tree?${params}`).then(r => r.json());
            if (data.error) { alert(data.error); return; }
            
            // Then get lineage to find teacher
            const lineageParams = new URLSearchParams({name: name});
            const lineageData = await fetch(`/api/get_lineage?${lineageParams}`).then(r => r.json());
            
            // Build tree: current monk at center (đời 1), with teacher above (đời 0), students below (đời 2)
            let treeData;
            const teacherName = lineageData.teacher || lineageData.great_teacher || lineageData.grand_teacher;
            
            // Current searched monk is the ROOT (đời 1)
            treeData = data;
            
            // If teacher exists, add teacher ABOVE as parent (đời 0)
            if (teacherName) {
                const teacherNode = {
                    name: teacherName,
                    children: [data]  // Current monk is child of teacher (đời 2 relative to teacher)
                };
                treeData = teacherNode;
            }
            
            root = d3.hierarchy(treeData, d => d.children);
            root.x0 = 0; root.y0 = 0;
            
            // Collapse children deeper than MAX_INITIAL_DEPTH 
            root.each(d => { 
                if (d.depth > MAX_INITIAL_DEPTH && d.children) { 
                    d._children = d.children; 
                    d.children = null; 
                }
            });
            
            update(root);
            centerTree();
        }

        // Orthogonal V-H-V link path from AGENTS.md
        function linkPath(d) {
            const sX = d.source.x;
            const sY = d.source.y + 22; // Start from bottom of parent node
            const tX = d.target.x;
            const tY = d.target.y - 22; // End at top of child node
            const midY = (sY + tY) / 2;
            // Vertical -> Horizontal -> Vertical (orthogonal elbow)
            return `M${sX},${sY} V${midY} H${tX} V${tY}`;
        }

        function update(source) {
            let treeData;
            
            // Always use custom layout to ensure proper spacing at all levels
            if (currentMode === 'home') {
                // For home mode, use distributeEvenly
                treeData = distributeEvenly(root);
            } else {
                // For search mode, use customSearchLayout but preserve collapsed state
                // Clone only the visible structure to keep _children
                treeData = customSearchLayoutWithCollapsed(root);
            }
            
            const nodes = treeData.descendants();
            const links = treeData.links();

            const link = container.selectAll(".link").data(links, d => d.target.data.id || d.target.data.name);
            link.enter().append("path").attr("class", "link")
                .attr("d", linkPath({source: {x: source.x, y: source.y}, target: {x: source.x, y: source.y}}))
                .merge(link).transition().duration(300).attr("d", linkPath);
            link.exit().remove();

            const node = container.selectAll(".node").data(nodes, d => d.data.id || d.data.name);
            const nodeEnter = node.enter().append("g").attr("class", d => {
                let cls = "node";
                // Highlight searched monk
                if (searchedMonkName && d.data.name === searchedMonkName) {
                    cls += " node-searched";
                }
                return cls;
            }).attr("transform", d => `translate(${source.x},${source.y})`);
            
            // Auto-fit node width based on label length
            nodeEnter.each(function(d) {
                const label = d.data.label || d.data.name || "";
                const textLen = label.length;
                let nodeW = NODE_WIDTH;
                let fontSize = 13;
                if (textLen > 30) { nodeW = 320; fontSize = 11; }
                else if (textLen > 25) { nodeW = 280; fontSize = 11; }
                else if (textLen > 20) { nodeW = 240; fontSize = 12; }
                else if (textLen > 15) { nodeW = 200; fontSize = 12; }
                
                // Check if this is the searched monk
                const isSearched = searchedMonkName && d.data.name === searchedMonkName;
                const rectFill = isSearched ? "#fff9c4" : "#fffde7";
                const rectStroke = isSearched ? "#e53935" : "#8d6e63";
                const rectStrokeWidth = isSearched ? 3 : 1;
                
                const g = d3.select(this);
                g.append("rect").attr("width", nodeW).attr("height", NODE_HEIGHT).attr("x", -nodeW/2).attr("y", -NODE_HEIGHT/2).attr("rx", 8)
                    .attr("fill", rectFill).attr("stroke", rectStroke).attr("stroke-width", rectStrokeWidth)
                    .on("click", (e) => { e.stopPropagation(); showBio(d.data.name || d.data.founder); });
                g.append("text").attr("dy", -8).attr("font-size", fontSize).text(label);
                
                // Add buttons in SEARCH mode
                if (currentMode === 'search') {
                    const isGen0 = d.depth === 0 && d.parent === undefined;
                    const isGen1 = d.depth === 1;
                    const hasChildren = d.children && d.children.length > 0;
                    const hasHiddenChildren = d._children && d._children.length > 0;
                    
                    // ⬅️ Toggle siblings button for đời 1 - always show, toggle on click
                    // Icon: ⬅️ when siblings hidden, 👁️ when siblings shown
                    if (isGen1) {
                        const isSiblingsExpanded = window._siblingsState?.[d.data.name];
                        const toggleIcon = isSiblingsExpanded ? "👁️" : "⬅️";
                        g.append("rect").attr("class", "toggle-siblings-btn-bg")
                            .attr("x", -nodeW/2 - 35).attr("y", -NODE_HEIGHT/2 - 10)
                            .attr("width", 30).attr("height", 30).attr("rx", 5)
                            .attr("fill", isSiblingsExpanded ? "#FF5722" : "#4CAF50").attr("opacity", 0.8)
                            .style("cursor", "pointer")
                            .on("click", (e) => { e.stopPropagation(); toggleSiblings(d.data.name); });
                        g.append("text").attr("class", "toggle-siblings-btn")
                            .attr("x", -nodeW/2 - 20).attr("y", -NODE_HEIGHT/2 + 10)
                            .attr("text-anchor", "middle").attr("fill", "#fff").attr("font-size", "16px")
                            .style("pointer-events", "none").text(toggleIcon)
                            .on("click", (e) => { e.stopPropagation(); toggleSiblings(d.data.name); });
                    }
                    
                    // 📂 for đời 1 siblings with children (lazy load)
                    if (isGen1 && (hasChildren || hasHiddenChildren)) {
                        g.append("rect").attr("class", "expand-btn-bg")
                            .attr("x", nodeW/2 + 5).attr("y", -NODE_HEIGHT/2 - 10)
                            .attr("width", 30).attr("height", 30).attr("rx", 5)
                            .attr("fill", "#FF9800").attr("opacity", 0.8)
                            .style("cursor", "pointer")
                            .on("click", (e) => { e.stopPropagation(); toggleNode(d); });
                        g.append("text").attr("class", "expand-btn")
                            .attr("x", nodeW/2 + 20).attr("y", -NODE_HEIGHT/2 + 10)
                            .attr("text-anchor", "middle").attr("fill", "#fff").attr("font-size", "16px")
                            .style("pointer-events", "none").text("📂")
                            .on("click", (e) => { e.stopPropagation(); toggleNode(d); });
                    }
                    
                    // ⬆ for đời 0 (trace to root - Bồ Đề Đạt Ma)
                    if (isGen0) {
                        g.append("rect").attr("class", "trace-btn-bg")
                            .attr("x", nodeW/2 + 5).attr("y", -NODE_HEIGHT/2 - 10)
                            .attr("width", 30).attr("height", 30).attr("rx", 5)
                            .attr("fill", "#2196F3").attr("opacity", 0.8)
                            .style("cursor", "pointer")
                            .on("click", (e) => { e.stopPropagation(); traceToOrigin(d.data.name); });
                        g.append("text").attr("class", "trace-btn")
                            .attr("x", nodeW/2 + 20).attr("y", -NODE_HEIGHT/2 + 10)
                            .attr("text-anchor", "middle").attr("fill", "#fff").attr("font-size", "16px")
                            .style("pointer-events", "none").text("⬆")
                            .on("click", (e) => { e.stopPropagation(); traceToOrigin(d.data.name); });
                    }
                }
            });
            nodeEnter.append("text").attr("class", "founder-text").attr("dy", 12).text(d => d.data.founder ? `Khai Tổ: ${d.data.founder}` : "");

            const nodeUpdate = nodeEnter.merge(node);
            nodeUpdate.transition().duration(300).attr("transform", d => `translate(${d.x},${d.y})`);
            
            // Update rect width and text for merged nodes
            nodeUpdate.each(function(d) {
                const label = d.data.label || d.data.name || "";
                const textLen = label.length;
                let nodeW = NODE_WIDTH;
                let fontSize = 13;
                if (textLen > 30) { nodeW = 320; fontSize = 11; }
                else if (textLen > 25) { nodeW = 280; fontSize = 11; }
                else if (textLen > 20) { nodeW = 240; fontSize = 12; }
                else if (textLen > 15) { nodeW = 200; fontSize = 12; }
                
                // Highlight searched monk
                const isSearched = searchedMonkName && d.data.name === searchedMonkName;
                const rectFill = isSearched ? "#fff9c4" : "#fffde7";
                const rectStroke = isSearched ? "#e53935" : "#8d6e63";
                const rectStrokeWidth = isSearched ? 3 : 1;
                
                d3.select(this).select("rect")
                    .attr("width", nodeW)
                    .attr("x", -nodeW/2)
                    .attr("fill", rectFill)
                    .attr("stroke", rectStroke)
                    .attr("stroke-width", rectStrokeWidth);
                d3.select(this).select("text")
                    .attr("font-size", fontSize)
                    .text(label);
            });
            node.exit().remove();
            nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
            
            // Raise links to avoid being hidden - from AGENTS.md
            container.selectAll(".link").raise();
        }

        function toggle(d) {
            // If collapsed (_children exists), expand
            if (d._children) {
                d.children = d._children;
                d._children = null;
                update(d);
            } 
            // If no children at all, load from API
            else if (!d.children || d.children.length === 0) {
                loadChildrenAndExpand(d);
            }
            // If expanded, collapse
            else {
                d._children = d.children;
                d.children = null;
                update(d);
            }
        }
        
        function toggleNode(d) {
            toggle(d);
            // Focus on the clicked node after update
            setTimeout(() => focusOnNode(d), 300);
        }
        
        function focusOnNode(node) {
            if (!node) return;
            try {
                const svgNode = svg.node();
                const svgW = svgNode.clientWidth;
                const svgH = svgNode.clientHeight;
                const scale = 0.8;
                const x = (svgW / 2) - node.x * scale;
                const y = (svgH / 2) - node.y * scale;
                svg.transition().duration(500).call(
                    d3.zoom().transform, 
                    d3.zoomIdentity.translate(x, y).scale(scale)
                );
            } catch(e) {
                console.error("focusOnNode error:", e);
            }
        }
        
        async function loadChildrenAndExpand(d) {
            const monkName = d.data.name;
            if (!monkName) return;
            
            try {
                const params = new URLSearchParams({name: monkName});
                const data = await fetch(`/api/get_tree?${params}`).then(r => r.json());
                
                if (data.error || !data.children) {
                    alert("Không tìm thấy đệ tử của " + monkName);
                    return;
                }
                
                // Add children to the node - calculate depth based on parent depth
                const parentDepth = d.depth;
                d.data.children = data.children;
                d.children = d.data.children.map(c => {
                    const child = d3.hierarchy(c, n => n.children);
                    // Set the depth correctly based on parent
                    child.depth = parentDepth + 1;
                    // If this would be deeper than allowed (depth 4+), collapse it
                    if (child.depth > MAX_INITIAL_DEPTH) {
                        child._children = child.children;
                        child.children = null;
                    }
                    return child;
                });
                
                update(root);
            } catch(e) {
                console.error("Error loading children:", e);
                alert("Lỗi tải đệ tử: " + e.message);
            }
        }

        // Toggle siblings - show/hide huynh đệ đồng môn
        async function toggleSiblings(monkName) {
            if (!monkName) return;
            console.log(`toggleSiblings called for: ${monkName}, current state: ${window._siblingsState?.[monkName]}`);
            
            // Check current state - if siblings are visible, collapse; otherwise expand
            const isExpanded = window._siblingsState?.[monkName];
            
            if (isExpanded) {
                // Siblings are showing - collapse to just current monk
                await collapseSiblings(monkName);
            } else {
                // Siblings not showing - expand to show all siblings
                await expandSiblings(monkName);
            }
        }
        
        async function expandSiblings(monkName) {
            console.log(`expandSiblings: Loading teacher + siblings for ${monkName}`);
            try {
                // Get lineage data to find teacher
                const params = new URLSearchParams({name: monkName});
                const data = await fetch(`/api/get_lineage?${params}`).then(r => r.json());
                if (data.error) { alert(data.error); return; }
                
                // Get teacher - try multiple fields
                let teacherName = data.teacher || data.great_teacher || data.grand_teacher;
                if (!teacherName) {
                    console.log(`No teacher found for ${monkName} in API, trying offline JSON`);
                    const offlineParams = new URLSearchParams({name: monkName, fallback: 'true'});
                    const offlineData = await fetch(`/api/get_lineage?${offlineParams}`).then(r => r.json());
                    if (offlineData.teacher) {
                        teacherName = offlineData.teacher;
                        console.log(`Found teacher from offline: ${teacherName}`);
                    }
                    if (!teacherName) {
                        alert("Không tìm thấy thầy của " + monkName);
                        return;
                    }
                }
                
                // Get teacher's full data to find all students (siblings)
                const teacherParams = new URLSearchParams({name: teacherName});
                const teacherData = await fetch(`/api/get_tree?${teacherParams}`).then(r => r.json());
                
                // Get current monk's expanded children to preserve state
                let currentMonkChildren = [];
                if (root.children) {
                    const currentNode = root.children.find(c => c.data.name === monkName);
                    if (currentNode && currentNode.children) {
                        currentMonkChildren = currentNode.children.map(c => ({ name: c.data.name, children: c.children ? c.children.map(cc => ({ name: cc.data.name })) : [] }));
                    }
                }
                
                // Build siblings list - keep current monk with its expanded children, siblings collapsed
                let siblings = [];
                if (teacherData.children && teacherData.children.length > 0) {
                    siblings = teacherData.children.map(child => {
                        if (child.name === monkName) {
                            return { name: child.name, children: currentMonkChildren };
                        } else {
                            return { name: child.name, children: null };
                        }
                    });
                } else {
                    siblings = [{ name: monkName, children: currentMonkChildren }];
                }
                
                // Build new tree: teacher (depth 0) -> current monk + siblings (depth 1)
                const newTree = {
                    name: teacherName,
                    children: siblings
                };
                
                root = d3.hierarchy(newTree, d => d.children);
                root.x0 = 0; root.y0 = 0;
                
                // Mark current monk as having siblings visible
                if (!window._siblingsState) window._siblingsState = {};
                window._siblingsState[monkName] = true;
                
                // Collapse deeper than MAX_INITIAL_DEPTH
                root.each(d => { 
                    if (d.depth > MAX_INITIAL_DEPTH && d.children) { 
                        d._children = d.children; 
                        d.children = null; 
                    }
                });
                
                update(root);
                
                // Center on current monk (depth 1)
                setTimeout(() => {
                    const searchedNode = root.descendants().find(d => d.data.name === monkName && d.depth === 1);
                    if (searchedNode) {
                        focusOnNode(searchedNode);
                    }
                }, 500);
                
                console.log(`expandSiblings: Done - siblings shown, ${monkName} at center`);
            } catch(e) {
                console.error("Error in expandSiblings:", e);
                alert("Lỗi khi tải huynh đệ: " + e.message);
            }
        }
        
        async function collapseSiblings(monkName) {
            console.log(`collapseSiblings: Hiding siblings, keeping ${monkName} at center`);
            try {
                // Get lineage to find teacher
                const params = new URLSearchParams({name: monkName});
                const data = await fetch(`/api/get_lineage?${params}`).then(r => r.json());
                if (data.error) { alert(data.error); return; }
                
                let teacherName = data.teacher || data.great_teacher || data.grand_teacher;
                if (!teacherName) {
                    const offlineParams = new URLSearchParams({name: monkName, fallback: 'true'});
                    const offlineData = await fetch(`/api/get_lineage?${offlineParams}`).then(r => r.json());
                    if (!offlineData.teacher) {
                        // Just collapse to single node - no teacher
                        await collapseToSingleNode(monkName);
                        return;
                    }
                    teacherName = offlineData.teacher;
                }
                
                // Get teacher's tree to find current monk's children
                const treeParams = new URLSearchParams({name: teacherName});
                const teacherData = await fetch(`/api/get_tree?${treeParams}`).then(r => r.json());
                
                // Find current monk's children in teacher's tree
                let currentMonkChildren = [];
                if (teacherData.children) {
                    const currentNode = teacherData.children.find(c => c.name === monkName);
                    if (currentNode && currentNode.children) {
                        currentMonkChildren = currentNode.children;
                    }
                }
                
                // Build tree: teacher -> current monk (with its children)
                const newTree = {
                    name: teacherName,
                    children: [{ name: monkName, children: currentMonkChildren }]
                };
                
                root = d3.hierarchy(newTree, d => d.children);
                root.x0 = 0; root.y0 = 0;
                
                // Mark siblings as hidden
                if (!window._siblingsState) window._siblingsState = {};
                window._siblingsState[monkName] = false;
                
                // Collapse deeper than MAX_INITIAL_DEPTH
                root.each(d => { 
                    if (d.depth > MAX_INITIAL_DEPTH && d.children) { 
                        d._children = d.children; 
                        d.children = null; 
                    }
                });
                
                update(root);
                
                // Center on current monk (depth 1)
                setTimeout(() => {
                    const searchedNode = root.descendants().find(d => d.data.name === monkName && d.depth === 1);
                    if (searchedNode) {
                        focusOnNode(searchedNode);
                    }
                }, 500);
                
                console.log(`collapseSiblings: Done - siblings hidden, ${monkName} at center`);
            } catch(e) {
                console.error("Error in collapseSiblings:", e);
                alert("Lỗi khi ẩn huynh đệ: " + e.message);
            }
        }
        
        async function collapseToSingleNode(monkName) {
            // When no teacher found - just show the monk with its children
            const params = new URLSearchParams({name: monkName});
            const data = await fetch(`/api/get_tree?${params}`).then(r => r.json());
            
            root = d3.hierarchy(data, d => d.children);
            root.x0 = 0; root.y0 = 0;
            
            if (!window._siblingsState) window._siblingsState = {};
            window._siblingsState[monkName] = false;
            
            root.each(d => { 
                if (d.depth > MAX_INITIAL_DEPTH && d.children) { 
                    d._children = d.children; 
                    d.children = null; 
                }
            });
            
            update(root);
            setTimeout(() => {
                const node = root.descendants().find(d => d.data.name === monkName);
                if (node) focusOnNode(node);
            }, 500);
        }

        async function traceToOrigin(monkName) {
            if (!monkName) return;
            console.log(`traceToOrigin called for: ${monkName}`);
            try {
                const params = new URLSearchParams({name: monkName});
                const data = await fetch(`/api/trace_lineage?${params}`).then(r => r.json());
                if (data.error) { alert(data.error); return; }
                
                // Show popup with lineage chain
                if (data.chain && data.chain.length > 0) {
                    // Chain includes current monk + teachers. Exclude current monk to get generations count
                    const totalGens = Math.max(0, data.chain.length - 1);
                    let html = `<div style="height:100%;overflow-y:auto;padding:10px;box-sizing:border-box;">
                        <h3 style="margin:0 0 10px 0;color:#333;">Truyền thừa: ${monkName}</h3>
                        <p style="margin:0 0 10px 0;color:#666;">Tổng cộng: <strong>${totalGens} đời</strong> để về Tổ Bồ Đề Đạt Ma</p>
                        <ol style="padding-left:20px;margin:0;">`;
                    
                    // Show from root (Sơ Tổ) down to current
                    // API returns plain array of names like ["A", "B", "C"]
                    for (let i = data.chain.length - 1; i >= 0; i--) {
                        const name = data.chain[i];
                        // Filter out bracket items like "[Phái X]"
                        if (name && !name.startsWith('[')) {
                            html += `<li style="margin-bottom:4px;">${name}</li>`;
                        }
                    }
                    
                    html += `</ol></div>`;
                    
                    // Show in bio panel
                    document.getElementById("bio-title").textContent = "Truyền Thừa: " + monkName;
                    document.getElementById("bio-gens").innerHTML = "";
                    document.getElementById("bio-content").innerHTML = html;
                    document.getElementById("bio-panel").classList.add("open");
                } else {
                    alert("Không tìm thấy dòng truyền thừa cho " + monkName);
                }
            } catch(e) {
                console.error("Error in traceToOrigin:", e);
                alert("Lỗi khi truy tìm Tổ: " + e.message);
            }
        }

        function centerTree() {
            setTimeout(() => {
                try {
                    const bounds = container.node().getBBox();
                    
                    if (bounds.width === 0 || bounds.height === 0) {
                        return;
                    }
                    
                    const svgNode = svg.node();
                    const svgW = svgNode.clientWidth;
                    const svgH = svgNode.clientHeight;
                    
                    // Center of the rendered content
                    const cx = bounds.x + bounds.width / 2;
                    const cy = bounds.y + bounds.height / 2;
                    
                    // Target center in viewport (account for sidebar)
                    const targetX = (svgW - 60) / 2;
                    const targetY = svgH / 2;
                    
                    // Transform to center
                    const scale = 0.8;
                    const x = targetX - cx * scale;
                    const y = targetY - cy * scale;
                    
                    svg.transition().duration(500).call(
                        d3.zoom().transform, 
                        d3.zoomIdentity.translate(x, y).scale(scale)
                    );
                } catch(e) {
                    console.error("centerTree error:", e);
                }
            }, 500);
        }

        function toggleSearch() {
            d3.select("#search-container").classed("show", !d3.select("#search-container").classed("show"));
            if (d3.select("#search-container").classed("show")) {
                document.getElementById("inp").focus();
                loadMonkNames();
            }
        }

        async function loadMonkNames() {
            if (monkNames.length === 0) monkNames = await fetch('/api/monk_names').then(r => r.json());
        }

        function searchMonk(q) {
            if (!q || q.length < 2) { document.getElementById("sug").innerHTML = ""; return; }
            const matches = monkNames.filter(n => n.toLowerCase().includes(q.toLowerCase())).slice(0, 10);
            document.getElementById("sug").innerHTML = matches.map(n => `<div onclick="selectMonk('${n}')">${n}</div>`).join("");
        }

        function selectMonk(name) {
            document.getElementById("sug").innerHTML = "";
            searchRoot(name);
        }

        // Format bio text: keep paragraphs together, no auto-break after dash or dialogue
        function formatBioText(text) {
            if (!text) return "";
            // If text already has HTML (like bio-narrative divs), clean using DOM
            if (text.includes('<') && text.includes('>')) {
                // Create temp container to clean HTML
                const temp = document.createElement('div');
                temp.innerHTML = text;
                // Walk through text nodes and normalize whitespace
                const walker = document.createTreeWalker(temp, NodeFilter.SHOW_TEXT, null, false);
                let node;
                while (node = walker.nextNode()) {
                    node.textContent = node.textContent.replace(/\s+/g, ' ').trim();
                }
                // Reduce vertical space around zen-separator hr
                let html = temp.innerHTML;
                html = html.replace(/<br\s*\/?>\s*<hr class="zen-separator"\s*>\s*<br\s*\/?>/gi, '<hr class="zen-separator">');
                html = html.replace(/(<div class="bio-narrative">)\s*<br\s*\/?>/gi, '$1');
                html = html.replace(/<br\s*\/?>\s*(<\/div>)/gi, '$1');
                return html;
            }
            // Plain text: just collapse extra whitespace
            return text.replace(/\s+/g, ' ').trim();
        }

        async function showBio(name) {
            if (!name) return;
            document.getElementById("bio-title").textContent = name;
            document.getElementById("bio-gens").textContent = "";
            document.getElementById("bio-content").textContent = "Đang tải...";
            document.getElementById("bio-panel").classList.add("open");
            try {
                const data = await fetch(`/api/get_details?name=${encodeURIComponent(name)}`).then(r => r.json());
                // Show generation info - with line breaks
                if (data.gens) {
                    let gensHtml = "";
                    if (data.gens.l1) gensHtml += data.gens.l1 + "<br>";
                    if (data.gens.l2) gensHtml += data.gens.l2 + "<br>";
                    if (data.gens.l3_tag && data.gens.l3_val) gensHtml += `${data.gens.l3_tag}: ${data.gens.l3_val}`;
                    document.getElementById("bio-gens").innerHTML = gensHtml;
                }
                // Format text - remove auto line breaks after dash or dialogue markers
                const rawNote = data.note || "Chưa có tiểu sử.";
                const formattedNote = formatBioText(rawNote);
                document.getElementById("bio-content").innerHTML = formattedNote;
            } catch(e) {
                document.getElementById("bio-content").textContent = "Lỗi tải tiểu sử.";
            }
        }

        function closeBio() {
            document.getElementById("bio-panel").classList.remove("open");
        }

        window.addEventListener('load', function() {
            if (typeof d3 === 'undefined') {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/d3@7';
                script.onload = function() { initHome(); };
                document.head.appendChild(script);
            } else {
                initHome();
            }
            loadMonkNames();
        });
    </script>
</body>
</html>
'''

@app.route('/tree')
def tree_route():
    return index()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7861)
