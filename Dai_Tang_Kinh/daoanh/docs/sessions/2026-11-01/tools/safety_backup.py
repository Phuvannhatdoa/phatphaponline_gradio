"""Sao lưu an toàn ra ổ D (ngoài repo, ngoài git) — chạy theo giờ.

- lineage.db: sqlite backup API (nhất quán, không copy file thô), PRAGMA quick_check,
  ghi sha256 vào manifest. Giữ 24 bản gần nhất.
- Các file lớn trong data/ (>5MB) và các file ignored quan trọng: copy khi mtime/size đổi.
- Không ghi gì vào repo. Không xóa gì ngoài việc tỉa bản DB cũ đã vượt quá 24 bản.
"""
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path

REPO_DATA = Path("E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data")
DEST = Path("D:/DaoAnh-Backup")
DB = REPO_DATA / "lineage.db"
KEEP_DB = 24
BIG = 5 * 1024 * 1024


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def backup_db(stamp):
    d = DEST / "db"
    d.mkdir(parents=True, exist_ok=True)
    dst = d / f"lineage-{stamp}.db"
    src = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    out = sqlite3.connect(dst)
    try:
        src.backup(out)
    finally:
        out.close()
        src.close()
    chk = sqlite3.connect(dst).execute("PRAGMA quick_check").fetchone()[0]
    if chk != "ok":
        dst.unlink()
        raise RuntimeError(f"quick_check lỗi: {chk}")
    digest = sha256(dst)
    with open(d / "manifest.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"file": dst.name, "sha256": digest, "bytes": dst.stat().st_size,
                            "at": stamp}) + "\n")
    kept = sorted(d.glob("lineage-*.db"))
    for old in kept[:-KEEP_DB]:
        old.unlink()
    return dst.name, digest


def backup_big_files(stamp):
    state_path = DEST / "big-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    copied = []
    for p in REPO_DATA.rglob("*"):
        if not p.is_file() or p.stat().st_size <= BIG:
            continue
        key = str(p.relative_to(REPO_DATA)).replace("\\", "/")
        sig = f"{p.stat().st_size}:{int(p.stat().st_mtime)}"
        if state.get(key) == sig:
            continue
        dst = DEST / "data" / key
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        if sha256(p) != sha256(dst):
            raise RuntimeError(f"mã băm lệch: {key}")
        state[key] = sig
        copied.append(key)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return copied


def main():
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    name, digest = backup_db(stamp)
    copied = backup_big_files(stamp)
    print(f"DB: {name} sha256={digest[:16]}… | file lớn mới/đổi: {len(copied)}")


if __name__ == "__main__":
    main()
