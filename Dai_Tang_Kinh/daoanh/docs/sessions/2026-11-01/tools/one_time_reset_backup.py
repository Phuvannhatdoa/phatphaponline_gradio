"""Bước 1 của đưa cây chính về HEAD: sao lưu các file untracked KHÔNG nằm trong snapshot.

Chỉ sao lưu và kiểm mã băm. KHÔNG xóa, KHÔNG ghi vào repo.
Đích: C:/Users/Nam Thien/.claude/wip-unsnapshotted-20261101/<đường dẫn tương đối>
Manifest: cùng thư mục, manifest.json (sha256 + kích thước).
"""
import hashlib
import json
import os
import shutil
import subprocess

REPO = "E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app"
SNAP = "5ea88f6db6"
DEST = "C:/Users/Nam Thien/.claude/wip-unsnapshotted-20261101"
LIMIT = 5 * 1024 * 1024


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True).stdout


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def in_snapshot(path):
    r = subprocess.run(["git", "rev-parse", "-q", "--verify", f"{SNAP}:{path}"],
                       cwd=REPO, capture_output=True, text=True)
    return bool(r.stdout.strip())


def main():
    names = [n.decode("utf-8", "replace") for n in git("ls-files", "-o", "--exclude-standard", "-z").split(b"\0") if n]
    todo = []
    for n in names:
        full = os.path.join(REPO, n)
        if os.path.getsize(full) > LIMIT or not in_snapshot(n):
            todo.append(n)
    print(f"Cần sao lưu: {len(todo)} file")
    manifest = []
    os.makedirs(DEST, exist_ok=True)
    for i, n in enumerate(todo, 1):
        src = os.path.join(REPO, n)
        # Tên đích theo số thứ tự: đường dẫn gốc có tên không hợp lệ trên Windows.
        dst = os.path.join(DEST, f"file-{i:02d}.bin")
        shutil.copy2(src, dst)
        h_src, h_dst = sha256(src), sha256(dst)
        if h_src != h_dst:
            print("LỖI mã băm:", n)
            return 1
        manifest.append({"path": n, "sha256": h_src, "bytes": os.path.getsize(src)})
        print("OK", os.path.getsize(src), n)
    with open(os.path.join(DEST, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"Xong: {len(manifest)} file, manifest tại {DEST}/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
