"""Trích mọi <script> inline của một file HTML ra file .js tạm trong gate0/, rồi node --check.
usage: python check_js.py <file.html> <tag>
"""
import re, subprocess, sys, os
src, tag = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8", newline="").read().replace("\r\n", "\n")
blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"_js_{tag}.js")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n;\n".join(blocks))
print("inline script blocks:", len(blocks), "->", out)
r = subprocess.run(["node", "--check", out], capture_output=True, text=True)
print("node --check exit:", r.returncode, r.stderr.strip()[:800])
