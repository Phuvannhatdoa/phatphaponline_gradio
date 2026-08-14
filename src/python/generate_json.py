import json
from rdflib import Graph, URIRef, Literal
import sys
import os
import datetime
import rdflib.xsd_datetime
from typing import Dict, Any, List, Tuple, Set

# --- MONKEY-PATCHING: GHI ĐÈ XỬ LÝ NGÀY THÁNG LỊCH SỬ ---
# Điều chỉnh cách rdflib parse xsd:gYear cho các năm cổ đại (trước công nguyên)
if 'rdflib' in sys.modules and hasattr(rdflib, 'xsd_datetime'):
    
    def robust_parse_xsd_gyear(lexical):
        """
        Custom parser for xsd:gYear to bypass strict checks for ancient years (<1 AD)
        and non-4-digit years.
        """
        try:
            return rdflib.xsd_datetime.parse_xsd_gyear(lexical)
        except ValueError:
            # Trả về giá trị mặc định cho các năm lỗi/cổ đại không thể parse nghiêm ngặt
            return datetime.date(1, 1, 1)

    rdflib.xsd_datetime.parse_xsd_gyear = robust_parse_xsd_gyear

# ---------------------------------------------------------------------------------

# --- CẤU HÌNH ---
BASE_DIR = '/opt/phatphaponline_gradio/truyenthua/visjs-app'
DATA_DIRECTORY = '/opt/phatphaponline_gradio/2000_Files/ttl_output/reorganize_ttl' 
LINEAGE_FILE = f'{BASE_DIR}/data/raw/lineage_graph.jsonld'
OUTPUT_FILE = f'{BASE_DIR}/data/processed/genealogy_data.json' 
# Định nghĩa đường dẫn file report
REPORT_OUTPUT_DIR = '/opt/phatphaponline_gradio/2000_Files/ttl_output/'
REPORT_OUTPUT_FILE = os.path.join(REPORT_OUTPUT_DIR, 'report-update-ttl.json')

# --- RDF CONSTANTS ---
BKG_TTL_PREFIX = 'http://www.phatphaponline.org/ontology/buddhist-kg#'
BKG_LINEAGE_PREFIX = 'http://buddhist-kg.org/ontology/'

RDFS_LABEL = 'http://www.w3.org/2000/01/rdf-schema#label'
HAS_TEACHER = f'{BKG_TTL_PREFIX}hasTeacher'
IS_LINEAGE_FOUNDER_PROP = f'{BKG_TTL_PREFIX}isLineageFounder'
BKG_MONK = f'{BKG_TTL_PREFIX}Monk'
BKG_BIOGRAPHICAL_NOTE = f'{BKG_TTL_PREFIX}biographicalNote'

# DANH SÁCH CÁC TỪ KHÓA URI CẦN LOẠI BỎ KHỎI BÁO CÁO MONK (Đã cập nhật để loại trừ Work/Place/...)
URI_BLACKLIST_KEYWORDS = ['ex:work/', 'ex:place/', 'ex:lineage/', 'ex:event/', 'ex:concept/', 'ex:contribution/']


# =========================================================================
# === HÀM TRÍCH XUẤT LABEL TIẾNG VIỆT ƯU TIÊN ===
# =========================================================================
def get_prioritized_label(graph: Graph, subject_uri: str) -> str | None:
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
    # Khởi tạo map để lưu trữ URI và file nguồn của chúng
    uri_to_source_file: Dict[str, str] = {} 
    
    # 1. Load Lineage Graph JSON-LD
    try:
        if os.path.exists(LINEAGE_FILE):
            print(f"Đang đọc file Lineage/Founder: {LINEAGE_FILE}")
            g.parse(LINEAGE_FILE, format='json-ld')
            # URIs trong file lineage thường là founder, không cần gán source file cụ thể.
        else:
            print(f"CẢNH BÁO: Không tìm thấy file {LINEAGE_FILE}. Founder có thể bị thiếu.")
    except Exception as e:
        print(f"LỖI: Không thể đọc file {LINEAGE_FILE}. Lỗi: {e}", file=sys.stderr)

    # 2. Load tất cả các file TTL/JSON-LD (Monk data)
    print(f"Đang quét và đọc dữ liệu từ thư mục: {DATA_DIRECTORY}...")
    
    total_files_found = 0
    
    try:
        # Đảm bảo thư mục tồn tại để lưu report
        os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True) 

        for filename in os.listdir(DATA_DIRECTORY):
            filepath = os.path.join(DATA_DIRECTORY, filename)
            
            if filename.endswith(('.ttl', '.jsonld', '.json')):
                total_files_found += 1
                try:
                    format_hint = 'json-ld' if filename.endswith(('.jsonld', '.json')) else 'ttl'
                    
                    # TẠO GRAPH TẠM THỜI ĐỂ LẤY SUBJECTS
                    temp_g = Graph()
                    temp_g.parse(filepath, format=format_hint)
                    
                    # Load vào MAIN GRAPH
                    g.parse(filepath, format=format_hint) 
                    loaded_files += 1

                    # LẬP BẢN ĐỒ: Gán tất cả các Subjects trong file này vào tên file
                    for s, p, o in temp_g.triples((None, None, None)):
                        # Chỉ gán cho Subjects (đối tượng chính)
                        if str(s) not in uri_to_source_file:
                            uri_to_source_file[str(s)] = filename
                        
                except Exception:
                    # Bỏ qua lỗi parsing, không báo cáo chi tiết theo yêu cầu focus fix monk
                    pass
                    
    except FileNotFoundError:
        print(f"\nLỖI QUAN TRỌNG: Thư mục dữ liệu '{DATA_DIRECTORY}' không tồn tại.", file=sys.stderr)
        return
    except Exception as e:
        print(f"LỖI trong quá trình đọc thư mục: {e}", file=sys.stderr)
        return

    # --- IN BÁO CÁO TÓM TẮT TRÊN CONSOLE ---
    if total_files_found == 0:
        print(f"\nLỖI CHÍNH: Không tìm thấy file dữ liệu TTL/JSON-LD nào trong thư mục {DATA_DIRECTORY}.", file=sys.stderr)
        return
    
    print(f"Đã load thành công {loaded_files}/{total_files_found} files.")
    print(f"Tổng cộng {len(g)} triple (bộ ba) đã được load.")
    # -------------------------------------------------------------------------

    # 3. Truy vấn Khai tổ (Giữ nguyên)
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

    # 4. Trích xuất Nodes (Thiền sư) và Edges (Thầy/Trò)

    # --- BƯỚC 4a: TÌM TẤT CẢ CÁC URI CÓ THỂ LÀ MONK ---
    # Truy vấn rộng để tìm các URI có liên quan đến label, bio, hoặc thầy/trò
    monk_candidate_query = f"""
        PREFIX bkg: <{BKG_TTL_PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?uri
        WHERE {{
            {{ ?uri <{RDFS_LABEL}> ?o . }}
            UNION
            {{ ?uri <{BKG_BIOGRAPHICAL_NOTE}> ?o . }}
            UNION
            {{ ?uri <{HAS_TEACHER}> ?o . }}
            UNION
            {{ ?s <{HAS_TEACHER}> ?uri . }}
        }}
    """
    
    all_candidate_uris: Set[str] = set(str(row[0]) for row in g.query(monk_candidate_query))
    
    # --- BƯỚC 4b: CONSTRUCT CHỈ LẤY CÁC THIỀN SƯ ĐƯỢC PHÂN LOẠI ĐÚNG (a bkg:Monk) ---
    monk_construct_query = f"""
        PREFIX bkg: <{BKG_TTL_PREFIX}>
        CONSTRUCT {{
            ?person bkg:hasTeacher ?master .
            ?person bkg:isLineageFounder ?isFounder .
            ?person bkg:biographicalNote ?bio .
        }}
        WHERE {{
            ?person a <{BKG_MONK}> .
            OPTIONAL {{ ?person bkg:hasTeacher ?master . }}
            OPTIONAL {{ ?person bkg:isLineageFounder ?isFounder . }}
            OPTIONAL {{ ?person bkg:biographicalNote ?bio . }}
        }}
    """
    
    monk_graph = g.query(monk_construct_query).graph
    
    selected_monk_uris: Set[str] = set()
    for s, p, o in monk_graph:
        selected_monk_uris.add(str(s))
        if str(p) == HAS_TEACHER:
            selected_monk_uris.add(str(o))

    # --- KHỞI TẠO VÀ XỬ LÝ DỮ LIỆU (Tạo file genealogy_data.json) ---
    nodes_meta: Dict[str, Dict[str, Any]] = {}
    edges = []
    
    for uri in selected_monk_uris:
        default_label = uri.split('/')[-1].replace('_', ' ') 
        nodes_meta[uri] = {
            'id': uri, 
            'label': default_label,
            'isLineageFounder': uri in special_founder_uris, 
            'isMasterFounder': False,
            'teacher_uri_temp': None, 
            'bio': None 
        }

    for s, p, o in monk_graph:
        subject_uri = str(s)
        predicate_uri = str(p)
        object_value = str(o)

        if subject_uri not in nodes_meta:
             continue
            
        if predicate_uri == BKG_BIOGRAPHICAL_NOTE:
            nodes_meta[subject_uri]['bio'] = object_value 

        elif predicate_uri == IS_LINEAGE_FOUNDER_PROP:
            if object_value.lower() in ['true', 'true^^http://www.w3.org/2001/XMLSchema#boolean']:
                nodes_meta[subject_uri]['isMasterFounder'] = True

        elif predicate_uri == HAS_TEACHER:
            master_uri = object_value
            nodes_meta[subject_uri]['teacher_uri_temp'] = master_uri 
            
            edges.append({
                'id': f"{master_uri}->{subject_uri}",
                'from': master_uri,     
                'to': subject_uri,     
                'type': 'monk-to-monk'
            })

    # 5. Cập nhật Labels và Sắp xếp trường
    print(f"BƯỚC 5: Đang cập nhật {len(nodes_meta)} Nodes...")
    final_nodes = []
    
    for subject_uri, node_data in nodes_meta.items():
        vietnamese_label = get_prioritized_label(g, subject_uri)
        
        if vietnamese_label:
            node_data['label'] = vietnamese_label
        
        final_node_structure = {
            'id': node_data['id'],
            'label': node_data['label'],
            'isLineageFounder': node_data['isLineageFounder'],
            'isMasterFounder': node_data['isMasterFounder'],
        }
        
        if node_data.get('teacher_uri_temp'):
            final_node_structure['teacher'] = node_data['teacher_uri_temp']
        
        if node_data.get('bio'):
             final_node_structure['bio'] = node_data['bio']
        
        final_node_structure['rdfs:label'] = [str(o) for o in g.objects(URIRef(subject_uri), URIRef(RDFS_LABEL))]
             
        final_nodes.append(final_node_structure)
    
    # 6. Ghi kết quả vào file JSON tĩnh (genealogy_data.json)
    unique_edges = [dict(t) for t in {tuple(sorted(d.items())) for d in edges}]

    vis_js_data = {
        'nodes': final_nodes,
        'edges': unique_edges 
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(vis_js_data, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ HOÀN TẤT XỬ LÝ DỮ LIỆU. Đã tạo {len(vis_js_data['nodes'])} nodes vào file {OUTPUT_FILE}")

    # =========================================================================
    # === BƯỚC CUỐI CÙNG: TẠO FILE REPORT CHỈ FOCUS VÀO LỖI PHÂN LOẠI MONK ===
    # =========================================================================
    
    # Lỗi Phân loại (Classification Errors)
    unclassified_candidate_uris = all_candidate_uris - selected_monk_uris
    
    classification_errors: List[Dict[str, str]] = []
    
    for uri in sorted(list(unclassified_candidate_uris)):
        # LOẠI BỎ CÁC URI KHÔNG PHẢI LÀ MONK
        if any(keyword in uri for keyword in URI_BLACKLIST_KEYWORDS):
            continue

        label = get_prioritized_label(g, uri)
        
        # 1. Lấy Source File
        source_file = uri_to_source_file.get(uri, "File không xác định")
        
        required_triple = f"<{uri}> a <{BKG_MONK}> ."
        
        # 2. Tạo hướng dẫn sửa chi tiết
        fix_suggestion = (
            f"Vấn đề: URI này được cho là một Thiền sư (có label/bio/teacher) nhưng thiếu triple phân loại 'a bkg:Monk'.\n"
            f"Cách sửa: Mở file '{source_file}' và thêm triple sau:\n"
            f"```ttl\n{required_triple}\n```"
        )
        
        classification_errors.append({
            "uri": uri,
            "label": label if label else "URI không có rdfs:label (@vi)",
            "source_file": source_file, # THÊM TÊN FILE NGUỒN
            "required_fix_triple": required_triple, # Triple cần thêm
            "fix_suggestion": fix_suggestion # Hướng dẫn sửa chi tiết
        })

    # Dữ liệu Report cuối cùng
    report_data = {
        "metadata": {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_files_scanned": total_files_found,
            "monk_nodes_created": len(final_nodes)
        },
        "classification_errors": {
            "description": f"Các URI được cho là Thiền sư (không phải tác phẩm/địa điểm) nhưng bị thiếu triple phân loại 'a {BKG_MONK}'. Admin cần thêm triple phân loại vào file tương ứng.",
            "count": len(classification_errors),
            "monks": classification_errors
        }
    }
    
    # Ghi file report JSON
    try:
        with open(REPORT_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ ĐÃ TẠO REPORT FIX MONK THÀNH CÔNG. Vui lòng kiểm tra file:")
        
        # SỬA LỖI CHÍNH TẢ Ở ĐÂY: Dùng REPORT_OUTPUT_FILE
        print(f"   {REPORT_OUTPUT_FILE}") 
        
    except Exception as e:
        # Báo cáo lỗi khi ghi file (nếu có)
        print(f"\nLỖI QUAN TRỌNG: Không thể ghi file report tại {REPORT_OUTPUT_FILE}. Lỗi: {e}", file=sys.stderr)


if __name__ == "__main__":
    generate_visjs_json_from_local_files()