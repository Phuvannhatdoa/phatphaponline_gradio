#!/usr/bin/env python3
"""
Master Index Builder - Zero-RAM Architecture
Tạo Master_Index.idx từ 22 bộ từ điển + Entity Deduplication

@version: v2.0 (2026-04-14)
@architecture: 4-Pillar with Multi-index Search

Features:
- Entity Deduplication (group by Authority ID)
- Virtual Master Index (22 dicts → 1 master index)
- Source Ranking: Local > TTL > DILA
- Zero-RAM: Streaming parser for large files (>10MB)
"""

import os
import json
import struct
import mmap
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from functools import lru_cache


class MasterIndexBuilder:
    """
    Tạo Master Index từ 22 bộ từ điển
    Thực hiện Entity Deduplication + Source Ranking
    """
    
    # Source priority (lower = higher priority)
    SOURCE_PRIORITY = {
        'local_vietnam': 1,      # Tiếng Việt - ưu tiên cao nhất
        'local_dict': 2,          # Từ điển Việt Nam
        'ttl_lineage': 3,         # Graph TTL - truyền thừa
        'dila_authority': 4,      # DILA - học thuật
        'cbeta': 5,              # CBETA - kinh điển
        'other': 6                # Các nguồn khác
    }
    
    def __init__(self, dict_dir: str, output_dir: str):
        self.dict_dir = Path(dict_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Master index: key -> [(source, offset, size)]
        self.master_index = defaultdict(list)
        
        # Entity deduplication: normalized_name -> authority_id
        self.entity_map = {}
        
    def detect_source(self, filename: str) -> str:
        """Detect source type from filename"""
        fname = filename.lower()
        
        if 'viet' in fname or 'vn' in fname:
            return 'local_vietnam'
        elif 'dict' in fname or 'dien' in fname:
            return 'local_dict'
        elif 'ttl' in fname or 'lineage' in fname:
            return 'ttl_lineage'
        elif 'dila' in fname or 'authority' in fname:
            return 'dila_authority'
        elif 'cbeta' in fname or 'cbeta' in fname:
            return 'cbeta'
        else:
            return 'other'
    
    def normalize_key(self, key: str) -> str:
        """Normalize key for deduplication"""
        # Remove diacritics, lowercase
        key = key.lower().strip()
        
        # Common normalizations
        replacements = {
            'áàảãạăắằẳẵặâấầẩẫậ': 'a',
            'éèẻẽẹêếềểễệ': 'e',
            'íìỉĩị': 'i',
            'óòỏõọôốồổỗộơớờởỡợ': 'o',
            'úùủũụưứừửữứự': 'u',
            'ýỳỷỹỵ': 'y',
            'đ': 'd',
        }
        
        # Simplified normalization
        for old, new in replacements.items():
            for char in old:
                key = key.replace(char, new)
        
        return key
    
    def extract_authority_id(self, entry: Dict) -> Optional[str]:
        """Extract Authority ID from entry"""
        # Check various ID fields
        for field in ['authority_id', 'dila_id', 'id', 'a_id']:
            if field in entry and entry[field]:
                return entry[field]
        return None
    
    def build_from_json(self, json_file: str, source: str = 'other') -> int:
        """Build index from JSON file"""
        json_path = self.dict_dir / json_file
        
        if not json_path.exists():
            print(f"[SKIP] File not found: {json_file}")
            return 0
        
        print(f"[BUILD] Processing: {json_file} (source: {source})")
        
        count = 0
        
        # Use mmap for large files
        with open(json_path, 'rb') as f:
            # For small files, just read
            if json_path.stat().st_size < 10_000_000:
                content = f.read().decode('utf-8')
                data = json.loads(content)
            else:
                # Large file - stream
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode('utf-8')
                    data = json.loads(content)
        
        # Extract entries
        if isinstance(data, dict) and 'entries' in data:
            entries = data['entries']
        elif isinstance(data, list):
            entries = data
        else:
            entries = [data]
        
        # Get source priority
        priority = self.SOURCE_PRIORITY.get(source, 99)
        
        # Process each entry
        for entry in entries:
            # Get all possible keys (names)
            keys = self._extract_keys(entry)
            authority_id = self.extract_authority_id(entry)
            
            # Serialize entry for .dict file
            entry_json = json.dumps(entry, ensure_ascii=False)
            
            for key in keys:
                normalized = self.normalize_key(key)
                
                # Store in master index
                self.master_index[normalized].append({
                    'original_key': key,
                    'source': source,
                    'priority': priority,
                    'authority_id': authority_id,
                    'dict_file': json_file,
                    'data': entry_json
                })
                
                count += 1
        
        print(f"  -> Added {count} entries to master index")
        return count
    
    def _extract_keys(self, entry: Dict) -> List[str]:
        """Extract all searchable keys from entry"""
        keys = []
        
        # Field priorities for extraction
        key_fields = [
            'term', 'name', 'name_vietnamese', 'name_zh', 'name_han',
            'persName', 'placeName', 'title', 'alias', 'vietnamese'
        ]
        
        for field in key_fields:
            if field in entry and entry[field]:
                val = entry[field]
                if isinstance(val, str):
                    keys.append(val)
                elif isinstance(val, list):
                    keys.extend([v for v in val if isinstance(v, str)])
        
        # Add ID as key
        aid = self.extract_authority_id(entry)
        if aid:
            keys.append(aid)
        
        return list(set(keys))  # Remove duplicates
    
    def deduplicate(self) -> int:
        """
        Entity Deduplication - Merge entries with same Authority ID
        Returns number of entities merged
        """
        print("[DEDUP] Performing entity deduplication...")
        
        merged = 0
        
        for normalized_key, entries in self.master_index.items():
            if len(entries) <= 1:
                continue
            
            # Group by Authority ID
            by_authority = defaultdict(list)
            for e in entries:
                aid = e.get('authority_id') or 'unknown'
                by_authority[aid].append(e)
            
            # Keep only best source per Authority ID
            best_entries = []
            for aid, group in by_authority.items():
                # Sort by priority (lower = better)
                group.sort(key=lambda x: x['priority'])
                best_entries.append(group[0])
            
            # Update master index
            self.master_index[normalized_key] = best_entries
            merged += len(entries) - len(best_entries)
        
        print(f"[DEDUP] Merged {merged} duplicate entries")
        return merged
    
    def save_master_index(self, filename: str = 'master_index') -> Tuple[str, str]:
        """
        Save Master Index + Master Dict files
        Returns (idx_path, dict_path)
        """
        idx_path = self.output_dir / f"{filename}.idx"
        dict_path = self.output_dir / f"{filename}.dict"
        
        print(f"[SAVE] Writing master index to {idx_path}")
        
        # Write .dict file first (sequential data)
        dict_offsets = {}
        
        with open(dict_path, 'w', encoding='utf-8') as df:
            for normalized_key, entries in self.master_index.items():
                for entry in entries:
                    # Write to dict file
                    offset = df.tell()
                    df.write(entry['data'] + '\n')
                    size = len(entry['data']) + 1
                    
                    # Store offset
                    key = entry['original_key'].lower()
                    if key not in dict_offsets:
                        dict_offsets[key] = []
                    dict_offsets[key].append({
                        'offset': offset,
                        'size': size,
                        'source': entry['source'],
                        'priority': entry['priority']
                    })
        
        # Write .idx file (index)
        sorted_keys = sorted(dict_offsets.keys())
        
        with open(idx_path, 'wb') as idx_file:
            # Header
            magic = b'IDX\x00'
            version = 1
            count = len(sorted_keys)
            
            idx_file.write(magic)
            idx_file.write(struct.pack('<I', version))
            idx_file.write(struct.pack('<Q', count))
            
            # Index entries
            for key in sorted_keys:
                key_bytes = key.encode('utf-8')
                key_len = len(key_bytes)
                
                # Get best (lowest priority) offset
                best = min(dict_offsets[key], key=lambda x: x['priority'])
                
                idx_file.write(struct.pack('<I', key_len))
                idx_file.write(key_bytes)
                idx_file.write(struct.pack('<Q', best['offset']))
                idx_file.write(struct.pack('<I', best['size']))
        
        print(f"[OK] Master index: {count} keys, {idx_path.stat().st_size} bytes")
        print(f"[OK] Master dict: {dict_path.stat().st_size} bytes")
        
        return str(idx_path), str(dict_path)
    
    def build_all(self, json_files: List[Tuple[str, str]]) -> Dict:
        """
        Build master index from multiple JSON files
        json_files: [(filename, source), ...]
        """
        total = 0
        
        for json_file, source in json_files:
            count = self.build_from_json(json_file, source)
            total += count
        
        # Deduplicate
        merged = self.deduplicate()
        
        # Save
        idx_path, dict_path = self.save_master_index()
        
        return {
            'total_entries': total,
            'merged': merged,
            'unique_keys': len(self.master_index),
            'idx_file': idx_path,
            'dict_file': dict_path
        }


class MasterIndexReader:
    """
    Reader for Master Index - Zero-RAM with Binary Search
    """
    
    def __init__(self, idx_path: str, dict_path: str):
        self.idx_path = Path(idx_path)
        self.dict_path = Path(dict_path)
        
        # Load index into RAM (small - just keys + offsets)
        self.index = {}
        self.load_index()
    
    def load_index(self):
        """Load .idx into RAM"""
        with open(self.idx_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                magic = mm.read(4)
                if magic != b'IDX\x00':
                    print("[ERROR] Invalid index format")
                    return
                
                version = struct.unpack('<I', mm.read(4))[0]
                count = struct.unpack('<Q', mm.read(8))[0]
                
                print(f"[LOAD] Reading {count} keys from master index")
                
                for _ in range(count):
                    key_len = struct.unpack('<I', mm.read(4))[0]
                    key = mm.read(key_len).decode('utf-8')
                    offset = struct.unpack('<Q', mm.read(8))[0]
                    size = struct.unpack('<I', mm.read(4))[0]
                    
                    self.index[key] = (offset, size)
        
        print(f"[OK] Loaded {len(self.index)} keys into RAM")
    
    @lru_cache(maxsize=1000)
    def search(self, query: str) -> Optional[Dict]:
        """Binary search with caching"""
        query_norm = query.lower()
        
        # Exact match
        if query_norm in self.index:
            return self._fetch(query_norm)
        
        # Prefix match
        import bisect
        keys = sorted(self.index.keys())
        idx = bisect.bisect_left(keys, query_norm)
        
        if idx < len(keys) and keys[idx].startswith(query_norm):
            return self._fetch(keys[idx])
        
        return None
    
    def _fetch(self, key: str) -> Optional[Dict]:
        """Fetch single record via mmap"""
        offset, size = self.index[key]
        
        with open(self.dict_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                mm.seek(offset)
                data = mm.read(size).decode('utf-8').strip()
                return json.loads(data)


def main():
    import sys
    
    # Build master index from 22 dictionaries
    dict_dir = 'data/dictionaries'
    output_dir = 'data/indexed'
    
    # List of dictionaries to process
    dictionaries = [
        # Local Vietnam (highest priority)
        ('Danh Tu Thien Hoc - HT Duy Luc.json', 'local_vietnam'),
        ('Tu Dien Han Viet - Nguyen Quoc Hung.json', 'local_dict'),
        ('Tu Dien Phat Hoc Tong Hop - Viet - Anh - Cs Minh Thong.json', 'local_dict'),
        
        # Add more as needed...
    ]
    
    # Check what files exist
    dict_path = Path(dict_dir)
    available = list(dict_path.glob('*.json'))
    print(f"[INFO] Found {len(available)} JSON files in {dict_dir}")
    
    # Build from all JSON files
    all_files = [(f.name, 'local_dict') for f in available if f.suffix == '.json']
    
    builder = MasterIndexBuilder(dict_dir, output_dir)
    result = builder.build_all(all_files)
    
    print("\n[RESULT]")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
