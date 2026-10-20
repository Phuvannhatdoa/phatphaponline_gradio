# -*- coding: utf-8 -*-
"""T274 Bước 2: Dry-run export (chỉ đọc DB mode=ro, KHÔNG ghi DB).

Đọc data/dharma_edges.json (đã sinh bởi scripts/t270_label_edges.py sau khi thêm
nhánh T274) và xuất docs/evidence/2026-10-10_T274_vn_dry_run.tsv gồm:
  - Thống kê số cạnh mỗi nhóm nhãn.
  - Toàn bộ cạnh 'noi_phap_ttl_only' (quy tắc T274 mới).
  - Toàn bộ cạnh 'mo_ho' (cần Admin rà soát, kể cả cạnh mà Marcus thiếu bản ghi).
  - Ước lượng thô số cạnh thuộc dòng Việt Nam: đối chiếu people.dynasty của
    teacher/disciple có chứa chuỗi '越南' (Việt Nam) literal. Đây CHỈ là ước lượng
    (lower-bound, không suy diễn qua '陳'/'黎'/'阮'/'李' vì các chữ Hán này trùng
    với tên triều đại Trung Quốc) — không dùng để merge identity hay quyết định tự động.
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "lineage.db")
DHARMA_PATH = os.path.join(ROOT, "data", "dharma_edges.json")
OUT_PATH = os.path.join(ROOT, "docs", "evidence", "2026-10-10_T274_vn_dry_run.tsv")


def main():
    with open(DHARMA_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    vn_dynasty_ids = set()
    for r in conn.execute("SELECT id FROM people WHERE dynasty LIKE '%越南%'"):
        vn_dynasty_ids.add(r["id"])
    print(f"[T274 dry-run] Số người có dynasty chứa '越南' (ước lượng VN, literal only): {len(vn_dynasty_ids)}")

    ttl_only = [e for e in d["edges"] if e.get("label") == "noi_phap_ttl_only"]
    mo_ho = d.get("review_mo_ho", [])

    def vn_flag(e):
        return (e.get("teacher_id") in vn_dynasty_ids) or (e.get("disciple_id") in vn_dynasty_ids)

    n_ttl_only_vn = sum(1 for e in ttl_only if vn_flag(e))
    n_mo_ho_vn = sum(1 for e in mo_ho if vn_flag(e))
    n_mo_ho_no_marcus = sum(1 for e in mo_ho if not e.get("marcus_confirmed"))

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("# T274 dry-run — docs/evidence/2026-10-10_T274_vn_dry_run.tsv\n")
        f.write("# Nguồn: data/dharma_edges.json (scripts/t270_label_edges.py sau khi thêm nhánh T274)\n")
        f.write("# KHÔNG ghi DB. Ước lượng 'dòng Việt Nam' chỉ dựa trên people.dynasty chứa literal '越南' (lower-bound).\n")
        f.write("#\n")
        f.write("# === THỐNG KÊ TỔNG ===\n")
        f.write(f"# n_dila_edges_total\t{d['n_dila_edges_total']}\n")
        f.write(f"# n_noi_phap (TTL+Marcus)\t{d['n_noi_phap']}\n")
        f.write(f"# n_noi_phap_ttl_only (T274, TTL-only khi Marcus thiếu)\t{d['n_noi_phap_ttl_only']}\n")
        f.write(f"# n_tham_hoc\t{d['n_tham_hoc']}\n")
        f.write(f"# n_khong_ghep_duoc\t{d['n_khong_ghep_duoc']}\n")
        f.write(f"# n_mo_ho (cần Admin rà soát)\t{d['n_mo_ho']}\n")
        f.write(f"# n_mo_ho ma Marcus khong co ban ghi (trong so n_mo_ho tren)\t{n_mo_ho_no_marcus}\n")
        f.write(f"# Uoc luong VN trong noi_phap_ttl_only (dynasty chua '越南')\t{n_ttl_only_vn} / {len(ttl_only)}\n")
        f.write(f"# Uoc luong VN trong mo_ho (dynasty chua '越南')\t{n_mo_ho_vn} / {len(mo_ho)}\n")
        f.write("#\n")
        f.write("# === NHOM 1: noi_phap_ttl_only (nhan moi theo T274) ===\n")
        f.write("group\tteacher_id\tteacher_name_vi\tdisciple_id\tdisciple_name_vi\tdila_edge_id\tdila_citation\tttl_match_mode\tvn_guess\n")
        for e in ttl_only:
            f.write(
                "noi_phap_ttl_only\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    e.get("teacher_id"), e.get("teacher_name_vi"),
                    e.get("disciple_id"), e.get("disciple_name_vi"),
                    e.get("dila_edge_id"), (e.get("dila_citation") or "").replace("\t", " "),
                    (e.get("ttl_match") or {}).get("match_mode") if isinstance(e.get("ttl_match"), dict) else e.get("ttl_match"),
                    "VN" if vn_flag(e) else "",
                )
            )
        f.write("#\n")
        f.write("# === NHOM 2: mo_ho (can Admin ra soat — bao gom ca canh Marcus thieu ban ghi) ===\n")
        f.write("group\tteacher_id\tteacher_name_vi\tdisciple_id\tdisciple_name_vi\tdila_edge_id\tdila_citation\treason\tmarcus_confirmed\tvn_guess\n")
        for e in mo_ho:
            f.write(
                "mo_ho\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    e.get("teacher_id"), e.get("teacher_name_vi"),
                    e.get("disciple_id"), e.get("disciple_name_vi"),
                    e.get("dila_edge_id"), (e.get("dila_citation") or "").replace("\t", " "),
                    (e.get("reason") or "").replace("\t", " "),
                    e.get("marcus_confirmed"),
                    "VN" if vn_flag(e) else "",
                )
            )

    print(f"[T274 dry-run] Ghi: {OUT_PATH}")
    print(f"[T274 dry-run] noi_phap_ttl_only: {len(ttl_only)} (VN uoc luong: {n_ttl_only_vn})")
    print(f"[T274 dry-run] mo_ho: {len(mo_ho)} (Marcus thieu ban ghi: {n_mo_ho_no_marcus}; VN uoc luong: {n_mo_ho_vn})")


if __name__ == "__main__":
    main()
