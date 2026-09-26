#!/usr/bin/env python3
with open('E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/home.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Replace the broken searchHTML script
old_script = """<script>
document.addEventListener('DOMContentLoaded', function() {
  const header = document.querySelector('.da-header');
  if (!header) return;
  const searchHTML = '<div style=\\'margin-left:10px\\'>' + '<input type=\\'text\\' id=\\'homeSearch\\' placeholder=\\'Tìm kiếm\\' onkeyup=\\'if(this.value.length>=2) window.location=\\'/daoanh/places?q=\\' + encodeURIComponent(this.value)'>' + '<button onclick=\\'if(document.getElementById(\\'homeSearch\\').value.length>=2) window.location=\\'/daoanh/places?q=\\' + encodeURIComponent(document.getElementById(\\'homeSearch\\').value)>🔍</button>' + '</div>';
  const pos = header.querySelector('.da-header-actions');
  if (pos) { pos.innerHTML = searchHTML + pos.innerHTML; }
});
</script>"""

new_script = """<script>
document.addEventListener('DOMContentLoaded', function() {
  const header = document.querySelector('.da-header');
  if (!header) return;
  const input = document.createElement('input');
  input.type = 'text';
  input.id = 'homeSearch';
  input.placeholder = 'Tìm Thiếu Lâm Tự, chùa, tự...';
  input.autocomplete = 'off';
  input.style.cssText = 'padding:6px 12px; border-radius:20px; border:1px solid var(--da-border); background:var(--da-card); color:var(--da-text); font-size:12px;';
  input.onkeyup = function() {
    if (this.value.length >= 2) {
      window.location = '/daoanh/places?q=' + encodeURIComponent(this.value);
    }
  };
  const btn = document.createElement('button');
  btn.style.cssText = 'padding:6px 12px; margin-left:5px; border-radius:20px; border:1px solid var(--da-border); background:var(--da-gold); color:var(--da-dark-bg); font-size:12px; cursor:pointer;';
  btn.textContent = '🔍';
  btn.onclick = function() {
    if (input.value.length >= 2) {
      window.location = '/daoanh/places?q=' + encodeURIComponent(input.value);
    }
  };
  const actions = header.querySelector('.da-header-actions');
  if (actions) {
    actions.appendChild(input);
    actions.appendChild(btn);
  }
});
</script>"""

if old_script in c:
    c = c.replace(old_script, new_script)
    print('Replaced script block')
else:
    print('Old script not found, checking what exists...')
    # Debug: show what's around the script area
    idx = c.find('da-header-actions')
    if idx >= 0:
        print(f'Found da-header-actions at position {idx}')
        print(c[idx-100:idx+100])

with open('E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/home.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done writing')