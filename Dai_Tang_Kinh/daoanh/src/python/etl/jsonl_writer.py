#!/usr/bin/env python3
"""
JSONL Writer - ETL Pipeline
Stream extracted data to JSONL format

@version: v4.8 (2026-04-10)
@file: src/python/etl/jsonl_writer.py
"""

import json
import os
import argparse
from pathlib import Path
from typing import Generator, List, Dict, Optional
from datetime import datetime


class JSONLWriter:
    """Write data to JSONL format (one JSON object per line)"""
    
    def __init__(self, output_file: str, mode: str = 'write'):
        self.output_file = Path(output_file)
        self.mode = mode
        self.count = 0
        self.errors = 0
        
        # Open file in appropriate mode
        self._file = open(self.output_file, 'w' if mode == 'write' else 'a', encoding='utf-8')
        
    def write(self, data: dict) -> bool:
        """Write a single record to JSONL"""
        try:
            line = json.dumps(data, ensure_ascii=False)
            self._file.write(line + '\n')
            self.count += 1
            return True
        except Exception as e:
            self.errors += 1
            print(f"[JSONLWriter] Error writing record: {e}")
            return False
    
    def write_batch(self, data_list: List[dict]) -> int:
        """Write multiple records"""
        success = 0
        for data in data_list:
            if self.write(data):
                success += 1
        return success
    
    def write_generator(self, generator: Generator[dict, None, None], batch_size: int = 1000) -> int:
        """Write from a generator (memory efficient)"""
        batch = []
        total = 0
        
        for item in generator:
            batch.append(item)
            
            if len(batch) >= batch_size:
                total += self.write_batch(batch)
                batch = []
                
                # Progress indicator
                if total % 5000 == 0:
                    print(f"[JSONLWriter] Written {total} records...")
        
        # Write remaining
        if batch:
            total += self.write_batch(batch)
        
        return total
    
    def close(self):
        """Close the file handle"""
        if hasattr(self, '_file') and self._file:
            self._file.close()
    
    def get_stats(self) -> dict:
        """Get writer statistics"""
        return {
            'records_written': self.count,
            'errors': self.errors,
            'output_file': str(self.output_file)
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class JSONLReader:
    """Read JSONL files efficiently (streaming)"""
    
    def __init__(self, jsonl_file: str):
        self.jsonl_file = Path(jsonl_file)
        
    def read(self, limit: Optional[int] = None) -> List[dict]:
        """Read all records (or limit)"""
        records = []
        
        with open(self.jsonl_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                    
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"[JSONLReader] Error at line {i}: {e}")
        
        return records
    
    def stream(self, limit: Optional[int] = None) -> Generator[dict, None, None]:
        """Stream records one by one (memory efficient)"""
        with open(self.jsonl_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                    
                try:
                    yield json.loads(line.strip())
                except json.JSONDecodeError as e:
                    print(f"[JSONLReader] Error at line {i}: {e}")
    
    def filter(self, predicate) -> Generator[dict, None, None]:
        """Filter records by predicate function"""
        for record in self.stream():
            if predicate(record):
                yield record
    
    def count(self) -> int:
        """Count records without loading all into memory"""
        count = 0
        with open(self.jsonl_file, 'r', encoding='utf-8') as f:
            for _ in f:
                count += 1
        return count


def convert_json_to_jsonl(json_file: str, output_file: str, id_field: str = 'id') -> int:
    """Convert JSON array to JSONL format - Zero-RAM optimized"""
    
    print(f"[JSONLWriter] Converting {json_file} to JSONL...")
    
    # Check file size first
    file_size = os.path.getsize(json_file)
    print(f"[JSONLWriter] File size: {file_size / 1024 / 1024:.2f} MB")
    
    writer = JSONLWriter(output_file)
    count = 0
    
    # For large files (>10MB), use streaming with ijson
    if file_size > 10 * 1024 * 1024:
        print("[JSONLWriter] Large file detected - using streaming mode (ijson)")
        try:
            import ijson
            
            with open(json_file, 'rb') as f:
                # Stream parse JSON array
                for item in ijson.items(f, 'item'):
                    writer.write(item)
                    count += 1
                    if count % 5000 == 0:
                        print(f"[JSONLWriter] Processed {count} records...")
                        
        except ImportError:
            print("[JSONLWriter] ijson not installed - falling back to chunked load")
            count = _convert_json_chunked(json_file, output_file, id_field)
    else:
        # Smaller file: OK to load directly but process in chunks
        count = _convert_json_chunked(json_file, output_file, id_field)
    
    writer.close()
    print(f"[JSONLWriter] Converted {count} records to {output_file}")
    
    return count


def _convert_json_chunked(json_file: str, output_file: str, id_field: str = 'id') -> int:
    """Convert JSON with chunked processing - Zero-RAM pattern"""
    
    writer = JSONLWriter(output_file)
    count = 0
    CHUNK_SIZE = 5000
    
    with open(json_file, 'r', encoding='utf-8') as f:
        # Load and process in chunks to avoid memory issues
        data = json.load(f)
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('items', data.get('data', []))
        else:
            raise ValueError(f"Unsupported JSON format in {json_file}")
        
        # Process in chunks
        for i in range(0, len(items), CHUNK_SIZE):
            chunk = items[i:i + CHUNK_SIZE]
            for item in chunk:
                writer.write(item)
                count += 1
            
            # Clear reference to help garbage collection
            if i + CHUNK_SIZE < len(items):
                print(f"[JSONLWriter] Processed {count}/{len(items)} records...")
    
    return count


def merge_jsonl_files(input_files: List[str], output_file: str) -> int:
    """Merge multiple JSONL files into one"""
    
    writer = JSONLWriter(output_file)
    total = 0
    
    for input_file in input_files:
        reader = JSONLReader(input_file)
        
        for record in reader.stream():
            writer.write(record)
            total += 1
    
    writer.close()
    print(f"[JSONLWriter] Merged {total} records to {output_file}")
    
    return total


def main():
    parser = argparse.ArgumentParser(description='JSONL Writer/Converter')
    parser.add_argument('--mode', choices=['write', 'append'], default='write', help='Write mode')
    parser.add_argument('--output', required=True, help='Output JSONL file')
    parser.add_argument('--input', help='Input JSON file (for conversion)')
    parser.add_argument('--id-field', default='id', help='ID field for JSON objects')
    parser.add_argument('--merge', nargs='+', help='Input JSONL files to merge')
    
    args = parser.parse_args()
    
    if args.input:
        # Convert JSON to JSONL
        count = convert_json_to_jsonl(args.input, args.output, args.id_field)
        print(f"[JSONLWriter] Done: {count} records")
        
    elif args.merge:
        # Merge multiple JSONL files
        count = merge_jsonl_files(args.merge, args.output)
        print(f"[JSONLWriter] Done: {count} records")
        
    else:
        # Interactive mode
        writer = JSONLWriter(args.output, args.mode)
        
        print(f"[JSONLWriter] Ready. Write data with writer.write({{'key': 'value'}})")
        print("Example: writer.write({'name': 'Test', 'value': 123})")
        
        # Demo
        writer.write({
            'type': 'demo',
            'timestamp': datetime.now().isoformat(),
            'message': 'JSONL Writer initialized'
        })
        
        stats = writer.get_stats()
        print(f"[JSONLWriter] Stats: {stats}")
        
        writer.close()


if __name__ == '__main__':
    main()
