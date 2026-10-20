#!/usr/bin/env python3
with open('home.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

idx = content.lower().index('search')
start = max(0, idx - 100)
end = min(len(content), idx + 100)
print("Context around 'search':")
print(content[start:end])