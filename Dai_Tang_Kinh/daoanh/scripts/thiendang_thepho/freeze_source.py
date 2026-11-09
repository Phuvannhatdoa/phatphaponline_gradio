# -*- coding: utf-8 -*-
"""
T429 — Giai đoạn 1: Đóng băng nguồn CBETA X86n1601 (禪燈世譜).

CHỈ ĐỌC nguồn XML. Mọi output ghi vào research/thiendang-thepho/manifests/.
Không ghi DB, không sửa file nguồn, không gọi API.

Output:
  research/thiendang-thepho/manifests/source-manifest.json
  research/thiendang-thepho/manifests/source-header.xml   (trích verbatim <teiHeader>)
  research/thiendang-thepho/manifests/SHA256SUMS.txt
"""
import hashlib, json, os, datetime, sys

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
SRC_REL = r"data\cbeta\xml-p5-full\X\X86\X86n1601.xml"
SRC = os.path.join(ROOT, SRC_REL)
MAN = os.path.join(ROOT, "research", "thiendang-thepho", "manifests")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    from lxml import etree
    src_hash = sha256_file(SRC)
    st = os.stat(SRC)

    # --- Trích teiHeader VERBATIM từ byte thô (không qua serializer) ---
    raw = open(SRC, "rb").read()
    i0 = raw.find(b"<teiHeader")
    i1 = raw.find(b"</teiHeader>")
    assert i0 != -1 and i1 != -1, "không tìm thấy teiHeader"
    i1_end = i1 + len(b"</teiHeader>")
    header_bytes = raw[i0:i1_end]
    header_path = os.path.join(MAN, "source-header.xml")
    with open(header_path, "wb") as f:
        f.write(header_bytes)

    # --- Parse metadata ---
    tree = etree.parse(SRC)
    root = tree.getroot()
    ns = {"tei": "http://www.tei-c.org/ns/1.0", "cb": "http://www.cbeta.org/ns/1.0"}
    hdr = root.find("tei:teiHeader", ns)

    def txt(el):
        return "".join(el.itertext()).strip() if el is not None else None

    title_series_en = txt(hdr.find(".//tei:titleStmt/tei:title[@level='s']", ns))
    title_work = txt(hdr.find(".//tei:titleStmt/tei:title[@level='m']", ns))
    title_full = txt(hdr.find(".//tei:titleStmt/tei:title[@type='main']", ns))
    authors = [txt(a) for a in hdr.findall(".//tei:titleStmt/tei:author", ns)]
    availability = txt(hdr.find(".//tei:publicationStmt/tei:availability", ns))
    availability_p = txt(hdr.find(".//tei:publicationStmt/tei:availability/tei:p", ns))
    edition = txt(hdr.find(".//tei:editionStmt/tei:edition", ns))
    pub_date = txt(hdr.find(".//tei:publicationStmt/tei:date", ns))
    source_desc = txt(hdr.find(".//tei:sourceDesc/tei:bibl", ns))
    series = txt(hdr.find(".//tei:sourceDesc/tei:bibl/tei:series", ns))

    # số quyển: milestone unit=juan và cb:div type=juan
    juans_ms = root.findall(".//tei:milestone[@unit='juan']", ns)
    juan_values = sorted({m.get("n") for m in juans_ms if m.get("n")})
    divs_juan = root.findall(".//cb:div[@type='juan']", ns)

    # gaiji decl
    chardecl = hdr.findall(".//tei:charDecl/tei:char", ns)

    manifest = {
        "task": "T429",
        "phase": 1,
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": {
            "work_title_raw": title_work,
            "work_title_han": "禪燈世譜",
            "series_title_en": title_series_en,
            "title_full_electronic": title_full,
            "cbeta_sigla": "X86n1601",
            "authors_raw": authors,
            "juan_count_milestone": len(juans_ms),
            "juan_values": juan_values,
            "juan_count_cbdiv": len(divs_juan),
            "expected_juan": 9,
        },
        "file": {
            "path_relative_to_daoanh": SRC_REL.replace("\\", "/"),
            "size_bytes": st.st_size,
            "mtime_local": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(),
            "sha256": src_hash,
        },
        "provenance": {
            "origin": "CBETA XML P5 full release (bản sao local có sẵn trong repo, không tải mới)",
            "download_url": None,
            "note": "File đã có sẵn tại data/cbeta/xml-p5-full/; Giai đoạn 1 chỉ hash + đóng băng metadata.",
        },
        "rights": {
            "availability_raw": availability,
            "availability_p": availability_p,
            "condition": "non-commercial use when distributed with this header intact",
            "header_file": "research/thiendang-thepho/manifests/source-header.xml",
            "assessment_report": "docs/reports/thiendang-thepho/phase1/rights-assessment.md",
        },
        "header_metadata": {
            "edition": edition,
            "publication_date": pub_date,
            "source_bibl": source_desc,
            "series": series,
            "gaiji_char_decl_count": len(chardecl),
        },
        "integrity": {
            "hash_algorithm": "SHA256",
            "recompute_verified": None,  # điền bởi bước verify
        },
    }
    man_path = os.path.join(MAN, "source-manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # --- SHA256SUMS.txt (hash tái tính của các file đóng băng) ---
    sums_path = os.path.join(MAN, "SHA256SUMS.txt")
    lines = []
    for rel, p in [
        (SRC_REL.replace("\\", "/"), SRC),
        ("research/thiendang-thepho/manifests/source-header.xml", header_path),
        ("research/thiendang-thepho/manifests/source-manifest.json", man_path),
    ]:
        lines.append(f"{sha256_file(p)}  {rel}")
    with open(sums_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(json.dumps({
        "sha256_source": src_hash,
        "size": st.st_size,
        "title": title_work,
        "authors": authors,
        "juan_milestone": len(juans_ms),
        "juan_values": juan_values,
        "juan_cbdiv": len(divs_juan),
        "availability": availability,
        "edition": edition,
        "gaiji": len(chardecl),
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
