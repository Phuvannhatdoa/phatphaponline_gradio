"""BUG-052 follow-up: lặp lại gọi Groq trực tiếp (giống logic trong
api_person_dila_translate) để bắt được exception/HTTP status lúc fail.
Không in khóa. Không ghi DB."""
import json
import os
import re
import sys
import time

MAIN_DAOANH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
LLM_CFG_PATH = os.path.join(MAIN_DAOANH, "data", "llm_config.json")

with open(LLM_CFG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)
GROQ_KEY = cfg.get("groq_key") or ""
GROQ_MODEL = cfg.get("groq_model") or "qwen/qwen3.8-27b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT = (sys.argv[1] if len(sys.argv) > 1 else "Dịch câu này sang tiếng Anh: Xin chào thế giới.")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 8

import requests

for i in range(N):
    t0 = time.time()
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 0.1,
                "max_tokens": 4096,
            },
            timeout=35,
        )
        el = time.time() - t0
        try:
            gd = r.json()
        except Exception as pe:
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s NOT-JSON body[:200]={r.text[:200]!r} parse_err={pe}")
            continue
        if "error" in gd:
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s ERROR={json.dumps(gd['error'], ensure_ascii=False)[:300]}")
        elif gd.get("choices"):
            fr = gd["choices"][0].get("finish_reason")
            usage = gd.get("usage")
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s OK finish_reason={fr} usage={usage}")
        else:
            print(f"[{i}] HTTP {r.status_code} elapsed={el:.2f}s UNEXPECTED body[:300]={json.dumps(gd, ensure_ascii=False)[:300]}")
    except Exception as e:
        el = time.time() - t0
        print(f"[{i}] EXCEPTION elapsed={el:.2f}s {type(e).__name__}: {e}")
    time.sleep(0.5)
