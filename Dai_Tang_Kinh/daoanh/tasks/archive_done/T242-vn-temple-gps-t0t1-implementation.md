---
id: T242
title: "GPS Chùa Việt Nam — Triển khai ETL Tầng 0/1/2 (Wikidata + OSM + CSDL Chùa Việt → Geocode Google) → places_vn"
module: GIS / Places
priority: medium
status: done
depends_on: [T241]
created: 2026-10-06
updated: 2026-10-07
done_when: "places_vn có seed thật từ Wikidata (T0 enrich) + OSM area-VN (T1) + CSDL Chùa Việt disantongiao.vn geocode Google (T2), output JSON >0, validate bbox VN, đăng ký dataset_sources thật (WIKIDATA / OPENSTREETMAP / DISANTONGIAO_VN), ID VN không trùng DILA, cập nhật db_schema + session log + rebuild dashboard"
---

# T242 — GPS Chùa Việt Nam: TRIỂN KHAI (Tầng 0/1/2)

> Kế thừa thiết kế cấu trúc từ **T241 (DONE)** + đặc tả:
> `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-vietnam-consolidated.md` (M7-VN).
> Bảng đích: **`places_vn`** (RAW, mirror DILA, ID `VN`+10 số).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV (đủ để bắt đầu, không cần hỏi)

| Phần cần liên kết | Đường dẫn (mở ngay) | Dùng để |
|---|---|---|
| Đặc tả M7-VN (schema/luồng/logic chấp nhận) | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-vietnam-consolidated.md` | Định nghĩa `places_vn` 17 cột, 3-Layer, bbox VN, nguồn dữ liệu |
| Schema DB hiện có | `docs/db_schema.md` | Vị trí thêm bảng `places_vn` + bảng `places_dila` (RAW) để mirror; bảng `dataset_sources` (import phải insert) |
| Thư mục đặt script | `scripts/` (mặc định làm việc trong `daoanh/`) | Tạo `vn_places_t0_wikidata.py`, `vn_places_t1_osm.py`, **`vn_places_t2_disantongiao.py`**, **`vn_places_geocode_google.py`**, `vn_places_merge_validate.py` |
| Output dữ liệu | `data/` (`vn_places_t0_wikidata.json`, `vn_places_t1_osm.json`, **`vn_places_t2_disantongiao_raw.json`**, **`vn_places_t2_disantongiao_geocoded.json`**, **`geocode_cache.json`**) | JSON trung gian trước khi import DB |
| Nguồn T2 (crawl) | `https://disantongiao.vn/co-so-du-lieu-chua-viet.html` | CSDL Chùa Việt — tên + địa chỉ (không có GPS) → geocode |
| Hàm chuẩn hóa tên tái dùng | `app.py` → `normalize_text()` | Chuẩn hóa tên chùa (NFKC + bỏ dấu) theo chuẩn có sẵn |
| Build/Dashboard | `scripts/build_progress_data.py` + `dashboard/dashboard_process.html` | Rebuild dashboard để hiển thị tiến độ |
| Task kế thừa (design) | `tasks/T241-vn-temple-gps-t0t1.md` | Nguồn quyết định thiết kế đã chốt |
| Quy tắc chung | `docs/conventions.md` (bản thân dự án) + `AGENTS.md` (gốc) | Zero-RAM, Code Preservation, 3-Layer |

**Quy tắc bắt đầu:** mở đúng 1 file này + các đường dẫn bảng trên là đủ. Tất cả path là tương đối từ thư mục `daoanh/`.

## Mục tiêu

Cài đặt ETL thu thập ground truth GPS chùa / tổ đình / tự viện / thiền viện Việt Nam từ
**Wikidata `P625` (Tầng 0 — enrich)** + **OpenStreetMap Overpass (Tầng 1 — GPS chính)**
+ **CSDL Chùa Việt `disantongiao.vn` → Geocoding Google (Tầng 2 — nguồn địa chỉ)**, đổ vào bảng RAW
`places_vn`. **Bỏ qua GPS DILA** cho phạm vi VN. Không ghi đè `places_dila` / `places` / `entity`.

## 📊 A. Kết luận khảo sát nguồn (06/10/2026) — CHỐT, dev KHÔNG cần khảo sát lại

> Số đo thật lấy trực tiếp qua SPARQL Wikidata + Overpass API ngày **2026-10-06** (không ước lượng).

| Nguồn | Số đo thật (đã đo) | Quyết định |
|---|---|---|
| **OSM nội VN** (`area["ISO3166-1"="VN"][admin_level=2]`) | node `religion=buddhist` = **966** · `amenity=place_of_worship` = **5.044** · `historic=temple` = **3.749** | ✅ **T1 = nguồn GPS chính** (lọc theo area VN) |
| OSM bbox thô 8–24N / 102–110E | **9.820** | ❌ **CẤM dùng bbox thô** — trộn Thái/Lào/Cambodia → thổi số ~10× |
| **Wikidata** (`P17=Q881` + `P625`) | `place_of_worship` có tọa độ = **1.778** · nhưng chỉ **95** mục label tiếng Việt chứa "chùa" + tọa độ · class `temple` = **26** · `P140=Q959` = **0** · `P1566` (GeoNames) = **0** · `P402` (OSM) = **0** | ⚠️ **T0 = làm giàu (Q-ID/label) thôi, KHÔNG phải nguồn GPS chính**; không có cross-link → không kỳ vọng "định danh tự động" |
| **DILA** `places_dila` (đã trong DB) | **59.167** dòng · `places_dila` có 18 cột · CC BY-SA 4.0 | ✅ giữ làm nguồn ánh xạ lịch sử (không đụng) |
| `github.com/nanyang-temples` (host tại DILA) | chùa Trung Hoa **hải ngoại** (TQ/Thái/Sing/Indo/Malaysia/Đài) | ❌ **không có Việt Nam** → bỏ |
| `github.com/nguyenduy1133/Free-GIS-Data` | ranh giới **hành chính** VN (GeoJSON/SHP) | ❌ không có chùa → chỉ giữ làm fallback ranh giới |
| `github.com/xr843/fojin` · `poidata.io` | kinh văn Phật giáo · API **HTTP 403** trả phí | ❌ bỏ |
| **`disantongiao.vn` — CSDL Chùa Việt** | cột: `TT` (**ID c1…cN**) + `Pháp danh` + `Tên chùa` + `Địa chỉ`, filter Tỉnh/Quận · **KHÔNG có tọa độ** · `robots.txt` = `User-agent: * / Allow: /` | ✅ **T2 = nguồn mới** (tên + địa chỉ) → **geocoding Google** → `places_vn` |

**Kết luận then chốt:** *chưa tồn tại nguồn free nào "chuẩn DILA"* (ID cố định + GPS + danh mục chùa VN + tải được).
→ Việc **tự xây `places_vn` với ID `VN`+10 số** và **geocode riêng** là **bắt buộc**, không phải lựa chọn.

## Cách tiếp cận

### Tầng 0 — Wikidata
1. Tạo `scripts/vn_places_t0_wikidata.py` (generator + try-except tiếng Việt; dùng `requests` hoặc `SPARQLWrapper`).
2. SPARQL: entity chùa VN (`P17=Q881` + subclass temple) kèm `P625`, `P131`, `P138`, label vi/en/zh, sitelink.
3. Xuất `data/vn_places_t0_wikidata.json` → đăng ký source Wikidata (CC0, GREEN) → import `places_vn` (`accuracy='dila_exact'`).

### Tầng 1 — OpenStreetMap
4. Tạo `scripts/vn_places_t1_osm.py`.
5. Overpass **lọc theo `area` VN** (❌ không dùng bbox thô — xem bảng trên, bbox thổi số ~10×):
 ```sparql
 [out:json][timeout:40];
 area["ISO3166-1"="VN"][admin_level=2]->.VN;
 ( node["amenity"="place_of_worship"]["religion"="buddhist"](area.VN);
 way["amenity"="place_of_worship"]["religion"="buddhist"](area.VN);
 relation["amenity"="place_of_worship"]["religion"="buddhist"](area.VN); );
 out count;
 ```
 Chạy thêm 2 query phụ (không lọc `religion`, và `historic=temple`) để tăng phủ; tính centroid cho way/relation.
 Endpoint dự phòng: `maps.mail.ru/osm/tools/overpass` (public `overpass-api.de` có thể trả HTTP 406 qua proxy).
6. Dedupe với T0 (khoảng cách <200 m + trùng tên) → giữ record mới.
7. Xuất `data/vn_places_t1_osm.json` → đăng ký source OSM (ODbL, GREEN + attribution) → import `places_vn` (`accuracy='osm_centroid'`).

### Tầng 2 — CSDL Chùa Việt (`disantongiao.vn`) → Geocoding Google → tọa độ

> **Vì sao có tầng này:** site VN này đã có **tên chùa + địa chỉ + ID** nhưng **không có GPS** →
> copy về rồi **đẩy qua Google Geocoding** để lấy tọa độ, dùng cho DB OpenMaps (`places_vn`)
> mà map DILA-đang-dùng sẽ đọc. Đây là nguồn **VN-centric, tên chùa tiếng Việt thật** —
> bù cho Wikidata/OSM vốn mỏng tên tiếng Việt.

8. Tạo `scripts/vn_places_t2_disantongiao.py` (generator + try-except tiếng Việt, Zero-RAM):
 - Entry: `https://disantongiao.vn/co-so-du-lieu-chua-viet.html` (robots.txt = `Allow: /` ✅ crawl được).
 - Lọc theo `Tỉnh/Thành` + `Quận/Huyện` (2 dropdown GET/POST — dev inspect form thật).
 - Cột lấy: `TT` (ID dạng `c1…cN`), `Pháp danh`, `Tên chùa`, `Địa chỉ`, link `Xem Chi tiết` (lấy thêm mô tả).
 - Xuất `data/vn_places_t2_disantongiao_raw.json` — **chưa geocode**.
 - **Ràng buộc:** `User-Agent` rõ ràng + `sleep ≥ 1s` giữa request; ghi `source_url` từng record.

9. Tạo `scripts/vn_places_geocode_google.py` (script dùng chung cho T2, mở rộng sau cho T0/T1):
 - Input `data/vn_places_t2_disantongiao_raw.json` → build query `"{Tên chùa}, {Địa chỉ}"`.
 - Gọi **Google Geocoding API** `https://maps.googleapis.com/maps/api/geocode/json?address=…&key=${GOOGLE_MAPS_API_KEY}&region=vn`;
 key lấy từ env, **không hardcode**.
 - Output `data/vn_places_t2_disantongiao_geocoded.json`: `geo_lat`, `geo_long`,
 `geocode_provider='google'`, `accuracy='geocode_street'`, `geocode_confidence` (ROOFTOP/APPROXIMATE),
 `province`, `district` (parse `address_components`).
 - **Cache** theo `md5(query)` vào `data/geocode_cache.json` → không tốn quota khi chạy lại.
 - Rate-limit `≥ 50ms/request`; bắt `ZERO_RESULTS` / `OVER_QUERY_LIMIT` / `REQUEST_DENIED` → log tiếng Việt + ghi vào `pending`.

10. Merge: record **không geocode được** hoặc tọa độ **ngoài bbox VN** → `places_vn_pending` (đã có sẵn trong DB).
11. Dedupe + validate gộp **T0+T1+T2** → thực thi ở **bước 14** (`vn_places_merge_validate.py`).
12. Đăng ký `dataset_sources` mới: `DISANTONGIAO_VN`
 (`origin_url`, license = **"CC BY 4.0 (ghi rõ nguồn disantongiao.vn)"** → `usage_level=GREEN`
 **sau khi** dev xác nhận trang `Điều khoản sử dụng` cho phép tái sử dụng có ghi nguồn;
 nếu không → `YELLOW`), `attribution_text` tiếng Việt.
13. Đăng ký `dataset_sources` cho **Google Geocoding** (nếu không có → dùng Nominatim `OSM` free,
 `usage_level=GREEN`, `attribution=OpenStreetMap contributors`).


### Merge + kiểm định (gộp T0 + T1 + T2)

14. Tạo `scripts/vn_places_merge_validate.py`: gộp **T0+T1+T2**, gắn `source` (`wikidata` / `osm` / `disantongiao`) + `accuracy` (`dila_exact` / `osm_centroid` / `geocode_street`), validate bbox VN, chống trùng ID `PL*`, dedupe tên theo `normalize_text()`.
15. Cập nhật `docs/db_schema.md` (thêm bảng `places_vn` + 3-layer + nguồn geocoder).
16. Session log `docs/sessions/2026-10-06_T242_t0t1.md` (trong đó ghi thêm phần **T2** + số đếm area-VN) + cập nhật master `session.md`.
17. Chạy `python scripts/build_progress_data.py` → dashboard cập nhật.

## Ràng buộc
- Zero-RAM (generator/iterator), Code Preservation, 3-Layer, `dataset_sources`.
- GPS tự động được phép trực tiếp; liên kết lịch sử↔hiện đại vẫn vô hiệu đến 200 cặp ground truth.
- **Google Geocoding:** ⚠️ key từ env `GOOGLE_MAPS_API_KEY` (**không commit**), cần bật Billing
 (Geocoding có quota free ~5.000/tháng, sau đó **tính tiền**). **Bắt buộc cache** kết quả
 (`data/geocode_cache.json`) để không gọi lại. Tọa độ Google chỉ để **geocode địa chỉ** →
 `accuracy='geocode_street'` (**thấp hơn** `dila_exact`/`osm_centroid`).
- **Phương án free thay thế** (nếu không có key Google): **Nominatim** của OSM
 (`https://nominatim.openstreetmap.org/search`, `User-Agent` + `1 req/s`, ODbL) — cùng schema output.
- **Lọc theo `area` VN, KHÔNG bbox thô** (bbox 8–24N/102–110E thổi số ~10× do trộn Thái/Lào/Cambodia).

## Acceptance criteria

- [x] `scripts/vn_places_t0_wikidata.py` + `vn_places_t1_osm.py` + `vn_places_merge_validate.py` tồn tại.
- [x] **Tầng 2:** `scripts/vn_places_t2_disantongiao.py` + `scripts/vn_places_geocode_google.py` tồn tại.
- [x] Output JSON thực tế >0 record (T0 + T1 + T2).
- [x] T2 raw ≥1 record lấy được từ `disantongiao.vn`; T2 geocoded có `geo_lat/long` cho ≥1 record.
- [x] Mọi `places_vn.geo_lat/long` nằm trong bbox VN; ngoài bbox → `places_vn_pending`.
- [x] ID dùng namespace `VN`+10 số, không trùng format `PL`+12 số.
- [x] Mỗi nguồn đã đăng ký `dataset_sources` (`origin_url`, `license`, `usage_level`): **WIKIDATA, OPENSTREETMAP, DISANTONGIAO_VN** (+ nguồn geocoder nếu có).
- [x] Dedupe T0+T1+T2 thực thi; báo cáo precision/coverage.
- [x] T1 dùng **`area` VN** (không bbox thô); log số đếm được (966 / 5.044 / 3.749) vào session log.
- [x] API key Google không nằm trong source; cache geocode tồn tại; log tiếng Việt khi lỗi quota.
- [x] `docs/db_schema.md` đã thêm bảng `places_vn`.
- [x] Session log `docs/sessions/2026-10-06_T242_t0t1.md` tồn tại.
- [x] Dashboard hiển thị T242; progress_data.json rebuild.

## ▶ KẾT QUẢ TRIỂN KHAI (2026-10-07) — DONE

| Hạng mục | Số đo thật |
|---|---|
| T0 Wikidata (SPARQL `P17=Q881` + P625 + label chùa) | **78** record → `data/vn_places_t0_wikidata.json` |
| T1 OSM Overpass **area VN** (`out center tags`) | **6.106** record (buddhist 2.325 + place_of_worship 6.106, dedup type/id) → `data/vn_places_t1_osm.json` |
| T2 disantongiao.vn (bảng tĩnh — form lọc tỉnh hoá ra không hoạt động, đã probe) | **18** record raw → `data/vn_places_t2_disantongiao_raw.json` |
| Geocode T2 (không có `GOOGLE_MAPS_API_KEY` → **Nominatim** free) | **14/18** ok → `data/vn_places_t2_disantongiao_geocoded.json` + `data/geocode_cache.json` |
| Merge → `places_vn` | **6.002** dòng (wikidata 78 / osm 5.911 / disantongiao 13), `bad_id=0`, `out_of_bbox=0` |
| Merge → `places_vn_pending` | **14** (10 out-of-bbox + 4 no_gps) |
| Dedupe (T0+T1+T2, trùng tên trong 200m) | **186** record |
| `dataset_sources` đăng ký | `WIKIDATA`(GREEN,CC0), `OPENSTREETMAP`(GREEN,ODbL), `DISANTONGIAO_VN`(YELLOW — chờ xác minh điều khoản), `OPENSTREETMAP_NOMINATIM`(GREEN) |
| Test | `tests/test_t242_vn_places_etl.py` **9/9 PASS** (wire `npm run test:t242`) |

**Lệnh chạy lại:**
```bash
python scripts/vn_places_t0_wikidata.py --download
python scripts/vn_places_t1_osm.py --download
python scripts/vn_places_t2_disantongiao.py
python scripts/vn_places_geocode_google.py          # cần env GOOGLE_MAPS_API_KEY để dùng Google
python scripts/vn_places_merge_validate.py --apply
python scripts/vn_places_merge_validate.py --dry-run
python scripts/vn_places_merge_validate.py --revert # DROP 2 bảng + xoá source T242
```

**Lưu ý về nguồn:**
- `disantongiao.vn` form lọc Tỉnh (`cityid`) là GET nhưng mọi tổ hợp param trả cùng bảng tĩnh →
  script này crawl đúng bảng tĩnh (~18–29 dòng mẫu). Đủ acceptance T2; muốn full bộ dữ liệu cần
  điều tra AJAX riêng (ghi vào follow-up, KHÔNG chặn task này).
- `GOOGLE_MAPS_API_KEY` đọc từ env (không có trong source); khi chưa có key, fallback Nominatim
  (`usage_level=GREEN`, cache `geocode_cache.json` để không gọi lại).
- `DISANTONGIAO_VN` để **YELLOW** (chưa xác minh trang điều khoản). Admin xác nhận tái sử dụng
  có ghi nguồn → đổi `usage_level` GREEN.