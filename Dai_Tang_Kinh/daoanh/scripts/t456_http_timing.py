# -*- coding: utf-8 -*-
"""T456 — đo latency end-to-end qua HTTP (server đang chạy) cho các endpoint liên quan."""
import json, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASES = ["http://127.0.0.1:5000", "http://127.0.0.1:8080"]
PATHS = [
    "/daoanh/api/search/suggest?q={q}",
    "/daoanh/api/public/autocomplete?q={q}",
    "/daoanh/api/search?q={q}",
]
QS = ["Huy", "Thi", "Long", "Tâm", "Thiếu", "Nghĩa"]


def hit(base, path, timeout=15):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            body = r.read()
            ms = (time.perf_counter() - t0) * 1000
            return ms, r.status, body
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        return ms, None, str(e).encode("utf-8", "replace")


for base in BASES:
    print("=" * 70)
    print("BASE:", base)
    for tmpl in PATHS:
        print("  ", tmpl)
        for q in QS:
            path = tmpl.replace("{q}", urllib.parse.quote(q))
            times, status, body = [], None, b""
            for _ in range(3):
                ms, status, body = hit(base, path)
                times.append(ms)
            note = ""
            if status == 200:
                try:
                    d = json.loads(body.decode("utf-8", "replace"))
                    if isinstance(d, dict):
                        keys = {k: (len(v) if isinstance(v, list) else v) for k, v in d.items()
                                if isinstance(v, (list, int, float, str)) and k in
                                ("persons", "works", "places", "monks", "success", "count", "_timing_ms")}
                        note = str(keys)[:130]
                except Exception:
                    note = body[:80].decode("utf-8", "replace")
            else:
                note = body[:110].decode("utf-8", "replace").replace("\n", " ")
            print("     q=%-8s min=%6.1fms  http=%s  %s" % (q, min(times), status, note))
