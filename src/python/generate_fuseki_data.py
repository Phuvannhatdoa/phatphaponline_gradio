import requests
import json
import uuid
from rdflib import Graph

FUSEKI_QUERY_URL = "http://localhost:3030/buddhist-kg/query"

SPARQL_QUERY = """
PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?subject ?subjectLabel ?object ?objectLabel ?predicate
WHERE {
  GRAPH <http://data.phatphaponline.org/graph/monks> {
    {
      ?subject bkg:hasDisciple ?object .
      BIND ("hasDisciple" AS ?predicate)
    } UNION {
      ?subject bkg:hasTeacher ?object .
      BIND ("hasTeacher" AS ?predicate)
    }
    OPTIONAL { ?subject rdfs:label ?subjectLabel . }
    OPTIONAL { ?object rdfs:label ?objectLabel . }
  }
}
"""

def get_fuseki_data():
    """Fetches data from Fuseki using a SPARQL query."""
    headers = {
        "Accept": "application/sparql-results+json"
    }
    params = {
        "query": SPARQL_QUERY
    }
    try:
        response = requests.get(FUSEKI_QUERY_URL, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi kết nối Fuseki: {e}")
        return None

def process_data_for_cytoscape(sparql_results):
    """Processes SPARQL results into Cytoscape.js format, ensuring unique IDs and correct relationship direction."""
    elements = []
    nodes = {}

    for binding in sparql_results['results']['bindings']:
        subject_uri = binding['subject']['value']
        object_uri = binding['object']['value']
        subject_label = binding.get('subjectLabel', {}).get('value', subject_uri.split('/')[-1]).replace('_', ' ')
        object_label = binding.get('objectLabel', {}).get('value', object_uri.split('/')[-1]).replace('_', ' ')
        predicate = binding['predicate']['value']
        
        # Add nodes if they don't exist
        if subject_uri not in nodes:
            nodes[subject_uri] = True
            elements.append({
                'data': {'id': subject_uri, 'label': subject_label}
            })
        if object_uri not in nodes:
            nodes[object_uri] = True
            elements.append({
                'data': {'id': object_uri, 'label': object_label}
            })

        # Correct relationship direction for a family tree (parent -> child)
        source_uri = ""
        target_uri = ""
        edge_label = ""

        if predicate == "hasDisciple":
            source_uri = subject_uri
            target_uri = object_uri
            edge_label = "Đệ tử"
        elif predicate == "hasTeacher":
            source_uri = object_uri
            target_uri = subject_uri
            edge_label = "Sư phụ"
        
        # Create a unique ID for the edge to avoid duplicates
        edge_id = f'{source_uri}-{target_uri}-{uuid.uuid4()}'

        elements.append({
            'data': {
                'id': edge_id,
                'source': source_uri,
                'target': target_uri,
                'label': edge_label
            }
        })

    return elements

def main():
    """Main function to fetch, process, and save data."""
    print("Đang lấy dữ liệu từ Fuseki...")
    sparql_results = get_fuseki_data()
    
    if sparql_results:
        cytoscape_elements = process_data_for_cytoscape(sparql_results)
        
        with open('cytoscape_data.json', 'w', encoding='utf-8') as f:
            json.dump(cytoscape_elements, f, ensure_ascii=False, indent=2)
        print("✔️ Đã lưu dữ liệu vào file cytoscape_data.json thành công!")
    else:
        print("❌ Không thể lấy dữ liệu. Vui lòng kiểm tra kết nối Fuseki.")

if __name__ == "__main__":
    main()