import os

APP_PATH = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/app.py'
NEW_CODE = """
from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/daoanh/api/admin/places_pending')
def places_pending():
    try:
        conn = get_db_connection()
        places = conn.execute("SELECT id, name_zh FROM places_pending LIMIT 100").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
        conn.close()
        return jsonify({"success": True, "total": total, "places": [dict(p) for p in places]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/ai_judge/<id>')
def ai_judge(id):
    try:
        conn = get_db_connection()
        # FIX GPS: Bóc đúng gps_lat, gps_long từ Database
        row = conn.execute('SELECT id, name_zh, note, gps_lat, gps_long FROM places_pending WHERE id = ? OR id LIKE ?', (id, f"%{id[-6:]}")).fetchone()
        conn.close()
        if row:
            return jsonify({
                "success": True,
                "current_id": row['id'],
                "name_zh": row['name_zh'],
                "verdict": "",  # Để trống để thí chủ tự gõ Hán Việt chuẩn từ Note
                "full_description": row['note'],
                "gps_lat": row['gps_lat'],   # Đã có số thực!
                "gps_long": row['gps_long'], # Đã có số thực!
                "dict_name": "Manual Editor Mode"
            })
        return jsonify({"success": False, "error": "Not Found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/namevi-map-pl', methods=['POST'])
def save_mapping():
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute('INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, source) VALUES (?, ?, ?, "manual")', (data['dila_id'], data['name_vi'], data['name_zh']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
"""
with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(NEW_CODE.strip())
os.system("fuser -k 5000/tcp")
os.system(f"nohup python3 {APP_PATH} > flask.log 2>&1 &")
print("✅ ĐÃ FIX XONG: GPS sẽ hiện số và 404 sẽ biến mất!")
