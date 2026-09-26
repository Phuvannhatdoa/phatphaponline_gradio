#!/usr/bin/env python3
"""
RDF Converter - ETL Pipeline
Convert JSONL to Turtle (.ttl) RDF format

@version: v4.9 (2026-04-10)
@file: src/python/etl/rdf_converter.py
"""

import json
import re
import argparse
from pathlib import Path
from typing import Generator, List, Dict, Optional
from datetime import datetime


class RDFConverter:
    """Convert JSONL data to Turtle (.ttl) RDF format"""
    
    # RDF namespaces
    PREFIXES = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'dila': 'http://dila.edu.tw/ontology#',
        'pth': 'http://phatphaponline.org/ontology#',
        '': 'http://phatphaponline.org/entity/'
    }
    
    def __init__(self, output_file: str, base_uri: str = 'http://phatphaponline.org/entity/'):
        self.output_file = Path(output_file)
        self.base_uri = base_uri
        self.stats = {
            'persons': 0,
            'places': 0,
            'relations': 0,
            'triples': 0
        }
        
        # Open output file
        self._file = open(self.output_file, 'w', encoding='utf-8')
        
        # Write prefixes
        self._write_prefixes()
    
    def _write_prefixes(self):
        """Write RDF prefixes"""
        self._file.write("# RDF Turtle - Auto-generated\n")
        self._file.write(f"# Generated: {datetime.now().isoformat()}\n\n")
        
        for prefix, uri in self.PREFIXES.items():
            if prefix:
                self._file.write(f"PREFIX {prefix}: <{uri}>\n")
        
        self._file.write("\n")
    
    def convert(self, jsonl_file: str, entity_type: Optional[str] = None) -> int:
        """Convert JSONL file to TTL"""
        count = 0
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    
                    # Auto-detect type if not specified
                    if not entity_type:
                        entity_type = record.get('type', 'unknown')
                    
                    if entity_type == 'person':
                        self._write_person(record)
                        self.stats['persons'] += 1
                    elif entity_type == 'place':
                        self._write_place(record)
                        self.stats['places'] += 1
                    elif entity_type == 'relation':
                        self._write_relation(record)
                        self.stats['relations'] += 1
                    
                    count += 1
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"[RDFConverter] Error: {e}")
        
        print(f"[RDFConverter] Converted {count} records")
        return count
    
    def convert_record(self, record: dict) -> int:
        """Convert a single JSON record"""
        entity_type = record.get('type', 'unknown')
        triples = 0
        
        if entity_type == 'person':
            triples = self._write_person(record)
        elif entity_type == 'place':
            triples = self._write_place(record)
        elif entity_type == 'relation':
            triples = self._write_relation(record)
        
        return triples
    
    def _write_person(self, person: dict) -> int:
        """Write person entity to TTL"""
        triples = 0
        
        # Get ID
        person_id = person.get('id', '')
        if not person_id:
            # Generate ID from name
            names = person.get('names', [])
            if names:
                person_id = self._generate_id(names[0].get('full', 'unknown'))
            else:
                person_id = 'unknown'
        
        uri = self._make_uri(person_id)
        
        # Type declaration
        self._file.write(f"{uri} a :Monk .\n")
        triples += 1
        
        # Names (multilingual)
        for name_obj in person.get('names', []):
            name = name_obj.get('full', '')
            lang = name_obj.get('lang', 'en')
            
            if name:
                escaped_name = self._escape_string(name)
                self._file.write(f"{uri} rdfs:label \"\"\"{escaped_name}\"\"@{lang} .\n")
                triples += 1
        
        # Birth
        birth = person.get('birth')
        if birth:
            if isinstance(birth, dict):
                when = birth.get('when', '')
                if when:
                    self._file.write(f"{uri} :birth \"{when}\"^^xsd:integer .\n")
                    triples += 1
            else:
                self._file.write(f"{uri} :birth \"{birth}\"^^xsd:integer .\n")
                triples += 1
        
        # Death
        death = person.get('death')
        if death:
            if isinstance(death, dict):
                when = death.get('when', '')
                if when:
                    self._file.write(f"{uri} :death \"{when}\"^^xsd:integer .\n")
                    triples += 1
            else:
                self._file.write(f"{uri} :death \"{death}\"^^xsd:integer .\n")
                triples += 1
        
        # Floruit
        floruit = person.get('floruit')
        if floruit:
            if isinstance(floruit, dict):
                notBefore = floruit.get('notBefore', '')
                notAfter = floruit.get('notAfter', '')
                if notBefore:
                    self._file.write(f"{uri} :floruitStart \"{notBefore}\"^^xsd:integer .\n")
                    triples += 1
                if notAfter:
                    self._file.write(f"{uri} :floruitEnd \"{notAfter}\"^^xsd:integer .\n")
                    triples += 1
        
        # Lineage
        lineage = person.get('lineage')
        if lineage:
            lineage_uri = self._make_uri(lineage)
            self._file.write(f"{uri} :lineage {lineage_uri} .\n")
            triples += 1
        
        # DILA ID linking
        dila_id = person.get('dila_id')
        if dila_id:
            self._file.write(f"{uri} owl:sameAs dila:{dila_id} .\n")
            triples += 1
        
        self._file.write("\n")
        self.stats['triples'] += triples
        
        return triples
    
    def _write_place(self, place: dict) -> int:
        """Write place entity to TTL"""
        triples = 0
        
        # Get ID
        place_id = place.get('id', '')
        if not place_id:
            names = place.get('names', [])
            if names:
                place_id = self._generate_id(names[0].get('full', 'unknown'))
            else:
                place_id = 'unknown'
        
        uri = self._make_uri(place_id)
        
        # Type
        self._file.write(f"{uri} a :Place .\n")
        triples += 1
        
        # Names
        for name_obj in place.get('names', []):
            name = name_obj.get('full', '')
            lang = name_obj.get('lang', 'en')
            
            if name:
                escaped_name = self._escape_string(name)
                self._file.write(f"{uri} rdfs:label \"\"\"{escaped_name}\"\"@{lang} .\n")
                triples += 1
        
        # Coordinates
        coords = place.get('coordinates')
        if coords:
            lat = coords.get('lat')
            lng = coords.get('long') or coords.get('lng')
            
            if lat and lng:
                self._file.write(f"{uri} :gps \"{lat},{lng}\" .\n")
                triples += 1
        
        # Location (country, region)
        location = place.get('location')
        if location:
            country = location.get('country', '')
            region = location.get('region', '')
            
            if country:
                self._file.write(f"{uri} :country \"{country}\" .\n")
                triples += 1
            if region:
                self._file.write(f"{uri} :region \"{region}\" .\n")
                triples += 1
        
        self._file.write("\n")
        self.stats['triples'] += triples
        
        return triples
    
    def _write_relation(self, relation: dict) -> int:
        """Write relation entity to TTL"""
        triples = 0
        
        # Get subject and object
        subject = relation.get('subject') or relation.get('student')
        obj = relation.get('object') or relation.get('teacher')
        rel_type = relation.get('type', 'relatedTo')
        
        if subject and obj:
            subject_uri = self._make_uri(subject)
            obj_uri = self._make_uri(obj)
            
            # Map relation type
            prop = self._map_relation_type(rel_type)
            
            self._file.write(f"{subject_uri} {prop} {obj_uri} .\n")
            triples += 1
            
            self._file.write("\n")
            self.stats['triples'] += triples
        
        return triples
    
    def _map_relation_type(self, rel_type: str) -> str:
        """Map relation type to RDF property"""
        mapping = {
            'teacher': ':teacher',
            'student': ':student',
            'studentOf': ':teacher',
            'teacherOf': ':student',
            'teacherStudent': ':teacher',
            'friend': ':friend',
            'colleague': ':colleague',
            'lineage': ':lineage',
            'sameAs': 'owl:sameAs'
        }
        
        return mapping.get(rel_type.lower(), ':relatedTo')
    
    def _make_uri(self, identifier: str) -> str:
        """Create URI from identifier"""
        # Clean identifier
        clean_id = re.sub(r'[^\w\-]', '_', str(identifier))
        return f"<{self.base_uri}{clean_id}>"
    
    def _generate_id(self, name: str) -> str:
        """Generate ID from name"""
        # Remove special chars, convert to snake_case
        clean = re.sub(r'[^\w\s]', '', name)
        return clean.strip().replace(' ', '_')
    
    def _escape_string(self, s: str) -> str:
        """Escape string for Turtle"""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    def close(self):
        """Close output file"""
        if hasattr(self, '_file') and self._file:
            self._file.close()
    
    def get_stats(self) -> dict:
        """Get conversion statistics"""
        return self.stats.copy()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    parser = argparse.ArgumentParser(description='RDF Converter - JSONL to Turtle')
    parser.add_argument('--input', required=True, help='Input JSONL file')
    parser.add_argument('--output', required=True, help='Output TTL file')
    parser.add_argument('--base-uri', default='http://phatphaponline.org/entity/', help='Base URI')
    parser.add_argument('--type', choices=['person', 'place', 'relation'], help='Entity type (auto-detect if not specified)')
    
    args = parser.parse_args()
    
    converter = RDFConverter(args.output, args.base_uri)
    
    try:
        count = converter.convert(args.input, args.type)
        
        stats = converter.get_stats()
        print(f"[RDFConverter] Conversion complete:")
        print(f"  - Persons: {stats['persons']}")
        print(f"  - Places: {stats['places']}")
        print(f"  - Relations: {stats['relations']}")
        print(f"  - Total triples: {stats['triples']}")
        print(f"  - Output: {args.output}")
        
    finally:
        converter.close()


if __name__ == '__main__':
    main()
