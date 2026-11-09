import sys
sys.path.insert(0, r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh')
from app import app
with app.test_client() as client:
    resp = client.get('/daoanh/api/monk/A001984/lineage-tree?up=2&down=2')
    print(f"Status: {resp.status_code}")
    data = resp.get_json()
    print(f"OK: {data.get('ok') if data else 'N/A'}")
    if data and 'ok' in data and data['ok']:
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        print(f"\nNodes count: {len(nodes)}")
        print(f"Edges count: {len(edges)}")
        
        for edge in edges:
            print(f"  Edge: from={edge.get('from')}, to={edge.get('to')}, dir={edge.get('direction')}")
        
        for node in nodes:
            nid = node.get('id', '')
            print(f"  Node: id={nid}, name_vi={node.get('name_vi', 'N/A')[:60] if node.get('name_vi') else 'N/A'}")
    
    print("\n" + "="*60)
    
    resp2 = client.get('/daoanh/api/monk/A001984/ancestor-spine?max_hops=10')
    print(f"ancestor-spine Status: {resp2.status_code}")
    data2 = resp2.get_json()
    print(f"OK: {data2.get('ok') if data2 else 'N/A'}")
    if data2 and data2.get('ok') and data2.get('ancestors'):
        print(f"Ancestors: {data2['ancestors']}")
        for a in data2['ancestors']:
            print(f"  Ancestor id={a}")
    if data2 and data2.get('ok') and data2.get('edges'):
        print(f"\nEdges count: {len(data2['edges'])}")
        for e in data2['edges']:
            print(f"  Edge: from={e.get('from')}, to={e.get('to')}")