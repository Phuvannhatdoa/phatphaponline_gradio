#!/usr/bin/env python3
"""Insert fixed dark theme CSS into places.html."""
import re

filepath = 'places.html'

with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Find the insertion point: after the daoanh-design.css link
# Pattern: href="...daoanh-design.css"> followed by newline and the comment
pattern = r'(href="[^"]*daoanh-design\.css">)\n    <!-- Inline CSS removed'
match = re.search(pattern, c)

if match:
    css_block = '''<style>
/*!
 * Dao Anh — Design System v1
 * Dark theme overrides for places.html
 * Colors: --pp-dark-bg: #0a0c10, --pp-card-bg: rgba(22,28,38,0.8), --pp-text: #e2e8f0
 * Gold: --pp-gold: #f39c12
 */

        :root { 
            --pp-gold: #f39c12; 
            --pp-brown: #78350f;
            --pp-dark-bg: #0a0c10;
            --pp-card-bg: rgba(22, 28, 38, 0.8);
            --pp-text: #e2e8f0;
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--pp-dark-bg);
            color: var(--pp-text);
        }
        .serif { font-family: 'Noto Serif', serif; }
        #map { 
            height: calc(100vh - 70px); 
            z-index: 1; 
            background: #000;
        }
        .custom-div-icon { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .halo-active {
            box-shadow: 0 0 0 4px rgba(243, 156, 18, 0.2), 0 0 35px 20px rgba(243, 156, 18, 0.3);
            background-color: var(--pp-gold) !important;
            transform: scale(2.2);
            z-index: 1000 !important;
            border: 2px solid white !important;
        }
        .pp-sidebar {
            background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        .pp-card {
            background: var(--pp-card-bg);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            transition: all 0.3s ease;
        }
        .pp-card:hover { 
            border-color: rgba(243, 156, 18, 0.5);
            transform: translateY(-2px);
        }
        .sidebar-scroll::-webkit-scrollbar { width: 4px; }
        .sidebar-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        .timeline-container {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(243, 156, 18, 0.2);
            box-shadow: 0 30px 60px rgba(0,0,0,0.8);
        }
        input[type=range]::-webkit-slider-runnable-track {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        .place-label {
            background: rgba(0, 0, 0, 0.82);
            color: #fbbf24;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 5px;
            border: 1px solid rgba(251, 191, 36, 0.35);
            white-space: nowrap;
            pointer-events: auto; cursor: pointer;
            text-shadow: 0 1px 4px rgba(0,0,0,0.9);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            letter-spacing: 0.03em;
            backdrop-filter: blur(6px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.5);
            transition: opacity 0.2s;
        }
        .place-label-major {
            font-size: 13px;
            font-weight: 700;
            background: rgba(10, 10, 10, 0.9);
            border: 2px solid rgba(251, 191, 36, 0.55);
            padding: 5px 11px;
            box-shadow: 0 3px 10px rgba(251, 191, 36, 0.2);
        }
        @media (max-width: 768px) {
            .place-label { font-size: 10px; padding: 2px 6px; }
            .place-label-major { font-size: 12px; padding: 4px 9px; }
        }
        .osm-dark-mode {
            filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
        }
        .leaflet-marker-pane, .leaflet-popup-pane, .leaflet-tooltip-pane {
            filter: none !important;
        }
</style>'''

    # Insert: css_block, then keep the existing comment
    prefix = match.group(1)  # href="...daoanh-design.css">
    # The rest of the line + comment
    rest = c[idx + len(prefix):]
    
    new_c = c[:idx + len(prefix)] + css_block + '\n    <!-- Inline CSS removed - using external daoanh-design.css -->\n\n' + c[idx + len(prefix) + len('<!-- Inline CSS removed - using external daoanh-design.css -->'):]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_c)
    print('SUCCESS: CSS block inserted before comment')
else:
    # Fallback: append before </head>
    head_end = c.find('</head>')
    if head_end >= 0:
        css_block = '<style>\n        :root { --pp-dark-bg: #0a0c10; --pp-card-bg: rgba(22,28,38,0.8); --pp-text: #e2e8f0; }\n        body { background-color: var(--pp-dark-bg); color: var(--pp-text); }\n        .pp-sidebar { background: linear-gradient(180deg, #0f172a 0%, #020617 100%); }\n        .pp-card { background: var(--pp-card-bg); border-radius: 20px; }\n    </style>'
        new_c = c[:head_end] + css_block + c[head_end:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_c)
        print('SUCCESS: CSS block appended before </head> (fallback)')
    else:
        print('Could not find insertion point')