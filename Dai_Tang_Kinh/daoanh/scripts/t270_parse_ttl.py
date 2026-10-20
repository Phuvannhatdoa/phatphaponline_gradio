# -*- coding: utf-8 -*-
"""T270 Giai đoạn 1: Parse toàn bộ TTL một lần, xây chỉ mục cạnh thầy-trò + cờ nối pháp.

Chỉ đọc data/ttl/*.ttl. Không đọc DB, không ghi DB.
Xuất data/ttl_dharma_index.json.

Cờ nối pháp cho một cạnh (teacher_slug -> disciple_slug) được lấy từ FILE của
NGƯỜI TRÒ (disciple's own file), vì đó là nơi ghi "PHÁP TỰ của <thầy>" / "đắc pháp"
mô tả việc chính người trò này được truyền pháp từ thầy đó. Cạnh suy ra chỉ từ
hasDisciple (không có file riêng của người trò, hoặc file trò không xác nhận lại
quan hệ qua hasTeacher) được giữ cờ nối pháp = False (không có chứng cứ độc lập).

Chạy: python -X utf8 scripts/t270_parse_ttl.py
"""
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTL_DIR = os.path.join(ROOT, "data", "ttl")
OUT_PATH = os.path.join(ROOT, "data", "ttl_dharma_index.json")

# T270 fix điểm 5: tách STRICT (đủ rõ nghĩa một mình, giữ nguyên hành vi cũ) khỏi
# GENERIC (từ khóa chung, dễ chỉ là danh từ/tính từ mô tả chứ không khẳng định
# chính NGƯỜI NÀY nối pháp từ thầy nào — chỉ nhận khi câu có tên thầy đi kèm và
# không bị phủ định).
STRICT_DHARMA_MARKERS = [
    "PHÁP TỰ",
    "pháp tự",
    "đắc pháp",
    "ĐẮC PHÁP",
    "kế thừa dòng pháp",
    "KẾ THỪA DÒNG PHÁP",
    "kế thừa pháp",
    "truyền y bát",
    "truyền tâm pháp",
    "kế thừa tổ vị",
]

GENERIC_DHARMA_MARKERS = [
    "nối pháp",
    "NỐI PHÁP",
    "truyền pháp cho",
    "pháp tử",
]

NEGATION_WORDS = ["chẳng", "không"]

SLUG_RE = re.compile(r"<ex:monk/([a-zA-Z0-9_]+)>")
LABEL_RE = re.compile(r'<ex:monk/([a-zA-Z0-9_]+)>\s+rdfs:label\s+"([^"]*)"')
HAS_TEACHER_RE = re.compile(r"bkg:hasTeacher\s+((?:<ex:monk/[a-zA-Z0-9_]+>\s*,?\s*)+)", re.MULTILINE)
HAS_DISCIPLE_RE = re.compile(r"bkg:hasDisciple\s+((?:<ex:monk/[a-zA-Z0-9_]+>\s*,?\s*)+)", re.MULTILINE)
SUBJECT_RE = re.compile(r"^<ex:monk/([a-zA-Z0-9_]+)>\s+a\s+<bkg:Monk>", re.MULTILINE)

# Tách câu đơn giản (không cần NLP đầy đủ): ngắt theo dấu kết câu hoặc xuống
# dòng, đủ để khoanh vùng ngữ cảnh quanh một từ khóa chung.
_SENTENCE_SPLIT_RE = re.compile(r"[\.\n;]+")


def extract_slugs(block_text):
    return SLUG_RE.findall(block_text)


def split_sentences(text):
    return _SENTENCE_SPLIT_RE.split(text)


def has_strict_marker(text):
    return any(marker in text for marker in STRICT_DHARMA_MARKERS)


def has_generic_marker_with_teacher_context(text, teacher_names):
    """Từ khóa chung chỉ được tính là nối pháp khi câu chứa từ khóa đó CŨNG có
    tên một trong các thầy (hasTeacher) của chính record này, và câu đó không
    bị phủ định (chẳng/không). Không khớp được tên thầy -> không tính (an toàn,
    không suy đoán)."""
    names = [n for n in teacher_names if n and n.strip()]
    if not names:
        return False
    for sentence in split_sentences(text):
        if any(marker in sentence for marker in GENERIC_DHARMA_MARKERS):
            if any(neg in sentence for neg in NEGATION_WORDS):
                continue
            if any(name in sentence for name in names):
                return True
    return False


def has_dharma_marker(text, teacher_names=()):
    if has_strict_marker(text):
        return True
    return has_generic_marker_with_teacher_context(text, teacher_names)


def parse_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    labels = {}
    for m in LABEL_RE.finditer(text):
        slug, label = m.group(1), m.group(2)
        labels.setdefault(slug, label)

    subj_match = SUBJECT_RE.search(text)
    subject_slug = subj_match.group(1) if subj_match else None

    teacher_slugs = []
    tm = HAS_TEACHER_RE.search(text)
    if tm:
        teacher_slugs = extract_slugs(tm.group(1))

    disciple_slugs = []
    dm = HAS_DISCIPLE_RE.search(text)
    if dm:
        disciple_slugs = extract_slugs(dm.group(1))

    return {
        "subject_slug": subject_slug,
        "labels": labels,
        "teacher_slugs": teacher_slugs,
        "disciple_slugs": disciple_slugs,
        "text": text,
    }


def main():
    t0 = time.time()
    files = sorted(glob.glob(os.path.join(TTL_DIR, "*.ttl")))
    print(f"[T270 P1] Tổng file TTL: {len(files)}", flush=True)

    # Pass 1: đọc toàn bộ file một lần, dựng slug -> label TOÀN CỤC trước. Cần
    # thiết vì tên thầy (dùng để xét ngữ cảnh từ khóa chung ở Pass 2) thường chỉ
    # có rdfs:label trong FILE RIÊNG của chính người thầy đó, không phải trong
    # file của người trò đang xét.
    parsed_by_file = {}
    all_labels = {}
    errors = []
    for i, path in enumerate(files, 1):
        fname = os.path.basename(path)
        try:
            parsed_by_file[fname] = parse_file(path)
        except Exception as ex:
            errors.append({"file": fname, "error": str(ex)})
            continue
        all_labels.update(parsed_by_file[fname]["labels"])
        if i % 500 == 0:
            print(f"[T270 P1] (pass 1/2 - đọc & gom label) {i}/{len(files)} file...", flush=True)
        if time.time() - t0 > 300:
            print("[T270 P1] QUÁ 5 PHÚT ở pass 1 — DỪNG GIỮA CHỪNG, báo cáo tình trạng hiện tại.", flush=True)
            break

    edges = {}  # (teacher_slug, disciple_slug) -> dict
    n_dharma_files = 0
    n_edges_from_teacher = 0
    n_edges_from_disciple_list = 0
    n_flag_changed_vs_old = 0  # T270 fix điểm 5: số file mà cờ đổi so với logic cũ (không xét ngữ cảnh)

    for i, (fname, parsed) in enumerate(parsed_by_file.items(), 1):
        text = parsed["text"]
        teacher_names = [all_labels.get(s) for s in parsed["teacher_slugs"]]

        old_flag = any(marker in text for marker in STRICT_DHARMA_MARKERS + GENERIC_DHARMA_MARKERS)
        new_flag = has_dharma_marker(text, teacher_names)
        if old_flag != new_flag:
            n_flag_changed_vs_old += 1

        if new_flag:
            n_dharma_files += 1

        subject = parsed["subject_slug"]
        if subject:
            # hasTeacher: cạnh (teacher -> subject), cờ nối pháp lấy từ file của subject (người trò)
            for t_slug in parsed["teacher_slugs"]:
                key = (t_slug, subject)
                prev = edges.get(key)
                flag = new_flag
                if prev is None or (flag and not prev["dharma_flag"]):
                    edges[key] = {
                        "teacher_slug": t_slug,
                        "disciple_slug": subject,
                        "dharma_flag": flag,
                        "evidence_file": fname,
                        "evidence_kind": "hasTeacher_in_disciple_file",
                    }
                n_edges_from_teacher += 1

            # hasDisciple: cạnh (subject -> disciple), không có chứng cứ độc lập từ
            # file này riêng cho việc disciple có PHÁP TỰ hay không -> flag mặc định False
            # trừ khi cạnh đã được xác nhận ở trên qua hasTeacher của file disciple đó.
            for d_slug in parsed["disciple_slugs"]:
                key = (subject, d_slug)
                if key not in edges:
                    edges[key] = {
                        "teacher_slug": subject,
                        "disciple_slug": d_slug,
                        "dharma_flag": False,
                        "evidence_file": fname,
                        "evidence_kind": "hasDisciple_listing_only",
                    }
                n_edges_from_disciple_list += 1

        if i % 500 == 0:
            print(f"[T270 P1] (pass 2/2 - tính cờ nối pháp) {i}/{len(parsed_by_file)} file...", flush=True)

        if time.time() - t0 > 600:
            print("[T270 P1] QUÁ 10 PHÚT — DỪNG GIỮA CHỪNG, báo cáo tình trạng hiện tại.", flush=True)
            break

    edge_list = list(edges.values())
    n_dharma_edges = sum(1 for e in edge_list if e["dharma_flag"])

    out = {
        "generated_by": "scripts/t270_parse_ttl.py",
        "ttl_dir": TTL_DIR,
        "n_files": len(files),
        "n_files_parsed_ok": len(files) - len(errors),
        "n_files_with_dharma_marker": n_dharma_files,
        "n_files_flag_changed_vs_old_logic": n_flag_changed_vs_old,
        "n_edges_total": len(edge_list),
        "n_edges_dharma_flagged": n_dharma_edges,
        "n_edges_from_teacher_direction": n_edges_from_teacher,
        "n_edges_from_disciple_listing_direction": n_edges_from_disciple_list,
        "labels": all_labels,
        "edges": edge_list,
        "errors": errors,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    elapsed = time.time() - t0
    print(f"[T270 P1] XONG trong {elapsed:.1f}s", flush=True)
    print(f"[T270 P1] File TTL: {len(files)}; parse lỗi: {len(errors)}", flush=True)
    print(f"[T270 P1] Tổng cạnh: {len(edge_list)}; cạnh có cờ nối pháp (file-level marker): {n_dharma_edges}", flush=True)
    print(f"[T270 P1] Số file bị đổi cờ so với logic cũ (sau khi thêm điều kiện ngữ cảnh tên thầy + loại phủ định): {n_flag_changed_vs_old}", flush=True)
    print(f"[T270 P1] Ghi: {OUT_PATH}", flush=True)
    if errors:
        print(f"[T270 P1] Lỗi mẫu: {errors[:5]}", flush=True)


if __name__ == "__main__":
    main()
