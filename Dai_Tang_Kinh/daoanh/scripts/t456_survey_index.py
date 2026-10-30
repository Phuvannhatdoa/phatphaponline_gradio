# -*- coding: utf-8 -*-
"""T456 — khảo sát code autocomplete HOME hiện có (index.html + backend routes)."""
import os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"

idx = open(os.path.join(BASE, "index.html"), encoding="utf-8", errors="replace").read()

print("=== index.html: các block liên quan suggest ===")
for m in re.finditer(r"(searchSuggest|suggestAutocomplete|runSuggest|fetchSuggest|sr-suggest)", idx):
    s = max(0, m.start() - 120)
    print("---")
    print(idx[s:m.start() + 260].replace("\r", "")[:420])

print()
print("=== endpoint được gọi trong index.html ===")
for m in set(re.finditer(r"['\"](/daoanh/api[^'\"]*)['\"]", idx)):
    print("   ", m.group(1))
print()
print("=== fetch/axios trong index.html ===")
for m in set(re.finditer(r"(fetch\(|axios\.)", idx)):
    s = max(0, m.start() - 60)
    print("   ...", idx[s:m.start() + 150].replace("\n", " ")[:210])
