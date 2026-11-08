# -*- coding: utf-8 -*-
"""T232: mặc định dry-run; --apply tạo kho additive sau SQLite backup."""
import argparse,hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src_python import generation_engine_v2 as g

def seed_configs(conn):
    cbeta=ROOT/'data/cbeta/xml-p5-full/T/T48/T48n2008.xml'
    raw=cbeta.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if '惠能是為三十三祖' not in raw.decode('utf8'):
        raise ValueError('CBETA local không có câu chứng minh Huệ Năng 33.')
    e={'citation':'六祖大師法寶壇經 T48n2008_p0361c15–19: Đạt Ma 28, Huệ Năng 33; quy ước Ca Diếp 1.',
       'version':'local-sha256:'+sha,'independence_key':'T2008-Zongbao-edition',
       'url':'https://cbetaonline.dila.edu.tw/zh/T2008_001#p0361c15'}
    def anchor(aid,name,n,evidence):
        return {'person_id':aid,'name_zh':name,'number':n,'status':'source_asserted','evidence':evidence,
                'rationale':'Mốc sử liệu/quy ước để tính dự kiến; chưa đủ 3 chứng cứ độc lập để duyệt.'}
    def dila(aid,citation):
        i=g.identity(conn,aid)
        return {'citation':citation,'version':i['version']+':'+i['sha256'],'independence_key':'DILA-compiled-authority',
                'url':'https://authority.dila.edu.tw/person/search.php?aid='+aid}
    bodhi=anchor('A001361','菩提達磨',28,[e,dila('A001361','DILA concise: 西天第二十八祖')])
    hui=anchor('A001719','惠能',33,[e])
    sect={'citation':'Pháp cổ sơn EP199: 興化存獎．臨濟二祖; đường 義玄 → 存獎.',
      'version':'2025-05-20','independence_key':'DDM-EP199-editorial',
      'url':'https://www.ddcep.org.tw/default-ddmtw/xmnews/cont?qcat=0L221596734435375771&sid=0P135550259221313171&xsmsid=0L207419114119814182'}
    configs=[{'id':'chan_ca_diep_1','label':'Thiền Tông · Ca Diếp 1',
      'convention':'Danh sách tổ truyền thống: Ca Diếp=1, Thích Ca=gốc 0; Đạt Ma=28, Huệ Năng=33. Mốc tính gần nhất, không mặc nhiên chứng thực toàn bộ lịch sử.',
      'root_id':'A001361','policy':'dila_candidate','anchors':[bodhi,hui]},
      {'id':'linji','label':'Lâm Tế Tông','convention':'Lâm Tế Nghĩa Huyền=1; truyền pháp trực tiếp cộng 1; Hưng Hóa Tồn Tưởng=2.',
       'root_id':'A003627','policy':'dila_candidate','anchors':[
        anchor('A003627','臨濟義玄',1,[sect,dila('A003627','DILA ID chính xác khai tổ Lâm Tế')]),
        anchor('A004980','興化存獎',2,[sect,dila('A004980','DILA concise: 臨濟義玄禪師法嗣')])]},
      {'id':'linji_yangqi','label':'Lâm Tế · Dương Kỳ','convention':'Dương Kỳ Phương Hội=1 trong nhánh Dương Kỳ; số này độc lập đời Lâm Tế tổng.',
       'root_id':'A004146','policy':'dila_candidate','anchors':[
        anchor('A004146','楊岐方會',1,[dila('A004146','DILA sect 臨濟宗 楊岐派; concise pháp hệ gọi 楊岐派; khai tổ=1 là quy ước riêng.')])]},
      {'id':'linji_chucthanh','label':'Lâm Tế · Chúc Thánh','convention':'Khai tổ Chúc Thánh=1; cần chứng minh định danh Minh Hải–Pháp Bảo trước khi nhập mốc. Không gán A000662 chỉ vì trùng tên 明海.',
       'root_id':'','policy':'dila_candidate','anchors':[]}]
    return [g.validate_scheme(conn,c) for c in configs]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(ROOT/'data/lineage.db',timeout=30);c.row_factory=sqlite3.Row
    configs=seed_configs(c);(out/'seed-schemes.json').write_text(json.dumps(configs,ensure_ascii=False,indent=2),encoding='utf8')
    if not args.apply:print('DRY-RUN: 4 hệ đếm; 0 DB writes.');return
    if g.table(c,'generation_v2_scheme_revisions') and g.schemes(c):
        raise ValueError('Registry đã cài; không ghi đè revision hiện có.')
    backup=out/'lineage-before.db'
    if backup.exists():raise ValueError('Backup đã có; chọn thư mục mới để giữ rollback.')
    snap=sqlite3.connect(backup);c.backup(snap,pages=512);snap.close()
    tables=['people','vn_person_authority','vn_person_relations','lineage_edge_assertions','person_gen_computed']
    before={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
    g.ensure_schema(c)
    for config in configs:g.save_scheme(c,config,0)
    after={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
    assert before==after
    (out/'install-result.json').write_text(json.dumps({'schemes':4,'before':before,'after':after,'legacy_mutations':0,'backup':str(backup)},indent=2),encoding='utf8')
    print('PASS: 4 registry revisions; 0 sửa bảng nguồn/legacy. Backup:',backup)

if __name__=='__main__':
    try:main()
    except Exception as e:print('Không cài được số đời v2:',str(e),file=sys.stderr);sys.exit(1)
