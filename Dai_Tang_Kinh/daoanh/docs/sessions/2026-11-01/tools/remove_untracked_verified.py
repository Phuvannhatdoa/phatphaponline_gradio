"""Xóa các file CHƯA THEO DÕI trong cây chính, CHỈ KHI đã được bảo toàn:
  - nằm trong snapshot wip (refs/wip, blob trùng hash), HOẶC
  - nằm trong manifest sao lưu ngoài repo (sha256 khớp).
Không xóa file nào khác. Dừng ngay nếu có file không xác minh được.
"""
import hashlib
import json
import os
import subprocess

REPO = "E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app"
SNAP = "5ea88f6db6"
BK = "C:/Users/Nam Thien/.claude/wip-unsnapshotted-20261101"
LIMIT = 5 * 1024 * 1024


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


manifest = {m["path"]: m["sha256"] for m in json.load(open(os.path.join(BK, "manifest.json"), encoding="utf-8"))}
untracked = [n.decode("utf-8", "replace") for n in git("ls-files", "-o", "--exclude-standard", "-z").stdout.split(b"\0") if n]

to_remove, unverified = [], []
for n in untracked:
    full = os.path.join(REPO, n)
    if not os.path.isfile(full):
        continue
    size = os.path.getsize(full)
    if n in manifest:
        # Đã sao lưu ngoài repo và kiểm mã băm lúc sao lưu: xác minh lại trước khi xóa.
        if sha256(full) == manifest[n]:
            to_remove.append(n)
        else:
            unverified.append(n)
        continue
    if size > LIMIT:
        if n in manifest and sha256(full) == manifest[n]:
            to_remove.append(n)
        else:
            unverified.append(n)
        continue
    blob = git("rev-parse", "-q", "--verify", f"{SNAP}:{n}").stdout.decode().strip()
    hd = git("hash-object", "--path", n, "--", n).stdout.decode().strip()
    if blob and blob == hd:
        to_remove.append(n)
    else:
        unverified.append(n)

print(f"Xác minh được, sẽ xóa: {len(to_remove)} | chưa xác minh (giữ nguyên): {len(unverified)}")
for n in unverified:
    print("  GIỮ:", n)
if unverified:
    raise SystemExit("Dừng: còn file chưa xác minh, không xóa gì.")

for n in to_remove:
    os.remove(os.path.join(REPO, n))
print("Đã xóa", len(to_remove), "file đã xác minh.")
print("Còn lại chưa theo dõi:", len(git("ls-files", "-o", "--exclude-standard").stdout.splitlines()))
