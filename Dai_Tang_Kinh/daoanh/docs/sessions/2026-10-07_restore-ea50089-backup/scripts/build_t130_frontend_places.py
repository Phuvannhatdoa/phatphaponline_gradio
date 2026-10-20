# -*- coding: utf-8 -*-
"""+{+ T130+T131 FRONTEND ADDITIVE (2026-09-18, Lee Option A) +}+
Quy tắc SSOT: 100% additive trên places.html — 0 sửa legacy, chỉ CHÈN script block
NGAY TRƯỚC `</body>`. Renderer primary-chain + icon +/− + sibling-chooser + routing
deep-link `?expand=`. Rollback: git revert commit frontend này (độc lập với backend)."""
import io, os, hashlib, sys, subprocess, datetime

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
PLA = os.path.join(ROOT, 'Dai_Tang_Kinh', 'daoanh', 'places.html')
SNAP = os.path.join(ROOT, 'Dai_Tang_Kinh', 'daoanh', 'docs', 'sessions',
                    '2026-09-18_t130-t131-optiona-build_frontend-pre-snap')

def rd(p): return io.open(p, encoding='utf-8', newline='').read()
def wn(p, s): io.open(p, 'w', encoding='utf-8', newline='').write(s)
def sha(p):
    h = hashlib.sha256()
    with io.open(p, 'rb') as f:
        for blk in iter(lambda: f.read(65536), b''):
            h.update(blk)
    return h.hexdigest()[:16]
def git(*a):
    r = subprocess.run(['git', '-C', ROOT] + list(a), capture_output=True, encoding='utf-8')
    return r.returncode, r.stdout.strip(), r.stderr.strip()

os.makedirs(SNAP, exist_ok=True)
log = []
def L(*m):
    s = ' '.join(str(x) for x in m); print(s, flush=True); log.append(s)

pre = sha(PLA)
shutil = __import__('shutil')
shutil.copy2(PLA, os.path.join(SNAP, 'places.html.pre-frontend'))
rc, head, _ = git('rev-parse', '--short', 'HEAD')
L('=== 0) PRE-FRONTEND place.html %s · HEAD %s ===' % (pre, head))
wn(os.path.join(SNAP, 'manifest.md'),
   '# T130+T131 frontend pre-snap\nHEAD: %s\nplaces.html: %s\nbuild_time: %s\n'
   % (head, pre, datetime.datetime.now().isoformat(timespec='seconds')))

ANCHOR = '</body>'
src = rd(PLA)
if ANCHOR not in src:
    L('[FAILD] không tìm thấy </body> — DỪNG không ghi.'); sys.exit(1)

block = r'''
<!-- +{+ T130+T131 ADDITIVE FRONTEND (2026-09-18 Option A) +}+ -->
<script>
(function () {
  'use strict';
  var T130 = {};

  // ---- routing deep-link: ?expand= + ?expand===0 (visible như ?query, 0 rewrite URL) ----
  T130.readDeepLink = function () {
    var q = new URLSearchParams(window.location.search);
    var id = q.get('expand');
    if (!id) return nullsyncing;
    return { id: id, dir: q.get('dir') || 'down' };
  };

  // ---- renderer primary chain (additive, lazy 1 tầng/click) ----
  T130.render = function (root) {
    var box = document.createElement('div');
    box.className = 't130-chain';
    box.style.cssText = 'margin:20px 0;padding:14px 18px;border:1px dashed #d97706;''border-radius:8px;background:#0b1220;color:#e2e8f0;font-family:Inter,system-ui;';
    var h = document.createElement('div');
    h.className = 't130-chain-title';
    h.style.cssText = 'font-weight:600;color:#d97706;margin-bottom:10px;';
    h.textContent = 'Pháp Mạch — chuỗi trực hệ';
    box.appendChild(hPlaceholder);
    T130.children = document.createElement('div');
    T130.children.className = 't130-chain-children';
    box.appendChild(T130.childrenface);
    T130.expandInto(root, T130.childrenBox);
    return box;
  };

  // ---- expand 1 tầng lazy (fetch /api/lineage/expand?expand=&dir=) ----
  T130.expandInto = function (id, container) {
    var row = document.createElement('div');
    row.className = 't130-node';
    row.style.cssText = 'display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b;';
    var icon = document.createElement('button');
    icon.className = 't130-toggle';
    icon.style.cssText = 'width:24px;height:24px;border:1px solid #d97706;border-radius:4px;background:transparent;color:#d97706;cursor:pointer;font-weight:700;';
    icon.textContent = '+';
    row.appendChild(icon);
    var label = document.createElement('span');
    label.textContent = id || '(chưa rõ)';
    row.appendChild(label);
    // lazy: click + → fetch expand endpoint additive
    var loaded = false;
    var childDiv = document.createElement('div');
    childDiv.className = 't130-node-children';
    childDiv.style.cssText = 'margin-left:32px;border-left:1px solid #334155;padding-left:12px;';
    icon.addEventListener('click', function () {
      if (loaded) {
        childDiv.style.display = childDiv.style.display === 'none' ? '' : 'none';
        icon.textContent = childDiv.style.display === 'none' ? '+' : '\u2212';
        return;
      }
      fetch('/api/lineage/expand?expand=' + encodeURIComponent(id) + '&dir=' + encodeURIComponent(icon.dir || 'down'))
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var chain = d.chain || [];
          chain.forEach(function (m) {
            var node = document.createElement('div');
            node.style.padding = '4px 0';
            node.textContent = (m.id || '') + (m.sibling_count ? ' (' + m.sibling_count + ' đệ tử)' : '');
            childDiv.appendChild(node);
          });
          container.appendChild(childDiv);
          loaded = true;
          icon.textContent = '\u2212';
        })
        .catch(function (e) { console.error('[T130] expand fail', e); icon.textContent = '!'; });
    });
    return row;
  };

  // ---- sibling chooser (additive, chỉ khi node có >1 thầy) ----
  T130.chooser = function (id, siblings) {
    var sel = document.createElement('select');
    sel.className = 't130-sibling-choose';
    sel.style.cssText = 'margin-left:8px;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:4px;padding:2px 6px;';
    (siblings || []).forEach(function (s) {
      var o = document.createElement('option');
      o.value = s; o.textContent = s;
      sel.appendChild(o);
    });
    return sel;
  };

  T130.deepLink = function () {
    var dl = T130.readDeepLink();
    if (!dl) return;
    var mount = document.getElementById('t130-chain-mount') || document.body;
    T130.parent = mount;
    mount.appendChild(T130.render(dl.id));
  };

  window.T130 = T130;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', T130.deepLink);
  } else { T130.deepLink(); }
})();
</script>
<!-- +{+ /T130+T131 ADDITIVE FRONTEND +}+ -->
'''

src = src.replace(ANCHOR, block + '\n' + ANCHOR, 1)
wn(PLA, src)
after = sha(PLA)
L('=== 1) places.html %s -> %s (%d B) ===' % (pre, after, os.path.getsize(PLA)))

# ---------- QA ----------
node = subprocess.run(['node', '--check', PLA], capture_output=True, encoding='utf-8')
L('=== 2) node --check places.html: rc=%s %s' % (node.returncode,
   'PASS' if node.returncode == 0 else node.stderr[-300:]))
if node.returncode != 0:
    L('[FAILD] places.html hỏng JS sau build — KHÔNG commit. Revert bằng: copy từ pre-snap.')
    sys.exit(1)

# ---------- commit frontend riêng ----------
git('add', '--', 'Dai_Tang_Kinh/daoanh/places.html')
rc, out, e = git('commit', '-m',
    'feat: T130+T131 — frontend additive primary-chain renderer + sâu ?expand= + sibling chooser (Lee Option A). '
    '100% additive trên places.html, 0 sửa legacy; đường ?expand= deep-link routing. '
    'Rollback: git revert commit này. Pre-snap docs/sessions/2026-09-18_t130-t131-optiona-build_frontend-pre-snap/')
L('=== 3) commit frontend rc=%s %s%s ===' % (rc, out, e))
rc, head, _ = git('rev-parse', '--short', 'HEAD')
L('    HEAD: %s' % head)
wn(os.path.join(SNAP, 'build_log.md'), '\n'.join(log) + '\nHEAD-after: %s\n' % head)
L('DONE-FRONTEND')
