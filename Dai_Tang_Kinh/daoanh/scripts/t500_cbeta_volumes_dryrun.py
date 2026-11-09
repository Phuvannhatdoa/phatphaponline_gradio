"""T500 — ETL dry-run quan hệ quyển từ snapshot CBETA Catalog API (chỉ đọc, không ghi DB).

Đầu vào:
  data/dila_import/cbeta_catalog_api/2026-10-29/catalog_entry_raw.json   (snapshot, offline)
  data/lineage.db  (bảng dila_catalog_works, mở chế độ read-only)

Đầu ra (docs/sessions/2026-10-29/cbeta-volumes/):
  work_volumes_dryrun.csv   dòng quyển sinh từ node tác phẩm (work_id, juan_no, cbeta_node_n,
                            file_id, source_snapshot)
  alias_dryrun.csv          node alt và các mã tương đương "(=...)" có trong DB
  errors_dryrun.csv         lỗi và lệch cần Admin xem (không tự sửa)
  dryrun_summary.json       số liệu tổng hợp

Quy tắc (theo tasks/T500):
  - Node có trường `work` và node_type='work': sinh đúng juan_end - juan_start + 1 dòng.
  - Node alt: không sinh quyển; chỉ ghi vào alias_dryrun.csv.
  - Node thiếu juan_start/juan_end: ghi errors, không đoán.
  - Kiểm chéo: tổng quyển từ node so với dila_catalog_works.juans; lệch thì ghi errors.
"""
import csv
import json
import pathlib
import re
import sqlite3
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "data" / "dila_import" / "cbeta_catalog_api" / "2026-10-29"
RAW = SNAP_DIR / "catalog_entry_raw.json"
DB = ROOT / "data" / "lineage.db"
OUT = ROOT / "docs" / "sessions" / "2026-10-29" / "cbeta-volumes"
SNAPSHOT_TAG = "cbeta_catalog_api/2026-10-29"

ID_TOKEN = re.compile(r"^[A-Za-z]{1,3}\d{3,4}[A-Za-z]?$")
EQUIV = re.compile(r"^([A-Za-z]{1,3}\d{3,4}[A-Za-z]?)\(=([^)]*)\)")
# Nhãn có số quyển dạng "(60卷)" khi API không trả juan_end (phần lớn node).
COUNT_LABEL = re.compile(r"\((\d+)卷\)")


def node_juan_range(node):
    """Trả (start, end, nguồn). Ưu tiên juan_start/juan_end của API; thiếu end thì đọc nhãn."""
    js, je = node.get("juan_start"), node.get("juan_end")
    if js is not None and je is not None:
        return js, je, "api_range"
    m = COUNT_LABEL.search(node.get("label") or "")
    if js is not None and m:
        n = int(m.group(1))
        return js, js + n - 1, "label_count"
    return None, None, "thiếu"


def load_nodes():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    nodes = {}
    for resp in raw.values():
        for r in resp.get("results", []) or []:
            if r.get("n"):
                nodes[r["n"]] = r
    return nodes


def load_db_works():
    uri = DB.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        return {cid: juans for cid, juans in con.execute(
            "SELECT cbeta_id, juans FROM dila_catalog_works")}
    finally:
        con.close()


def main():
    nodes = load_nodes()
    db = load_db_works()

    work_nodes = defaultdict(list)
    alt_nodes = []
    for r in nodes.values():
        if r.get("node_type") == "work" and r.get("work"):
            work_nodes[r["work"]].append(r)
        elif r.get("node_type") == "alt":
            alt_nodes.append(r)

    volume_rows, errors = [], []
    per_work_total = {}

    for wid in db:
        nlist = work_nodes.get(wid, [])
        if not nlist:
            continue
        # Cùng một tác phẩm có thể nằm ở nhiều nhánh cây (ví dụ orig-T.005.001 và các node chia nhỏ).
        # Gộp theo tập số quyển (union), không cộng dồn từng node.
        juan_files = defaultdict(set)   # juan_no -> {file}
        juan_node = {}                  # juan_no -> (node_n, nguồn) của node đầu tiên
        for node in nlist:
            js, je, source = node_juan_range(node)
            if js is None:
                errors.append([wid, node["n"], "node_thiếu_juan", "", ""])
                continue
            if je < js:
                errors.append([wid, node["n"], "juan_end_nhỏ_hơn_start", js, je])
                continue
            for j in range(js, je + 1):
                juan_files[j].add(node.get("file", ""))
                juan_node.setdefault(j, (node["n"], source))
        for j in sorted(juan_files):
            files = sorted(juan_files[j])
            if len(files) > 1:
                errors.append([wid, juan_node[j][0], "file_xung_đột", j, "|".join(files)])
            node_n, source = juan_node[j]
            volume_rows.append([wid, j, node_n, "|".join(files), source, SNAPSHOT_TAG])
        total = len(juan_files)
        per_work_total[wid] = total
        db_juans = db[wid]
        if db_juans is None:
            errors.append([wid, "", "juans_db_null", total, ""])
        elif db_juans != total:
            errors.append([wid, "", "lệch_juans_db_vs_api", db_juans, total])

    # Alt: tìm mã tương đương trong DB
    alias_rows = []
    alt_unparsed = 0
    alt_with_db = set()
    for node in alt_nodes:
        m = EQUIV.match(node.get("label") or "")
        if not m:
            alt_unparsed += 1
            continue
        own, eq = m.group(1), m.group(2)
        tokens = [t for t in re.split(r"[+]", eq) if ID_TOKEN.match(t)]
        for tok in tokens:
            if tok in db:
                alias_rows.append([tok, own, node["n"], "alt:(=...) tương đương trong DB"])
                alt_with_db.add(node["n"])

    works_without_node = [cid for cid in db if cid not in work_nodes]
    no_node_reason = Counter()
    alt_ids = set()
    for node in alt_nodes:
        m = EQUIV.match(node.get("label") or "")
        if m:
            alt_ids.add(m.group(1))
    for cid in works_without_node:
        no_node_reason["có node alt" if cid in alt_ids else "không có node nào"] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "work_volumes_dryrun.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["work_id", "juan_no", "cbeta_node_n", "file_id", "juan_source", "source_snapshot"])
        w.writerows(volume_rows)
    with open(OUT / "alias_dryrun.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["work_id_db", "alt_code", "alt_node_n", "note"])
        w.writerows(alias_rows)
    with open(OUT / "errors_dryrun.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["work_id", "node_n", "loại_lỗi", "giá_trị_1", "giá_trị_2"])
        w.writerows(errors)

    # Đếm số dòng nếu gom theo khoảng liên tục (cùng file, cùng nguồn) — chỉ để so sánh, không ghi.
    range_rows = 0
    by_work = defaultdict(list)
    for wid, j, node_n, file_id, source, _snap in volume_rows:
        by_work[wid].append((j, file_id, source))
    for items in by_work.values():
        items.sort()
        prev = None
        for j, file_id, source in items:
            if prev is None or j != prev[0] + 1 or (file_id, source) != (prev[1], prev[2]):
                range_rows += 1
            prev = (j, file_id, source)

    mismatch = sum(1 for e in errors if e[2] == "lệch_juans_db_vs_api")
    summary = {
        "db_works": len(db),
        "works_with_work_node": len([c for c in db if c in work_nodes]),
        "works_without_work_node": len(works_without_node),
        "works_without_work_node_breakdown": dict(no_node_reason),
        "volume_rows": len(volume_rows),
        "volume_rows_if_grouped_by_range": range_rows,
        "alias_rows_in_db": len(alias_rows),
        "alt_nodes_total": len(alt_nodes),
        "alt_nodes_unparsed": alt_unparsed,
        "alt_nodes_with_db_equivalent": len(alt_with_db),
        "juans_mismatch_works": mismatch,
        "error_count": len(errors),
        "error_types": dict(Counter(e[2] for e in errors)),
    }
    (OUT / "dryrun_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
