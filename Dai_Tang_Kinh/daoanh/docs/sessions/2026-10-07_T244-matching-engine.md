# T244 — M7 Matching Engine `matchGeographicSites` (BUILD DONE)

> Ngày build: 2026-10-07 · Task: `tasks/T244-m7-matching-engine.md`
> Nguồn đặc tả: `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` §Logic Khớp

## 1. Tóm tắt
- Engine khớp **`matchGeographicSites`** theo đúng M7: điểm `0,5·tên + 0,3·không gian + 0,2·loại&thời kỳ`, trùng **chữ Hán** `+0,2` (cốc 1,0); auto khi Hán-exact ≤2km hoặc một bên tâm hành chính ≤10km; queue khi 2–25km **hoặc** tên giống 0,85–0,95; **>25km không bao giờ auto**; va chạm cùng tọa độ → demote queue; **gate VN**: auto→queue cho tới khi có ≥200 cặp ground truth.
- **15/15 test PASS** (fixture thuần, không mạng). Chạy thật: 38.199 cặp, **`auto_over_25km_raw = 0`** ✓.
- **Phát hiện then chốt:** `raw_auto == 0` — auto path **chưa kích hoạt được** trên dữ liệu thật vì places_vn thiếu `name_zh` + không có admin-polygon. Sẽ định lượng qua calibrate sample 319 cặp.

## 2. Files
```
scripts/vn_places_t244_matching.py      # ENGINE (mới)
tests/test_t244_matching.py             # 15/15 (mới)
data/t244_sample_pairs.json             # 319 cặp gán nhãn (sinh ra, additive)
data/t244_matching_report.json          # report khớp (sinh ra, additive)
package.json                            # wire test:t244 sau test:t243
```

## 3. Kết quả đo được
```
places_vn: 6002 | places_dila ref (bbox VN): 1445 | pairs_total: 38199 | ~107s
by_decision: raw_queue 37112 · raw_reject 1087 · raw_auto 0
auto_over_25km_raw: 0  ← done_when
sample rows: 319  (queue 300 / reject 13 / name_low 6; name_band 0, auto 0, collision 0)
T244 PASS 15/15
```

## 4. Quyết định & phát hiện
- **`raw_auto==0` là dữ liệu, không phải bug:** engine thực thi đúng spec; spec yêu cầu auto phải có Hán-exact ≤2km (hoặc admin ≤10km). places_vn (Wikidata/OSM/disantongiao) hầu như không có `name_zh`; admin-polygon không tồn tại trong dữ liệu hiện tại.
- **Hệ quả kế hoạch:** muốn mở auto-link ở Việt Nam cần nạp `name_zh` cho places_vn (ứng viên: nối Wikidata `zh`/`P1448`, hoặc crawl). Đề xuất đưa vào **T245 (geo_cross_ref)** — nhưng T245 chỉ dùng để *reference linkage*, phần `name_zh` có thể thành một mục con. Đã ghi vào task T244 (dòng "Đề xuất…T245").
- **sample ≥200 cặp đạt** (319). Người gán nhãn điền `label` ∈ {`accept`,`reject`,`later`}; chạy `--eval data/<labels>.json` → precision/coverage theo `raw_decision` (trước gate).
- Bỏ `match_geographic_sites` phiên bản rác đầu (đang set/dict không hashable) → viết lại bằng bucket id.

## 5. Sai lầm đã vấp (thuế bài cho session sau)
1. **cmd `& echo %ERRORLEVEL%` nở lúc parse** → luôn ra 0 dù python fail. Dùng `cmd /c "py ... > log 2>&1"` rồi lấy `$LASTEXITCODE` từ PowerShell.
2. **PowerShell redirect `> file` ghi UTF-16** → Read tool báo "binary file". Redirect qua cmd thuần.
3. **Float so sánh `0.857 == 6/7` fail** → assert tolerance.
4. **`tp` kỳ vọng sai:** period rỗng → `_period_overlap` 0,5 ⇒ `tp=0,75` không phải 1,0; unknown type vs monastery → `_type_match` 0,3.
5. **Cand là set dict** (không hashable) → chuyển set id + `by_id`.

## 6. Chưa xong
- **Gán nhãn 319 cặp** (Admin/human) → `data/t244_labels.json` → chạy `--eval` để báo precision/coverage (yêu cầu bước 4 acceptance).
- Nạp `name_zh` cho places_vn để kích hoạt auto path (đề xuất T245).
- Cân nhắc mở cấu hình `--no-vn-gate` cho môi trường ngoài VN (gate chỉ bắt `country=='VN'`).

## 7. Lệnh chạy lại / revert
```bash
python -X utf8 tests/test_t244_matching.py                        # 15/15
python -X utf8 scripts/vn_places_t244_matching.py --build-candidates   # full + sample + report
python -X utf8 scripts/vn_places_t244_matching.py --eval data/t244_labels.json
# revert dữ liệu: xóa data/t244_sample_pairs.json + data/t244_matching_report.json (DB không bị sửa)
# revert git:   git revert --no-edit 32e75bc84b80f9a5bca111cb6f2cce0e8489e20b 6b30a7ab013f44d9247802a6d94f13a675c4682c
#               (pass-2 trước, pass-1 sau; ROLLBACK.md §1 hash đã verify)
```