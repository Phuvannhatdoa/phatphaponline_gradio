import json
import networkx as nx

def load_genealogy_data(file_path="genealogy_data.json"):
    """
    Đọc dữ liệu Thiền sư từ tệp JSON.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def find_all_cycles(data):
    """
    Xây dựng đồ thị có hướng (DiGraph) và tìm tất cả các chu trình đơn giản.
    """
    # Khởi tạo đồ thị có hướng
    G = nx.DiGraph()
    
    # 1. Thêm các nodes (Thiền sư)
    for node in data.get('nodes', []):
        G.add_node(node.get('id'), label=node.get('label'))

    # 2. Thêm các edges (Mối quan hệ thầy-trò)
    # Trong dữ liệu đã cung cấp, mối quan hệ thầy-trò được suy ra từ các node:
    # node.teacher hoặc node['bkg:hasTeacher'] -> node.id (Trò)
    edges_found = 0
    for node in data.get('nodes', []):
        disciple_id = node.get('id')
        
        # Hàm hỗ trợ trích xuất ID từ đối tượng
        def extract_teacher_id(prop):
            if isinstance(prop, list):
                for item in prop:
                    if isinstance(item, dict) and '@id' in item:
                        return item['@id']
                return None
            if isinstance(prop, dict) and '@id' in prop:
                return prop['@id']
            return prop

        teacher_id = node.get('teacher')
        if not teacher_id:
            teacher_id = extract_teacher_id(node.get('bkg:hasTeacher'))

        if teacher_id and disciple_id:
            # Mối quan hệ: Thầy -> Trò (Teacher -> Disciple)
            G.add_edge(teacher_id, disciple_id)
            edges_found += 1

    print(f"--- Đã tải {G.number_of_nodes()} Thiền sư và {edges_found} mối quan hệ ---")

    # 3. Tìm các chu trình
    try:
        # TÌM TẤT CẢ CÁC CHU TRÌNH ĐƠN GIẢN
        cycles = list(nx.simple_cycles(G))
        
        if cycles:
            print("\n❌ LỖI NGHIÊM TRỌNG: ĐÃ PHÁT HIỆN CÁC CHU TRÌNH TRUYỀN THỪA (CYCLES) ❌")
            print("==================================================================")
            
            error_count = 0
            for cycle in cycles:
                error_count += 1
                # Lấy tên nhãn (label) thay vì chỉ ID
                cycle_labels = [G.nodes[node]['label'] if 'label' in G.nodes[node] else node for node in cycle]
                
                print(f"\nChu trình #{error_count} (Độ dài: {len(cycle)}):")
                print(" -> ".join(cycle_labels))
                print("\n\t=> CẦN SỬA LỖI: Kiểm tra lại mối quan hệ thầy trò trong vòng lặp này.")

            print("\n==================================================================")
            print(f"Tổng cộng {len(cycles)} chu trình đã được tìm thấy. Vui lòng sửa trong file JSON.")
            return False
        else:
            print("\n✅ THÀNH CÔNG: Dữ liệu không chứa chu trình. Đồ thị là Acyclic (DAG).")
            return True

    except Exception as e:
        print(f"\nLỗi khi tìm chu trình: {e}")
        return False

# Chạy kiểm tra
if __name__ == "__main__":
    genealogy_data = load_genealogy_data()
    find_all_cycles(genealogy_data)