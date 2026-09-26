import urllib.request
import re

try:
    r = urllib.request.urlopen('http://localhost:8080/daoanh/places/PL000000023255', timeout=5)
    data = r.read().decode('utf-8', errors='replace')
    
    print('=== PLACES DETAIL FOR PL000000023255 ===')
    print()
    
    # Find bdrc block
    bdrc_match = re.search(r'<div id="bdrcBlock"[^>]*>(.*?)</div>', data, re.DOTALL)
    if bdrc_match:
        print('BDRC Block found!')
        content = bdrc_match.group(1)
        # Extract just the visible text content (remove HTML tags)
        text_only = re.sub(r'<[^>]+>', ' ', content)
        print(f'BDRC Content (first 500 chars): {text_only[:500]}')
    else:
        print('BDRC Block NOT found (element may be hidden)')
    
    # Find bdrcId field
    bdrc_id_match = re.search(r'BDRC: <span[^>]*>([^<]*)</span>', data)
    if bdrc_id_match:
        print(f'BDRC ID field: {bdrc_id_match.group(1)}')
    else:
        print('BDRC ID field not found in HTML')
        
    # Find chipBdrc
    chip_match = re.search(r'chipBdrc[^>]*>([^<]*)</span>', data)
    if chip_match:
        print(f'BDRC Chip: {chip_match.group(1)}')
    else:
        print('BDRC Chip not found')
    
    # Print first 1500 chars for context
    print('\n=== FIRST 1500 CHARS ===')
    print(data[:1500])
    
except Exception as e:
    print(f'Error: {e}')