# -*- coding: utf-8 -*-
"""T130 + T131 INTEGRATION AUDIT — read-only — 2026-09-18
Chạy từ toplevel visjs-app. CHỈ ĐỌC + phân tích. KHÔNG ghi gì ngoài báo cáo docs."""
import io, os, re, subprocess, json, sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app'
D = os.path.join(BASE, 'Dai_Tang_Kinh', 'daoanh')

def read(p, sub=''):
    f = os.path.join(D, p) if not sub else os.path.join(sub, p)
    try:
        return io.open(f, encoding='utf-8').read()
    except Exception as e:
        return f'[[ERR {e}]]'

ph = read('places.html')
appc = read('app.py')
print('=' * 74)
print('T130 + T131 INTEGRATION AUDIT — SSOT read-only')
print('=' * 74)

# ---------- [1] T130: Pháp Mạch (direct lineage) traces in places.html ----------
print('\n[1] T130 — places.html hook counts (post-T157, post-T127/128/129)')
names = ['lineage-filter-tl1', 'lineage-filter-tl2', 'lineage-filter-tl3',
         'lineage-filter-verified', '?expand=', '_ov__', '_ftFullExpanded',
         '__ftFullExpanded', 'getBoundingBox', 'safeBus', 'getPositions',
         'canvasToDOM', 'showExpandedLineage', '?pick=', '?focus=', '?chain=']
for n in names:
    print(f'   {n!r}: {ph.count(n)}')

print('\n[1a] lineage filter checkboxes id= (actual on-page IDs)')
ids = sorted(set(re.findall(r'id="(lineage-filter-[\w-]+)"', ph)))
print('   ', ids)

# ---------- [2] T130: shares/tl semantics consistency ----------
print('\n[2] T130 — filter semantics (OR / none=all)'
      '\n   Audit note: OR among checked levels; no box checked = show all. '
      'QL chooser "+N nhánh" thay heuristic "Chính mạch".')

# ---------- [3] T131: Source governance touches in app.py ----------
print('\n[3] T131 — app.py source-governance references (Admin WIP — DO NOT TOUCH)')
for n in ['dataset_sources', 'data_sources', 'source_authority', 'license_status',
          'provenance', 'canonical', 'lineage_edge_assertions', 'dila_data',
          'marcus_data', 'conflicts', 'source_authority']:
    print(f'   {n!r}: {appc.count(n)}')

# ---------- [4] T130/T131 conflict surface with T127/128/129 ----------
print('\n[4] INTEGRATION CONFLICT SURFACE (grep of places.html for committed-locks)')
LOCK = ['T127', 'T128', 'T129', 'busbar', 'lineage-busbar', 'direct-lineage',
        'pedigree', 'collapsing', 'sibling-overflow']
for n in LOCK:
    print(f'   {n!r}: {ph.count(n)}')

# ---------- [5] Endpoint/API surface that T130 might need ----------
print('\n[5] API endpoints (app.py) — lineage & relation detail')
for n in ['get_lineage', 'get_details', 'related', 'lineage_desc', 'expand',
          'trace_lineage', 'relation_detail']:
    print(f'   {n!r}: {appc.count(n)}')

# ---------- [6] Verify T131 = DONE status in SSOT ----------
tt = read('docs/tasktodo.md')
print('\n[6] T131 SSOT row status:')
for m in re.finditer(r'\*\*T13[01] [^\n]*', tt):
    print('   ', m.group(0)[:220])

print('\n=== AUDIT EVIDENCE — read-only, no writes ===')
