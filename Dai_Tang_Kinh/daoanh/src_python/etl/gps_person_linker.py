#!/usr/bin/env python3
"""
GPS Person Linker - Link Temples (Place) with Monks (Person)
Tạo quan hệ giữa GPS coordinates và các vị Tổ trụ trì

@version: v1.0 (2026-04-14)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional


class GPSPersonLinker:
    """Link GPS places with person data"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.places = {}       # place_id -> place_data
        self.persons = {}      # person_id -> person_data
        self.place_person_links = []  # [(place_id, person_id, role)]
    
    def remove_diacritics(self, text: str) -> str:
        """Remove Vietnamese diacritics"""
        replacements = {
            'áàảãạăắằẳẵặâấầẩẫậ': 'a',
            'éèẻẽẹêếềểễệ': 'e',
            'íìỉĩị': 'i',
            'óòỏõọôốồổỗộơớờởỡợ': 'o',
            'úùủũụưứừửữứự': 'u',
            'ýỳỷỹỵ': 'y',
            'đ': 'd'
        }
        for old, new in replacements.items():
            for char in old:
                text = text.replace(char, new)
        return text
    
    def normalize(self, text: str) -> str:
        """Normalize name for matching"""
        text = text.strip().lower()
        text = self.remove_diacritics(text)
        text = re.sub(r'[\s\-–—.,;:!?\'\"\(\)\[\]]+', '', text)
        return text
    
    def load_places(self, places_file: str = 'places.json'):
        """Load places with GPS"""
        json_path = self.data_dir / places_file
        
        if not json_path.exists():
            print(f"[WARN] File not found: {json_path}")
            return
        
        print(f"[LOAD] Reading places from {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        places = data if isinstance(data, list) else data.get('places', data.get('features', []))
        print(f"  -> Found {len(places)} places")
        
        for p in places:
            place_id = p.get('id', '')
            if not place_id:
                continue
            
            name = p.get('nameChinese', p.get('nameEnglish', p.get('nameVietnamese', '')))
            lat_str = p.get('lat', '0')
            lon_str = p.get('lon', '0')
            
            try:
                lat = float(lat_str) if lat_str and lat_str.strip() else 0
                lng = float(lon_str) if lon_str and lon_str.strip() else 0
            except (ValueError, TypeError):
                lat, lng = 0, 0
            
            if name and lat and lng:
                self.places[place_id] = {
                    'id': place_id,
                    'name': name,
                    'lat': float(lat),
                    'lng': float(lng),
                    'normalized': self.normalize(name)
                }
        
        print(f"  -> Indexed {len(self.places)} places with GPS")
    
    def load_persons(self, persons_file: str = 'persons.json'):
        """Load persons with names"""
        json_path = self.data_dir / persons_file
        
        if not json_path.exists():
            print(f"[WARN] File not found: {json_path}")
            return
        
        print(f"[LOAD] Reading persons from {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        persons = data if isinstance(data, list) else data.get('persons', [])
        print(f"  -> Found {len(persons)} persons")
        
        for p in persons:
            person_id = p.get('id', '')
            if not person_id:
                continue
            
            names = p.get('names', [])
            for name_entry in names:
                name = name_entry.get('value', '')
                if name:
                    norm = self.normalize(name)
                    if norm not in self.persons:
                        self.persons[norm] = {
                            'id': person_id,
                            'names': [name]
                        }
                    else:
                        self.persons[norm]['names'].append(name)
        
        print(f"  -> Indexed {len(self.persons)} person names")
    
    def find_temple_links(self) -> List[Dict]:
        """Find links between temples and monks - simplified"""
        print("[MATCH] Finding Place-Person links...")
        print("[INFO] Skipping complex matching - generating map data only")
        
        # For now, just use places for map visualization
        # Complex matching will be done with external data later
        return []
    
    def generate_map_data(self, output_file: str = 'map_data.json') -> str:
        """Generate map data for visualization"""
        map_data = {
            'type': 'FeatureCollection',
            'features': [],
            'metadata': {
                'total_places': len(self.places),
                'total_links': len(self.place_person_links)
            }
        }
        
        for place_id, place_data in self.places.items():
            linked_persons = [
                link for link in self.place_person_links 
                if link['place_id'] == place_id
            ]
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [
                        place_data['lng'],
                        place_data['lat']
                    ]
                },
                'properties': {
                    'id': place_id,
                    'name': place_data['name'],
                    'monks': [
                        {
                            'id': lp['person_id'],
                            'name': lp['person_name'],
                            'relationship': lp['relationship']
                        } for lp in linked_persons
                    ]
                }
            }
            map_data['features'].append(feature)
        
        json_path = self.output_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        
        print(f"[MAP] Generated {json_path}")
        return str(json_path)
    
    def generate_lineage_graph(self, output_file: str = 'place_lineage.ttl') -> str:
        """Generate TTL with place-person relationships"""
        ttl_path = self.output_dir / output_file
        
        with open(ttl_path, 'w', encoding='utf-8') as f:
            f.write("@prefix pth: <http://phatphaponline.org/> .\n")
            f.write("@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .\n")
            f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n")
            
            for place_id, place_data in self.places.items():
                lat = place_data['lat']
                lng = place_data['lng']
                
                f.write(f"pth:{place_id} geo:lat {lat} .\n")
                f.write(f"pth:{place_id} geo:long {lng} .\n")
                
                linked = [l for l in self.place_person_links if l['place_id'] == place_id]
                for link in linked:
                    person_id = link['person_id']
                    rel = link['relationship']
                    f.write(f"pth:{person_id} pth:{rel} pth:{place_id} .\n")
        
        print(f"[TTL] Generated {ttl_path}")
        return str(ttl_path)
    
    def generate_json_mapping(self, output_file: str = 'place_person_mapping.json') -> str:
        """Generate JSON mapping"""
        mapping = {
            'metadata': {
                'source': 'DILA Authority',
                'relationship': 'place-person',
                'generated': '2026-04-14'
            },
            'links': self.place_person_links,
            'statistics': {
                'total_places': len(self.places),
                'total_persons': len(self.persons),
                'links_found': len(self.place_person_links)
            }
        }
        
        json_path = self.output_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"[JSON] Generated {json_path}")
        return str(json_path)
    
    def run(self) -> Dict:
        """Execute GPS Person linking"""
        print("=" * 50)
        print("GPS PERSON LINKER - Temple-Monks Integration")
        print("=" * 50)
        
        self.load_places('places.json')
        self.load_persons('persons.json')
        self.find_temple_links()
        
        map_file = self.generate_map_data()
        ttl_file = self.generate_lineage_graph()
        json_file = self.generate_json_mapping()
        
        result = {
            'status': 'complete',
            'places': len(self.places),
            'persons': len(self.persons),
            'links': len(self.place_person_links),
            'files': {
                'map': map_file,
                'ttl': ttl_file,
                'json': json_file
            }
        }
        
        print("=" * 50)
        print(f"[RESULT] {len(self.place_person_links)} place-person links")
        print("=" * 50)
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='GPS Person Linker')
    parser.add_argument('--data', '-d', default='data', help='Data directory')
    parser.add_argument('--output', '-o', default='data/indexed', help='Output directory')
    args = parser.parse_args()
    
    linker = GPSPersonLinker(args.data, args.output)
    result = linker.run()
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()