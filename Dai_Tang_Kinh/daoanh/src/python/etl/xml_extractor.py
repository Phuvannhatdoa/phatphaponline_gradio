#!/usr/bin/env python3
"""
XML Extractor - ETL Pipeline
Parse DILA XML/RDF files

@version: v4.7 (2026-04-10)
@file: src/python/etl/xml_extractor.py
"""

import xml.etree.ElementTree as ET
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Generator, Optional
import argparse


class DILAXMLExtractor:
    """Extract entities từ DILA XML/RDF"""
    
    # DILA XML namespaces
    NAMESPACES = {
        'tei': 'http://www.tei-c.org/ns/1.0',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'dila': 'http://dila.edu.tw/ontology#'
    }
    
    # Entity fields to extract
    PERSON_FIELDS = ['persName', 'birth', 'death', 'floruit', 'sex', 'occupation', 'lineage']
    PLACE_FIELDS = ['placeName', 'location', 'country', 'region', 'lat', 'long']
    RELATION_FIELDS = ['relation', 'relationGrp']
    
    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.stats = {
            'files_processed': 0,
            'persons': 0,
            'places': 0,
            'relations': 0,
            'errors': 0
        }
    
    def extract_file(self, filename: str) -> Generator[dict, None, None]:
        """Extract entities từ một file XML"""
        filepath = self.input_dir / filename
        
        if not filepath.exists():
            print(f"[XMLExtractor] File not found: {filepath}")
            return
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Detect file type
            if self._is_tei(root):
                yield from self._extract_tei(root, filename)
            elif self._is_rdf(root):
                yield from self._extract_rdf(root, filename)
            else:
                yield from self._extract_generic(root, filename)
            
            self.stats['files_processed'] += 1
            
        except ET.ParseError as e:
            print(f"[XMLExtractor] Parse error in {filename}: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            print(f"[XMLExtractor] Error in {filename}: {e}")
            self.stats['errors'] += 1
    
    def extract_all(self, pattern: str = "*.xml") -> List[dict]:
        """Extract tất cả files matching pattern"""
        results = []
        
        for filepath in self.input_dir.glob(pattern):
            for entity in self.extract_file(filepath.name):
                if entity:
                    results.append(entity)
                    self._update_stats(entity)
        
        return results
    
    def _is_tei(self, root: ET.Element) -> bool:
        """Check if XML is TEI format"""
        return 'TEI' in root.tag or 'tei' in root.tag
    
    def _is_rdf(self, root: ET.Element) -> bool:
        """Check if XML is RDF format"""
        return 'RDF' in root.tag or 'rdf:RDF' in root.tag
    
    def _extract_tei(self, root: ET.Element, filename: str) -> Generator[dict, None, None]:
        """Extract từ TEI format"""
        # Find all person entries
        for person in root.findall('.//{http://www.tei-c.org/ns/1.0}person'):
            entity = self._extract_tei_person(person, filename)
            if entity:
                yield entity
        
        # Find all place entries
        for place in root.findall('.//{http://www.tei-c.org/ns/1.0}place'):
            entity = self._extract_tei_place(place, filename)
            if entity:
                yield entity
    
    def _extract_tei_person(self, person: ET.Element, source: str) -> Optional[dict]:
        """Extract person entity từ TEI"""
        entity = {
            'type': 'person',
            'source': source,
            'id': person.get('{http://www.w3.org/XML/1998/namespace}id', ''),
            'names': [],
            'birth': None,
            'death': None,
            'floruit': None,
            'lineage': None,
            'relations': []
        }
        
        # Extract names
        for name in person.findall('.//{http://www.tei-c.org/ns/1.0}persName'):
            name_data = {
                'full': name.text or '',
                'lang': name.get('{http://www.w3.org/XML/1998/namespace}lang', 'zh')
            }
            
            # Get parts of name
            forename = name.find('.//{http://www.tei-c.org/ns/1.0}forename')
            surname = name.find('.//{http://www.tei-c.org/ns/1.0}surname')
            addName = name.find('.//{http://www.tei-c.org/ns/1.0}addName')
            
            if forename:
                name_data['forename'] = forename.text
            if surname:
                name_data['surname'] = surname.text
            if addName:
                name_data['addName'] = addName.text
            
            entity['names'].append(name_data)
        
        # Extract birth/death
        birth = person.find('.//{http://www.tei-c.org/ns/1.0}birth')
        if birth is not None:
            entity['birth'] = {
                'when': birth.get('when', ''),
                'notBefore': birth.get('notBefore', ''),
                'notAfter': birth.get('notAfter', ''),
                'text': birth.text or ''
            }
        
        death = person.find('.//{http://www.tei-c.org/ns/1.0}death')
        if death is not None:
            entity['death'] = {
                'when': death.get('when', ''),
                'notBefore': death.get('notBefore', ''),
                'notAfter': death.get('notAfter', ''),
                'text': death.text or ''
            }
        
        # Extract floruit
        floruit = person.find('.//{http://www.tei-c.org/ns/1.0}floruit')
        if floruit is not None:
            entity['floruit'] = {
                'notBefore': floruit.get('notBefore', ''),
                'notAfter': floruit.get('notAfter', ''),
                'text': floruit.text or ''
            }
        
        # Extract relations (teacher/student)
        for rel in person.findall('.//{http://www.tei-c.org/ns/1.0}relation'):
            rel_data = {
                'type': rel.get('type', ''),
                'ref': rel.get('ref', ''),
                'active': rel.get('active', ''),
                'passive': rel.get('passive', '')
            }
            entity['relations'].append(rel_data)
        
        return entity if entity['names'] else None
    
    def _extract_tei_place(self, place: ET.Element, source: str) -> Optional[dict]:
        """Extract place entity từ TEI"""
        entity = {
            'type': 'place',
            'source': source,
            'id': place.get('{http://www.w3.org/XML/1998/namespace}id', ''),
            'names': [],
            'location': None,
            'coordinates': None
        }
        
        # Extract names
        for name in place.findall('.//{http://www.tei-c.org/ns/1.0}placeName'):
            name_data = {
                'full': name.text or '',
                'lang': name.get('{http://www.w3.org/XML/1998/namespace}lang', 'zh')
            }
            entity['names'].append(name_data)
        
        # Extract coordinates
        location = place.find('.//{http://www.tei-c.org/ns/1.0}location')
        if location is not None:
            geo = location.find('.//{http://www.tei-c.org/ns/1.0}geo')
            if geo is not None and geo.text:
                coords = geo.text.split()
                if len(coords) >= 2:
                    entity['coordinates'] = {
                        'lat': float(coords[0]),
                        'long': float(coords[1])
                    }
            
            # Extract country/region
            country = location.find('.//{http://www.tei-c.org/ns/1.0}country')
            region = location.find('.//{http://www.tei-c.org/ns/1.0}region')
            
            entity['location'] = {
                'country': country.text if country is not None else '',
                'region': region.text if region is not None else ''
            }
        
        return entity if entity['names'] else None
    
    def _extract_rdf(self, root: ET.Element, filename: str) -> Generator[dict, None, None]:
        """Extract từ RDF format"""
        for desc in root.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'):
            about = desc.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')
            
            if not about:
                continue
            
            # Determine type
            rdf_type = desc.find('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type')
            if rdf_type is not None:
                type_uri = rdf_type.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
                
                if 'Person' in type_uri:
                    yield self._extract_rdf_person(desc, about, filename)
                elif 'Place' in type_uri:
                    yield self._extract_rdf_place(desc, about, filename)
    
    def _extract_rdf_person(self, desc: ET.Element, about: str, source: str) -> dict:
        """Extract person từ RDF"""
        entity = {
            'type': 'person',
            'source': source,
            'id': about,
            'names': [],
            'relations': []
        }
        
        for child in desc:
            tag = child.tag.split('}')[-1]  # Remove namespace
            
            if tag == 'label':
                entity['names'].append({'full': child.text or '', 'lang': 'en'})
            elif tag == 'birthDate':
                entity['birth'] = child.text
            elif tag == 'deathDate':
                entity['death'] = child.text
            elif tag == 'lineage':
                entity['lineage'] = child.text
        
        return entity
    
    def _extract_rdf_place(self, desc: ET.Element, about: str, source: str) -> dict:
        """Extract place từ RDF"""
        entity = {
            'type': 'place',
            'source': source,
            'id': about,
            'names': [],
            'coordinates': None
        }
        
        for child in desc:
            tag = child.tag.split('}')[-1]
            
            if tag == 'label':
                entity['names'].append({'full': child.text or '', 'lang': 'en'})
            elif tag == 'lat':
                entity['coordinates'] = {'lat': float(child.text)}
            elif tag == 'long':
                if entity['coordinates']:
                    entity['coordinates']['long'] = float(child.text)
        
        return entity
    
    def _extract_generic(self, root: ET.Element, filename: str) -> Generator[dict, None, None]:
        """Generic extraction fallback"""
        for elem in root.iter():
            if elem.tag.lower() in ['person', 'place', 'relation']:
                yield {
                    'type': elem.tag.lower(),
                    'source': filename,
                    'id': elem.get('id', ''),
                    'text': elem.text,
                    'attrib': dict(elem.attrib)
                }
    
    def _update_stats(self, entity: dict):
        """Update statistics"""
        if entity['type'] == 'person':
            self.stats['persons'] += 1
        elif entity['type'] == 'place':
            self.stats['places'] += 1
        elif entity['type'] == 'relation':
            self.stats['relations'] += 1
    
    def get_stats(self) -> dict:
        """Get extraction statistics"""
        return self.stats.copy()


def main():
    parser = argparse.ArgumentParser(description='DILA XML Extractor')
    parser.add_argument('--input-dir', required=True, help='Input XML directory')
    parser.add_argument('--pattern', default='*.xml', help='File pattern')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    extractor = DILAXMLExtractor(args.input_dir)
    results = extractor.extract_all(args.pattern)
    
    print(f"[XMLExtractor] Extracted {len(results)} entities")
    print(f"[XMLExtractor] Stats: {extractor.get_stats()}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[XMLExtractor] Output saved to {args.output}")


if __name__ == '__main__':
    main()
