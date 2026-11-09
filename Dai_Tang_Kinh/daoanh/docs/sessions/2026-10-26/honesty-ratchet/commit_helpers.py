"""Helper cho commit thủ công trên máy Windows (AGENTS §14/§17).

Dùng:
  python commit_helpers.py cas <ref_file> <parent> <new>   # CAS thủ công, ghi tại chỗ
  python commit_helpers.py backup <src> <dst>              # sao lưu byte
  python commit_helpers.py sync <tmp_index> <real_index>   # ghi byte index tạm vào index thật

Không dùng os.replace / git update-ref (xem AGENTS §17: CAS của update-ref không ổn trên máy này).
"""
import shutil
import sys


def cas(ref, parent, new):
    with open(ref, encoding="utf-8") as f:
        cur = f.read().strip()
    if cur != parent:
        print("CAS FAIL: ref=%s hien_tai=%s ky_vong=%s" % (ref, cur, parent))
        return 3
    with open(ref, "w", encoding="utf-8", newline="\n") as f:   # ghi tại chỗ, LF như git
        f.write(new + "\n")
    print("CAS OK: %s %s -> %s" % (ref, parent, new))
    return 0


def sync(tmp, real):
    with open(tmp, "rb") as f:
        data = f.read()
    with open(real, "r+b") as f:                               # ghi tại chỗ (chỉ cần quyền Write)
        f.write(data)
        f.truncate()
    print("SYNC index: %d bytes -> %s" % (len(data), real))
    return 0


def main(argv):
    if len(argv) >= 5 and argv[1] == "cas":
        return cas(argv[2], argv[3], argv[4])
    if len(argv) >= 4 and argv[1] == "backup":
        shutil.copy2(argv[2], argv[3])
        print("BACKUP OK: %s -> %s" % (argv[2], argv[3]))
        return 0
    if len(argv) >= 4 and argv[1] == "sync":
        return sync(argv[2], argv[3])
    print("usage: see docstring")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
