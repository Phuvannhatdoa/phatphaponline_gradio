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
    with open(os.path.join(LOG_DIR, "start_all.log"), "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

write_log("=== Starting all 3 servers ===")

def check_port_ready(port, max_wait_seconds, interval=2):
    """Check if a port has a process listening (TCP connectivity check)."""
    write_log(f"Checking port {port} readiness (max {max_wait_seconds}s)...")
    elapsed = 0
    while elapsed < max_wait_seconds:
        time.sleep(interval)
        try:
            # Use urllib to check if server responds on the port
            # This works because Flask returns a 404 page even when running,
            # but the connection itself proves the server is listening
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
            write_log(f"✅ Port {port} is responding.")
            return True
        except Exception:
            elapsed += interval
    write_log(f"⚠️ Port {port} NOT responding within {max_wait_seconds}s.")
    return False

# 1. app.py:5000
proc1 = start("app.py:5000", "app.py")
check_port_ready(5000, 60)

# 2. server.py:5001
proc2 = start("server.py:5001", "server.py")
check_port_ready(5001, 15)

# 3. local_gateway.py:8080
proc3 = start("local_gateway.py:8080", "local_gateway.py")
check_port_ready(8080, 15)

write_log("All servers started. Monitor: background PIDs 1=app 2=gateway 3=server")
print("All servers started. Check dashboard/start_all.log for details.")
print(f"app.py PID: {proc1.pid}, server.py PID: {proc2.pid}, gateway.py PID: {proc3.pid}")