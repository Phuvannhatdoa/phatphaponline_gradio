import subprocess, os
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
raw = subprocess.run(["git", "show", "HEAD:Dai_Tang_Kinh/daoanh/docs/tasktodo.md"], capture_output=True).stdout
txt = raw.decode("utf-8")
print("CRLF count:", txt.count("\r\n"), "LF total:", txt.count("\n"))
s = txt.index("<!-- T453:START -->")
e = txt.index("<!-- T453:END -->") + len("<!-- T453:END -->")
print(repr(txt[s:e]))
