#!/usr/bin/env python3
"""Add search functionality to home.html"""
with open('home.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Find the da-header-actions div and add search box after it
# Pattern: da-header-actions
import re
# Actually, let's just add the search script before </body>
search_script = "<script>\ndocument.addEventListener('DOMContentLoaded', function() {\n  const header = document.querySelector('.da-header');\n  if (!header) return;\n  const searchHTML = '<div style=\\'margin-left:10px\\'>' + '<input type=\\'text\\' id=\\'homeSearch\\' placeholder=\\'Tìm kiếm\\' onkeyup=\\'if(this.value.length>=2) window.location=\\'/daoanh/places?q=\\' + encodeURIComponent(this.value)'>' + '<button onclick=\\'if(document.getElementById(\\'homeSearch\\').value.length>=2) window.location=\\'/daoanh/places?q=\\' + encodeURIComponent(document.getElementById(\\'homeSearch\\').value)>🔍</button>' + '</div>';\n  const pos = header.querySelector('.da-header-actions');\n  if (pos) { pos.innerHTML = searchHTML + pos.innerHTML; }\n});\n</script>";

# Find position before </body>
body_end = c.rfind('</body>')
if body_end >= 0:
    new_c = c[:body_end] + search_script + c[body_end:]
    with open('home.html', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print('SUCCESS: Search script added before </body>')
else:
    print('Could not find </body>')