"""Kiem chung read-only qua Flask test_client (khong start server, khong ghi DB).
Chay tu thu muc daoanh: python -X utf8 docs/sessions/2026-10-26/compliance-route/verify.py
"""
import json
import os
import sys
import time
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
os.chdir(DAOANH)
sys.path.insert(0, DAOANH)

try:
    import app as appmod
except Exception as e:  # khong start server, chi bao loi
    print("IMPORT app LOI:", type(e).__name__, e)
    sys.exit(2)

c = appmod.app.test_client()
results = {}


def show(label, r):
    print("==", label, "->", r.status_code)
    return r


# 1) compliance dashboard (doc file san co)
r = show("GET compliance/dashboard", c.get("/daoanh/api/compliance/dashboard"))
body = r.get_json(silent=True) or {}
print("  keys:", sorted(body.keys()))
print("  has_failures:", body.get("has_failures"))
print("  contract_failures:", body.get("contract_failures"))
print("  coverage_gaps:", body.get("coverage_gaps"))
print("  gate_policy:", body.get("gate_policy"))
print("  regenerated:", body.get("regenerated"))
results["dashboard"] = r.status_code

# 2) regenerate=1 (chay lai script that; exit 1/0 deu phai 200)
r = show("GET compliance/dashboard?regenerate=1", c.get("/daoanh/api/compliance/dashboard?regenerate=1"))
body = r.get_json(silent=True) or {}
print("  has_failures:", body.get("has_failures"), "| contract:", body.get("contract_failures"),
      "| coverage:", body.get("coverage_gaps"), "| regenerated:", body.get("regenerated"))
results["regen"] = r.status_code

# 3) edge: script exit 1 nhung JSON moi hop le -> 200 (regenerate that, khong mock)
#    edge: script crash rc=2 -> 500
import subprocess as _sp  # noqa: E402
real_run = _sp.run


def fake_crash(*a, **kw):
    class R:
        returncode = 2
        stdout = ""
        stderr = "Traceback: boom"
    return R()


with mock.patch("subprocess.run", side_effect=fake_crash):
    r = show("EDGE script crash rc=2 (mong 500)", c.get("/daoanh/api/compliance/dashboard?regenerate=1"))
    print("  body:", r.get_json(silent=True))
    results["crash_rc2"] = r.status_code


# rc=1 nhung KHONG ghi JSON moi (mtime cu) -> 500 (script loi that)
def fake_rc1_nowrite(*a, **kw):
    class R:
        returncode = 1
        stdout = ""
        stderr = "crashed after exit 1"
    # lam cho file JSON co mtime cu hon thoi diem bat dau
    p = os.path.join(appmod.DATA_DIR, "design_compliance.json")
    old = time.time() - 3600
    os.utime(p, (old, old))
    return R()


with mock.patch("subprocess.run", side_effect=fake_rc1_nowrite):
    r = show("EDGE rc=1 khong ghi JSON moi (mong 500)", c.get("/daoanh/api/compliance/dashboard?regenerate=1"))
    print("  body:", r.get_json(silent=True))
    results["rc1_stale"] = r.status_code
# khoi phuc mtime (chi la metadata file report, se duoc sinh lai o lan regenerate ke tiep)
os.utime(os.path.join(appmod.DATA_DIR, "design_compliance.json"), None)


# rc=1 MA JSON moi hop le (cong hai tang: contract fail) -> phai 200 (CORE V1)
def fake_rc1_fresh(*a, **kw):
    class R:
        returncode = 1
        stdout = ""
        stderr = ""
    p = os.path.join(appmod.DATA_DIR, "design_compliance.json")
    os.utime(p, None)  # mtime = bay gio
    print("  [debug] mtime=%.3f now=%.3f" % (os.path.getmtime(p), time.time()))
    return R()


with mock.patch("subprocess.run", side_effect=fake_rc1_fresh):
    r = show("EDGE rc=1 + JSON moi (mong 200)", c.get("/daoanh/api/compliance/dashboard?regenerate=1"))
    print("  has_failures:", (r.get_json(silent=True) or {}).get("has_failures"))
    results["rc1_fresh"] = r.status_code

# 4) search: 3 key DILA van con (khong regression)
r = show("GET /daoanh/api/search?q=Huyền Trang", c.get("/daoanh/api/search", query_string={"q": "Huyền Trang"}))
sb = r.get_json(silent=True) or {}
print("  keys:", sorted(sb.keys()))
print("  has dila_works/dila_people/dila_works_total:",
      all(k in sb for k in ("dila_works", "dila_people", "dila_works_total")))
results["search"] = r.status_code

# 5) dila_works A000294 -> 78
r = show("GET /daoanh/api/public/dila_works?person_id=A000294",
         c.get("/daoanh/api/public/dila_works", query_string={"person_id": "A000294"}))
dw = r.get_json(silent=True) or {}
print("  count:", dw.get("count"), "| total:", dw.get("total"), "| keys:", sorted(dw.keys()))
results["dila_works"] = r.status_code

# 6) search Khuy Co / Long Mon (de doi chieu guard V2 o phia client)
for q in ("Khuy Cơ", "Long Môn"):
    r = show("GET /daoanh/api/search?q=" + q, c.get("/daoanh/api/search", query_string={"q": q}))
    sb = r.get_json(silent=True) or {}
    print("  monks:", len(sb.get("monks") or []), "| places:", len(sb.get("places") or []),
          "| works:", len(sb.get("works") or []),
          "| dila_works:", len(sb.get("dila_works") or []),
          "| dila_people:", len(sb.get("dila_people") or []))

print("\nSUMMARY", json.dumps(results))
