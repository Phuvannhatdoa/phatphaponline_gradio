#!/usr/bin/env python3
import os, sys
os.chdir(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh')
sys.path.insert(0, 'scripts')
from t457_extract_bio_nexus import extract_file

src = r'data\dila_import\biographies.2024-01\biographies-master'
out = r'data\dila_import\biographies.2024-01\nexus_src_test'
os.makedirs(out, exist_ok=True)

book = 'Mingsengzhuanchao'
xml_files = sorted(__import__('glob').glob(os.path.join(src, book, '*.xml')))
print(f"Processing {len(xml_files)} files for {book}")

all_rows = []
total_problems = 0
for f in xml_files:
    rows, problems = extract_file(f, book)
    all_rows += rows
    total_problems += len(problems)
    print(f"  {os.path.basename(f)}: {len(rows)} nexus, {len(problems)} problems")

print(f"Total: {len(all_rows)} nexus, {total_problems} problems")

# Write output
from t457_extract_bio_nexus import write_book
out_path = os.path.join(out, f'{book}.nexus.xml')
write_book(book, all_rows, out, commit='4e82453')
print(f"Written to {out_path}")