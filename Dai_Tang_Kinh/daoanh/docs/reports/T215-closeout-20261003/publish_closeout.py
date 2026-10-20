# -*- coding: utf-8 -*-
"""Báo cáo từng file và Dashboard admin, giữ tên pending trống status."""
import json,sqlite3,html,hashlib,datetime
from pathlib import Path
D=Path.cwd()/'daoanh';O=D/'docs/reports/T215-closeout-20261003';B=D/'data/backups/T215-closeout-20261003';R=D/'docs/reports/T215-eight-uri-20261003'
P=json.loads((B/'change-plan.json').read_text(encoding='utf-8'));S=json.loads((O/'after-audit/summary.json').read_text(encoding='utf-8')); V=json.loads((O/'api-verification.json').read_text(encoding='utf-8')); SY=json.loads((B/'sync-report.json').read_text(encoding='utf-8'));assert SY['committed'] and all(x['pass'] for x in V)
def dump(x):return json.dumps(x,ensure_ascii=False,indent=2)+'\n'
def write(p,text):
 if p.exists():
  raw=p.read_bytes();dest=B/'docs'/p.relative_to(D);dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(raw)
  assert p.read_bytes()==raw,'File đang đổi: '+str(p)
 p.write_text(text,encoding='utf-8',newline='\n')
esc=lambda s:html.escape(str(s))
records=json.loads((R/'cases.json').read_text(encoding='utf-8'))
for c in records['cases']:
 case=c['case'];e=c.get('reconstruction_evidence')
 c['closeout_report']='../T215-closeout-20261003/README.md'
 if case==1:
  c.update(display_status='DONE',status='TTL → DB → API đã khớp',db_action='Đã sync A003636, thầy A001897; API kiểm lại PASS',note=c['note']+' Đồng bộ DB và API 2026-10-03 PASS.')
  if e:
   e['verified_claims'].append('DB và API đã dùng TS-Phuoc-Chau-Dai-An.ttl, A003636; cạnh thầy A001897 có nguồn DILA, Marcus, TTL.')
   e['unresolved_claims']=[x for x in e['unresolved_claims'] if 'chưa đồng bộ DB' not in x]
   e['next_steps']=['Đã sync riêng và kiểm API PASS; số37 chỉ giữ tham chiếu TTL, chưa tái chứng nhận số đời.']
 elif case==4:
  c['note']+=' Đợt closeout: chuyển bản trùng TS-Dao-Ninh-Dao-Khoan.ttl ra thư mục cách ly; bản chính và URI dao_ninh_dao_khoan giữ nguyên.'
 else:
  c['display_status']='';c['exists']=False
  c['active_file_action']='absent_before_closeout' if case in (2,8) else 'quarantined_with_backup'
  if e:
   if case==8:
    e['verified_claims'].append('Đã sửa riêng DB Thạch Cữu: provenance TS-Thach-Cuu.ttl, A019919; thầy Mã Tổ A003623. API PASS. Không tạo TTL Linh Cưu.')
    e['next_steps']=[x for x in e['next_steps'] if 'provenance' not in x]+['Linh Cưu vẫn chờ tên Hán và chứng cứ cùng người; không dùng dữ liệu Thạch Cữu.']
   elif case==2:e['verified_claims'].append('TS-Di-Phong-Kinh-Ninh.ttl đã không còn trong corpus trước đợt closeout; không tái tạo và không gán ID.')
   else:e['verified_claims'].append('File sai/rỗng đã được lưu nguyên trạng trong data/ttl_quarantine/T215-closeout-20261003; không tiếp tục import bản này.')
 if e:
  e['closeout_report']='../../T215-closeout-20261003/README.md'
  lines=['# '+c['file'],'','Chứng cứ để tạo TTL sau; trạng thái chưa xác minh giữ trống trên Dashboard.','']
  for title,key in [('Đã xác minh','verified_claims'),('Chưa xác minh','unresolved_claims'),('Bác bỏ','rejected_claims'),('Bước tiếp theo','next_steps'),('Nguồn','sources')]:
   lines+=['## '+title,'']+[('- '+x) for x in e[key]]+['']
  lines+=['[Báo cáo closeout](../../T215-closeout-20261003/README.md)','',e['generation_rule']]
  write(R/e['evidence_file'],'\n'.join(lines)+'\n')
write(R/'cases.json',dump(records))
public={'task':'T215','title':'Đối chiếu 8 URI TTL','cases':[dict(file=c['file'],status=c['display_status'],**({'evidence':c['reconstruction_evidence']} if not c['display_status'] else {})) for c in records['cases']]}
write(D/'dashboard/t215-eight-uri-cases.json',dump(public))
style='body{margin:0;background:#020617;color:#e2e8f0;font:16px/1.6 Inter,system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:24px}a,h1,h2,h3{color:#fbbf24}table{width:100%;border-collapse:collapse;background:#0f172a}td,th{padding:12px;text-align:left;border-bottom:1px solid #334155;vertical-align:top}td:first-child,pre{overflow-wrap:anywhere}summary{cursor:pointer}details,section{background:#0f172a;border:1px solid #334155;border-radius:10px;padding:12px;margin:12px 0}pre{white-space:pre-wrap;font-size:14px}.done{color:#86efac;font-weight:700}'
def page(title,content):return '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+style+'</style></head><body><main><a href="dashboard_process.html">← Dashboard</a><h1>'+esc(title)+'</h1>'+content+'</main></body></html>\n'
rows=[]
for c in records['cases']:
 if c['display_status']:rows.append('<tr><td>'+esc(c['file'])+'</td><td class="done">DONE</td></tr>');continue
 e=c['reconstruction_evidence'];detail=''
 for title,key in [('Đã xác minh','verified_claims'),('Chưa xác minh','unresolved_claims'),('Không dùng / đã bác bỏ','rejected_claims'),('Dùng khi tạo TTL sau','next_steps')]:
  detail+='<h3>'+title+'</h3><ul>'+''.join('<li>'+esc(x)+'</li>' for x in e[key])+'</ul>'
 detail+='<h3>Nguồn</h3><ul>'+''.join('<li><a href="'+esc(x)+'">'+esc(x)+'</a></li>' for x in e['sources'])+'</ul><p>'+esc(e['generation_rule'])+'</p>'
 rows.append('<tr><td><details><summary>'+esc(c['file'])+'</summary>'+detail+'</details></td><td></td></tr>')
write(D/'dashboard/t215-eight-uri.html',page('T215 — Đối chiếu 8 URI TTL','<p>Bấm filename để xem chứng cứ dùng khi tạo TTL sau.</p><table><thead><tr><th>Filename và chứng cứ</th><th>Trạng thái</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'))
write(R/'README.md','# T215 — Đối chiếu 8 URI TTL\n\n| Filename | Trạng thái |\n|---|---|\n'+''.join('| '+('['+c['file']+']('+c['reconstruction_evidence']['evidence_file']+')' if not c['display_status'] else c['file'])+' | '+c['display_status']+' |\n' for c in records['cases']))
# Hồ sơ từng file: index nhỏ chứa cấu trúc, không nạp kinh văn vào RAM.
findings=[]
with (O/'after-audit/findings.jsonl').open(encoding='utf-8') as stream:
 for line in stream:findings.append(json.loads(line))
byfile={}
for f in findings:
 files=([f['file']] if 'file' in f else f.get('files',[]));files=files.split(',') if isinstance(files,str) else files
 for name in files:byfile.setdefault(name,[]).append(f)
idx=sqlite3.connect(O/'after-audit/index.sqlite');idx.row_factory=sqlite3.Row;decisions=[]
with (O/'file-decisions.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
 for r in idx.execute('select * from nodes order by file'):
  data=dict(r);data['findings']=byfile.get(r['file'],[]);data['academic_verified']=False;data['action']='skip_unconfirmed' if data['findings'] else 'no_structural_conflict_found';data['reason']='Không tự sửa tên/ID/quan hệ/đời khi thiếu chứng cứ; alias P1 và tên file không tự coi là lỗi.';stream.write(json.dumps(data,ensure_ascii=False)+'\n');decisions.append(data)
idx.close()
gen=[f for f in findings if f['code']=='GENERATION_REVIEW'];write(O/'generation-review.json',dump({'count':len(gen),'action':'Giữ nguyên mọi số đời; cần ít nhất3 dữ liệu độc lập và cùng hệ đếm.','cases':gen}))
verified_files={'TS-Phuoc-Chau-Dai-An.ttl','TS-Ma-To-Dao-Nhat.ttl','TS-Phong-Huyet-Dien-Chieu.ttl','TS-Thach-Cuu.ttl','TS-Dai-Ninh-Dao-Khoan.ttl'}
write(O/'decision-summary.json',dump({'files':len(decisions),'files_with_review_flags':len(byfile),'structural_conflicts':0,'generation_review_pairs':len(gen),'identity_api_verified_in_this_round':sorted(verified_files),'skipped_remapped_edges':P['skipped_edges'],'limitations':S['limitations']}))
content='<section><strong>Đợt closeout 2026-10-03: 1037/1037 TTL đang dùng đọc được.</strong><p>0 cạnh tự nối, 0 URI trùng, 0 vòng thầy–trò; số đời giữ nguyên. 7 file lỗi/trùng đã lưu cách ly. 9 hồ sơ tự nối trước đây vẫn là đợt đã hoàn tất; T215 toàn corpus còn các mục thiếu chứng cứ.</p><p>Đã sync Phước Châu; sửa provenance Thạch Cữu; sửa ID Mã Tổ/Phong Huyệt; hợp nhất Đại Ninh. Rút 142 assertion TTL sai và bổ sung 72 assertion có DILA xác nhận. Nguồn DILA/Marcus/Lineage không đổi.</p><a href="/daoanh/docs/reports/T215-closeout-20261003/README.md">Báo cáo, rollback và kết quả API</a> · <a href="t215-eight-uri.html">8 hồ sơ URI</a></section><h2>26 cặp đời: giữ nguyên, chờ ít nhất 3 dữ liệu độc lập</h2>'
for f in gen:content+='<details><summary>'+esc(f['teacher'])+' → '+esc(f['disciple'])+'</summary><pre>'+esc(dump(f))+'</pre><p>Chưa đủ chứng cứ để kết luận số sai hoặc số đúng; không suy thầy+1.</p></details>'
content+='<h2>'+str(len(byfile))+' file có cờ cần đối chiếu</h2><p>Cờ không đồng nghĩa lỗi học thuật. Danh tính, P1 alias, tên file và quan hệ chưa xác minh được giữ nguyên; chi tiết từng file có trong file-decisions.jsonl.</p>'
for r in decisions:
 if not r['findings']:continue
 content+='<details><summary>'+esc(r['file'])+' · '+esc(', '.join(sorted({f['code'] for f in r['findings']})))+'</summary><pre>'+esc(dump(r))+'</pre></details>'
write(D/'dashboard/t215-other-ttl-bugs.html',page('T215 — Kết quả toàn corpus và hồ sơ còn chờ',content))
write(D/'dashboard/t215-closeout-summary.json',dump({'task':'T215','updated':'2026-10-03','status':'in_progress','audit':S,'api':V,'generation_unchanged':True,'quarantined_files':[x['file'] for x in P['files'] if x['action']=='quarantine'],'report_url':'/daoanh/docs/reports/T215-closeout-20261003/README.md'}))
print('DASHBOARD_UPDATED; FILE_DOSSIERS='+str(len(decisions))+'; REVIEW_FILES='+str(len(byfile))+'; GENERATION_UNCHANGED')
