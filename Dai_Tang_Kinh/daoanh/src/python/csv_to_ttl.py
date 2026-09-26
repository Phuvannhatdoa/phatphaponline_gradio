#!/usr/bin/env python3
"""
CSV to TTL Converter for Vietnam Buddhist Places
Multi-source integration with owl:sameAs linking

@version: v1.0 (2026-04-10)
@file: csv_to_ttl.py
"""

import csv
import os
import argparse
from datetime import datetime
from pathlib import Path


class CSVToTTLConverter:
    """Convert Vietnam Buddhist Places CSV to Turtle RDF"""
    
    PREFIXES = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .
@prefix schema: <http://schema.org/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix dila: <http://www.dila.edu.tw/rdf/entity/> .
@prefix pth: <http://phatphaponline.org/entity/> .
@prefix ja: <http://example.org/ja/> .
@prefix zh: <http://example.org/zh/> .
@prefix sa: <http://example.org/sa/> .
@prefix pi: <http://example.org/pi/> .
@prefix vi: <http://example.org/vi/> .
@prefix en: <http://example.org/en/> .
"""
    
    def __init__(self, input_file, output_file=None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else input_file.replace('.csv', '.ttl')
        self.places = []
        self.stats = {
            'total': 0,
            'with_dila': 0,
            'with_wiki': 0,
            'with_stardict': 0,
            'with_phahe': 0,
            'multi_language': 0
        }
    
    def parse_csv(self):
        """Parse CSV file with multi-language support"""
        print(f"[CSVToTTL] Parsing: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            
            for row in reader:
                # Skip comments and empty rows
                if not row.get('id') or row['id'].startswith('#'):
                    continue
                
                self.places.append(row)
                self.stats['total'] += 1
                
                # Track sources
                if row.get('dila_id'): self.stats['with_dila'] += 1
                if row.get('wikidata_id'): self.stats['with_wiki'] += 1
                if row.get('stardict_id'): self.stats['with_stardict'] += 1
                if row.get('bkg_id'): self.stats['with_phahe'] += 1
                
                # Multi-language check
                langs = [row.get('nameJapanese'), row.get('nameChinese'), 
                        row.get('nameSanskrit'), row.get('namePali')]
                if any(langs):
                    self.stats['multi_language'] += 1
        
        print(f"[CSVToTTL] Parsed {self.stats['total']} places")
        return self.places
    
    def generate_ttl(self):
        """Generate Turtle RDF with owl:sameAs linking"""
        print(f"[CSVToTTL] Generating TTL: {self.output_file}")
        
        lines = []
        lines.append("# Vietnam Buddhist Places - Multi-Source RDF")
        lines.append(f"# Generated: {datetime.now().isoformat()}")
        lines.append(self.PREFIXES)
        lines.append("")
        
        for place in self.places:
            uri = self._generate_uri(place['id'])
            lines.append(f"{uri} a bkg:BuddhistPlace ;")
            
            # Names with language tags (multi-language)
            namesAdded = False
            nameOrder = [
                ('nameVietnamese', 'vi'),
                ('nameJapanese', 'ja'),
                ('nameChinese', 'zh'),
                ('nameSanskrit', 'sa'),
                ('namePali', 'pi'),
                ('nameEnglish', 'en')
            ]
            
            for field, lang in nameOrder:
                value = place.get(field, '').strip()
                if value:
                    safe_value = self._escape(value)
                    lines.append(f"    rdfs:label \"{safe_value}\"@{lang} ;")
                    namesAdded = True
            
            # GPS
            lat = place.get('lat', '').strip()
            lon = place.get('lon', '').strip()
            if lat and lon:
                lines.append(f"    geo:lat {lat} ;")
                lines.append(f"    geo:long {lon} ;")
            
            # Country & Province
            country = place.get('country', '').strip()
            province = place.get('province', '').strip()
            if province:
                province_safe = self._escape(province)
                lines.append(f"    dgm:province \"{province_safe}\" ;")
            if country:
                lines.append(f"    dgm:country \"{country}\" ;")
            
            # Place Type
            place_type = place.get('placeType', '').strip()
            if place_type:
                type_uri = f"bkg:{place_type}" if place_type in ['Temple', 'Monastery', 'Stupa', 'Shrine', 'Cave'] else f"bkg:OtherPlaceType"
                lines.append(f"    bkg:placeType {type_uri} ;")
            
            # owl:sameAs links (multi-source integration)
            dila_id = place.get('dila_id', '').strip()
            stardict_id = place.get('stardict_id', '').strip()
            wikidata_id = place.get('wikidata_id', '').strip()
            bkg_id = place.get('bkg_id', '').strip()
            
            sameAsLinks = []
            if dila_id:
                sameAsLinks.append(f"dila:{dila_id}")
            if stardict_id:
                sameAsLinks.append(f"pth:{stardict_id}")
            if wikidata_id:
                sameAsLinks.append(f"<https://www.wikidata.org/entity/{wikidata_id}>")
            if bkg_id:
                sameAsLinks.append(f"bkg:{bkg_id}")
            
            for link in sameAsLinks[:-1]:
                lines.append(f"    owl:sameAs {link} ;")
            if sameAsLinks:
                lines.append(f"    owl:sameAs {sameAsLinks[-1]} .")
            else:
                lines[-1] = lines[-1].rstrip(';') + ' .'
            
            lines.append("")
        
        # Write output
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"[CSVToTTL] Generated: {self.output_file}")
        print(f"[CSVToTTL] Stats: {self.stats}")
        return self.output_file
    
    def _generate_uri(self, place_id):
        """Generate URI for place"""
        return f"pth:{place_id}"
    
    def _escape(self, s):
        """Escape string for TTL"""
        if not s:
            return ""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
    
    def get_stats(self):
        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Convert Vietnam Buddhist Places CSV to TTL')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file')
    parser.add_argument('--output', '-o', help='Output TTL file (optional)')
    args = parser.parse_args()
    
    converter = CSVToTTLConverter(args.input, args.output)
    converter.parse_csv()
    converter.generate_ttl()
    
    print("\n[CSVToTTL] Done!")
    print(f"Total places: {converter.stats['total']}")
    print(f"Multi-language: {converter.stats['multi_language']}")
    print(f"With DILA link: {converter.stats['with_dila']}")
    print(f"With Wiki link: {converter.stats['with_wiki']}")


if __name__ == '__main__':
    main()