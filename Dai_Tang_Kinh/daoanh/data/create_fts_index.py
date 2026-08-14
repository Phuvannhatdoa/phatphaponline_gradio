import sqlite3, os

DB_PATH = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'

def main():
    if not os.path.exists(DB_PATH):
        print(f"Khong tim thay DB: {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='places_search_fts'")
    if cursor.fetchone():
        print("FTS5 da ton tai, dang rebuild...")
        cursor.execute("INSERT INTO places_search_fts(places_search_fts) VALUES('rebuild')")
    else:
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS places_search_fts USING fts5(
                name_vi, name_zh, dila_id,
                content='namevi_map_places', content_rowid='id'
            )
        """)
        cursor.execute("INSERT INTO places_search_fts(places_search_fts) VALUES('rebuild')")
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM places_search_fts").fetchone()[0]
    conn.close()
    print(f"FTS5 index da tao/rebuild xong! {count} records trong index")

if __name__ == "__main__":
    main()
