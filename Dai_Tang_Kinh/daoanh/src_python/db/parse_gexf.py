#!/usr/bin/env python3
"""
Parse Marcus GEXF file - extract nodes and edges
Source: CB_HSNA_2021-06.gexf (18,130 nodes, 33,977 edges)
Output: JSON files for nodes and edges
"""
import json
import os
from lxml import etree
from collections import defaultdict

GEXF_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/CB_HSNA_2021-06.gexf"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna"

NS = {"g": "http://www.gexf.net/1.2draft"}

def parse_gexf():
    """Parse GEXF file"""
    
    nodes = {}
    edges = []
    edge_types = defaultdict(int)
    
    print("Parsing GEXF file...")
    tree = etree.parse(GEXF_FILE)
    
    for node in tree.findall(".//g:node", NS):
        node_id = node.get("id")
        label = node.get("label", "")
        
        attrs = {}
        for av in node.findall(".//g:attvalue", NS):
            attr_id = av.get("for")
            attr_val = av.get("value")
            if attr_id and attr_val:
                attrs[attr_id] = attr_val
        
        nodes[node_id] = {
            "id": node_id,
            "label": label,
            "attrs": attrs
        }
    
    for edge in tree.findall(".//g:edge", NS):
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type", "")
        
        e_attrs = {}
        for av in edge.findall(".//g:attvalue", NS):
            attr_id = av.get("for")
            attr_val = av.get("value")
            if attr_id and attr_val:
                e_attrs[attr_id] = attr_val
        
        edges.append({
            "source": source,
            "target": target,
            "type": edge_type,
            "attrs": e_attrs
        })
        
        if edge_type:
            edge_types[edge_type] += 1
    
    print(f"✓ Parsed: {len(nodes):,} nodes, {len(edges):,} edges")
    print(f"  Edge types: {dict(edge_types)}")
    
    return nodes, edges

def extract_relation(desc):
    """Extract relation type from e@desc"""
    if not desc:
        return "unknown"
    desc_lower = desc.lower()
    if "teacher" in desc_lower:
        return "da:isTeacherOf"
    elif "disciple" in desc_lower:
        return "da:isDiscipleOf"
    elif "father" in desc_lower or "mother" in desc_lower:
        return "kinship"
    elif "ordained" in desc_lower:
        return "da:ordainedBy"
    else:
        return "da:relatedTo"

def save_outputs(nodes, edges):
    """Save parsed data to JSON"""
    
    nodes_file = os.path.join(OUTPUT_DIR, "marcus_nodes.json")
    edges_file = os.path.join(OUTPUT_DIR, "marcus_edges.json")
    
    with open(nodes_file, "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    
    enhanced_edges = []
    for e in edges:
        desc = e["attrs"].get("e@desc", "")
        e["relation_type"] = extract_relation(desc)
        enhanced_edges.append(e)
    
    with open(edges_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_edges, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved: {nodes_file}")
    print(f"✓ Saved: {edges_file}")

def show_sample(nodes, edges):
    """Show sample data"""
    print("\n=== Sample Nodes ===")
    for i, (k, v) in enumerate(list(nodes.items())[:3]):
        print(f"  {k}: {v['label']} | birthY={v['attrs'].get('n@birthY')} deathY={v['attrs'].get('n@deathY')}")
    
    print("\n=== Sample Edges (with relation type) ===")
    for e in edges[:5]:
        src_label = nodes.get(e['source'], {}).get('label', e['source'])
        tgt_label = nodes.get(e['target'], {}).get('label', e['target'])
        rel = e.get('relation_type', 'unknown')
        print(f"  {src_label} --[{rel}]--> {tgt_label}")
        print(f"    desc: {e['attrs'].get('e@desc', '')[:50]}")

if __name__ == "__main__":
    nodes, edges = parse_gexf()
    save_outputs(nodes, edges)
    show_sample(nodes, edges)