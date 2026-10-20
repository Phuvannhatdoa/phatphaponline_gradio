# -*- coding: utf-8 -*-
"""T215: áp dụng/hoàn tác có guard file và snapshot DB từng row."""
import sys,json,sqlite3,hashlib,datetime,argparse,shutil
from pathlib import Path
D=Path.cwd()/'daoanh';O=D/'docs/reports/T215-closeout-20261003';B=D/'data/backups/T215-closeout-20261003';Q=D/'data/ttl_quarantine/T215-closeout-20261003'
sys.path.insert(0,str(D/'data/backups/T215-fix-sync-20261002/python-deps'))
from rdflib import Graph
P=json.loads((B/'change-plan.json').read_text(encoding='utf-8')); now=datetime.datetime.now().isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
def rr(c,q,a=()):return [dict(r) for r in c.execute(q,a)]
def qs(x):return ','.join('?' for _ in x)
def protection(c):
 h=hashlib.sha256()
 for r in c.execute("select * from lineage_edge_assertions where source_code!='TTL' order by id"):h.update(json.dumps(dict(r),sort_keys=True).encode())
 return h.hexdigest()
slugs=[r['id'] for r in P['authority_before']]+['phuoc_chau_dai_an']
refs=P['quarantine_refs']+list(P['parsed_focus'])+['TS-Dai-Ninh-Dao-Khoan']
for x in P['files']:
 if x['action']=='text_fix':refs.append(Path(x['file']).stem)
ids=[r['id'] for r in P['bad_assertions']]
pairs=sorted({(r['subject_person_id'],r['object_person_id']) for r in P['bad_assertions']}|{(r['teacher'],r['disciple']) for r in P['accepted_edges']})
edge_refs=sorted(set(refs+[r['ref'] for r in P['accepted_edges']]))
def snapshot(c):
 return {'vn_person_authority':rr(c,'select * from vn_person_authority where id in ('+qs(slugs)+') or ttl_filename in ('+qs(refs)+') order by id',slugs+refs),
 'vn_person_relations':rr(c,'select * from vn_person_relations where person_id in ('+qs(slugs)+') or ttl_filename in ('+qs(refs)+') order by id',slugs+refs),
 'lineage_edge_assertions':rr(c,"select * from lineage_edge_assertions where id in ("+qs(ids)+") or (source_code='TTL' and ref in ("+qs(edge_refs)+')) order by id',ids+edge_refs),
 'lineage_edge_consensus':rr(c,'select * from lineage_edge_consensus where '+' or '.join('(teacher_id=? and disciple_id=?)' for _ in pairs)+' order by id',[x for p in pairs for x in p]),
 'people':rr(c,"select * from people where id='A038890'")}
def restore(c,b,a):
 for table in b:
  old={r['id']:r for r in b[table]};new={r['id']:r for r in a[table]}
  for ident in new.keys()-old.keys():c.execute('delete from '+table+' where id=?',(ident,))
  for ident,r in old.items():
   if ident not in new:c.execute('insert into '+table+' ('+','.join(r)+') values('+qs(r)+')',list(r.values()))
   else:
    cols=[k for k in r if k!='id'];c.execute('update '+table+' set '+','.join(k+'=?' for k in cols)+' where id=?',[r[k] for k in cols]+[ident])
def check_files(before=True):
 for p in P['files']:
  target=(D/'data/ttl'/p['file']).resolve();assert target.is_relative_to(D.resolve()),'Đường dẫn ngoài workspace'
  if not before and p['action']=='quarantine':target=(Q/p['file']).resolve(); assert not (D/'data/ttl'/p['file']).exists()
  assert sha(target.read_bytes())==p['before_sha256'] if before or p['action']=='quarantine' else sha(target.read_bytes())==p['after_sha256'],p['file']+' đã đổi; dừng để không đè session khác'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--revert',action='store_true');a=ap.parse_args();assert not(a.apply and a.revert)
 c=sqlite3.connect(D/'data/lineage.db',timeout=30);c.row_factory=sqlite3.Row;changed=[]
 try:
  c.execute('BEGIN IMMEDIATE')
  if a.revert:
   R=json.loads((B/'sync-report.json').read_text(encoding='utf-8'));assert R['committed'];assert snapshot(c)==R['after'],'DB đã đổi, không ghi đè rollback';check_files(False)
   restore(c,R['before'],R['after'])
   for p in P['files']:
    target=D/'data/ttl'/p['file'];assert target.resolve().is_relative_to(D.resolve())
    target.write_bytes((B/'ttl'/p['file']).read_bytes())
   c.commit();dump(B/'rollback-result.json',{'restored':True,'checked_at':now,'note':'Bản cách ly còn nguyên để đối chiếu, không xoá.'});print('ROLLBACK_PASS');return
  assert not (B/'sync-report.json').exists(),'Đã sync; không apply hai lần';check_files()
  for r in P['authority_before']:assert rr(c,'select * from vn_person_authority where id=?',(r['id'],))==[r],'Authority đã đổi '+r['id']
  for r in P['bad_assertions']:assert rr(c,'select * from lineage_edge_assertions where id=?',(r['id'],))==[r],'Assertion đã đổi'
  before=snapshot(c);guard=protection(c)
  if not a.apply:c.rollback();dump(O/'preflight.json',{'pass':True,'file_actions':len(P['files']),'reject_ttl':len(ids),'accepted_source_edges':len(P['accepted_edges']),'skip_edges':len(P['skipped_edges']),'row_snapshot_counts':{k:len(v) for k,v in before.items()}});print('PREFLIGHT_PASS; chưa ghi DB/TTL');return
  (B/'ttl').mkdir(exist_ok=True);Q.mkdir(parents=True,exist_ok=True)
  for p in P['files']:
   dest=B/'ttl'/p['file'];assert not dest.exists();dest.write_bytes((D/'data/ttl'/p['file']).read_bytes())
  dump(B/'db-before.json',before)
  # Chỉ metadata người có danh tính khóa bằng DILA; đời đã có luôn giữ nguyên.
  bindings={'ma_to_dao_nhat':('A003623','馬祖道一'),'phong_huyet_dien_chieu':('A004982','風穴延沼'),'phuoc_chau_dai_an':('A003636','福州大安'),'thach_cuu':('A019919','石臼')}
  for f,p in P['parsed_focus'].items():
   s=p['slug'];aid,zh=bindings.get(s,('', ''));old=rr(c,'select * from vn_person_authority where id=?',(s,));v={'ttl_filename':f,'name_vi':p['label'],'name_zh':zh,'dila_id':aid,'status':'verified','biographical_note_vi':p['bio'].strip(),'dharma_lineage':p['lineage'],'gender':'Male'}
   if s=='phat_y_linh_nhac':
    # File chép tên Trường Viễn vào URI Phật Ý; giữ ID/đời đang có, chỉ phục hồi provenance và văn bản đúng.
    v.pop('dila_id');v.pop('name_zh');v['status']='pending'
   if old:c.execute('update vn_person_authority set '+','.join(k+'=?' for k in v)+' where id=?',list(v.values())+[s])
   else:
    assert s=='phuoc_chau_dai_an';v.update(id=s,generation_order=int(p['generation']),is_lineage_founder=0);c.execute('insert into vn_person_authority ('+','.join(v)+') values('+qs(v)+')',list(v.values()))
  # Alias spelling Phúc Châu giữ nguyên. Bản stub trống không được coi là TTL của alias.
  # Rút local relation lấy từ file cách ly; không xoá assertion lịch sử.
  c.execute('delete from vn_person_relations where ttl_filename in ('+qs(P['quarantine_refs'])+') and ttl_filename!=?',P['quarantine_refs']+['TS-Dao-Ninh-Dao-Khoan'])
  c.execute("update vn_person_relations set ttl_filename='TS-Dai-Ninh-Dao-Khoan' where ttl_filename='TS-Dao-Ninh-Dao-Khoan'")
  c.execute("update lineage_edge_assertions set ref='TS-Dai-Ninh-Dao-Khoan' where source_code='TTL' and ref='TS-Dao-Ninh-Dao-Khoan'")
  for f,p in P['parsed_focus'].items():
   for kind,key in [('hasTeacher','teachers'),('hasDisciple','students')]:
    for target in p[key]:
     label=(c.execute('select name_vi from vn_person_authority where id=?',(target,)).fetchone() or [''])[0]
     c.execute('insert or ignore into vn_person_relations(person_id,relation_type,target_id,target_label_vi,ttl_filename) values(?,?,?,?,?)',(p['slug'],kind,target,label,f))
     # UNIQUE local edge: chuyển provenance sai của Thạch Cữu sang file đang dùng.
     if p['slug']=='thach_cuu':c.execute('update vn_person_relations set ttl_filename=?,target_label_vi=? where person_id=? and relation_type=? and target_id=?',(f,label,p['slug'],kind,target))
  c.execute("update people set name_vi=NULL where id='A038890' and name_vi='Mã Tổ Đạo Nhất'")
  c.execute("update lineage_edge_assertions set status='rejected',mapping_verified=0 where id in ("+qs(ids)+')',ids)
  inserted=[]
  for x in P['accepted_edges']:
   t,d,f=x['teacher'],x['disciple'],x['ref']
   if c.execute("select 1 from lineage_edge_assertions where source_code='TTL' and status='active' and mapping_verified=1 and subject_person_id=? and object_person_id=? and ref=?",(t,d,f)).fetchone():continue
   c.execute("insert into lineage_edge_assertions(edge_key,subject_person_id,relation_type,object_person_id,source_code,raw_relation_type,ref,mapping_verified,trust_level,status,created_at) values(?,?,'da:isTeacherOf',?,'TTL',?,?,1,'L2','active',?)",('TTL|'+t+'|'+d,t,d,x['raw_relation_type'],f,now));inserted.append(c.execute('select last_insert_rowid()').fetchone()[0])
  for t,d in pairs:
   active=int(bool(c.execute("select 1 from lineage_edge_assertions where source_code='TTL' and status='active' and mapping_verified=1 and subject_person_id=? and object_person_id=?",(t,d)).fetchone()))
   for r in rr(c,'select * from lineage_edge_consensus where teacher_id=? and disciple_id=?',(t,d)):
    flags=[r['dila_asserted'],r['marcus_asserted'],active,r['lineage_asserted']];n=sum(bool(v) for v in flags);badge=', '.join(s for s,v in zip(['DILA','Marcus','TTL','Lineage'],flags) if v)
    c.execute('update lineage_edge_consensus set ttl_asserted=?,agreeing_source_count=?,consensus_status=?,source_badge=?,updated_at=? where id=?',(active,n,'confirmed_2plus' if n>=2 else ('single_source' if n else 'unconfirmed'),badge,now,r['id']))
  # Đồng bộ Ð -> Đ ở đúng các row có cùng provenance, không đổi ID/quan hệ/đời.
  for p in P['files']:
   if p['action']=='text_fix':
    f=Path(p['file']).stem
    for r in rr(c,'select * from vn_person_authority where ttl_filename=?',(f,)):
     v={k:r[k].replace('\u00d0','\u0110') for k in ('name_vi','biographical_note_vi','dharma_lineage') if isinstance(r[k],str) and '\u00d0' in r[k]}
     if v:c.execute('update vn_person_authority set '+','.join(k+'=?' for k in v)+' where id=?',list(v.values())+[r['id']])
    for r in rr(c,'select * from vn_person_relations where ttl_filename=?',(f,)):
     if r['target_label_vi'] and '\u00d0' in r['target_label_vi']:c.execute('update vn_person_relations set target_label_vi=? where id=?',(r['target_label_vi'].replace('\u00d0','\u0110'),r['id']))
  assert protection(c)==guard,'Nguồn DILA/Marcus/Lineage bị thay đổi'
  after=snapshot(c)
  oldgen={r['id']:r['generation_order'] for r in before['vn_person_authority']};assert all(r['generation_order']==oldgen[r['id']] for r in after['vn_person_authority'] if r['id'] in oldgen)
  assert not c.execute("select 1 from lineage_edge_assertions where source_code='TTL' and status='active' and (subject_person_id='A038890' or object_person_id='A038890')").fetchone()
  # Kiểm hoàn tác trên snapshot nhỏ, không copy toàn DB vào RAM.
  m=sqlite3.connect(':memory:');m.row_factory=sqlite3.Row
  for table,data in after.items():
   m.execute(c.execute('select sql from sqlite_master where name=?',(table,)).fetchone()[0])
   for r in data:m.execute('insert into '+table+' ('+','.join(r)+') values('+qs(r)+')',list(r.values()))
  restore(m,before,after);assert snapshot(m)==before;m.close()
  for p in P['files']:
   target=D/'data/ttl'/p['file'];assert sha(target.read_bytes())==p['before_sha256']
   if p['action']=='quarantine':
    dest=(Q/p['file']).resolve();assert dest.is_relative_to(D.resolve()) and not dest.exists();target.rename(dest)
   else:
    Graph().parse(data=p['after_text'],format='turtle');target.write_bytes(p['after_text'].encode('utf-8'));assert sha(target.read_bytes())==p['after_sha256']
   changed.append(p)
  check_files(False)
  R={'committed':False,'checked_at':now,'before':before,'after':after,'inserted_assertion_ids':inserted,'rejected_assertion_ids':ids,'rollback_test':'PASS','non_ttl_source_hash_before':guard,'non_ttl_source_hash_after':protection(c),'generation_existing_rows_unchanged':True,'quarantine_files':[p for p in P['files'] if p['action']=='quarantine'],'file_actions':[(p['file'],p['action']) for p in P['files']]}
  dump(B/'sync-report.json',R);c.commit();R['committed']=True;dump(B/'sync-report.json',R);dump(Q/'manifest.json',{'task':'T215','created_at':now,'files':R['quarantine_files'],'canonical_duplicates':{'TS-Dao-Ninh-Dao-Khoan.ttl':'TS-Dai-Ninh-Dao-Khoan.ttl'},'restoration_script':'docs/reports/T215-closeout-20261003/apply_closeout.py --revert'});print('DB_SYNC_PASS; FILE_GUARDS_PASS; ROLLBACK_TEST_PASS; REJECTED='+str(len(ids))+'; ADDED='+str(len(inserted)))
 except Exception:
  c.rollback()
  for p in changed:
   target=D/'data/ttl'/p['file']
   if p['action']=='quarantine' and (Q/p['file']).exists() and not target.exists():(Q/p['file']).rename(target)
   elif p['action']!='quarantine':target.write_bytes((B/'ttl'/p['file']).read_bytes())
  raise
 finally:c.close()
if __name__=='__main__':
 try:main()
 except Exception as e:print('Lỗi T215: '+str(e));sys.exit(1)
