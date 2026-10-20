#!/usr/bin/env python3
"""Fix broken inline CSS in places.html by removing the broken <style> block."""
import re

filepath = 'places.html'

with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find <style>...</style> block
start = content.find('<style>')
end = content.find('</style>') + len('</style>')

if start >= 0 and end > start:
    # Replace the entire <style>...</style> block with a comment
    new_block = '<!-- Inline CSS removed - using external daoanh-design.css -->\n'
    new_content = content[:start] + new_block + content[end:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Removed broken inline <style> block, using external CSS only")
    print(f"Removed {end - start} characters from places.html")
else:
    print("Could not find <style> tags, no changes made")