# Đánh giá logic T202-POST-REVIEW-01 — 2026-10-09

**Kết luận: đúng một phần; chưa đủ căn cứ để gộp/tách/xóa nhân vật.** Đối chiếu báo cáo ngày01/10 với commit của báo cáo và code/DB ngày09/10. Chỉ tạo artifact review; không sửa app, TTL, DB, báo cáo gốc, không stage/commit hoặc gọi LLM.

## 1. Phạm vi và kết quả kiểm tra

Báo cáo gốc: [T202-POST-REVIEW-01](../../Mimo-Flash/T202-POST-REVIEW-01.md), SHA256 `801fd73c408193e6661b0562b54e4fbfff3c6588c53501a634f7f618120a67d4`. Snapshot báo cáo `6efc89d`; HEAD hiện tại `c5e3afba45a262afec0e104afbe1f48e60b99ce4`.

Đọc `canonical_lock.py`, `vnpa_lookup.py`, các đoạn liên quan trong `app.py`, ba file test; TTL `TS-Hoang-Long-Tri-Minh.ttl`; `docs/tasktodo.md`, task T223. Code cũ kiểm bằng git show từ root visjs-app. DB thật dùng URI mode=ro trong một transaction đọc nhất quán: [script](audit_t202_logic.py), [kết quả](db-evidence.json).

T166 unit **18/18**, matrix **23/23**, T200 **25/25**: **66/66 PASS**. Probe bổ sung chỉ dùng DB tạm: [script](probe_fixture_and_validator.py), [kết quả](probe-evidence.json). Chưa chạy full pipeline hoặc kiểm browser; không claim toàn hệ thống PASS.

## 2. Các phần đúng

Đổi join places_dila.dila_id thành places_dila.id đúng schema DB thật. ORDER BY status-rank,id ASC làm các consumer đã nối helper trả kết quả xác định với cùng dữ liệu. P8 OFF tắt phần thêm chỉ dẫn entity và phân tích XML P8. Giữ các nhóm chưa rõ để xét là phù hợp. Những điều này chưa xác minh lịch sử hoặc identity của row được chọn.

## 3. P0 — P8 OFF không ngắt lời gọi LLM gốc

§D dòng187/195 và §H dòng369 kết luận không gửi DILA ra LLM. Nhưng ngay commit6efc89d, app.py19250 gọi `_t73_call_gemini` ngoài `if _p8_active`; hiện tại tương ứng app.py20732. Nhánh dịch mới vẫn có thể gọi ra ngoài khi có cấu hình key. Tên hàm là di sản: cả code cũ và hiện tại gọi **Groq**, không phải Gemini; hiện app.py19250 thực hiện requests.post(GROQ_URL,...). Không đọc/in key hoặc gọi endpoint dịch trong review này.

**Sửa kết luận:** P8 alignment không hoạt động mặc định; luồng dịch LLM gốc vẫn tồn tại. Nếu yêu cầu không gửi ra ngoài, cần outbound gate riêng tại điểm gọi chung và test mock chứng minh không request khi OFF. Không suy ra governance không bị bypass chỉ từ gate P8; kiểm riêng auth/policy/điểm gửi request.

## 4. P0 — A001984 bị loại PLACE

canonical_lock.py920 gán cứng PLACE cho mọi row canonical_decision, kể cả row join people. Lỗi có cả ở snapshot báo cáo. DB thật hôm nay: 靈祐 → A001984 / Quy Sơn Linh Hựu / **PLACE / LOCKED**, đồng thời có **PERSON / Linh Hữu / CANDIDATE**. Resolver gom theo (source_form,entity_type), nên khác loại còn làm hai nguồn không được xét chung. Claim LOCKED=True bỏ sót loại thực thể.

**Đề xuất:** xác định loại từ bảng/cột thực thể đáng tin; PERSON khi ID tồn tại trong people, PLACE khi tồn tại trong places, chưa rõ thì review. Test phải assert ID+type+value+source và các entry/claims khác. Sau sửa loại có thể lộ CONFLICT tên ngắn/tên đầy đủ; giải quyết alias bằng chứng, không xóa nguồn chỉ để ép PASS.

## 5. P0 — is_valid_vi chỉ kiểm non-ASCII

§B dòng72 kết luận bộ lọc chặn đúng corrupt data, nhưng canonical_lock.py134 chỉ yêu cầu chuỗi không toàn ASCII. Hai chuỗi ASCII bị loại không chứng minh chặn được mọi tên hỏng. Probe trên DB tạm, schema đã sửa và admin-approved cho kết quả:

| Giá trị thử | Validator | Builder |
|---|---|---|
| Th? S?t H?i | False | Bỏ ở nguồn này |
| Thập S?t Hải | True | LOCKED |
| 法雅 | True | LOCKED trong trường Việt |
| ThÃ¡p | True | LOCKED |
| An | False | UNKNOWN_REVIEW khi không có nguồn khác |

Các tên LOCKED trên là **dữ liệu tổng hợp**, không phải row vừa phát hiện trong DB thật.

**Đề xuất:** tách chất lượng chuỗi khỏi identity; phát hiện ký tự thay thế/dấu hỏi mất mã/mẫu mojibake/chữ Hán trong trường Việt; chưa chắc thì review, không tự phục hồi ký tự mất. Cho phép tên Latin không dấu hợp lệ. Bị loại ở một nguồn không đủ kết luận toàn hệ thống không lock; kiểm builder với mọi nguồn và đúng source form.

## 6. P1 — PASS chưa chứng minh nguồn canonical chạy đúng

Fixture tests/test_t166_canonical_lock.py36–38 khai báo places_dila.dila_id, còn code dùng pd.id. Unit vẫn18/18PASS nhưng có warning no such column:pd.id; probe ghi được lỗi qua safe_errors(). Fixture lỗi cũng tồn tại tại commit báo cáo. Các test có thể qua nguồn khác, không chứng minh nguồn canonical_decision.

**Đề xuất:** fixture khớp schema thật, assert safe_errors()==[] ở ca bình thường. Ca cố ý thiếu bảng phải assert đúng lỗi mong đợi. Thêm regressions PERSON/PLACE, các tên hỏng, tên ASCII và nhánh P8OFF. Sau triển khai sửa code mới chạy pipeline đầy đủ trước review Admin.

## 7. P1 — CLEAR_ALIAS và 18/33 chưa đủ curation

§F xếp A008471 CLEAR_ALIAS vì hai dòng cùng tên Hoàng Đình Kiên. DB hiện vẫn có hoang_dinh_kien và hoang_long_tri_minh cùng tên đó, nhưng TTL thứ hai có subject hoang_long_tri_minh, nhãn **Hoàng Long Trí Minh**, tiểu sử **Thiền sư Trí Minh ở Hoàng Long**. Đây là lệch nguồn/DB cần kiểm, không phải bằng chứng alias. Không suy ID mới từ filename hoặc slug.

[DILA chính thức A008471](https://authority.dila.edu.tw/person/search.php?aid=A008471) ghi 黃庭堅, không phải tăng sĩ. Điều này xác minh chủ thể của ID; chưa xác minh ID thay thế cho Trí Minh. [Chứng cứ nguồn](official-source-evidence.json).

§E dòng265 quy hai người chung ID trong DILA từ hai row VNPA local. Chỉ chứng minh được **local DB gán cùng ID**; cần XML/TTL/crosswalk/ETL trước quy lỗi DILA. Khác tiền tố chùa không đủ chứng minh khác người. A047679 chưa truy cập được trang chính thức qua web tool, nên không chốt identity.

**Đề xuất:** hồ sơ mỗi nhóm gồm subject local, tên/alias Hán gốc, XML version/hash, tiểu sử/niên đại/quan hệ có nguồn, mapping ETL và lý do quyết định. Tách alias đã xác minh, trùng dòng cùng người, mapping sai đã xác minh và chưa rõ. Giữ alias có chứng cứ và bỏ qua trường chưa xác nhận. Không thêm UNIQUE(dila_id) lên bảng alias nhiều dòng; một tên ưu tiên cần bảng quyết định riêng theo ID/type.

18/33 là mức phân nhóm sơ bộ để mở hồ sơ, chưa đủ căn cứ cho mọi quyết định gộp/tách/xóa. Status-rank là fallback hiển thị Admin đã chọn, không phải điểm chất lượng sử liệu.

## 8. P1 — ID rỗng không mặc nhiên orphan hoặc vô ảnh hưởng

Hai helper lookup_by_dila/map_dila_to_name bỏ ID rỗng, đúng. Nhưng app.py11965–11978, endpoint /daoanh/api/admin/search_all tìm va.name_vi trực tiếp, không lọc ID rỗng. DB có Minh Hải Pháp Bảo với dila_id rỗng, có thể được query này trả về. Nhiều row rỗng còn bị gom theo cùng ID trong seen; NULL có thể gây lỗi rid.startswith nếu row đi vào render. Đây là phân tích code và truy vấn RO, chưa kiểm endpoint qua browser.

**Đề xuất:** coi là thực thể local chưa ánh xạ; điều hướng bằng ID local ổn định, phân biệt unmapped/distinct-person, bảo tồn dữ liệu. Không gán DILA ID chỉ để hết rỗng. Đổi empty thành NULL phải kiểm consumer/serializer trước; nhân vật Việt Nam không có DILA vẫn cần giữ.

## 9. P2 — Số liệu và kế hoạch kế thừa

- git rev-list --count a41eb7a..6efc89d trả **3**, không phải +2.
- §E dòng276 viết rank3<rank1 sai; pending thắng vì rank1 nhỏ hơn.
- Báo cáo01/10:1506row,33nhóm ID thực,211IDrỗng. Snapshot09/10: **1507row,31nhóm/65row,210empty+1NULL**; nhóm chưa ánh xạ đều pending.
- Hai row canonical đã đổi: PL...314=Thế Sát Hải/admin-approved/verified/LOCKED; PL...001=Khoát Tạt Đa Quốc/auto-transliterate/needs_review/CANDIDATE. Đây là kiểm giá trị/hành vi DB, chưa xác minh lại lịch sử địa danh.
- Đã có **T223** kế thừa T200; task đó ghi29nhóm ngày03/10 cũng là số lịch sử. Không cấp lại T202/T203 như báo cáo đề nghị.

## 10. Thứ tự xử lý đề xuất

1. Ghi các kết luận bị bác bỏ và link review này, giữ chứng cứ lịch sử.
2. Sửa type/validator/fixture/schema-error checks. Rà consumer chưa dùng SSOT; namevimap hiện còn MAX(name_vi) và MAX(status) độc lập, có thể lấy từ hai row khác nhau.
3. Refresh T223 với snapshot hiện tại; kiểm nguồn và URI trước, rồi nhãn, rồi mapping. Phân loại tự động không là phán quyết nhân thân.
4. Tách display preference khỏi identity alignment; fallback ghi rõ, nhóm chưa rõ giữ review/conflict, không nâng verified.
5. Chỉ sau mapping có chứng cứ mới dry-run sửa từng row, backup/snapshot, guard giá trị cũ, transaction, rollback và kiểm API. Không chạy importer toàn bộ.
6. Chế độ no-external cần outbound gate riêng; kiểm bằng mock, không gọi API trả phí.

Scope **data-only, không sửa code** của §H chưa đủ: lỗi type/validator/fixture/consumer cần code; dữ liệu cần hồ sơ mapping riêng. **Review xong; các sửa chữa chỉ là đề xuất, chưa triển khai.**

## 11. Lệnh đã dùng / chạy lại

Từ daoanh, dùng python -B -X utf8 cho audit_t202_logic.py, probe_fixture_and_validator.py, tests/test_t166_canonical_lock.py, tests/test_t166_matrix.py và tests/test_t200_vnpa_tiebreak.py. Lần này PYTHONPATH dùng python-deps trong backup T226/T215; PYTHONDONTWRITEBYTECODE=1.

Git từ root visjs-app: git rev-parse HEAD; git rev-list --count a41eb7a..6efc89d; git show 6efc89d:./Dai_Tang_Kinh/daoanh/app.py, canonical_lock.py và tests/test_t166_canonical_lock.py. Định vị code bằng rg, đọc UTF8 bằng Node. Không import app.py, không chạy ETL/migration/dịch/sync DB. Artifacts mới chỉ trong thư mục review, Handoff và session log.


## Current related plan — 2026-10-11

[T357](../../../tasks/T357-vnpa-etl-safety-remediation.md) records the approved production ETL safety remediation formerly labeled T223; the distinct 29-group identity task retains T223. The plan addresses atomicity, fail-closed preflight, rowset/provenance proof and birth/death candidate quarantine. It does not promote inferred identity/lineage/date claims or implement any DB/TTL correction from this review. Historical measurements and errata remain unchanged.
