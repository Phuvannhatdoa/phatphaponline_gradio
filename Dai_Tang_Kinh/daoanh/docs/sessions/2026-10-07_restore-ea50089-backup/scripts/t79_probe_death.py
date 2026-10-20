#!/usr/bin/env python3
"""Detailed probe of death/birth signal patterns in bio text."""
import sqlite3, re, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT id, name_vi, bio FROM people WHERE bio IS NOT NULL AND bio != ''")
rows = c.fetchall()

PAREN = re.compile(r'[（(]\s*(\d{3,4})\s*(?:[-–至]\s*(\d{3,4}))?\s*[）)]')
DEATH_KW = re.compile(r'示寂|圓寂|入寂|寂於|卒於|薨|歿')

death_kw_bios = 0
death_kw_with_paren = 0
death_kw_paren_after = 0
death_kw_paren_before = 0

for pid, name, bio in rows:
    if not bio:
        continue
    m_kw = DEATH_KW.search(bio)
    if m_kw:
        death_kw_bios += 1
        parens = list(PAREN.finditer(bio))
        if parens:
            death_kw_with_paren += 1
            # any paren after the death keyword?
            after = [p for p in parens if p.start() > m_kw.start()]
            before = [p for p in parens if p.start() < m_kw.start()]
            if after:
                death_kw_paren_after += 1
            if before:
                death_kw_paren_before += 1

print(f"Total bios analyzed: {len(rows)}")
print(f"Bios with death keyword: {death_kw_bios}")
print(f"  of which have parenthetical year anywhere: {death_kw_with_paren}")
print(f"  paren AFTER death keyword (death year likely): {death_kw_paren_after}")
print(f"  paren BEFORE death keyword (e.g. （YYYY）示寂): {death_kw_paren_before}")

# Show some death_kw_paren_before examples (where death keyword is AFTER paren)
print("\n=== death keyword BEFORE paren (后年（YYYY）示寂) examples ===")
count = 0
for pid, name, bio in rows:
    if not bio:
        continue
    m_kw = DEATH_KW.search(bio)
    if not m_kw:
        continue
    parens = list(PAREN.finditer(bio))
    after = [p for p in parens if p.start() > m_kw.start()]
    if after:
        y = after[0]
        print(f"{pid} ({name}): ...{bio[max(0,y.start()-40):y.end()+20]}...")
        count += 1
        if count >= 8:
            break

print("\n=== death keyword AFTER paren (（YYYY）示寂) examples ===")
count = 0
for pid, name, bio in rows:
    if not bio:
        continue
    m_kw = DEATH_KW.search(bio)
    if not m_kw:
        continue
    parens = list(PAREN.finditer(bio))
    before = [p for p in parens if p.start() < m_kw.start()]
    if before:
        p = before[-1]
        print(f"{pid} ({name}): ...{bio[max(0,p.start()-30):m_kw.end()+20]}...")
        count += 1
        if count >= 8:
            break
conn.close()
