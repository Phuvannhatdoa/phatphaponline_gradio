# -*- coding: utf-8 -*-
# QA M2 - verify T453 Gate 0 backend (read-only, Flask test_client, khong start server)
# Vietnames duoc viet duoi dang unicode escape de tranh loi encoding PowerShell.
import sys, os, json, sqlite3
DAOANH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
sys.path.insert(0, DAOANH)
os.chdir(DAOANH)
print("== import app ...")
from app import app as flask_app
c = flask_app.test_client()
Q_HTRANG = "Huy\u1ec1n Trang"
Q_LMON = "Long M\u00f4n"
Q_LMON_TQ = "Long M\u00f4n Th\u1ea1ch Qu\u1eadt"
Q_TL = "Thi\u1ebfu L"
def show(name, r, pick=None):
    ok = r.status_code
    try:
        b = r.get_json()
    except Exception:
        b = None
    body = pick(b) if (pick and isinstance(b, dict)) else (
        {k: b[k] for k in list(b)[:12] if not isinstance(b[k], list)} if isinstance(b, dict) else None)
    print(name, "| status=", ok, "| body=", json.dumps(body, ensure_ascii=False, default=str)[:1800])
    return ok, b

ok1, b1 = show("TEST1 dila_works?person_id=A000294",
    c.get("/daoanh/api/public/dila_works", query_string={"person_id": "A000294"}),
    lambda b: {"count": b.get("count"),
               "sample": [{"cbeta_id": w.get("cbeta_id"), "title_zh": w.get("title_zh"),
                            "title_vi": w.get("title_vi")} for w in (b.get("works") or [])[:2]],
               "len_works": len(b.get("works") or [])})
ok2, b2 = show("TEST2 dila_works (thieu person_id)",
    c.get("/daoanh/api/public/dila_works"), lambda b: {"error": b.get("error"), "success": b.get("success")})
ok3, b3 = show("TEST3 dila_works?person_id=NOT_EXIST",
    c.get("/daoanh/api/public/dila_works", query_string={"person_id": "NOT_EXIST"}),
    lambda b: {"count": b.get("count"), "len_works": len(b.get("works") or [])})
ok4, b4 = show("TEST4 /daoanh/api/search?q=Huyen Trang",
    c.get("/daoanh/api/search", query_string={"q": Q_HTRANG}),
    lambda b: {"success": b.get("success"),
               "monks": len(b.get("monks") or []),
               "dila_works": len(b.get("dila_works") or []),
               "dila_works_total": b.get("dila_works_total"),
               "dila_people": len(b.get("dila_people") or []),
               "sample_people": [{"person_id": p.get("person_id"), "name_vi": p.get("name_vi"),
                                   "works": p.get("works"), "juans": p.get("juans")}
                                  for p in (b.get("dila_people") or [])[:3]],
               "sample_work": [(w.get("cbeta_id"), w.get("title_vi") or w.get("title_zh"))
                               for w in (b.get("dila_works") or [])[:2]]})
if b4:
    print("TEST4a keys=", sorted(b4.keys()))
ok5, b5 = show("TEST5 /daoanh/api/search?q=a",
    c.get("/daoanh/api/search", query_string={"q": "a"}),
    lambda b: {"success": b.get("success"),
               "monks": len(b.get("monks") or []), "places": len(b.get("places") or []),
               "works": len(b.get("works") or []),
               "dila_works": len(b.get("dila_works") or []),
               "dila_people": len(b.get("dila_people") or [])})
ok6, b6 = show("TEST6 /daoanh/api/search?q=Long Mon",
    c.get("/daoanh/api/search", query_string={"q": Q_LMON}),
    lambda b: {"dila_works": len(b.get("dila_works") or []),
               "dila_people": len(b.get("dila_people") or [])})
ok6b, b6b = show("TEST6b /daoanh/api/search?q=Long Mon Thach Quat",
    c.get("/daoanh/api/search", query_string={"q": Q_LMON_TQ}),
    lambda b: {"dila_works": len(b.get("dila_works") or []),
               "dila_people": len(b.get("dila_people") or [])})
ok7, b7 = show("TEST7 /daoanh/api/public/autocomplete?q=Thieu L",
    c.get("/daoanh/api/public/autocomplete", query_string={"q": Q_TL}),
    lambda b: {"len": len(b) if isinstance(b, list) else (b.get("count") if isinstance(b, dict) else "?")})
print("== DB check (mode=ro)")
con = sqlite3.connect("file:data/lineage.db?mode=ro", uri=True)
q = lambda s: con.execute(s).fetchone()[0]
print("DB dila_catalog_works count =", q("SELECT COUNT(*) FROM dila_catalog_works"))
print("DB dila_catalog_contributors count =", q("SELECT COUNT(*) FROM dila_catalog_contributors"))
print("DB works cua A000294 =", q(
    "SELECT COUNT(*) FROM dila_catalog_works w WHERE w.cbeta_id IN "
    "(SELECT cbeta_id FROM dila_catalog_contributors WHERE person_id='A000294')"))
print("DB juans A000294 =", q(
    "SELECT COALESCE(SUM(w.juans),0) FROM dila_catalog_works w WHERE w.cbeta_id IN "
    "(SELECT cbeta_id FROM dila_catalog_contributors WHERE person_id='A000294')"))
rows = con.execute(
    "SELECT person_id, name_zh, name_vi FROM dila_catalog_contributors "
    "WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 3", ("%Huy\u1ec1n Trang%", "%Huy\u1ec1n Trang%")).fetchall()
print("DB contributors ten chua 'Huyen Trang':", rows)
rows2 = con.execute(
    "SELECT place_id, name_zh, name_vi FROM namevi_map_places WHERE name_vi LIKE '%Long M\u00f4n%' LIMIT 5").fetchall()
print("DB namevi_map_places 'Long Mon':", rows2)
con.close()
print("== DONE M2 script")
