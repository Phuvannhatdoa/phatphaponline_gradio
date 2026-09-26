#!/usr/bin/env python3
"""
Map Marcus node IDs to DILA using persons.json (which has richer data)
Input: marcus_nodes.json, marcus_edges.json
Output: Network data with Vietnamese labels and lineage
"""
import json
import os

NODES_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/marcus_nodes.json"
EDGES_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/marcus_edges.json"
PERSONS_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/persons.json"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna"

def load_nodes():
    with open(NODES_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_edges():
    with open(EDGES_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_persons():
    """Load persons.json - list of dict with rich data"""
    with open(PERSONS_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    
    persons_list = raw.get("persons", [])
    
    lookup = {}
    for p in persons_list:
        p_id = p.get("id")
        if not p_id:
            continue
        
        name_zh = ""
        name_vi = ""
        for nm in p.get("names", []):
            if nm.get("type") == "primary":
                name_zh = nm.get("value", "")
            if nm.get("lang") == "vie":
                name_vi = nm.get("value", "")
        
        if not name_vi:
            for nm in p.get("names", []):
                if nm.get("lang") in ("zho-Hant", "zho-Hans"):
                    name_vi = nm.get("value", "")
                    break
        
        lineage = p.get("lineage", "")
        
        lookup[p_id] = {
            "dila_id": p_id,
            "name_zh": name_zh,
            "name_vi": name_vi,
            "lineage": lineage,
            "dynasty": p.get("dynasty", ""),
            "birth_year": p.get("birth_year", ""),
            "death_year": p.get("death_year", ""),
            "biography": p.get("biography", ""),
            "teacher": p.get("teacher", []),
            "student": p.get("student", [])
        }
    
    print(f"✓ Loaded {len(lookup):,} persons from persons.json")
    return lookup

def map_marcus_to_dila(nodes, persons_lookup):
    """Map Marcus nodes to persons.json data"""
    
    mapped = {}
    unmapped_ids = []
    
    for node_id, node in nodes.items():
        label = node.get("label", "")
        
        if node_id in persons_lookup:
            pers = persons_lookup[node_id]
            node["dila_id"] = pers["dila_id"]
            node["name_vi"] = pers.get("name_vi", "")
            node["lineage"] = pers.get("lineage", "")
            node["dynasty"] = pers.get("dynasty", "")
            node["birth_year"] = pers.get("birth_year", "")
            node["death_year"] = pers.get("death_year", "")
            node["biography"] = pers.get("biography", "")
            node["teacher"] = pers.get("teacher", [])
            node["student"] = pers.get("student", [])
            mapped[node_id] = node
        else:
            node["dila_id"] = None
            node["name_vi"] = ""
            node["lineage"] = ""
            node["dynasty"] = node["attrs"].get("n@nationality", "")
            node["birth_year"] = node["attrs"].get("n@birthY", "")
            node["death_year"] = node["attrs"].get("n@deathY", "")
            node["biography"] = ""
            node["teacher"] = []
            node["student"] = []
            unmapped_ids.append(node_id)
            mapped[node_id] = node
    
    if unmapped_ids:
        print(f"⚠ {len(unmapped_ids):,} nodes NOT in persons.json")
    
    print(f"✓ Mapped: {len(mapped):,} nodes")
    return mapped

def enrich_edges(nodes, edges):
    """Enrich edges with label info"""
    
    enriched = []
    for e in edges:
        source_id = e["source"]
        target_id = e["target"]
        
        src = nodes.get(source_id, {})
        tgt = nodes.get(target_id, {})
        
        e["source_label"] = src.get("label", source_id)
        e["source_name_vi"] = src.get("name_vi", "")
        e["target_label"] = tgt.get("label", target_id)
        e["target_name_vi"] = tgt.get("name_vi", "")
        
        enriched.append(e)
    
    print(f"✓ Enriched {len(enriched):,} edges")
    return enriched

def save_outputs(nodes, edges):
    """Save mapped data"""
    
    nodes_file = os.path.join(OUTPUT_DIR, "marcus_nodes_mapped.json")
    edges_file = os.path.join(OUTPUT_DIR, "marcus_edges_mapped.json")
    
    with open(nodes_file, "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    
    with open(edges_file, "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved: {nodes_file}")
    print(f"✓ Saved: {edges_file}")

def show_stats(nodes):
    """Show mapping statistics"""
    total = len(nodes)
    with_vi = sum(1 for n in nodes.values() if n.get("name_vi"))
    with_lineage = sum(1 for n in nodes.values() if n.get("lineage"))
    with_bio = sum(1 for n in nodes.values() if n.get("biography"))
    
    print(f"\n=== Mapping Stats ===")
    print(f"  Total nodes: {total:,}")
    print(f"  Has name_vi: {with_vi:,} ({100*with_vi/total:.1f}%)")
    print(f"  Has lineage: {with_lineage:,} ({100*with_lineage/total:.1f}%)")
    print(f"  Has biography: {with_bio:,} ({100*with_bio/total:.1f}%)")

if __name__ == "__main__":
    nodes = load_nodes()
    edges = load_edges()
    
    persons_lookup = load_persons()
    
    nodes = map_marcus_to_dila(nodes, persons_lookup)
    edges = enrich_edges(nodes, edges)
    
    save_outputs(nodes, edges)
    show_stats(nodes)
    
    print("\n=== Sample ===")
    sample_id = "A000005"
    if sample_id in nodes:
        n = nodes[sample_id]
        print(f"  {n['label']} ({n['name_vi']})")
        print(f"  lineage: {n['lineage'][:50] if n.get('lineage') else 'N/A'}...")
        print(f"  dynasty: {n['dynasty']}, {n['birth_year']}-{n['death_year']}")