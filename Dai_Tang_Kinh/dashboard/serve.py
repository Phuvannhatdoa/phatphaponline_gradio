#!/usr/bin/env python3
"""
DILA Team Dashboard — minimal static server + 1 endpoint.

Mục đích:
  - Serve /dashboard/*.html|css|js và /tasks/*.md như một static server bình thường.
  - Thêm duy nhất 1 endpoint POST /api/task-status để nút Approve/Reject
    cập nhật đúng dòng "## Status" trong đúng file task.

KHÔNG:
  - gọi agent nào (Claude Code / OpenCode / DeepSeek)
  - tạo state file, agents.json, progress_tracker
  - tự tính / tự sinh progress
  - ghi bất kỳ file nào ngoài dòng Status của task được chọn

Chạy:
  python dashboard/serve.py            # mặc định http://127.0.0.1:8090
  python dashboard/serve.py --port 9000 --host 127.0.0.1
"""

import argparse
import csv
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DASHBOARD_DIR)          # thư mục chứa dashboard/ và tasks/
TASKS_DIR = os.path.join(ROOT_DIR, "tasks")
DASHBOARD_PATH = "/dashboard/agent_team.html"

ALLOWED_STATUS = {"approved", "rejected"}
SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")

# --- task thật daoanh/tasks: cho phép đổi status qua dashboard ---
REAL_TASKS_DIR = os.path.join(ROOT_DIR, "daoanh", "tasks")
ALLOWED_REAL_STATUS = {
    "pending", "in_progress", "debugging", "blocked", "done", "deferred",
    "partial", "superseded", "cancelled", "qa", "review",
}
MAX_NOTE_LEN = 4000

# --- Khi Admin xác nhận DONE (task thật → status: done): build progress data rồi báo Tiểu Thiên ---
DAOANH_DIR = os.path.join(ROOT_DIR, "daoanh")
BUILD_PROGRESS_REL = os.path.join("scripts", "build_progress_data.py")
NOTIFY_DONE_REL = os.path.join("scripts", "notify_done.ps1")
SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._-]{1,60}$")

# --- Admin quyết định (2026-11-02): nút "Xác nhận DONE" của tab Visual CHỈ ghi status: done
# vào file task trong worktree coder-<id> tương ứng, KHÔNG ghi vào cây chính (REAL_TASKS_DIR).
# Việc đọc danh sách task/phân loại vẫn lấy từ cây chính như cũ (_main_tree_tasks).
WORKTREES_ROOT = os.path.join(os.path.expanduser("~"), ".claude", "worktrees")


def _one_line(text, limit=150):
    t = " ".join(str(text or "").split())
    return t[:limit] + ("…" if len(t) > limit else "")


def read_task_meta(path):
    """Đọc nhanh id/title trong frontmatter task thật."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(4000)
    except OSError:
        return {}
    m = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", head)
    fm = m.group(1) if m else ""
    out = {}
    for key in ("id", "title"):
        km = re.search(r"^" + key + r"\s*:\s*(.+)$", fm, re.M)
        if km:
            v = km.group(1).strip().strip('"').strip("'")
            out[key] = v
    return out


def run_done_pipeline(task_id, title, dry=False, skip_notify=False, wt_dir=None):
    """
    Luồng Admin xác nhận DONE:
      1) python scripts/build_progress_data.py   (trong <wt_dir>/Dai_Tang_Kinh/daoanh/,
             KHÔNG ghi cây chính — Admin quyết định 2026-11-02: "Ghi qua worktree".
             Nếu không có wt_dir (không tìm thấy worktree giữ file task), BỎ QUA bước
             build này và ghi cảnh báo vào log — không fallback về cây chính.)
      2) powershell -ExecutionPolicy Bypass -File scripts/notify_done.ps1
             -Title "T<id> Done" -Message "<mô tả ngắn>"   (giữ nguyên, vẫn chạy ở cây chính)
    Chỉ chạy khi được gọi từ hành động chuyển status → done (Admin xác nhận).
    dry=True: chỉ trả lệnh, không chạy (dùng để kiểm tra).
    """
    tid = str(task_id or "").strip()
    if not SAFE_TASK_ID.match(tid):
        return {"ok": False, "skipped": True, "error": "task id không hợp lệ"}
    if not tid.upper().startswith(("T", "BUG", "G")):
        tid = "T" + tid
    msg = _one_line(title) or ("Hoàn thành " + tid)
    notify_title = tid + " Done"

    # Thư mục daoanh/ dùng để chạy build_progress_data.py: PHẢI là worktree (wt_dir),
    # không fallback về DAOANH_DIR (cây chính) khi không có wt_dir.
    build_daoanh_dir = os.path.join(wt_dir, "Dai_Tang_Kinh", "daoanh") if wt_dir else None

    build_rel = BUILD_PROGRESS_REL
    notify_rel = NOTIFY_DONE_REL
    build_cmd = [sys.executable, build_rel]
    notify_cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", notify_rel,
                  "-Title", notify_title, "-Message", msg]

    if dry:
        return {
            "ok": True, "dry": True, "cwd": DAOANH_DIR,
            "build_cwd": build_daoanh_dir,
            "build": build_cmd, "notify": notify_cmd,
            "title": notify_title, "message": msg,
        }

    steps = []

    # 1) build progress data — chạy trong worktree (wt_dir), không ghi cây chính.
    if not build_daoanh_dir:
        steps.append({"step": "build_progress_data", "ok": False, "skipped": True,
                      "error": "không có wt_dir (không tìm thấy worktree giữ file task) → "
                               "bỏ qua build, không fallback về cây chính"})
        log(f"[notify] {tid}: bỏ qua build_progress_data — không có wt_dir "
            f"(không tìm thấy worktree giữ file task)")
    elif os.path.isfile(os.path.join(build_daoanh_dir, build_rel)):
        try:
            r = subprocess.run(build_cmd, cwd=build_daoanh_dir, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=180)
            tail = (r.stdout or "") + (r.stderr or "")
            steps.append({"step": "build_progress_data", "ok": r.returncode == 0,
                          "rc": r.returncode, "cwd": build_daoanh_dir, "tail": tail[-500:]})
        except Exception as e:
            steps.append({"step": "build_progress_data", "ok": False, "error": str(e)})
    else:
        steps.append({"step": "build_progress_data", "ok": False, "skipped": True,
                      "error": f"không thấy {build_rel} trong {build_daoanh_dir}"})

    # 2) Tiểu Thiên báo Done (script tự chọn ảnh ngẫu nhiên + phát âm thanh)
    if skip_notify:
        steps.append({"step": "notify_done", "ok": True, "skipped": True,
                      "note": "skip_notify=true (chỉ chạy build)"})
    elif os.path.isfile(os.path.join(DAOANH_DIR, notify_rel)):
        try:
            r2 = subprocess.run(notify_cmd, cwd=DAOANH_DIR, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=90)
            tail2 = (r2.stdout or "") + (r2.stderr or "")
            steps.append({"step": "notify_done", "ok": r2.returncode == 0, "rc": r2.returncode,
                          "title": notify_title, "message": msg, "tail": tail2[-300:]})
        except Exception as e:
            steps.append({"step": "notify_done", "ok": False, "error": str(e)})
    else:
        steps.append({"step": "notify_done", "ok": False, "skipped": True,
                      "error": "không thấy scripts/notify_done.ps1"})

    return {"ok": all(s.get("ok") for s in steps), "steps": steps,
            "title": notify_title, "message": msg}


# --- Kết quả lần chạy nền gần nhất + hàng đợi (vì build_progress_data mất ~60-90s) ---
LAST_NOTIFY = {"state": "idle", "started": None, "finished": None, "result": None}
_NOTIFY_LOCK = threading.Lock()


def _run_done_pipeline_bg(task_id, title, skip_notify=False, wt_dir=None):
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    with _NOTIFY_LOCK:
        LAST_NOTIFY.update({"state": "running", "started": started,
                            "finished": None, "result": None,
                            "task_id": task_id, "title": task_id + " Done"})
    try:
        result = run_done_pipeline(task_id, title, dry=False, skip_notify=skip_notify,
                                   wt_dir=wt_dir)
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    with _NOTIFY_LOCK:
        LAST_NOTIFY.update({"state": "done" if result.get("ok") else "error",
                            "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "result": result})
    log(f"[notify-bg] {task_id}: " + ("ok" if result.get("ok") else "có lỗi"))


def queue_done_pipeline(task_id, title, skip_notify=False, wt_dir=None):
    """Chạy nền, trả về ngay để UI không phải chờ 60-90s."""
    threading.Thread(target=_run_done_pipeline_bg,
                     args=(task_id, title, skip_notify, wt_dir), daemon=True).start()
    return {"queued": True, "title": task_id + " Done",
            "message": _one_line(title), "state_url": "/api/notify-done/last"}


# =====================================================================
#  NGỮ CẢNH MÔ TẢ TASK — bù mô tả cho task thiếu, lấy từ các file .md
# =====================================================================
DOCS_DIR = os.path.join(ROOT_DIR, "daoanh", "docs")
TASK_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_-])(T\d{1,4}|BUG-?\d{1,4}|G\d{1,4})(?![0-9])")
OWN_SECTIONS = (
    "mô tả", "mô tả nhiệm vụ", "mục tiêu", "mục đích", "tóm tắt", "bối cảnh",
    "overview", "summary", "description", "goal", "objective", "vấn đề",
    "phân tích", "cách tiếp cận", "approach", "ràng buộc", "constraints",
    "hiện trạng", "yêu cầu", "audit", "bàn giao", "đề xuất", "giải pháp",
)
SKIP_DOC_DIRS = {"_book", "archive", "node_modules", ".git", "mockup", "data-exports"}
CONTEXT_CACHE = {"index": None, "built_at": None, "docs": 0, "ids": 0,
                 "composed": None, "composed_at": None}
_CONTEXT_LOCK = threading.Lock()


def norm_task_key(token):
    """T22 → T22, BUG-025 → BUG025 (bỏ hyphen) để so khớp chéo file."""
    k = str(token or "").strip().upper().replace(" ", "")
    return k.replace("-", "")


def _norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def extract_own_description(text):
    """Mô tả lấy từ chính file task: các section Mô tả/Mục tiêu/Cách tiếp cận/Audit…"""
    parts = []
    cur_name, cur_lines = None, []

    def flush():
        if cur_name and any(cur_name.startswith(p) for p in OWN_SECTIONS):
            body = "\n".join(cur_lines).strip()
            body = re.sub(r"\n{2,}", "\n\n", body)
            if body:
                first = [p for p in re.split(r"\n\s*\n", body) if p.strip()][:2]
                if first:
                    parts.append((cur_name, _norm_ws(" ".join(first))[:700]))

    for line in str(text).replace("\r\n", "\n").split("\n"):
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if m:
            flush()
            cur_name = m.group(2).strip().lower()
            cur_lines = []
        else:
            cur_lines.append(line)
    flush()

    if parts:
        return "\n\n".join(name[:1].upper() + name[1:] + ": " + body for name, body in parts[:3])

    # fallback: đoạn văn đầu tiên không phải heading/bảng/checklist
    body_text = re.sub(r"^---\n.*?\n---\n", "", str(text), count=1, flags=re.S)
    para = []
    for line in body_text.split("\n"):
        s = line.strip()
        if not s:
            if para:
                break
            continue
        if s.startswith("#") or s.startswith("|") or re.match(r"^[-*]\s*\[", s):
            if para:
                break
            continue
        para.append(re.sub(r"^>\s*", "", s))
    return _norm_ws(" ".join(para))[:600]


def build_context_index(force=False):
    """Quét các file .md trong daoanh/docs để gom ngữ cảnh theo mã task."""
    with _CONTEXT_LOCK:
        if CONTEXT_CACHE["index"] is not None and not force:
            return CONTEXT_CACHE["index"]
        index = {}
        n_docs = 0
        for root, dirs, files in os.walk(DOCS_DIR):
            dirs[:] = [d for d in dirs if d not in SKIP_DOC_DIRS]
            for fn in files:
                if not fn.lower().endswith(".md"):
                    continue
                path = os.path.join(root, fn)
                try:
                    if os.path.getsize(path) > 400_000 and fn.lower() != "tasktodo.md":
                        continue
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                except OSError:
                    continue
                n_docs += 1
                rel = os.path.relpath(path, ROOT_DIR).replace("\\", "/")
                base = fn.lower()
                kind = ("tasktodo" if base == "tasktodo.md"
                        else "handoff" if base.startswith("handoff")
                        else "doc")
                for block in re.split(r"\n\s*\n", text):
                    if not block or not TASK_TOKEN_RE.search(block):
                        continue
                    keys = {norm_task_key(m) for m in TASK_TOKEN_RE.findall(block)}
                    body = _norm_ws(block)
                    if len(body) < 60 or len(keys) > 6:
                        continue
                    for k in keys:
                        index.setdefault(k, []).append(
                            {"source": rel, "kind": kind, "text": body[:900]})

        CONTEXT_CACHE.update(index=index, built_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                             docs=n_docs, ids=len(index))
        log(f"[context] index: {len(index)} task id từ {n_docs} file docs")
        return index


# Admin 4A (2026-11-02): tab Visual đọc trạng thái task từ daoanh/tasks/ ở CÂY CHÍNH
# (REAL_TASKS_DIR, đã khai báo ở đầu file), không còn phụ thuộc worktree coder-*.
# Phát hiện tiến trình OpenCode đang chạy (_opencode_running_tasks) không phụ thuộc
# worktree nào nên giữ nguyên.
CODER_TASK_RE = re.compile(r"Coder\s+(T\d+[a-z]?)")
FRONTMATTER_ID_RE = re.compile(r"^id:\s*(\S+)\s*$", re.M)
FRONTMATTER_STATUS_RE = re.compile(r"^status:\s*(\S+)\s*$", re.M)
FRONTMATTER_TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.M)


TESTER_TASK_RE = re.compile(r"Tester\s+(T\d+[a-z]?)")


def _opencode_running_tasks():
    """Liệt kê tiến trình OpenCode đang chạy "Chạy Coder <ID>" và "Chạy Tester <ID>" (chỉ đọc, Windows).

    Trả (coder_running, tester_running), mỗi cái là dict {task_id: {pid, started}}.
    """
    # wmic nhanh hơn PowerShell Get-CimInstance nhiều trên máy này (≈6s thay vì ≈40s)
    try:
        proc_run = subprocess.run(
            ["wmic", "process", "where", "name='node.exe' or name='opencode.exe'",
             "get", "ProcessId,CommandLine,Name", "/format:csv"],
            capture_output=True, timeout=30)
        out = (proc_run.stdout or b"").decode("utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return {}, {}
    coder, tester = {}, {}
    for row in csv.DictReader(io.StringIO(out)):
        cmd = row.get("CommandLine") or ""
        m = CODER_TASK_RE.search(cmd)
        if m:
            coder[m.group(1)] = {"pid": row.get("ProcessId"), "started": None}
        m = TESTER_TASK_RE.search(cmd)
        if m:
            tester[m.group(1)] = {"pid": row.get("ProcessId"), "started": None}
    return coder, tester


def _sessions_dir_for_task(task_id, suffix):
    """Thư mục session <ID><suffix> (ví dụ '-coder') mới nhất trong daoanh/docs/sessions/
    ở CÂY CHÍNH, hoặc None nếu chưa có. Chỉ đọc, không phụ thuộc worktree."""
    sessions = os.path.join(DAOANH_DIR, "docs", "sessions")
    if not os.path.isdir(sessions):
        return None
    try:
        days = sorted(os.listdir(sessions), reverse=True)
    except OSError:
        return None
    for day in days:
        day_path = os.path.join(sessions, day)
        if not os.path.isdir(day_path):
            continue
        cand = os.path.join(day_path, task_id + suffix)
        if os.path.isdir(cand):
            return cand
    return None


def _tester_report_for_task(task_id):
    """Tìm báo cáo tester mới nhất cho task trong daoanh/docs/sessions/ CÂY CHÍNH
    (chỉ đọc tên file, không đọc nội dung)."""
    coder_dir = _sessions_dir_for_task(task_id, "-coder")
    if coder_dir is None:
        return None
    try:
        reports = [n for n in os.listdir(coder_dir) if n.upper().startswith("TESTER-REPORT")]
    except OSError:
        return None
    if not reports:
        return None
    # Lấy báo cáo mới nhất theo thời gian sửa (không theo tên: "TESTER-REPORT.md" < "TESTER-REPORT-4.md")
    return max(reports, key=lambda n: os.path.getmtime(os.path.join(coder_dir, n)))


def _main_tree_tasks():
    """Đọc id/status/title của task từ daoanh/tasks/ ở CÂY CHÍNH (REAL_TASKS_DIR) — nguồn sự
    thật duy nhất cho tab Visual (Admin 4A). KHÔNG đọc worktree coder-*.

    Raise RuntimeError nếu không đọc được thư mục tasks (báo lỗi rõ ràng, không trả rỗng âm thầm).
    """
    if not os.path.isdir(REAL_TASKS_DIR):
        raise RuntimeError(f"Không tìm thấy thư mục task cây chính: {REAL_TASKS_DIR}")
    try:
        names = os.listdir(REAL_TASKS_DIR)
    except OSError as e:
        raise RuntimeError(f"Không đọc được {REAL_TASKS_DIR}: {e}")

    tasks = {}
    for fname in names:
        if not fname.startswith("T") or not fname.endswith(".md"):
            continue
        path = os.path.join(REAL_TASKS_DIR, fname)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                head = fh.read(3000)
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        m_st = FRONTMATTER_STATUS_RE.search(head)
        if not m_st:
            continue
        m_id = FRONTMATTER_ID_RE.search(head)
        task_id = m_id.group(1) if m_id else fname.split("-", 1)[0]
        # Cùng 1 id có thể trùng tên file hiếm khi: lấy bản sửa gần nhất (mtime mới nhất)
        if task_id in tasks and tasks[task_id]["updated_ts"] >= mtime:
            continue
        m_title = FRONTMATTER_TITLE_RE.search(head)
        tasks[task_id] = {
            "task_id": task_id,
            "title": m_title.group(1) if m_title else task_id,
            "status": m_st.group(1),
            "file": fname,
            "tester_report": _tester_report_for_task(task_id),
            "updated_ts": mtime,
        }
    return tasks


def _main_task_path(task_id):
    """Đường dẫn file task (<ID>-*.md) trong daoanh/tasks/ CÂY CHÍNH, hoặc None."""
    if not os.path.isdir(REAL_TASKS_DIR):
        return None
    try:
        names = os.listdir(REAL_TASKS_DIR)
    except OSError:
        return None
    for fname in names:
        if fname.split("-", 1)[0] == task_id and fname.endswith(".md"):
            return os.path.join(REAL_TASKS_DIR, fname)
    return None


def _find_worktree_task_file(task_id):
    """Tìm file task <task_id>-*.md trong các worktree 'coder-*' (KHÔNG phải cây chính).

    Quét trực tiếp các thư mục con tên 'coder-*' trong WORKTREES_ROOT (tương đương
    liệt kê bằng 'git worktree list' nhưng chỉ đọc filesystem, không gọi git), tìm
    <worktree>/Dai_Tang_Kinh/daoanh/tasks/<task_id>-*.md. Nếu nhiều worktree cùng giữ
    file này, chọn bản có mtime mới nhất. Trả (path, worktree_dir) hoặc (None, None)
    nếu không worktree nào giữ file. Chỉ đọc, không ghi gì.
    """
    if not os.path.isdir(WORKTREES_ROOT):
        return None, None
    try:
        names = os.listdir(WORKTREES_ROOT)
    except OSError:
        return None, None

    candidates = []  # (mtime, path, worktree_dir)
    for name in names:
        if not name.lower().startswith("coder-"):
            continue
        wt_dir = os.path.join(WORKTREES_ROOT, name)
        tasks_dir = os.path.join(wt_dir, "Dai_Tang_Kinh", "daoanh", "tasks")
        if not os.path.isdir(tasks_dir):
            continue
        try:
            fnames = os.listdir(tasks_dir)
        except OSError:
            continue
        for fname in fnames:
            if fname.split("-", 1)[0] == task_id and fname.endswith(".md"):
                fpath = os.path.join(tasks_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                except OSError:
                    continue
                candidates.append((mtime, fpath, wt_dir))

    if not candidates:
        return None, None
    candidates.sort(key=lambda c: c[0], reverse=True)
    _, best_path, best_wt = candidates[0]
    return best_path, best_wt


def _tester_state(task, tester_running):
    """Trạng thái đoạn Tester: 'running' (đang test) | 'done' (đã test xong) | 'waiting' (chờ tester)."""
    if task["task_id"] in tester_running:
        return "running"
    if not task.get("tester_report"):
        return "waiting"
    coder_dir = _sessions_dir_for_task(task["task_id"], "-coder")
    if coder_dir is None:
        return "waiting"
    report_path = os.path.join(coder_dir, task["tester_report"])
    coder_report = os.path.join(coder_dir, "CODER-REPORT.md")
    coder_mtime = os.path.getmtime(coder_report) if os.path.exists(coder_report) else 0
    # Báo cáo tester phải mới hơn báo cáo coder: nếu coder làm lại sau đó thì vẫn là "chờ tester"
    return "done" if os.path.getmtime(report_path) >= coder_mtime else "waiting"


VISUAL_CACHE = {"snapshot": None, "started": False}
VISUAL_REFRESH_SECONDS = 8


def _visual_refresh_loop():
    """Luồng nền: quét tiến trình + worktree định kỳ, để request HTTP trả về ngay."""
    while True:
        try:
            VISUAL_CACHE["snapshot"] = _build_visual_live()
        except Exception as exc:  # không để luồng nền chết
            VISUAL_CACHE["snapshot"] = {"ok": False, "error": str(exc), "tasks": []}
        time.sleep(VISUAL_REFRESH_SECONDS)


def get_visual_live():
    """Trả snapshot mới nhất (luồng nền cập nhật mỗi VISUAL_REFRESH_SECONDS giây)."""
    if not VISUAL_CACHE["started"]:
        VISUAL_CACHE["started"] = True
        threading.Thread(target=_visual_refresh_loop, daemon=True).start()
    return VISUAL_CACHE["snapshot"] or {"ok": True, "loading": True,
                                        "generated_at": "", "tasks": []}


def _build_visual_live():
    """Trạng thái sống: task nào OpenCode đang chạy, task nào chờ tester, task nào đã xong.

    Nguồn task: daoanh/tasks/ ở CÂY CHÍNH (_main_tree_tasks, Admin 4A). Nếu không đọc được
    thư mục đó, trả ok=False kèm lỗi rõ ràng (không trả danh sách rỗng âm thầm)."""
    running, tester_running = _opencode_running_tasks()
    try:
        tasks = _main_tree_tasks()
    except RuntimeError as e:
        return {"ok": False, "error": str(e), "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "tasks": []}
    for task_id in running:
        if task_id not in tasks:
            tasks[task_id] = {"task_id": task_id, "title": task_id, "status": "coding",
                              "file": None, "tester_report": None, "updated_ts": 0}
    rows = []
    for task_id, t in tasks.items():
        proc = running.get(task_id)
        row = {**t, "running": proc is not None, "pid": proc and proc.get("pid"),
               "started": proc and proc.get("started")}
        row["tester_state"] = _tester_state(row, tester_running)
        rows.append(row)
    rows.sort(key=lambda r: (not r["running"], r["task_id"]))
    return {"ok": True, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "tasks": rows}


def get_task_contexts(force=False):
    """Trả contexts (cache 5 phút) để không compose lại mỗi lần F5."""
    now = time.time()
    cached = CONTEXT_CACHE.get("composed")
    if cached is not None and not force and CONTEXT_CACHE.get("composed_at") and \
            now - CONTEXT_CACHE["composed_at"] < 300:
        return cached
    files = []
    if os.path.isdir(REAL_TASKS_DIR):
        for name in sorted(os.listdir(REAL_TASKS_DIR)):
            if name.lower().endswith(".md") and not name.startswith("."):
                p = os.path.join(REAL_TASKS_DIR, name)
                if os.path.isfile(p):
                    files.append((p, name))
    contexts = compose_task_context(files) if files else {}
    CONTEXT_CACHE["composed"] = contexts
    CONTEXT_CACHE["composed_at"] = now
    log(f"[context] compose: {len(contexts)}/{len(files)} task có mô tả")
    return contexts


def compose_task_context(task_files):
    """Ghép mô tả chi tiết cho từng task: own sections + tasktodo + Handoff + docs."""
    index = build_context_index()
    out = {}
    for path, rel in task_files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        fm = read_task_meta(path)
        tid = str(fm.get("id") or os.path.basename(path).split("-")[0])
        key = norm_task_key(tid)
        own = extract_own_description(text)
        refs = index.get(key, [])
        ordered = sorted(refs, key=lambda r: {"tasktodo": 0, "handoff": 1}.get(r["kind"], 2))
        extra = []
        seen = {_norm_ws(own).lower()}
        for r in ordered:
            t = r["text"]
            if _norm_ws(t).lower() in seen:
                continue
            seen.add(_norm_ws(t).lower())
            extra.append({"source": r["source"], "kind": r["kind"], "text": t[:600]})
            if len(extra) >= 2:
                break
        if not own and extra:
            own = extra[0]["text"]
            extra = extra[1:]
        if not own and not extra:
            continue
        sources = [r["source"] for r in ordered[:2]]
        out[rel] = {
            "id": tid,
            "description": own,
            "extra": extra,
            "sources": sources,
            "done_when": str(fm.get("done_when") or "")[:500],
        }
    return out

# 3 nguồn dữ liệu THẬT mà dashboard được phép đọc (chỉ .md, không ghi gì ngoài Status của task DILA)
SOURCES = {
    "dila": {
        "dir": TASKS_DIR,
        "rel": "tasks",
        "label": "DILA Team tasks (format DILA)",
    },
    "real": {
        "dir": os.path.join(ROOT_DIR, "daoanh", "tasks"),
        "rel": "daoanh/tasks",
        "label": "Task thật của dự án (frontmatter)",
    },
    "docs": {
        "dir": os.path.join(ROOT_DIR, "daoanh", "docs"),
        "rel": "daoanh/docs",
        "label": "Tài liệu thật (docs)",
    },
}


def log(msg):
    """In log an toàn trên mọi console (cp1252/cp437/utf-8)."""
    text = str(msg)
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe = text.encode(enc, "replace").decode(enc, "replace")
        print(safe, flush=True)


def replace_file(tmp, path, attempts=6, delay=0.3):
    """
    os.replace trên Windows bị từ chối (WinError 5) khi file đích đang bị tiến trình khác
    giữ tạm thời (trình quét, editor). Thử lại vài lần trước khi báo lỗi.
    """
    for i in range(attempts):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(delay)


def safe_task_path(filename):
    """Trả về đường dẫn tuyệt đối nếu filename là task .md hợp lệ trong tasks/, ngược lại None."""
    name = unquote(filename or "").strip()
    if not name or not SAFE_FILENAME.match(name):
        return None
    path = os.path.realpath(os.path.join(TASKS_DIR, name))
    tasks_real = os.path.realpath(TASKS_DIR)
    # chặn path traversal: file phải nằm trực tiếp trong tasks/
    if os.path.dirname(path) != tasks_real:
        return None
    if not os.path.isfile(path):
        return None
    return path


def safe_real_task_path(filename):
    """Như safe_task_path nhưng cho daoanh/tasks/."""
    name = unquote(filename or "").strip()
    if not name or not SAFE_FILENAME.match(name):
        return None
    path = os.path.realpath(os.path.join(REAL_TASKS_DIR, name))
    if os.path.dirname(path) != os.path.realpath(REAL_TASKS_DIR):
        return None
    if not os.path.isfile(path):
        return None
    return path


def append_admin_note(path, note):
    """
    Ghi mô tả của Admin vào task file dưới section '## Admin Notes' (append, có timestamp).
    Chỉ THÊM dòng, không sửa nội dung cũ. Trả về timestamp đã dùng.
    """
    note = " ".join(str(note).split())        # gộp newline/spaces → 1 bullet
    if not note:
        raise ValueError("nội dung ghi chú rỗng")
    if len(note) > MAX_NOTE_LEN:
        raise ValueError(f"ghi chú quá dài (> {MAX_NOTE_LEN} ký tự)")

    stamp = time.strftime("%Y-%m-%d %H:%M")
    bullet = f"- [{stamp}] {note}\n"

    with open(path, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()

    heading_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+admin notes\s*$", line.strip(), re.I):
            heading_idx = i
            break

    if heading_idx is None:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append("\n## Admin Notes\n")
        lines.append(bullet)
    else:
        end = len(lines)
        for j in range(heading_idx + 1, len(lines)):
            if re.match(r"^#{1,2}\s", lines[j]):
                end = j
                break
        insert_at = end
        while insert_at - 1 > heading_idx and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines.insert(insert_at, bullet)

    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_note_", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
        replace_file(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return stamp


def rewrite_frontmatter_status(path, new_status):
    """
    Đổi đúng dòng `status:` trong YAML frontmatter của task thật.
    Mọi dòng khác giữ nguyên byte-for-byte. Trả (old, new).
    """
    with open(path, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()

    start = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start = i
            break
    if start is None:
        raise ValueError("file không có YAML frontmatter")

    end = None
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "---":
            end = j
            break
    if end is None:
        raise ValueError("frontmatter không đóng bằng '---'")

    for k in range(start + 1, end):
        m = re.match(r"^(\s*status\s*:\s*)(.*?)(\r?\n?)$", lines[k], re.I)
        if not m:
            continue
        old = m.group(2).strip().strip('"').strip("'")
        lines[k] = m.group(1) + new_status + m.group(3)

        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_task_", suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.writelines(lines)
            replace_file(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return old, new_status

    raise ValueError("frontmatter không có dòng 'status:'")


def rewrite_status(path, new_status):
    """
    Ghi đè đúng dòng giá trị ngay sau '## Status'. Mọi dòng khác giữ nguyên byte-for-byte.
    Trả về (old_status, new_status).
    """
    with open(path, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()

    heading = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "## status":
            heading = i
            break
    if heading is None:
        raise ValueError("file không có section '## Status'")

    value_idx = None
    for j in range(heading + 1, len(lines)):
        if lines[j].strip() == "":
            continue
        if lines[j].lstrip().startswith("#"):
            break
        value_idx = j
        break
    if value_idx is None:
        raise ValueError("section '## Status' rỗng")

    old = lines[value_idx].strip()
    eol = "\n" if lines[value_idx].endswith("\n") else ""
    lines[value_idx] = new_status + eol

    # ghi atomic: temp cùng thư mục + os.replace
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_task_", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
        replace_file(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return old, new_status


def list_tasks():
    """Liệt kê task: (file, size, mtime_iso) — chỉ metadata, không đọc nội dung."""
    items = []
    if not os.path.isdir(TASKS_DIR):
        return items
    for name in sorted(os.listdir(TASKS_DIR)):
        if not name.endswith(".md") or name.startswith("."):
            continue
        p = os.path.join(TASKS_DIR, name)
        if not os.path.isfile(p):
            continue
        st = os.stat(p)
        items.append({
            "file": name,
            "size": st.st_size,
            "modified": st.st_mtime,
        })
    return items


def list_dir_md(directory):
    """Liệt kê file .md (chỉ top-level) trong 1 thư mục nguồn — metadata + mtime."""
    items = []
    if not os.path.isdir(directory):
        return items
    for name in sorted(os.listdir(directory)):
        if not name.lower().endswith(".md") or name.startswith("."):
            continue
        p = os.path.join(directory, name)
        if not os.path.isfile(p):
            continue
        try:
            st = os.stat(p)
        except OSError:
            continue
        items.append({
            "file": name,
            "size": st.st_size,
            "modified": st.st_mtime,
        })
    return items


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    # ---------- helpers ----------
    def _json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _no_cache_static(self):
        self.send_header("Cache-Control", "no-store")

    def end_headers(self):
        if self.path.startswith(("/tasks/", "/dashboard/")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # ---------- routing ----------
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(302)
            self.send_header("Location", DASHBOARD_PATH)
            self.end_headers()
            return
        if path in ("/api/health", "/api/dashboard-health"):
            # BUG-052 fix (2026-10-26): /api/dashboard-health là alias additive của
            # /api/health, để local_gateway.py (cổng 8080) proxy riêng path này sang
            # serve.py mà không đụng route /api/health gốc của app.py:5000. agent_team.js
            # gọi /api/dashboard-health (không còn gọi /api/health) — xem agent_team.js.
            # Route /api/health cũ giữ nguyên hành vi, không đổi/xoá, để ai chạy serve.py
            # độc lập (ví dụ port 8090) vẫn dùng được như trước.
            self._json(200, {
                "ok": True,
                "mode": "dila-dashboard",
                "root": ROOT_DIR,
                "tasks_dir": TASKS_DIR,
                "dashboard": DASHBOARD_PATH,
                "sources": {k: v["rel"] for k, v in SOURCES.items()},
                "endpoints": ["GET /tasks/", "GET /api/list?source=real|docs",
                              "GET /tasks/<file>.md", "POST /api/task-status",
                              "POST /api/real-task-status", "POST /api/task-note",
                              "POST /api/notify-done", "GET /api/notify-done/last",
                              "GET /api/task-contexts (mô tả chi tiết task)",
                              "GET /api/dashboard-health (alias /api/health)"],
            })
            return
        if path == "/api/visual-live":
            # Trạng thái sống cho tab Visual: tiến trình OpenCode đang chạy + status task (chỉ đọc)
            self._json(200, get_visual_live())
            return
        if path == "/api/task-contexts":
            qs = parse_qs(urlparse(self.path).query)
            force = (qs.get("refresh") or ["0"])[0] == "1"
            contexts = get_task_contexts(force=force)
            self._json(200, {
                "ok": True,
                "built_at": CONTEXT_CACHE["built_at"],
                "docs_scanned": CONTEXT_CACHE["docs"],
                "ids_indexed": CONTEXT_CACHE["ids"],
                "count": len(contexts),
                "contexts": contexts,
            })
            return
        if path == "/api/notify-done/last":
            with _NOTIFY_LOCK:
                self._json(200, {"ok": True, "last": dict(LAST_NOTIFY)})
            return
        if path in ("/tasks/", "/tasks"):
            self._json(200, {"tasks": list_tasks(), "tasks_dir": TASKS_DIR})
            return
        if path == "/api/list":
            qs = parse_qs(urlparse(self.path).query)
            src = (qs.get("source") or ["dila"])[0]
            entry = SOURCES.get(src)
            if not entry:
                self._json(400, {"ok": False, "error": "source không hợp lệ: " + src,
                                 "allowed": sorted(SOURCES)})
                return
            files = list_dir_md(entry["dir"])
            self._json(200, {
                "ok": True,
                "source": src,
                "label": entry["label"],
                "dir": entry["rel"],
                "count": len(files),
                "files": files,
            })
            return
        # còn lại: static (dashboard/*.html|css|js, tasks/*.md)
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/visual-confirm-done":
            # Admin bấm nút "Xác nhận DONE" trên tab Visual. Đọc trạng thái/phân loại task từ
            # daoanh/tasks/ CÂY CHÍNH (không đổi — vẫn nguồn sự thật cho việc hiển thị/kiểm tra
            # "testing"), nhưng VIỆC GHI status: done chỉ thực hiện trong file task của worktree
            # coder-<id> tương ứng (Admin quyết định 2026-11-02: không ghi cây chính ở bước này).
            try:
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception as e:
                self._json(400, {"ok": False, "error": f"JSON không hợp lệ: {e}"})
                return
            task_id = str(payload.get("task_id", "")).strip()
            if not re.fullmatch(r"T\d{1,5}[a-z]?", task_id):
                self._json(400, {"ok": False, "error": f"task_id không hợp lệ: {task_id!r}"})
                return
            try:
                current = _main_tree_tasks().get(task_id)
            except RuntimeError as e:
                self._json(500, {"ok": False, "error": str(e)})
                return
            if not current:
                self._json(404, {"ok": False, "error": f"{task_id} không có trong daoanh/tasks/ (cây chính)"})
                return
            if current["status"] != "testing":
                self._json(409, {"ok": False, "error": f"{task_id} đang ở status "
                                 f"'{current['status']}', chỉ xác nhận DONE khi 'testing'"})
                return
            path_task, wt_dir = _find_worktree_task_file(task_id)
            if not path_task:
                self._json(404, {"ok": False, "error": f"không tìm thấy worktree coder-* nào giữ "
                                 f"file task của {task_id} (đã quét {WORKTREES_ROOT})"})
                return
            try:
                old, new = rewrite_frontmatter_status(path_task, "done")
            except Exception as e:
                self._json(500, {"ok": False, "error": f"ghi file thất bại: {e}"})
                return
            log(f"[admin-dashboard] {task_id} ({os.path.basename(path_task)} @ "
                f"{os.path.basename(wt_dir)}): {old} -> {new}")
            self._json(200, {"ok": True, "task_id": task_id, "old": old, "new": new,
                             "file": path_task, "worktree": wt_dir})
            return

        if path == "/api/real-task-status":
            # Admin quyết định (2026-11-02, cùng mẫu /api/visual-confirm-done): endpoint này
            # CHỈ ghi status vào file task trong worktree coder-<id> tương ứng, KHÔNG ghi vào
            # daoanh/tasks/ CÂY CHÍNH (REAL_TASKS_DIR). safe_real_task_path() vẫn dùng để
            # validate tên file/status hợp lệ và lấy task_id — không dùng path đó để ghi.
            try:
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception as e:
                self._json(400, {"ok": False, "error": f"JSON không hợp lệ: {e}"})
                return
            filename = payload.get("file", "")
            status = str(payload.get("status", "")).strip().lower()
            if status not in ALLOWED_REAL_STATUS:
                self._json(400, {"ok": False, "error": "status chỉ nhận: " +
                                 ", ".join(sorted(ALLOWED_REAL_STATUS))})
                return
            path_main = safe_real_task_path(filename)
            if not path_main:
                self._json(400, {"ok": False, "error": f"file không hợp lệ: {filename!r}"})
                return
            task_id = str(read_task_meta(path_main).get("id") or
                          os.path.basename(path_main).split("-", 1)[0])
            path_task, wt_dir = _find_worktree_task_file(task_id)
            if not path_task:
                self._json(404, {"ok": False, "error": f"không tìm thấy worktree coder-* nào "
                                 f"giữ file task của {task_id} (đã quét {WORKTREES_ROOT})"})
                return
            try:
                old, new = rewrite_frontmatter_status(path_task, status)
            except ValueError as e:
                self._json(422, {"ok": False, "error": str(e)})
                return
            except Exception as e:
                self._json(500, {"ok": False, "error": f"ghi file thất bại: {e}"})
                return
            log(f"[admin-dashboard] {task_id} ({os.path.basename(path_task)} @ "
                f"{os.path.basename(wt_dir)}): {old} -> {new}")

            # Admin xác nhận DONE → chạy build_progress_data.py rồi gọi Tiểu Thiên báo Done.
            # KHÔNG chạy khi: chưa phải done, đã done trước đó, hoặc task đang lỗi/chờ quyết định.
            notify = None
            if str(new).strip().lower() == "done" and str(old).strip().lower() != "done":
                meta = read_task_meta(path_task)
                title = meta.get("title", "")
                try:
                    if payload.get("wait") or payload.get("dry"):
                        notify = run_done_pipeline(task_id, title,
                                                   dry=bool(payload.get("dry")),
                                                   skip_notify=bool(payload.get("skipNotify")),
                                                   wt_dir=wt_dir)
                        log(f"[notify] {task_id}: " +
                            ("dry-run" if notify.get("dry") else
                             ("ok" if notify.get("ok") else "có bước lỗi")))
                    else:
                        # build_progress_data ~60-90s → chạy nền, trả về ngay
                        notify = queue_done_pipeline(task_id, title,
                                                     skip_notify=bool(payload.get("skipNotify")),
                                                     wt_dir=wt_dir)
                        log(f"[notify] {task_id}: queued (chạy nền)")
                except Exception as e:
                    notify = {"ok": False, "error": f"notify pipeline lỗi: {e}"}
                    log(f"[notify] lỗi: {e}")

            self._json(200, {"ok": True, "file": os.path.basename(path_task),
                             "worktree": wt_dir, "old": old, "status": new, "notify": notify})
            return

        if path == "/api/notify-done":
            # Gọi lại/kiểm tra pipeline "build_progress_data + Tiểu Thiên báo Done".
            try:
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception as e:
                self._json(400, {"ok": False, "error": f"JSON không hợp lệ: {e}"})
                return
            filename = payload.get("file", "")
            task_id = str(payload.get("id", "")).strip()
            title = str(payload.get("title", "")).strip()

            if filename:
                path_task = safe_real_task_path(filename)
                if not path_task:
                    self._json(400, {"ok": False, "error": f"file không hợp lệ: {filename!r}"})
                    return
                meta = read_task_meta(path_task)
                task_id = str(meta.get("id") or task_id)
                title = title or str(meta.get("title") or "")
            if not task_id:
                self._json(400, {"ok": False, "error": "thiếu id hoặc file task"})
                return

            # Build progress data phải ghi qua worktree coder-<id> giữ file task (Admin
            # quyết định 2026-11-02). Không tìm được worktree → wt_dir=None, run_done_pipeline
            # sẽ tự bỏ qua bước build (không fallback cây chính), chỉ còn notify_done.ps1.
            _, wt_dir = _find_worktree_task_file(task_id)

            skip = bool(payload.get("skipNotify"))
            if payload.get("wait") or payload.get("dry"):
                notify = run_done_pipeline(task_id, title, dry=bool(payload.get("dry")),
                                           skip_notify=skip, wt_dir=wt_dir)
                log(f"[notify-done] {task_id}: " + ("dry-run" if notify.get("dry") else
                                                     ("ok" if notify.get("ok") else "có bước lỗi")))
                self._json(200 if (notify.get("ok") or notify.get("dry")) else 207,
                           {"ok": bool(notify.get("ok")), "notify": notify})
            else:
                notify = queue_done_pipeline(task_id, title, skip_notify=skip, wt_dir=wt_dir)
                self._json(200, {"ok": True, "notify": notify})
            return

        if path == "/api/task-note":
            try:
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception as e:
                self._json(400, {"ok": False, "error": f"JSON không hợp lệ: {e}"})
                return
            src = str(payload.get("source", "dila")).strip().lower()
            filename = payload.get("file", "")
            note = payload.get("note", "")

            if src not in ("dila", "real"):
                self._json(400, {"ok": False, "error": "source chỉ nhận 'dila' hoặc 'real'"})
                return

            wt_dir = None
            if src == "dila":
                path_task = safe_task_path(filename)
                if not path_task:
                    self._json(400, {"ok": False, "error": f"file không hợp lệ: {filename!r}"})
                    return
            else:
                # Admin quyết định (2026-11-02, cùng mẫu /api/real-task-status): endpoint này
                # CHỈ ghi ghi chú vào file task trong worktree coder-<id> tương ứng, KHÔNG ghi
                # vào daoanh/tasks/ CÂY CHÍNH (REAL_TASKS_DIR). safe_real_task_path() vẫn dùng
                # để validate tên file hợp lệ và lấy task_id — không dùng path đó để ghi.
                path_main = safe_real_task_path(filename)
                if not path_main:
                    self._json(400, {"ok": False, "error": f"file không hợp lệ: {filename!r}"})
                    return
                task_id = str(read_task_meta(path_main).get("id") or
                              os.path.basename(path_main).split("-", 1)[0])
                path_task, wt_dir = _find_worktree_task_file(task_id)
                if not path_task:
                    self._json(404, {"ok": False, "error": f"không tìm thấy worktree coder-* nào "
                                     f"giữ file task của {task_id} (đã quét {WORKTREES_ROOT})"})
                    return

            try:
                stamp = append_admin_note(path_task, note)
            except ValueError as e:
                self._json(422, {"ok": False, "error": str(e)})
                return
            except Exception as e:
                self._json(500, {"ok": False, "error": f"ghi file thất bại: {e}"})
                return
            log(f"[admin-note] {src}/{os.path.basename(path_task)}"
                f"{(' @ ' + os.path.basename(wt_dir)) if wt_dir else ''} @ {stamp}")
            self._json(200, {"ok": True, "source": src, "file": os.path.basename(path_task),
                             "worktree": wt_dir, "stamp": stamp})
            return

        if path != "/api/task-status":
            self._json(404, {"ok": False, "error": "endpoint không tồn tại"})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw or "{}")
        except Exception as e:
            self._json(400, {"ok": False, "error": f"JSON không hợp lệ: {e}"})
            return

        filename = payload.get("file", "")
        status = str(payload.get("status", "")).strip().lower()

        if status not in ALLOWED_STATUS:
            self._json(400, {"ok": False, "error": "status chỉ nhận 'approved' hoặc 'rejected'"})
            return

        path_task = safe_task_path(filename)
        if not path_task:
            self._json(400, {"ok": False, "error": f"file không hợp lệ: {filename!r}"})
            return

        try:
            old, new = rewrite_status(path_task, status)
        except ValueError as e:
            self._json(422, {"ok": False, "error": str(e)})
            return
        except Exception as e:
            self._json(500, {"ok": False, "error": f"ghi file thất bại: {e}"})
            return

        log(f"[admin] {os.path.basename(path_task)}: {old} -> {new}")
        self._json(200, {"ok": True, "file": os.path.basename(path_task), "old": old, "status": new})

    def log_message(self, fmt, *args):
        # gọn log
        log("  %s %s" % (self.command, self.path))


def main():
    # Console Windows mặc định cp1252 → ép utf-8 để log tiếng Việt không crash
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="DILA Team Dashboard server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8090)
    args = ap.parse_args()

    if not os.path.isdir(TASKS_DIR):
        log(f"[!] Không thấy thư mục tasks/: {TASKS_DIR} — dashboard sẽ hiển thị rỗng.")

    ThreadingHTTPServer.allow_reuse_address = True
    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        log(f"[!] Không bind được {args.host}:{args.port}: {e}")
        sys.exit(1)

    url = f"http://{args.host}:{args.port}{DASHBOARD_PATH}"
    log("DILA Team Dashboard")
    log(f"  URL      : {url}")
    log(f"  Tasks dir: {TASKS_DIR}")
    log("  Mode     : static + POST /api/task-status (Approve/Reject)")
    log("  Agent    : KHÔNG gọi agent nào. Chỉ đọc/ghi file task.")
    log("  Ctrl+C để dừng.")

    # warm cache mô tả task (quét docs ~5s) để trang đầu mở nhanh
    def _warm():
        try:
            build_context_index()
            get_task_contexts()
        except Exception as e:
            log(f"[context] warm lỗi: {e}")
    threading.Thread(target=_warm, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("\nĐã dừng.")


if __name__ == "__main__":
    main()
