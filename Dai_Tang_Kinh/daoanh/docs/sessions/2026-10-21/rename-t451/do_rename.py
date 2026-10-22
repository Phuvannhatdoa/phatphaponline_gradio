import os
base = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\tasks"
src = os.path.join(base, "T445-claude-place-name-import.md")
dst = os.path.join(base, "T451-claude-place-name-import.md")
assert os.path.exists(src), "src missing"
assert not os.path.exists(dst), "dst exists"
os.rename(src, dst)
print("renamed ->", dst, os.path.exists(dst), os.path.exists(src))
