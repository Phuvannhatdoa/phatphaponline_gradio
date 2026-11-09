import sys
sys.path.insert(0, r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh')
from app import app

test_dilas = ['A001984', 'AA001028', 'AA001544', 'AA001861', 'AA001971', 'AA002188']

with app.test_client() as client:
    for dila_id in test_dilas:
        print(f"\n===== Testing {dila_id} =====")
        # Test lineage-tree
        try:
            resp = client.get(f'/daoanh/api/monk/{dila_id}/lineage-tree?up=2&down=2')
            data = resp.get_json()
            if data and data.get('ok'):
                # Find edges where from is a teacher of A001984's group or center
                # Just check the first few edges for teacher info
                edges = data.get('edges', [])
                nodes = data.get('nodes', [])
                
                # Find teacher nodes near the center
                center_id = dila_id
                for node in nodes:
                    if node.get('id') == center_id:
                        center_name = node.get('name_vi', 'N/A')[:30]
                        break
                
                # Check for teacher edges (direction=teacher pointing TO center)
                teacher_edges = [e for e in edges if e.get('to') == center_id and e.get('direction') == 'teacher']
                if teacher_edges:
                    for e in teacher_edges[:3]:
                        from_id = e.get('from')
                        # Find name of teacher
                        from_node = next((n for n in nodes if n.get('id') == from_id), None)
                        from_name = from_node.get('name_vi', 'N/A')[:30] if from_node else 'N/A'
                        print(f"  lineage-tree: teacher of {center_id} = A{from_id} ({from_name})")
                else:
                    # Check ancestor spine instead
                    print(f"  lineage-tree: no direct teacher edge to {center_id}")
        except Exception as e:
            print(f"  lineage-tree ERROR: {e}")
        
        # Test ancestor-spine
        try:
            resp2 = client.get(f'/daoanh/api/monk/{dila_id}/ancestor-spine?max_hops=10')
            data2 = resp2.get_json()
            if data2 and data2.get('ok'):
                ancestors = data2.get('ancestors', [])
                edges = data2.get('edges', [])
                print(f"  ancestor-spine: ancestors = {ancestors[:5]}")
                # Check if first ancestor has is_primary=1 backing
                if ancestors:
                    first_ancestor = ancestors[0]
                    # Find the edge from first ancestor to next
                    anc_edges = [e for e in edges if e.get('from') == first_ancestor]
                    if anc_edges:
                        print(f"  ancestor-spine: first edge from A{first_ancestor} is OK")
        except Exception as e:
            print(f"  ancestor-spine ERROR: {e}")