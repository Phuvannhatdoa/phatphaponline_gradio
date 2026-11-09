"""Verify route DILA trên HOME bằng Flask test_client của chính app.py.
KHÔNG ghi DB: get_db_connection được thay bằng kết nối sqlite read-only (mode=ro).
KHÔNG khởi động server. Chạy từ thư mục daoanh:
    python -X utf8 docs/sessions/2026-10-26/gate0/verify.py
"""
import json, os, sqlite3, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # gate0 → 2026-10-26 → sessions → docs → daoanh
os.chdir(DAOANH)
sys.path.insert(0, DAOANH)

import app as M  # noqa: E402  (import không khởi động server: app.run nằm trong __main__)

db_abs = os.path.abspath(M.DB_PATH).replace("\\", "/")
RO_URI = "file:" + urllib.parse.quote(db_abs) + "?mode=ro"


def _ro_conn():
    c = sqlite3.connect(RO_URI, uri=True, timeout=10)
    c.row_factory = sqlite3.Row
    return c


M.get_db_connection = _ro_conn  # mọi route gọi tên global → đi qua kết nối read-only

client = M.app.test_client()
fails = []


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        fails.append(label)


def get(url):
    r = client.get(url)
    data = None
    try:
        data = json.loads(r.get_data(as_text=True))
    except Exception:
        pass
    return r.status_code, data


# A. Route mới: kinh của một người (A000294 Huyền Trang; báo cáo gate0: 78 dòng contributors).
st, d = get("/daoanh/api/public/dila_works?person_id=A000294&sort=juans")
check(st == 200, f"dila_works A000294 HTTP {st}")
works = (d or {}).get("works", [])
print("  count =", (d or {}).get("count"), " len(works) =", len(works))
check(bool(d and d.get("success")), "dila_works success=true")
check(len(works) > 0, "dila_works: works KHÁC RỖNG")
check(len(works) == 78, f"dila_works A000294 đúng 78 (thực tế {len(works)})")
check(all("cbeta_id" in w and ("title_zh" in w) for w in works), "mỗi work có cbeta_id + title_zh")
for w in works[:3]:
    print("  sample:", w.get("cbeta_id"), "|", w.get("title_zh"), "|", w.get("title_vi"), "| juans", w.get("juans"))

# A2. sort khác + người không tồn tại + thiếu person_id (edge/fallback).
st2, d2 = get("/daoanh/api/public/dila_works?person_id=A000294&sort=title")
check(st2 == 200 and len((d2 or {}).get("works", [])) == 78, "sort=title vẫn 78")
st3, d3 = get("/daoanh/api/public/dila_works?person_id=A999999999")
check(st3 == 200 and (d3 or {}).get("count") == 0, "person không tồn tại → 200, count 0")
st4, d4 = get("/daoanh/api/public/dila_works")
check(st4 == 400, f"thiếu person_id → 400 (thực tế {st4})")

# B. /daoanh/api/search?q=Huyền Trang: có đủ key DILA (dila_people có thể rỗng nhưng key phải có).
st, s = get("/daoanh/api/search?q=" + urllib.parse.quote("Huyền Trang"))
check(st == 200, f"search Huyền Trang HTTP {st}")
for k in ["monks", "places", "works", "dila_works", "dila_works_total", "dila_people"]:
    check(s is not None and k in s, f"search có key '{k}'")
dw = (s or {}).get("dila_works", [])
dp = (s or {}).get("dila_people", [])
print("  dila_works len =", len(dw), " total =", (s or {}).get("dila_works_total"),
      " dila_people len =", len(dp), " monks =", len((s or {}).get("monks", [])),
      " places =", len((s or {}).get("places", [])), " works =", len((s or {}).get("works", [])))
check(len(dw) > 0, "search: dila_works KHÁC RỖNG")
check((s or {}).get("dila_works_total", 0) >= len(dw) > 0, "dila_works_total >= len(dila_works)")
check(len(dp) > 0, "search: dila_people KHÁC RỖNG (A000294 phải có)")
if dp:
    print("  dila_people[0]:", dp[0].get("person_id"), dp[0].get("name_zh"), "works", dp[0].get("works"),
          "places", [p.get("name_zh") for p in dp[0].get("places", [])][:3])
for w in dw[:3]:
    print("  search work:", w.get("cbeta_id"), "|", w.get("title_zh"), "| contributors", len(w.get("contributors", [])))

# C. Regression: autocomplete + search cũ (monks/places/works).
st, ac = get("/daoanh/api/public/autocomplete?q=" + urllib.parse.quote("Thiếu L"))
check(st == 200, f"autocomplete 'Thiếu L' HTTP {st}")
st, s2 = get("/daoanh/api/search?q=" + urllib.parse.quote("Khuy Cơ"))
check(st == 200 and all(k in (s2 or {}) for k in ["monks", "places", "works"]), "search 'Khuy Cơ' vẫn có monks/places/works")
print("  Khuy Cơ monks =", len((s2 or {}).get("monks", [])), " dila_works =", len((s2 or {}).get("dila_works", [])))

# D. Edge: q quá ngắn → nhánh sớm trong api_global_search (không có key DILA — UI dùng `|| []`).
st, s3 = get("/daoanh/api/search?q=a")
print("  q='a' keys:", sorted((s3 or {}).keys()), "HTTP", st)
check(st == 200, "q ngắn → 200")

print("\nSUMMARY:", "ALL PASS" if not fails else f"FAILS={fails}")
sys.exit(1 if fails else 0)
