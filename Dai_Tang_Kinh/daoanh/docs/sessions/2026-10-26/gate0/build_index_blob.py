"""Dựng blob index.html = HEAD + khối DILA (T453) — KHÔNG kéo WIP T467/T469.
usage: python build_index_blob.py <head_ref.html> <out.html>
Nguồn khối DILA: docs/sessions/2026-10-26/index.html (đã so với worktree: 4 khối DILA
giống hệt — CSS dw-*, #dilaWorks, _esc/_line/renderDilaPeople/loadAllWorks/renderDilaWorks,
handleSearch bản DILA). Neo định vị theo chuỗi, assert đúng 1 lần.
"""
import sys

head_path, out_path = sys.argv[1], sys.argv[2]
DOCS = "docs/sessions/2026-10-26/index.html"

def rd(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")

head = rd(head_path)
docs = rd(DOCS)

def one(text, s):
    n = text.count(s)
    assert n == 1, f"anchor count={n}: {s[:60]!r}"
    return text.index(s)

# 1) CSS dw-* : docs dòng 457..484 (từ "/* T453: kết quả kinh lục DILA */" đến ".dw-list li").
css_start = one(docs, "/* T453: kết quả kinh lục DILA */")
css_end = one(docs, ".dw-list li { margin-bottom: 4px; color: var(--text-hi); }\n") + len(".dw-list li { margin-bottom: 4px; color: var(--text-hi); }\n")
css = docs[css_start:css_end]
assert css.count("\n") == 28, css.count("\n")

# 2) Div kết quả DILA: docs dòng 945..946.
div = ('    <!-- ── T453: kết quả kinh lục DILA ─── -->\n'
       '    <div class="dw-wrap" id="dilaWorks" hidden></div>\n\n')
assert docs.count(div) == 1, "div anchor in docs"

# 3) handleSearch bản DILA + khối JS DILA: docs từ "function handleSearch(e) {" đến trước "function setSearch(val) {".
hs_start = one(docs, "function handleSearch(e) {")
dila_js_start = one(docs, "/* ── T453: hiển thị kinh lục DILA")
ss_docs = one(docs, "function setSearch(val) {")
assert hs_start < dila_js_start < ss_docs
docs_hs = docs[hs_start:dila_js_start]          # handleSearch + "}\n\n"
docs_dila_js = docs[dila_js_start:ss_docs]      # khối DILA JS, kết thúc "}\n"
assert docs_hs.rstrip().endswith("}") and docs_dila_js.rstrip().endswith("}")

# ---- áp vào HEAD ----
# (1) CSS trước </style>
s = one(head, "</style>")
head = head[:s] + "\n" + css + head[s:]

# (2) div trước khối demo Thiếu Lâm Tự
anchor = "    <!-- ── Thiếu Lâm Tự demo result panel ─── -->"
a = one(head, anchor)
head = head[:a] + div + head[a:]

# (3) thay handleSearch của HEAD bằng bản DILA, chèn khối JS DILA trước setSearch
hs_h = one(head, "function handleSearch(e) {")
ss_h = one(head, "function setSearch(val) {")
assert hs_h < ss_h
head = head[:hs_h] + docs_hs + docs_dila_js + head[ss_h:]

with open(out_path, "w", encoding="utf-8", newline="") as f:
    f.write(head)
print("OK css_lines=%d docs_hs_lines=%d dila_js_lines=%d -> %s" % (
    css.count("\n"), docs_hs.count("\n"), docs_dila_js.count("\n"), out_path))
