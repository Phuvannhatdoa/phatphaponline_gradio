#!/usr/bin/env python3
"""
Generate owl:sameAs Linking - DILA ↔ TTL Entity Mapping
Creates owl:sameAs statements for entity linking across data sources

@version: v1.0 (2026-04-14)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import argparse


class SameAsGenerator:
    """Generate owl:sameAs links between DILA and TTL entities"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.mappings = []
        self.entity_map = {}
    
    def normalize(self, name: str) -> str:
        """Normalize name for matching"""
        name = name.lower().strip()
        replacements = {
            'áàảãạăắằẳẵặâấầẩẫậ': 'a',
            'éèẻẽẹêếềểễệ': 'e',
            'íìỉĩị': 'i',
            'óòỏõọôốồổỗộơớờởỡợ': 'o',
            'úùủũụưứừửữứự': 'u',
            'ýỳỷỹỵ': 'y',
            'đ': 'd',
        }
        for old, new in replacements.items():
            for char in old:
                name = name.replace(char, new)
        name = re.sub(r'[\s\-–—.,;:!?"\'\(\)\[\]]+', '', name)
        return name
    
    def extract_persons(self, persons_file: str = 'persons.json') -> Dict[str, str]:
        """Extract person names from persons.json"""
        persons = {}
        json_path = self.data_dir / persons_file
        
        if not json_path.exists():
            print(f"[WARN] File not found: {json_path}")
            return persons
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            person_list = data if isinstance(data, list) else data.get('persons', [])
            print(f"[PERSONS] Found {len(person_list)} entries")
            
            for i, p in enumerate(person_list[:1000]):
                pth_id = p.get('id', '')
                if not pth_id:
                    continue
                
                names = p.get('names', [])
                for name_entry in names:
                    name = name_entry.get('value', '')
                    if name:
                        norm = self.normalize(name)
                        if norm not in persons:
                            persons[norm] = {'name': name, 'id': pth_id}
        except Exception as e:
            print(f"[ERROR] {e}")
        
        return persons
    
    def extract_dila_entities(self, dila_dir: str = 'data/dila_import/Authority-Databases/authority_person') -> Dict[str, str]:
        """Extract DILA authority IDs from XML"""
        entities = {}
        xml_path = Path(dila_dir)
        
        if not xml_path.exists():
            print(f"[WARN] DILA path not found: {xml_path}")
            return entities
        
        xml_file = xml_path / 'Buddhist_Studies_Person_Authority.xml'
        if not xml_file.exists():
            return entities
        
        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for record in root.findall('.//{*}record'):
                aid = record.get('id', '')
                if not aid:
                    continue
                
                for name_elem in record.findall('.//{*}name'):
                    name = name_elem.text or ''
                    if name:
                        norm = self.normalize(name)
                        entities[norm] = {'name': name, 'id': aid}
            
            print(f"[DILA] Found {len(entities)} authority records")
        except Exception as e:
            print(f"[ERROR] XML parse: {e}")
        
        return entities
    
    def find_sameas_links(self) -> List[Dict]:
        """Find owl:sameAs links between sources"""
        print("[SAMEAS] Finding entity links...")
        
        persons = self.extract_persons()
        print(f"[PERSONS] Indexed {len(persons)} person names")
        
        dila_entities = self.extract_dila_entities()
        print(f"[DILA] Indexed {len(dila_entities)} authority names")
        
        links = []
        matched = 0
        
        for norm, p in persons.items():
            if norm in dila_entities:
                links.append({
                    'pth:' + p['id']: 'dila:' + dila_entities[norm]['id'],
                    'source_name': p['name'],
                    'target_name': dila_entities[norm]['name']
                })
                matched += 1
                self.mappings.append((p['id'], dila_entities[norm]['id']))
        
        print(f"[SAMEAS] Found {matched} exact matches")
        return links
    
    def generate_ttl_sameas(self, links: List[Dict], output_file: str = 'entity_sameas.ttl') -> str:
        """Generate TTL file with owl:sameAs statements"""
        ttl_path = self.output_dir / output_file
        
        with open(ttl_path, 'w', encoding='utf-8') as f:
            f.write("@prefix pth: <http://phatphaponline.org/> .\n")
            f.write("@prefix dila: <http://dila.edu.vn/> .\n")
            f.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n\n")
            
            for link in links:
                for pth_id, dila_id in link.items():
                    if pth_id.startswith('pth:'):
                        f.write(f"{pth_id} owl:sameAs {dila_id} .\n")
        
        print(f"[SAMEAS] Generated {ttl_path}")
        return str(ttl_path)
    
    def generate_json_mapping(self, output_file: str = 'entity_mapping.json') -> str:
        """Generate JSON mapping file"""
        mapping = {
            'mappings': [
                {'pth': p, 'dila': d} for p, d in self.mappings
            ],
            'total': len(self.mappings)
        }
        
        json_path = self.output_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"[SAMEAS] Generated {json_path}")
        return str(json_path)


def main():
    parser = argparse.ArgumentParser(description='Generate owl:sameAs entity links')
    parser.add_argument('--data', '-d', default='data', help='Data directory')
    parser.add_argument('--output', '-o', default='data/indexed', help='Output directory')
    args = parser.parse_args()
    
    generator = SameAsGenerator(args.data, args.output)
    links = generator.find_sameas_links()
    
    if links:
        ttl_file = generator.generate_ttl_sameas(links)
        json_file = generator.generate_json_mapping()
        print(f"\n[SUCCESS] {len(links)} owl:sameAs links created")
    else:
        print("[WARN] No links found - check data files")


if __name__ == '__main__':
    main()