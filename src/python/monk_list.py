#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from rdflib import Graph, Namespace, URIRef

# ===============================
# CONFIG
# ===============================
TTL_DIR = "/opt/phatphaponline_gradio/2000_Files/ttl_output/reorganize_ttl"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/monk_list.json"

BKG = Namespace("http://www.phatphaponline.org/ontology/buddhist-kg#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

# ===============================
# MAIN
# ===============================
def extract_monk_labels():
    monks = []

    if not os.path.isdir(TTL_DIR):
        print(f"[ERROR] Không tìm thấy thư mục: {TTL_DIR}")
        return

    ttl_files = [f for f in os.listdir(TTL_DIR) if f.endswith(".ttl")]
    print(f"[INFO] Tìm thấy {len(ttl_files)} file TTL.")

    for tt in ttl_files:
        fpath = os.path.join(TTL_DIR, tt)

        try:
            g = Graph()
            g.parse(fpath, format="turtle")

            for s in g.subjects(RDFS.label, None):
                label = str(g.value(s, RDFS.label))
                if label:
                    monks.append({
                        "id": str(s),
                        "label": label.strip()
                    })

        except Exception as e:
            print(f"[ERROR] Lỗi đọc file {tt}: {e}")

    # Loại bỏ trùng lặp theo URI
    unique = {}
    for m in monks:
        unique[m["id"]] = m

    monks = list(unique.values())
    monks.sort(key=lambda x: x["label"])

    # Xuất JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(monks, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Đã xuất {len(monks)} thiền sư vào file: {OUTPUT_JSON}")


if __name__ == "__main__":
    extract_monk_labels()
