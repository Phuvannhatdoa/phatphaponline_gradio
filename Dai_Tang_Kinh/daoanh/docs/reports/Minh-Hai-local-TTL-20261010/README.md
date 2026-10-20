# Minh Hải Pháp Bảo — cập nhật hồ sơ gốc TTL local của PTDA

Ngày: 2026-10-10. Liên quan T232; không tạo task ID mới.

## Kết quả

Đã cập nhật riêng `data/ttl/TS-Minh-Hai-Phap-Bao.ttl` theo chỉ thị Admin. Đây là hồ sơ tiếng Việt local của PTDA khi DILA-ID cho khai tổ Chúc Thánh chưa được xác minh. Không gắn A000662 và không chờ một lời hứa DILA sẽ cấp ID mới mới lưu dữ liệu PTDA.

| Trường | Trước | Sau |
|---|---|---|
| URI chính | ex:monk/minh_hai_phap_bao | Giữ nguyên |
| Nhãn vi | Nguyên Thiều Siêu Bạch | Minh Hải Pháp Bảo |
| Tiểu sử vi | Trống | Tiểu sử local: Minh Hải, xuất xứ tu học Báo Tư, nhánh Chúc Thánh tại Việt Nam, quy ước đời 71 |
| Nhãn Hán | Không có | 明海法寶 |
| generationOrder | 71 | 71, không tăng đời |
| Hệ đếm | Không được ghi rõ | Ma Ha Ca Diếp = 1, số đời toàn mạch Thiền Tông |
| hasTeacher | ex:monk/nguyen_thieu_sieu_bach | Giữ nguyên |
| Tên dòng / khai tổ | Lâm Tế Chúc Thánh Việt Nam / true | Giữ nguyên |
| Định danh local | URI legacy | Thêm dct:identifier PTDA:minh_hai_phap_bao |
| DILA ID / sameAs | Không có | Không tạo |

Tên đúng được đối chiếu triple đang có trong TTL Nguyên Thiều và nhiều TTL đệ tử, cùng chỉ thị Admin; không suy từ filename. Nguyên Thiều local đang đời 70 và có hasDisciple tới URI Minh Hải. Ma Ha Ca Diếp local đang đời 1. Hai kiểm tra này xác nhận tính nhất quán số học ở phạm vi local, chưa chứng minh toàn đường truyền bằng ba sử liệu độc lập.

## Phạm vi “cùng xuất xứ”

Ghi theo xác nhận Admin là cùng nguồn tu học/pháp mạch chùa Báo Tư ở Quảng Châu, Quảng Đông. Không sao chép quê sinh của Nguyên Thiều sang Minh Hải. Không gộp dữ liệu hai nhân vật, không tự xác định Báo Tư cũ hay Báo Tư Tân Tự, không tự suy đồng môn/thầy xuất gia từ cùng chùa.

Bằng chứng nghiên cứu về 明海法寶 và các giới hạn Báo Tư đã lưu ở [đợt kiểm nguồn](../Minh-Hai-source-recheck-20261010/README.md). Hồ sơ lần này ghi rõ nguồn Admin PTDA, không tự trình bày phát biểu Admin là kết luận DILA.

## Provenance và số đời

Bổ sung SourceRecord LOCAL theo vocabulary hiện có của T226, tên người xác nhận/ngày/phiên bản/citation, và RDF Statement cho số đời 71 với countingScheme cụ thể. Trạng thái số đời là `source_asserted`, phương pháp `admin_confirmation_retaining_legacy_value`.

Giữ trường legacy generationOrder=71 để tương thích dữ liệu hiện có. Không nâng thành assertion accepted trong hệ v2, không dựng ba nguồn giả, không thêm mốc vào registry số đời, không chạy tính đệ quy hoặc đổi số đời các vị khác. File là legacy có metadata bổ sung; không tuyên bố đã hoàn tất migration profile 2.0.0 của toàn corpus.

## Thực thi và kiểm chứng

- Tạo backup file-level trước sửa, có manifest và hash guard trước ghi TTL active.
- Chạy `t203_quarantine_ttl.py --stats` và `--dry-run`: chỉ đọc, không move corpus.
- Kiểm bản đề xuất và active bằng rdflib: 12 → 36 triple; chỉ bỏ hai triple cũ của nhãn sai và tiểu sử trống. Các triple cũ còn lại giữ nguyên.
- 0 self-edge; 0 owl:sameAs; 0 DILA-ID; quan hệ Nguyên Thiều→Minh Hải có chiều đối ứng; đời 70→71 và root Ca Diếp=1.
- Hash TTL Nguyên Thiều và bản `old/TS-Minh-Hai-Phap-Bao.ttl` trước/sau không đổi tại lần verify.
- Reader T226 import_legacy + validate: conforms=true, đúng tên Việt, DILA-ID rỗng, 12 cảnh báo legacy chưa chấp nhận. Metadata chưa tự biến thành fact v2.
- Lệnh revert dry-run PASS; chỉ khôi phục file đã sửa nếu hash vẫn đúng, không đè chỉnh sửa mới.

### Các checks chưa xanh toàn dự án

`post-preflight.log`: exit 1, 23 cờ L1/L2/L3 thuộc các file khác và 24 cảnh báo L5. Minh Hải không xuất hiện trong danh sách lỗi/cảnh báo này. Đây là flags của scanner; không tự biến thành 23 lỗi lịch sử đã được chứng minh.

`pipeline.log`: SSOT guard PASS, dừng ở dup:ids với 8 ID trùng: T158/T168/T169/T170/T171/T177/T206/T215. Các bước sau dup:ids chưa chạy. Không yêu cầu Admin review bản build, không báo toàn pipeline PASS, không tự rename task của session khác.

DB, registry thế hệ, raw DILA/CBETA và UI không được sửa/import ở phiên này. Chưa xác minh API hiển thị nội dung mới; đổi file local không tự chứng minh DB đã đồng bộ.

## Backup và hoàn tác

Backup: `data/backups/Minh-Hai-local-TTL-20261010-d60a0689/TS-Minh-Hai-Phap-Bao.ttl`.
Before SHA-256: `dd018d9f2d5656ec375215462cd67a8ffa18961e620f170b857278b1f30f8d65`.
After SHA-256: `bad70763da261a07ed0736f06cab7599c45046f22e6f1eab9a03cfff0e3856d8`.

Từ daoanh:

```powershell
python -B -X utf8 docs/reports/Minh-Hai-local-TTL-20261010/revert_ttl.py --dry-run
python -B -X utf8 docs/reports/Minh-Hai-local-TTL-20261010/revert_ttl.py --apply
```

Không chạy `--apply` khi chỉ muốn kiểm tra. Script từ chối nếu TTL đã có chỉnh sửa mới. Không cần DB rollback cho phiên này.

## Hồ sơ kiểm chứng

- `before.json` / `dry-run-plan.json` / `manifest.json`: đầu vào, thay đổi được duyệt và hash.
- `proposed.ttl`: bản đề xuất đã qua RDF và đã áp dụng.
- `verification-candidate.json` / `verification-active.json` / `checks.json`: kết quả thực tế.
- `pre-stats.log` / `pre-dry-run.log` / `post-preflight.log` / `pipeline.log`: lệnh đã chạy.
- `verify_change.py` / `revert_ttl.py`: kiểm dữ liệu và hoàn tác có guard.

## Việc tiếp theo

Nếu cần nội dung mới hiện lên ứng dụng, dùng luồng sync riêng hồ sơ local sau khi xử lý cổng preflight phù hợp; không chạy full importer chỉ vì một TTL đã đúng. Việc duyệt mốc cho thuật toán v2 vẫn cần chứng cứ từng quan hệ và đường truyền theo quy trình ba gốc độc lập. DILA mapping sẽ được bổ sung riêng khi có chứng cứ đúng người.
