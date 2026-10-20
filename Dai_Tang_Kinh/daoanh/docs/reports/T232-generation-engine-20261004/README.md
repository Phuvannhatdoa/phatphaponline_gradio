---
task: tasks/T232-evidence-based-generation-engine.md
---
# T232 — Engine số đời đa hệ có chứng cứ

**Engine/API/UI/TTL đã triển khai; các mốc hiện là dự kiến, không là số đời đã duyệt.** Unit20/20 và UI thực PASS; pipeline cuối xem Handoff/log. Không sửa generationOrder TTL hay person_gen_computed.

## Phương pháp

Mỗi hệ có root DILA ID, quy ước0/1, mốc, policy và revision bất biến/hash. Thiền Tông Ca Diếp1/Thích Ca0 và Thích Ca1 là hai hệ riêng: Đạt Ma28/29, Huệ Năng33/34. Nhánh riêng lấy khai tổ1 là **quy ước trong nhánh**, không dùng năm2026 để đoán số đời.

Đường trực tiếp thầy→trò cộng1. Duyệt tổ tiên bằng stack/memo + backpointer, không dùng shortest path/BFS để chọn thầy tiện lợi; nhiều đường khác số → conflict, tự nối/vòng/mốc trái nhau → chặn số, đứt nhánh → incomplete, chưa thuộc nhánh → unreachable. Mốc checkpoint chỉ dùng khi có đường tới root; snapshot giữ toàn đường căn cứ. Giới hạn2500 nodes/10000 edges/128 values và50000 bước witness; resource_limit không trả số chốt một phần.

DILA teacher_of chung chỉ tạo candidate. Cạnh phải tồn tại đúng ID trong XML child.teacher hoặc parent.student, có phiên bản/hash/citation nguồn. Không trộn TTL/Marcus teacher vào policy DILA. Policy reviewed_transmission chỉ dùng cạnh truyền pháp đã có người/ngày duyệt + citation/version. Mốc accepted cần ≥3 gốc chứng cứ độc lập, rationale và reviewer/date; URL mirror cùng tác phẩm không thành ba nguồn. ID/tên Hán khớp record/alias, source drift cần revision mới. Thuật toán không tự xác minh tính độc lập hàn lâm của nguồn — Admin chịu trách nhiệm review chứng cứ.

## Chín hệ đã cài

| Hệ | Root/mốc exact | Trạng thái |
|---|---|---|
| chan_ca_diep_1 | A001361菩提達磨28, A001719惠能33 | source_asserted |
| chan_phat_1 | cùng ID,29/34 theo quy ước khác | source_asserted |
| linji | A003627臨濟義玄1; A004980興化存獎2 | source_asserted |
| linji_yangqi | A004146楊岐方會1 | source_asserted |
| caodong | A009489洞山良价1 | source_asserted |
| yunmen | A003703雲門文偃1 | source_asserted |
| fayan | A000174法眼文益1 | source_asserted |
| guiyang | A001984溈山靈祐1 | source_asserted; chưa thêm co-founder A009491仰山慧寂 |
| linji_chucthanh | chưa khóa ID Minh Hải Pháp Bảo | missing_anchor |

Hai bảng additive generation_v2_scheme_revisions/generation_v2_calculations. Tất cả mốc seed chưa đủ điều kiện accepted; chưa lưu snapshot phép tính vào DB (UI compute chỉ đọc/attach, save_result cần Admin).

## Kết quả thực và giới hạn lịch sử

9 hồ sơ đọc lại,81 kết quả hệ trong `../T233-codex-namevi-20261004/live-generation-results.jsonl` và summary. Huệ Năng33/34 candidate, Lâm Tế1, Hưng Hóa Tồn Tưởng2; bốn khai tổ nhánh riêng1 candidate. **Tồn Tưởng 存獎, không phải Nghĩa Tồn**.

Nguyên ThiềuA044921: DILA teacher chung cho Lâm Tế29/30/31/34 (conflict), Thiền Tông66/67/68/71; không tự chọn34 hoặc ghi đè mốc33 từ sử liệu. Đây là lý do cần phân loại xuất gia/tham học/truyền pháp và review đường có chứng cứ.

Nghiên cứu sử liệu Nguyên Thiều33, Minh Hải34 ở [bài Lê Xuân Thông](https://phatgiao.org.vn/so-to-minh-hai-dac-tri-phap-bao-cua-dong-thien-lam-te-chuc-thanh-d49548.html), [Giác Ngộ](https://giacngo.vn/long-trong-tuong-niem-to-minh-hai-phap-bao-post23886.html), [Nghiên cứu Phật học](https://www.tapchinghiencuuphathoc.vn/truyen-thua-thien-phai-lam-te-tai-hue.html). Nếu **quy ước truyền thống Lâm Tế38** và cùng đường truyền đã xác minh thì phép quy đổi lần lượt70/71; đổi Thích Ca1 thành71/72. **Không phải kết quả đã chứng minh đường DILA.** Hai bài kể lại cùng tư liệu không được tự coi là3 gốc chứng cứ.

A000662明海/X0613 vẫn là ứng viên chưa xác định với Minh Hải Pháp Bảo. Không sameAs/đặt mốc Chúc Thánh cho ID này. Source `TS-Minh-Hai-Phap-Bao.ttl` còn nhãn Nguyên Thiều/tiểu sử rỗng/generation71; giữ nguyên để audit identity riêng, không sửa theo tên filename.

Mốc truyền thống có CBETA localT48n2008_p0361c15–19; source SHA trong seed. Linji/Xinghua có [DDM EP199](https://www.ddcep.org.tw/default-ddmtw/xmnews/cont?qcat=0L221596734435375771&sid=0P135550259221313171&xsmsid=0L207419114119814182) và DILA exact XML. Khai tổ nhánh đối chiếu exact aliases/sect trong XML DB, đời1 là quy ước công bố.

## Admin sử dụng

[TTL form](http://localhost:8080/daoanh/admin/monk_ttl_add.html): nhập db_id rồi nạp DB, xem9 hệ tính tự động, bấm tính để bổ sung draft+nguồn suy dẫn, bấm lưu snapshot nếu muốn giữ audit. Editor mốc bằng textbox/select/chứng cứ, không yêu cầu viết JSON. Lưu revision có expected_revision để tránh phiên khác ghi đè. Số legacy vẫn giữ riêng. TTL xuất mới lưu counting_scheme, trạng thái, rationale và source snapshot đường truyền. Không xuất lại hàng loạt1.037 file đã xuất của T227 trong phiên này.

[Cây mẫu](http://localhost:8080/daoanh/places?mode=lineage&focus=A004980&lm=tree): panel phụ hiển thị mỗi hệ và đường; candidate/conflict/incomplete/missing_anchor rõ ràng.

CLI `scripts/compute_generations_v2.py` snapshotDB, xử lý từng ID, outputJSONL; chưa chạy tính toàn bộ48.673 người trong phiên này. Installer seed gốc5 hệ + extension4 trong report; các revision mới sau này phải qua UI/API.

## Hồi quy/hoàn tác

20 tests gồm chu trình/self, đa đường cùng/khác độ dài, conflict/checkpoint/disconnect, nguồn thiếu/drift, identity,3gốc, reviewed transmission, CAS, bound và RDF roundtrip. UI real kiểm không thay ô số legacy; zero pageerrors. Năm bảng nguồn hash giữ nguyên xem reportT233.

Backup `data/backups/T232-generation-engine-20261004/db-install/lineage-before.db`. Hoàn tác bằng công cụ chung `scripts/rollback-name-generation.py`, dry-run mặc định/hash guards, chỉ6bảngT232+T233, không restore toànDB dùng chung. Báo cáo, dữ liệu JSONL và back-up luôn được giữ.
