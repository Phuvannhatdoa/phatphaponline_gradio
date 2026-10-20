---
task: tasks/T226-academic-ttl-profile-v2.md
updated: 2026-10-04
---

# T226 — Phật Tổ Đạo Ảnh: hồ sơ TTL học thuật và roadmap

## 1. Kết luận thiết kế

Phật Tổ Đạo Ảnh cần một **application profile về nhân vật có chứng cứ**, không chỉ một mẫu tiểu sử dài. Đây là mô hình của dự án dựa trên các chuẩn công khai, **chưa phải một “chuẩn Phật giáo quốc tế” đã được cộng đồng phê chuẩn**.

DILA ID là mã của hồ sơ authority nhân vật trong phạm vi DILA. Nó không chứng minh tất cả nội dung của một TTL Việt dịch đều thuộc đúng người, không xác nhận mọi quan hệ là truyền pháp và không xác nhận số đời. Tên trùng không đủ để ghép ID; một người có nhiều biệt danh cũng không được tự tách thành nhiều người.

Dự án có URI nhân vật riêng để bảo tồn công trình Việt dịch và nhận định học thuật. DILA tiếp tục là authority chính cho phạm vi Hán truyền; CBETA là nguồn văn bản và định vị; Marcus là nguồn dữ liệu mạng với loại cạnh và phương pháp của bộ dữ liệu; các authority khác có vai trò theo phạm vi riêng. Không xây một thứ tự “nguồn nào luôn đúng hơn” cho mọi trường.

## 2. Vấn đề của TTL cũ và cách xử lý

| Vấn đề | Hệ quả | Thiết kế v2 |
|---|---|---|
| URI dạng `<ex:monk/...>`, class `<bkg:Monk>` | Đây là IRI dùng scheme ex:/bkg:, không phải QName tự mở rộng bởi prefix; khó liên thông HTTP | URI HTTP riêng, namespace pth: khai báo đúng; giữ nguyên URI/text cũ trong hồ sơ migration |
| P1_is_identified_by trỏ lại chính người | Không mô tả một identifier assignment có nguồn | ID và mapping thành assertion riêng; lộ trình tách IdentifierAssignment có scheme, lịch sử và hiệu lực |
| Quan hệ bkg:hasTeacher/hasDisciple | Không tách truyền pháp, thụ giới, tham học, đồng môn | Thầy → trò theo loại; loại chung không tự nâng thành truyền pháp; giữ original_predicate |
| Số đời chỉ là một số | Có thể lẫn gốc đếm Thiền Tông, Lâm Tế, nhánh và hệ gia phả | Số + hệ đếm + chứng cứ độc lập + lập luận + người/ngày duyệt; bỏ cộng 37 và thầy + 1 trong form |
| Các trường nhiều nguồn nằm trong ghi chú | Không biết nguồn nào xác nhận trường nào | SourceRecord + Assertion + evidence theo từng trường |
| Trang hồ sơ DILA dùng owl:sameAs | Đồng nhất trang tài liệu với con người | Record URL là foaf:page/authorityRecord; sameAs chỉ dùng URI nhân vật được xác minh |
| Thiếu dữ liệu bị điền Nam / không khai tổ | Biến thiếu thông tin thành kết luận | Cho phép chưa xác định; không tự tạo false/Male |
| Regex import và nội dung HTML | Có thể mất Unicode, xuống dòng, trích dẫn và triple lạ | Parser RDF; roundtrip; originalTurtle và SHA256; graph/payload không khớp thì chặn |

**Biên tập tên hiển thị** được xuất dưới pth:displayName. Tên lịch sử rdfs:label/biệt danh được giữ trong assertion; chỉ assertion accepted mới chiếu thành triple trực tiếp. Một tên Việt dùng điều hướng không được coi là DILA đã chứng nhận bản dịch.

## 3. Các lớp dữ liệu

| Lớp | Nội dung bắt buộc / mục đích | v2.0 hiện thực |
|---|---|---|
| Person | URI ổn định, loại nhân vật, tên điều hướng | Có; loại điều hướng riêng. rdf:type crm:E21_Person/Monastic là assertion có nguồn, chỉ projected khi accepted; chưa tuân thủ toàn bộ CIDOC CRM |
| Identifier / mapping | Scheme, ID, record URL, version, trạng thái, chứng cứ | DILA và externalIdentifier qua assertions; chưa tự tạo sameAs |
| SourceRecord | Code, record ID, citation/URL, version, ngày truy xuất, SHA, nguyên bản, quyền dùng | Có; sourceSnapshot giữ XML/JSON record đầy đủ |
| Assertion | Subject/predicate/object, language/datatype, evidence, trạng thái, lập luận, derivation | Có; RDF 1.1 reification, không phụ thuộc RDF-star |
| Review | Người/ngày duyệt, kết luận | Có metadata trên assertion; Agent/ORCID/Review activity riêng là bước tiếp |
| CountingScheme | Gốc, đời đầu, phạm vi, quy ước và edition | v2.0 là mô tả có tên; resource có URI/version là bước tiếp |
| Dataset / dossier | Profile version, chủ thể, nguồn gốc và access level | Có DCAT Dataset/PROV; catalog/distribution/checksum release là bước tiếp |
| Event / Place / Work / Organization | Sinh–mất, trụ trì, thụ giới, chùa, tác phẩm, vai trò theo thời gian | Chưa chuẩn hóa đầy đủ; lưu nguyên văn và ID/source; không đoán ngày hoặc ghép địa danh |

Các nhận định dùng trạng thái draft / source_asserted / accepted / disputed / rejected / legacy_unverified. “Nguồn ghi nhận” có nghĩa nguồn nói điều đó; không có nghĩa ban biên tập đã xác nhận.

## 4. Quy tắc học thuật không được nới

1. **Định danh:** kiểm đúng tên/biệt danh Hán trên chính record DILA; không dùng tên Việt, filename, tên hai chữ cuối hoặc vị thầy để đoán ID. API duyệt DILA hiện kiểm exact alias trong artifact local và record SHA/version. Khớp tên vẫn chưa loại hết khả năng nhầm người cùng tên: review còn phải kiểm triều đại, địa điểm, hành trạng và các nguồn dẫn.
2. **Quan hệ:** giữ nguyên loại cạnh gốc; ghi hướng thầy → trò và bối cảnh. Các cạnh giao tiếp, gặp gỡ, thư từ hay cùng hoạt động không tự biến thành truyền pháp. Cạnh tự nối bị chặn; cycle toàn corpus và mâu thuẫn thời gian phải qua gate trước apply DB.
3. **Số đời:** không có công thức cộng chung. Duyệt cần ≥3 nguồn gốc chứng cứ độc lập, cùng hệ đếm và lập luận về số đang sai/số đề xuất đúng. Ba URL, ba bộ dữ liệu hoặc thầy + hai đồng môn có thể cùng xuất phát từ một gia phả; phải kiểm độc lập thực sự. independence_key chỉ là metadata cho máy kiểm, **không thay thế đánh giá của học giả**.
4. **Không đủ căn cứ:** để trống hoặc lưu tham chiếu legacy_unverified/disputed. Không “làm sạch” bằng cách đoán. Giá trị cũ và mâu thuẫn vẫn có thể được giữ trong dossier có provenance.
5. **Ngày tháng:** giữ nguyên niên hiệu, âm lịch, khoảng ngày, mức chắc chắn và lời dẫn. Không biến khoảng năm thành ngày 1/1 chính xác, không suy năm mất từ tuổi nếu nguồn không cho phép. Quy đổi phải tạo một nhận định dẫn xuất riêng ghi phương pháp/version.
6. **Bản dịch:** giữ Hán bản và Việt dịch riêng, language tag rõ; provenance dịch, editor, ngày duyệt và tình trạng AI phải đi cùng bản dịch. Không sửa raw XML/DOCX.
7. **Quyền dùng:** kiểm artifact cụ thể, không lấy giấy phép phần mềm làm giấy phép văn bản/ảnh hoặc dữ liệu. Export nội bộ không đồng nghĩa được phát hành quốc tế. Gate public hiện yêu cầu registry duyệt quyền tái phân phối và license URL/version trùng nguồn khai báo; artifact-level approval/compatibility còn thuộc P1/P5.

## 5. Nguồn đã đối chiếu

- [DILA Authority download](https://authority.dila.edu.tw/docs/open_content/download.php) và [repository chính thức](https://github.com/DILA-edu/Authority-Databases): web đã có release 2026-10; artifact đang dùng trong T226 là XML Person **2026-09** local. Header XML ghi CC BY-SA 3.0 Unported; SHA record được lưu. Không giả metadata source_version=2026.03 trong DB là bản XML này. Cần đăng ký artifact/version/license riêng trước release.
- [CBETA XML P5 chính thức](https://github.com/cbeta-org/xml-p5): lưu sigla, collection T/X/... đúng edition, quyển, trang/cột/dòng và XML ID; đoạn văn phải có nguyên văn và định vị kiểm lại được. Repository URL không đủ làm quyền phát hành mọi văn bản/bản dịch.
- [Marcus ChineseBuddhism_SNA](https://github.com/mbingenheimer/ChineseBuddhism_SNA): đây là dữ liệu mạng, có phương pháp và loại cạnh riêng; có sử dụng authority DILA. Không đếm Marcus và DILA là hai chứng cứ độc lập khi cùng nguồn gốc. README có thông tin giấy phép ở phạm vi dataset và phạm vi work khác nhau; phải khóa đúng artifact, không tự áp một giấy phép toàn bộ.
- [RDF 1.1](https://www.w3.org/TR/rdf11-primer/), [PROV-O](https://www.w3.org/TR/prov-o/), [SHACL](https://www.w3.org/TR/shacl/), [DCAT 3](https://www.w3.org/TR/vocab-dcat-3/), [CIDOC CRM 7.1.3](https://cidoc-crm.org/html/cidoc_crm_v7.1.3.html): nền tảng graph, provenance, kiểm cấu trúc, catalog và mô hình di sản; application profile phải nêu rõ phần nào đã áp dụng.
- [Web Annotation](https://www.w3.org/TR/annotation-model/): bước tiếp dùng quote/position/XPath selector khóa đoạn chứng cứ. [TEI att.datable](https://www.tei-c.org/Vault/P5/4.10.1/doc/tei-p5-doc/en/html/ref-att.datable.w3c.html): phân biệt ngày xác định, khoảng và giới hạn ngày. [FAIR](https://www.go-fair.org/fair-principles/fairification-process/): cần định danh, metadata, khả năng truy xuất và provenance; không chỉ một file TTL.

Kiểm DB read-only ngày 2026-10-03: **14 data_sources, 14 source_authority, 10 dataset_sources**; docs/trusted-sources.md cũ ghi20. Chưa xác minh danh mục25 Admin nhắc. Tất cả14 row data_sources hiện license_verified=0; không sửa tự động để mở export. Kiến trúc không hard-code số lượng nguồn; catalog25 phải được đối chiếu riêng.

## 6. Những gì T226 đã xây dựng

- Form monk_ttl_add thay bằng form v2: trường tuỳ chọn, chưa xác định, nạp DILA XML, nạp CBETA mentions và Marcus crosswalk/node/edges đã index (snapshot giữ loại cạnh gốc, mapping chưa tự duyệt), source cards, assertion cards, checkbox chứng cứ, loại/hướng quan hệ, người/ngày duyệt, hệ đếm và lập luận.
- Nút Tạo TTL trên person.html tiếp tục gửi cùng sessionStorage draft. Form mới giữ **toàn bộ snapshot person/dila/vi/bio_zh**, gồm cả key tương lai; nạp DILA cấu trúc từ artifact local riêng. Số đời DB chuyển ở legacy_unverified, không tự duyệt.
- JSON Schema, ontology và SHACL ở ontology/ttl-profile-v2. SHACL thực thi đã kiểm positive/negative; gate tên DILA, quyền registry, roundtrip và cycles bổ sung nằm trong ứng dụng.
- API ttl_v2/schema, from_dila, local_sources, import, render, validate, save. Save cần phiên Admin, chỉ tạo revision content-addressed tại data/ttl_v2/drafts; không đè TTL đang chạy hoặc full-ETL.
- Parser legacy đọc RDF, giữ originalTurtle và record hash, giữ giá trị số đời; không lấy trang HTML làm owl:sameAs. Unknown triples vẫn trong nguyên bản; **chưa tuyên bố mọi triple lạ đã chuẩn hóa thành vocabulary v2**.
- CLI migrate_ttl_profile_v2 chạy từng file, manifest JSONL, hash đầu vào/đầu ra, kiểm roundtrip; default là audit. --stage ghi output mới riêng, chưa có --apply DB.

**Triển khai ngày 2026-10-04:** main 5000 đã nạp Blueprint qua Windows RunAs/UAC. [Form chính trên 8080](http://localhost:8080/daoanh/admin/monk_ttl_add.html) đạt UI 14/14, schema v2.0.0/API lineages/login đều HTTP 200. Save chỉ staging; chưa apply dữ liệu vào DB hoặc TTL active. Lần Access denied trước đó là giới hạn quyền Windows đã được xử lý, không phải auto-review rejection. Bằng chứng ở `T226-ttl-profile-20261003/deployment-verified.json` và `reload-status.json`.

## 7. Roadmap theo thứ tự thực hiện

| Giai đoạn | Công việc cụ thể | Điều kiện hoàn tất |
|---|---|---|
| P0 — chốt profile và triển khai form | Review namespace/domain; cố định version2.0; mô tả semantics từng property; kiểm form và API; nạp lại main server | Schema/shapes/tests đạt; form8080 hoạt động; bản legacy không bị ghi đè; base URI được cam kết bảo tồn |
| P1 — catalog nguồn và pháp lý | Đối chiếu danh mục25 với3 bảng registry; mỗi artifact có release/commit/SHA, provenance gốc, adapter version, license bằng chứng, quyền dịch/chia sẻ; phân vai authority/text/network | Danh mục đầy đủ, không coi code-license là data-license; nguồn chưa rõ ở draft, không mở public |
| P2 — identity và crosswalk | DILA aliases/dynasty/place; mapping Marcus nodeIDs; place/time/work authorities; local người chưa có DILA; merge/split/deprecated ID có review/history | Không gộp theo tên; mỗi mapping có trạng thái/chứng cứ; test đồng tên khác đời; URI nội bộ không đổi khi đổi tên hoặc thêm ID |
| P3 — chứng cứ và mô hình chuyên sâu | BibliographicWork/Edition/Passage, quote+selector, chuỗi provenance, URI assertion/source bất biến theo revision hoặc named graph (không union các revision cùng dossier thiếu phân biệt); Person/Event/Place/Role/Work; dịch Hán–Việt có editor/review; CountingScheme resource | Mỗi factaccepted truy ngược đúng đoạn/edition; ngày khoảng/niên hiệu không bị làm giả chính xác; hệ đếm có root/firstNumber/pathScope/version |
| P4 — migration toàn TTL local | Audit → stage từng file → danh sách conflict/quarantine → review → snapshot DB → apply riêng TTL provenance → đối chiếu API/tree → rollback rehearsal | 100% byte/text gốc giữ được; không đổi số đời/ID/quan hệ thiếu căn cứ; không xoá cạnh DILA/Marcus; manifest/hashes/cycles toàn corpus đạt |
| P5 — công bố dùng chung | URI resolver, RDF/JSON-LD negotiation; SPARQL/API read-only; DCAT catalog/distributions; version/release/changelog/checksum; license và attribution; DOI/archive | URI thực sự truy xuất được; tổ chức thứ ba tải, kiểm SHACL, nối ID và dùng factsaccepted mà không cần hiểu code nội bộ |
| P6 — vận hành lâu dài | Theo dõi release nguồn; incremental diff; hàng đợi review; schema migrations có version; audit license; backups/restore; hội đồng biên tập và đóng góp | Nguồn mới không âm thầm ghi đè cũ; changelog giải thích từng thay đổi; split/merge có redirects; chỉ số chất lượng và rollback kiểm định kỳ |

Không cấp ID task mới hàng loạt trong roadmap để tránh trùng/race; khi bắt đầu từng giai đoạn phải kiểm2 tầng theo AGENTS.

## 8. Batch chuyển đổi dự kiến

~~~powershell
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
python -X utf8 scripts/migrate_ttl_profile_v2.py --input data/ttl --output data/ttl_v2/staging/<batch-moi> --stage
~~~

Output phải là thư mục mới, nằm ngoài input. CLI từ chối trùng URI legacy và file lỗi; không tự gộp. Đối chiếu input_sha256 với file hiện tại trước apply vì worktree dùng chung. Không đưa data/ttl_quarantine vào batch active; các hồ sơ chưa xác minh vẫn pending theo T215/T223.

Sau stage phải xây **importer v2 riêng**: parse assertion states, chỉ áp factsaccepted; biographicalNote và Việt dịch là nội dung riêng có provenance; chỉ supersede rows source TTL đúng batch/file; không gọi etl_gen_compute.py tính lại đời cả corpus. Export view legacy cho frontend cũ phải có nhãn provenance và không tạo thêm fact lịch sử.

## 9. Kiểm chất lượng và release

Đo riêng: syntactic-valid %, schema/SHACL-valid %, identity-verified %, relation-verified %, generation-verified %, citation-resolvable %, artifact-license-verified %, translation-reviewed %. Không gọi “100% đúng lịch sử” khi mới parse được Turtle.

Cần bộ gold corpus được học giả duyệt: cùng tên khác triều; temple-prefix/biệt danh; ID gán nhầm; nhiều thầy khác loại; thầy/trò được ghi trong câu nhưng không phải truyền pháp; tuổi/năm/niên hiệu mâu thuẫn; nam/nữ/chưa rõ; local không có DILA; nhiều CountingScheme; CBETA dị bản và Marcus cạnh khác loại.

P5 phải có bên thứ ba thử sử dụng độc lập: không cần source code Python/JSON editor để đọc assertion RDF; tải ontology/shapes/sample; query factsaccepted theo nguồn/version; báo issue có record/selector. RDF.JSON payload là phụ trợ editor, không phải điều kiện duy nhất để tái sử dụng.

## 10. Tiêu chí phát hành học thuật

Không xuất trước khi resolver, catalog nguồn và quyền artifact được chốt. Bản release có README phương pháp, citation, authors/contributors, glossary phạm vi, schema/ontology/shapes version, vocabulary crosswalk, completeness/uncertainty statement, examples, changelog, manifest/checksum và hướng dẫn rollback.

Một hồ sơ “đầy đủ” nghĩa mọi trường có trong nguồn được bảo toàn và truy nguyên được, cùng trạng thái thiếu/chưa rõ; không phải mọi người đều phải có ngày sinh, ngày mất, thầy và số đời. Sự không chắc chắn là dữ liệu cần lưu.


Audit cuối T226:1037 hồ sơ chuyển được,template duy nhất bị chặn. Hai selfhasDisciple thấy ở lượt đầu đã đổi nội dung trong workspace chung; chưa suy ra tính đúng học thuật của bản mới. Xem manifest/hashdiff trong báo cáo. Giai đoạn P2 phải duyệt canonicalPersonURI templates trước owl:sameAs; importer P4 chỉ dùng DILA mapping được duyệt, không lấy dila_id metadata candidate làm mapping thật.
