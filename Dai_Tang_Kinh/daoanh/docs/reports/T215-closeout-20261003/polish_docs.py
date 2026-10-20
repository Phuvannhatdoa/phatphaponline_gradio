# -*- coding: utf-8 -*-
import re
from pathlib import Path
D=Path.cwd()/'daoanh'
replacements={
 'sốđời':'số đời','thầy+1':'thầy + 1','ít nhất3':'ít nhất 3','MãTổ':'Mã Tổ','PhongHuyệt':'Phong Huyệt','PhướcChâu':'Phước Châu','ThạchCữu':'Thạch Cữu','ĐạiNinh':'Đại Ninh','DiPhong':'Di Phong','TríBản':'Trí Bản','ĐạiXa':'Đại Xa','MinhHoằng':'Minh Hoằng','TuyếtGiàu':'Tuyết Giàu','LinhCưu':'Linh Cưu','PhậtÝ':'Phật Ý','MappingTênViệt':'Mapping Tên Việt',
 'chứngcứ':'chứng cứ','chứngminh':'chứng minh','xácminh':'xác minh','xác nhận':'xác nhận','khôngđổi':'không đổi','giữnguyên':'giữ nguyên','dữliệu':'dữ liệu','độc lập/cùng':'độc lập, cùng','cùnghệđếm':'cùng hệ đếm','hệđếm':'hệ đếm','căn cứ':'căn cứ','thiếucăn':'thiếu căn','thiếu dữliệu':'thiếu dữ liệu','địnhdanh':'định danh','danh tính':'danh tính',
 'quốctế':'quốc tế','bấtbiến':'bất biến','tiếpsession':'tiếp session','cáchly':'cách ly','đốichiếu':'đối chiếu','đối chiếu':'đối chiếu','truyvết':'truy vết','nguyêntắc':'nguyên tắc','đềxuất':'đề xuất','bổsung':'bổ sung','bỏqua':'bỏ qua','tựnối':'tự nối','URItrùng':'URI trùng','gánnhầm':'gán nhầm','hồsơ':'hồ sơ','statustrống':'status trống','chưaxácminh':'chưa xác minh','từngngười':'từng người','cờ chờ':'cờ chờ',
 'khônggittrack':'không git track','khôngcommit/stage':'không commit/stage','khôngcommit':'không commit','khôngsuy':'không suy','khôngrestore':'không restore','khônggánID':'không gán ID','khôngtồn':'không tồn','không tìmthấy':'không tìm thấy','khôngtìmthấy':'không tìm thấy','khôngđồng':'không đồng','đồngnghĩa':'đồng nghĩa','khôngsửa':'không sửa','khôngimport':'không import','khôngép':'không ép','khôngapply':'không apply','không mất':'không mất',
 'thiếucăn cứ':'thiếu căn cứ','từngrow':'từng row','từngfile':'từng file','rowcũ':'row cũ','rowmới':'row mới','snapshotcũ':'snapshot cũ','thầyA':'thầy A','tròA':'trò A','đờiNULL':'đời NULL','TTL35':'TTL 35','TTL41':'TTL 41','chỉthamchiếu':'chỉ tham chiếu','chỉ localDB':'chỉ local DB','LocalDB':'Local DB','localDB':'local DB','cảDB':'cả DB',
 'rawXML':'raw XML','RawXML':'Raw XML','sourceURL':'source URL','nguồnquốc':'nguồn quốc','logWindows':'log Windows','filecách':'file cách','folderngười':'folder người','người khác':'người khác','bảncách':'bản cách','bảnDILA':'bản DILA','bịbácbỏ':'bị bác bỏ','choĐại':'cho Đại','thiếucăn':'thiếu căn','suyđoán':'suy đoán','tái tạo':'tái tạo','khóa danh':'khóa danh',
 'gitadd':'git add','gittrack':'git track','cảdocs/tasks':'cả docs/tasks','backupbytes':'backup bytes','bắtbuộc':'bắt buộc','fullETL':'full ETL','bypassguard':'bypass guard','outputriêng':'output riêng','outputmới':'output mới','sessionkhác':'session khác','trước khôi':'trước khôi','HEAD diđộng':'HEAD di động','fullETL':'full ETL',
 'nhánhclick':'nhánh click','chưakiểmclick':'chưa kiểm click','clickđó':'click đó','làmxanh':'làm xanh','chưakiểm':'chưa kiểm','chưaxác':'chưa xác','suite hiệncó':'suite hiện có','theologi':'theo logi','source-edge':'source-edge','appendlặp':'append lặp','logspipeline':'logs pipeline','cuốiphiên':'cuối phiên','khôngchạy':'không chạy','memory-save.json/tasktodo':'memory-save.json và tasktodo',
 'agentkếtiếp':'agent kế tiếp','source/old-value/hashguard':'source/old-value/hash guard','DILAcanonical':'DILA canonical','TTLViệtthamchiếu':'TTL Việt tham chiếu','snapshotnhỏ':'snapshot nhỏ','Guardfail':'Guard fail','hashguard':'hash guard','rawtemplate':'raw template','backtickMarkdown':'backtick Markdown','stdlibinspect':'stdlib inspect','fencetilde':'fence tilde','audittrước/sau':'audit trước/sau','metadata Phật Ý':'metadata Phật Ý','vàmetadata':'và metadata','đãđổi':'đã đổi','đãbị':'đã bị','filechưa':'file chưa','đượcghi':'được ghi','đổi fencetilde':'đổi fence tilde','quyếtID':'quyết ID','buộcAdmin':'buộc Admin','Khôngcó':'Không có','Agentkế':'Agent kế','DILA không':'DILA không','mộtbản':'một bản','ThiếuID/quan hệ':'Thiếu ID/quan hệ',
 'DùngGraph':'Dùng Graph','lỗiPathWindows':'lỗi Path trên Windows','Graph.parse(data=UTF8),hashbytes':'Graph.parse(data=UTF8), hash bytes','TênViệt':'Tên Việt','ký tựÐ':'ký tự Ð','kýtự':'ký tự','tạo lại':'tạo lại','nguồn khi có':'nguồn khi có','bổsung':'bổ sung','học thuật':'học thuật','thao tác':'thao tác','Admin mở8':'Admin mở 8','đọc chứngcứ':'đọc chứng cứ','cảdocs':'cả docs','Cóguard':'Có guard','cóguard':'có guard','Docbackup':'Doc backup','Docsbackupở':'Docs backup ở','SourceXML':'Source XML','TừDai':'Từ Dai','thìdừng':'thì dừng','dựaphái':'dựa phái',
 'không xoá folder':'không xoá folder','sửa mới trước':'sửa mới trước','sectiont215-review':'section t215-review','Dashboardchính':'Dashboard chính','trước/sau,XML/API':'trước/sau, XML/API','taskT215':'task T215','T215-closeout-20261003:change-plan':'T215-closeout-20261003: change-plan','T215-closeout-20261003:7':'T215-closeout-20261003: 7',
 'DILA A003623馬':'DILA A003623 馬','A038890道':'A038890 道','A004981南':'A004981 南','A004982風':'A004982 風','A003636thầy':'A003636 thầy','A019919thầy':'A019919 thầy','A001897;Thạch':'A001897; Thạch','A004981,trò':'A004981, trò','ởdila':'ở dila','ởdata':'ở data','ởCDN':'ở CDN','X1667_p0560a03 choĐại':'X1667_p0560a03 cho Đại','DẫnX1667':'Dẫn X1667','JSrawtemplate':'JS raw template','đượcghi,đổi':'được ghi, đổi','filecờ':'file cờ','khôngtìm':'không tìm','đãđổi':'đã đổi','Phước Châu37':'Phước Châu 37','DILA A004982風':'DILA A004982 風'
}
paths=[D/'docs/reports/T215-closeout-20261003/README.md',D/'docs/Handoff-2026-10-03-T215-closeout.md',D/'docs/sessions/2026-10-03-T215-closeout.md',D/'agents/SESSION.md',D/'tasks/T215-dila-ttl-evidence-and-self-edges.md',D/'docs/plans/T215-dila-ttl-evidence-plan.md',D/'docs/tasktodo.md',D/'docs/ROLLBACK.md',D/'dashboard/dashboard_process.html']
for p in paths:
 old=p.read_text(encoding='utf-8-sig');text=old
 # Chỉ chỉnh phần bàn giao phiên này trên các file dùng chung.
 marker='## T215 — closeout có chứng cứ, 2026-10-03'
 if p.name in ('SESSION.md','T215-dila-ttl-evidence-and-self-edges.md','T215-dila-ttl-evidence-plan.md'):
  prefix,text=old.split(marker,1);prefix+=marker
 elif p.name=='tasktodo.md':
  lines=old.splitlines();i=next(i for i,l in enumerate(lines) if '[2026-10-03 · T215 closeout]' in l);prefix=None;text=lines[i]
 elif p.name=='ROLLBACK.md':prefix,text=old.split('## T215 — closeout 2026-10-03',1);prefix+='## T215 — closeout 2026-10-03'
 elif p.name=='dashboard_process.html':
  rx=re.compile(r'<section id="t215-review"[\s\S]*?</section>');m=rx.search(old);prefix=None;text=m[0]
 else:prefix=''
 for bad,good in sorted(replacements.items(),key=lambda kv:-len(kv[0])):text=text.replace(bad,good)
 text=re.sub(r'(?<![A-Za-z0-9_])(\d+)(?=(?:file|cặp|nguồn|dữ|đề|assert|ký|API|self|hồ|kiểm|lần|runtime|pending|DONE|kýtự))',r'\1 ',text)
 text=text.replace('audit1037','audit 1037').replace('Audit1037','Audit 1037').replace('mỗi1037file','mỗi file trong 1.037 file').replace('2/2PASS','2/2 PASS').replace('2DONE','2 DONE').replace('8filename','8 filename')
 if p.name=='tasktodo.md':lines[i]=text;new='\n'.join(lines)+'\n'
 elif p.name=='dashboard_process.html':new=old[:m.start()]+text+old[m.end():]
 else:new=prefix+text
 if p.name=='T215-dila-ttl-evidence-and-self-edges.md':new=new.replace('updated: 2026-10-02','updated: 2026-10-03',1)
 assert p.read_text(encoding='utf-8-sig')==old,'File đang đổi';p.write_text(new,encoding='utf-8',newline='\n')
print('Bàn giao T215 đã chuẩn hóa khoảng trắng và giữ nguyên phần task khác.')
