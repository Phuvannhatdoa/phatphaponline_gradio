import json
from rdflib import Graph, URIRef, Literal
import sys
import os
import datetime
import rdflib.xsd_datetime

# --- MONKEY-PATCHING: GHI ĐÈ XỬ LÝ NGÀY THÁNG LỊCH SỬ ---
if 'rdflib' in sys.modules and hasattr(rdflib, 'xsd_datetime'):
    
    def robust_parse_xsd_gyear(lexical):
        """
        Custom parser for xsd:gYear to bypass strict checks for ancient years (<1 AD)
        and non-4-digit years.
        """
        try:
            return rdflib.xsd_datetime.parse_xsd_gyear(lexical)
        except ValueError:
            # Trả về một năm an toàn làm placeholder (ví dụ: năm 1 AD)
            return datetime.date(1, 1, 1)

    print("Áp dụng bản vá lỗi (Monkey-Patch) cho xử lý ngày tháng lịch sử/cổ đại...")
    rdflib.xsd_datetime.parse_xsd_gyear = robust_parse_xsd_gyear

# ---------------------------------------------------------------------------------

# --- CẤU HÌNH ---
DATA_DIRECTORY = '/opt/phatphaponline_gradio/2000_Files/ttl_output/reorganize_ttl' 
LINEAGE_FILE = 'lineage_graph.jsonld'
OUTPUT_FILE = 'genealogy_data.json' 

BKG_TTL_PREFIX = 'http://www.phatphaponline.org/ontology/buddhist-kg#'
BKG_LINEAGE_PREFIX = 'http://buddhist-kg.org/ontology/'

RDFS_LABEL = 'http://www.w3.org/2000/01/rdf-schema#label'
HAS_TEACHER = f'{BKG_TTL_PREFIX}hasTeacher'
IS_LINEAGE_FOUNDER_PROP = f'{BKG_TTL_PREFIX}isLineageFounder'
BKG_MONK = f'{BKG_TTL_PREFIX}Monk'
BKG_BIOGRAPHICAL_NOTE = f'{BKG_TTL_PREFIX}biographicalNote'


# =========================================================================
# === HÀM TRÍCH XUẤT LABEL TIẾNG VIỆT ƯU TIÊN (Giữ nguyên) ===
# =========================================================================
def get_prioritized_label(graph, subject_uri):
    """
    Trích xuất rdfs:label. Ưu tiên label có tag @vi.
    """
    
    for label_literal in graph.objects(URIRef(subject_uri), URIRef(RDFS_LABEL)):
        if isinstance(label_literal, Literal):
            if label_literal.language == 'vi':
                return str(label_literal) 
            
    for label_literal in graph.objects(URIRef(subject_uri), URIRef(RDFS_LABEL)):
        if isinstance(label_literal, Literal):
            return str(label_literal)
            
    return None 


def generate_visjs_json_from_local_files():
    print(f"BƯỚC 1: Đang khởi tạo Graph và đọc tất cả files...")
    
    g = Graph()
    loaded_files = 0
    # ĐÃ THAY ĐỔI: failed_files lưu trữ (filename, error_message)
    failed_files = [] 
    
    # 1. Load Lineage Graph JSON-LD
    try:
        if os.path.exists(LINEAGE_FILE):
            print(f"Đang đọc file Lineage/Founder: {LINEAGE_FILE}")
            g.parse(LINEAGE_FILE, format='json-ld')
        else:
            print(f"CẢNH BÁO: Không tìm thấy file {LINEAGE_FILE}. Founder có thể bị thiếu.")
    except Exception as e:
        print(f"LỖI: Không thể đọc file {LINEAGE_FILE}. Lỗi: {e}", file=sys.stderr)

    # 2. Load tất cả các file TTL/JSON-LD (Monk data)
    print(f"Đang quét và đọc dữ liệu từ thư mục: {DATA_DIRECTORY}...")
    try:
        for filename in os.listdir(DATA_DIRECTORY):
            filepath = os.path.join(DATA_DIRECTORY, filename)
            
            if filename.endswith(('.ttl', '.jsonld', '.json')):
                try:
                    format_hint = 'json-ld' if filename.endswith(('.jsonld', '.json')) else 'ttl'
                    g.parse(filepath, format=format_hint)
                    loaded_files += 1
                except Exception as e:
                    # ĐÃ THAY ĐỔI: GHI LẠI TÊN FILE KÈM THÔNG BÁO LỖI CHI TIẾT
                    failed_files.append((filename, str(e)))
                    
    except FileNotFoundError:
        print(f"\nLỖI QUAN TRỌNG: Thư mục dữ liệu '{DATA_DIRECTORY}' không tồn tại.", file=sys.stderr)
        return
    except Exception as e:
        print(f"LỖI trong quá trình đọc thư mục: {e}", file=sys.stderr)
        return

    # -------------------------------------------------------------------------
    # BÁO CÁO LỖI CÚ PHÁP CHI TIẾT
    # -------------------------------------------------------------------------
    if len(failed_files) > 0:
        print(f"\n=======================================================")
        print(f"❌ BÁO CÁO CẢNH BÁO CHI TIẾT: LỖI CÚ PHÁP TTL/JSON-LD (ĐỂ ADMIN FIX)")
        print(f"Đã bỏ qua TỔNG CỘNG {len(failed_files)} files do lỗi cú pháp. Chi tiết:")
        print(f"=======================================================")
        
        # Duyệt qua danh sách file lỗi để in chi tiết
        for i, (filename, error_msg) in enumerate(failed_files):
            print(f"  [{i+1}/{len(failed_files)}] FILE: {filename}")
            # In thông báo lỗi, giới hạn 2 dòng để dễ đọc
            print(f"     LỖI: {error_msg.strip()}")
            
        print(f"=======================================================")
    
    # -------------------------------------------------------------------------


    if loaded_files == 0:
        print(f"\nLỖI CHÍNH: Không tìm thấy file dữ liệu TTL/JSON-LD nào trong thư mục {DATA_DIRECTORY}.", file=sys.stderr)
        return
    
    print(f"Đã load thành công {loaded_files} files, tổng cộng {len(g)} triple (bộ ba).")

    # 3. Truy vấn Khai tổ
    LINEAGE_TYPES = [f'{BKG_TTL_PREFIX}DharmaLineage', f'{BKG_LINEAGE_PREFIX}DharmaLineage']
    HAS_FOUNDER_PROPS = [f'{BKG_TTL_PREFIX}hasFounder', f'{BKG_LINEAGE_PREFIX}hasFounder']
    special_founder_uris = set()
    for lineage_type in LINEAGE_TYPES:
        for founder_prop in HAS_FOUNDER_PROPS:
            founder_query = f"""
                SELECT DISTINCT ?founderURI
                WHERE {{
                    ?lineage a <{lineage_type}> . 
                    ?lineage <{founder_prop}> ?founderURI .
                }}
            """
            for row in g.query(founder_query):
                special_founder_uris.add(str(row[0]))

    print(f"Đã tìm thấy {len(special_founder_uris)} vị Khai tổ qua bkg:hasFounder.")
    
    # 4. Trích xuất Nodes (Thiền sư) và Edges (Thầy/Trò)
    nodes_meta = {}
    edges = []

    monk_construct_query = f"""
        PREFIX bkg: <{BKG_TTL_PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        CONSTRUCT {{
            ?person bkg:hasTeacher ?master .
            ?person bkg:isLineageFounder ?isFounder .
            ?person bkg:generationOrder ?generationOrder .
            ?person bkg:biographicalNote ?bio .
        }}
        WHERE {{
            ?person a <{BKG_MONK}> .
            OPTIONAL {{ ?person bkg:hasTeacher ?master . }}
            OPTIONAL {{ ?person bkg:isLineageFounder ?isFounder . }}
            OPTIONAL {{ ?person bkg:generationOrder ?generationOrder . }}
            OPTIONAL {{ ?person bkg:biographicalNote ?bio . }}
        }}
    """
    
    monk_graph = g.query(monk_construct_query).graph
    
    for s, p, o in monk_graph:
        subject_uri = str(s)
        predicate_uri = str(p)
        object_value = str(o)
        
        if subject_uri not in nodes_meta:
            default_label = subject_uri.split('/')[-1].replace('_', ' ') 
            nodes_meta[subject_uri] = {
                'id': subject_uri, 
                'label': default_label,
                'isLineageFounder': subject_uri in special_founder_uris, 
                'isMasterFounder': False,
                'bio': None
            }
            
        if predicate_uri == BKG_BIOGRAPHICAL_NOTE:
            nodes_meta[subject_uri]['bio'] = object_value 

        elif predicate_uri == IS_LINEAGE_FOUNDER_PROP:
            if object_value.lower() in ['true', 'true^^http://www.w3.org/2001/XMLSchema#boolean']:
                nodes_meta[subject_uri]['isMasterFounder'] = True

        elif predicate_uri == HAS_TEACHER:
            master_uri = object_value
            
            edges.append({
                'id': f"{master_uri}->{subject_uri}",
                'from': master_uri,  
                'to': subject_uri,    
                'type': 'monk-to-monk'
            })
            
            if master_uri not in nodes_meta:
                default_label = master_uri.split('/')[-1].replace('_', ' ')
                nodes_meta[master_uri] = {
                    'id': master_uri, 
                    'label': default_label,
                    'isLineageFounder': master_uri in special_founder_uris, 
                    'isMasterFounder': False, 
                    'bio': None
                }
    
    # 5. Cập nhật Labels (Ưu tiên Tiếng Việt)
    print(f"BƯỚC 5: Đang cập nhật {len(nodes_meta)} Nodes với Label tiếng Việt chính xác...")
    for subject_uri in nodes_meta.keys():
        vietnamese_label = get_prioritized_label(g, subject_uri)
        
        if vietnamese_label:
            nodes_meta[subject_uri]['label'] = vietnamese_label
        
        nodes_meta[subject_uri]['rdfs:label'] = [str(o) for o in g.objects(URIRef(subject_uri), URIRef(RDFS_LABEL))]

    
    # 6. Ghi kết quả vào file JSON tĩnh
    vis_js_data = {
        'nodes': list(nodes_meta.values()),
        'edges': [dict(t) for t in {tuple(sorted(d.items())) for d in edges}] 
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(vis_js_data, f, ensure_ascii=False, indent=4)
    
    print(f"\nHoàn tất. Đã tạo {len(vis_js_data['nodes'])} nodes và {len(vis_js_data['edges'])} edges vào file {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_visjs_json_from_local_files()