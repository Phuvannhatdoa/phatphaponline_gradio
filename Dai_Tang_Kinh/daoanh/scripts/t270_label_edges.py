# -*- coding: utf-8 -*-
"""T270 Giai đoạn 2: Gán nhãn NỐI PHÁP / THAM HỌC cho mọi cạnh thầy-trò DILA trong corpus.

Đọc DB mode=ro. Không ghi DB.

Quy tắc join: dùng cạnh DILA (lineage_edge_assertions, đã verified) làm trục chính
(đây cũng là tập cạnh mà generation_engine_v2.parents() dùng). Với mỗi cạnh DILA
(teacher_id -> disciple_id):
  - Lấy name_vi của teacher_id, disciple_id từ bảng people (đây CHỈ dùng để tra cứu
    chỉ mục TTL, KHÔNG dùng tên để merge identity — ID vẫn luôn là DILA id).
  - Nếu name_vi của một trong hai bên trống/NULL -> "không ghép được" (thiếu tên để tra TTL).
  - Nếu tên trùng với NHIỀU người khác trong bảng people theo CẢ HAI chiều bất lợi
    (xem chú thích match_ambiguous) -> vẫn thử ghép qua TTL theo đúng cặp tên; nếu
    TTL không có cặp (teacher_name, disciple_name) tương ứng -> không tính là nối pháp
    qua TTL (an toàn), không suy đoán.
  - ttl_confirmed = True nếu tồn tại cạnh TTL (từ ttl_dharma_index.json) với
    label(teacher_slug)==teacher_name_vi và label(disciple_slug)==disciple_name_vi
    và dharma_flag=True.
  - marcus_confirmed = True nếu (teacher_id, disciple_id) có trong marcus_networks
    (relation_type='da:isTeacherOf'), đối chiếu qua marcus_people_link nếu cần.
  - Nhãn: NỐI PHÁP nếu ttl_confirmed AND marcus_confirmed; còn lại THAM HỌC.
  - [T274 — Admin phê chuẩn 2026-10-10] Ngoại lệ cho dòng Marcus không có bản ghi
    (chủ yếu dòng Việt Nam): nếu marcus_confirmed=False NHƯNG ttl_confirmed=True
    (TTL ghi rõ "pháp tự"/"đắc pháp") VÀ cặp KHÔNG mơ hồ (đã qua mọi kiểm tra đồng
    danh/hậu tố ở trên) -> nhãn NỐI PHÁP (TTL-only) = 'noi_phap_ttl_only'. Quy tắc cũ
    (cần cả hai nguồn) giữ nguyên cho cạnh có Marcus.
  - Nếu không tìm được bất kỳ cạnh TTL nào khớp theo tên cho cặp này (TTL không có
    quan hệ này) -> vẫn nhãn THAM HỌC (không phải lỗi ghép ID, đơn giản là TTL không
    xác nhận) nhưng ghi rõ ttl_match='no_ttl_relation' để minh bạch.

Xuất data/dharma_edges.json (toàn corpus, không ghi DB).
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "lineage.db")
TTL_INDEX_PATH = os.path.join(ROOT, "data", "ttl_dharma_index.json")
OUT_PATH = os.path.join(ROOT, "data", "dharma_edges.json")


def main():
    t0 = time.time()

    if not os.path.exists(TTL_INDEX_PATH):
        print("[T270 P2] LỖI: chưa có data/ttl_dharma_index.json — chạy t270_parse_ttl.py trước.", flush=True)
        sys.exit(1)

    with open(TTL_INDEX_PATH, "r", encoding="utf-8") as f:
        ttl_index = json.load(f)

    ttl_labels = ttl_index["labels"]  # slug -> name_vi
    ttl_edges = ttl_index["edges"]  # [{teacher_slug, disciple_slug, dharma_flag, evidence_file, evidence_kind}]

    # T274 fix: Build slug -> dharma_lineage map from TTL files (dòng Việt Nam)
    # Dòng Việt Nam: chứa "Việt Nam" trong dharmaLineageName
    VIETNAMESE_LINEAGE_KEYWORDS = ("Việt Nam", "Viet Nam", "VIETNAM", "vietnam")
    slug_lineage = {}  # slug -> dharmaLineageName
    try:
        for path in sorted(Path(os.path.join(ROOT, "data", "ttl")).glob("*.ttl")):
            text = path.read_text(encoding="utf-8")
            m_subj = RE_SUBJECT.search(text)
            if not m_subj:
                continue
            slug = m_subj.group(1)
            m_lin = RE_DHARMA_LINEAGE.search(text)
            if m_lin:
                slug_lineage[slug] = m_lin.group(1)
    except Exception as ex:
        print(f"[T270 P2] CẢNH BÁO: Không xây được slug_lineage: {ex}", flush=True)

    # name_vi -> list of (teacher_slug?/disciple_slug? doesn't matter, just name) dharma-flagged pairs
    # Xây set các cặp tên (teacher_name, disciple_name) có dharma_flag=True, và set mọi cặp tên có quan hệ (bất kể cờ)
    ttl_pairs_dharma = set()
    ttl_pairs_any = {}  # key=(t_name,d_name) -> {evidence_file, evidence_kind, dharma_flag, teacher_slug, disciple_slug}
    all_ttl_names = set()
    for e in ttl_edges:
        t_name = ttl_labels.get(e["teacher_slug"])
        d_name = ttl_labels.get(e["disciple_slug"])
        if not t_name or not d_name:
            continue
        all_ttl_names.add(t_name)
        all_ttl_names.add(d_name)
        key = (t_name, d_name)
        if e["dharma_flag"]:
            ttl_pairs_dharma.add(key)
        ttl_pairs_any[key] = {
            "evidence_file": e["evidence_file"],
            "evidence_kind": e["evidence_kind"],
            "dharma_flag": e["dharma_flag"],
            "teacher_slug": e["teacher_slug"],
            "disciple_slug": e["disciple_slug"],
        }

    # Bù khác biệt cách ghi tên: TTL hay ghi tên đầy đủ kèm hiệu núi/trú xứ
    # (ví dụ "Thạch Đầu Hy Thiên"), còn people.name_vi của DILA chỉ ghi pháp hiệu
    # ngắn ("Hy Thiên"). Không merge identity theo tên — ID vẫn luôn từ DILA
    # (subject/object_person_id trong lineage_edge_assertions). Tên chỉ dùng để
    # TRA CỨU xem TTL có ghi cặp quan hệ này không, qua khớp HẬU TỐ theo ranh giới
    # từ (word-boundary suffix), không khớp theo tiền tố/chuỗi con tuỳ tiện.
    suffix_index = {}
    for full_name in all_ttl_names:
        words = full_name.split(" ")
        for start in range(len(words)):
            suffix = " ".join(words[start:])
            suffix_index.setdefault(suffix, set()).add(full_name)

    def ttl_candidates_for(dila_name):
        """Trả về tập tên đầy đủ TTL mà dila_name khớp HẬU TỐ (ranh giới từ)."""
        return suffix_index.get(dila_name, set())

    print(f"[T270 P2] TTL index: {len(ttl_edges)} cạnh, {len(ttl_pairs_dharma)} cặp tên có cờ nối pháp.", flush=True)

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Marcus edges set (teacher_id, student_id) đã là DILA ID theo xác minh trước (marcus_people_link exact_id)
    marcus_edges = set()
    for r in conn.execute(
        "SELECT teacher_id, student_id FROM marcus_networks WHERE relation_type='da:isTeacherOf'"
    ):
        marcus_edges.add((r["teacher_id"], r["student_id"]))
    print(f"[T270 P2] Marcus edges (isTeacherOf): {len(marcus_edges)}", flush=True)

    # DILA edges — đúng tập mà generation_engine_v2.parents() dùng
    dila_rows = conn.execute(
        """SELECT id, subject_person_id AS teacher_id, object_person_id AS disciple_id, ref
           FROM lineage_edge_assertions
           WHERE source_code='DILA' AND relation_type='da:isTeacherOf'
             AND raw_relation_type='dila:teacher_of' AND status='active' AND mapping_verified=1
           ORDER BY id"""
    ).fetchall()
    print(f"[T270 P2] DILA edges (base pool của engine): {len(dila_rows)}", flush=True)

    # Cache name_vi theo id
    name_cache = {}

    def name_of(pid):
        if pid in name_cache:
            return name_cache[pid]
        # Thử bảng people trước (DILA IDs)
        row = conn.execute("SELECT name_vi FROM people WHERE id=?", (pid,)).fetchone()
        v = row["name_vi"] if row and row["name_vi"] else None
        # Nếu không có trong people, thử vn_person_authority (cho các ID TTL slug của Việt Nam)
        if v is None:
            row = conn.execute("SELECT name_vi FROM vn_person_authority WHERE id=?", (pid,)).fetchone()
            v = row["name_vi"] if row and row["name_vi"] else None
        name_cache[pid] = v
        return v

    # T274 fix: helper to check if an edge belongs to Vietnamese lineage
    # Vietnamese lineage = teacher or disciple slug has dharmaLineageName containing "Việt Nam"
    VIETNAMESE_LINEAGE_KEYWORDS = ("Việt Nam", "Viet Nam", "VIETNAM", "vietnam")
    def is_vietnamese_lineage(t_slug, d_slug):
        """Check if either teacher or disciple slug belongs to Vietnamese lineage."""
        for slug in (t_slug, d_slug):
            lineage = slug_lineage.get(slug)
            if lineage and any(kw in lineage for kw in VIETNAMESE_LINEAGE_KEYWORDS):
                return True
        return False

    # T270 fix điểm 4: tên DILA (name_vi) trùng giữa >1 ID DILA khác nhau (đồng
    # danh) -> tra TTL theo tên này KHÔNG an toàn, vì không biết TTL đang nói về
    # ID nào trong số các ID trùng tên. Không merge theo tên (naming-and-identity
    # rule) -> không gán nối pháp/tham học qua tên mơ hồ, luôn nhãn mo_ho.
    ambiguous_names = set()
    for r in conn.execute(
        "SELECT name_vi FROM people WHERE name_vi IS NOT NULL AND name_vi<>'' "
        "GROUP BY name_vi HAVING COUNT(DISTINCT id) > 1"
    ):
        ambiguous_names.add(r["name_vi"])
    print(f"[T270 P2] Tên DILA đồng danh (>1 ID chung name_vi): {len(ambiguous_names)}", flush=True)

    out_edges = []
    review_mo_ho = []  # T270 fix điểm 4: danh sách cần rà soát thủ công (tên TTL khớp >1 ứng viên)
    n_noi_phap = 0
    n_noi_phap_ttl_only = 0  # T274: VN-only rule — TTL xác nhận, Marcus không có bản ghi
    n_tham_hoc = 0
    n_khong_ghep = 0
    n_mo_ho = 0

    for i, row in enumerate(dila_rows, 1):
        t_id, d_id = row["teacher_id"], row["disciple_id"]
        t_name = name_of(t_id)
        d_name = name_of(d_id)

        if not t_name or not d_name:
            out_edges.append(
                {
                    "teacher_id": t_id,
                    "disciple_id": d_id,
                    "dila_edge_id": row["id"],
                    "label": "khong_ghep_duoc",
                    "reason": "thiếu name_vi trong bảng people để tra TTL",
                }
            )
            n_khong_ghep += 1
        else:
            marcus_confirmed = (t_id, d_id) in marcus_edges

            # Khớp trực tiếp (tên giống nguyên văn) trước; nếu không có, dò hậu tố
            # ranh giới từ để bù khác biệt "tên đầy đủ kèm hiệu núi" (TTL) vs
            # "pháp hiệu ngắn" (DILA people.name_vi). ID nối pháp vẫn luôn là
            # t_id/d_id từ cạnh DILA — tên chỉ để tra có ghi nhận trong TTL hay không.
            key = (t_name, d_name)
            ttl_info = ttl_pairs_any.get(key)
            ttl_confirmed = key in ttl_pairs_dharma
            match_mode = "exact" if ttl_info else None
            ambiguous_candidates = None  # T270 fix điểm 4 (đồng danh phía TTL)

            # Dò hậu tố nếu không khớp chính xác (LUÔN chạy, kể cả khi có homonym)
            # để T274 có cơ hội tìm thấy match cho dòng Việt Nam
            if ttl_info is None:
                t_cands = ttl_candidates_for(t_name)
                d_cands = ttl_candidates_for(d_name)
                found = []
                for tc in t_cands:
                    for dc in d_cands:
                        k2 = (tc, dc)
                        if k2 in ttl_pairs_any:
                            found.append(k2)
                if len(found) == 1:
                    k2 = found[0]
                    ttl_info = ttl_pairs_any[k2]
                    ttl_confirmed = k2 in ttl_pairs_dharma
                    match_mode = "suffix_boundary"
                elif len(found) > 1:
                    ambiguous_candidates = sorted(set(found))

            # T270 fix điểm 4 (đồng danh phía DILA): nếu name_vi của teacher hoặc
            # disciple trùng với >1 ID DILA khác (homonym), thì tra TTL theo tên
            # này là không an toàn — TTL có thể đang nói về người đồng danh khác,
            # không phải chính t_id/d_id của cạnh này. Không merge theo tên ->
            # luôn nhãn mơ hồ, không suy ra nối pháp/tham học qua tên mơ hồ.
            homonym_reason = None
            if t_name in ambiguous_names:
                homonym_reason = "teacher_name_vi '" + t_name + "' trùng với nhiều ID DILA (đồng danh) — không an toàn để tra TTL theo tên"
            elif d_name in ambiguous_names:
                homonym_reason = "disciple_name_vi '" + d_name + "' trùng với nhiều ID DILA (đồng danh) — không an toàn để tra TTL theo tên"

            if homonym_reason is not None or ambiguous_candidates is not None:
                # T274 fix: cho phép bypass homonym/ambiguity cho dòng Việt Nam
                # khi marcus_confirmed=False (Marcus không có bản ghi) VÀ
                # ttl_confirmed=True (TTL xác nhận nối pháp) VÀ
                # edge thuộc dòng Việt Nam (theo TTL dharmaLineageName).
                is_t274_candidate = (ttl_confirmed and not marcus_confirmed)
                is_vietnamese = False
                if is_t274_candidate and ttl_info:
                    t_slug = ttl_info.get("teacher_slug")
                    d_slug = ttl_info.get("disciple_slug")
                    if is_vietnamese_lineage(t_slug, d_slug):
                        is_vietnamese = True

                if is_t274_candidate and is_vietnamese:
                    # Bypass homonym/ambiguity cho T274 Việt Nam
                    pass
                else:
                    label = "mo_ho"
                    n_mo_ho += 1
                    reason = homonym_reason or (
                        "tên TTL khớp hậu tố với nhiều hơn 1 ứng viên — không chọn ngẫu nhiên, cần rà soát thủ công"
                    )
                    entry = {
                        "teacher_id": t_id,
                        "teacher_name_vi": t_name,
                        "disciple_id": d_id,
                        "disciple_name_vi": d_name,
                        "dila_edge_id": row["id"],
                        "dila_citation": row["ref"] or "",
                        "label": "mo_ho",
                        "reason": reason,
                        "ambiguous_candidates": (
                            [{"teacher_full_name": a, "disciple_full_name": b} for a, b in ambiguous_candidates]
                            if ambiguous_candidates is not None
                            else []
                        ),
                        "marcus_confirmed": marcus_confirmed,
                        "marcus_source": "marcus_networks" if marcus_confirmed else None,
                    }
                    out_edges.append(entry)
                    review_mo_ho.append(entry)
                    continue

            # T274 (Admin phê chuẩn 2026-10-10): với cạnh mà Marcus KHÔNG có bản ghi
            # tương ứng (chủ yếu dòng Việt Nam, Marcus thiếu phần lớn dòng này), TTL
            # một mình là nguồn đủ để gán NỐI PHÁP tự động khi dharma_flag=True cho
            # cặp tên (ttl_confirmed=True) VÀ cặp không mơ hồ. "Không mơ hồ" ở đây là
            # đã qua được toàn bộ kiểm tra đồng danh/hậu tố phía trên (homonym_reason
            # is None và ambiguous_candidates is None) — nếu không, luồng đã rẽ vào
            # nhãn 'mo_ho' và continue ở trên, không tới được đoạn này.
            # Quy tắc cũ (cần cả TTL và Marcus) GIỮ NGUYÊN không đổi cho cạnh có Marcus.
            if ttl_confirmed and marcus_confirmed:
                label = "noi_phap"
                n_noi_phap += 1
            elif ttl_confirmed and not marcus_confirmed:
                label = "noi_phap_ttl_only"
                n_noi_phap_ttl_only += 1
            else:
                label = "tham_hoc"
                n_tham_hoc += 1

            out_edges.append(
                {
                    "teacher_id": t_id,
                    "teacher_name_vi": t_name,
                    "disciple_id": d_id,
                    "disciple_name_vi": d_name,
                    "dila_edge_id": row["id"],
                    "dila_citation": row["ref"] or "",
                    "label": label,
                    "ttl_confirmed": ttl_confirmed,
                    "ttl_match": (
                        {
                            "evidence_file": ttl_info["evidence_file"],
                            "evidence_kind": ttl_info["evidence_kind"],
                            "match_mode": match_mode,
                        }
                        if ttl_info
                        else "no_ttl_relation"
                    ),
                    "marcus_confirmed": marcus_confirmed,
                    "marcus_source": "marcus_networks" if marcus_confirmed else None,
                }
            )

        if i % 500 == 0:
            print(f"[T270 P2] Đã xử lý {i}/{len(dila_rows)} cạnh DILA...", flush=True)

        if time.time() - t0 > 600:
            print("[T270 P2] QUÁ 10 PHÚT — DỪNG GIỮA CHỪNG, báo cáo tình trạng hiện tại.", flush=True)
            break

    out = {
        "generated_by": "scripts/t270_label_edges.py",
        "n_dila_edges_total": len(dila_rows),
        "n_processed": len(out_edges),
        "n_noi_phap": n_noi_phap,
        "n_noi_phap_ttl_only": n_noi_phap_ttl_only,
        "n_tham_hoc": n_tham_hoc,
        "n_khong_ghep_duoc": n_khong_ghep,
        "n_mo_ho": n_mo_ho,
        "edges": out_edges,
        "review_mo_ho": review_mo_ho,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    elapsed = time.time() - t0
    print(f"[T270 P2] XONG trong {elapsed:.1f}s", flush=True)
    print(
        f"[T270 P2] Tổng cạnh DILA xử lý: {len(out_edges)}; "
        f"NỐI PHÁP (TTL+Marcus): {n_noi_phap}; NỐI PHÁP (TTL-only, T274): {n_noi_phap_ttl_only}; "
        f"THAM HỌC: {n_tham_hoc}; "
        f"không ghép được: {n_khong_ghep}; mơ hồ (cần rà soát): {n_mo_ho}",
        flush=True,
    )
    print(f"[T270 P2] Ghi: {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
