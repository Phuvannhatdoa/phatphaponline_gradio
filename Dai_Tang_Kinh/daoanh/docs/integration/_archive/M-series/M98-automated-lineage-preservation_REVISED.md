# M98 · Automated Dharma Lineage Preservation (REVISED — Evidence-Based)

**Spec · P2** (Revised from archived M98 per T277 Phase A)

## Mục đích (Revised)

Hệ thống **đối soát và bảo toàn mối quan hệ thầy-trò** dựa trên **bằng chứng DILA + TTL** — không dùng blockchain, không AI tự động, không cam kết 100 năm.

Chỉ thực hiện: (1) đối chiếu `lineage_edge_assertions` (DILA verified) với `hasTeacher/hasDisciple` (TTL), (2) ghi log sự không khớp để Admin rà soát, (3) xuất báo cáo định kỳ cho team biên tập.

## Phân tích thực tế (2026-10-11)

| Nguồn | Cạnh thầy→đệ | Có số đời | Ghi chú |
|---|---|---|---|
| DILA (`lineage_edge_assertions` verified) | 46.004 | Không | Chỉ xác nhận quan hệ, không có generationOrder |
| TTL (`hasTeacher/hasDisciple`) | ~1.000 | Có (`generationOrder`) | Chỉ 1.021 vị có TTL file |
| Khớp TTL↔DILA | ~1.000 cạnh | Có | Chỉ ~22% cạnh DILA có TTL mapping |

**Kết luận:** Không thể "tự động tồn tại 100% mạch truyền thừa" — chỉ có ~22% cạnh DILA có bằng chứng TTL. Blockchain/AI/100-year là **speculative** (không có bằng chứng), loại bỏ.

## Chỉ số thực tế (từ T275)

- Cạnh DILA verified: **46.004**
- Cạnh TTL có `generationOrder`: **1.007** (khớp +1: 911, lệch: 48, thiếu file đệ tử: 70)
- Cạnh DILA có mapping TTL: **~1.000** (~22%)
- Cạnh DILA **không** có TTL: **~45.000** (cần Admin rà soát thủ công)

## Chỉ giữ: Quy trình đối soát định kỳ (Evidence-Based)

1. **Mỗi sprint:** Chạy `scripts/t275_ttl_anchor.py` xuất TSV cạnh TTL↔DILA + trạng thái khớp/lech
2. **Admin rà soát:** Cạnh `lech` / `thiếu_file_đệ_tử` → đưa vào hàng chờ Admin
3. **Báo cáo:** Xuất CSV cho team biên tập (`docs/evidence/T275_ttl_anchor_edges.tsv`)
4. **Không** ghi DB tự động, **không** blockchain, **không** AI tự động sửa

## Acceptance Criteria (Revised)

- [x] Xuất TSV cạnh TTL↔DILA với trạng thái `khớp`/`lech`/`thiếu_file_đệ_tử`/`thiếu_số_đời`
- [x] Admin có CSV để rà soát 48 cạnh lệch + 70 thiếu file đệ tử
- [ ] Pipeline `scripts/t275_ttl_anchor.py --lines` chạy tự động trong CI (chờ Admin cấu hình)
- [ ] Không có code blockchain/AI/immutable storage

## Loại bỏ (Archived Speculative Claims)

| Claim gốc | Lý do loại bỏ |
|---|---|
| Blockchain immutable storage | Không có bằng chứng, không phù hợp dữ liệu Phật học |
| AI auto-detect/fix 90% | Không có training data, không có validation |
| 100 năm immutable storage | Không có infrastructure, không có SLA |
| 10.000+ mạch dữ liệu training | Không có dataset, số liệu bịa |
| 90% AI accuracy | Không có benchmark, số liệu bịa |
| 100 năm preservation | Không có infrastructure commitment |

## File liên quan

- Task gốc: `docs/integration/_archive/M-series/M98-automated-lineage-preservation.md` (archived)
- Spec liên quan: `tasks/T275-ttl-anchor-generation.md` (neo số đời từ TTL)
- Evidence: `docs/evidence/2026-10-10_T275_ttl_anchor_edges.tsv`
- Task T277: `tasks/T277-archive-and-future-integration.md` (Phase A)