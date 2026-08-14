#!/usr/bin/env python3
"""
Relationship Extractor - ETL Pipeline
Extract teacher-student relationships from entity data

@version: v4.11 (2026-04-10)
@file: src/python/etl/relation_extractor.py
"""

import json
import re
import argparse
from pathlib import Path
from typing import Generator, List, Dict, Optional, Set, Tuple
from collections import defaultdict


class RelationshipExtractor:
    """Extract teacher-student relationships from data"""
    
    # Relationship keywords
    RELATION_PATTERNS = {
        'teacher': [
            r'đệ tử của', r'học trò của', r'thụ huấn', r'thụ giáo',
            r'sự sinh', r'sinh sự', r'truyền truyền', r'kế thừa',
            r'dược truyền', r'truyền pháp', r'truyền tâm',
            r'is student of', r'student of', r'disciple of',
            r'teacher', r'spiritual teacher'
        ],
        'student': [
            r'đệ tử', r'học trò', r'truyền nhân', r'truyền duyên',
            r'thừa tự', r'thừa kế', r'truyền thừa',
            r'is teacher of', r'teacher of', r'master of'
        ]
    }
    
    # Lineage patterns
    LINEAGE_KEYWORDS = [
        'dòng', 'phái', 'tông', 'lam tế', 'lâm tế', 'vân môn',
        'thiền tông', 'trúc lâm', 'yên tử', 'quỳnh lâm',
        'thượng sơn', 'nam hoa', 'cảnh sắc', 'tào khê'
    ]
    
    def __init__(self):
        self.stats = {
            'persons_processed': 0,
            'relations_found': 0,
            'lineage_relations': 0,
            'teacher_student_relations': 0,
            'ambiguous': 0
        }
        
        # Cache for person lookups
        self.person_cache = {}
        self.relation_graph = defaultdict(list)
    
    def extract_from_jsonl(self, jsonl_file: str) -> List[Dict]:
        """Extract relationships from JSONL file"""
        relations = []
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    
                    if record.get('type') == 'person':
                        rels = self.extract_from_person(record)
                        relations.extend(rels)
                        
                        self.stats['persons_processed'] += 1
                        
                except json.JSONDecodeError:
                    continue
        
        print(f"[RelationExtractor] Found {len(relations)} relations")
        return relations
    
    def extract_from_person(self, person: dict) -> List[Dict]:
        """Extract relationships from a person record"""
        relations = []
        
        person_id = person.get('id', '')
        person_name = self._get_primary_name(person)
        
        # Skip if no valid ID
        if not person_id:
            return relations
        
        self.person_cache[person_id] = person
        
        # Method 1: Explicit relations in record
        explicit_rels = person.get('relations', [])
        for rel in explicit_rels:
            rel_type = rel.get('type', '')
            ref = rel.get('ref', '') or rel.get('active', '') or rel.get('passive', '')
            
            if rel_type in ['teacher', 'student', 'teacherStudent'] and ref:
                relations.append({
                    'subject': person_id,
                    'subject_name': person_name,
                    'predicate': ':teacher' if rel_type == 'teacher' else ':student',
                    'object': ref,
                    'confidence': 1.0,
                    'source': 'explicit'
                })
                self.stats['teacher_student_relations'] += 1
        
        # Method 2: Extract from text descriptions
        text = person.get('text', '') or person.get('description', '')
        if text:
            text_rels = self._extract_from_text(text, person_id, person_name)
            relations.extend(text_rels)
        
        # Method 3: Extract from biography text
        bio = person.get('biography', '')
        if bio:
            bio_rels = self._extract_from_text(bio, person_id, person_name)
            relations.extend(bio_rels)
        
        # Method 4: Lineage extraction
        lineage = person.get('lineage', '')
        if lineage:
            relations.append({
                'subject': person_id,
                'subject_name': person_name,
                'predicate': ':lineage',
                'object': lineage,
                'confidence': 0.9,
                'source': 'lineage_field'
            })
            self.stats['lineage_relations'] += 1
        
        return relations
    
    def _extract_from_text(self, text: str, subject_id: str, subject_name: str) -> List[Dict]:
        """Extract relationships from text using patterns"""
        relations = []
        
        # Try to find teacher references
        for pattern in self.RELATION_PATTERNS['teacher']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Get context (surrounding text)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # Try to extract name from context
                names = self._extract_names_from_context(context)
                
                for name in names:
                    if name != subject_name:  # Don't link to self
                        relations.append({
                            'subject': subject_id,
                            'subject_name': subject_name,
                            'predicate': ':teacher',
                            'object': name,
                            'confidence': 0.7,
                            'source': 'text_pattern',
                            'context': context
                        })
                        self.stats['teacher_student_relations'] += 1
        
        return relations
    
    def _extract_names_from_context(self, context: str) -> List[str]:
        """Extract person names from context"""
        names = []
        
        # Pattern for Vietnamese names (2-4 words, capitalized)
        # This is a simple heuristic
        words = context.split()
        
        # Try consecutive capitalized words
        current_name = []
        for word in words:
            if word[0].isupper() and len(word) > 1:
                current_name.append(word)
                if len(current_name) >= 2:
                    names.append(' '.join(current_name))
            else:
                if current_name and len(current_name) >= 2:
                    names.append(' '.join(current_name))
                current_name = []
        
        return names
    
    def _get_primary_name(self, person: dict) -> str:
        """Get primary name from person record"""
        names = person.get('names', [])
        
        if names:
            # Prefer Vietnamese name
            for name in names:
                if name.get('lang') == 'vi':
                    return name.get('full', '')
            
            return names[0].get('full', '')
        
        return person.get('label', '') or person.get('id', '')
    
    def resolve_relations(self, relations: List[Dict]) -> List[Dict]:
        """Resolve relation objects to IDs"""
        resolved = []
        
        for rel in relations:
            obj = rel.get('object', '')
            
            # Skip if already an ID
            if obj.startswith('dila:') or obj.startswith('pth:') or obj.startswith('A'):
                resolved.append(rel)
                continue
            
            # Try to find matching person in cache
            matched_id = self._find_person_by_name(obj)
            
            if matched_id:
                rel['object'] = matched_id
                rel['object_resolved'] = True
            else:
                rel['object_resolved'] = False
            
            resolved.append(rel)
        
        return resolved
    
    def _find_person_by_name(self, name: str) -> Optional[str]:
        """Find person ID by name in cache"""
        name_lower = name.lower()
        
        for person_id, person in self.person_cache.items():
            person_name = self._get_primary_name(person).lower()
            
            if name_lower in person_name or person_name in name_lower:
                return person_id
        
        return None
    
    def build_lineage_tree(self, relations: List[Dict]) -> Dict:
        """Build a lineage tree from relations"""
        tree = {
            'teachers': defaultdict(list),  # person -> [teachers]
            'students': defaultdict(list),  # person -> [students]
            'lineages': defaultdict(list)   # person -> [lineages]
        }
        
        for rel in relations:
            subject = rel.get('subject')
            predicate = rel.get('predicate')
            obj = rel.get('object')
            
            if predicate == ':teacher':
                tree['teachers'][obj].append(subject)
                tree['students'][subject].append(obj)
            elif predicate == ':lineage':
                tree['lineages'][subject].append(obj)
        
        return tree
    
    def find_ancestors(self, person_id: str, tree: Dict, max_depth: int = 10) -> List[str]:
        """Find all ancestors (teachers) of a person"""
        ancestors = []
        visited = set()
        queue = [(person_id, 0)]
        
        while queue:
            current, depth = queue.pop(0)
            
            if current in visited or depth > max_depth:
                continue
            
            visited.add(current)
            
            teachers = tree['teachers'].get(current, [])
            for teacher in teachers:
                if teacher not in visited:
                    ancestors.append(teacher)
                    queue.append((teacher, depth + 1))
        
        return ancestors
    
    def find_descendants(self, person_id: str, tree: Dict, max_depth: int = 10) -> List[str]:
        """Find all descendants (students) of a person"""
        descendants = []
        visited = set()
        queue = [(person_id, 0)]
        
        while queue:
            current, depth = queue.pop(0)
            
            if current in visited or depth > max_depth:
                continue
            
            visited.add(current)
            
            students = tree['students'].get(current, [])
            for student in students:
                if student not in visited:
                    descendants.append(student)
                    queue.append((student, depth + 1))
        
        return descendants
    
    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return self.stats.copy()
    
    def save_relations(self, relations: List[Dict], output_file: str):
        """Save relations to JSONL file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for rel in relations:
                f.write(json.dumps(rel, ensure_ascii=False) + '\n')
        
        print(f"[RelationExtractor] Saved {len(relations)} relations to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Relationship Extractor')
    parser.add_argument('--input', required=True, help='Input JSONL file')
    parser.add_argument('--output', help='Output relations file (JSONL)')
    parser.add_argument('--resolve', action='store_true', help='Resolve relation objects to IDs')
    
    args = parser.parse_args()
    
    extractor = RelationshipExtractor()
    
    # Extract relations
    relations = extractor.extract_from_jsonl(args.input)
    print(f"[RelationExtractor] Found {len(relations)} raw relations")
    
    # Resolve if requested
    if args.resolve:
        relations = extractor.resolve_relations(relations)
        print(f"[RelationExtractor] Resolved relations")
    
    # Save if output specified
    if args.output:
        extractor.save_relations(relations, args.output)
    
    # Build tree
    tree = extractor.build_lineage_tree(relations)
    print(f"[RelationExtractor] Teachers: {len(tree['teachers'])}")
    print(f"[RelationExtractor] Students: {len(tree['students'])}")
    print(f"[RelationExtractor] Lineages: {len(tree['lineages'])}")
    
    # Stats
    stats = extractor.get_stats()
    print(f"\n[RelationExtractor] === Statistics ===")
    print(f"Persons processed: {stats['persons_processed']}")
    print(f"Relations found: {len(relations)}")
    print(f"Teacher-student: {stats['teacher_student_relations']}")
    print(f"Lineage: {stats['lineage_relations']}")


if __name__ == '__main__':
    main()
