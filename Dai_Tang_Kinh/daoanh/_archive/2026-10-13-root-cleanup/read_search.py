#!/usr/bin/env python3
with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

idx = content.find('api_places_search')
if idx >= 0:
    # Print the function definition and body
    print(content[idx:idx+3000])
else:
    print('api_places_search not found')
PYEOF