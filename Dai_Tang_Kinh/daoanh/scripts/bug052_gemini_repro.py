"""BUG-052 follow-up: lặp lại gọi Gemini trực tiếp (fallback trong
api_person_dila_translate) để xem có lỗi key/quota không. Không in khóa."""
import json
import os
import re
import sys
import time

MAIN_DAOANH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
ENV_PATH = os.path.join(MAIN_DAOANH, ".env")

with open(ENV_PATH, "r", encoding="utf-8") as f:
    text = f.read()
m = re.search(r"^GEMINI_API_KEY\s*=\s*(.*)$", text, re.M)
GEMINI_KEY = m.group(1).strip() if m else ""

PROMPT = (sys.argv[1] if len(sys.argv) > 1 else "Dịch câu này sang tiếng Anh: Xin chào thế giới.")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 5

import requests

g_url = ("https://generativelanguage.googleapis.com/v1beta/models/"
         "gemini-3.6-flash:generateContent?key=" + GEMINI_KEY)

for i in range(N):
    t0 = time.time()
    try:
        r = requests.post(g_url, json={
            "contents": [{"parts": [{"text": PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.1},
        }, timeout=45)
        el = time.time() - t0
        try:
            gd = r.json()
        except Exception as pe:
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s NOT-JSON body[:200]={r.text[:200]!r}")
            continue
        if gd.get("candidates"):
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s OK candidates={len(gd['candidates'])}")
        else:
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s NO-CANDIDATES body={json.dumps(gd, ensure_ascii=False)[:400]}")
    except Exception as e:
        el = time.time() - t0
        print(f"[{i}] EXCEPTION elapsed={el:.2f}s {type(e).__name__}: {e}")
    time.sleep(0.3)
