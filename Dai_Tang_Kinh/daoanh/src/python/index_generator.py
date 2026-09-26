#!/usr/bin/env python3
"""
Index Generator - Zero-RAM Indexing
Tạo .idx files từ JSON data cho Zero-RAM lookup

@version: v4.5 (2026-04-10)
@file: src/python/index_generator.py
"""

import json
import os
import struct
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Generator
import argparse


class IndexGenerator:
    """Tạo index files cho Zero-RAM lookup"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_idx_file(self, json_file: str, key_field: str = 'id') -> str:
        """
        Tạo .idx file từ JSON file
        
        Format .idx:
        - Header: magic number + version + entry_count
        - Index entries: key (string) -> byte_offset (int64)
        - Data section: JSON objects stored sequentially
        """
        json_path = self.data_dir / json_file
        idx_path = self.output_dir / f"{json_file.replace('.json', '')}.idx"
        
        print(f"[IndexGenerator] Processing: {json_path}")
        
        entries = []
        data_offset = 0
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('items', [data])
        else:
            raise ValueError(f"Unsupported data format in {json_file}")
        
        # Build index
        with open(idx_path, 'wb') as idx_file:
            # Write header
            magic = b'IDX\x00'
            version = 1
            entry_count = len(items)
            
            idx_file.write(magic)
            idx_file.write(struct.pack('<I', version))
            idx_file.write(struct.pack('<Q', entry_count))
            
            # Reserve space for index entries
            index_start = idx_file.tell()
            index_entries = []
            
            for item in items:
                key = item.get(key_field, '')
                if not key:
                    continue
                    
                # Store offset after header + index section
                entry_offset = idx_file.tell()
                index_entries.append((key, entry_offset))
                
                # Write data (JSON string)
                data_json = json.dumps(item, ensure_ascii=False)
                idx_file.write(data_json.encode('utf-8'))
                idx_file.write(b'\n')
            
            # Write index section
            for key, offset in index_entries:
                key_bytes = key.encode('utf-8')
                idx_file.write(struct.pack('<I', len(key_bytes)))
                idx_file.write(key_bytes)
                idx_file.write(struct.pack('<Q', offset))
        
        print(f"[IndexGenerator] Created: {idx_path} ({entry_count} entries)")
        return str(idx_path)
    
    def generate_trie_index(self, json_file: str, text_field: str = 'name') -> str:
        """
        Tạo Trie index cho autocomplete
        
        Returns: JSON file với trie structure
        """
        json_path = self.data_dir / json_file
        trie_path = self.output_dir / f"{json_file.replace('.json', '')}_trie.json"
        
        print(f"[IndexGenerator] Building trie: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('items', [data])
        else:
            raise ValueError(f"Unsupported data format")
        
        # Build trie
        trie = {}
        
        for item in items:
            text = item.get(text_field, '')
            if not text:
                continue
                
            # Normalize text (remove diacritics for search)
            normalized = self._remove_diacritics(text.lower())
            
            node = trie
            for char in normalized:
                if char not in node:
                    node[char] = {'_ids': []}
                node = node[char]
                node['_ids'].append(item.get('id', ''))
        
        # Save trie
        with open(trie_path, 'w', encoding='utf-8') as f:
            json.dump(trie, f, ensure_ascii=False)
        
        print(f"[IndexGenerator] Created: {trie_path}")
        return str(trie_path)
    
    def generate_search_index(self, json_file: str, search_fields: List[str]) -> str:
        """
        Tạo search index (key-value lookup)
        """
        json_path = self.data_dir / json_file
        idx_path = self.output_dir / f"{json_file.replace('.json', '')}_search.idx"
        
        print(f"[IndexGenerator] Building search index: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            items = data
        else:
            items = data.get('items', [data])
        
        index = {}
        
        for item in items:
            item_id = item.get('id', '')
            
            for field in search_fields:
                value = item.get(field, '')
                if not value:
                    continue
                
                # Add to index
                normalized = self._remove_diacritics(str(value).lower())
                index[normalized] = item_id
                
                # Add partial matches
                for i in range(1, len(normalized)):
                    partial = normalized[:i]
                    if partial not in index:
                        index[partial] = item_id
        
        # Save as simple key-value (one entry per line for fast lookup)
        with open(idx_path, 'w', encoding='utf-8') as f:
            for key, value in sorted(index.items()):
                f.write(f"{key}\t{value}\n")
        
        print(f"[IndexGenerator] Created: {idx_path}")
        return str(idx_path)
    
    def _remove_diacritics(self, text: str) -> str:
        """Remove Vietnamese diacritics"""
        VIETNAMESE_DIACRITICS = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd'
        }
        
        result = []
        for char in text:
            result.append(VIETNAMESE_DIACRITICS.get(char, char))
        return ''.join(result)


class ByteOffsetReader:
    """Reader cho .idx files (Zero-RAM)"""
    
    def __init__(self, idx_file: str):
        self.idx_file = idx_file
        self._load_header()
    
    def _load_header(self):
        with open(self.idx_file, 'rb') as f:
            magic = f.read(4)
            if magic != b'IDX\x00':
                raise ValueError("Invalid index file")
            
            self.version = struct.unpack('<I', f.read(4))[0]
            self.entry_count = struct.unpack('<Q', f.read(8))[0]
            self.index_start = f.tell()
    
    def lookup(self, key: str) -> Optional[dict]:
        """Lookup một key (Zero-RAM: chỉ đọc phần cần thiết)"""
        key_bytes = key.encode('utf-8')
        
        with open(self.idx_file, 'rb') as f:
            # Seek to index section
            f.seek(self.index_start)
            
            # Linear search (có thể tối ưu với binary search)
            for _ in range(self.entry_count):
                key_len = struct.unpack('<I', f.read(4))[0]
                stored_key = f.read(key_len)
                
                if stored_key == key_bytes:
                    offset = struct.unpack('<Q', f.read(8))[0]
                    f.seek(offset)
                    
                    # Read JSON object
                    data = f.readline().decode('utf-8')
                    return json.loads(data)
                
                # Skip offset
                f.seek(8, 1)
        
        return None


def main():
    parser = argparse.ArgumentParser(description='Index Generator for Zero-RAM lookup')
    parser.add_argument('--data-dir', default='../../data/processed', help='Input data directory')
    parser.add_argument('--output-dir', default='../../data/indexed', help='Output index directory')
    parser.add_argument('--files', nargs='+', help='JSON files to index')
    parser.add_argument('--trie', action='store_true', help='Generate trie index')
    parser.add_argument('--search', action='store_true', help='Generate search index')
    
    args = parser.parse_args()
    
    # Default files
    if not args.files:
        args.files = [
            'monk_names.json',
            'temples_master_gps.json',
            'search_index_critical.json'
        ]
    
    generator = IndexGenerator(args.data_dir, args.output_dir)
    
    for json_file in args.files:
        try:
            # Generate .idx file
            idx_file = generator.generate_idx_file(json_file, key_field='id')
            
            if args.trie:
                generator.generate_trie_index(json_file, text_field='name')
            
            if args.search:
                generator.generate_search_index(json_file, search_fields=['name', 'label'])
                
        except FileNotFoundError:
            print(f"[IndexGenerator] File not found: {json_file}")
        except Exception as e:
            print(f"[IndexGenerator] Error processing {json_file}: {e}")


if __name__ == '__main__':
    main()
