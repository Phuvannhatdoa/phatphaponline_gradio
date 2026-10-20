#!/usr/bin/env python3
"""
BDRC Linker - owl:sameAs Integration
Kết nối ID DILA với BDRC qua owl:sameAs

@version: v1.0 (2026-04-14)
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set
fromcollections import defaultdict


class BDRCLinker:
    """Link DILA IDs to BDRC via owl:sameAs"""
    
    BDRC_API = "https://library.bdrc.io/api"
    NAMESPACE = {
        'pth': 'http://phatphaponline.org/',
        'bdrc': 'http://purl.bdrc.org/resource/',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'
    }
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.dila_names = {}      # normalized_name -> dila_id
        self.bdrc_names = {}     # normalized_name -> bdrc_id
        self.sameas_links = []    # [(dila_id, bdrc_id)]
        self.orphans = []       # dila_id without BDRC link
    
    def remove_diacritics(self, text: str) -> str:
        """Remove Vietnamese diacritics"""
        replacements = {
            'áàảãạăắằẳẵặâấầẩẫậ': 'a',
            'éèẻẽẹêếềểễệ': 'e',
            'íìỉĩị': 'i',
            'óòỏõọôốồổỗộơớờởỡợ': 'o',
            'úùủũụưứừửữứự': 'u',
            'ýỳỷỹỵ': 'y',
            'đ': 'd',
            'ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ': 'A',
            'ÉÈẺẼẸÊẾỀỂỄỆ': 'E',
            'ÍÌỈĨỊ': 'I',
            'ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ': 'O',
            'ÚÙỦŨỤƯỪỬỮỨỰ': 'U',
            'ÝỲỶỸỴ': 'Y',
            'Đ': 'D'
        }
        for old, new in replacements.items():
            for char in old:
                text = text.replace(char, new)
        return text
    
    def normalize(self, name: str) -> str:
        """Normalize name for matching"""
        name = name.strip().lower()
        name = self.remove_diacritics(name)
        name = re.sub(r'[\s\-–—.,;:!?\'\"\(\)\[\]]+', '', name)
        return name
    
    def load_dila_names(self, persons_file: str = 'persons.json'):
        """Load names from persons.json"""
        json_path = self.data_dir / persons_file
        
        if not json_path.exists():
            print(f"[WARN] File not found: {json_path}")
            return
        
        print(f"[LOAD] Reading DILA persons from {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        persons = data if isinstance(data, list) else data.get('persons', [])
        print(f"  -> Found {len(persons)} persons")
        
        for p in persons:
            dila_id = p.get('id', '')
            if not dila_id:
                continue
            
            names = p.get('names', [])
            for name_entry in names:
                name = name_entry.get('value', '')
                if name:
                    norm = self.normalize(name)
                    if norm and norm not in self.dila_names:
                        self.dila_names[norm] = dila_id
        
        print(f"  -> Indexed {len(self.dila_names)} unique names")
    
    def load_bdrc_data(self, bdrc_file: Optional[str] = None):
        """Load BDRC data from file or use sample matching"""
        if bdrc_file:
            json_path = self.data_dir / bdrc_file
            if not json_path.exists():
                print(f"[WARN] BDRC file not found: {bdrc_file}")
                return
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                name = item.get('name', '')
                bdrc_id = item.get('id', '')
                if name and bdrc_id:
                    norm = self.normalize(name)
                    self.bdrc_names[norm] = bdrc_id
            
            print(f"[LOAD] Indexed {len(self.bdrc_names)} BDRC names")
        else:
            print("[INFO] No BDRC file - using name-based matching only")
    
    def find_sameas_links(self) -> List[Dict]:
        """Find owl:sameAs links between DILA and BDRC"""
        print("[MATCH] Finding owl:sameAs links...")
        
        matched = 0
        for norm_name, dila_id in self.dila_names.items():
            if norm_name in self.bdrc_names:
                bdrc_id = self.bdrc_names[norm_name]
                self.sameas_links.append({
                    'dila_id': dila_id,
                    'bdrc_id': bdrc_id,
                    'name': norm_name,
                    'relationship': 'owl:sameAs'
                })
                matched += 1
        
        print(f"  -> Found {matched} exact matches")
        
        self.orphans = [dila_id for norm_name, dila_id in self.dila_names.items() 
                     if norm_name not in self.bdrc_names]
        print(f"  -> {len(self.orphans)} DILA IDs without BDRC link")
        
        return self.sameas_links
    
    def generate_ttl(self, output_file: str = 'bdrc_sameas.ttl') -> str:
        """Generate TTL file with owl:sameAs"""
        ttl_path = self.output_dir / output_file
        
        with open(ttl_path, 'w', encoding='utf-8') as f:
            f.write("@prefix pth: <http://phatphaponline.org/> .\n")
            f.write("@prefix bdrc: <http://purl.bdrc.org/resource/> .\n")
            f.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n")
            
            for link in self.sameas_links:
                dila_uri = f"pth:{link['dila_id']}"
                bdrc_uri = f"bdrc:{link['bdrc_id']}"
                
                f.write(f"{dila_uri} owl:sameAs {bdrc_uri} .\n")
                f.write(f"{dila_uri} rdfs:seeAlso <https://library.bdrc.io/resource/{link['bdrc_id']}> .\n")
        
        print(f"[TTL] Generated {ttl_path}")
        return str(ttl_path)
    
    def generate_json_mapping(self, output_file: str = 'bdrc_mapping.json') -> str:
        """Generate JSON mapping file"""
        mapping = {
            'metadata': {
                'source': 'DILA Authority + BDRC',
                'relationship': 'owl:sameAs',
                'generated': '2026-04-14'
            },
            'links': self.sameas_links,
            'statistics': {
                'total_dila': len(self.dila_names),
                'total_bdrc': len(self.bdrc_names),
                'matched': len(self.sameas_links),
                'orphans': len(self.orphans)
            }
        }
        
        json_path = self.output_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"[JSON] Generated {json_path}")
        return str(json_path)
    
    def run(self) -> Dict:
        """Execute full BDRC linking pipeline"""
        print("=" * 50)
        print("BDRC LINKER - owl:sameAs Integration")
        print("=" * 50)
        
        self.load_dila_names('persons.json')
        self.load_bdrc_data()
        self.find_sameas_links()
        
        ttl_file = self.generate_ttl()
        json_file = self.generate_json_mapping()
        
        result = {
            'status': 'complete',
            'matched': len(self.sameas_links),
            'orphans': len(self.orphans),
            'files': {
                'ttl': ttl_file,
                'json': json_file
            }
        }
        
        print("=" * 50)
        print(f"[RESULT] {len(self.sameas_links)} owl:sameAs links created")
        print("=" * 50)
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='BDRC Linker - owl:sameAs')
    parser.add_argument('--data', '-d', default='data', help='Data directory')
    parser.add_argument('--output', '-o', default='data/indexed', help='Output directory')
    args = parser.parse_args()
    
    linker = BDRCLinker(args.data, args.output)
    result = linker.run()
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()