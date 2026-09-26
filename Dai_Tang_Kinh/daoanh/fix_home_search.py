#!/usr/bin/env python3
"""Fix home.html search autocomplete functionality"""
with open('E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/home.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Find the da-header-actions div and add search box after the logo
# Or add search input at the end before </body>
# Let me add it before </body>

search_input = '''
<!-- Search box in header -->
<div style="margin-left:15px;">
    <input type="text" id="homenavsearch" placeholder="Tìm Thiếu Lâm Tự, chùa, tự..." 
           onkeyup="if(this.value.length>=2) window.location='/daoanh/places?q='+encodeURIComponent(this.value)"
           autocomplete="off"
           style="padding:6px 12px; border-radius:20px; border:1px solid var(--da-border); background:var(--da-card); color:var(--da-text); font-size:12px;">
    <button style="padding:6px 12px; margin-left:5px; border-radius:20px; border:1px solid var(--da-border); background:var(--da-gold); color:var(--da-dark-bg); font-size:12px; cursor:pointer;">🔍</button>
</div>'''

# Insert before </body>
body_end = c.rfind('</body>')
if body_end >= 0:
    new_c = c[:body_end] + search_input + c[body_end:]
    with open('E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/home.html', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print('SUCCESS: Search input added before </body>')
else:
    print('Could not find </body>')