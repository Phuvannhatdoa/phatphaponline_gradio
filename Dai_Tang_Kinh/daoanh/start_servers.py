"""Start all 3 servers: app.py:5000, server.py:5001, local_gateway.py:8080"""
import subprocess
import sys
import time
import os
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE, "dashboard")
os.makedirs(LOG_DIR, exist_ok=True)

def start(name, script):
    out = os.path.join(LOG_DIR, f"{script}_restart.out.log")
    err = os.path.join(LOG_DIR, f"{script}_restart.err.log")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, script)],
        stdout=open(out, "w"),
        stderr=open(err, "w"),
        cwd=BASE,
        shell=False,
    )
    write_log(f"Started {name} (PID={proc.pid})")
    return proc

def write_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "start_all.log"), "a") as f:
        f.write(f"[{ts}] {msg}\n")

write_log("=== Starting all 3 servers ===")

# 1. app.py:5000
proc1 = start("app.py:5000", "app.py")

# Wait for app.py to be ready
write_log("Waiting for app.py:5000 to be ready (max 60s)...")
ready = False
for i in range(30):
    time.sleep(2)
    try:
        urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=1)
        ready = True
        break
    except:
        pass
if ready:
    write_log("!OK: app.py:5000 listening.")
else:
    write_log("!WARN: app.py:5000 NOT listening within 60s!")

# 2. server.py:5001
proc2 = start("server.py:5001", "server.py")

write_log("Waiting for server.py:5001 to be ready (max 15s)...")
ready = False
for i in range(15):
    time.sleep(1)
    try:
        urllib.request.urlopen("http://127.0.0.1:5001/health", timeout=1)
        ready = True
        break
    except:
        pass
if ready:
    write_log("!OK: server.py:5001 listening.")
else:
    write_log("!WARN: server.py:5001 NOT listening within 15s!")

# 3. local_gateway.py:8080
proc3 = start("local_gateway.py:8080", "local_gateway.py")

write_log("Waiting for gateway:8080 to be ready (max 15s)...")
ready = False
for i in range(15):
    time.sleep(1)
    try:
        urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=1)
        ready = True
        break
    except:
        pass
if ready:
    write_log("!OK: local_gateway.py:8080 listening.")
else:
    write_log("!WARN: local_gateway.py:8080 NOT listening within 15s!")

write_log("All servers started. Monitor: background PIDs 1=app 2=gateway 3=server")
print("All servers started. Check dashboard/start_all.log for details.")
print(f"app.py PID: {proc1.pid}, server.py PID: {proc2.pid}, gateway.py PID: {proc3.pid}")