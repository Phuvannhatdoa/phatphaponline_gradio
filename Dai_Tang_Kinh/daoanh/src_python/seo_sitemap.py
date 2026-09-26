#!/usr/bin/env python3
"""
SEO Sitemap Generator
Tạo sitemap.xml cho Google indexing

@version: v1.0 (2026-04-14)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class SitemapGenerator:
    """Generate sitemap for hybrid graph"""
    
    BASE_URL = "https://phatphaponline.org"
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.urls = []
    
    def load_persons(self) -> List[str]:
        """Load person URLs"""
        json_path = self.data_dir / 'persons.json'
        
        if not json_path.exists():
            return []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        persons = data if isinstance(data, list) else data.get('persons', [])
        urls = []
        
        for p in persons:
            pid = p.get('id', '')
            if pid:
                urls.append(f"{self.BASE_URL}/person/{pid}")
        
        return urls
    
    def load_places(self) -> List[str]:
        """Load place URLs"""
        json_path = self.data_dir / 'places.json'
        
        if not json_path.exists():
            return []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        places = data if isinstance(data, list) else data.get('places', [])
        urls = []
        
        for p in places:
            pid = p.get('id', '')
            if pid:
                urls.append(f"{self.BASE_URL}/place/{pid}")
        
        return urls
    
    def generate_sitemap_index(self, urls: List[str], output_file: str = 'sitemap.xml'):
        """Generate sitemap.xml"""
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]
        
        for url in urls[:50000]:  # Limit to 50k per sitemap
            xml_lines.append('  <url>')
            xml_lines.append(f'    <loc>{url}</loc>')
            xml_lines.append('    <changefreq>weekly</changefreq>')
            xml_lines.append('    <priority>0.8</priority>')
            xml_lines.append('  </url>')
        
        xml_lines.append('</urlset>')
        
        sitemap_path = self.output_dir / output_file
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xml_lines))
        
        print(f"[SITEMAP] Generated {sitemap_path} with {len(urls)} URLs")
        return str(sitemap_path)
    
    def generate_schema_jsonld(self, output_file: str = 'schema_persons.jsonld'):
        """Generate Schema.org JSON-LD for persons"""
        json_path = self.data_dir / 'persons.json'
        
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        persons = data if isinstance(data, list) else data.get('persons', [])
        
        schema = {
            "@context": "https://schema.org",
            "@graph": []
        }
        
        for p in persons[:1000]:  # Limit for performance
            pid = p.get('id', '')
            if not pid:
                continue
            
            names = p.get('names', [])
            name = names[0].get('value', '') if names else ''
            
            person_schema = {
                "@type": "Person",
                "@id": f"{self.BASE_URL}/person/{pid}",
                "name": name,
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "authorityId", "value": pid}
                ]
            }
            
            if p.get('birth_year'):
                person_schema['birthDate'] = p.get('birth_year')
            if p.get('death_year'):
                person_schema['deathDate'] = p.get('death_year')
            
            schema['@graph'].append(person_schema)
        
        jsonld_path = self.output_dir / output_file
        with open(jsonld_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        
        print(f"[SCHEMA] Generated {jsonld_path} with {len(schema['@graph'])} persons")
        return str(jsonld_path)
    
    def run(self) -> Dict:
        """Generate all SEO files"""
        print("=" * 60)
        print("SEO SITEMAP GENERATOR")
        print("=" * 60)
        
        person_urls = self.load_persons()
        place_urls = self.load_places()
        
        all_urls = person_urls + place_urls
        print(f"[URLS] Total: {len(all_urls)}")
        
        sitemap = self.generate_sitemap_index(all_urls)
        schema = self.generate_schema_jsonld()
        
        result = {
            'status': 'complete',
            'total_urls': len(all_urls),
            'person_urls': len(person_urls),
            'place_urls': len(place_urls),
            'files': {
                'sitemap': sitemap,
                'schema': schema
            }
        }
        
        print("=" * 60)
        print(f"[RESULT] SEO files generated successfully")
        print("=" * 60)
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SEO Sitemap Generator')
    parser.add_argument('--data', '-d', default='data', help='Data directory')
    parser.add_argument('--output', '-o', default='data/indexed', help='Output directory')
    args = parser.parse_args()
    
    gen = SitemapGenerator(args.data, args.output)
    result = gen.run()
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()