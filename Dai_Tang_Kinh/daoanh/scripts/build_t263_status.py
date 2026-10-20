"""
Sinh data/t263_h3_status.json cho dashboard_process.html.

Chỉ ĐỌC: file TSV audit T263, file task T263, và thư mục .claude/agents + skills.
Chỉ GHI: data/t263_h3_status.json. Không đụng DB, không đụng task file.

Chạy (ở thư mục daoanh/):
    python -X utf8 scripts/build_t263_status.py
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # daoanh/
PROJECT = ROOT.parent                                   # Dai_Tang_Kinh/
TSV = ROOT / "docs" / "evidence" / "2026-10-08_T263_h3_conflicts.tsv"
SUMMARY = ROOT / "docs" / "evidence" / "2026-10-08_T263_h3_conflicts_summary.tsv"
TASK = ROOT / "tasks" / "T263-h3-year-conflict-resolution.md"
AGENTS_DIR = PROJECT / ".claude" / "agents"
SKILLS_DIR = PROJECT / ".claude" / "skills"
TASK_T265 = ROOT / "tasks" / "T265-h3-year-support-plan.md"
TASK_T269 = ROOT / "tasks" / "T269-ai-dich-rules-enforcement.md"
TASK_T273 = ROOT / "tasks" / "T273-review-destruction-events.md"
TASK_T274 = ROOT / "tasks" / "T274-vn-lineage-ttl-rule.md"
TASK_T275 = ROOT / "tasks" / "T275-ttl-anchor-generation.md"
TASK_T276 = ROOT / "tasks" / "T276-spec-t170-review-fixes.md"
TASK_T277 = ROOT / "tasks" / "T277-archive-and-future-integration.md"
DB = ROOT / "data" / "lineage.db"
OUT = ROOT / "data" / "t263_h3_status.json"


def read_plan(path, section_prefix="## 3."):
    """Đọc checklist '- [x] / - [ ]' trong mục có tiêu đề bắt đầu bằng section_prefix.

    Mặc định '## 3.' (mục 'Các bước' của task T265). Truyền section_prefix khác
    cho task có số mục khác (ví dụ T269 dùng '## 2. Các bước').
    """
    if not path.exists():
        return []
    steps, in_section = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.startswith(section_prefix)
            continue
        if in_section:
            m = re.match(r"^- \[( |x)\] (.*)$", line)
            if m:
                steps.append({"done": m.group(1) == "x", "text": m.group(2)})
    return steps


def read_support():
    """Đếm quyết định trong timeline_year_support (chỉ đọc)."""
    import sqlite3
    if not DB.exists():
        return {"exists": False, "counts": {}}
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='timeline_year_support'"
        ).fetchone()
        if not exists:
            return {"exists": False, "counts": {}}
        rows = con.execute("SELECT status, COUNT(*) FROM timeline_year_support GROUP BY status").fetchall()
        return {"exists": True, "counts": {s: n for s, n in rows}}
    finally:
        con.close()


def read_tsv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_frontmatter(path):
    """Đọc YAML frontmatter đơn giản (key: value một dòng) — đủ cho các trường cần hiển thị."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = {}
    if not m:
        return meta
    for line in m.group(1).splitlines():
        mm = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if mm:
            meta[mm.group(1)] = mm.group(2).strip().strip('"')
    return meta


def read_agent(path):
    meta = {"file": path.name}
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^(name|model):\s*(.*)$", line)
            if mm:
                meta[mm.group(1)] = mm.group(2).strip()
    return meta


def list_skills():
    out = []
    if not SKILLS_DIR.exists():
        return out
    for p in sorted(SKILLS_DIR.iterdir()):
        if p.is_dir() and (p / "SKILL.md").exists():
            out.append({"name": p.name, "file": f"{p.name}/SKILL.md"})
        elif p.is_file() and p.suffix == ".md":
            out.append({"name": p.stem, "file": p.name})
    return out


def pipeline_stats():
    """T276: thống kê side-car T170/T169 (chỉ đọc). Lỗi không làm hỏng dashboard."""
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import t276_audit_stats as t276
        return t276.collect()
    except Exception as ex:
        return {"ok": False, "error": str(ex), "tables": {}}


def integration_tasks():
    """Khu Integration: trạng thái các task T283–T353 (đọc frontmatter, chỉ đọc)."""
    out = []
    for p in sorted((ROOT / "tasks").glob("T*.md")):
        n = int(p.name[1:4]) if p.name[1:4].isdigit() else 0
        if 283 <= n <= 353:
            meta = read_frontmatter(p)
            out.append({"id": meta.get("id", p.name[:4]), "title": meta.get("title", ""), "status": meta.get("status", "")})
    return out


def main():
    for p in (TSV, SUMMARY, TASK):
        if not p.exists():
            print(f"[LỖI] Không thấy file: {p}", file=sys.stderr)
            return 1

    rows = read_tsv(TSV)
    summary = read_tsv(SUMMARY)
    meta = read_frontmatter(TASK)

    counts = {"B": 0, "C": 0, "A": 0}
    for r in rows:
        if r["group"] in counts:
            counts[r["group"]] += 1

    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": {
            "id": meta.get("id", "T263"),
            "title": meta.get("title", ""),
            "status": meta.get("status", ""),
            "updated": meta.get("updated", ""),
            "done_when": "audit_h3_conflicts.py --strict trả 0",
            "phase": "P1 xong · lô B đã áp dụng (T265) · lô C, A chờ Admin duyệt",
        },
        "totals": {
            "conflict": len(rows),
            "groups": counts,
            "summary": summary,
        },
        "rows": rows,
        "plan": {
            "task": "T265",
            "steps": read_plan(TASK_T265),
            "support": read_support(),
        },
        "plan2": {
            "task": "T269",
            # Chỉ lấy 7 "Bước N" (bỏ dòng checklist cuối "Admin xác nhận DONE."
            # — đó là cổng xác nhận, không phải bước thực hiện).
            "steps": [
                s for s in read_plan(TASK_T269, section_prefix="## 2.")
                if s["text"].startswith("**Bước")
            ],
        },
        "plan3": {
            "task": "T273",
            "steps": read_plan(TASK_T273),
        },
        "plan4": {
            "task": "T274",
            "steps": read_plan(TASK_T274),
        },
        "plan5": {
            "task": "T275",
            "steps": read_plan(TASK_T275),
        },
        "plan6": {
            "task": "T276",
            "steps": read_plan(TASK_T276),
        },
        "plan7": {
            "task": "T277",
            "steps": read_plan(TASK_T277),
        },
        "pipeline": pipeline_stats(),
        "integration": integration_tasks(),
        "harness": {
            "agents": [read_agent(p) for p in sorted(AGENTS_DIR.glob("*.md"))] if AGENTS_DIR.exists() else [],
            "skills": list_skills(),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(rows)} dòng CONFLICT (B={counts['B']} C={counts['C']} A={counts['A']}) -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
