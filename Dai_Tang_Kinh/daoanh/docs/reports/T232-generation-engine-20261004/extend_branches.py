import sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from src_python import generation_engine_v2 as g
c=sqlite3.connect('data/lineage.db',timeout=30);c.row_factory=sqlite3.Row
for code,label,aid,name in [('caodong','Tào Động','A009489','洞山良价'),('yunmen','Vân Môn','A003703','雲門文偃'),('fayan','Pháp Nhãn','A000174','法眼文益'),('guiyang','Quy Ngưỡng','A001984','溈山靈祐')]:
 i=g.identity(c,aid,name)
 config={'id':code,'label':label,'convention':name+'=1 trong hệ riêng; mỗi cạnh trực tiếp +1; teacher chung DILA chỉ cho số dự kiến.', 'root_id':aid,'policy':'dila_candidate','anchors':[{'person_id':aid,'name_zh':name,'number':1,'status':'source_asserted','rationale':'DILA concise/sect ghi khai tổ; đời khai tổ 1 là quy ước hệ đếm riêng. Chưa đủ ba chứng cứ để accepted.','evidence':[{'citation':'DILA TEI '+aid+' persName alternative + note concise/sect; khóa đúng khai tổ, không dùng tên trùng.','version':i['version']+':'+i['sha256'],'independence_key':'DILA-compiled-authority','url':'https://authority.dila.edu.tw/person/search.php?aid='+aid}]}]}
 if not any(s['id']==code for s in g.schemes(c)):g.save_scheme(c,config,0)
print('Registry systems:',len(g.schemes(c)));c.close()
