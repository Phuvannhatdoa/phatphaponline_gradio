#!/usr/bin/env python3
"""
P1 Setup: Place Ontology Validator & Loader
Kiểm tra và load Place ontology vào GraphDB

Usage:
    python3 setup_place_ontology.py --validate    # Chỉ kiểm tra syntax
    python3 setup_place_ontology.py --load        # Load vào GraphDB
    python3 setup_place_ontology.py --test        # Test query mẫu
"""

import sys
import os
import argparse
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

# Configuration
GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/buddhist"
PROJECT_ROOT = "/opt/phatphaponline_gradio/daoanh"
ONTOLOGY_DIR = os.path.join(PROJECT_ROOT, "ontology")

# Namespaces
BKG = Namespace("http://www.phatphaponline.org/ontology/buddhist-kg#")
SCHEMA = Namespace("http://schema.org/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")

def validate_ttl_files():
    """Kiểm tra syntax của các file TTL"""
    print("=" * 60)
    print("P1: VALIDATE TTL FILES")
    print("=" * 60)
    
    ttl_files = [
        "place_schema.ttl",
        "sample_isipatana.ttl"
    ]
    
    for filename in ttl_files:
        filepath = os.path.join(ONTOLOGY_DIR, filename)
        print(f"\n📄 Kiểm tra: {filename}")
        
        if not os.path.exists(filepath):
            print(f"   ❌ File không tồn tại: {filepath}")
            continue
            
        try:
            g = Graph()
            g.parse(filepath, format="turtle")
            print(f"   ✅ Syntax OK - {len(g)} triples")
            
            # Check required classes
            classes = [
                (BKG.BuddhistPlace, "bkg:BuddhistPlace"),
                (BKG.PlaceType, "bkg:PlaceType"),
                (BKG.SacredSite, "bkg:SacredSite"),
            ]
            
            print("   📋 Classes found:")
            for cls, name in classes:
                if (cls, RDF.type, OWL.Class) in g or (cls, RDFS.subClassOf, None) in g:
                    print(f"      ✓ {name}")
            
            # Check sample instance
            if filename == "sample_isipatana.ttl":
                print("   📍 Sample Instance Check:")
                isipatana = URIRef("http://www.phatphaponline.org/ontology/buddhist-kg#place_ISIPATANA")
                
                # Check properties
                props = {
                    BKG.nameVietnamese: "Tên Hán-Việt",
                    GEO.lat: "Vĩ độ",
                    GEO.long: "Kinh độ",
                    SCHEMA.description: "Mô tả"
                }
                
                for prop, label in props.items():
                    values = list(g.objects(isipatana, prop))
                    if values:
                        val_str = str(values[0])[:50]
                        print(f"      ✓ {label}: {val_str}...")
                    else:
                        print(f"      ⚠ {label}: NOT FOUND")
                        
        except Exception as e:
            print(f"   ❌ Lỗi: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ VALIDATION COMPLETE")
    print("=" * 60)

def test_graphdb_connection():
    """Test kết nối GraphDB"""
    print("\n🔌 Testing GraphDB Connection...")
    
    try:
        import requests
        
        # Check if GraphDB is running
        response = requests.get(
            "http://localhost:7200/",
            timeout=5
        )
        
        if response.status_code == 200:
            print("   ✅ GraphDB is running at localhost:7200")
        else:
            print(f"   ⚠ GraphDB returned status: {response.status_code}")
            
    except ImportError:
        print("   ⚠ requests library not available - skipping GraphDB test")
    except Exception as e:
        print(f"   ❌ Cannot connect to GraphDB: {str(e)}")
        print("   💡 Đảm bảo GraphDB đang chạy: sudo systemctl start graphdb")

def load_to_graphdb():
    """Load Place ontology vào GraphDB"""
    print("\n📤 LOADING TO GRAPHDB")
    print("   (Chức năng này sẽ được gọi sau khi Admin duyệt mẫu)")
    print("   Lệnh: curl -X POST -F file=@ontology/place_schema.ttl ...")
    print("   hoặc sử dụng GraphDB Workbench")

def main():
    parser = argparse.ArgumentParser(description="P1: Place Ontology Setup")
    parser.add_argument("--validate", action="store_true", help="Validate TTL files")
    parser.add_argument("--load", action="store_true", help="Load to GraphDB")
    parser.add_argument("--test", action="store_true", help="Test GraphDB connection")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        args.validate = True
        args.test = True
    
    if args.validate:
        validate_ttl_files()
    
    if args.test:
        test_graphdb_connection()
    
    if args.load:
        load_to_graphdb()

if __name__ == "__main__":
    main()
