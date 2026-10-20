# T226: server preview tạm, không thay port 5000/5001/8080.
from pathlib import Path
import sys,sqlite3,requests
BASE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(BASE))
from flask import Flask,send_from_directory
from api_ttl_profile_v2 import create_ttl_profile_blueprint
def db():
 c=sqlite3.connect('file:'+str(BASE/'data/lineage.db').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c
def verify(token):
 if not token:return False
 try:return requests.post('http://127.0.0.1:5001/api/login/check',json={'session_token':token},timeout=5).json().get('valid') is True
 except Exception:return False
app=Flask(__name__)
app.register_blueprint(create_ttl_profile_blueprint(BASE,db,verify))
@app.route('/daoanh/admin/<path:file>')
def admin(file):return send_from_directory(BASE/'admin',file)
@app.route('/daoanh/docs/<path:file>')
def docs(file):return send_from_directory(BASE/'docs',file)
if __name__=='__main__':app.run(host='127.0.0.1',port=5006,debug=False,threaded=True)
