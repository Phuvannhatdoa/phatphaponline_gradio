#!/usr/bin/env python3
import json, os

lines_file = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging\t457_dila_bio_nexus.jsonl'
lines = open(lines_file, encoding='utf-8').readlines()
print(f'Total lines: {len(lines)}')

# Check a few records
for i in [0, 100, 1000, 21739]:
    rec = json.loads(lines[i])
    nid = rec['nexus_id']
    bk = rec['book']
    tzh = rec['text_zh']
    yf = rec['year_from']
    st = rec['status']
    print(f'Record {i}: nexus_id={nid}, book={bk}, text_zh_len={len(tzh) if tzh else 0}, year_from={yf}, status={st}')

# Check for duplicates
ids = [json.loads(l)['nexus_id'] for l in lines]
print(f'Unique IDs: {len(set(ids))} out of {len(ids)}')

# Check empty text_zh
empty = sum(1 for l in lines if not json.loads(l)['text_zh'])
print(f'Empty text_zh: {empty}/{len(lines)}')

# Check all required keys
required = ['book', 'source_file', 'nexus_id', 'seq', 'from_anchor', 'to_anchor', 'text_zh', 'person_id', 'place_id', 'jd_from', 'jd_to', 'year_from', 'year_to', 'provenance', 'status']
for i in range(min(3, len(lines))):
    rec = json.loads(lines[i])
    missing = [k for k in required if k not in rec]
    if missing:
        print(f'Record {i} missing keys: {missing}')
    else:
        print(f'Record {i}: all {len(required)} keys present')

# Verify JSONL is valid (all lines parse)
valid = 0
for l in lines:
    try:
        json.loads(l)
        valid += 1
    except:
        pass
print(f'Valid JSONL lines: {valid}/{len(lines)}')

print('\nAll checks complete.')