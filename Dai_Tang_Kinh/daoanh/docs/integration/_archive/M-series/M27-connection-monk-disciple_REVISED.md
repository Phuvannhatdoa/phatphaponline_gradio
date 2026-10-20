# M27 · Kết nối Thầy–Trò Dựa trên Bằng Chứng DILA/TTL (REVISED — Evidence-Based)

**Spec · P1** (Revised from archived M27 per T277 Phase A)

## Mục đích (Revised)

Hệ thống **tra cứu và hiển thị mối quan hệ thầy–trò** dựa trên **bằng chứng DILA verified + TTL generationOrder** — không phải mạng xã hội, không rating 1-5 sao, không "10.000+ practitioners", không kết nối xã hội.

Chỉ thực hiện: (1) tra cứu quan hệ thầy–trò từ `lineage_edge_assertions` (DILA verified), (2) hiển thị số đời từ TTL (`generationOrder`) khi có, (3) ghi rõ nguồn bằng chứng cho từng cạnh.

## Phân tích thực tế (2026-10-11)

| Nguồn | Loại quan hệ | Số lượng | Có số đời | Ghi chú |
|---|---|---|---|---|
| DILA `lineage_edge_assertions` (verified) | `da:isTeacherOf` | 46.004 cạnh | Không | Chỉ xác nhận quan hệ, không có generationOrder |
| TTL `hasTeacher/hasDisciple` | `bkg:hasTeacher/hasDisciple` | ~1.000 cạnh | Có (`generationOrder`) | Chỉ 1.021 vị có TTL file |
| T274 `noi_phap_ttl_only` | TTL-only (VN lineage) | 0 cạnh (chờ Admin) | Có | Chờ Admin quyết định base pool |

**Kết luận:** Không có "10.000+ practitioners", không rating, không mạng xã hội. Chỉ có 46.004 cạnh DILA verified và ~1.000 cạnh TTL có số đời.

## Chỉ giữ: Tra cứu quan hệ thầy–trò có bằng chứng

1. **Tra cứu theo người:** Cho ID DILA/TTL slug → trả về danh sách thầy/trò + nguồn bằng chứng
2. **Hiển thị số đời:** Nếu có TTL `generationOrder` → hiển thị "TTL đời X"; nếu chỉ DILA → "DILA confirmed, số đời chưa có"
3. **Ghi rõ nguồn:** Mỗi cạnh ghi rõ `source: DILA|TTL|TTL-only` + `evidence_file`/`ref`
4. **Không** rating, **không** mạng xã hội, **không** "10.000+ practitioners", **không** kết nối xã hội

## Dữ liệu thực tế (2026-10-11)

| Chỉ số | Giá trị | Nguồn |
|---|---|---|
| Cạnh DILA verified (`da:isTeacherOf`) | 46.004 | `lineage_edge_assertions` |
| Cạnh TTL có `generationOrder` | 1.007 | `t275_ttl_anchor.py` |
| Cạnh khớp DILA↔TTL | ~1.000 | `t275_ttl_anchor.py` |
| Cạnh lệch số đời | 48 | `t275_ttl_anchor.py` |
| Thiếu file đệ tử | 70 | `t275_ttl_anchor.py` |

## UI/UX (Revised — Evidence-Based)

| Trang | Mô tả | Dữ liệu hiển thị |
|---|---|---|
| `/daoanh/lineage/relations/<id>` | Tra cứu thầy/trò của 1 người | Danh sách thầy/trò + `source` + `evidence_file` + `generationOrder` (nếu có) |
| `/daoanh/lineage/chain/<id>` | Chuỗi truyền thừa lên gốc | Đường đi + `generationOrder` tại mỗi bước + `source` tại mỗi cạnh |
| `/daoanh/lineage/discrepancies` | Danh sách cạnh lệch/đối soát | Danh sách 48 cạnh lệch + 70 thiếu file đệ tử (từ T275) |

**Không có:** Trang tìm thầy/trainee xã hội, rating 1-5 sao, hồ sơ cá nhân, kết nối xã hội, notifications.

## Acceptance Criteria (Revised)

- [x] API tra cứu quan hệ thầy/trò trả về `source` + `evidence_file` + `generationOrder`
- [x] Cạnh DILA không có TTL → ghi rõ "DILA confirmed, số đời chưa có"
- [x] Cạnh TTL có `generationOrder` → hiển thị "TTL đời X"
- [x] Xuất CSV cạnh DILA↔TTL cho Admin rà soát
- [ ] Không có UI rating/đánh giá/social features

## Loại bỏ (Archived Speculative Claims)

| Claim gốc | Lý do loại bỏ |
|---|---|
| 10.000+ practitioners | Số liệu bịa, không có bằng chứng đăng ký |
| Rating 1-5 sao | Không có hệ thống đánh giá, không phù hợp quan hệ thầy-trò truyền thống |
| Mạng xã hội (theo dõi, kết nối, profile) | Không phù hợp quan hệ thầy-trò truyền thống Phật giáo |
| Notifications cho kết nối mới | Không có hệ thống kết nối xã hội |
| "Cộng đồng tập training" | Sai bản chất quan hệ thầy-trò Phật giáo |

## File liên quan

- Task gốc: `docs/integration/_archive/M-series/M27-connection-monk-disciple.md` (archived)
- Spec liên quan: `tasks/T275-ttl-anchor-generation.md` (neo số đời từ TTL)
- Evidence: `docs/evidence/2026-10-10_T275_ttl_anchor_edges.tsv`
- Task T277: `tasks/T277-archive-and-future-integration.md` (Phase A)