# -*- coding: utf-8 -*-
import sys, os, json, sqlite3
DAOANH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
sys.path.insert(0, DAOANH)
os.chdir(DAOANH)
from app import app as flask_app
c = flask_app.test_client()
r = c.get("/daoanh/api/public/autocomplete", query_string={"q": "Thi\u1ebfu L"})
b = r.get_json()
print("TEST7 status=", r.status_code, "| type=", type(b).__name__)
print("TEST7 body_head=", json.dumps(b, ensure_ascii=False, default=str)[:600])
r2 = c.get("/daoanh/api/search", query_string={"q": "Khuy C\u01a1"})
b2 = r2.get_json()
print("TEST8 Khuy Co | status=", r2.status_code,
      "| monks=", len(b2.get("monks") or []),
      "| dila_works=", len(b2.get("dila_works") or []),
      "| dila_people=", len(b2.get("dila_people") or []),
      "| places=", len(b2.get("places") or []))
monks_sample = [(m.get("id"), m.get("name_vi") or m.get("name_zh")) for m in (b2.get("monks") or [])[:3]]
print("TEST8 monks sample=", monks_sample)
con = sqlite3.connect("file:data/lineage.db?mode=ro", uri=True)
cols = [row[1] for row in con.execute("PRAGMA table_info(namevi_map_places)").fetchall()]
print("DB namevi_map_places columns=", cols)
con.close()
