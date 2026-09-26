#!/usr/bin/env python3
"""Probe bio text patterns to understand date extraction opportunities."""
import sqlite3, re, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# Count bios with parenthetical CE year pattern like （1053）
c.execute("SELECT COUNT(*) FROM people WHERE bio LIKE '%（%'")
parens = c.fetchone()[0]

# Count bios with 生卒年不詳 (unknown)
c.execute("SELECT COUNT(*) FROM people WHERE bio LIKE '%生卒年不詳%'")
unknown = c.fetchone()[0]

# Count bios with 示寂 (passed away)
c.execute("SELECT COUNT(*) FROM people WHERE bio LIKE '%示寂%'")
shiji = c.fetchone()[0]

# Count bios with 生 (born) near year context
c.execute("SELECT COUNT(*) FROM people WHERE bio LIKE '%生%' AND bio LIKE '%年%'")
born = c.fetchone()[0]

# Count total non-empty bio
c.execute("SELECT COUNT(*) FROM people WHERE bio IS NOT NULL AND bio != ''")
total_bio = c.fetchone()[0]

# Sample bios with （YYYY） CE years
c.execute("""SELECT id, name_zh, name_vi, bio FROM people 
    WHERE bio LIKE '%（%）%' AND bio LIKE '%年%'
    AND bio NOT LIKE '%生卒年不詳%'
    LIMIT 20""")
samples = c.fetchall()

print(f"Total persons with bio: {total_bio}")
print(f"Bios with parens: {parens}")
print(f"Bios with 生卒年不詳: {unknown}")
print(f"Bios with 示寂: {shiji}")
print(f"Bios with 生+年: {born}")
print()
print("=== SAMPLES with parenthetical years ===")
for r in samples:
    print(f"\n--- {r[0]} ({r[1] or r[2]}) ---")
    print(r[3][:350])
conn.close()
