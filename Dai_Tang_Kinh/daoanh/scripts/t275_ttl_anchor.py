"""
T275 — Neo số đời lấy từ TTL (generationOrder + hasTeacher/hasDisciple).

Ý tưởng "vô não" trước: mỗi file TTL của một vị đã ghi sẵn số đời (generationOrder)
và thầy/đệ tử trực tiếp. Nếu cạnh thầy→đệ có số đời thì đệ = thầy + 1.
Script này:
  1. Đọc TTL (chỉ đọc), lấy số đời + quan hệ thầy-trò trực tiếp.
  2. Kiểm tra mỗi cạnh: đệ có đúng bằng thầy + 1 không.
  3. Xuất TSV dẫn xuất (không ghi DB) để Admin xem các cạnh lệch.
  4. Có hàm tra cứu: từ một vị, đi lên tới gốc và xuống, trả về số đời.

Chỉ GHI: docs/evidence/2026-10-10_T275_ttl_anchor_edges.tsv
Không đụng DB, không đụng TTL.

Chạy (ở thư mục daoanh/):
    python -X utf8 scripts/t275_ttl_anchor.py                 # xuất TSV + thống kê
    python -X utf8 scripts/t275_ttl_anchor.py --chain bon_qua_khoang_vien
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # daoanh/
TTL_DIR = ROOT / "data" / "ttl"
OUT = ROOT / "docs" / "evidence" / "2026-10-10_T275_ttl_anchor_edges.tsv"

RE_SUBJECT = re.compile(r"<ex:monk/([^>]+)>\s+a\s+<?bkg:Monk>?")
RE_GEN = re.compile(r"bkg:generationOrder\s+(\d+)")
RE_TEACHER = re.compile(r"bkg:hasTeacher\s+([^;.]+)")
RE_DISCIPLE = re.compile(r"bkg:hasDisciple\s+([^;.]+)")
RE_ID = re.compile(r"<ex:monk/([^>]+)>")
RE_LABEL_VI = re.compile(r'<ex:monk/([^>]+)>\s+rdfs:label\s+"([^"]+)"@vi')
RE_DHARMA_LINEAGE = re.compile(r'bkg:dharmaLineageName\s+"([^"]+)"@vi')


def read_file(path):
    """Đọc một file TTL; trả về (slug chủ thể, số đời, thầy, đệ tử, nhãn, hệ truyền thừa)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as ex:
        print(f"[CẢNH BÁO] Không đọc được {path.name}: {ex}", file=sys.stderr)
        return None
    m = RE_SUBJECT.search(text)
    if not m:
        return None
    slug = m.group(1)
    gen = RE_GEN.search(text)
    teachers = RE_ID.findall(RE_TEACHER.search(text).group(1)) if RE_TEACHER.search(text) else []
    disciples = RE_ID.findall(RE_DISCIPLE.search(text).group(1)) if RE_DISCIPLE.search(text) else []
    label = None
    for lm in RE_LABEL_VI.finditer(text):
        if lm.group(1) == slug:
            label = lm.group(2)
            break
    lineage_match = RE_DHARMA_LINEAGE.search(text)
    dharma_lineage = lineage_match.group(1) if lineage_match else None
    return {
        "slug": slug,
        "gen": int(gen.group(1)) if gen else None,
        "teachers": teachers,
        "disciples": disciples,
        "label": label or slug,
        "file": path.name,
        "dharma_lineage": dharma_lineage,
    }


def load_all():
    """Đọc toàn bộ TTL (không nạp tất cả vào RAM cùng lúc: mỗi file một lần)."""
    monks = {}
    try:
        for path in sorted(TTL_DIR.glob("*.ttl")):
            rec = read_file(path)
            if rec is None:
                continue
            # Giữ bản đầu tiên nếu một slug xuất hiện ở nhiều file; ghi nhận xung đột.
            if rec["slug"] in monks:
                print(f"[CẢNH BÁO] Trùng slug {rec['slug']} ở {rec['file']}; giữ bản đầu.", file=sys.stderr)
                continue
            monks[rec["slug"]] = rec
    except FileNotFoundError:
        print(f"[LỖI] Không thấy thư mục TTL: {TTL_DIR}", file=sys.stderr)
        sys.exit(1)
    return monks


def check_edges(monks):
    """Mỗi cạnh thầy→đệ: đệ phải = thầy + 1 khi cả hai có số đời."""
    rows = []
    for slug, rec in monks.items():
        for disc in rec["disciples"]:
            d = monks.get(disc)
            status, note = _judge(rec["gen"], d["gen"] if d else None, d is not None)
            rows.append({
                "teacher": slug, "teacher_label": rec["label"], "teacher_gen": rec["gen"] or "",
                "teacher_lineage": rec["dharma_lineage"] or "",
                "disciple": disc, "disciple_label": d["label"] if d else disc,
                "disciple_gen": (d["gen"] if d and d["gen"] is not None else ""),
                "disciple_lineage": d["dharma_lineage"] if d else "",
                "status": status, "note": note,
            })
    return rows


def _judge(t_gen, d_gen, d_known):
    if t_gen is None or d_gen is None:
        if not d_known:
            return "thiếu_file_đệ_tử", "Đệ tử không có file TTL riêng trong thư mục."
        return "thiếu_số_đời", "Một trong hai không có generationOrder."
    if d_gen == t_gen + 1:
        return "khớp", ""
    return "lệch", f"đệ={d_gen}, thầy+1={t_gen + 1}"


def chain(monks, slug):
    """Đi lên theo hasTeacher tới gốc (chặn chu trình), rồi xuống theo hasDisciple."""
    if slug not in monks:
        return None
    up, seen, cur = [], set(), slug
    while cur in monks and cur not in seen:
        seen.add(cur)
        up.append(cur)
        ts = monks[cur]["teachers"]
        if not ts:
            break
        cur = ts[0]
    down = []
    cur = slug
    seen2 = {slug}
    while True:
        ds = [d for d in monks.get(cur, {}).get("disciples", []) if d not in seen2]
        if not ds:
            break
        cur = ds[0]
        seen2.add(cur)
        down.append(cur)
    return list(reversed(up)), down


LINES_OUT = ROOT / "docs" / "evidence" / "2026-10-10_T275_ttl_lines.tsv"


def export_lines(monks):
    """Mỗi vị một dòng: đường từ gốc tới vị đó, số đời TTL và độ sâu từ gốc.

    Độ sâu = số bậc từ gốc (gốc = 0). Đường ghi bằng slug để không lẫn tên.
    """
    rows = []
    for slug, rec in monks.items():
        path, cur, seen = [], slug, set()
        while cur in monks and cur not in seen:
            seen.add(cur)
            path.append(cur)
            ts = monks[cur]["teachers"]
            if not ts:
                break
            cur = ts[0]
        path.reverse()
        root = path[0]
        depth = len(path) - 1
        gen_root = monks[root]["gen"]
        rows.append({
            "vi": slug,
            "label": rec["label"],
            "gen_ttl": rec["gen"] if rec["gen"] is not None else "",
            "dharma_lineage": rec["dharma_lineage"] or "",
            "goc": root,
            "do_sau": depth,
            "gen_goc": gen_root if gen_root is not None else "",
            "chenh": (rec["gen"] - gen_root - depth) if (rec["gen"] is not None and gen_root is not None) else "",
            "duong": " → ".join(path),
        })
    return rows


def _fmt(monks, slug):
    rec = monks.get(slug)
    if not rec:
        return f"{slug} (không có file)"
    return f"{rec['label']} [đời {rec['gen'] if rec['gen'] is not None else '?'}]"


def main():
    ap = argparse.ArgumentParser(description="T275: neo số đời từ TTL")
    ap.add_argument("--chain", help="slug vị cần tra (ví dụ bon_qua_khoang_vien)")
    ap.add_argument("--lines", action="store_true", help="xuất đường truyền của mọi vị ra TSV")
    args = ap.parse_args()

    monks = load_all()
    print(f"Đã đọc {len(monks)} vị có khai báo bkg:Monk trong TTL.")

    if args.lines:
        rows = export_lines(monks)
        with LINES_OUT.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(rows)
        lech = sum(1 for r in rows if r["chenh"] not in ("", 0))
        print(f"Đã xuất {len(rows)} dòng đường truyền -> {LINES_OUT}")
        print(f"Vị có số đời TTL lệch với độ sâu từ gốc: {lech}")
        return 0

    if args.chain:
        res = chain(monks, args.chain)
        if res is None:
            print(f"Không tìm thấy vị '{args.chain}' trong TTL.")
            return 1
        up, down = res
        print("Đường lên: " + " → ".join(_fmt(monks, s) for s in up))
        print("Đường xuống: " + " → ".join(_fmt(monks, s) for s in down) if down else "Không có đệ tử trực tiếp.")
        return 0

    rows = check_edges(monks)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["teacher"], delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    stat = {}
    for r in rows:
        stat[r["status"]] = stat.get(r["status"], 0) + 1
    print(f"Tổng cạnh thầy→đệ: {len(rows)}")
    for k, v in sorted(stat.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"Đã ghi: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
