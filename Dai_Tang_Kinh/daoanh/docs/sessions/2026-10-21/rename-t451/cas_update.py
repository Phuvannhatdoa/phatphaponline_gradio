import sys

REF = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\.git\refs\heads\truyen-dang-the-pho-clean"
PARENT = "2a882ff6f38de3511469d2c289e9d372b49ddebc"
NEW = "e09444a35ca64a981ac25166455eca20af1d83bc"

with open(REF, "r") as f:
    cur = f.read().strip()
if cur != PARENT:
    print("RACE: ref =", cur, "expected", PARENT)
    sys.exit(2)
with open(REF, "w") as f:
    f.write(NEW + "\n")
with open(REF, "r") as f:
    print("ref now:", f.read().strip())
