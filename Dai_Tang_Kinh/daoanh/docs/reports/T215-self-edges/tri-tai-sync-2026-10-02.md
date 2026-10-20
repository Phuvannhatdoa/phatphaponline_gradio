# T215 — Case7 Thụy Nham Trí Tài (2026-10-02)

## Xác minh

Nguồn [gói DILA2026-09 chính thức](https://authority.dila.edu.tw/downloads/authority_person.2026-09.zip). Lưu archivehash + hairecord trích stream trong data/backups/T215-tri-tai-sync-20261002/dila-evidence.json. Không nạp toàn XML/RAM. A026976 alias瑞巖智才, teacherA013875. A013875 alias石門守進, studentA026976, teacherA010933. ĐịađiểmMinhChâu/瑞巖 trong dẫn chứng khớp tiểu sử Việt. XML hai chiềucùngnguồn khôngtínhhai chứngcứđộc lập vềsố đời; giữ44/43 theoTTL, khôngđổi số.

## Kết quả

TTLTríTài doAdminđãđổihasTeacher thach_mon_thu_tan đúng; không sửađè. Sửa2 URI trong TTLThủTấn: subject rỗng→thach_mon_thu_tan; deathEvent→thach_mon_thu_tan_deathEvent. Đồngbộmetadata2person, teacher local/DILAedgeTTLđúng. RejectTTL58284 DiệpHuyện→TríTài, giữself58285rejected. ThêmassertionTTLThủTấn→TríTài vàDiệpHuyện→ThủTấn; DILA/Marcus giữ nguyênhash.

Clearedprocessed people[A026976].birth_year1556/death_year693: khớpsốkinh1556/sốtrang693trongcitation, XML2026-09khôngcóbirth/death. Khôngđặt nămthaythế; rawXMLbấtbiến. API trảnull dates.

## Kiểm chứng

RDF2PASS; DB_SYNC_PASS; API200name/Hán/gen/bio/teacherđúng2person; self0; rollbackinmemoryPASS. Snapshot/scriptguard/data/backups/T215-tri-tai-sync-20261002. Chi tiếtAPI api-check.json. Pipelineđangchạy, cập nhật kếtquảcuối.

## Revert

Từdaoanh: `python -X utf8 data/backups/T215-tri-tai-sync-20261002/sync_case.py --revert`. GuardkhóaafterrowvàTTL, dừngnếuđãđổi sauapply. Khôiphụcmetadata/relations/assertions/consensus/datefields vàTTLthầy; giữTTLTríTàiAdmin đãsửa.


### Kiểm tra cuối phiên
RDF2/DB/API/rollbackPASS; DBsnapshotafter vẫnkhớp saupipeline. Dashboardcase7liveconfirmed/header9PASS. Cú phápHTML/JS5pagePASS. Pipeline lầnđầu dừng T17867/68 vì readonlySQLite khiimport app; standaloneappimportPASS, chạy lại đúng T178 đạt69/69PASS (test được phiênkhác cập nhật). Không sửa app/test để épPASS. Không tuyên bốfullpipeline exit0 vì đãdừng trướcstage sauT178. Logpipeline.log/import-check.log/t178-retry.log trongbackupdir; PowerShellUTF16LE. Sessionmemory37700khôngkết nối, tasktodo + localHandoffđã lưu.
