#!/usr/bin/env python3
"""
Export Lineage Tree from GraphDB to JSON
========================================
Query all monks with teacher/student relationships from GraphDB,
export to JSON for offline use with Cytoscape.js
"""

import requests
import json
import os

GRAPHDB_URL = "http://localhost:7200/repositories/buddhist"

def query_graphdb(sparql):
    """Execute SPARQL query against GraphDB"""
    headers = {'Accept': 'application/sparql-results+json'}
    response = requests.get(GRAPHDB_URL, params={'query': sparql}, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    return response.json().get('results', {}).get('bindings', [])

def get_all_monks_with_teachers():
    """Query all monks with their teachers"""
    print("Querying all monks with teachers...")
    sparql = """
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?monk ?label ?teacher ?teacherLabel WHERE {
        ?monk rdfs:label ?label .
        FILTER(lang(?label) = "vi")
        OPTIONAL {
            ?monk bkg:hasTeacher ?t .
            ?t rdfs:label ?teacherLabel .
            FILTER(lang(?teacherLabel) = "vi")
            BIND(?teacherLabel AS ?teacher)
        }
    }
    """
    results = query_graphdb(sparql)
    
    monks = {}
    for row in results:
        monk_id = row.get('monk', {}).get('value', '')
        label = row.get('label', {}).get('value', '')
        teacher = row.get('teacher', {}).get('value', '')
        
        if label:
            if label not in monks:
                monks[label] = {
                    'id': monk_id,
                    'label': label,
                    'teacher': teacher if teacher else None,
                    'students': [],
                    'isFounder': False,
                    'isMainTree': False
                }
            elif teacher and not monks[label].get('teacher'):
                monks[label]['teacher'] = teacher
                
    return monks

def get_students_for_monks(monks_dict):
    """Query all students for the monks"""
    print("Querying all student relationships...")
    sparql = """
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?student ?studentLabel ?teacherLabel WHERE {
        ?student rdfs:label ?studentLabel .
        FILTER(lang(?studentLabel) = "vi")
        ?student bkg:hasTeacher ?t .
        ?t rdfs:label ?teacherLabel .
        FILTER(lang(?teacherLabel) = "vi")
    }
    """
    results = query_graphdb(sparql)
    
    # Build student lists
    for row in results:
        student = row.get('studentLabel', {}).get('value', '')
        teacher = row.get('teacherLabel', {}).get('value', '')
        
        if teacher and student:
            if teacher in monks_dict:
                if student not in monks_dict[teacher]['students']:
                    monks_dict[teacher]['students'].append(student)
    
    return monks_dict

def get_founders(monks_dict):
    """Query monks with isLineageFounder = true"""
    print("Querying lineage founders...")
    sparql = """
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?monk ?label WHERE {
        ?monk bkg:isLineageFounder true .
        ?monk rdfs:label ?label .
        FILTER(lang(?label) = "vi")
    }
    """
    results = query_graphdb(sparql)
    
    founder_count = 0
    for row in results:
        label = row.get('label', {}).get('value', '')
        if label in monks_dict:
            monks_dict[label]['isFounder'] = True
            founder_count += 1
    
    print(f"Found {founder_count} lineage founders")
    return monks_dict

def identify_main_tree(monks_dict):
    """
    Identify main tree (Tông Lâm Tế → Dòng Dương Kỳ)
    Count founders in each branch to determine main vs sub
    """
    print("Identifying main tree...")
    
    # Calculate founder counts for each branch
    branch_counts = {}
    
    # Main tree starts from these key monks
    main_tree_roots = [
        "Lâm Tế Nghĩa Huyền",  # Tông Lâm Tế
        "Dương Kỳ Phương Hội",  # Dòng Dương Kỳ
    ]
    
    # For simplicity, mark monks in main tree lineage as isMainTree = True
    # We can refine this later based on actual data
    
    # Count total founders
    total_founders = sum(1 for m in monks_dict.values() if m['isFounder'])
    print(f"Total founders: {total_founders}")
    
    return monks_dict

def export_to_json(monks_dict, output_file):
    """Export to JSON file"""
    print(f"Exporting to {output_file}...")
    
    # Convert to sorted JSON structure
    output = {
        "monks": monks_dict,
        "metadata": {
            "total_monks": len(monks_dict),
            "total_founders": sum(1 for m in monks_dict.values() if m['isFounder']),
            "exported_from": "GraphDB",
            "description": "Full lineage tree data for Cytoscape.js offline use"
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Exported {len(monks_dict)} monks to {output_file}")
    return output

def main():
    # Step 1: Get all monks with teachers
    monks = get_all_monks_with_teachers()
    print(f"Found {len(monks)} monks")
    
    # Step 2: Get all student relationships
    monks = get_students_for_monks(monks)
    
    # Step 3: Mark founders
    monks = get_founders(monks)
    
    # Step 4: Identify main tree
    monks = identify_main_tree(monks)
    
    # Step 5: Export
    output_file = '/opt/phatphaponline_gradio/truyenthua/visjs-app/data/lineage_tree.json'
    export_to_json(monks, output_file)
    
    # Print some stats
    print("\n=== Export Statistics ===")
    print(f"Total monks: {len(monks)}")
    print(f"Monks with teachers: {sum(1 for m in monks.values() if m.get('teacher'))}")
    print(f"Monks with students: {sum(1 for m in monks.values() if m.get('students'))}")
    print(f"Founders: {sum(1 for m in monks.values() if m.get('isFounder'))}")

if __name__ == '__main__':
    main()
