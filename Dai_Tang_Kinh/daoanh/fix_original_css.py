#!/usr/bin/env python3
"""Fix the original inline CSS from places.html by adding missing } closing braces."""
import re

filepath = 'original_style_block.txt'

with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Systematically fix each missing } by replacing broken patterns
fixes = [
    # Fix 1: Add } after var(--pp-text); and before .serif
    (r'background-color: var\(--pp-dark-bg\);\s+color: var\(--pp-text\);\s+\.serif', 
     'background-color: var(--pp-dark-bg);\n            color: var(--pp-text);\n        }\n        .serif'),
    
    # Fix 2: Add } after .serif 
    (r'\.serif \{ font-family: .Noto Serif., serif; \}', 
     '.serif { font-family: \'Noto Serif\', serif; }\n        #map {'),
    
    # Fix 3: Add } after #map background and z-index
    (r'background: #000;\s+z-index: 1;?\s+\.custom-div-icon', 
     'background: #000;\n            z-index: 1;\n        }\n        .custom-div-icon'),
    
    # Fix 4: Add } after .halo-active properties (before .pp-sidebar)
    (r'border: 2px solid white !important;\s*\n', 
     'border: 2px solid white !important;\n            }\n        .pp-sidebar {'),
    
    # Fix 5: Add } after .pp-sidebar background (before .pp-card)
    (r'border-right: 1px solid rgba\(255,255,255,0.05\);\)?\s*\n\s*\n\s*\.pp-card', 
     'border-right: 1px solid rgba(255,255,255,0.05);\n        }\n        .pp-card {'),
    
    # Fix 6: Add } after .pp-card properties (box-shadow)
    (r'box-shadow: 0 4px 20px rgba\(0,0,0,0.4\);\)?\s*\n\s*\n\s*\.pp-card:hover', 
     'box-shadow: 0 4px 20px rgba(0,0,0,0.4);\n        }\n        .pp-card:hover {'),
    
    # Fix 7: Add } after .pp-card:hover properties (before .sidebar-scroll)
    (r'transform: translateY\(-2px\);\)?\s*\n\s*\n\s*\.sidebar-scroll', 
     'transform: translateY(-2px);\n        }\n        .sidebar-scroll::-webkit-scrollbar {'),
    
    # Fix 8: Add } after .sidebar-scroll .webkit-scrollbar
    (r'\.sidebar-scroll::-webkit-scrollbar \{ width: 4px; \}\s*\n\s*\n\s*\.sidebar-scroll::-webkit-scrollbar-thumb', 
     '.sidebar-scroll::-webkit-scrollbar { width: 4px; }\n        }\n        .sidebar-scroll::-webkit-scrollbar-thumb {'),
    
    # Fix 9: Add } after .sidebar-scroll thumb
    (r'background: rgba\(255,255,255,0.1\); border-radius: 10px; \}\s*\n\s*\n\s*\.timeline-container', 
     'background: rgba(255,255,255,0.1); border-radius: 10px; }\n        }\n        .timeline-container {'),
    
    # Fix 10: Add } after timeline-container properties (before input[type=range])
    (r'backdrop-filter: blur\(20px\); border: 1px solid rgba\(243, 156, 18, 0.2\); box-shadow: 0 30px 60px rgba\(0,0,0,0.8\);\)?\s*\n\s*\n\s*input', 
     'backdrop-filter: blur(20px);\n            border: 1px solid rgba(243, 156, 18, 0.2);\n            box-shadow: 0 30px 60px rgba(0,0,0,0.8);\n        }\n        input[type=range]::-webkit-slider-runnable-track {'),
    
    # Fix 11: Add } after input[type=range] track
    (r'background: rgba\(255,255,255,0.1\); border-radius: 10px; \}\)?\s*\n\s*\n\s*\.place-label', 
     'background: rgba(255,255,255,0.1); border-radius: 10px; }\n        }\n        .place-label {'),
    
    # Fix 12: Add } after .place-label properties (before .place-label-major)
    (r'border-radius: 5px; border: 1px solid rgba\(251, 191, 36, 0.35\); white-space: nowrap; pointer-events: auto; cursor: pointer; text-shadow: 0 1px 4px rgba\(0,0,0,0.9\); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; letter-spacing: 0.03em; backdrop-filter: blur\(6px\); box-shadow: 0 2px 6px rgba\(0,0,0,0.5\); transition: opacity 0.2s;\)?\s*\n\s*\n\s*\.place-label-major', 
     'border-radius: 5px; border: 1px solid rgba(251, 191, 36, 0.35); white-space: nowrap; pointer-events: auto; cursor: pointer; text-shadow: 0 1px 4px rgba(0,0,0,0.9); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; letter-spacing: 0.03em; backdrop-filter: blur(6px); box-shadow: 0 2px 6px rgba(0,0,0,0.5); transition: opacity 0.2s; }\n        }\n        .place-label-major {'),
    
    # Fix 13: Add } after .place-label-major
    (r'box-shadow: 0 3px 10px rgba\(251, 191, 36, 0.2\);\)?\s*\n\s*\n\s*@media', 
     'box-shadow: 0 3px 10px rgba(251, 191, 36, 0.2);\n        }\n        @media (max-width: 768px) {'),
    
    # Fix 14: Add } after @media inner .place-label
    (r'font-size: 10px; padding: 2px 6px; \}\s*\n\s*\n\s*\.place-label', 
     'font-size: 10px; padding: 2px 6px; }\n        }\n        .place-label {'),
    
    # Fix 15: Add } after .place-label max-width properties
    (r'font-size: 11px; color: #fbbf24; \}\s*\n\s*\n\s*\.osm-dark-mode', 
     'font-size: 11px; color: #fbbf24; }\n        }\n        .osm-dark-mode {'),
    
    # Fix 16: Add } after .osm-dark-mode filter
    (r'filter: invert\(100%\) hue-rotate\(180deg\) brightness\(95%\) contrast\(90%\);\)?\s*\n\s*\n\s*\.leaflet', 
     'filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);\n        }\n        .leaflet-marker-pane, .leaflet-popup-pane, .leaflet-tooltip-pane {'),
    
    # Fix 17: Add } after leaflet panes, before </style>
    (r'\.leaflet-marker-pane, \.leaflet-popup-pane, \.leaflet-tooltip-pane \{ filter: none !important; \}\)?\s*\n\s*\n\s*</style>', 
     '.leaflet-marker-pane, .leaflet-popup-pane, .leaflet-tooltip-pane { filter: none !important; }\n        }\n    </style>'),
]

# Apply all fixes
for i, (pattern, replacement) in enumerate(fixes):
    matches = len(re.findall(pattern, content))
    if matches > 0:
        content = re.sub(pattern, replacement, content)
        print(f'Fix {i+1}: {matches} match(es) applied')
    else:
        print(f'Fix {i+1}: 0 matches (pattern may not match)')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nAll fixes applied. Final length: {len(content)}')
print('Has </style>:', '</style>' in content)
print('Has .pp-sidebar:', '.pp-sidebar' in content)