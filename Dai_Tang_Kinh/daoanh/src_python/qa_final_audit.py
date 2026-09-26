#!/usr/bin/env python3
"""
Final QA Audit - Data Integrity Check
Kiểm tra toàn vẹn dữ liệu trước khi production

@version: v1.0 (2026-04-14)
"""

import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


class FinalQAAuditor:
    """Final QA audit cho hybrid graph"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        
        self.persons = {}      # id -> data
        self.places = {}      # id -> data
        self.dicts = {}      # term -> data
        
        self.issues = []    # list of issues found
        self.stats = {}
    
    def load_all(self):
        """Load all data sources"""
        print("[LOAD] Loading data for final QA...")
        
        # Load persons
        persons_file = self.data_dir / 'persons.json'
        if persons_file.exists():
            with open(persons_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            persons = data if isinstance(data, list) else data.get('persons', [])
            for p in persons:
                pid = p.get('id', '')
                if pid:
                    self.persons[pid] = p
            print(f"  -> persons: {len(self.persons)}")
        
        # Load places
        places_file = self.data_dir / 'places.json'
        if places_file.exists():
            with open(places_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            places = data if isinstance(data, list) else data.get('places', [])
            for p in places:
                pid = p.get('id', '')
                if pid:
                    self.places[pid] = p
            print(f"  -> places: {len(self.places)}")
        
        # Load combined dict
        dict_file = self.data_dir / 'indexed' / 'combined_dict.json'
        if dict_file.exists():
            with open(dict_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entries = data if isinstance(data, list) else data.get('entries', [])
            for e in entries:
                term = e.get('term', '')
                if term:
                    self.dicts[term] = e
            print(f"  -> dict entries: {len(self.dicts)}")
        
        return len(self.persons) + len(self.places) + len(self.dicts)
    
    def check_persons_integrity(self):
        """Check person data integrity"""
        print("[CHECK] Persons integrity...")
        
        issues = {
            'no_id': [],
            'no_names': [],
            'no_birth_year': [],
            'orphans': []
        }
        
        for pid, pdata in self.persons.items():
            # Check ID format
            if not pid.startswith('A') and not pid.startswith('P'):
                issues['no_id'].append(pid)
            
            # Check names
            names = pdata.get('names', [])
            if not names:
                issues['no_names'].append(pid)
            
            # Check birth year (optional but track)
            birth = pdata.get('birth_year', '')
            death = pdata.get('death_year', '')
            if not birth and not death:
                issues['no_birth_year'].append(pid)
        
        # Find orphans (not in any dict)
        orphan_count = 0
        for pid in self.persons:
            names = self.persons[pid].get('names', [])
            found = False
            for n in names:
                val = n.get('value', '')
                if val in self.dicts:
                    found = True
                    break
            if not found:
                orphan_count += 1
                issues['orphans'].append(pid)
        
        self.stats['persons'] = {
            'total': len(self.persons),
            'issues': {
                'no_id': len(issues['no_id']),
                'no_names': len(issues['no_names']),
                'no_dates': len(issues['no_birth_year']),
                'orphans': orphan_count
            }
        }
        
        print(f"  -> Issues found: {sum(self.stats['persons']['issues'].values())}")
        self.issues.append(('persons', issues))
        
        return issues
    
    def check_places_integrity(self):
        """Check place data integrity"""
        print("[CHECK] Places integrity...")
        
        issues = {
            'no_id': [],
            'no_gps': [],
            'no_names': []
        }
        
        for pid, pdata in self.places.items():
            # Check ID format
            if not pid.startswith('PL'):
                issues['no_id'].append(pid)
            
            # Check GPS
            lat = pdata.get('lat', 0)
            lon = pdata.get('lon', 0)
            if not lat or not lon:
                issues['no_gps'].append(pid)
            
            # Check names
            name = pdata.get('nameChinese', pdata.get('nameEnglish', ''))
            if not name:
                issues['no_names'].append(pid)
        
        self.stats['places'] = {
            'total': len(self.places),
            'issues': {
                'no_id': len(issues['no_id']),
                'no_gps': len(issues['no_gps']),
                'no_names': len(issues['no_names'])
            }
        }
        
        print(f"  -> Issues found: {sum(self.stats['places']['issues'].values())}")
        self.issues.append(('places', issues))
        
        return issues
    
    def check_dicts_integrity(self):
        """Check dictionary integrity"""
        print("[CHECK] Dictionary integrity...")
        
        issues = {
            'no_term': [],
            'no_definition': [],
            'no_source': []
        }
        
        for term, entry in self.dicts.items():
            if not term:
                issues['no_term'].append(term)
            
            if not entry.get('definition'):
                issues['no_definition'].append(term)
            
            if not entry.get('source'):
                issues['no_source'].append(term)
        
        self.stats['dicts'] = {
            'total': len(self.dicts),
            'issues': {
                'no_term': len(issues['no_term']),
                'no_definition': len(issues['no_definition']),
                'no_source': len(issues['no_source'])
            }
        }
        
        print(f"  -> Issues found: {sum(self.stats['dicts']['issues'].values())}")
        
        return issues
    
    def run(self) -> Dict:
        """Run complete QA"""
        print("=" * 60)
        print("FINAL QA AUDIT - Hybrid Graph System")
        print("=" * 60)
        
        total = self.load_all()
        
        self.check_persons_integrity()
        self.check_places_integrity()
        self.check_dicts_integrity()
        
        # Summary
        total_issues = sum(
            sum(s['issues'].values()) 
            for s in self.stats.values()
        )
        
        result = {
            'status': 'complete',
            'total_entries': total,
            'statistics': self.stats,
            'total_issues': total_issues,
            'health_score': round((total - total_issues) / total * 100, 2) if total > 0 else 0
        }
        
        print("=" * 60)
        print(f"[RESULT] Health Score: {result['health_score']}%")
        print(f"  Total entries: {total}")
        print(f"  Total issues: {total_issues}")
        print("=" * 60)
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Final QA Audit')
    parser.add_argument('--data', '-d', default='data', help='Data directory')
    parser.add_argument('--output', '-o', default='data/indexed', help='Output directory')
    args = parser.parse_args()
    
    auditor = FinalQAAuditor(args.data)
    result = auditor.run()
    
    # Save report
    output_file = Path(args.output) / 'QA_FINAL_REPORT.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# QA_FINAL_REPORT.md\n")
        f.write("**Generated:** 2026-04-14\n\n")
        f.write("## Statistics\n\n")
        f.write(f"- **Health Score:** {result['health_score']}%\n")
        f.write(f"- **Total Entries:** {result['total_entries']}\n")
        f.write(f"- **Total Issues:** {result['total_issues']}\n\n")
        
        for source, data in result['statistics'].items():
            f.write(f"### {source.capitalize()}\n\n")
            f.write(f"- Total: {data['total']}\n")
            f.write("- Issues:\n")
            for issue, count in data['issues'].items():
                f.write(f"  - {issue}: {count}\n")
            f.write("\n")
    
    print(f"\n[SAVED] {output_file}")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()