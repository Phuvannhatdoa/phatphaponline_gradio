#!/usr/bin/env python3
"""
Import Lexicon - Buddhist Dictionary Terms
Priority: 1=HanLam, 2=Phổ Thông, 3=Tham Khảo
Note: StarDict format requires special parser, using sample here
"""
import sqlite3
import json
import os

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
DB_PATH = os.path.join(DATA_DIR, "sqlite", "buddhist_db.sqlite")

def create_sample_lexicon():
    """Create sample Buddhist lexicon terms"""
    # Common Buddhist terms with priority
    terms = [
        # Priority 1: Han Lâm (最高)
        ('阿弥陀佛', 'A Di Đà Phật - Buddha Amitabha', 1, 'HanLam', 'zh'),
        ('般若波罗蜜多', 'Bát Nhã Ba La Mật Đa - Prajnaparamita', 1, 'HanLam', 'zh'),
        ('法华经', 'Pháp Hoa Kinh - Lotus Sutra', 1, 'HanLam', 'zh'),
        ('金刚经', 'Kim Cang Kinh - Diamond Sutra', 1, 'HanLam', 'zh'),
        ('如来', 'Như Lai - Tathagata', 1, 'HanLam', 'zh'),
        ('菩萨', 'Bồ Tát - Bodhisattva', 1, 'HanLam', 'zh'),
        ('涅槃', 'Niết Bàn - Nirvana', 1, 'HanLam', 'zh'),
        
        # Priority 2: Phổ Thông (普通)
        ('佛', 'Phật - Buddha', 2, 'Phổ Thông', 'vi'),
        ('僧', 'Tăng - Monk', 2, 'Phổ Thông', 'vi'),
        ('寺', 'Chùa - Temple', 2, 'Phổ Thông', 'vi'),
        ('经', 'Kinh - Sutra', 2, 'Phổ Thông', 'vi'),
        ('塔', 'Tháp - Stupa', 2, 'Phổ Thông', 'vi'),
        ('僧院', 'Tăng Viện - Monastery', 2, 'Phổ Thông', 'vi'),
        
        # Priority 3: Tham Khảo
        ('袈裟', 'Ca Sa - Kasaya', 3, 'Tham Khảo', 'vi'),
        ('锡杖', 'Tích Trượng - Monastic staff', 3, 'Tham Khảo', 'vi'),
        ('钵', 'Bát - Alms bowl', 3, 'Tham Khảo', 'vi'),
        ('香', 'Hương - Incense', 3, 'Tham Khảo', 'vi'),
        ('灯', 'Đăng - Lamp', 3, 'Tham Khảo', 'vi'),
    ]
    
    return terms

def import_lexicon():
    """Import lexicon terms"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Try to parse StarDict format if available
    dict_file = os.path.join(DATA_DIR, "indexed", "combined_dict.json")
    
    if os.path.exists(dict_file):
        print("📚 Loading combined_dict.json...")
        with open(dict_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            for term, value in data.items():
                definition = value.get('definition', '') if isinstance(value, dict) else str(value)
                source = value.get('source', 'HanLam') if isinstance(value, dict) else 'HanLam'
                
                priority = 1 if source == 'HanLam' else (2 if source == 'Phổ Thông' else 3)
                
                cursor.execute('''
                    INSERT INTO lexicon (term, definition, priority, source, language)
                    VALUES (?, ?, ?, ?, ?)
                ''', (term, definition[:500], priority, source, 'zh'))
    
    # Add sample terms
    print("📚 Adding sample lexicon terms...")
    terms = create_sample_lexicon()
    
    for term, definition, priority, source, lang in terms:
        cursor.execute('''
            INSERT INTO lexicon (term, definition, priority, source, language)
            VALUES (?, ?, ?, ?, ?)
        ''', (term, definition, priority, source, lang))
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM lexicon")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Total lexicon terms: {count}")
    
    # Show priority breakdown
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT priority, COUNT(*) 
        FROM lexicon 
        GROUP BY priority 
        ORDER BY priority
    ''')
    print("\n📊 Priority Breakdown:")
    for priority, count in cursor.fetchall():
        print(f"   Priority {priority}: {count}")
    
    conn.close()
    
    return count

if __name__ == "__main__":
    print("="*50)
    print("Importing Lexicon Layer")
    print("="*50)
    
    import_lexicon()
    
    print("\n" + "="*50)
    print("✅ Lexicon Layer Complete!")
    print("="*50)