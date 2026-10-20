import argparse,copy,json,sqlite3,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from src_python import generation_engine_v2 as g
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
c=sqlite3.connect(root/'data/lineage.db',timeout=30);c.row_factory=sqlite3.Row
configs=g.schemes(c);before=next(x for x in configs if x['id']=='linji_chucthanh')
if before['anchors'] or before['root_id']:raise ValueError('Chúc Thánh đã có mốc ở phiên khác; dừng để đối soát trước.')
identity=g.identity(c,'A000662','明海');config=copy.deepcopy(before)
decision={'dila_id':'A000662','dila_name_zh':'明海','excluded_target_name_vi':'Minh Hải Pháp Bảo — khai tổ Lâm Tế Chúc Thánh','resolution':'distinct_person','basis':'Admin xác nhận khác thời đại, hai nhân vật khác nhau.','provenance_kind':'admin_confirmation','confirmed_at':'2026-10-05','reviewer':'Admin','user_statement':'A000662 明海  : xác nhận là nhân vật khác Minh Hải Pháp Bảo của Khai Tổ Lâm Tế Chúc Thánh, hai thời đại, 2 nhân vật khác nhau.','dila_record':identity}
existing=config.get('identity_decisions',[])
if any(x.get('dila_id')=='A000662' and x.get('resolution')=='distinct_person' for x in existing):print('NO-OP: quyết định đã được lưu.');sys.exit(0)
config['identity_decisions']=existing+[decision]
config['convention']='Khai tổ Chúc Thánh=1. Admin xác nhận ngày 2026-10-05: A000662 明海 là nhân vật khác Minh Hải Pháp Bảo Chúc Thánh, thuộc thời đại khác; loại trừ ID này khỏi định danh khai tổ Chúc Thánh. Chưa xác minh được ID riêng của Minh Hải Pháp Bảo nên root_id và anchors để trống; không gán số đời bằng ID này.'
g.validate_scheme(c,config)
folder=Path(__file__).parent
(folder/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf8')
(folder/'proposed-scheme.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8')
if not args.apply:print(json.dumps({'dry_run':True,'expected_revision':before['_revision'],'decision':decision},ensure_ascii=False));sys.exit(0)
backup=root/'data/backups/T232-A000662-distinct-20261005';backup.mkdir(parents=True,exist_ok=True)
with (backup/'scheme-before.json').open('x',encoding='utf8') as f:json.dump(before,f,ensure_ascii=False,indent=2)
other_before={x['id']:x['_sha256'] for x in configs if x['id']!='linji_chucthanh'}
person_before=dict(c.execute('SELECT * FROM people WHERE id=?',('A000662',)).fetchone())
map_before=[dict(x) for x in c.execute('SELECT * FROM name_vi_map WHERE dila_id=?',('A000662',))]
after=g.save_scheme(c,config,before['_revision'])
assert not after['anchors'] and not after['root_id']
assert other_before=={x['id']:x['_sha256'] for x in g.schemes(c) if x['id']!='linji_chucthanh'}
assert person_before==dict(c.execute('SELECT * FROM people WHERE id=?',('A000662',)).fetchone())
assert map_before==[dict(x) for x in c.execute('SELECT * FROM name_vi_map WHERE dila_id=?',('A000662',))]
computed=g.compute(c,'A000662',after);assert computed['number'] is None and computed['status']=='missing_anchor'
result={'before_revision':before['_revision'],'after_revision':after['_revision'],'after_sha256':after['_sha256'],'distinct_decision_persisted':True,'other8scheme_hashes_unchanged':True,'dila_person_and_name_map_unchanged':True,'ttl_mapping_bad_links':0,'chucthanh_number_for_A000662':computed['number'],'calculation_status':computed['status'],'backup':str(backup/'scheme-before.json')}
(folder/'apply-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');(folder/'scheme-after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False));c.close()
