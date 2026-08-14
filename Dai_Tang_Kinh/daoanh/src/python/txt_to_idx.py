#!/usr/bin/env python3
"""
Txt Dictionary to .idx Index Generator
Parse plain text dictionaries and create .idx files for Zero-RAM lookup

@version: v1.0 (2026-04-14)
"""

import json
import os
import struct
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


class TxtDictionaryParser:
    """Parse txt dictionary files"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_txt_file(self, txt_path: Path) -> List[Dict]:
        """Parse a txt dictionary file"""
        entries = []
        source_name = txt_path.stem
        
        with open(txt_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        term = None
        definition_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                if term and definition_lines:
                    entries.append({
                        'term': term,
                        'definition': ' '.join(definition_lines).strip(),
                        'source': source_name
                    })
                term = None
                definition_lines = []
                i += 1
                continue
            
            line_clean = line
            if line_clean.startswith('﻿'):
                line_clean = line_clean[1:].strip()
            
            is_bullet_line = '\u25CF' in line_clean or '*' in line_clean
            
            if not is_bullet_line:
                if term and definition_lines:
                    entries.append({
                        'term': term,
                        'definition': ' '.join(definition_lines).strip(),
                        'source': source_name
                    })
                term = line_clean
                definition_lines = []
            else:
                if term:
                    parts = line_clean.split('\u25CF', 1) if '\u25CF' in line_clean else line_clean.split('*', 1)
                    def_part = parts[1].strip() if len(parts) > 1 else ''
                    definition_lines.append(def_part)
            
            i += 1
        
        if term and definition_lines:
            entries.append({
                'term': term,
                'definition': ' '.join(definition_lines).strip(),
                'source': source_name
            })
        
        return entries
    
    def convert_all(self) -> str:
        """Convert all txt files to combined JSON"""
        all_entries = []
        
        txt_files = list(self.input_dir.glob("*.txt"))
        print(f"[TxtDictionaryParser] Found {len(txt_files)} txt files")
        
        for txt_file in txt_files:
            print(f"[Processing] {txt_file.name}")
            entries = self.parse_txt_file(txt_file)
            print(f"  -> {len(entries)} entries extracted")
            all_entries.extend(entries)
        
        seen = set()
        unique_entries = []
        for e in all_entries:
            key = e['term'].lower()
            if key not in seen:
                seen.add(key)
                unique_entries.append(e)
        
        unique_entries.sort(key=lambda x: x['term'])
        
        output_json = self.output_dir / "combined_dict.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump({'entries': unique_entries}, f, ensure_ascii=False, indent=2)
        
        print(f"[DONE] Saved {len(unique_entries)} entries to {output_json}")
        return str(output_json)


class IdxGenerator:
    """Create .idx files for Zero-RAM lookup"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _stream_json_entries(self, json_path: Path):
        """Generator for streaming large JSON files"""
        try:
            import ijson
            for item in ijson.items(open(json_path, 'rb'), 'entries.item'):
                yield item
        except ImportError:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            data = json.loads(content)
            for item in data.get('entries', []):
                yield item
    
    def create_idx_file(self, json_file: str, key_field: str = 'term') -> str:
        """Create .idx file from JSON file"""
        json_path = self.data_dir / json_file
        idx_path = self.output_dir / f"{json_file.replace('.json', '')}.idx"
        dict_path = self.output_dir / f"{json_file.replace('.json', '')}.dict"
        
        print(f"[IdxGenerator] Creating index: {json_file}")
        
        file_size = json_path.stat().st_size
        print(f"  -> File size: {file_size / 1024 / 1024:.2f} MB")
        
        if file_size > 10 * 1024 * 1024:
            items = list(self._stream_json_entries(json_path))
        else:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            items = data.get('entries', [])
        
        print(f"  -> {len(items)} items to index")
        
        data_offsets = []
        
        with open(dict_path, 'w', encoding='utf-8') as dict_file:
            for item in items:
                key = item.get(key_field, '')
                if not key:
                    continue
                
                data_json = json.dumps(item, ensure_ascii=False)
                dict_file.write(data_json + '\n')
                
                offset = dict_file.tell() - len(data_json) - 1
                size = len(data_json)
                data_offsets.append((key, offset, size))
        
        data_offsets.sort(key=lambda x: x[0])
        
        with open(idx_path, 'wb') as idx_file:
            magic = b'IDX\x00'
            version = 1
            count = len(data_offsets)
            
            idx_file.write(magic)
            idx_file.write(struct.pack('<I', version))
            idx_file.write(struct.pack('<Q', count))
            
            for key, offset, size in data_offsets:
                key_bytes = key.encode('utf-8')
                key_len = len(key_bytes)
                
                idx_file.write(struct.pack('<I', key_len))
                idx_file.write(key_bytes)
                idx_file.write(struct.pack('<Q', offset))
                idx_file.write(struct.pack('<I', size))
        
        print(f"  -> Created {idx_path} ({idx_path.stat().st_size} bytes)")
        print(f"  -> Created {dict_path} ({dict_path.stat().st_size} bytes)")
        
        return str(idx_path)


def main():
    parser = argparse.ArgumentParser(description='Txt Dict to .idx Generator')
    parser.add_argument('--input', '-i', default='data/dictionaries', help='Input directory')
    parser.add_argument('--output', '-o', default='data/indexed', help='Output directory')
    args = parser.parse_args()
    
    parser = TxtDictionaryParser(args.input, args.output)
    json_path = parser.convert_all()
    
    index_gen = IdxGenerator(args.output, args.output)
    json_name = Path(json_path).name
    index_gen.create_idx_file(json_name, 'term')
    
    print("\n[SUCCESS] Dictionary index created!")


if __name__ == '__main__':
    main()