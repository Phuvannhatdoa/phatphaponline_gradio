"""Tao noi dung app.py = blob HEAD + chi hunk route compliance/dashboard (dinh vi theo ngu canh).
Ghi ra OUT_PATH; khong dung worktree lam nguon. Chay: python -X utf8 make_blob.py <out_path>
"""
import os
import subprocess
import sys

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
REL = "Dai_Tang_Kinh/daoanh/app.py"
WT = os.path.join(ROOT, *REL.split("/"))
START = b"@app.route('/daoanh/api/compliance/dashboard', methods=['GET'])"
END = b"@app.route('/api/name_vi/<path:dila_id>', methods=['GET'])"


def block(b):
    i = b.index(START)
    j = b.index(END, i)
    return b[i:j]


head = subprocess.run(["git", "show", "HEAD:" + REL], cwd=ROOT, capture_output=True).stdout
wt = open(WT, "rb").read()
print("head bytes", len(head), "crlf", b"\r\n" in head, "| wt crlf", b"\r\n" in wt)
new_block = block(wt)
old_block = block(head)
print("head block lines", old_block.count(b"\n"), "| wt new block lines", new_block.count(b"\n"))
assert head.count(START) == 1, "HEAD co nhieu hon 1 route compliance"
assert wt.count(START) == 1, "WT co nhieu hon 1 route compliance"
out = head.replace(old_block, new_block, 1)
assert out != head, "khong thay doi gi"
assert out.count(START) == 1
out_path = sys.argv[1]
open(out_path, "wb").write(out)
print("wrote", out_path, len(out))
