# -*- coding: utf-8 -*-
"""Lưu T215; snapshot docs và nối đúng trạng thái phiên này."""
import json,re,urllib.request,subprocess
from pathlib import Path
D=Path.cwd()/'daoanh';O=D/'docs/reports/T215-closeout-20261003';B=D/'data/backups/T215-closeout-20261003'
def write(p,text):
 if p.exists():
  old=p.read_bytes();dest=B/'docs'/p.relative_to(D);dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(old)
  assert p.read_bytes()==old,'Tài liệu đổi từ session khác'
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
def append(p,text):
 old=p.read_text(encoding='utf-8-sig') if p.exists() else ''
 if 'T215-closeout-20261003/README.md' not in old:write(p,old.rstrip()+'\n\n'+text+'\n')
report='''# T215 — Closeout có chứng cứ, 2026-10-03

Đã thực hiện các mục có căn cứ và cách ly file gây xung đột. Phần thiếu chứng cứ được bỏ qua; không tuyên bố toàn corpus đã được chứng nhận học thuật.

## Kết quả

| Kiểm tra | Kết quả |
|---|---|
| TTL đang dùng | 1037/1037 RDF hợp lệ, mỗi file một main subject |
| Tự nối / URI trùng / vòng thầy–trò | 0 / 0 / 0 |
| Trước xử lý | 1044 file; 2 rỗng, 1 main unsupported, 1 multiple main, 4 nhóm URI trùng, 2 vòng |
| File cách ly nguyên bytes | 7, có manifest và backup |
| Assertion TTL sai | 142 rejected, mapping_verified=0; giữ lịch sử |
| Assertion mới | 72 thuộc36 cặp có DILA xác nhận; các file có thể cùng xác nhận một cặp |
| Đề xuất remap bỏ qua | 44 source-edge thiếu căn cứ, không suy ID thay thế |
| Mã hóa | 40 ký tự Ð đổi thành Đ trong5 TTL; URI, Hán tự, quan hệ giữ nguyên |
| Số đời | Mọi row đã có giữ nguyên;26 cặp review |
| DB / API / rollback | PASS;5 hồ sơ API +2 kiểm người từng bị gán nhầm |
| Dashboard | 8 filename;2DONE,6pending status trống; mở chứng cứ PASS |
| Raw XML / nguồn quốc tế | Zip và hash toàn bộ assertion không thuộc TTL không đổi |

## Đã xử lý

| File | ID và hành động |
|---|---|
| TS-Phuoc-Chau-Dai-An.ttl | A003636 福州大安; thầy A001897. DB/API PASS. Row mới chép37 tham chiếu TTL, chưa tái chứng nhận số đời. |
| TS-Dai-Ninh-Dao-Khoan.ttl | A020545 大寧道寬; thầy A001439. Giữ45 và URI dao_ninh_dao_khoan; bản TS-Dao-Ninh trùng lưu cách ly. |
| TS-Thach-Cuu.ttl | A019919 石臼; thầy A003623. Đổi provenance DB TS-Linh-Cuu → TS-Thach-Cuu. Không tạo Linh Cưu từ Thạch Cữu. |
| TS-Ma-To-Dao-Nhat.ttl | A003623 馬祖道一, không phải A038890 道一/みちかず. Bổ sung owl:sameAs; rút TTL assertion Nhật Bản. DB đờiNULL giữNULL; TTL35 nguyên. |
| TS-Phong-Huyet-Dien-Chieu.ttl | A004982 風穴延沼, không phải A004981 南院慧顒. Thầy A004981; trò A004983. DB đờiNULL giữNULL; TTL41 nguyên. |
| TS-Phat-Y-Linh-Nhac.ttl | Phục hồi metadata/provenance Phật Ý sau file Trường Viễn ghi đè. Chưa gán DILA ID; row đời72 giữ nguyên. |

[DILA Mã Tổ](https://authority.dila.edu.tw/person/search.php?aid=A003623), [DILA Phong Huyệt](https://authority.dila.edu.tw/person/search.php?aid=A004982), [DILA Phước Châu](https://authority.dila.edu.tw/person/search.php?aid=A003636). Record XML/source/hash có trong [dila-evidence.json](dila-evidence.json).

## Cách ly / chưa xác minh

7 file lưu nguyên tại data/ttl_quarantine/T215-closeout-20261003, backup bytes tại data/backups/T215-closeout-20261003/ttl:

- TS-Dot-Khong-Tri-Ban.ttl: có tên 突空智板 trong X1667; chưa có DILA ID/thầy khóa đúng. Không khẳng định DILA không có ID.
- TS-Tuyet-Giau-Chon-Phac.ttl: chép2 block Phong Huyệt; chưa chứng minh 雪梪真發 ↔ 雪槱真樸 cùng người.
- TS-Dai-Xa-Nhu-Truong.ttl, TS-Minh-Hoang-Tu-Dung.ttl: admin đã để trống trước lượt này; giữ dossier, không import. Dẫn X1667_p0560a03 cho Đại Xa đã bị bác bỏ.
- TS-Truong-Vien.ttl: chép URI/biography Phật Ý; chưa xác minh Trường Viễn.
- TS-Phuc-Chau-Dai-An.ttl: template rỗng; không suy ID từ filename. Alias DB phuc_chau_dai_an giữ nguyên; API chọn row canonical Phước Châu verified.
- TS-Dao-Ninh-Dao-Khoan.ttl: bản trùng lưu nguyên; dùng bản Đại Ninh canonical.

TS-Di-Phong-Kinh-Ninh.ttl và TS-Linh-Cuu.ttl đã không có trước lượt này; không tái tạo/gán ID suy đoán. 6 hồ sơ URI pending vẫn có filename + chứng cứ, status trống.

[File-decisions.jsonl](file-decisions.jsonl) chứa một dossier cấu trúc/hash/quyết định cho mỗi1037file;783file có cờ không đồng nghĩa sai. Kiểm DILA toàn corpus dùng DB local, mapping legacy có thể sai, chưa xác minh web từngngười. Giữ101P1alias khácsubject và77filename khácslug khi chưa chứng minh lỗi. [Generation-review.json](generation-review.json) có26cặp; không sửa đời thiếu3dữ liệu độc lập/cùng hệ đếm.

## Kiểm thử

[Verification](verification.json), [API](api-verification.json), [Dashboard](dashboard-verification.json) PASS. npm run pipeline đã chạy: các bước trước runtime PASS, runtime bị ERR_NETWORK_ACCESS_DENIED ởCDN dẫn L is not defined. Chạy lại nguyên2runtime test với mạng và output riêng:2/2PASS; không bỏ assertion. Logs: [pipeline](pipeline-utf8.log), [runtime retry](runtime-network-output-utf8.log).

Suite báo không tìm thấy nút Mapping Tên Việt và bỏ qua nhánhclick theo logic hiện có: PASS chứng minh tải trang/API, chưa chứng minh nhánhclick đó. Retry đầu bị Windows khóa test-results/.last-run.json; dùng output riêng, không xoá folder session khác.

## Kiểm tra / rollback

Chạy từ Dai_Tang_Kinh:

~~~powershell
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/verify_closeout.py
node daoanh/docs/reports/T215-closeout-20261003/check_dashboard.cjs
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/apply_closeout.py --revert
~~~

Rollback DB từngrow và TTL từngfile có guard: dữ liệu đã đổi thì dừng; không restore cảDB. Bản cách ly giữ lại để tra cứu. Docs/Dashboard backup riêng ởdata/backups/T215-closeout-20261003/docs; so với sửa mới trước khôi phục. Không apply hai lần hoặc tự chạy publish_closeout.py lại vì sẽ append chứng cứ lặp. Chỉ localDB, chưa deploy server từxa.
'''
write(O/'README.md',report)
entry='''## T215 — closeout có chứng cứ, 2026-10-03

Đã sync Phước Châu, hợp nhất Đại Ninh, sửa provenance Thạch Cữu và ID Mã Tổ/Phong Huyệt, phục hồi Phật Ý. Cách ly7file, sửa40ký tự/5TTL. Audit1037/1037 RDF;0 tự nối/URI trùng/vòng. Giữ nguyên26cặp đời. Rút142 TTL assertion sai, bổ sung72assertion/36cặp;44đề xuất chưa chứng minh bỏ qua. DB/API/rollback/Dashboard PASS. Pipeline đã chạy; runtime retry có mạng2/2PASS (nhánhclick Mapping chưa được suite thực thi).

T215 in_progress ở chứng cứ học thuật:6hồ sơ URI thiếu danh tính giữ statustrống,783filecó cờ và26cặp đời cầnđối chiếu. Không suy ID/đời. [Report và rollback](../docs/reports/T215-closeout-20261003/README.md).
'''
append(D/'tasks/T215-dila-ttl-evidence-and-self-edges.md',entry)
append(D/'docs/plans/T215-dila-ttl-evidence-plan.md',entry.replace('../docs/reports/','../reports/'))
write(D/'docs/sessions/2026-10-03-T215-closeout.md',entry.replace('../docs/reports/','../reports/'))
append(D/'agents/SESSION.md',entry)
p=D/'dashboard/dashboard_process.html';txt=p.read_text(encoding='utf-8-sig');rx=re.compile(r'<section id="t215-review"[\s\S]*?</section>');assert len(rx.findall(txt))==1
section='<section id="t215-review" style="margin:16px 24px;padding:16px;border:1px solid #d97706;border-radius:12px;background:#0f172a;color:#e2e8f0"><strong>T215 — 9 hồ sơ đã đồng bộ · Closeout 2026-10-03</strong><p>1037/1037 TTL đang dùng RDF hợp lệ;0 tự nối,0 vòng thầy–trò,0 URI trùng. Đã sync Phước Châu, hợp nhất Đại Ninh, sửa provenance Thạch Cữu và ID Mã Tổ/Phong Huyệt. 7file lưu cách ly;26cặp đời giữ nguyên.</p><p>DB/API/rollback/Dashboard PASS. Cờ chưa xác minh bỏ qua; T215 học thuật vẫn in_progress.</p><a href="/daoanh/dashboard/t215-self-edges.html" style="color:#fbbf24">9 hồ sơ →</a> · <a href="/daoanh/dashboard/t215-other-ttl-bugs.html" style="color:#fbbf24">Toàn corpus và hồ sơ chờ →</a> · <a href="/daoanh/dashboard/t215-eight-uri.html" style="color:#fbbf24">8 URI TTL →</a> · <a href="/daoanh/docs/reports/T215-closeout-20261003/README.md" style="color:#fbbf24">Báo cáo closeout →</a></section>'
write(p,rx.sub(lambda m:section,txt))
p=D/'docs/tasktodo.md';txt=p.read_text(encoding='utf-8-sig')
if 'T215-closeout-20261003/README.md' not in txt:
 lines=txt.splitlines();lines[1:1]=['','> **[2026-10-03 · T215 closeout] in_progress:** Đã xử lý các mục có chứng cứ;7file cách ly, audit1037/1037,0self/URItrùng/vòng,26cặp đời giữnguyên;5API+2kiểm người bị gánnhầm/rollback PASS. 142TTLassertion rejected,72assertion/36cặp bổsung;44đềxuất bỏqua. Runtime retry với mạng2/2PASS;click Mapping chưa kiểm. 6hồsơURI và783filecờ chờ chứngcứ. [Report, Dashboard và rollback](reports/T215-closeout-20261003/README.md).',''];write(p,'\n'.join(lines)+'\n')
head=subprocess.run(['git','rev-parse','HEAD'],cwd=D.parents[1],capture_output=True,text=True).stdout.strip()
handoff='''# Handoff-2026-10-03-T215-closeout

## 1. Đọc nhanh

| Mục | Trạng thái |
|---|---|
| Task | T215; thao tác có chứng cứ xong, học thuật in_progress |
| HEAD lúc bàn giao | HEAD_VALUE; session này khôngcommit/stage |
| Preflight / DB / TTL / rollback | PASS, verification.json/sync-report.json |
| API / Dashboard | 5+2API PASS;8filename/2DONE/6pending đúng |
| Pipeline | Đã chạy; runtime mạng chặn, retry có mạng2/2PASS;click Mapping chưa kiểm |

## 2. Đọc trong 2 phút

Đã sync Phước Châu, hợp nhất Đại Ninh, sửa provenance Thạch Cữu/ID Mã Tổ/Phong Huyệt vàmetadata Phật Ý. Audit1037/1037;0self/URItrùng/vòng. Admin mở8URI Dashboard, đọc chứngcứ pending, bổsung nguồn khi có; không phải sửa code. LocalDB, chưa deploy.

## 3. Vấn đề, sửa và bằng chứng

Mã Tổ A038890道一/みちかず sai;DILA A003623馬祖道一 đúng, thầyA004015. Phong Huyệt A004981南院慧顒 sai;DILA A004982風穴延沼 đúng, thầyA004981,tròA004983. Phước ChâuA003636thầyA001897;ThạchCữuA019919thầyA003623. XML/hash/sourceURL ởdila-evidence.json. Rút142assertionTTL, thêm72assertion/36cặp,44đềxuất bỏqua. 40kýtựÐ→Đ; sốđời rowcũ khôngđổi. [Report](reports/T215-closeout-20261003/README.md).

## 4. Cảnh báo bắt buộc

Worktree chung/HEAD diđộng: không gitadd cảdocs/tasks. TTL khônggittrack: backupbytes/manifest bắtbuộc. Khôngrestore cảDB hoặcfullETL bypassguard. RawXML/assertionquốctế bấtbiến. Khôngsuy đời thầy+1, cần3dữliệu độc lập/cùng hệđếm. Khôngimport lại filecáchly chưa khóa danh tính.

## 5. Hoàn tác

~~~powershell
# cwd: Dai_Tang_Kinh
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/apply_closeout.py --revert
~~~

| Phần | Mất dữ liệu? |
|---|---|
| DB | Restore từngrow cóguard, khôngrestore cảDB |
| TTL | Restore bytes từngfile, bảncáchly giữđối chiếu |
| Docs/Dashboard | Backup data/backups/T215-closeout-20261003/docs;so sửa mới trước khôi phục |

## 6. File tạo/sửa

Report T215-closeout-20261003: plan,prepare/apply/revert/verify,audittrước/sau,XML/API,1037dossiers/26cặpđời/logs. Backup T215-closeout-20261003:change-plan,before/afterrows,TTLbytes,docs. Quarantine T215-closeout-20261003:7file/manifest. Dashboard:t215-eight-uri(.html/-cases.json),t215-other-ttl-bugs.html,t215-closeout-summary.json vàsectiont215-review củaDashboardchính. Docs:tasktodo,taskT215,plan,session,Handoff,ROLLBACK.

## 7. Sai lầm đã sửa / bài học

Script tạm inspect.py che stdlibinspect;đãđổi inspection_legacy.py. Runtime retry đầu khôngunlink logWindows;outputriêng tránhxoá folderngười khác. JSrawtemplate chứa backtickMarkdown gây lỗi parser;filechưađượcghi,đổi fencetilde rồi tạo lại. DùngGraph.parse(data=UTF8),hashbytes để tránh lỗiPathWindows. ThiếuID/quan hệ trong mộtbảnDILA không chứngminh khôngtồn tại. DẫnX1667_p0560a03 choĐạiXa đãbịbácbỏ.

## 8. Chưa xong, ưu tiên

1. 6pendingURI:DiPhong,TríBản,ĐạiXa,MinhHoằng,TuyếtGiàu,LinhCưu;giữdossier,khônggánID suyđoán.
2. 783fileflag và44đềxuất thiếucăn cứ;chưaxácminhweb từngngười,flagkhông đồngnghĩa lỗi.
3. 26cặpđời cần3nguồn/cùnghệđếm. DB MãTổ/PhongHuyệt đờiNULL giữNULL,TTL35/41 nguyên;rowmớiPhướcChâu37chỉthamchiếu.
4. Runtime suite khôngtìmthấyMappingTênViệt nên chưakiểmclick;khôngsửa testđểlàmxanh.

Khôngcó câu hỏi buộcAdmin sửa code hoặcquyếtID thiếu dữliệu.

## 9. Kiểm tra nhanh

~~~powershell
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/verify_closeout.py
node daoanh/docs/reports/T215-closeout-20261003/check_dashboard.cjs
~~~

Guardfail:đọc sửa mới,khôngép snapshotcũ. Xemlogspipeline/runtime retry trongreport.

## 10. Cho agent kế tiếp

Đọc change-plan,sync-report,verification,dossiers trước sửa. Khôngapply2lần hoặcpublish lại(chứngcứappendlặp). DILAcanonical;TTLViệtthamchiếu. Sửa mới cầnsource/old-value/hashguard/backup/API/rollback. Memory37700được thử cuốiphiên;nếu khôngchạy,đọc memory-save.json/tasktodo. Khôngcommit/stagephiênnày.
'''.replace('HEAD_VALUE',head)
write(D/'docs/Handoff-2026-10-03-T215-closeout.md',handoff)
append(D/'docs/ROLLBACK.md','## T215 — closeout 2026-10-03\n\n[Report](reports/T215-closeout-20261003/README.md). TừDai_Tang_Kinh: python -X utf8 daoanh/docs/reports/T215-closeout-20261003/apply_closeout.py --revert. Guard row/hash fail thìdừng;khôngrestore cảDB/importcáchly. Docsbackupởdata/backups/T215-closeout-20261003/docs.')
payload={'contentSessionId':'daoanh-master','tool_name':'tasktodo','tool_input':{},'tool_response':json.dumps({'current_task':'T215-closeout','status':'in_progress','next_task':'T215-unconfirmed-evidence'}),'cwd':'/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh'}
try:
 req=urllib.request.Request('http://127.0.0.1:37700/api/sessions/observations',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'});resp=urllib.request.urlopen(req,timeout=3);m={'saved':True,'status':resp.status}
except Exception as e:m={'saved':False,'reason':str(e),'fallback':'docs/tasktodo.md, agents/SESSION.md, Handoff-2026-10-03-T215-closeout.md'}
write(O/'memory-save.json',json.dumps(m,ensure_ascii=False,indent=2));print('DOCS_HANDOFF_SESSION_UPDATED; MEMORY='+str(m['saved']))
