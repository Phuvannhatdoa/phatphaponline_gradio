# -*- coding: utf-8 -*-
# Kiem chung READ-ONLY tren HEAD: mốc đặc trưng, không lọt WIP, cú pháp.
import re
import subprocess
import sys

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
D = "Dai_Tang_Kinh/daoanh/"
APP, IDXH, NVM = D + "app.py", D + "index.html", D + "admin/namevimap.html"
PARENT0 = "c2b9a4f5ac3c03e23b324eb2c6e71ee6162481f2"


def git(args):
    r = subprocess.run(["git"] + args, cwd=REPO, capture_output=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.decode("utf-8")


def blob(path):
    return git(["cat-file", "blob", "HEAD:" + path])


fails = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        fails.append(label)


app, idx, nvm = blob(APP), blob(IDXH), blob(NVM)

# --- mốc T465
check("T465 app: JOIN codex_place_name", "LEFT JOIN codex_place_name c ON c.dila_id = pd.id" in app)
check("T465 app: claude_name_vi select+dict", "c.name_vi AS claude_name_vi" in app and "r['claude_name_vi']" in app)
check("T465 nvm: cell dung item.claude_name_vi", "item.claude_name_vi" in nvm)
# --- mốc T467
check("T467 index: handleSearch doc d.monks/d.works", "const monks = (d && d.monks) || [];" in idx)
check("T467 index: renderSearchResults ton tai", "function renderSearchResults(monks, works, q, placesUrl)" in idx)
check("T467 index: khong con d.dila_works dau handleSearch chi doc", "d.dila_works" in idx)  # T453 nhanh van con (HEAD)
# --- mốc T469
check("T469 app: endpoint /daoanh/api/search/suggest", "@app.route('/daoanh/api/search/suggest')" in app)
check("T469 app: cache builders", "_get_person_suggest_cache" in app and "_get_work_suggest_cache" in app)
check("T469 index: initSearchSuggest + hero searchSuggest", "function initSearchSuggest()" in idx and 'id="searchSuggest"' in idx)
check("T469 index: closeSuggest trong setSearch", "function setSearch(val) {\n  closeSuggest();" in idx)

# --- KHONG lọt WIP của task khác
for label, marker, text in [
    ("app: T466 gemini_join", "gemini_join", app),
    ("app: T466 lexicon han lookup trong vi-map", "for han_name in set(name_zhs)", app),
    ("app: T445 wizard", "T445 Wizard API Endpoints", app),
    ("app: ancestor primary_candidate (chua duoc commit)", "primary_candidate", app),
    ("nvm: T466 gemini cell", "item.gemini_name_vi", nvm),
    ("nvm: T446 place-compare-summary", "place-compare-summary", nvm),
    ("nvm: T437 flag batch", "etlFlagQueueLoadAll", nvm),
    ("index: T469 closeSuggest trong handleSearch", "closeSuggest(); // T469: Enter", idx),
]:
    check("KHONG co " + label, marker not in text)

# --- cú pháp: compile python từ blob; JS inline qua node --check (stdin, không ghi file)
try:
    compile(app, APP, "exec")
    check("py_compile app.py (HEAD blob)", True)
except SyntaxError as e:
    check("py_compile app.py (HEAD blob): %s" % e, False)

scripts = re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", idx, re.S)
js = "\n;\n".join(scripts)
r = subprocess.run(["node", "--check", "-"], input=js.encode("utf-8"), capture_output=True)
check("node --check JS inline index.html (HEAD): " + (r.stderr.decode("utf-8", "replace")[:200] or "ok"), r.returncode == 0)

# --- diff phạm vi toàn cục từ PARENT0 tới HEAD
stat = git(["diff", "--stat", PARENT0 + "..HEAD"])
print(stat)
names = git(["diff", "--name-only", PARENT0 + "..HEAD"]).split()
check("Pham vi commit: chi 3 file", sorted(names) == sorted([APP, IDXH, NVM]))

print("FAILS:", fails)
sys.exit(1 if fails else 0)
