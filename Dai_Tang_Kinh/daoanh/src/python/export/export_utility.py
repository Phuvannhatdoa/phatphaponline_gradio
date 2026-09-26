#!/usr/bin/env python3
"""
Data Export Utility - Export data to various formats
Export to JSON, CSV, TTL, GeoJSON for GIS

@version: v4.23 (2026-04-10)
@file: src/python/export/export_utility.py
"""

import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Optional


class DataExporter:
    """Export data to various formats"""
    
    def __init__(self, output_dir: str = 'exports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {'exported': 0, 'errors': 0}
    
    def export_json(self, data: List[Dict], filename: str) -> str:
        """Export to JSON format"""
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.stats['exported'] += len(data)
            print(f"[DataExporter] Exported {len(data)} records to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"[DataExporter] Error: {e}")
            return ''
    
    def export_csv(self, data: List[Dict], filename: str, fields: List[str] = None) -> str:
        """Export to CSV format"""
        if not data:
            return ''
        
        output_path = self.output_dir / filename
        
        # Auto-detect fields if not provided
        if fields is None:
            fields = list(data[0].keys())
        
        try:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            
            self.stats['exported'] += len(data)
            print(f"[DataExporter] Exported {len(data)} records to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"[DataExporter] Error: {e}")
            return ''
    
    def export_geojson(self, data: List[Dict], filename: str, 
                      lat_field: str = 'lat', lng_field: str = 'lng',
                      label_field: str = 'name') -> str:
        """Export to GeoJSON format for GIS"""
        features = []
        
        for item in data:
            lat = item.get(lat_field)
            lng = item.get(lng_field)
            
            if lat is not None and lng is not None:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [float(lng), float(lat)]
                    },
                    'properties': {
                        'name': item.get(label_field, ''),
                        **{k: v for k, v in item.items() if k not in [lat_field, lng_field]}
                    }
                }
                features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        self.stats['exported'] += len(features)
        print(f"[DataExporter] Exported {len(features)} geojson features to {output_path}")
        return str(output_path)
    
    def export_ttl(self, data: List[Dict], filename: str, base_uri: str = 'http://phatphaponline.org/entity/') -> str:
        """Export to Turtle RDF format"""
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write prefixes
                f.write('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n')
                f.write('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n')
                f.write('@prefix : <http://phatphaponline.org/ontology#> .\n\n')
                
                for item in data:
                    entity_id = item.get('id', item.get('name', 'unknown'))
                    uri = f'<{base_uri}{entity_id}>'
                    
                    f.write(f'{uri} a :Entity .\n')
                    
                    for key, value in item.items():
                        if key not in ['id'] and value:
                            safe_value = str(value).replace('"', '\\"')
                            f.write(f'{uri} :{key} "{safe_value}" .\n')
                    
                    f.write('\n')
            
            self.stats['exported'] += len(data)
            print(f"[DataExporter] Exported {len(data)} TTL records to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"[DataExporter] Error: {e}")
            return ''
    
    def export_lineage_tree(self, relations: List[Dict], filename: str) -> str:
        """Export lineage relationships as tree structure"""
        tree = self._build_tree(relations)
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            self._write_tree(f, tree, 0)
        
        print(f"[DataExporter] Exported lineage tree to {output_path}")
        return str(output_path)
    
    def _build_tree(self, relations: List[Dict]) -> Dict:
        """Build tree from parent-child relations"""
        tree = {}
        
        for rel in relations:
            parent = rel.get('parent')
            child = rel.get('child')
            
            if parent not in tree:
                tree[parent] = {'children': [], 'parents': []}
            if child not in tree:
                tree[child] = {'children': [], 'parents': []}
            
            tree[parent]['children'].append(child)
            tree[child]['parents'].append(parent)
        
        return tree
    
    def _write_tree(self, f, node, name, indent=0):
        """Recursively write tree structure"""
        prefix = '  ' * indent
        f.write(f'{prefix}- {name}\n')
        
        if name in node:
            for child in node[name].get('children', []):
                self._write_tree(f, node, child, indent + 1)
    
    def get_stats(self) -> Dict:
        return self.stats.copy()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Data Export Utility')
    parser.add_argument('--input', required=True, help='Input JSON file')
    parser.add_argument('--output-dir', default='exports', help='Output directory')
    parser.add_argument('--format', choices=['json', 'csv', 'geojson', 'ttl'], default='json')
    parser.add_argument('--fields', nargs='*', help='Fields to export (CSV)')
    
    args = parser.parse_args()
    
    exporter = DataExporter(args.output_dir)
    
    # Load data
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    # Export
    base_name = Path(args.input).stem
    
    if args.format == 'json':
        exporter.export_json(data, f'{base_name}.json')
    elif args.format == 'csv':
        exporter.export_csv(data, f'{base_name}.csv', args.fields)
    elif args.format == 'geojson':
        exporter.export_geojson(data, f'{base_name}.geojson')
    elif args.format == 'ttl':
        exporter.export_ttl(data, f'{base_name}.ttl')
    
    print(f"[DataExporter] Stats: {exporter.get_stats()}")


if __name__ == '__main__':
    main()
