# -*- coding: utf-8 -*-
"""
T429 — Giai đoạn 2: phân tích cấu trúc sơ đồ X86n1601 (chỉ ĐỌC nguồn).

Output (chỉ ghi vào research/thiendang-thepho/):
  derived/structure-inventory.json
  sources/sample-source-fragments/*.xml
  logs/analyze-structure-run.json
Không ghi DB / TTL / production. Không gọi API.
"""
import hashlib, json, os, datetime, re
from lxml import etree

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
SRC = os.path.join(ROOT, "data", "cbeta", "xml-p5-full", "X", "X86", "X86n1601.xml")
RES = os.path.join(ROOT, "research", "thiendang-thepho")
FRAG = os.path.join(RES, "sources", "sample-source-fragments")

TEI = "http://www.tei-c.org/ns/1.0"
CB = "http://www.cbeta.org/ns/1.0"
XMLID = "{http://www.w3.org/XML/1998/namespace}id"
NS = {"tei": TEI}

CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

def cn_to_int(s):
    """Đổi số Trung giản đơn: 一..三十三 (đủ dùng cho nhãn 第N祖 / N世)."""
    s = s.strip()
    if not s:
        return None
    if s == "十":
        return 10
    m = re.fullmatch(r"([一二三四五六七八九])?十([一二三四五六七八九])?", s)
    if m:
        tens = CN_NUM[m.group(1)] if m.group(1) else 1
        ones = CN_NUM[m.group(2)] if m.group(2) else 0
        return tens * 10 + ones
    if s in CN_NUM:
        return CN_NUM[s]
    return None

def parse_label(lbl):
    """'第一祖'→(1,'zu'); '二世'→(2,'shi'); '始祖'→(0,'shizu'); '□□世'→(None,'shi')."""
    if not lbl:
        return None, None
    lbl = lbl.strip()
    if lbl == "始祖":
        return 0, "shizu"
    m = re.fullmatch(r"第?([一二三四五六七八九十]+)祖", lbl)
    if m:
        return cn_to_int(m.group(1)), "zu"
    m = re.fullmatch(r"第?([一二三四五六七八九十□]+)世", lbl)
    if m:
        n = cn_to_int(m.group(1)) if "□" not in m.group(1) else None
        return n, "shi"
    return None, None

def txt(el):
    return "".join(el.itertext()).strip() if el is not None else ""

def label_of(item):
    for n in item.findall("tei:note", NS):
        if n.get("place") == "inline":
            return txt(n)
    return None

def name_of(item):
    """Tên = text trước <p>/<list> đầu tiên, không gồm nhãn đời (note inline)."""
    out = [item.text or ""]
    for ch in item:
        if ch.tag in (f"{{{TEI}}}p", f"{{{TEI}}}list"):
            break
        if ch.tag == f"{{{TEI}}}note" and ch.get("place") == "inline":
            out.append(ch.tail or "")
            continue
        out.append("".join(ch.itertext()))
        out.append(ch.tail or "")
    return "".join(out).strip()

def head_of(d):
    return txt(d.find("tei:head", NS))

def item_children(item):
    """các item con trực tiếp (qua list con trực tiếp)."""
    kids = []
    for lst in item.findall("tei:list", NS):
        kids.extend(lst.findall("tei:item", NS))
    return kids

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def frag(el, fname, note):
    """Lưu fragment (re-serialize từ lxml — trung thành nội dung, không phải byte verbatim)."""
    os.makedirs(FRAG, exist_ok=True)
    p = os.path.join(FRAG, fname)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"<!-- T429 sample-source-fragment | {note} | re-serialized by lxml from X86n1601.xml (SHA256 0020c4847b8107260e8674233d7833fd590cccafba2210d0ac479edd88ff75eb) -->\n")
        f.write(etree.tostring(el, encoding="unicode"))
    return f"research/thiendang-thepho/sources/sample-source-fragments/{fname}"

def main():
    tree = etree.parse(SRC)
    root = tree.getroot()
    body = root.find("tei:text/tei:body", NS)

    inv = {"task": "T429", "phase": 2, "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "source_file": "data/cbeta/xml-p5-full/X/X86/X86n1601.xml",
           "source_sha256": sha256_file(SRC)}

    # ---- đếm toàn cục ----
    counts = {}
    for tag in ["list", "item", "p", "note", "lb", "g", "app", "lem", "rdg", "head", "milestone", "table", "div"]:
        counts[f"tei:{tag}"] = len(root.findall(f".//{{{TEI}}}{tag}", NS))
    counts["cb:div"] = len(root.findall(f".//{{{CB}}}div"))
    counts["tei:table"] = len(root.findall(f".//{{{TEI}}}table", NS))
    inv["global_counts"] = counts

    # note theo (type, place)
    from collections import Counter
    nt = Counter((n.get("type"), n.get("place")) for n in root.iter(f"{{{TEI}}}note"))
    inv["note_by_type_place"] = {f"{t}|{p}": c for (t, p), c in nt.most_common()}

    # gaiji: charDecl vs sử dụng
    decl = root.findall(".//tei:charDecl/tei:char", NS)
    used = Counter(g.get("ref") for g in root.iter(f"{{{TEI}}}g"))
    inv["gaiji"] = {"char_decl_count": len(decl),
                    "g_usage_total": sum(used.values()),
                    "distinct_refs_used": len(used)}

    # ---- div inventory + juan ----
    # gán juan: duyệt body theo thứ tự, milestone unit=juan đánh dấu biên
    div_infos = []
    current_juan = None
    juan_of_div = {}
    for el in body.iter():
        if el.tag == f"{{{TEI}}}milestone" and el.get("unit") == "juan":
            current_juan = el.get("n")
        elif el.tag == f"{{{CB}}}div" and el.get("type") in ("other", "xu", "apparatus", "xuzang-notes", "add-notes"):
            h = txt(el.find("tei:head", NS))
            div_infos.append({"head": h, "type": el.get("type"), "juan": current_juan,
                              "element": el})
    for di in div_infos:
        d = di.pop("element")
        lists = d.findall(".//tei:list", NS)
        items = d.findall(".//tei:item", NS)
        # depth tối đa của cấu trúc list/item lồng nhau (list>item>list>item…)
        def item_depth(item, acc=1):
            best = acc
            for lst in item.findall("tei:list", NS):
                for sub in lst.findall("tei:item", NS):
                    best = max(best, item_depth(sub, acc + 1))
            return best
        maxd = max((item_depth(it) for it in d.findall(".//tei:item", NS)), default=0)
        di.update({"lists": len(lists), "items": len(items), "max_list_depth": maxd})
    inv["divs"] = div_infos
    diagrams = [d for d in div_infos if d["type"] == "other"]
    inv["diagram_count"] = len(diagrams)

    # ---- nhãn đời toàn cục ----
    lbl_stats = Counter()
    items_lbl = []
    for it in root.iter(f"{{{TEI}}}item"):
        lbl = label_of(it)
        n, kind = parse_label(lbl)
        key = f"{kind}|{'missing' if n is None and kind else 'num'}" if kind else "none"
        lbl_stats[key if kind else "no_label"] += 1
        if lbl:
            items_lbl.append((it, lbl, n, kind))
    inv["item_label_stats"] = dict(lbl_stats)

    # ---- R01: dãy 第N祖 liên tục ----
    d33 = [d for d in div_infos if "三十三祖世系圖" in d["head"]][0]
    d33_el = [d for d in root.iter(f"{{{CB}}}div") if d.get("type") == "other" and "三十三祖世系圖" in txt(d.find("tei:head", NS))][0]
    tl = d33_el.find("tei:list", NS)
    tops = tl.findall("tei:item", NS)
    seq = []
    for it in tops:
        lbl = label_of(it)
        n, kind = parse_label(lbl)
        seq.append((it.get(XMLID), lbl, n, kind, name_of(it)))
    zu = [s for s in seq if s[3] == "zu"]
    nums = [s[2] for s in zu]
    r01_continuous = nums == list(range(1, len(nums) + 1))
    inv["r01"] = {
        "div_head": d33["head"], "top_items": len(tops),
        "shizu": {"xml_id": seq[0][0], "label": seq[0][1], "name": seq[0][4]},
        "zu_count": len(zu), "zu_numbers": nums, "continuous_1_to_N": r01_continuous,
        "first": {"xml_id": zu[0][0], "label": zu[0][1], "name": zu[0][4]},
        "middle": {"xml_id": zu[len(zu)//2][0], "label": zu[len(zu)//2][1], "name": zu[len(zu)//2][4]},
        "last": {"xml_id": zu[-1][0], "label": zu[-1][1], "name": zu[-1][4]},
        "label_form_note": "nhãn không thuần nhất: 第一祖 nhưng 二祖/三祖… (thiếu 第) — parser phải chấp nhận cả hai dạng",
    }

    # ---- kiểm chéo nhãn toàn cục (R02): con = cha + 1 ----
    ok = mismatch = unlabeled_parent = unlabeled_child = 0
    mismatch_ex = []
    pair_total = 0
    multi_heir_parents = []   # 1 cha có ≥2 con CÙNG nhãn k+1 (nhiều người nối pháp cùng đời)
    for it in root.iter(f"{{{TEI}}}item"):
        pn, pk = parse_label(label_of(it))
        if pn is None:
            continue
        kids_labeled = []
        for kid in item_children(it):
            pair_total += 1
            kn, kk = parse_label(label_of(kid))
            if kn is None:
                unlabeled_child += 1
            elif kn == pn + 1:
                ok += 1
                kids_labeled.append(kid)
            else:
                mismatch += 1
                if len(mismatch_ex) < 12:
                    mismatch_ex.append({"parent": {"xml_id": it.get(XMLID), "label": label_of(it), "name": name_of(it)[:20]},
                                        "child": {"xml_id": kid.get(XMLID), "label": label_of(kid), "name": name_of(kid)[:20]}})
        if len(kids_labeled) >= 2:
            multi_heir_parents.append({"parent": {"xml_id": it.get(XMLID), "label": label_of(it), "name": name_of(it)[:20]},
                                       "children_same_label": [{"xml_id": k.get(XMLID), "name": name_of(k)[:20]} for k in kids_labeled]})
    inv["label_crosscheck"] = {"pairs_parent_labeled": pair_total, "child_eq_parent_plus_1": ok,
                               "mismatch": mismatch, "child_unlabeled": unlabeled_child,
                               "mismatch_examples": mismatch_ex,
                               "parents_with_multiple_labeled_children": len(multi_heir_parents),
                               "multi_heir_examples": multi_heir_parents[:5]}

    # ---- R02: ví dụ đầu/giữa/cuối theo thứ tự sơ đồ ----
    r02_ex = []
    for di in diagrams:
        d_el = [d for d in root.iter(f"{{{CB}}}div") if d.get("type") == "other" and txt(d.find("tei:head", NS)) == di["head"]][0]
        found = None
        for it in d_el.iter(f"{{{TEI}}}item"):
            pn, _ = parse_label(label_of(it))
            if pn is None:
                continue
            for kid in item_children(it):
                kn, _ = parse_label(label_of(kid))
                if kn is not None and kn == pn + 1:
                    found = {"div": di["head"], "parent": {"xml_id": it.get(XMLID), "label": label_of(it), "name": name_of(it)[:20]},
                             "child": {"xml_id": kid.get(XMLID), "label": label_of(kid), "name": name_of(kid)[:20]}}
                    break
            if found:
                break
        if found:
            r02_ex.append(found)
    inv["r02_examples_first_middle_last"] = [r02_ex[0], r02_ex[len(r02_ex)//2], r02_ex[-1]] if r02_ex else []
    inv["r02_divs_with_labeled_chain"] = len(r02_ex)
    inv["r02_divs_without_labeled_chain"] = [d["head"] for d in diagrams if d["head"] not in {e["div"] for e in r02_ex}]

    # ---- R03: item không nhãn cùng list con với item có nhãn ----
    r03_lists = 0
    r03_unlabeled_total = 0
    r03_example = None
    for lst in root.iter(f"{{{TEI}}}list"):
        kids = lst.findall("tei:item", NS)
        if not kids or lst.getparent().tag != f"{{{TEI}}}item":
            continue
        labeled = [k for k in kids if parse_label(label_of(k))[0] is not None]
        unlabeled = [k for k in kids if parse_label(label_of(k))[0] is None]
        if labeled and unlabeled:
            r03_lists += 1
            r03_unlabeled_total += len(unlabeled)
            if not r03_example and any("黃檗" in name_of(lst.getparent()) for _ in [0]):
                pass
    # ví dụ cụ thể 黃檗
    dny = [d for d in root.iter(f"{{{CB}}}div") if d.get("type") == "other" and txt(d.find("tei:head", NS)).endswith("南嶽法派世系圖")][0]
    for it in dny.iter(f"{{{TEI}}}item"):
        if name_of(it).startswith("黃檗"):
            kids = item_children(it)
            r03_example = {"parent": {"xml_id": it.get(XMLID), "label": label_of(it), "name": name_of(it)},
                           "labeled_children": [{"xml_id": k.get(XMLID), "label": label_of(k), "name": name_of(k)[:20]} for k in kids if parse_label(label_of(k))[0] is not None],
                           "unlabeled_children": [{"xml_id": k.get(XMLID), "name": name_of(k)[:20]} for k in kids if parse_label(label_of(k))[0] is None]}
            break
    inv["r03"] = {"lists_mixed_labeled_unlabeled": r03_lists, "unlabeled_items_in_such_lists": r03_unlabeled_total,
                  "example_huangbo": r03_example}

    # ---- R04: item chỉ có văn tiểu sử ----
    r04_count = 0
    r04_ex = []
    for it in root.iter(f"{{{TEI}}}item"):
        nm = name_of(it)
        lbl = label_of(it)
        has_p = it.find("tei:p", NS) is not None
        has_list = it.find("tei:list", NS) is not None
        # "chỉ có văn tiểu sử": không nhãn, không tên đứng đầu (text đầu = chính văn dài), thường có p hoặc text dài
        if lbl is None and (has_p or (not has_list and len(nm) > 30)):
            r04_count += 1
            if len(r04_ex) < 3:
                par = it.getparent().getparent() if it.getparent().tag == f"{{{TEI}}}list" else None
                r04_ex.append({"xml_id": it.get(XMLID), "name_head": nm[:40],
                               "has_p": has_p, "parent": par.get(XMLID) if par is not None else None,
                               "parent_name": name_of(par)[:20] if par is not None else None})
    inv["r04"] = {"bio_only_items_estimate": r04_count, "examples": r04_ex}

    # ---- R05: 別見 ----
    full_text = txt(root)
    inv["r05"] = {"biejian_total": full_text.count("別見"),
                  "paiyi_biejian": full_text.count("派裔別見"),
                  "fasi_biejian": full_text.count("法嗣別見"),
                  "examples": []}
    cnt = 0
    for it in root.iter(f"{{{TEI}}}item"):
        t = txt(it)
        idx = t.find("別見")
        if idx != -1:
            cnt += 1
            if cnt <= 3 or cnt >= 48:
                inv["r05"]["examples"].append({"xml_id": it.get(XMLID), "context": t[max(0, idx-12):idx+6]})

    # ---- R06: □□世 ----
    r06 = []
    for it in root.iter(f"{{{TEI}}}item"):
        lbl = label_of(it)
        if lbl and "□" in lbl:
            node = it
            while node is not None and node.tag != f"{{{CB}}}div":
                node = node.getparent()
            r06.append({"xml_id": it.get(XMLID), "label": lbl, "name": name_of(it)[:20], "div": head_of(node)})
    inv["r06"] = {"count": len(r06), "items": r06}

    # ---- R07: app/lem/rdg + note lớp ----
    apps = root.findall(".//tei:app", NS)
    app_ex = []
    for a in (apps[0], apps[len(apps)//2], apps[-1]):
        app_ex.append({"index": apps.index(a), "lem": txt(a.find("tei:lem", NS)),
                       "rdg": [txt(r) for r in a.findall("tei:rdg", NS)],
                       "wit": [r.get("wit") for r in a.findall("tei:rdg", NS)]})
    inv["r07"] = {"app_count": len(apps), "note_add": nt.get(("add", None), 0),
                  "note_orig_foot": nt.get(("orig", "foot text"), 0),
                  "note_cf1": nt.get(("cf1", None), 0), "note_cf2": nt.get(("cf2", None), 0),
                  "app_examples": app_ex}

    # ---- lưu inventory ----
    inv_path = os.path.join(RES, "derived", "structure-inventory.json")
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inv, f, ensure_ascii=False, indent=2)

    # ---- fragments ----
    saved = []
    def save(el, fname, note):
        saved.append({"file": frag(el, fname, note), "note": note})

    # R01
    save(tops[1], "r01_first_di_1zu_mohajiaye.xml", "R01 đầu: 第一祖 摩訶迦葉")
    save(tops[len(tops)//2], "r01_middle_shiqizu.xml", "R01 giữa: 十七祖")
    save(tops[-1], "r01_last_33zu_huineng.xml", "R01 cuối: 三十三祖 慧能")
    # R02
    t2 = None
    for it in dny.iter(f"{{{TEI}}}item"):
        if it.get(XMLID) == "itemX86p0335a0601":
            t2 = it
            break
    save(t2.getparent().getparent(), "r02_mazu_daoyi_2shi.xml", "R02: 馬祖道一 二世 ⊂ 南獄懷讓 一世")
    # R03
    for it in dny.iter(f"{{{TEI}}}item"):
        if name_of(it).startswith("黃檗"):
            save(it, "r03_huangbo_children.xml", "R03: 黃檗希運 四世 + con có nhãn/không nhãn")
            break
    # R04
    save(tops[1].find("tei:list", NS), "r04_bio_only_under_mohajiaye.xml", "R04: list con chỉ tiểu sử dưới 摩訶迦葉")
    # R05
    for it in root.iter(f"{{{TEI}}}item"):
        if it.get(XMLID) == "itemX86p0324a0101":
            save(it, "r05_huineng_paiyi_biejian.xml", "R05: 慧能 三十三祖 — 輪派裔別見")
            break
    # R06
    for it in root.iter(f"{{{TEI}}}item"):
        if it.get(XMLID) == "itemX86p0472a1301":
            save(it, "r06_missing_gen_label.xml", "R06: nhãn □□世 mất chữ")
            break
    # R07
    save(apps[0], "r07_app_first.xml", "R07: app/lem/rdg đầu tiên")
    save(apps[-1], "r07_app_last.xml", "R07: app/lem/rdg cuối")

    runlog = {"generated_at_utc": inv["generated_at_utc"], "source_sha256": inv["source_sha256"],
              "inventory": "research/thiendang-thepho/derived/structure-inventory.json",
              "fragments": saved,
              "key_results": {"r01_continuous": r01_continuous, "zu_count": len(zu),
                              "label_crosscheck": inv["label_crosscheck"] | {"mismatch_examples": len(mismatch_ex)},
                              "r03_lists_mixed": r03_lists, "r04_estimate": r04_count,
                              "r05_biejian": inv["r05"]["biejian_total"], "r06_count": len(r06),
                              "r07_app": len(apps)}}
    with open(os.path.join(RES, "logs", "analyze-structure-run.json"), "w", encoding="utf-8") as f:
        json.dump(runlog, f, ensure_ascii=False, indent=2)

    print(json.dumps(runlog["key_results"], ensure_ascii=False, indent=2))
    print("fragments:", len(saved))

if __name__ == "__main__":
    main()
