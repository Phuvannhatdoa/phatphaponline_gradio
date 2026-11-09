"""WIP guard — sao lưu WIP không chạm worktree/index, và phát hiện ghi đè.

Lệnh:
  snapshot  Chụp WIP hiện tại (file tracked đã sửa + file mới không ignore, <5MB)
            thành một commit mồ côi, gắn ref refs/wip/<ts>. KHÔNG đổi worktree,
            KHÔNG đổi index thật (dùng GIT_INDEX_FILE tạm), KHÔNG stash/reset.
  check     So worktree hiện tại với snapshot gần nhất. Với mỗi file đã có WIP
            ở snapshot mà bây giờ: (a) biến mất, (b) mất >20% số dòng, hoặc
            (c) đổi nhưng không có dòng trong docs/sessions/*/overwrite-log.md
            → in CẢNH BÁO cụ thể và exit 2.

Quy tắc ghi đè hợp lệ: mọi agent sửa file có WIP phải ghi một dòng vào
docs/sessions/<ngày>/overwrite-log.md (xem hàm log_overwrite). `check` coi file
có dòng log là đã được giải thích.
"""
import datetime as dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # daoanh/
REPO = ROOT.parents[1]                               # visjs-app (git toplevel)
DOCS = ROOT / "docs" / "sessions"
REF_PREFIX = "refs/wip/"
MAX_NEW_FILE = 5 * 1024 * 1024
SHRINK_LIMIT = 0.20


def git(*args, env=None, check=True):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout


def _rel(path_bytes):
    return path_bytes.decode("utf-8", "replace")


def dirty_files():
    """Đường dẫn (relative tới REPO) đã sửa/xoá (tracked) + file mới hợp lệ."""
    tracked = git("diff", "--name-only", "HEAD", "-z", "--", ".", check=False).split(b"\0")
    untracked = git("ls-files", "-o", "--exclude-standard", "-z", "--", ".", check=False).split(b"\0")
    out = set()
    for p in tracked:
        if p:
            out.add(_rel(p))
    for p in untracked:
        if not p:
            continue
        f = REPO / _rel(p)
        if f.is_file() and f.stat().st_size <= MAX_NEW_FILE:
            out.add(_rel(p))
    return sorted(out)


def snapshot():
    files = dirty_files()
    if not files:
        print("Không có WIP để chụp.")
        return 0
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    fd, idx = tempfile.mkstemp(prefix="wipidx-")
    os.close(fd)
    os.unlink(idx)
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    try:
        git("read-tree", "HEAD", env=env)
        for f in files:
            if (REPO / f).exists():
                git("update-index", "--add", "--", f, env=env)
            else:
                git("update-index", "--force-remove", "--", f, env=env)
        tree = git("write-tree", env=env).decode().strip()
        head = git("rev-parse", "HEAD").decode().strip()
        msg = f"WIP snapshot {ts} ({len(files)} file) — tự động, không phải commit làm việc"
        commit = git("commit-tree", tree, "-p", head, "-m", msg).decode().strip()
        git("update-ref", f"{REF_PREFIX}{ts}", commit)
    finally:
        if os.path.exists(idx):
            os.unlink(idx)
    print(f"Đã chụp {len(files)} file vào {REF_PREFIX}{ts} = {commit[:10]}")
    return 0


def latest_snapshot():
    refs = git("for-each-ref", "--sort=-creatordate", "--format=%(refname)", REF_PREFIX).decode().split()
    return refs[0] if refs else None


def line_count(blob_bytes):
    return blob_bytes.count(b"\n")


def logged_today(path):
    """True nếu file này đã có dòng trong overwrite-log.md của hôm nay (hoặc hôm trước)."""
    for d in sorted(DOCS.glob("*"), reverse=True)[:3]:
        log = d / "overwrite-log.md"
        if log.exists() and path in log.read_text(encoding="utf-8", errors="replace"):
            return True
    return False


def snapshot_blobs(ref):
    """{path: blob_sha} của snapshot — một lần ls-tree, không gọi git từng file."""
    out = git("ls-tree", "-r", ref, "--", ".", check=False).decode("utf-8", "replace")
    res = {}
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 3:
            res[path] = parts[2]
    return res


def current_blobs(paths):
    """Hash đĩa theo đúng bộ lọc git (CRLF/LF) — so khớp với blob đã lưu trong git."""
    out = {}
    for p in paths:
        if not (REPO / p).is_file():
            continue
        h = git("hash-object", "--path", p, "--", p, check=False).decode().strip()
        out[p] = h
    return out


def check():
    ref = latest_snapshot()
    if not ref:
        print("Chưa có snapshot. Chạy: python scripts/wip_guard.py snapshot")
        return 0
    snap = snapshot_blobs(ref)
    wip_at_snap = dirty_files_at(ref)
    now = current_blobs(wip_at_snap)
    warnings = []
    for f in wip_at_snap:
        if f not in snap:
            continue
        f_full = REPO / f
        if not f_full.exists():
            warnings.append((f, "BIẾN MẤT khỏi đĩa, WIP còn trong snapshot " + ref))
            continue
        if now.get(f) == snap[f]:
            continue
        before = git("cat-file", "blob", snap[f])
        after = f_full.read_bytes()
        if line_count(after) < line_count(before) * (1 - SHRINK_LIMIT):
            warnings.append((f, f"MẤT >20% dòng: {line_count(before)} → {line_count(after)}"))
        elif not logged_today(f):
            warnings.append((f, "ĐỔI KHÔNG CÓ GHI CHÚ trong overwrite-log.md"))
    if not warnings:
        print(f"OK — không phát hiện ghi đè so với {ref}.")
        return 0
    print(f"CẢNH BÁO ghi đè so với snapshot {ref}:")
    for f, why in warnings:
        print(f"  - {f}: {why}")
    return 2


def dirty_files_at(ref):
    """Danh sách file có WIP tại thời điểm snapshot: đối chiếu snapshot với HEAD."""
    out = git("diff", "--name-only", "HEAD", ref, "--", ".", check=False).decode("utf-8", "replace").split("\n")
    return [p for p in out if p]


def log_overwrite(path, reason, agent):
    """Agent gọi hàm này TRƯỚC khi ghi đè file có WIP, để có dấu vết truy ngược."""
    day = dt.datetime.now().strftime("%Y-%m-%d")
    d = DOCS / day
    d.mkdir(parents=True, exist_ok=True)
    log = d / "overwrite-log.md"
    stamp = dt.datetime.now().strftime("%H:%M:%S")
    line = f"- {stamp} | {agent} | {path} | {reason}\n"
    with open(log, "a", encoding="utf-8") as f:
        f.write(line)
    return line


def main(argv):
    if len(argv) < 2 or argv[1] not in ("snapshot", "check"):
        print(__doc__)
        return 1
    return snapshot() if argv[1] == "snapshot" else check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
