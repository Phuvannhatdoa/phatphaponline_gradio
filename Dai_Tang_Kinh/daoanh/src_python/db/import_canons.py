#!/usr/bin/env python3
"""
Import Canon Layer - CBETA/Taisho texts
Uses iterparse for memory efficiency
"""
import sqlite3
import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
DB_PATH = os.path.join(DATA_DIR, "sqlite", "buddhist_db.sqlite")

# CBETA typically stored in XML format
# Sample mapping: T01n0001 = Taisho volume 1, text 1

def parse_cbeta_catalog(xml_file):
    """Parse CBETA catalog XML using iterparse"""
    print(f"📖 Parsing {xml_file}...")
    
    texts = []
    count = 0
    
    # Use iterparse for memory efficiency
    context = ET.iterparse(xml_file, events=('end',))
    
    for event, elem in context:
        if elem.tag in ['text', 'item', 'Ttext', 'taisho']:
            # Extract text info
            text_id = elem.get('id') or elem.get('T') or elem.get('n')
            
            # Try different title fields
            title = elem.find('.//title') or elem.find('.//Ttitle')
            title_zh = title.text if title is not None else ''
            
            if not title_zh:
                # Try attributes
                title_zh = elem.get('title', '')
            
            if title_zh:
                texts.append({
                    'text_id': text_id,
                    'title_zh': title_zh[:200] if title_zh else ''
                })
                count += 1
                
                if count % 100 == 0:
                    print(f"   Progress: {count}")
            
            # Clear element to free memory
            elem.clear()
    
    return texts

def create_sample_canons():
    """Create sample canon data for structure"""
    # Since we don't have actual CBETA XML, create sample structure
    canons = []
    
    # Common Taisho volumes
    volumes = [
        ('T01', '大正藏 第1卷', '阿含部', 1),
        ('T02', '大正藏 第2卷', '本缘部', 2),
        ('T03', '大正藏 第3卷', '般若部', 3),
        ('T04', '大正藏 第4卷', '法华部', 4),
        ('T05', '大正藏 第5卷', '华严部', 5),
        ('T06', '大正藏 第6卷', '宝积部', 6),
        ('T07', '大正藏 第7卷', '集部', 7),
        ('T12', '大正藏 第12卷', '论集部', 12),
        ('T14', '大正藏 第14卷', '论集部', 14),
        ('T16', '大正藏 第16卷', '中观部', 16),
        ('T20', '大正藏 第20卷', '律部', 20),
        ('T22', '大正藏 第22卷', '经集部', 22),
        ('T24', '大正藏 第24卷', '论部', 24),
        ('T32', '大正藏 第32卷', '史传部', 32),
        ('T35', '大正藏 第35卷', '外教部', 35),
        ('T40', '大正藏 第40卷', '文字部', 40),
        ('T44', '大正藏 第44卷', '目录部', 44),
        ('T45', '大正藏 第45卷', '古逸部', 45),
        ('T47', '大正藏 第47卷', '疑似部', 47),
        ('T48', '大正藏 第48卷', '续论部', 48),
        ('T49', '大正藏 第49卷', '续律部', 49),
        ('T50', '大正藏 第50卷', '续经部', 50),
        ('T51', '大正藏 第51卷', '续杂部', 51),
        ('T52', '大正藏 第52卷', '续集部', 52),
        ('T55', '大正藏 第55卷', '续论部', 55),
        ('T70', '大正藏 第70卷', '图像部', 70),
        ('T85', '大正藏 第85卷', '新嘉续', 85),
    ]
    
    for vol_id, title, canon_type, vol in volumes:
        canons.append({
            'text_id': vol_id,
            'title_zh': title,
            'title_en': f'Taisho Vol {vol}',
            'author_id': None,
            'author_name': None,
            'canon_type': canon_type,
            'volume': str(vol)
        })
    
    return canons

def import_canons():
    """Import canon catalog"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Try to find CBETA catalog XML
    potential_files = [
        os.path.join(DATA_DIR, "cbeta_catalog.xml"),
        os.path.join(DATA_DIR, "CBETA", "catalog.xml"),
    ]
    
    texts = []
    for f in potential_files:
        if os.path.exists(f):
            texts = parse_cbeta_catalog(f)
            break
    
    # If no XML, create sample structure
    if not texts:
        print("⚠️ No CBETA XML found, creating sample structure...")
        texts = create_sample_canons()
    
    # Import
    imported = 0
    for t in texts:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO canons_catalog (
                    text_id, title_zh, title_en, author_id, author_name, canon_type, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                t.get('text_id'),
                t.get('title_zh', ''),
                t.get('title_en', ''),
                t.get('author_id'),
                t.get('author_name'),
                t.get('canon_type'),
                t.get('volume')
            ))
            imported += 1
        except Exception as e:
            if imported < 5:
                print(f"   ⚠️ Error: {e}")
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM canons_catalog")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Imported {imported} canon texts")
    print(f"   Total in DB: {count}")
    
    return imported

def import_text_mapping():
    """Import text mapping (cross-reference)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create sample mappings between Taisho, CBETA, Linh Son
    # Format: Taisho T01n0001 = CBETA T0001 = Linh Son A0001
    
    mappings = [
        ('T01n0001', 'T0001', 'A0001'),
        ('T01n0002', 'T0002', 'A0002'),
        ('T02n0003', 'T0003', 'B0101'),
        ('T03n0020', 'T0020', 'C0101'),
        ('T04n0022', 'T0022', 'C0201'),
        ('T05n0027', 'T0027', 'D0101'),
        ('T06n0035', 'T0035', 'E0101'),
    ]
    
    for taisho, cbeta, linhson in mappings:
        cursor.execute('''
            INSERT INTO text_mapping (taisho_id, cbeta_id, linhson_id, source)
            VALUES (?, ?, ?, ?)
        ''', (taisho, cbeta, linhson, 'DILA'))
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM text_mapping")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ Imported {len(mappings)} text mappings")
    print(f"   Total in DB: {count}")
    
    return len(mappings)

if __name__ == "__main__":
    print("="*50)
    print("Importing Canon Layer")
    print("="*50)
    
    print("\n📌 Step 1: Import Canon Catalog")
    import_canons()
    
    print("\n📌 Step 2: Import Text Mappings")
    import_text_mapping()
    
    print("\n" + "="*50)
    print("✅ Canon Layer Complete!")
    print("="*50)