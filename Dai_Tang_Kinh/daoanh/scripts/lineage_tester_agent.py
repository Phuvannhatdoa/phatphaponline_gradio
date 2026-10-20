#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lineage_tester_agent.py — Agent tự động kiểm tra lỗi logic truyền thừa trong DB

Chạy:
    python scripts/lineage_tester_agent.py
    python scripts/lineage_tester_agent.py --monk "Đan Hà Thiên Nhiên"
    python scripts/lineage_tester_agent.py --check cycles
    python scripts/lineage_tester_agent.py --limit 500

Kết quả lưu vào: test-results/lineage_audit_YYYYMMDD_HHMMSS.json
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False
    print("[WARN] networkx chưa cài — bỏ qua kiểm tra chu trình. Cài bằng: pip install networkx")

# ───────────────────────────────────────────────────────────────────
# CẤU HÌNH
# ───────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "lineage.db"
OUT_DIR  = BASE_DIR / "test-results"

# Danh sách thiền sư "hạt nhân" để bắt đầu — mỗi người có lý do test riêng
SEED_MONKS = [
    "Đan Hà Thiên Nhiên",   # học cả Mã Tổ lẫn Thạch Đầu — 2 dòng thầy khác nguồn
    "Mã Tổ Đạo Nhất",       # trung tâm mạng lưới Thiền Tông Đường — rất nhiều môn đệ
    "Thạch Đầu Hi Thiên",   # song song với Mã Tổ — dễ nhầm truyền thừa
    "Lâm Tế Nghĩa Huyền",  # sáng lập Lâm Tế tông — sử liệu phong phú
    "Triệu Châu Tùng Thẩm", # tuổi thọ đặc biệt cao (778–897 = 120 tuổi) → test lifespan
    "Hoàng Bá Hi Vận",      # thầy của Lâm Tế — hay bị nhầm thứ tự
    "Lục Tổ Huệ Năng",      # gốc của toàn bộ cây — nếu có cycle ở đây là lỗi nghiêm trọng
    "Bách Trượng Hoài Hải", # lập Thiền Lâm — quan trọng cho mốc lịch sử
]

# Khoảng năm theo triều đại Trung Quốc (dùng để kiểm tra dynasty mismatch)
DYNASTY_RANGES = {
    "Đông Hán":    (25,   220),
    "Tây Tấn":     (265,  316),
    "Đông Tấn":    (317,  420),
    "Lưu Tống":    (420,  479),
    "Nam Tề":      (479,  502),
    "Lương":       (502,  557),
    "Trần":        (557,  589),
    "Tùy":         (581,  618),
    "Đường":       (618,  907),
    "Ngũ Đại":     (907,  960),
    "Tống":        (960,  1279),
    "Bắc Tống":    (960,  1127),
    "Nam Tống":    (1127, 1279),
    "Nguyên":      (1271, 1368),
    "Minh":        (1368, 1644),
    "Thanh":       (1644, 1912),
    # tên tiếng Anh phổ biến trong DB
    "Tang":  (618,  907),
    "Song":  (960,  1279),
    "Yuan":  (1271, 1368),
    "Ming":  (1368, 1644),
    "Qing":  (1644, 1912),
    "Han":   (206,  220),
}

# ───────────────────────────────────────────────────────────────────
# KẾT NỐI DB VÀ PHÁT HIỆN BẢNG
# ───────────────────────────────────────────────────────────────────

def connect_db():
    if not DB_PATH.exists():
        sys.exit(f"[LỖI] Không tìm thấy DB: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn):
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return {r[0] for r in cur.fetchall()}


def detect_schema(conn):
    """Phát hiện tên cột thực tế của các bảng chính trong DB."""
    tables = list_tables(conn)
    schema = {}

    for tbl in ["people", "persons", "monks", "person_authority",
                "networks", "lineage", "relationships",
                "marcus_reference"]:
        if tbl in tables:
            cur = conn.execute(f"PRAGMA table_info({tbl})")
            schema[tbl] = {r["name"] for r in cur.fetchall()}

    return schema, tables


# ───────────────────────────────────────────────────────────────────
# LOADER: load dữ liệu người + quan hệ
# ───────────────────────────────────────────────────────────────────

def load_people(conn, schema, limit=None):
    """Trả về dict id → {name, birth, death, dynasty, sources...}."""
    people = {}

    for tbl in ["people", "persons", "monks", "person_authority"]:
        if tbl not in schema:
            continue
        cols = schema[tbl]

        # Ánh xạ cột thực tế
        id_col    = next((c for c in ["id", "person_id", "dila_id"] if c in cols), None)
        name_cols = [c for c in ["name_vi", "name_zh", "name_en", "label", "label_vi"] if c in cols]
        birth_col = next((c for c in ["birth_year", "birth", "year_birth"] if c in cols), None)
        death_col = next((c for c in ["death_year", "death", "year_death"] if c in cols), None)
        dyn_col   = next((c for c in ["dynasty", "era"] if c in cols), None)
        src_col   = next((c for c in ["source", "sources"] if c in cols), None)

        if not id_col:
            continue

        sel = [id_col] + name_cols
        if birth_col: sel.append(birth_col)
        if death_col: sel.append(death_col)
        if dyn_col:   sel.append(dyn_col)
        if src_col:   sel.append(src_col)

        sql = f"SELECT {', '.join(sel)} FROM {tbl}"
        if limit:
            sql += f" LIMIT {limit}"

        for row in conn.execute(sql):
            pid = str(row[id_col])
            name = None
            for nc in name_cols:
                v = row[nc] if nc in cols else None
                if v:
                    name = v
                    break

            people[pid] = {
                "id":      pid,
                "name":    name or pid,
                "birth":   int(row[birth_col]) if birth_col and row[birth_col] else None,
                "death":   int(row[death_col]) if death_col and row[death_col] else None,
                "dynasty": row[dyn_col] if dyn_col else None,
                "source":  row[src_col] if src_col else tbl,
                "_table":  tbl,
            }
        break  # dùng bảng đầu tiên tìm được

    return people


def load_relations(conn, schema, source_filter=None):
    """Trả về list (teacher_id, student_id, source, relation_type)."""
    relations = []

    for tbl in ["networks", "lineage", "relationships"]:
        if tbl not in schema:
            continue
        cols = schema[tbl]

        src_col  = next((c for c in ["person_id", "source_id", "teacher_id", "from_id"] if c in cols), None)
        tgt_col  = next((c for c in ["target_id", "student_id", "disciple_id", "to_id"] if c in cols), None)
        rel_col  = next((c for c in ["relation_type", "relation", "type"] if c in cols), None)
        dsrc_col = next((c for c in ["source", "data_source"] if c in cols), None)

        if not src_col or not tgt_col:
            continue

        sel = [src_col, tgt_col]
        if rel_col:  sel.append(rel_col)
        if dsrc_col: sel.append(dsrc_col)

        sql = f"SELECT {', '.join(sel)} FROM {tbl}"

        for row in conn.execute(sql):
            rel_type = row[rel_col] if rel_col else "teacher_of"
            dsrc     = row[dsrc_col] if dsrc_col else tbl
            teacher  = str(row[src_col])
            student  = str(row[tgt_col])

            # Chuẩn hóa: chỉ giữ quan hệ thầy→trò
            rt = (rel_type or "").lower()
            if any(k in rt for k in ["student", "disciple", "studied_under", "has_teacher"]):
                teacher, student = student, teacher
            elif not any(k in rt for k in ["teacher", "master", "directed", "lineage"]):
                continue  # bỏ qua quan hệ không phải truyền thừa

            if teacher != student:  # loại self-loop rõ ràng
                relations.append({
                    "teacher": teacher,
                    "student": student,
                    "source":  dsrc,
                    "type":    rel_type,
                })
        break

    return relations


# ───────────────────────────────────────────────────────────────────
# TÌM KIẾM THIỀN SƯ
# ───────────────────────────────────────────────────────────────────

def find_monk_ids(conn, schema, name_query):
    """Tìm tất cả ID khớp với tên (tiếng Việt hoặc Hán)."""
    ids = []
    name_q = name_query.lower().strip()

    for tbl in ["people", "persons", "monks", "person_authority"]:
        if tbl not in schema:
            continue
        cols = schema[tbl]
        id_col = next((c for c in ["id", "person_id", "dila_id"] if c in cols), None)
        if not id_col:
            continue

        name_cols = [c for c in ["name_vi", "name_zh", "name_en", "label", "label_vi"] if c in cols]
        for nc in name_cols:
            rows = conn.execute(
                f"SELECT {id_col} FROM {tbl} WHERE LOWER({nc}) LIKE ?",
                (f"%{name_q}%",)
            ).fetchall()
            ids.extend(str(r[0]) for r in rows)
        break

    return list(set(ids))


# ───────────────────────────────────────────────────────────────────
# CÁC HÀM KIỂM TRA
# ───────────────────────────────────────────────────────────────────

def check_cycles(relations):
    """CHECK_CYCLE: Tìm chu trình trong đồ thị thầy→trò."""
    if not HAS_NX:
        return []

    G = nx.DiGraph()
    for r in relations:
        G.add_edge(r["teacher"], r["student"])

    bugs = []
    for cycle in nx.simple_cycles(G):
        bugs.append({
            "check":    "CHECK_CYCLE",
            "severity": "HIGH",
            "ids":      cycle,
            "desc":     f"Chu trình truyền thừa: {' → '.join(cycle[:6])}{'→ ...' if len(cycle)>6 else ''}",
            "detail":   f"Độ dài chu trình: {len(cycle)} thiền sư",
        })
    return bugs


def check_date_paradox(people, relations):
    """CHECK_DATE_PARADOX: Học trò sinh trước khi thầy chết là bình thường,
    nhưng thầy chết TRƯỚC KHI học trò sinh là phi lý."""
    bugs = []
    for r in relations:
        t = people.get(r["teacher"])
        s = people.get(r["student"])
        if not t or not s:
            continue

        t_death = t.get("death")
        s_birth = s.get("birth")
        t_birth = t.get("birth")
        s_death = s.get("death")

        if t_death and s_birth and t_death < s_birth:
            bugs.append({
                "check":    "CHECK_DATE_PARADOX",
                "severity": "HIGH",
                "ids":      [r["teacher"], r["student"]],
                "desc":     (
                    f"Thầy [{t['name']}] mất năm {t_death}, "
                    f"nhưng trò [{s['name']}] sinh năm {s_birth} — phi lý!"
                ),
                "source":   r["source"],
            })

        # Thầy sinh SAU học trò
        if t_birth and s_birth and t_birth > s_birth:
            bugs.append({
                "check":    "CHECK_DATE_PARADOX",
                "severity": "HIGH",
                "ids":      [r["teacher"], r["student"]],
                "desc":     (
                    f"Thầy [{t['name']}] sinh năm {t_birth}, "
                    f"nhưng trò [{s['name']}] sinh năm {s_birth} — thầy trẻ hơn trò!"
                ),
                "source":   r["source"],
            })

        # Khoảng cách sinh quá gần (< 5 năm) — nghi ngờ nhầm vai
        if t_birth and s_birth and abs(t_birth - s_birth) < 5:
            bugs.append({
                "check":    "CHECK_GENERATION_GAP",
                "severity": "MEDIUM",
                "ids":      [r["teacher"], r["student"]],
                "desc":     (
                    f"Thầy [{t['name']}] sinh {t_birth}, "
                    f"trò [{s['name']}] sinh {s_birth} — chênh lệch chỉ {abs(t_birth-s_birth)} năm"
                ),
                "source":   r["source"],
            })

    return bugs


def check_lifespan(people):
    """CHECK_LIFESPAN: Tuổi thọ phi lý (<0 hoặc >130)."""
    bugs = []
    for pid, p in people.items():
        b, d = p.get("birth"), p.get("death")
        if not b or not d:
            continue
        age = d - b
        if age < 0:
            bugs.append({
                "check":    "CHECK_LIFESPAN",
                "severity": "HIGH",
                "ids":      [pid],
                "desc":     f"[{p['name']}] chết năm {d} trước khi sinh {b} — tuổi âm {age}",
            })
        elif age > 130:
            bugs.append({
                "check":    "CHECK_LIFESPAN",
                "severity": "MEDIUM",
                "ids":      [pid],
                "desc":     f"[{p['name']}] sống {age} tuổi ({b}–{d}) — cực kỳ bất thường",
                "note":     "Triệu Châu Tùng Thẩm thọ 120 là có sử chứng; >130 cần xác minh",
            })
    return bugs


def check_self_teacher(relations):
    """CHECK_SELF_TEACHER: Thiền sư là thầy của chính mình."""
    bugs = []
    for r in relations:
        if r["teacher"] == r["student"]:
            bugs.append({
                "check":    "CHECK_SELF_TEACHER",
                "severity": "HIGH",
                "ids":      [r["teacher"]],
                "desc":     f"ID [{r['teacher']}] vừa là thầy vừa là trò của chính mình",
                "source":   r["source"],
            })
    return bugs


def check_dynasty_mismatch(people):
    """CHECK_DYNASTY_MISMATCH: Năm sinh/mất không khớp với triều đại ghi nhận."""
    bugs = []
    for pid, p in people.items():
        dynasty = p.get("dynasty")
        b, d = p.get("birth"), p.get("death")
        if not dynasty or (not b and not d):
            continue

        year = b or d
        for dy_name, (dy_start, dy_end) in DYNASTY_RANGES.items():
            if dy_name.lower() in dynasty.lower():
                if not (dy_start - 20 <= year <= dy_end + 20):
                    bugs.append({
                        "check":    "CHECK_DYNASTY_MISMATCH",
                        "severity": "MEDIUM",
                        "ids":      [pid],
                        "desc":     (
                            f"[{p['name']}] thuộc triều {dynasty} ({dy_start}–{dy_end}), "
                            f"nhưng năm {year} nằm ngoài khoảng này"
                        ),
                    })
                break
    return bugs


def check_source_conflicts(conn, schema, people):
    """CHECK_SOURCE_CONFLICT: Cùng một thiền sư nhưng thầy khác nhau giữa DILA và Marcus."""
    bugs = []

    if "conflicts" not in schema.get("_all_tables", set()):
        # Tự xây dựng từ networks nếu có source column
        source_teacher = defaultdict(lambda: defaultdict(set))

        for tbl in ["networks", "lineage", "relationships"]:
            if tbl not in schema:
                continue
            cols = schema[tbl]
            src_col  = next((c for c in ["person_id", "source_id", "teacher_id"] if c in cols), None)
            tgt_col  = next((c for c in ["target_id", "student_id", "disciple_id"] if c in cols), None)
            dsrc_col = next((c for c in ["source", "data_source"] if c in cols), None)

            if not src_col or not tgt_col or not dsrc_col:
                continue

            for row in conn.execute(f"SELECT {src_col}, {tgt_col}, {dsrc_col} FROM {tbl}"):
                teacher, student, src = str(row[0]), str(row[1]), str(row[2] or "unknown")
                source_teacher[student][src].add(teacher)

        for student_id, src_teachers in source_teacher.items():
            if len(src_teachers) < 2:
                continue
            sources = list(src_teachers.keys())
            # So sánh từng cặp nguồn
            for i in range(len(sources)):
                for j in range(i + 1, len(sources)):
                    s1, s2 = sources[i], sources[j]
                    t1, t2 = src_teachers[s1], src_teachers[s2]
                    only_s1 = t1 - t2
                    only_s2 = t2 - t1
                    if only_s1 or only_s2:
                        p = people.get(student_id, {})
                        bugs.append({
                            "check":    "CHECK_SOURCE_CONFLICT",
                            "severity": "MEDIUM",
                            "ids":      [student_id],
                            "desc":     (
                                f"[{p.get('name', student_id)}]: "
                                f"{s1} ghi thầy {list(only_s1)[:3]}, "
                                f"{s2} ghi thầy {list(only_s2)[:3]}"
                            ),
                            "sources":  {s1: list(t1), s2: list(t2)},
                        })

    return bugs


def check_orphan_nodes(people, relations):
    """CHECK_ORPHAN: ID xuất hiện trong quan hệ nhưng không có trong bảng người."""
    known = set(people.keys())
    orphans = set()
    for r in relations:
        for pid in [r["teacher"], r["student"]]:
            if pid not in known:
                orphans.add(pid)
    bugs = []
    for oid in orphans:
        bugs.append({
            "check":    "CHECK_ORPHAN_NODE",
            "severity": "LOW",
            "ids":      [oid],
            "desc":     f"ID [{oid}] xuất hiện trong quan hệ nhưng không có trong bảng người",
        })
    return bugs[:100]  # giới hạn output


# ───────────────────────────────────────────────────────────────────
# CASE SINH TỰ ĐỘNG
# ───────────────────────────────────────────────────────────────────

def auto_generate_cases(conn, schema, people, relations):
    """Tự động chọn các thiền sư tiềm năng nhiều lỗi để làm seed test case."""
    seeds = []

    # 1. Tìm người có > 3 thầy (nhiều thầy có thể là xung đột nguồn)
    student_teachers = defaultdict(list)
    for r in relations:
        student_teachers[r["student"]].append(r["teacher"])

    for sid, teachers in student_teachers.items():
        if len(teachers) >= 3:
            p = people.get(sid, {})
            seeds.append({
                "monk_id":   sid,
                "monk_name": p.get("name", sid),
                "reason":    f"Có {len(teachers)} thầy — nghi xung đột nguồn",
                "priority":  "HIGH",
            })

    # 2. Tìm người không có ngày nhưng có nhiều quan hệ (không thể kiểm tra mốc thời gian)
    high_degree = defaultdict(int)
    for r in relations:
        high_degree[r["teacher"]] += 1
        high_degree[r["student"]] += 1

    for pid, degree in sorted(high_degree.items(), key=lambda x: -x[1])[:20]:
        p = people.get(pid, {})
        if not p.get("birth") and not p.get("death") and degree > 5:
            seeds.append({
                "monk_id":   pid,
                "monk_name": p.get("name", pid),
                "reason":    f"Độ kết nối cao ({degree}) nhưng không có ngày — cần bổ sung",
                "priority":  "MEDIUM",
            })

    # 3. Seed từ danh sách cứng (SEED_MONKS)
    for name in SEED_MONKS:
        ids = find_monk_ids(conn, schema, name)
        for mid in ids:
            seeds.append({
                "monk_id":   mid,
                "monk_name": name,
                "reason":    "Seed cứng — thiền sư quan trọng cần xác minh truyền thừa",
                "priority":  "HIGH",
            })

    return seeds


# ───────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────

def run_audit(monk_filter=None, check_filter=None, limit=None):
    print("=" * 64)
    print("🔍 LINEAGE TESTER AGENT — Phật Tổ Đạo Ảnh")
    print("=" * 64)

    conn = connect_db()
    schema, all_tables = detect_schema(conn)
    schema["_all_tables"] = all_tables

    print(f"✓ Kết nối DB: {DB_PATH}")
    print(f"✓ Phát hiện bảng: {len(all_tables)} bảng")

    print("\n📥 Tải dữ liệu...")
    people    = load_people(conn, schema, limit=limit)
    relations = load_relations(conn, schema)
    print(f"  → {len(people):,} thiền sư, {len(relations):,} quan hệ truyền thừa")

    if not people and not relations:
        print("[WARN] Không tải được dữ liệu. Kiểm tra lại tên bảng trong DB.")
        conn.close()
        return

    # Lọc theo monk nếu có
    focus_ids = set()
    if monk_filter:
        ids = find_monk_ids(conn, schema, monk_filter)
        focus_ids = set(ids)
        if ids:
            print(f"\n🎯 Tìm kiếm '{monk_filter}': {len(ids)} kết quả — {ids[:5]}")
        else:
            print(f"\n[WARN] Không tìm thấy '{monk_filter}' trong DB")

    # Sinh test case tự động
    print("\n🤖 Sinh test case tự động...")
    auto_cases = auto_generate_cases(conn, schema, people, relations)
    if monk_filter and focus_ids:
        auto_cases = [c for c in auto_cases if c["monk_id"] in focus_ids]
    print(f"  → {len(auto_cases)} test case")

    # Chạy các kiểm tra
    all_bugs = []
    checks_run = []

    def should_run(name):
        return not check_filter or check_filter.lower() in name.lower()

    if should_run("cycles"):
        print("\n🔄 CHECK_CYCLE: Tìm chu trình...")
        bugs = check_cycles(relations)
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_CYCLE", len(bugs)))
        print(f"  → {len(bugs)} chu trình")

    if should_run("date"):
        print("\n📅 CHECK_DATE_PARADOX + CHECK_GENERATION_GAP...")
        bugs = check_date_paradox(people, relations)
        if focus_ids:
            bugs = [b for b in bugs if any(i in focus_ids for i in b.get("ids", []))]
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_DATE_PARADOX", len(bugs)))
        print(f"  → {len(bugs)} lỗi ngày tháng")

    if should_run("lifespan"):
        print("\n🧓 CHECK_LIFESPAN...")
        bugs = check_lifespan(people)
        if focus_ids:
            bugs = [b for b in bugs if any(i in focus_ids for i in b.get("ids", []))]
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_LIFESPAN", len(bugs)))
        print(f"  → {len(bugs)} tuổi thọ bất thường")

    if should_run("self"):
        print("\n🪞 CHECK_SELF_TEACHER...")
        bugs = check_self_teacher(relations)
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_SELF_TEACHER", len(bugs)))
        print(f"  → {len(bugs)} lỗi tự làm thầy")

    if should_run("dynasty"):
        print("\n👑 CHECK_DYNASTY_MISMATCH...")
        bugs = check_dynasty_mismatch(people)
        if focus_ids:
            bugs = [b for b in bugs if any(i in focus_ids for i in b.get("ids", []))]
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_DYNASTY_MISMATCH", len(bugs)))
        print(f"  → {len(bugs)} lỗi triều đại")

    if should_run("conflict") or should_run("source"):
        print("\n⚔️  CHECK_SOURCE_CONFLICT...")
        bugs = check_source_conflicts(conn, schema, people)
        if focus_ids:
            bugs = [b for b in bugs if any(i in focus_ids for i in b.get("ids", []))]
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_SOURCE_CONFLICT", len(bugs)))
        print(f"  → {len(bugs)} xung đột nguồn")

    if should_run("orphan"):
        print("\n👻 CHECK_ORPHAN_NODE...")
        bugs = check_orphan_nodes(people, relations)
        all_bugs.extend(bugs)
        checks_run.append(("CHECK_ORPHAN_NODE", len(bugs)))
        print(f"  → {len(bugs)} node mồ côi")

    # Đánh số bug ID
    for i, bug in enumerate(all_bugs, 1):
        bug["bug_id"] = f"LT-{i:04d}"
        bug["status"] = "NEW"

    # ─── Xuất báo cáo ───────────────────────────────────────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = OUT_DIR / f"lineage_audit_{ts}.json"
    out_md   = OUT_DIR / f"lineage_audit_{ts}.md"

    report = {
        "timestamp":    datetime.now().isoformat(),
        "db_path":      str(DB_PATH),
        "monk_filter":  monk_filter,
        "total_people": len(people),
        "total_relations": len(relations),
        "checks_run":   checks_run,
        "auto_cases":   auto_cases[:50],
        "bugs":         all_bugs,
        "summary": {
            "total":  len(all_bugs),
            "high":   sum(1 for b in all_bugs if b.get("severity") == "HIGH"),
            "medium": sum(1 for b in all_bugs if b.get("severity") == "MEDIUM"),
            "low":    sum(1 for b in all_bugs if b.get("severity") == "LOW"),
        },
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Viết markdown
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# LINEAGE AUDIT REPORT\n\n")
        f.write(f"**Thời gian:** {report['timestamp']}  \n")
        f.write(f"**DB:** {DB_PATH}  \n")
        if monk_filter:
            f.write(f"**Lọc thiền sư:** {monk_filter}  \n")
        f.write(f"\n## Tóm tắt\n\n")
        s = report["summary"]
        f.write(f"| Mức độ | Số lỗi |\n|--------|--------|\n")
        f.write(f"| 🔴 HIGH   | {s['high']} |\n")
        f.write(f"| 🟡 MEDIUM | {s['medium']} |\n")
        f.write(f"| 🔵 LOW    | {s['low']} |\n")
        f.write(f"| **Tổng**  | **{s['total']}** |\n\n")

        if auto_cases:
            f.write(f"## Test Cases Tự Động Sinh ({len(auto_cases)})\n\n")
            f.write("| ID | Tên | Lý do | Ưu tiên |\n|----|----|-------|--------|\n")
            for c in auto_cases[:30]:
                f.write(f"| {c['monk_id'][:20]} | {c['monk_name']} | {c['reason']} | {c['priority']} |\n")
            f.write("\n")

        if all_bugs:
            f.write(f"## Chi tiết Lỗi ({len(all_bugs)})\n\n")
            for bug in sorted(all_bugs, key=lambda x: ["HIGH","MEDIUM","LOW"].index(x.get("severity","LOW"))):
                sev_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}.get(bug.get("severity"), "⚪")
                f.write(f"### {bug['bug_id']} — {bug['check']} {sev_icon}\n\n")
                f.write(f"**Mô tả:** {bug['desc']}  \n")
                if bug.get("source"):
                    f.write(f"**Nguồn dữ liệu:** {bug['source']}  \n")
                if bug.get("note"):
                    f.write(f"**Ghi chú:** {bug['note']}  \n")
                f.write(f"**IDs:** `{', '.join(str(i) for i in bug.get('ids', []))}`  \n")
                f.write(f"**Status:** {bug['status']}\n\n")
        else:
            f.write("## Không tìm thấy lỗi nào!\n\n✅ Dữ liệu truyền thừa sạch.\n")

    # ─── In tóm tắt cuối ─────────────────────────────────────────
    print("\n" + "=" * 64)
    print("📊 KẾT QUẢ AUDIT")
    print("=" * 64)
    s = report["summary"]
    print(f"  🔴 HIGH:   {s['high']:4d} lỗi")
    print(f"  🟡 MEDIUM: {s['medium']:4d} lỗi")
    print(f"  🔵 LOW:    {s['low']:4d} lỗi")
    print(f"  ─────────────────")
    print(f"  Tổng:      {s['total']:4d} lỗi")

    if s["total"] == 0:
        print("\n✅ Không tìm thấy lỗi — dữ liệu sạch!")
    elif s["high"] > 0:
        print(f"\n❌ Có {s['high']} lỗi HIGH cần xử lý ngay!")
    else:
        print(f"\n⚠️  Có {s['medium']} lỗi MEDIUM cần review.")

    print(f"\n📄 Báo cáo JSON: {out_json}")
    print(f"📄 Báo cáo MD:   {out_md}")
    print("=" * 64)

    conn.close()
    return report


# ───────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lineage Tester Agent — kiểm tra lỗi logic truyền thừa Phật giáo"
    )
    parser.add_argument(
        "--monk", "-m",
        help='Tên thiền sư cần tập trung kiểm tra, VD: "Đan Hà Thiên Nhiên"',
        default=None
    )
    parser.add_argument(
        "--check", "-c",
        help="Chỉ chạy một loại kiểm tra: cycles | date | lifespan | self | dynasty | conflict | orphan",
        default=None
    )
    parser.add_argument(
        "--limit", "-l",
        help="Giới hạn số thiền sư tải (mặc định: tất cả)",
        type=int,
        default=None
    )
    args = parser.parse_args()

    run_audit(
        monk_filter=args.monk,
        check_filter=args.check,
        limit=args.limit,
    )
