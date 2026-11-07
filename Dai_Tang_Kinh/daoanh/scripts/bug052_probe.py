"""BUG-052 follow-up probe: đo kích thước source_data/prompt cho A000004 và gọi
Groq trực tiếp bằng prompt giống route /daoanh/api/person/<id>/dila_translate,
để xác định nguyên nhân 503/500 (không in khóa, không ghi DB)."""
import json
import os
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET

MAIN_DAOANH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
DB_PATH = os.path.join(MAIN_DAOANH, "data", "lineage.db")
ENV_PATH = os.path.join(MAIN_DAOANH, ".env")
LLM_CFG_PATH = os.path.join(MAIN_DAOANH, "data", "llm_config.json")

PERSON_ID = sys.argv[1] if len(sys.argv) > 1 else "A000004"

NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def read_env_key(name):
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return ""
    m = re.search(rf"^{name}\s*=\s*(.*)$", text, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def read_llm_cfg():
    try:
        with open(LLM_CFG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_extra_for_person(conn, pid):
    """Rút gọn của _t148_load_dila_extra(): chỉ quét record XML chứa pid này,
    không load toàn bộ 49k person vào RAM."""
    rows = conn.execute(
        "SELECT id, raw_text FROM ttl_v2_source_records "
        "WHERE kind='DILA_XML' AND raw_text IS NOT NULL AND raw_text LIKE ?",
        (f"%{pid}%",),
    ).fetchall()
    data = {"alt_names": [], "listbibl": [], "listbibl_items": [], "relations": []}
    found = False
    for rec_id, xml_text in rows:
        try:
            root = ET.fromstring(xml_text)
        except Exception as ex:
            print(f"[WARN] parse error record {rec_id}: {ex}")
            continue
        for elem in root.iter(f"{{{NS}}}person"):
            this_pid = elem.get(f"{{{XML_NS}}}id") or elem.get("xml:id")
            if this_pid != pid:
                continue
            found = True
            for child in elem:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == "persName":
                    ptype = child.get("type", "")
                    txt = (child.text or "").strip()
                    if ptype == "alternative" and txt:
                        data["alt_names"].append(txt)
                elif tag == "listBibl":
                    for bibl in child:
                        t = (bibl.text or "").strip()
                        ref_el = bibl.find(f"{{{NS}}}ref")
                        if ref_el is not None and not t:
                            t = (ref_el.text or "").strip()
                        if t:
                            data["listbibl"].append(t)
                elif tag == "note":
                    ntype = child.get("type", "")
                    txt = "".join(child.itertext()).strip()
                    if ntype == "biogHist":
                        data["bio_extensive"] = txt
                    elif ntype == "worksInTripitaka":
                        data["works_tripitaka"] = txt
                    elif ntype == "worksByThisAuthor":
                        data["works_by"] = txt
                    elif ntype == "secondaryLiterature":
                        data["secondary_lit"] = txt
                    elif ntype == "mentionedIn":
                        data["mentioned_in"] = txt
                    elif ntype == "activeAt":
                        data["active_at"] = txt
                    elif ntype == "placeOfOrigin":
                        data["place_of_origin"] = txt
                    elif ntype == "occupation":
                        data["occupation"] = txt
                    elif ntype == "deathNote":
                        data["death_note"] = txt
                elif tag == "linkGrp" or tag == "relation":
                    pass  # không cần cho probe kích thước
    return data if found else {}


def build_source_data(name_zh, bio_zh, extra):
    d = {
        "name_zh": name_zh or "",
        "alt_names": extra.get("alt_names") or [],
        "bio_concise": bio_zh or "",
        "bio_extensive": extra.get("bio_extensive") or "",
        "listbibl": extra.get("listbibl") or [],
        "works_tripitaka": extra.get("works_tripitaka") or "",
        "works_by": extra.get("works_by") or "",
        "secondary_lit": extra.get("secondary_lit") or "",
        "mentioned_in": extra.get("mentioned_in") or "",
        "active_at": extra.get("active_at") or "",
        "dynasty_xml": extra.get("dynasty_xml") or "",
        "occupation": extra.get("occupation") or "",
        "place_of_origin": extra.get("place_of_origin") or "",
        "death_note": extra.get("death_note") or "",
        "birth_death_quote": extra.get("birth_death_quote") or "",
    }
    return d


def build_prompt(data):
    truncated = dict(data)
    truncated["bio_concise"] = (data.get("bio_concise") or "")[:2000]
    truncated["bio_extensive"] = (data.get("bio_extensive") or "")[:4000]
    fields_block = json.dumps(truncated, ensure_ascii=False, indent=2)
    return (
        "Bạn là thành viên Ban Dịch PTDA — dịch giả Hán-Việt chuyên ngành Phật học hàn lâm Việt Nam.\n"
        "Nhiệm vụ: dịch các trường thông tin nhân vật Phật giáo sau sang tiếng Việt.\n\n"
        "QUY TẮC BẮT BUỘC (DILA card): [rút gọn cho probe — không ảnh hưởng kích thước đáng kể]\n"
        f"DỮ LIỆU CẦN DỊCH:\n{fields_block}\n\n"
        "Trả về DUY NHẤT một JSON object...\n"
    ), fields_block


def approx_tokens(s):
    # Ước lượng thô: ~2.2 ký tự / token cho văn bản hỗn hợp Hán+Việt qua BPE
    # (không chính xác bằng tokenizer thật nhưng đủ để thấy quy mô).
    return round(len(s) / 2.2)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    p = conn.execute(
        "SELECT id, name_zh, bio FROM people WHERE id=?", (PERSON_ID,)
    ).fetchone()
    if not p:
        print(f"[ERR] Không tìm thấy person {PERSON_ID}")
        return 1
    name_zh = p["name_zh"] or ""
    bio_zh = p["bio"] or ""

    t0 = time.time()
    extra = load_extra_for_person(conn, PERSON_ID)
    t1 = time.time()
    print(f"[INFO] load_extra_for_person: {t1-t0:.2f}s, found={bool(extra)}")
    print(f"[INFO] listbibl count = {len(extra.get('listbibl', []))}")
    listbibl_chars = sum(len(x) for x in extra.get("listbibl", []))
    print(f"[INFO] listbibl total chars = {listbibl_chars}")
    for k in ("bio_extensive", "works_tripitaka", "works_by", "secondary_lit", "mentioned_in"):
        v = extra.get(k) or ""
        print(f"[INFO] {k} chars = {len(v)}")

    data = build_source_data(name_zh, bio_zh, extra)
    prompt, fields_block = build_prompt(data)
    print(f"[INFO] prompt total chars = {len(prompt)} ; approx_tokens ~= {approx_tokens(prompt)}")
    print(f"[INFO] fields_block chars = {len(fields_block)} ; approx_tokens ~= {approx_tokens(fields_block)}")

    # --- Gọi Groq thật, đo finish_reason/usage (không in prompt, không in key) ---
    groq_key = read_llm_cfg().get("groq_key") or os.environ.get("GROQ_API_KEY") or ""
    groq_model = read_llm_cfg().get("groq_model") or os.environ.get("GROQ_MODEL") or "qwen/qwen3.8-27b"
    if not groq_key:
        print("[ERR] Không có groq_key để test (khóa rỗng cả llm_config.json và env).")
        return 1
    print(f"[INFO] groq_model = {groq_model}")

    import requests

    t2 = time.time()
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": groq_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 4096,
            },
            timeout=35,
        )
    except Exception as e:
        print(f"[ERR] request exception: {type(e).__name__}: {e}")
        return 1
    t3 = time.time()
    print(f"[INFO] HTTP status = {resp.status_code}, elapsed = {t3-t2:.2f}s")
    try:
        gd = resp.json()
    except Exception as e:
        print(f"[ERR] response not JSON: {e}; raw[:300]={resp.text[:300]!r}")
        return 1

    if "error" in gd:
        print(f"[ERR] Groq error object: {json.dumps(gd['error'], ensure_ascii=False)[:500]}")
        return 1

    usage = gd.get("usage")
    print(f"[INFO] usage = {usage}")
    choices = gd.get("choices") or []
    if choices:
        fr = choices[0].get("finish_reason")
        content = choices[0].get("message", {}).get("content", "")
        print(f"[INFO] finish_reason = {fr}")
        print(f"[INFO] content length (chars) = {len(content)}")
        print(f"[INFO] content tail (last 200 chars) = {content[-200:]!r}")
    else:
        print(f"[WARN] no choices in response: {json.dumps(gd, ensure_ascii=False)[:500]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
