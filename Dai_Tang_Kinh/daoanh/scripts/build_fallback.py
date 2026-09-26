#!/usr/bin/env python3
"""
Build hanviet_fallback table: extract char maps from Lexicon + batch HVDic API
"""
import sqlite3, re, requests, time

DB = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. Extract char maps from lexicon (pattern: "NUM) CJK: HV" or "NUM) CJK：HV")
count = 0
rows = cur.execute("SELECT term FROM lexicon WHERE term GLOB '*) ?:*' AND length(term) < 15").fetchall()
for (term,) in rows:
    m = re.search(r'\)\s*([\u4e00-\u9fff])\s*[:：]\s*(\S+)', term)
    if m:
        cur.execute("INSERT OR IGNORE INTO hanviet_fallback (ch, hv) VALUES (?, ?)", (m.group(1), m.group(2).rstrip(';，；')))
        count += 1

# Also match "NUM) CJK WORD" (e.g. "02) 哆: Đa")
rows2 = cur.execute("SELECT term FROM lexicon WHERE term GLOB '*) ?*' AND term NOT LIKE '%:%' AND term NOT LIKE '%：%' AND length(term) < 15").fetchall()
for (term,) in rows2:
    m = re.search(r'\)\s*([\u4e00-\u9fff])\s+(\S+)', term)
    if m:
        cur.execute("INSERT OR IGNORE INTO hanviet_fallback (ch, hv) VALUES (?, ?)", (m.group(1), m.group(2).rstrip(';，；')))
        count += 1

conn.commit()
print(f"✅ Extracted {count} char maps from lexicon")

# 2. Get all unique CJK chars from places_pending NOT yet in hanviet_fallback
pending = cur.execute("""
    SELECT DISTINCT substr(p.name_zh, i, 1) ch
    FROM places_pending p
    JOIN (SELECT 1 i UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
          UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8) idx
    WHERE i <= length(p.name_zh)
      AND substr(p.name_zh, i, 1) NOT IN (SELECT ch FROM hanviet_fallback)
      AND unicode(substr(p.name_zh, i, 1)) BETWEEN 0x4E00 AND 0x9FFF
""").fetchall()
missing = [r[0] for r in pending]
print(f"📡 {len(missing)} missing chars — calling HVDic API in batches...")

# Batch HVDic: send up to 30 chars at once
HVDIC_URL = "https://hvdic.thivien.net/transcript-query.json.php"
BATCH = 30
added_api = 0
missing_list = list(missing)

for start in range(0, len(missing_list), BATCH):
    batch = missing_list[start:start+BATCH]
    batch_str = "".join(batch)
    try:
        resp = requests.post(HVDIC_URL,
            data=f"mode=trans&lang=1&input={batch_str}".encode('utf-8'),
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            timeout=15)
        data = resp.json()
        result = data.get('result', [])
        for el in result:
            ch = el.get('c', '')
            hv_parts = el.get('o', [''])
            hv = " ".join([p for p in hv_parts if p])
            if ch and hv:
                cur.execute("INSERT OR IGNORE INTO hanviet_fallback (ch, hv) VALUES (?, ?)", (ch, hv))
                added_api += 1
    except Exception as e:
        print(f"  ⚠️ batch {start} failed: {e}")
    if (start // BATCH + 1) % 10 == 0:
        conn.commit()
        print(f"  ⏳ {start+BATCH}/{len(missing)} — {added_api} new chars added")
    time.sleep(0.1)

conn.commit()
total = cur.execute("SELECT COUNT(*) FROM hanviet_fallback").fetchone()[0]
print(f"✅ hanviet_fallback: {total} total entries (lexicon: {count}, API: {added_api})")
conn.close()
