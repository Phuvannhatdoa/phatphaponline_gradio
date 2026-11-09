#!/usr/bin/env python3
"""T462 coder runner: gửi task cho model coder OpenRouter FREE, cho model dùng tool
đọc/tìm/sửa file (chỉ các file được phép), ghi log và kết quả vào thư mục session.

Dùng khi OpenCode GO và OpenCode free đều hết quota (xem tasks/T462-harness-coder-tester-loop.md).
Model coder phải khác model tester.

Chạy (từ thư mục daoanh/):
    python -X utf8 scripts/harness_coder_openrouter.py --task tasks/T445-placevn-wizard-ui-b0-b9.md \
        --session docs/sessions/2026-10-25/T445-coder --max-steps 80
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
TESTER_MODEL = "nvidia/nemotron-3.5-lightning:free"
ALLOWED_WRITE = {"admin/placevn.html", "app.py"}
ALLOWED_READ = ALLOWED_WRITE | {"tasks/T445-placevn-wizard-ui-b0-b9.md"}
MAX_READ_LINES = 200
MAX_GREP = 60

SYSTEM = """Bạn là CODER của dự án Đạo Ảnh (harness T462). Nhiệm vụ: code theo spec task.
Quy tắc bắt buộc:
- Chỉ sửa các file: admin/placevn.html, app.py. Không sửa file khác, không chạy lệnh shell, không ghi DB.
- Nền hiện tại là HEAD. KHÔNG xoá và KHÔNG sửa code có sẵn; chỉ THÊM phần mới (wizard, route mới).
- Route mới đặt ngay trước dòng `if __name__ == '__main__':` cuối cùng của app.py.
- Sửa bằng replace(file, old, new): old phải là đoạn duy nhất, copy đúng từng ký tự.
- Đọc từng đoạn bằng read_lines (tối đa 200 dòng); tìm bằng grep trước khi đọc.
- Khi xong spec, gọi done(summary) với danh sách việc đã làm và việc chưa làm. Không tự đánh DONE.
"""

TOOLS = [
    {"type": "function", "function": {"name": "read_lines", "description": "Đọc dòng [start,end] của file được phép (tối đa 200 dòng)",
        "parameters": {"type": "object", "properties": {"file": {"type": "string"}, "start": {"type": "integer"}, "end": {"type": "integer"}}, "required": ["file", "start", "end"]}}},
    {"type": "function", "function": {"name": "grep", "description": "Tìm chuỗi/regex trong file được phép, trả về số dòng và nội dung (tối đa 60 kết quả)",
        "parameters": {"type": "object", "properties": {"file": {"type": "string"}, "pattern": {"type": "string"}}, "required": ["file", "pattern"]}}},
    {"type": "function", "function": {"name": "replace", "description": "Thay đúng 1 lần xuất hiện của old bằng new trong file được phép để ghi",
        "parameters": {"type": "object", "properties": {"file": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["file", "old", "new"]}}},
    {"type": "function", "function": {"name": "done", "description": "Kết thúc, báo tóm tắt việc đã làm và việc chưa làm",
        "parameters": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}}},
]


def load_key():
    env = ROOT.parent / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("Không tìm thấy OPENROUTER_API_KEY trong .env")


def call_model(key, model, messages, tools):
    body = json.dumps({"model": model, "messages": messages, "tools": tools,
                       "tool_choice": "auto", "max_tokens": 4000}).encode("utf-8")
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429 and attempt < 3:
                time.sleep(30)
                continue
            raise SystemExit(f"HTTP {e.code}: {err}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < 3:
                time.sleep(20)
                continue
            raise SystemExit(f"Lỗi mạng sau 4 lần thử: {e}")


def check_file(name, allowed):
    if name not in allowed:
        raise ValueError(f"file không được phép: {name}")
    return ROOT / name


def tool_read_lines(args):
    p = check_file(args["file"], ALLOWED_READ)
    lines = p.read_text(encoding="utf-8").splitlines()
    start = max(1, int(args["start"]))
    end = min(len(lines), int(args["end"]), start + MAX_READ_LINES - 1)
    return "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))


def tool_grep(args):
    import re
    p = check_file(args["file"], ALLOWED_READ)
    pat = re.compile(args["pattern"])
    out = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if pat.search(line):
            out.append(f"{i}: {line[:240]}")
            if len(out) >= MAX_GREP:
                out.append("... (đã cắt)")
                break
    return "\n".join(out) or "(không có kết quả)"


def tool_replace(args, log):
    p = check_file(args["file"], ALLOWED_WRITE)
    text = p.read_text(encoding="utf-8")
    count = text.count(args["old"])
    if count != 1:
        return f"LỖI: old xuất hiện {count} lần, cần đúng 1. Hãy grep để lấy đoạn duy nhất."
    p.write_text(text.replace(args["old"], args["new"], 1), encoding="utf-8")
    log.append({"tool": "replace", "file": args["file"], "old_len": len(args["old"]), "new_len": len(args["new"])})
    return "OK: đã thay thế."


SYSTEM_TESTER = """Bạn là TESTER (OpenRouter) của dự án Đạo Ảnh (harness T462). Chỉ ĐỌC, không sửa code.
- Kiểm tra từng mục trong Verification Checklist của spec bằng read_lines/grep trên admin/placevn.html và app.py.
- Với mỗi mục: PASS (có bằng chứng dòng code), FAIL (nêu dòng và lý do), hoặc KHÔNG KIỂM ĐƯỢC (nói rõ vì sao, ví dụ cần trình duyệt).
- Không tự đánh DONE. Khi xong, gọi done(summary) với bảng PASS/FAIL và danh sách bug để Claude Code chuyển cho daoanh-debugger.
"""

TESTER_TOOLS = [t for t in TOOLS if t["function"]["name"] != "replace"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--session", required=True)
    ap.add_argument("--max-steps", type=int, default=80)
    ap.add_argument("--role", choices=["coder", "tester"], default="coder")
    args = ap.parse_args()

    session = ROOT / args.session
    session.mkdir(parents=True, exist_ok=True)
    task_text = (ROOT / args.task).read_text(encoding="utf-8")
    key = load_key()
    log = []
    transcript = session / f"transcript-{args.role}.jsonl"
    is_tester = args.role == "tester"
    model = TESTER_MODEL if is_tester else CODER_MODEL
    tools = TESTER_TOOLS if is_tester else TOOLS
    system = SYSTEM_TESTER if is_tester else SYSTEM

    if is_tester:
        first = f"Spec task (đọc kỹ, phần Verification Checklist là nội dung test):\n\n{task_text}\n\nBắt đầu kiểm từng mục bằng grep."
    else:
        first = f"Spec task (đọc kỹ):\n\n{task_text}\n\nBắt đầu bằng grep để tìm vị trí cần sửa trong placevn.html và app.py."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": first},
    ]
    summary = None
    with transcript.open("a", encoding="utf-8") as tf:
        for step in range(args.max_steps):
            resp = call_model(key, model, messages, tools)
            if "choices" not in resp:
                err = json.dumps(resp, ensure_ascii=False)[:300]
                if step > 0:
                    time.sleep(30)
                    resp = call_model(key, model, messages, tools)
                if "choices" not in resp:
                    raise SystemExit(f"Model không trả choices ở bước {step}: {err}")
            msg = resp["choices"][0]["message"]
            messages.append({k: v for k, v in msg.items() if v is not None})
            tf.write(json.dumps({"step": step, "message": msg}, ensure_ascii=False) + "\n")
            calls = msg.get("tool_calls") or []
            if not calls:
                messages.append({"role": "user", "content": "Hãy dùng tool. Khi xong, gọi done(summary)."})
                continue
            finished = False
            for c in calls:
                name = c["function"]["name"]
                try:
                    a = json.loads(c["function"]["arguments"] or "{}")
                    if name == "read_lines":
                        result = tool_read_lines(a)
                    elif name == "grep":
                        result = tool_grep(a)
                    elif name == "replace" and not is_tester:
                        result = tool_replace(a, log)
                    elif name == "replace":
                        result = "LỖI: tester không được sửa file."
                    elif name == "done":
                        summary = a.get("summary", "")
                        finished = True
                        result = "ok"
                    else:
                        result = f"tool không tồn tại: {name}"
                except Exception as e:  # lỗi tool trả về cho model, không dừng runner
                    result = f"LỖI: {e}"
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": result[:8000]})
            if finished:
                break

    out = session / ("tester_report.md" if is_tester else "coder_summary.md")
    out.write_text(
        f"# {'Tester' if is_tester else 'Coder'} (OpenRouter) — {model}\n\n{summary or '(không có done)'}\n\n## Thay đổi\n\n"
        + "\n".join(f"- {x['tool']} {x['file']} (old {x['old_len']} ký tự → new {x['new_len']} ký tự)" for x in log) + "\n",
        encoding="utf-8")
    print(f"Xong. Số lần sửa: {len(log)}. Báo cáo: {out}")


if __name__ == "__main__":
    sys.exit(main())
