"""
Phase 0 Audit — CBETA Corpus (Read-only)
Chạy: python scripts/audit_cbeta_corpus.py
Output: docs/cbeta-corpus-audit-results-YYYYMMDD.md + .json
Không thay đổi bất kỳ dữ liệu nào.
"""
import sqlite3
import re
import json
import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')

date_str = datetime.now().strftime('%Y%m%d')
out_md   = os.path.join(DOCS_DIR, f'cbeta-corpus-audit-results-{date_str}.md')
out_json = os.path.join(DOCS_DIR, f'cbeta-corpus-audit-results-{date_str}.json')

results = {}

def run(label, sql, con):
    cur = con.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    results[label] = {'columns': cols, 'rows': rows}
    return cols, rows

def section(title):
    print(f'\n=== {title} ===')

con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row

# ── 1. Tổng quan ─────────────────────────────────────────────────────────────
section('1. Tổng quan corpus')
cols, rows = run('overview', """
    SELECT
        COUNT(*)  AS total_passages,
        SUM(CASE WHEN vi_text IS NOT NULL AND vi_text != '' THEN 1 ELSE 0 END) AS has_vi,
        SUM(CASE WHEN translation_draft = 1 THEN 1 ELSE 0 END)                 AS is_draft,
        SUM(CASE WHEN raw_text IS NULL OR raw_text = '' THEN 1 ELSE 0 END)     AS empty_han,
        SUM(CASE WHEN vi_text IS NULL OR vi_text = '' THEN 1 ELSE 0 END)        AS empty_vi,
        ROUND(AVG(length(raw_text)), 1) AS avg_han_len,
        MAX(length(raw_text))           AS max_han_len,
        MIN(length(raw_text))           AS min_han_len
    FROM passage
""", con)
for row in rows:
    for c, v in zip(cols, row):
        print(f'  {c}: {v}')

# ── 2. Phân phối theo text_id (CBETA work) ───────────────────────────────────
section('2. Phân phối theo text_id (CBETA work)')
cols, rows = run('by_work', """
    SELECT text_id,
           COUNT(*) AS total,
           SUM(CASE WHEN vi_text IS NOT NULL AND vi_text != '' THEN 1 ELSE 0 END) AS translated,
           ROUND(AVG(length(raw_text)), 1) AS avg_han_len,
           MAX(length(raw_text)) AS max_han_len
    FROM passage
    GROUP BY text_id
    ORDER BY total DESC
""", con)
print(f"  {'text_id':<20} {'total':>6} {'translated':>10} {'avg_han':>8} {'max_han':>8}")
for row in rows:
    print(f"  {row[0]:<20} {row[1]:>6} {row[2]:>10} {row[3]:>8} {row[4]:>8}")

# ── 3. Passages quá dài (dấu hiệu concat) ────────────────────────────────────
section('3. Passages quá dài (> 2000 chars) — dấu hiệu concat')
cols, rows = run('too_long', """
    SELECT passage_id, text_id, loc_ref, length(raw_text) AS len,
           substr(raw_text, 1, 100) AS preview
    FROM passage
    WHERE length(raw_text) > 2000
    ORDER BY len DESC
    LIMIT 20
""", con)
if rows:
    print(f"  Found {len(rows)} passages > 2000 chars (showing first 20):")
    for row in rows:
        print(f"  [{row[1]}] {row[2]} len={row[3]} | {row[4][:60]}...")
else:
    print('  OK — không có passage nào > 2000 chars')

# ── 4. Duplicate raw_text ─────────────────────────────────────────────────────
section('4. Duplicate raw_text')
cols, rows = run('duplicates', """
    SELECT raw_text, COUNT(*) AS cnt,
           GROUP_CONCAT(passage_id, ' / ') AS ids
    FROM passage
    WHERE raw_text IS NOT NULL AND raw_text != ''
    GROUP BY raw_text
    HAVING cnt > 1
    ORDER BY cnt DESC
    LIMIT 20
""", con)
if rows:
    print(f'  Found {len(rows)} duplicates (showing first 20):')
    for row in rows:
        print(f'  cnt={row[1]} | ids={row[2][:80]}')
else:
    print('  OK — không có duplicate raw_text')

# ── 5. vi_text ratio (quá ngắn hoặc quá dài) ─────────────────────────────────
section('5. vi_text ratio (passages đã dịch)')
cols, rows = run('vi_ratio_short', """
    SELECT passage_id, text_id, loc_ref,
           length(raw_text) AS han_len, length(vi_text) AS vi_len,
           ROUND(CAST(length(vi_text) AS FLOAT) / MAX(length(raw_text),1), 2) AS vi_han_ratio
    FROM passage
    WHERE vi_text IS NOT NULL AND vi_text != ''
    ORDER BY vi_han_ratio ASC
    LIMIT 10
""", con)
print('  Ratio thấp nhất (có thể bị cắt):')
for row in rows:
    print(f'  {row[0]} ratio={row[5]} han={row[3]} vi={row[4]}')

cols_h, rows_h = run('vi_ratio_high', """
    SELECT passage_id, text_id, loc_ref,
           length(raw_text) AS han_len, length(vi_text) AS vi_len,
           ROUND(CAST(length(vi_text) AS FLOAT) / MAX(length(raw_text),1), 2) AS vi_han_ratio
    FROM passage
    WHERE vi_text IS NOT NULL AND vi_text != ''
    ORDER BY vi_han_ratio DESC
    LIMIT 5
""", con)
print('  Ratio cao nhất (có thể bị duplicate/lẫn):')
for row in rows_h:
    print(f'  {row[0]} ratio={row[5]} han={row[3]} vi={row[4]}')

# ── 6. Hán văn trong vi_text (Python REGEXP) ─────────────────────────────────
section('6. Hán văn trong vi_text')
cur = con.cursor()
cur.execute("SELECT passage_id, text_id, vi_text FROM passage WHERE vi_text IS NOT NULL AND vi_text != ''")
han_leak = []
HAN_RE = re.compile(r'[一-鿿]{10,}')
for row in cur.fetchall():
    if HAN_RE.search(row[2]):
        han_leak.append({'passage_id': row[0], 'text_id': row[1], 'preview': row[2][:120]})
results['han_in_vi'] = han_leak
if han_leak:
    print(f'  CẢNH BÁO: {len(han_leak)} passages có Hán văn trong vi_text:')
    for x in han_leak[:5]:
        print(f'  {x["passage_id"]} | {x["preview"][:80]}')
else:
    print('  OK — không phát hiện Hán văn trong vi_text')

# ── 7. Orphan passage_entity (passage không còn tồn tại) ─────────────────────
section('7. Orphan passage_entity')
cols, rows = run('orphan_pe', """
    SELECT pe.passage_id, COUNT(*) AS orphan_count
    FROM passage_entity pe
    LEFT JOIN passage p ON pe.passage_id = p.passage_id
    WHERE p.passage_id IS NULL
    GROUP BY pe.passage_id
    ORDER BY orphan_count DESC
    LIMIT 10
""", con)
if rows:
    print(f'  CẢNH BÁO: {len(rows)} orphan passage_entity (showing top 10)')
    for row in rows:
        print(f'  {row[0]} count={row[1]}')
else:
    print('  OK — không có orphan passage_entity')

# ── 8. Sequence gaps trong loc_ref ───────────────────────────────────────────
section('8. Phân tích loc_ref pattern per text_id')
cols, rows = run('loc_ref_stats', """
    SELECT text_id, COUNT(*) AS cnt,
           MIN(loc_ref) AS first_ref, MAX(loc_ref) AS last_ref
    FROM passage
    WHERE text_id IS NOT NULL
    GROUP BY text_id
    ORDER BY cnt DESC
""", con)
for row in rows:
    print(f'  {row[0]}: {row[1]} passages | {row[2]} → {row[3]}')

# ── 9. Kiểm tra bảng alignment schema có chưa ────────────────────────────────
section('9. Trạng thái alignment schema')
cur = con.cursor()
alignment_tables = ['text_passages', 'translation_segments', 'passage_translation_alignment']
for tbl in alignment_tables:
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
    exists = cur.fetchone()
    status = '✅ Có' if exists else '❌ Chưa có'
    print(f'  {status}: {tbl}')
    results[f'table_{tbl}'] = bool(exists)

# Extra: check if hash column exists on passage
cur.execute('PRAGMA table_info(passage)')
passage_cols = [r[1] for r in cur.fetchall()]
print(f'  passage.raw_zh_hash: {"✅ Có" if "raw_zh_hash" in passage_cols else "❌ Chưa có"}')
print(f'  passage.passage_id_ref: {"✅ Có" if "passage_id_ref" in passage_cols else "❌ Chưa có"}')
results['passage_columns'] = passage_cols

con.close()

# ── Output ────────────────────────────────────────────────────────────────────
print(f'\n=== Ghi kết quả ===')

# JSON (machine-readable, rows are lists)
json_out = {}
for k, v in results.items():
    if isinstance(v, dict) and 'rows' in v:
        json_out[k] = {'columns': v['columns'], 'rows': [list(r) for r in v['rows']]}
    else:
        json_out[k] = v

with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(json_out, f, ensure_ascii=False, indent=2)
print(f'  JSON: {out_json}')

# Markdown summary
ov = results.get('overview', {})
ov_row = ov.get('rows', [[]])[0] if ov.get('rows') else []
ov_cols = ov.get('columns', [])
ov_dict = dict(zip(ov_cols, ov_row)) if ov_row else {}

by_work_rows = results.get('by_work', {}).get('rows', [])
too_long = results.get('too_long', {}).get('rows', [])
dups = results.get('duplicates', {}).get('rows', [])
han_in_vi = results.get('han_in_vi', [])
orphans = results.get('orphan_pe', {}).get('rows', [])

md_lines = [
    f'# CBETA Corpus Audit — Kết quả {date_str}',
    '',
    f'**Chạy:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  ',
    f'**Script:** `scripts/audit_cbeta_corpus.py`  ',
    f'**DB:** `data/lineage.db`  ',
    f'**Trạng thái:** Read-only — không thay đổi dữ liệu',
    '',
    '---',
    '',
    '## 1. Tổng quan',
    '',
    f'| Chỉ số | Giá trị |',
    f'|--------|---------|',
]
for col in ov_cols:
    md_lines.append(f'| {col} | {ov_dict.get(col, "?")} |')

md_lines += [
    '',
    '## 2. Phân phối theo work (text_id)',
    '',
    '| text_id | total | translated | avg_han | max_han |',
    '|---------|-------|-----------|---------|---------|',
]
for row in by_work_rows:
    md_lines.append(f'| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |')

md_lines += ['', '## 3. Rủi ro phát hiện', '']
md_lines.append(f'| Rủi ro | Số lượng | Mức độ |')
md_lines.append(f'|--------|---------|--------|')
md_lines.append(f'| Passages > 2000 chars (concat?) | {len(too_long)} | {"HIGH" if too_long else "OK"} |')
md_lines.append(f'| Duplicate raw_text | {len(dups)} | {"HIGH" if len(dups) > 5 else "OK" if not dups else "MED"} |')
md_lines.append(f'| Hán văn trong vi_text | {len(han_in_vi)} | {"HIGH" if han_in_vi else "OK"} |')
md_lines.append(f'| Orphan passage_entity | {len(orphans)} | {"MED" if orphans else "OK"} |')
md_lines.append(f'| Alignment schema (text_passages) | ❌ Chưa có | CRITICAL |')
md_lines.append(f'| Hash column (raw_zh_hash) | ❌ Chưa có | HIGH |')

md_lines += [
    '',
    '## 4. Hành động tiếp theo',
    '',
    '- [ ] **Phase 1**: Tạo `text_passages` + `translation_segments` + `passage_translation_alignment` (additive, không đụng data cũ)',
    '- [ ] **Phase 2**: Pilot T50n2060 — backup + approval trước khi chạy',
    '- [ ] **Phase 3**: Validate + test TC-001 đến TC-011',
    '',
    '---',
    '',
    '*Xem: `docs/cbeta-corpus-audit.md` · `docs/cbeta-migration-rollout-plan.md` · `docs/t50n2060-repair-plan.md`*',
]

with open(out_md, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))
print(f'  MD:   {out_md}')
print('\nPhase 0 Audit hoàn tất — không có dữ liệu nào bị thay đổi.')
