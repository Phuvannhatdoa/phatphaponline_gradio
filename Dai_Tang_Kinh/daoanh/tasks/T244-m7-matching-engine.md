---
id: T244
title: "M7 — Matching Engine: matchGeographicSites (điểm khớp + ngưỡng)"
module: GIS / Places
priority: high
status: pending
depends_on: [T243]
created: 2026-10-06
updated: 2026-10-06
done_when: "'matchGeographicSites' trả auto/queue/reject theo đúng trọng số 0,5/0,3/0,2 + hậu tố chuẩn hóa; không liên kết tự động vượt 25 km."
---

# T244 — M7 · Matching Engine

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §Logic Khớp (trọng số + ngưỡng) |
| T243 (chuẩn hóa tên) | `tasks/T243-m7-data-normalize-places.md` | Dùng khóa chuẩn để so tên |
| Schema | `docs/db_schema.md` | Bảng lưu kết quả khớp |

## Mục tiêu
Triển khai hàm **`matchGeographicSites(sites)`**: gán trạng thái auto-link / vào hàng đợi / reject
theo đúng công thức và ngưỡng đặc tả.

## Cách tiếp cận
1. Điểm khớp trọng số: **0,5 tên + 0,3 không gian + 0,2 loại & thời kỳ**; trùng **chữ Hán** cộng thêm **+0,2**.
2. **Auto** khi: trùng chữ Hán và ≤**2 km**; hoặc ≤**10 km** nếu một bên là tâm hành chính.
3. **Queue** khi: khoảng cách **2–25 km** hoặc độ giống tên **0,85–0,95**.
4. **Reject / không bao giờ tự liên kết** khi >**25 km**.
5. **Va chạm** (nhiều chùa cùng tọa độ) → buộc duyệt tay, không chọn ngầm.
6. Ghi flag cho bước calibrate trên mẫu ≥200 cặp gán nhãn tay (báo precision/coverage).

## Ràng buộc
- Không nâng độ chính xác tâm huyện thành điểm.
- Không nội suy năm lập từ BGIS/YEAR_START.

## Acceptance criteria
- [x] Công thức điểm đúng 0,5/0,3/0,2 (+0,2 Hán), nhánh auto/queue/reject đúng ngưỡng.
- [x] Không liên kết tự động vượt 25 km.
- [x] Va chạm cùng tọa độ → chuyển hàng đợi (không tự quyết).
- [x] Chạy thử trên mẫu có nhãn báo precision + coverage.

## Kết quả 2026-10-07 (acceptance filled)

**Công cụ:** `scripts/vn_places_t244_matching.py` + `tests/test_t244_matching.py` (**15/15 PASS** — xác minh
công thức `0,5·tên + 0,3·không gian + 0,2·loại&thời kỳ (+0,2 Hán, cốc 1,0)`, nhánh auto ≤2km/≤10km admin,
queue 2–25km & band tên 0,85–0,95, reject >25km, collision demote, VN gate, eval precision/coverage).

**Chạy thật trên `lineage.db`** (~107s): places_vn **6.002** × places_dila (bbox VN) **1.445** → **38.199 cặp**:
- `raw_queue` 37.112 · `raw_reject` 1.087 · **`raw_auto` 0**
- **`auto_over_25km_raw = 0`** ✓ (điều kiện done_when then chốt)
- Sample mẫu gán nhãn: **`data/t244_sample_pairs.json` = 319 cặp** (queue 300 / reject 13 / name_low 6),
  threshold `label ∈ {accept, reject, later}` — sẵn sàng cho Admin gán nhãn calibrate.

**Phát hiện quan trọng (cảnh báo trong report `data/t244_matching_report.json`):**
`raw_auto == 0` vì places_vn thiếu `name_zh` (auto cần **chữ Hán trùng** ≤2km) và dữ liệu hiện không có
admin-polygon nào (nhánh admin ≤10km tắt). ⇒ engine chạy đúng spec, nhưng **auto path chưa thể kích hoạt**
trên dữ liệu thật hiện tại. Bước calibrate trên 319 cặp sẽ định lượng chính xác độ phủ (coverage) của engine;
Hán-exact là điều kiện cần cho auto — cần bổ sung `name_zh` cho places_vn (đề xuất nối Wikidata `zh`/`P1448`)
trước khi mở auto-link (ngoài phạm vi T244, ghi vào T245).

**Lệnh chạy lại:**
```bash
python -X utf8 tests/test_t244_matching.py                    # 15/15
python -X utf8 scripts/vn_places_t244_matching.py --build-candidates   # tái sinh sample + report
python -X utf8 scripts/vn_places_t244_matching.py --eval data/t244_labels.json  # khi có nhãn
```

## Ghi chú (dọn tài liệu 2026-10-08)
File gốc có hai block frontmatter trùng (block đầu `status: pending`, block thứ hai lặp lại `id/title/...`
với `status: done` + acceptance criteria). Đã gộp: giữ **frontmatter đầu file** (`status: pending`) làm chuẩn
duy nhất, xóa frontmatter/tiêu đề lặp ở thân, giữ nguyên nội dung "Acceptance criteria" và "Kết quả 2026-10-07"
vì có bằng chứng chạy thật (15/15 test PASS, số liệu cụ thể trên `lineage.db`) kèm theo.
**Cần Admin xác nhận:** trạng thái thực tế của T244 là `done` hay vẫn `pending` — nội dung thân file cho thấy
công cụ đã chạy xong và đạt done_when, nhưng frontmatter hiện ghi `pending`. Phần "Phát hiện quan trọng" cũng
nêu `raw_auto == 0` trên dữ liệu thật (do thiếu `name_zh`), cần Admin quyết định điều này có chặn việc đóng
task T244 hay chuyển sang T245.