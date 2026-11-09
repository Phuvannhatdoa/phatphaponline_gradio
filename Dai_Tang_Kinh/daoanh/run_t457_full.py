#!/usr/bin/env python3
import sys, os, re, glob, json
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, 'scripts')
from t457_extract_bio_nexus import extract_file, write_book, split_parts, jd_to_year

src = r'data\dila_import\biographies.2024-01\biographies-master'
out = r'data\dila_import\biographies.2024-01\nexus_src_new'
os.makedirs(out, exist_ok=True)

books = sorted(d for d in os.listdir(src) 
               if os.path.isdir(os.path.join(src, d)) 
               and d not in {'bin', 'Schema'})

print(f"Found {len(books)} books")
total_nexus = 0

for book in books:
    xml_files = sorted(glob.glob(os.path.join(src, book, '*.xml')))
    print(f"  {book}: {len(xml_files)} XML files")
    all_rows = []
    for f in xml_files:
        rows, problems = extract_file(f, book)
        all_rows += rows
    print(f"    Extracted {len(all_rows)} nexus, {len(problems)} problems")
    
    # Write as single book file
    part_size = 0  # no splitting for now
    if part_size and len(all_rows) > part_size:
        parts = split_parts(all_rows, part_size)
        for k, part in enumerate(parts, 1):
            out_path = os.path.join(out, f'{book}.part{k:02d}.nexus.xml')
            write_book(book, part, out, commit='4e82453', name=f'{book}.part{k:02d}')
    else:
        out_path = os.path.join(out, f'{book}.nexus.xml')
        write_book(book, all_rows, out, commit='4e82453')
    
    total_nexus += len(all_rows)
    print(f"    Written to: {out_path}")

print(f"\nTOTAL nexus: {total_nexus}")