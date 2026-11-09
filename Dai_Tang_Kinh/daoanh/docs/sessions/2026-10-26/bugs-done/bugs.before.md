# bugs.md — Bug Tracker Nexus / Đồ Thị / Graph

> Theo quy tắc logging trong `docs/PLACE_GRAPH_DISPLAY_SPEC.md §7`:  
> Ghi bug TRƯỚC khi sửa. Không đánh DONE cho đến khi Admin xác nhận.  
> Resolution phải có: commit hash, changed files, test evidence, người xác nhận, timestamp.

---

## Format

```
## BUG-NNN — Tên ngắn
**Route/URL:** ...
**Root entity ID:** ...
**Thời gian phát hiện:** YYYY-MM-DD HH:MM
**Expected:** ...
**Actual:** ...
**Evidence:** [console log / API payload / screenshot path]
**Status:** open | in_progress | pending_confirm | fixed

### Resolution (sau khi Admin xác nhận)
- Commit: `<hash>`
- Changed files: `...`
- Test evidence: ...
- Xác nhận bởi: Admin / namthien@gmail.com
- Timestamp: YYYY-MM-DD HH:MM
```

---

## Bug List

## BUG-001 — Edge thiếu trường `evidence_type` trong api_places_graph
**Route/URL:** `/daoanh/api/places/<id>/graph`
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự)
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Mỗi edge trả về trường `evidence_type` ∈ {with_evidence, partial, co_mention, unverified}
**Actual:** Edges chỉ có `label`, `from`, `to`; không có `evidence_type` — frontend không thể phân biệt mức độ bằng chứng
**Evidence:** Audit code app.py line 4465 (lân cận), 4454 (kinh điển listbibl), 4515 (nexus_events person)
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-002 — Edge thiếu trường `evidence_type` trong api_nexus
**Route/URL:** `/daoanh/api/nexus/<type>/<id>`
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Edges cbeta_ref → `with_evidence`; no ref → `unverified`
**Actual:** Branch etype=person: 2 edges thiếu evidence_type (chỉ có ref/citation); branch etype=place: đã có evidence_type
**Evidence:** Audit code app.py api_nexus line 6418-6424 (etype=person branch)
**Fix (2026-09-22 T161):** Thêm _src + evidence_type "unverified"/"partial" cho 2 edges trong etype=person branch. Revert: `git revert <commit-T161>`
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-003 — Không có PARTIAL badge trên edge thiếu provenance
**Route/URL:** Nexus tab (places.html `_renderVisGraph`)
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Edge partial hiện badge ⚑ + title lý do thiếu provenance
**Actual:** Không có badge — không phân biệt `partial` vs `with_evidence` trên UI
**Evidence:** Code audit `_renderVisGraph` line 3410-3435 places.html
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-004 — `co_mention`/`unverified` edges hiển thị mặc định (spec yêu cầu ẩn)
**Route/URL:** Nexus tab
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** co_mention/unverified ẩn mặc định, chỉ hiện khi bật "Research mode"
**Actual:** Tất cả edges hiện mặc định; không có toggle "Research mode"
**Evidence:** Filter bar HTML line 791-802 places.html — không có Research mode checkbox
**Root cause:** `_nexusToggleResearch` gọi `_nexusRender` (không tồn tại) → state thay đổi nhưng graph không re-render. `_nexusRenderGrouped` không filter `evidence_type`. Ngoài ra: `tang_nhan` group là object dynasty→count, không có verified-count riêng từ backend; tất cả place-person connections là `unverified` (co-mention qua place_person_bibl).
**Fix (places.html):**
- `_nexusToggleResearch`: `_nexusRender` → `_nexusRenderGrouped` (line 5299)
- Group node "Tăng nhân": Research mode OFF → border/font vàng `#e0b252` + tooltip cảnh báo co_mention; Research mode ON → cam `#c4891a` bình thường
- Expansion (dynasty → persons): Research mode OFF → persons hiện badge ⚠ + border vàng + tooltip; Research mode ON → normal styling, không badge
**Test evidence:** JS verify: Research mode OFF → `border="#e0b252", fontColor="#e0b252"` ✓; Research mode ON → `border="#c4891a", fontColor="#f5c84b"` ✓. Graph re-render sau toggle ✓. Screenshot before/after (2026-09-08).
**Design decision:** Không ẩn persons (all connections đều unverified ở place model) — thay bằng visual warning signal để giữ transparency học thuật (evidence-first T108).
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-005 — `_nexusSafeLabel` thiếu fallback chain đầy đủ theo spec §6
**Route/URL:** Nexus tab (mọi entity)
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Fallback: name_vi > preferred_label_vi > display_name > name_han/name_zh > source_label > canonical_id
**Actual:** Chỉ có: label_vi || label || label_zh || id (thiếu name_vi, preferred_label_vi, display_name, source_label, name_han)
**Evidence:** Code line 5211-5216 places.html
**Fix:** Đã có đầy đủ fallback chain trong code hiện tại (line 7051-7057 places.html): name_vi || label_vi || preferred_label_vi || display_name || label || name_han || label_zh || source_label || name_zh || id || canonical_id
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-006 — Place view không auto-expand tang_nhan (spec §4.1 default 3-đời)
**Route/URL:** Nexus tab cho place entity
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Mặc định mở đến đời 2 (root → group → subgroup) — tang_nhan expanded khi load
**Actual:** `_nexusGroupState = { expanded: null, subexpanded: null }` — collapsed mặc định, cần 2 click để thấy subgroup
**Evidence:** Code line 5324 places.html
**Fix:** Đã có `expanded: 'tang_nhan'` cho place entities (places.html line 7165): `const defaultExp = d.entity_type === 'place' ? 'tang_nhan' : null; _nexusGroupState = { expanded: defaultExp, subexpanded: null, ... }`
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-007 (GRAPH_DILA_PROFILE_PANEL_NOT_LOADING_001) — Panel trái không tải hồ sơ DILA khi click node Nexus
**Route/URL:** `/daoanh/` · Tab Nexus · Root: Thiếu Lâm Tự (PL000000023255)
**Clicked node:** Thích Đạo Bằng (道憑) — display_id A005278 · aliases: 釋道憑, Đạo Bằng
**Thời gian phát hiện:** 2026-09-08
**Expected:** Click node person trong Nexus graph → panel trái (`#detailContent`) nhận canonical DILA ID của node được click (A005278), tải hồ sơ qua API, hiển thị loading/error/empty state rõ ràng. `#dilaId` phải được reset trước khi gọi API.
**Actual (2 vấn đề):**
1. Click node → `_nexusShowDetail` chỉ hiện `#nmp-detail` (strip nội bộ Nexus) — panel trái KHÔNG cập nhật; vẫn hiện root PL000000023255, không dùng A005278.
2. Khi user click "→ Vô tab Truyền Thừa" → `selectPerson('A005278')` được gọi: `#dilaId` element KHÔNG được reset trước fetch → hiển thị stale value từ entity trước (PL000000023255). Nếu `/daoanh/api/monk/A005278/graph` fail → `catch (e) { /* silent */ }` → không có error state, `#dilaId` giữ giá trị cũ sai.
**Root cause:**
- `_nexusShowDetail` không gọi left-panel update khi click person node.
- `selectPerson()` line 1932: không có `document.getElementById('dilaId').innerText = '—'` trước fetch.
- Silent catch tại line 1947 che lỗi API.
**Files liên quan:** `daoanh/places.html` lines 1897-1953 (selectPerson), 5667-5733 (_nexusShowDetail)
**Diagnostic evidence:**
- Node `_nxPerson.id` = A005278 (DILA person ID từ `event_text_link.entity_id`).
- `_nexusNetwork.on('click')` → `_nexusShowDetail(node._nxPerson, d)` — không gọi `_currentPlaceId` update.
- `selectPerson` line 1905: `itemId` = A005278 ✓; line 1939: `dilaId` chỉ set nếu `d.ok && d.center` → không reset trước đó.
**Status:** superseded-closed — cả 2 vấn đề đã được fix bởi work chung 2026-09-08 (BUG-010): (1) `_nexusShowDetail` → `openEntityProfileFromNode(n)` dispatcher trung tâm mọi node (person/place/text) tự tải panel trái; (2) `selectPerson` line 2305-2306 reset `#dilaId` thành '—' trước fetch (ghi chú BUG-007 trong code). Verify 2026-09-22: code hiện tại đã có cả 2 fix; catch vẫn silent nhưng không còn stale `#dilaId` vì reset trước fetch + `_nexusProfileReqId` stale guard. Xem BUG-010.

## BUG-008 (MAP_NEARBY_TEMPLE_LAYER_HIDES_SELECTED_PLACE_001) — Filter "Chùa / Tự viện" ẩn selected marker
**Route/URL:** `/daoanh/places.html?id=PL000000023255` · Tab THỰC THỂ · Map filter "Chùa / Tự viện"
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự 少林寺) · lat=34.507018, lng=112.935331
**Thời gian phát hiện:** 2026-09-08
**Expected:** Click filter "Chùa / Tự viện" → giữ marker Thiếu Lâm Tự (z-index cao), đồng thời nạp nearby temples trong viewport/radius vào layer riêng.
**Actual:** Marker Thiếu Lâm Tự bị ẩn sau khi click filter. Danh sách chùa/tự viện lân cận không tải.
**Rules:** selected marker là persistent layer; nearby temples là filter layer độc lập. Toggle filter chỉ ảnh hưởng filter layer.
**Root cause (4 nguyên nhân):**
1. `clusterGroup.clearLayers()` xóa toàn bộ markers kể cả selected — không có persistent layer
2. `viLabels` (không tồn tại) được dùng thay vì `labelLayer` → ReferenceError crash, filter handler dừng giữa chừng
3. `_currentGps` async race — giá trị chưa có khi filter được click sớm
4. `highlightMarker()` gọi sync → Leaflet cluster cluster gộp marker → remove khỏi DOM → `getElementById` trả null → halo không apply
**Fix:**
- `viLabels` → `labelLayer` (places.html line 1248)
- `_selectedLat/_selectedLng` sync fallback (places.html line 854-855)
- `persistentMarkerLayer = L.layerGroup().addTo(map)` — layer riêng, không cluster → selected marker luôn ở DOM (places.html line 853)
- Filter handler: selected marker thêm vào `persistentMarkerLayer` với halo baked in icon, z-index 9000 (places.html lines 1251-1268)
- Backend bbox filter: `AND p.gps_lat BETWEEN ? AND ? AND p.gps_long BETWEEN ? AND ?` (app.py lines 3272-3282)
**Test evidence (real user flow, không inject JS):**
- Search "Thiếu Lâm Tự" → Enter → chờ load → click filter "Chùa / Tự viện" (real click ref_97)
- Network: `bbox=34.1516,112.6099,34.8611,113.2608` gửi trong API call ✓
- DOM: `haloActive=1, haloElementId="dot-PL000000023255", selectedDotInDOM=true, persistentLayerCount=1` ✓
- Screenshot: marker xanh halo (Thiếu Lâm Tự) + marker đỏ nearby temples cùng hiện sau filter click ✓
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-010 (GRAPH_NODE_CLICK_LEFT_PROFILE_PANEL_NOT_LOADING_002) — Click node tree/graph không tải panel trái
**Route/URL:** `/daoanh/places.html` · Tab Nexus
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự)
**Thời gian phát hiện:** 2026-09-08
**Expected:** Click bất kỳ node nào (root, địa danh, tu sĩ) → panel trái tải hồ sơ entity đúng với canonical ID của node đó; loading state → populated/error/empty rõ ràng; click nhiều node liên tiếp không để lại dữ liệu cũ.
**Actual:** Click root Thiếu Lâm Tự → không có gì xảy ra với panel trái. Click node địa danh/nhân vật trong expansion → panel trái không cập nhật (chỉ strip nmp-detail bên phải hiện).
**Root cause (3 vấn đề):**
1. Click handler trong `_nexusGroupedFinalize`: center node (không có `_nxGroup`/`_nxSubgroup`/`_nxPerson`) không được xử lý → không có action.
2. `_nexusShowDetail`: chỉ gọi `_nexusLoadPersonProfile` nếu `n.navigable && n.group === 'person'` — place nodes (từ dila expansion) và text nodes không được load profile.
3. Không có hàm trung tâm nào routing node → entity type → canonical ID → profile loader — mỗi node type xử lý riêng lẻ.
**Fix plan:** Thêm `_nexusLoadPlaceProfile(n)`, `openEntityProfileFromNode(node)` (dispatcher trung tâm), cập nhật click handler xử lý center node, cập nhật `_nexusShowDetail` gọi `openEntityProfileFromNode`.
**Files liên quan:** `daoanh/places.html` lines 5791-5806 (click handler), 5902-5910 (_nexusShowDetail), 5859-5899 (_nexusLoadPersonProfile)
**Fix applied (2026-09-08):**
- Added `_nexusLoadPlaceProfile(n)` — lightweight place profile loader for left panel (no tab reset, no map flyTo).
- Added `openEntityProfileFromNode(node)` — central dispatcher routing any node via ID priority chain → correct profile loader. Handles person, place, and unknown/text nodes without parsing labels.
- Added `_nexusProfileReqId` counter → stale fetch guard in both `_nexusLoadPersonProfile` and `_nexusLoadPlaceProfile` — rapid node clicks no longer leave stale data.
- Updated `_nexusShowDetail`: replaced person-only check with `openEntityProfileFromNode(n)` — all navigable nodes now load left panel.
- Updated click handler in `_nexusGroupedFinalize`: added `else if (String(nid) === String(d.center.id))` → center node click now calls `openEntityProfileFromNode` with root entity.
**Test evidence:** JS syntax OK ✅ · node scripts/e2e-test.js → ✅ All pages passed.
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-011 (MAP_MARKER_PLACE_PROFILE_METADATA_NOT_LOADING_001) — Click marker bản đồ không load GPS/district/note/category vào panel trái

**Admin xác nhận DONE 2026-10-11.**
**Route/URL:** `/daoanh/places.html` · Tab THỰC THỂ · Map view
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự — và tất cả places không có row trong `entity_source_ids`)
**Thời gian phát hiện:** 2026-09-09
**Expected:** Click marker → panel trái hiển thị đầy đủ: tên Việt/Hán, GPS coordinates, địa chỉ hành chính (district_vi), loại địa danh (note_category badge), mô tả DILA (note), DILA Place ID.
**Actual:** Panel trái chỉ hiển thị tên và Place ID. GPS → '—', district → '—', note_category badge ẩn, note block ẩn.
**Evidence (API + DB):**
- `GET /daoanh/api/entity/PL000000023255/unified` trả `{"ok":true,"sources":{"dila":{"active":false},...}}` vì `entity_source_ids` không có DILA mapping cho entity này.
- DB `places_dila WHERE id='PL000000023255'`: `geo_lat=34.507018, geo_long=112.935331, district='中國-河南省-鄭州市-登封市', note_category='寺廟、佛塔、佛教文化地點'`, note đầy đủ.
- DB `namevi_map_places WHERE dila_id='PL000000023255'`: `gps_lat=34.507018, country_vi='Trung Quốc', district_vi='Thành Phố 登封...', vn_name_status='reviewed'`.
- DB `entity WHERE entity_id='PL000000023255'`: FOUND (alias_vi='Thiếu Lâm Tự') → unified trả `ok:true` → frontend vào UNIFIED PATH, không fallback legacy.
- DB `entity_hub WHERE entity_id='PL000000023255'`: NOT FOUND.
- DB `entity_source_ids WHERE source_entity_id='PL000000023255'`: 0 rows → `source_map={}` → `sources.dila.active=false`.
**Root cause:**
`entity_unified` tìm DILA source qua `entity_source_ids` — không có row → `sources['dila'] = {"active": False}`. Unified vẫn trả `ok:true` vì entity tồn tại trong `entity` table → frontend chọn UNIFIED PATH → không fallback legacy. DILA data (GPS/district/note/category) không được populate.
**Fix (app.py `entity_unified` ~line 13082):**
Thêm fallback: khi `'DILA' not in source_map` nhưng `entity_id.startswith('PL')` → dùng `entity_id` trực tiếp làm DILA ID để lookup `places_dila` + `namevi_map_places`. Thêm `name_vi` vào response. Strip HTML từ note.
**Fix (places.html `selectItem` ~line 1042):**
- Thêm `_selectToken` counter để guard stale response khi click nhiều marker liên tiếp (`_myToken !== _selectToken → return`).
- Thêm reset `dilaId` → '—' trong phần reset ban đầu (trước đây không có).
**Changed files:** `app.py` (entity_unified ~line 13082-13141), `places.html` (~line 861-867, 1044-1048, 1058-1072, 1106-1110, 1232-1234)
**Syntax check:** JS OK (1 block, 0 fail) · Python ast.parse OK
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

## BUG-012 (GIS_SEARCH_MARKER_STATE_MISMATCH_001) — Lệch state GPS/RAG giữa tìm kiếm và marker bản đồ

**Admin xác nhận DONE 2026-10-11: BUG-012a và BUG-012b.**
**Route/URL:** `/daoanh/places.html` · Tab THỰC THỂ · Ô tìm kiếm + Map marker
**Root entity ID:** Bất kỳ entity nào không có `note` trong unified DILA source
**Thời gian phát hiện:** 2026-09-09
**Expected:**
- Sau khi click marker → search entity mới: khối "Vị Trí · 3 Lớp RAG" hiển thị GPS của entity MỚI (hoặc '—' nếu không có data)
- Web Update (Thông Tin Cập Nhật Từ Web) tra thông tin của entity MỚI
**Actual:**
- (A) Khối GPS/RAG vẫn hiện dữ liệu của entity CŨ (race condition: response cũ ghi đè sau reset)
- (B) Web Update dùng `_currentEnrichEntityId` của entity trước → tra/hiển thị thông tin sai entity
**Evidence (code audit):**
- `initWebEnrichPanel(d.source_record_id)` tại line 1212 chỉ được gọi BÊN TRONG `if (d.note)` block — nếu unified response không có `note` (nhiều entity), `_currentEnrichEntityId` không được update
- `initWebEnrichPanel` không có `_selectToken` guard → response từ fetch cũ có thể ghi vào panel của entity mới
- `_currentEnrichEntityId` KHÔNG được reset khi `selectItem` bắt đầu → nếu entity mới không trigger `initWebEnrichPanel`, state cũ tồn tại
**Root cause:**
1. `initWebEnrichPanel` đặt điều kiện sai — phụ thuộc vào `d.note` thay vì luôn được gọi
2. Thiếu `_selectToken` guard trong `initWebEnrichPanel` fetch callback
3. Thiếu reset đồng bộ `_currentEnrichEntityId` khi `selectItem` bắt đầu
**Files liên quan:** `daoanh/places.html` line 1082-1091 (sync reset), line 1205-1215 (unified dila block), line 1949-1966 (initWebEnrichPanel)
**Fix:**
- Sync reset: `_currentEnrichEntityId = null` + webEnrichPanel clear ngay khi `selectItem` bắt đầu
- Unified path: gọi `initWebEnrichPanel(d.source_record_id || id)` NGOÀI `if (d.note)`, bên trong `if (src.dila)` — xóa call cũ trong `if (d.note)`
- `initWebEnrichPanel`: thêm `const _b12EnToken = _selectToken` + guard `if (_b12EnToken !== _selectToken) return` trong `.then` và `.catch`
- Debug logs: `[select]`, `[rag-geo]`, `[web-update]`
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.
**Changed files:** `daoanh/places.html` (3 edits: sync reset tại selectItem start, gọi initWebEnrichPanel ngoài if(d.note), thêm _b12EnToken race guard)
**Revert:** `git revert e69ddf2`

## BUG-009 (MAP_PLACE_TYPE_ICON_MISCLASSIFICATION_001) — Map markers không dùng icon semantic theo loại địa điểm
**Route/URL:** `/daoanh/places.html` · Tab THỰC THỂ · Map view
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự — test case chính)
**Thời gian phát hiện:** 2026-09-08
**Expected:** Mỗi loại địa điểm hiển thị icon SVG semantic khác nhau dựa trên `places_dila.note_category` — temple-gate cho tự viện/chùa, tam giác cho núi, sóng cho sông/hồ, v.v. `selected` state không override place type icon.
**Actual:** Markers dùng icon/dot đồng nhất, không phân biệt loại địa điểm. Temple-gate icon sai khi dùng làm global fallback thay vì chỉ cho confirmed Buddhist sites.
**Root cause (3 nguyên nhân):**
1. Không có field `icon_type` trong API response — frontend không biết loại địa điểm
2. `places_dila.note_category` không được JOIN vào query — chỉ có `place_type` (generic)
3. `places.id` (PL000001) vs `places_dila.id` (PL000000000001) dùng padding khác nhau → JOIN thất bại trả NULL

**Fix (app.py):**
- Thêm `_note_category_to_icon_type(nc, name_zh)` helper: DILA note_category → icon_type string (17 types)
- Sửa JOIN trong 5 query paths của `api_places_search` và `api_places_all`: `d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))`
- Thêm `d.note_category` trong SELECT, `'icon_type': _note_category_to_icon_type(r['note_category'], r['name_zh'])` trong result dict
- Sửa `api_places_all`: bỏ `p.note_category` (column không tồn tại) → dùng `d.note_category` qua JOIN

**Fix (places.html):**
- Thêm `CATE_DOT_COLORS` với 17 types, `ICON_TYPE_LABELS` Vietnamese display names
- Thêm `resolvePlaceIconType(place)`: primary=`place.icon_type`, secondary=`place.note_category` parse, fallback=name heuristics (compound keywords, `$` end-anchor)
- Thêm `getPlaceIconSvg(cate, isSelected)` switch với SVG riêng: temple_site (gate), mountain (triangle), river_lake (wave), cave (arch), pass (notch), country (flag), natural_region (leaf), mythological (cloud), province/prefecture/district/town/city/dynasty_region (building by color)
- Sửa `addMarker`: thêm tooltip `'Loại: ' + typeLabel` bindTooltip
- Sửa `addMarkerFromResult`: `iconType = cate || r.icon_type || resolvePlaceIconType(r)`
- Sửa persistent marker filter handler (line ~1411) và BẢN ĐỒ tab (line ~7083)

**False positive prevention:**
- `藍氏` bị match sai (character class `[伽藍]` bắt `藍`): fix → compound keyword regex `寺|廟|塔|庵|精舍|伽藍|石窟`
- `興都庫什山` bị classify thành city (ký tự `都` giữa tên): fix → end-anchor `$` (`[城都]$`)

**Test evidence (API — real server, không inject JS):**
| # | Place | id | note_category | icon_type kỳ vọng | icon_type thực tế |
|---|---|---|---|---|---|
| 1 | Thiếu Lâm Tự 少林寺 | PL000000023255 | 寺廟、佛塔、佛教文化地點 | temple_site | ✅ temple_site |
| 2 | 並州 (Bịnh Châu) | — | 寺廟、佛塔、佛教文化地點 | temple_site (DILA data) | ✅ temple_site |
| 3 | 魯國 (Lỗ Quốc) | — | 寺廟、佛塔、佛教文化地點 | temple_site (DILA data) | ✅ temple_site |
| 4 | api_places_all count | — | — | >0 | ✅ count=10 |
| 5 | ID normalization | PL000001 | — | JOIN thành công | ✅ printf padding fix |

**Test evidence (UI — real click, screenshot):**
- Search "Thiếu Lâm Tự" → Enter → load → marker **đỏ hình cổng chùa (temple-gate)** xuất hiện trên map tại tọa độ Hà Nam, Trung Quốc ✓
- Badge `寺廟、佛塔、佛教文化地點` hiển thị trên left panel ✓
- Screenshot: 2026-09-08 session BUG-009 UI verify

**Field priority order:**
1. `places_dila.note_category` (authoritative DILA classification)
2. Name-suffix heuristics với compound keywords (compound only, end-anchored for admin subtypes)
3. Fallback: `unknown`

**Status:** fix applied 2026-09-08 (UI verify + screenshot). **2026-09-10 (Batch D):** công việc này ≡ **MAP_SEMANTIC_MARKER_ICONS_001** (tasktodo ACTIVE) — cùng code `getPlaceIconSvg`/`cateMap` trong places.html; đã hợp nhất, bản ghi này chuyển CLOSED-as-duplicate. Chờ 1 lần admin confirm DONE chung (tại mục ACTIVE).

---

## BUG-015 (CONSOLE_SYNTAXERROR_MONK_RESOLVE_001) — SyntaxError: Unexpected end of input + monk-resolve 404

**Admin xác nhận DONE 2026-10-11.**
**Route/URL:** `/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255`
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự)
**Thời gian phát hiện:** 2026-09-10
**Expected:** Không có SyntaxError trong console khi load entity. Mọi fetch() trả JSON hợp lệ hoặc có fallback.
**Actual:**
```
:8080/daoanh/api/monk-resolve?name=Thiếu+Lâm+Tự  → 404 NOT FOUND
places.html:1  Uncaught SyntaxError: Unexpected end of input  (×3)
```
**Root cause (đã xác minh):**
1. Route `/daoanh/api/monk-resolve` (`app.py:10390`) **có sẵn**, không thiếu như giả thuyết ban đầu — nó cố ý trả `404` khi tên gõ vào không khớp row `people` nào (vd. gõ 1 địa danh như "Thiếu Lâm Tự" vào ô search dùng chung place+monk). "Không tìm thấy" là outcome hợp lệ của 1 resolver, không phải lỗi server → dùng HTTP 404 cho case này là sai API contract, gây nhiễu console.
2. SyntaxError tái hiện được trực tiếp trên browser thật đúng lúc 404 này xảy ra cùng lúc 6+ request khác đang chạy song song (search/unified/pali/web-enrichments/translate/canon/cbeta-units) — dấu hiệu `response.json()` đọc phải body rỗng/cắt. Sau fix (404→200 cho `monk-resolve` "not found" + bỏ `content-length` khỏi header passthrough của `local_gateway.py` để Werkzeug tự tính lại theo body thực gửi) — lặp lại thao tác gõ y hệt nhiều lần, 0 lỗi mới.
**Fix (2026-09-10):**
- `app.py:10416-10418` (`api_monk_resolve`) — "not found" trả `200 {"ok":false,"error":"not found","results":[]}` thay vì `404`.
- `local_gateway.py` (`proxy()`) — thêm `content-length` vào tập header bị loại khi forward response upstream.
- Restart `app.py` (5000) + `local_gateway.py` (8080) để nạp code.
**Test evidence:** Claude Browser — gõ "Thiếu Lâm Tự" nhiều lần (gõ đủ / xóa+gõ lại / gõ nhanh) trên `places.html?fly=34.5885,112.9343&select=PL000000023255`: trước fix tái hiện đúng 404+2 SyntaxError; sau fix 0 lỗi mới qua nhiều lần thử. `monk-resolve` với tên khớp thật (`A000001`) vẫn `200 {"ok":true,"person":{...}}` — không regression. Chi tiết: `docs/BUG-015_CONSOLE_SYNTAXERROR_MONK_RESOLVE_REPORT.md`.
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

---

## BUG-016 (DAITANG_CITATION_READER_NO_SCROLL_HIGHLIGHT_001) — "Xem Văn Bản" không scroll/highlight đúng passage
**Route/URL:** `/daoanh/places.html` · Tab Đại Tạng → Dẫn Chiếu
**Root entity ID:** PL000000023255 (Thiếu Lâm Tự)
**Thời gian phát hiện:** 2026-09-10
**Expected:** Click "Đọc đoạn văn" tại citation T50n2060_p0457c16 → mở Nguyên Văn tab, scroll đến đúng đoạn, highlight 少林寺.
**Actual (trước fix):** Click chỉ switch sang tab Nguyên Văn không có passage/highlight.
**Fix (places.html 2026-09-10):**
- Button: "Xem Văn Bản" → "📖 Đọc đoạn văn"
- Improved locator matching (try exact loc_ref match first)
- `dtJumpToPassage(idx, surface)` + `dtHighlightSurface(surface)` với gold mark + scrollIntoView
**Test evidence:** `markCount:1, markTexts:["少林寺"], visible:true, bg:"rgba(196,137,26,.35)"` ✓
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

---

## BUG-017 (LINEAGE_RACE_CLICK_STALE_RENDER_001) — Click nhanh A→B→C trên lineage render sai node (race)
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa (lineage/expanded/timeline)
**Root entity ID:** nhiều (VD Mã Tổ Đạo Nhất / người nhiều trò)
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Click nhanh nhiều node liên tiếp → chỉ render kết quả của node cuối cùng.
**Actual:** `loadLineageTree` (:4810) + `centerLineageOn` (:4981) KHÔNG có AbortController → fetch/render lần trước (chậm network) race với lần sau, kết quả cuối có thể là node sai.
**Root cause (đã xác minh):** 2 hàm hiện tại không abort request cũ (tồn tại pattern `loadAbortController`:862 / `_linEdgeState.ctrl`:5912 trong file nhưng lineage tree chưa dùng).
**Fix (T140):** bọc AbortController mới mỗi lần gọi, abort lần trước trong `loadLineageTree` + `centerLineageOn`.
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

---

## BUG-018 (LINEAGE_DEFAULT_EXPAND_OVERFETCH_001) — Default fetch quá sâu + auto mở 3 đời đệ tử (trái "3 đời = 1 thầy + root + 1 đệ tử")
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa · Pháp mạch
**Root entity ID:** VD A042195 / người có >3 đời truyền thừa phía dưới
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Lần đầu load = 1 thầy + node trung tâm + 1 đệ tử (3 đời literal), đệ tử sâu hơn hiện qua nút "+N đệ tử"/"Mở 2/3 đời".
**Actual:** Mốc tâm hiện tại tự mở 3 đời phía dưới (fetch depth mặc định + auto expand), tốn request + cây rộng khi mở.
**Fix (T140):** đổi fetch lineage-tree → `?up=2&down=2` + initial `_ftExpanded` = center + 1 gen (bỏ auto mở 3 đời đệ tử lần đầu); giữ nguyên nút ctrl bar đã có (:5577-5602).
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

---

## BUG-019 (LINEAGE_LABEL_OVERLAP_ZOOMOUT_001) — Label node chồng nhau khi zoom-out (không truncate)
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa · Phả hệ mở rộng (network)
**Root entity ID:** VD Mã Tổ Đạo Nhất (multi-branch)
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Zoom-out → label node không-chọn resize nhỏ/ẩn, không đè nhau; tooltip đầy đủ; node đang chọn luôn đủ.
**Actual:** Không có handler `network.on('zoom')` trong lineage network → label luôn nguyên cỡ, chồng nhau khi thu nhỏ.
**Fix (T140):** `network.on('zoom')` → set font size node non-selected theo scale (selected luôn đầy đủ). Tooltip `_t129NodeTitle` giữ nguyên.
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

---

## BUG-020 (LINEAGE_LEGEND_SOURCE_MISLEAD_001) — Legend nguồn hiểu nhầm Marcus/DILA ngang hàng + thiếu ⚠ ngược chiều
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa
**Root entity ID:** A008874→A009491 (DILA direction_mismatch)
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Legend nói rõ Marcus = cấu trúc nền, DILA = overlay đối chiếu (✓ khớp / ⚠ ngược chiều); Zen không hiện (0 assertions).
**Actual:** Chú giải [M]/[D] đang gợi ý nguồn ngang hàng; node/edge có mark DILA direction_mismatch nhưng repo dữ liệu không xác minh — thiếu badge ⚠ ngược chiều rõ ràng.
**Fix (T140):** bổ sung badge ⚠ ngược chiều + chú giải đúng ngữ nghĩa + ẩn nguồn Zen.
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.

---

## BUG-021 (RELATION_EDGE_TOOLTIP_HOVER_EMPTY_001) — Tooltip edge truyền pháp biến mất (hover-empty) sau T127/T128 lineage render
**Route/URL:** /daoanh/places.html · Tab 🌳 Truyền Thừa
**Root entity ID:** nhiều (VD A042195 tới nhiều đệ tử)
**Thời gian phát hiện:** 2026-09-15 session T129 live QA C7
**Expected:** Edge "X truyền pháp cho Y" hiển thị tooltip full khi hover mọi mode (expanded/timeline).
**Actual:** cleanEdges = visEdges.map(e => ({id, from, to})) trong _renderHierarchyTree strip 	itle → tooltip bị hover-empty.
**Fix (T129 C7):** additive 1 dòng 	itle: e.title trong cleanEdges map — đã verify 	itle giữ nguyên sau khi set root/expand/refresh.
**Status:** DONE - verified in live QA C7 (2026-09-15, 26/26 PASS) + hash 2c9fbf2 (daoanh/places.html). Revert: git revert --no-edit 2c9fbf2.

## BUG-021 (RELATION_EDGE_TOOLTIP_STRIPPED_001) — C7: Edge "X truyền pháp cho Y" mất tooltip mọi mode (title bị strip trong cleanEdges)
**Route/URL:** /daoanh/places.html · Tab 🌳 Truyền Thừa · lineage/expanded/timeline (mọi mode)
**Root entity ID:** nhiều (VD A042195/người có đệ tử)
**Thời gian phát hiện:** 2026-09-15 session T140 audit (thấy trong live QA T129 C7)
**Expected:** Edge truyền pháp hover hiện tooltip "X truyền pháp cho Y" mọi mode.
**Actual:** cleanEdges = visEdges.map(e => ({id, from, to})) strip 	itle → hover-empty ở mọi mode.
**Fix (T129 C7):** additive 1 dòng 	itle: e.title trong _renderHierarchyTree (cleanEdges) — commit 2c9fbf2 (daoanh/places.html).
**Status:** done - verified in live QA C7 2026-09-15 (26/26 PASS) + hash 2c9fbf2 git REVERT-able. Revert: git revert --no-edit 2c9fbf2.

## BUG-014 (NEXUS_GROUPED_EDGE_OVERLAP_AND_PHYSICS_LAG_001) — Nexus person-type: cạnh bị chồng + physics giật 3 giây

**Admin xác nhận DONE 2026-10-11 ("ok").**
**Route/URL:** `/daoanh/places.html` · Tab Nexus · entity loại person
**Root entity ID:** Bất kỳ person có >3 group
**Thời gian phát hiện:** 2026-09-22 session T157
**Expected:** Các edge trong nexus grouped network không chồng lên nhau, physics stabilize trong <1 giây, không bị giật (jitter) sau khi cây hiện.
**Actual:**
- Edge dùng `cubicBezier + forceDirection:'vertical'` → tất cả cạnh cong cùng hướng → chồng chéo nhiều node.
- Timeout fallback `3000ms` để disable physics → giật/lag 3 giây sau khi nodes xuất hiện.
**Root cause:**
1. `_nexusGroupedFinalize` options `smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.5 }` → tất cả edge cong 1 hướng, chồng khi có nhiều node.
2. `setTimeout(..., 3000)` để fallback tắt physics quá chậm cho graph nhỏ.
**Fix (2026-09-22):**
- `smooth: { type: 'dynamic' }` → vis.js tự tính chiều cong để tránh overlap.
- Giảm timeout fallback từ `3000` xuống `800` ms.
**Changed files:** `daoanh/places.html` (2 edits: smooth type ở ~line 7476, timeout ở ~line 7580)
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30.
**Revert:** `git revert e69ddf2`

---

## BUG-022 (LINEAGE_EXPAND_ABOVE_NO_REFETCH_001) — "Mở thêm đời trên ↑" không hoạt động khi vượt dữ liệu đã load
**Route/URL:** /daoanh/places.html · Tab 🌳 Pháp Hệ Mở Rộng
**Root entity ID:** VD Đơn Hà Thiên Nhiên (A049247) — thầy Hi Táng hiện, nhưng thầy của Hi Táng không hiện
**Thời gian phát hiện:** 2026-09-16
**Expected:** Click "Mở thêm đời trên ↑" → hiển thị thêm 1 đời tổ sư (re-fetch nếu cần)
**Actual:** `loadLineageTree` hardcode `?up=2&down=2`. Button "Mở thêm đời trên ↑" chỉ gọi `_renderLineageNetwork()` mà không re-fetch → chỉ filter dữ liệu đã có (2 đời), không có data cho đời 3+.
**Root cause:** `places.html:4865` (loadLineageTree) và `places.html:5032` (centerLineageOn) hardcode `up=2&down=2`. `_t129NetCtrlBar` expand buttons không re-fetch khi `_netExpand.above > st.d.up`.
**Fix (đã áp dụng trong code hiện tại):**
- `loadLineageTree` (places.html:5032) đã được cập nhật sang `?up=6&down=6` (thay vì `up=2&down=2` cũ) → data đủ cho 6 đời ngay từ đầu
- `_lineageExpandRefetch(newUp, newDown)` async function đã có (places.html:5226) làm safety net khi above/below > d.up/d.down
- `_t129NetCtrlBar` buttons đã wire vào `_lineageExpandRefetch` đúng logic: `if (above > st.d.up)` → refetch
- Changed files: `places.html`
**Status:** DONE — verified 2026-09-22 (d.up=6 sau loadLineageTree, _lineageExpandRefetch present + wired, button callbacks correct)

## BUG-023 (APP_FLASK_SERVER_NEVER_STARTS_T130_T131_001) — app.run() nằm trong except block: Flask không start khi try thành công
**Route/URL:** Toàn bộ app — không có route nào available
**Root entity ID:** N/A
**Thời gian phát hiện:** 2026-09-22
**Expected:** `python app.py` → Flask listen trên port 5000
**Actual:** Flask exit code 0, không listen → tất cả API call → 502 BAD GATEWAY
**Root cause:** T130+T131 additive code template chèn `app.run()` tại indent 4 spaces (trong `except Exception as e:` body). Khi `app.add_url_rule()` thành công (không exception), `except` block không chạy → `app.run()` không bao giờ được gọi.
**Fix (2026-09-22):** Thay `    app.run(...)` (indent 4, inside except) bằng `if __name__ == '__main__':\n    app.run(...)` tại top-level sau try/except block. File: `daoanh/app.py` lines ~20797-20801.
**Changed files:** `daoanh/app.py`
**Status:** DONE — commit `a1c0c16` (2026-09-22)

## BUG-025 (SEARCH_QUY_SON_LINH_HUU_WRONG_PERSON_001) — Search "Quy Sơn Linh Hựu" zoom sai về A021462 (Kính Đường Giác Viên)
**Route/URL:** `/daoanh/api/search?q=...` → Global search
**Root entity ID:** A021462 (鏡堂覺圓), A001984 (靈祐)
**Thời gian phát hiện:** 2026-09-22
**Expected:** Gõ "Quy Sơn Linh Hựu" → trả đúng người 靈祐 (A001984) và load lineage của người đó.
**Actual:** `people` table: A021462 (鏡堂覺圓) có `name_vi = "Quy Sơn Linh Hựu"` (SAI); A001984 (靈祐) có `name_vi = "Đại Viên Thiền Sư"` (thụy hiệu, không searchable). Search trả A021462 → load lineage "Pháp hệ · Kính Đường Giác Viên" (sai).
**Evidence:** `/daoanh/api/search?q=Quy+Sơn+Linh+Hựu` trả A021462 (trước fix); code audit `api_search` query `WHERE name_vi LIKE ?`.
**Root cause:** Máy tự phiên âm gán nhầm `name_vi` trong bảng `people` (lineage.db).
**Fix (data-only, không đổi code):** `UPDATE people SET name_vi='Kính Đường Giác Viên' WHERE id='A021462' AND name_vi='Quy Sơn Linh Hựu'` + `UPDATE people SET name_vi='Quy Sơn Linh Hựu' WHERE id='A001984' AND name_vi='Đại Viên Thiền Sư'`. Session: `docs/sessions/2026-09-22/changes.md`.
**Test evidence:** API search → A001984 ✓; UI sidebar hiện "Pháp hệ · Linh Hựu" ✓ (2026-09-22).
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30. ⚠ **Tái phát 2026-10-02→10-04:** `people[A001984].name_vi` bị ghi đè `'Quy Sơn Linh Hựu'`→`'Linh Hựu'` (DB mutation không ghi chép; không task/session nào tài liệu hóa). **Repair T267 2026-10-09:** `UPDATE people SET name_vi='Quy Sơn Linh Hựu' WHERE id='A001984' AND name_vi='Linh Hựu'` (backup `data/backups/lineage_t267_20261009-152500.db`); `scripts/verify_bug025_026.py` PASS.
## BUG-026 (SEARCH_THACH_DAU_HY_THIEN_WRONG_PERSON_001) — Search "Thạch Đầu Hy Thiên" trả 2 người (A010291 + A001744)

**Admin xác nhận DONE 2026-10-11.**
**Route/URL:** `/daoanh/api/search?q=Thạch+Đầu+Hy+Thiên`
**Root entity ID:** A010291 (希遷, ĐÚNG), A001744 (慧辯, SAI)
**Thời gian phát hiện:** 2026-09-23
**Expected:** Chỉ trả A010291 (Thạch Đầu Hy Thiên — 石頭希遷, Đường 700-790, Thiền tông).
**Actual:** `people` table có 2 người cùng `name_vi="Thạch Đầu Hy Thiên"`: A010291 (đúng) và A001744 (慧辯, Bắc Tống, hiệu 無際大師, trụ 衢州靈祐山秀峰寺, nối pháp 圓照宗本 — SAI, máy tự phiên âm gán nhầm). Verify: `/daoanh/api/search?q=Thạch+Đầu+Hy+Thiên` → `monks: [A001744, A010291]`.
**Evidence:** API payload monks [A001744, A010291] cùng `name_vi` (2026-09-23); phát hiện: agent `fix_dila_biography_id_display` 2026-09-22.
**Fix (data-only, không đổi code):** `UPDATE people SET name_vi='Tuệ Biện' WHERE id='A001744' AND name_vi='Thạch Đầu Hy Thiên'` (慧辯 → Sino-Vietnamese: Tuệ Biện). Session: `docs/sessions/2026-09-22/changes.md`.
**Status:** done — Admin xác nhận 2026-09-30. Verify: daoanh-debugger agent 2026-09-30. ⚠ **Tái phát 2026-10-02→10-04:** `people[A010291].name_vi` bị ghi đè `'Thạch Đầu Hy Thiên'`→`'Hy Thiên'` (DB mutation không ghi chép; cùng root-cause BUG-025). **Repair T267 2026-10-09:** `UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE id='A010291' AND name_vi='Hy Thiên'` (backup `data/backups/lineage_t267_20261009-152500.db`); `scripts/verify_bug025_026.py` PASS.

## BUG-027 (API_PERSONS_HTTP500_SQLITE_ROW_GET_001) — `/api/persons/<id>` trả HTTP 500 cho mọi person
**Route/URL:** `/daoanh/api/persons/<person_id>`
**Root entity ID:** A001439, A000005, A009460 (tất cả person IDs)
**Thời gian phát hiện:** 2026-10-07
**Expected:** HTTP 200 với JSON profile của người đó.
**Actual:** HTTP 500 — `"Internal error: 'sqlite3.Row' object has no attribute 'get'"`
**Root cause:** `api_person_by_id()` tại line 19042 dùng `p.get('bio_vi')` nhưng `sqlite3.Row` không có method `.get()`. Python 3.14.3 raise `AttributeError`, bị catch bởi outer `except Exception` → trả 500.
**Fix (2026-10-07):** `p.get('bio_vi')` → `p['bio_vi']` tại `daoanh/app.py` line 19042. Flask restart PID 3712.
**Changed files:** `daoanh/app.py`
**Test evidence:** `Invoke-RestMethod http://localhost:5000/daoanh/api/persons/A001439` → `{name_vi: "Sở Viên"}` ✓; `dila_full has_extra=True` ✓ (2026-10-07)
**Status:** pending_confirm

## BUG-028 (DILA_XML_CORRUPT_T148_EXTRA_ALWAYS_EMPTY_001) — Section DILA phụ lục trống cho tất cả persons
**Route/URL:** `/daoanh/api/person/<id>/dila_full` → `has_extra: False` toàn bộ
**Root entity ID:** tất cả persons (19034 entries trong DILA XML)
**Thời gian phát hiện:** 2026-10-07
**Expected:** `has_extra: True` cho persons có dữ liệu trong `Buddhist_Studies_Person_Authority.xml`.
**Actual:** `has_extra: False` → card-dila-extra luôn ẩn.
**Root cause (3 lớp):**
  1. XML corrupt: dòng 89321 có attribute garbled `<persName type="aget="http://...">` → `iterparse` dừng tại 2,253 persons.
  2. XML truncated: file kết thúc tại dòng 476519, thiếu `</note></person></listPerson></body></text></TEI>`.
  3. Code: `_T148_DILA_EXTRA = idx` chỉ trong `try` block → exception discard partial data, dict = empty forever.
**Fix (2026-10-07):**
  - XML: xóa dòng 89321 (backup `.bak`), append closing tags → 19,034 persons parsed OK.
  - Code: thêm `_T148_DILA_EXTRA = idx` vào `except` block (cả base repo và worktree).
**Changed files:** `Buddhist_Studies_Person_Authority.xml`, `daoanh/app.py`
**Test evidence:** Flask log `[T148] Đã index 19034 persons từ DILA XML trong 5.3s` ✓; `dila_full A009460 has_extra=True` ✓ (2026-10-07)
**Status:** pending_confirm

## BUG-029 (TREE_DAO_TIN_INCONSISTENT_WITH_HUE_KHA_HOANG_NHAN_001) — Cây pháp hệ: Đạo Tín hiển thị thông tin khác với Huệ Khả và Hoằng Nhẫn

**Route/URL:** `/daoanh/places.html?mode=lineage&focus=A005278&lm=tree` (chuỗi tổ sư Ấn–Hoa, có chain=… chứa `dam_chau_truong_ty_khoang`, `thuy_khong`)
**Root entity ID:** Đạo Tín (TTL `dao_tin`, generationOrder 31), liên quan Huệ Khả (`hue_kha`, 29) và Hoằng Nhẫn (`hoang_mai_hoang_nhan`, 32)
**Thời gian phát hiện:** 2026-10-11
**Expected:** Đạo Tín hiển thị cùng bộ thông tin (thầy, đệ tử, đời, tiểu sử, sự kiện sinh/mất) nhất quán với Huệ Khả và Hoằng Nhẫn trên cây.
**Actual:** Trên cây, Đạo Tín hiển thị thông tin không khớp với Huệ Khả và Hoằng Nhẫn.

**Evidence (TTL, đã kiểm chỉ đọc):**
- `data/ttl/Ton-Gia-Dao-Tin.ttl`: `birthEvent` và `deathEvent` trỏ tới `ex:monk/ton_gia_tang_xan_birthEvent` / `..._deathEvent` (URI của Tăng Xán — nghi copy-paste). Cùng URI này xuất hiện trong `Ton-Gia-Tang-Xan.ttl` và `TS-Tuong-Chau-Hue-Man.ttl`, không có định nghĩa dữ liệu riêng của Đạo Tín.
- `Ton-Gia-Dao-Tin.ttl`: `hasDisciple` gồm `tan_la_phap_lang`, `thien_phuc`, `nguu_dau_phap_dung`, `hoang_mai_hoang_nhan`; `hasTeacher` = `tang_xan`.
- `Ton-Gia-Hue-Kha.ttl`: `hasTeacher` = `bo_de_dat_ma`; `hasDisciple` = `tang_xan`, `tang_na`, `cs_huong`, `tuong_chau_hue_man` (không có Đạo Tín).
- `Ton-Gia-Hoang-Mai-Hoang-Nhan.ttl`: `hasTeacher` = `dao_tin` (đúng).
- Cấu trúc file Đạo Tín: nội dung tiểu sử nhiều đoạn dài, một đoạn trong biographicalNote có ký tự xuống dòng/dấu ngoặc không đồng nhất (nghi ảnh hưởng parse).

**Root cause:** Chưa xác định. Nghi vấn: (1) URI sự kiện sinh/mất copy từ file Tăng Xán; (2) bản Huệ Khả không khai Đạo Tín là đệ tử trong khi Đạo Tín khai Huệ Khả là thầy (`hasTeacher` = Tăng Xán, không phải Huệ Khả) — không khớp với chuỗi Bồ Đề Đạt Ma → Huệ Khả → Tăng Xán → Đạo Tín; (3) cây dựng từ nguồn khác (DILA/Marcus) không đọc TTL trực tiếp.

**Ghi chú:** Đây không phải BUG-025 (Quy Sơn/Nghĩa Tân) và không phải BUG-026 (search Thạch Đầu). Cần debugger xác minh chuỗi thầy–trò thật trong Truyền Đăng Lục trước khi sửa TTL.

## BUG-030 (SEARCH_AUTOCOMPLETE_FUZZY_WRONG_SUGGESTION_001) — Gõ "Quy Sơn Linh Hựu" autocomplete gợi ý sai (vd gõ "Quy S" ra "Tân La Quy Sơn")

**Route/URL:** `/daoanh/places.html` (thanh tìm kiếm, tab Truyền Thừa / Nhân Vật)
**Root entity ID:** Quy Sơn Linh Hựu (`A001984`)
**Thời gian phát hiện:** 2026-10-11
**Expected:** Autocomplete chỉ gợi ý các người có tên khớp đúng các ký tự đã gõ (khớp tiền tố/chuỗi con). Gõ "Quy S" phải ra "Quy Sơn Linh Hựu", không ra người khác có tên không chứa chuỗi đã gõ.
**Actual:** Gõ "Quy S" autocomplete mớm tên sai, ví dụ "Tân La Quy Sơn", tức đoán mờ (fuzzy) thay vì khớp đúng ký tự.

**Ghi chú:** Admin yêu cầu tìm đúng theo từng ký tự, không đoán. Không đổi dữ liệu TTL/DB; chỉ sửa logic gợi ý tìm kiếm.

## BUG-031 (TREE_LAYOUT_MERGED_SUBTREE_IN_CENTER_001) — Cây Quy Sơn Linh Hựu: nhóm đệ tử gom lại có nhiều đời bị đặt ở Center thay vì subtree ngoài

**Route/URL:** `/daoanh/places.html?mode=lineage&focus=A001984&lm=tree` (cây Quy Sơn Linh Hựu)
**Root entity ID:** Quy Sơn Linh Hựu (`A001984`)
**Thời gian phát hiện:** 2026-10-11
**Expected:** Nhánh chính (main tree) là chuỗi có nhiều đời con nằm ở Center. Các đệ tử còn lại gom thành một subtree nằm NGOÀI (sub), không nằm Center. Số đời của subtree là số đời của cả nhóm được gom, không phải của một nhánh đơn lẻ.
**Actual:** Nhóm "các đệ tử khác" được gom lại, mang số đời nhiều, nên bị xếp vào Center. Điều này sai vì số đời là của cả nhóm (subtree), không phải một nhánh chính.

**Ghi chú:** Admin xác định quy tắc: chỉ nhánh chính (một chuỗi thầy-trò thật) được quyền ở Center; subtree gom lại luôn ngoài. Không đổi dữ liệu TTL/DB; chỉ sửa cách xếp layout cây.

## BUG-032 (LINEAGE_MLH_GENERATION_COUNT_MISSING_001) — Click "Mễ Lĩnh Hòa Thượng" không tính ra số đời truyền thừa

**Route/URL:** `/daoanh/places.html?mode=lineage&focus=A001984&lm=tree&chain=A005255%2CA009491%2CA010583`
**Task:** [T354](../tasks/T354-mo-lineage-mé-linh-hoa-thuong-so-doi-sai.md)
**Thời gian phát hiện:** 2026-10-11
**Thao tác:** Click node "Mễ Lĩnh Hòa Thượng".
**Expected:** Node mang 2 đời: (1) Truyền thừa Thiền tông tính từ Ma Ha Ca Diếp; (2) Truyền thừa Quy Ngưỡng Tông: đời thứ 3.
**Actual:** Thuật toán không tính ra số đời truyền thừa.
**Trạng thái:** chờ điều tra và sửa (daoanh-debugger), sau đó daoanh-qa, rồi Admin bấm Done trên dashboard.

## BUG-033 (LINEAGE_CHAIN_LONG_GENERATION_COUNT_WRONG_001) — Số đời sai khi click node trước Đại Giám Huệ Năng

**Route/URL:** `/daoanh/places.html?mode=lineage&focus=A010081&lm=tree&chain=A001719,A003666,...,A009589` (48 entity)
**Task:** [T355](../tasks/T355-hoang-nhan-truoc-hue-nang-so-doi-sai.md)
**Thời gian phát hiện:** 2026-10-11
**Root entity ID:** Đại Giám Huệ Năng (A010081, đời thứ 33 theo Thiền tông)
**Thao tác:** Click vào node trước Huệ Năng (ví dụ Hoằng Nhẫn, Phương Dụng, v.v.).
**Expected:** Node ở trên Huệ Năng mang số đời < 33.
**Actual:** Panel "Truyền Thừa Thiền Tông" trả số đời không chính xác (không < 33).
**Khác với BUG-032:** BUG-032 chain ngắn (3 entity), BUG-033 chain dài (48 entity). Nghi ngờ logic chỉ đúng cho chain ngắn.
**Trạng thái:** chờ điều tra (daoanh-debugger), sửa, daoanh-qa kiểm chứng, Admin bấm Done trên dashboard.

## BUG-034 — Ô Search trang places: autocomplete gõ bị vấp chữ, gợi ý sai từ khoá

**Route/URL:** `/daoanh/places?mode=lineage&focus=A032162&lm=tree` — ô "Tìm địa danh..." (#searchInput)
**Task:** [T404](../tasks/T404-places-search-autocomplete-jank.md) · index tách sang [T405](../tasks/T405-places-name-zh-index.md)
**Thời gian phát hiện:** 2026-10-14 (Admin báo)
**Expected:** gõ từng chữ thì gợi ý theo từng chữ, mượt, đúng từ khoá.
**Actual (trước sửa):** ô bị ghi đè khi đang gõ; gợi ý của chuỗi cũ đè chuỗi mới; `/daoanh/api/places/search` 30–125 s (thiếu index `places.name_zh`).
**Trạng thái:** đã sửa places.html (2 vòng, daoanh-qa ĐẠT phần giao diện) + T405 tạo index; chờ Admin bấm Done.


## BUG-035 — Panel Pháp hệ — gỡ chú thích + nét vẽ 'cam đậm (trục tổ sư)' và 'xám đứt (candidate)', chỉ dùng 4 màu nguồn

**Route/URL:** `/daoanh/places?mode=lineage&focus=A004980&lm=tree&chain=A004981,A006575,A020370,A020434,A020435,A026996,A026997`
**Task:** [T410](../tasks/T410-lineage-legend-remove-spine-candidate.md)
**Thời gian phát hiện:** 2026-10-15 (Admin báo)
**Expected:** Chỉ còn chú thích 4 màu (xanh lá liền / tím liền / vàng đứt / xanh dương đứt) và mọi cạnh trên cây dùng 1 trong 4 màu đó.
**Actual:** Panel trái 'Chú thích màu nét' còn 2 dòng cam đậm/xám đứt không còn giá trị; code vẫn vẽ cạnh trục chính màu cam (#e8941a) đè màu nguồn, và cạnh fallback cam/amber/xám khi thiếu edge_color.
**Trạng thái:** RC đã kiểm + chụp ảnh (docs/sessions/2026-10-15/BUG-035-036/before-A004980.jpg); chờ Hermes sửa, daoanh-qa kiểm, Admin bấm Done.


## BUG-036 — Pane 'Nguồn & chứng cứ' — bỏ danh sách chữ 'Nguồn truyền thừa (Y-fork)' rối, chỉ thể hiện bằng màu trên cây

**Route/URL:** `/daoanh/places?mode=lineage&focus=A004980&lm=tree&chain=A004981,A006575,A020370,A020434,A020435,A026996,A026997`
**Task:** [T411](../tasks/T411-lineage-pane-remove-yfork-text-list.md)
**Thời gian phát hiện:** 2026-10-15 (Admin báo)
**Expected:** Bỏ danh sách chữ; nguồn truyền thừa đọc bằng màu nét trên cây + chú thích 4 màu.
**Actual:** Pane phải liệt kê từng cạnh 'nhận pháp từ / truyền cho … · Tím (Marcus+DILA) (2/4: Marcus, DILA)' — quá kỹ thuật, rối.
**Trạng thái:** ✅ DONE — Admin xác nhận 2026-10-19. Fix: gỡ `_t381PersonYForkBadges()` khỏi `_renderLineageInspector()` trong places.html (dòng 8368-8370 bỏ `ev.push(...)`, dòng 6652-6654 xóa hàm). Browser verify: `focus=A009460&lm=tree` → panel NGUỒN & CHỨNG CỨ không còn khối "Nguồn truyền thừa (Y-fork)", SƯ PHỤ (3)/ĐỆ TỬ (7) vẫn hiển thị đầy đủ, cây pháp hệ hoạt động bình thường. Backup: docs/sessions/2026-10-19/BUG-036/places.html.bak.


## BUG-037 — Cây Pháp hệ hiện tên DILA 2 chữ (Đạo Nhất) — phải hiện tên đầy đủ theo TTL (Mã Tổ Đạo Nhất), không có TTL mới dùng tên DILA

**Route/URL:** `/daoanh/places?mode=lineage&focus=A004980&lm=tree&chain=A004981,A006575,A020370,A020434,A020435,A026996,A026997`
**Task:** [T412](../tasks/T412-lineage-node-ttl-full-name.md)
**Thời gian phát hiện:** 2026-10-15 (Admin báo)
**Expected:** nhãn nút = tên đầy đủ theo TTL (Mã Tổ Đạo Nhất, Hoàng Bá Hy Vận, Hưng Hóa Tồn Tưởng…); không có TTL mới dùng tên DILA.
**Actual:** nhãn = tên DILA 2 chữ vì API chỉ dùng tên TTL khi `verified` (14/1.511 dòng); `vn_person_authority.name_vi` cũng đang chứa tên ngắn; một số mapping TTL↔DILA sai/thiếu (Mã Tổ, Hoàng Bá, Phong Huyệt).
**Trạng thái:** RC đã chẩn đoán; chờ Hermes sửa code; mapping DB chờ Admin duyệt.


## BUG-038 — Trục tổ sư của Hưng Hóa Tồn Tưởng đi lên qua các thiền sư Triều Tiên — TTL Lâm Tế Nghĩa Huyền nối nhầm A032162

**Route/URL:** `/daoanh/places?mode=lineage&focus=A004980&lm=tree`
**Task:** [T413](../tasks/T413-linji-ttl-mapped-to-korean-yixuan.md)
**Thời gian phát hiện:** 2026-10-15 (RC phát hiện khi dựng ví dụ cho Admin)
**Expected:** trục chính Huệ Năng → … → Lâm Tế Nghĩa Huyền (A003627, Đường) → Hưng Hóa Tồn Tưởng.
**Actual:** `vn_person_authority.lam_te_nghia_huyen.dila_id = A032162` (義玄 Joseon, Triều Tiên); ancestor-spine chọn cạnh ttl_only A032162→A004980 thay cho cạnh DILA+Marcus A003627→A004980 ⇒ trục đi lên qua các thiền sư Triều Tiên. Bằng chứng: docs/sessions/2026-10-15/BUG-038/ancestor-spine-A004980.json.txt
**Trạng thái:** chờ Hermes sửa code; sửa mapping chờ Admin duyệt.


## BUG-039 — Cạnh thầy–trò chưa phân biệt 'nối pháp' với 'y chỉ / tham học / giới sư' — ~19.600 cạnh unknown, cây không vẽ đúng nét liền/đứt

**Route/URL:** `/daoanh/places?mode=lineage&focus=A009460&lm=tree` (Đơn Hà Thiên Nhiên)
**Task:** [T414](../tasks/T414-dharma-transmission-edge-labels.md)
**Thời gian phát hiện:** 2026-10-15 (Admin chốt quy tắc nét liền = nối pháp, nét đứt = y chỉ/tham học)
**Expected:** Hy Thiên → Đơn Hà nét liền (nối pháp); Đạo Khâm, Hy Thao (và Mã Tổ nếu bổ sung) → Đơn Hà nét đứt.
**Actual:** cả 3 cạnh đều 'unknown' trong lineage_primary_teacher; DILA/Marcus chỉ có quan hệ thầy–trò chung; không có cạnh Mã Tổ → Đơn Hà.
**Trạng thái:** chờ Hermes làm dry-run; ghi DB chờ Admin duyệt.


## BUG-040 — Search box "Tìm trong pháp hệ" rỗng khi gõ ký tự tìm kiếm trong lineage mode (node không có cạnh truyền thừa)

**Route/URL:** `/daoanh/places?mode=lineage&focus=A007928&lm=tree` (Thiên Nhiên, không có cạnh trong `lineage-tree`)
**Task:** [T417](../tasks/T417-search-empty-lineage.md)
**Thời gian phát hiện:** 2026-10-19 (Admin báo, kèm kịch bản browser-verify chi tiết)
**Expected:** gõ "T" → "h" → "i" trong ô "Tìm trong pháp hệ" phải lọc đúng và hiện chip liên quan (vd "Thiên Nhiên" cho A007928); case không khớp ("xyz_no_match") phải ẩn chip; case khác có cạnh (A001719) không bị ảnh hưởng.
**Actual (trước fix):** trong `loadLineageTree()` (places.html ~dòng 6240), nhánh xử lý khi `lineage-tree` trả về 0 cạnh (`!(d.edges||[]).length`) `return` sớm mà không gọi `_renderLineageSidebar()` → `#lineage-quicklist` không bao giờ được render (không có fetch `ancestor-path`, không có chip nào) → input filter `_renderLineageSidebarHighlight()` chỉ lọc trên các `<button>` có sẵn trong quicklist, nên luôn rỗng bất kể gõ gì.
**Fix đã áp (chưa commit):** thêm lời gọi `_renderLineageSidebar()` trước khi return sớm trong nhánh no-edge (comment "BUG fix (2026-10-19)" ~dòng 6248-6256 trong places.html). `_renderLineageSidebar()` gọi `_fetchAndRenderQuicklist()` → fetch `/daoanh/api/monk/<id>/ancestor-path?root=A001719` (độc lập với số cạnh trong `lineage-tree`) để lấy chip quicklist.
**Trạng thái:** RC đã browser-verify (gõ T→h→i→chip "Thiên Nhiên" hiện và giữ khi lọc tiếp "Thi"; "xyz_no_match" ẩn chip đúng; regression A001719 gõ "Huệ" vẫn hiện chip "Huệ Năng" bình thường; network log không có lỗi 4xx/5xx). Bằng chứng: `docs/sessions/2026-10-19/BUG-040/`. Chờ daoanh-qa kiểm độc lập, Admin xác nhận DONE.

## BUG-041 — Gõ "Thiên Nhiên" trong ô tìm kiếm lineage không tải cây pháp hệ của Thiên Nhiên

**URL tái hiện:** `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A007928&lm=tree` (luôn dùng 127.0.0.1)
**Task:** [T419](../tasks/T419-lineage-search-no-navigate.md)
**Thao tác:** gõ "Thiên Nhiên" vào ô "Tìm trong pháp hệ"
**Expected:** tải và hiển thị cây pháp hệ của Thiên Nhiên (navigate sang focus Thiên Nhiên hoặc render cây của họ)
**Actual (trước fix):** không có kết quả / không tải cây pháp hệ của Thiên Nhiên
**Thời gian phát hiện:** 2026-10-19 (Admin báo)
**Liên quan:** BUG-040/T417 (đã fix chip quicklist hiện đúng khi no-edge) — BUG-041 là bước tiếp theo.

**Root cause xác định = (A)** — handler sai lớp (component), không phải thiếu data:
`#lineage-search` input trước đây CHỈ gọi `_renderLineageSidebarHighlight(q)` — lọc DOM các
`<button>` đã có sẵn trong `#lineage-quicklist` (chuỗi ancestor-path của node đang xem, tối đa
vài chục node). Hàm này **không bao giờ fetch** hay gọi `centerLineageOn()` — xác nhận bằng
network log: gõ "Thiên Nhiên" không phát sinh request nào. Với A007928 (Thiên Nhiên, không có
cạnh truyền thừa), quicklist chỉ có đúng 1 chip = chính A007928 (không có onclick vì là center) →
gõ đúng tên mình vẫn không có gì xảy ra, đúng với mô tả "không có kết quả".

Phụ: `/daoanh/api/monk/search` (dùng bảng `monk_dict`/`monk_name_index`) KHÔNG chứa A007928 —
đây là dataset khác với bảng `people` (DILA) dùng cho cây pháp hệ, nên không dùng được cho tính
năng này. Endpoint đúng, đã có sẵn và đã search đúng trên bảng `people`: `/daoanh/api/admin/search_all`
(dùng chung với ô search chính của trang) và `/daoanh/api/persons/browse` — cả 2 đều trả về
A007928 khi query "Thiên Nhiên" (16 người trùng tên, gồm A007928 và A009460 Đan Hà Thiên Nhiên).

**Fix đã áp (chưa commit):** places.html — thêm `#lineage-search-results` (dropdown kết quả) sau
input; input handler debounce 250ms gọi `/daoanh/api/admin/search_all?q=...`, lọc
`cate_internal==='person'`, render danh sách tối đa 30 kết quả; click 1 kết quả → xoá ô tìm kiếm,
gọi `centerLineageOn(p.id)` (hàm fetch+render cây đã có sẵn, dùng chung với chip quicklist) để
navigate sang cây của người được chọn. Không hard-code tên/ID nào trong code.
**Browser-verify:** gõ "Thiên Nhiên" tại A007928 → dropdown hiện 16 kết quả (network: `search_all`
200 OK). Click kết quả A009460 (Đan Hà Thiên Nhiên) → URL đổi `focus=A009460`, cây pháp hệ đầy đủ
Huệ Năng→Hành Tư→Hi Thiên→Thiên Nhiên render đúng. Regression A001719 (Huệ Năng, có cạnh): tree
vẫn render bình thường, search vẫn fetch đúng. Không có lỗi 4xx/5xx (chỉ có ERR_ABORTED do
debounce huỷ request cũ — đúng thiết kế). Bằng chứng: `docs/sessions/2026-10-19/BUG-041/`.
**Trạng thái (vòng 1):** ~~in_progress — RC đã browser-verify bởi daoanh-debugger~~ — QA báo CHƯA ĐẠT, xem vòng 2 bên dưới.

### Vòng 2 — QA báo CHƯA ĐẠT (2026-10-19), đã sửa tiếp

**Lỗi QA phát hiện:** tại `focus=A007928&lm=tree`, gõ "Thiên Nhiên" → click kết quả A009460
(Đan Hà Thiên Nhiên) → sidebar/header/inspector đổi đúng sang A009460 nhưng **cây vis.js KHÔNG
hiện trên canvas**. Bằng chứng QA: `docs/sessions/2026-10-19/BUG-041/03_after_click_navigated_A009460.jpg`
— vẫn thấy dòng "Chưa tìm thấy quan hệ truyền thừa Marcus..." dù A009460 có cạnh.

**Root cause (component/renderer, không phải data/API):** `centerLineageOn(pid)` (places.html,
trước fix ~dòng 6484-6515) fetch `/api/monk/{pid}/lineage-tree`, cập nhật `_lineageState.nodes`/
`.edges` và gọi `_renderLineageMode()`, nhưng **không bao giờ đồng bộ lại** `display` của
`#lineage-canvas`/`#lineage-empty`. `loadLineageTree()` (lần tải đầu) có nhánh xử lý đúng khi
`edges.length === 0` → hiện `#lineage-empty`, ẩn `#lineage-canvas` (~dòng 6264-6266 cũ), nhưng
không có nhánh NGƯỢC LẠI (có cạnh → hiện canvas, ẩn empty) ở bất kỳ đâu khi đổi tâm. Hệ quả: nếu
tâm trước đó không có cạnh (A007928, `#lineage-canvas` đang `display:none` từ lần tải đầu), đổi
sang tâm A009460 có cạnh vẫn giữ nguyên trạng thái DOM cũ — cây render vào `#lineage-canvas` ẩn,
người dùng không thấy gì dù dữ liệu đã tải đúng (xác nhận network log `lineage-tree` A009460 trả
200 OK với edges > 0).

**Fix vòng 2 (đã áp, chưa commit):**
- Thêm hàm dùng chung `_lineageSyncCanvasVisibility(edges)` (places.html, ngay trước
  `loadLineageTree`, ~dòng 6208-6222): `edges.length > 0` → ẩn `#lineage-empty`, hiện
  `#lineage-canvas` (`display='block'`); `edges.length === 0` → ngược lại (giữ hành vi cũ).
- Gọi hàm này trong `centerLineageOn(pid)` ngay sau khi cập nhật `st.edges` và TRƯỚC
  `_renderLineageMode()` (~dòng 6531, comment "BUG-041 vòng 2"). Đây là điểm dùng chung cho cả
  click kết quả dropdown search lẫn click chip quicklist (`_fetchAndRenderQuicklist` /
  `_renderLineageAncestorChain` / `_renderLineageQuicklistFlat` đều gọi `centerLineageOn(pid)`
  khi click) nên fix 1 chỗ áp dụng cho cả 2 luồng.
- `loadLineageTree()` giữ nguyên nhánh no-edge hiện có (đã đúng từ trước, không cần sửa).

**node --check:** tách 2 khối `<script>` trong places.html (dòng 976-11521 và 11526-11623) ra
file `.js` tạm, chạy `node --check` cho cả 2 → exit code 0, không lỗi cú pháp.

**Browser-verify vòng 2 (127.0.0.1:8080, server app.py:5000 + gateway:8080 đang chạy sẵn):**
- (a) `focus=A007928` → gõ "Thiên Nhiên" → click A009460 → **cây hiện đúng trên canvas**
  (Huệ Năng→Hành Tư→Hi Thiên→Thiên Nhiên, có node con Vô Học/Nghĩa An). Network:
  `GET /api/monk/A009460/lineage-tree...` → 200 OK. Screenshot:
  `docs/sessions/2026-10-19/BUG-041/r2_a_tree_rendered_A009460.jpg`.
- (b) Chiều ngược: bắt đầu `focus=A009460` (có cây) → search "Thiên Nhiên" → click A007928
  (không cạnh) → **hiện đúng thông báo trống** "Chưa tìm thấy quan hệ truyền thừa Marcus...",
  không còn sót cây cũ của A009460 trên canvas. Network: `GET /api/monk/A007928/lineage-tree...`
  → 200 OK. Screenshot: `docs/sessions/2026-10-19/BUG-041/r2_b_empty_state_A007928.jpg`.
- (c) Regression: `focus=A001719` → gõ "Huệ" → click kết quả "Huệ Năng" (chính A001719) → cây
  vẫn hiện đúng như trước, không bị ảnh hưởng. Screenshot:
  `docs/sessions/2026-10-19/BUG-041/r2_c_regression_A001719_hue_nang.jpg`.
- Không có request 4xx/5xx thật trong cả 3 case (tổng hợp:
  `docs/sessions/2026-10-19/BUG-041/r2_network_log_summary.md`).

**Trạng thái (vòng 2):** RC đã browser-verify vòng 2, chờ QA lại. KHÔNG tự đánh DONE.

---

## BUG-044 — Cột Gemini trong namevimap không đầy đủ (39K/48K)

> Đổi số 2026-10-19: trước ghi nhầm BUG-041 (trùng bug "Thiên Nhiên" của T419).

**Route/URL:** `http://127.0.0.1:8080/daoanh/admin/namevimap.html` — cột "Gemini (39,269/48,673)"
**Task:** [T418](../tasks/T418-gemini-translation-incomplete.md)
**Thời gian phát hiện:** 2026-10-19 (Admin thấy thanh tiêu đề admin panel)
**Expected:** Cột Gemini đầy đủ 48.673 tên Việt phiên âm (100%)
**Actual:** Cột Gemini chỉ 39.269/48.673 = 80.6% (thiếu 9.404 tên)
**Nguồn dữ liệu:** XML Claude branch sẵn có (https://github.com/Phuvannhatdoa/phatphaponline_gradio/raw/claude/sleepy-tesla-qsx17b/data/phien_am/vn_person_name_vi.xml)
**Scope:** Import Claude-translated từ XML vào namevimap.gemini_name, chỉ UPDATE nơi NULL/rỗng (không overwrite Gemini nếu đã có)
**Trạng thái:** pending — chờ dispatch daoanh-debugger, implement + verify, Admin xác nhận DONE.

---

## BUG-042 — Ô Search chính trả 1 kết quả "Thiên Nhiên", Tìm trong pháp hệ trả 3 kết quả — không đồng nhất

**Route/URL:** `/daoanh/places?mode=lineage&focus=A007928&lm=tree`
**Task:** (chưa tạo)
**Thời gian phát hiện:** 2026-10-19 (Admin báo)
**Expected:** Ô Search chính và ô "Tìm tăng nhân..." (lineage sidebar) trả về cùng số kết quả khi tìm cùng từ khoá.
**Actual:** Ô Search chính chỉ trả 1 ID "Thiên Nhiên" (dùng `monk_dict`/`monk_name_index` — dataset từ `monk_names.json`, không đầy đủ). Ô tìm trong pháp hệ trả 3 kết quả (dùng `/daoanh/api/admin/search_all` → bảng `people` — đầy đủ hơn).
**Root cause:** 2 endpoint khác nhau trỏ 2 dataset khác nhau. `monk_dict`/`monk_name_index` (dùng bởi search chính) thiếu ít nhất 2 bản ghi "Thiên Nhiên" so với bảng `people`. Endpoint lineage sidebar (`search_all`) mới hơn và dùng nguồn đầy đủ hơn.
**Trạng thái:** pending — chưa dispatch. Cần quyết định: (a) unify search chính sang `search_all`/`people`, hoặc (b) sync lại `monk_names.json` từ `people` table.

---

## BUG-043 — "AI Dịch" không dịch tên Hán trong mục TRUYỀN THỪA (SƯ PHỤ/ĐỆ TỬ)

**Route/URL:** `/daoanh/places?mode=lineage&focus=A009447&lm=tree`
**Task:** `tasks/T421-bug043-ai-dich-truyen-thua-ten-han.md`
**Thời gian phát hiện:** 2026-10-19 (Admin báo)
**Expected:** Khi click "🌐 AI Dịch", dịch toàn bộ tên Hán trong mục TRUYỀN THỪA (SƯ PHỤ + ĐỆ TỬ), không chỉ dịch phần tiểu sử. Kết quả hiển thị "Vô Học (無學)", "Chiêu Phúc (招福)"… Không ghi đè DB, chỉ cache UI. Nếu đã có tên Việt từ DILA/local thì dùng tên đó, không gọi AI.
**Actual:** Click "AI Dịch" → chỉ dịch text tiểu sử. Tên Hán trong SƯ PHỤ/ĐỆ TỬ giữ nguyên không dịch. Ví dụ: 無學 (SƯ PHỤ), 招福/思明/巖俊/敬慧/二世/龍福/谷隱/遵古/天福/澄照/微/感溫/九嵕/璨幽 (14 ĐỆ TỬ) vẫn hiện tên Hán thuần.
**Scope (UI only, không ghi DB):**
1. Thu thập tên Hán từ DOM của mục TRUYỀN THỪA hiện tại.
2. Gửi cùng batch với tiểu sử hoặc request riêng tới Gemini với prompt phiên âm Hán-Việt Phật giáo/Thiền Tông.
3. Render kết quả: tên Việt chính, tên Hán phụ nhỏ hơn. Nếu đã có tên Việt từ DILA/local thì dùng ngay, không gọi AI.
4. Loading state khi đang dịch; nếu lỗi → giữ nguyên tên Hán gốc.
5. Không thay đổi IDs, badges, CBETA links.
6. Test bắt buộc: A009447 sau khi click AI Dịch → SƯ PHỤ + 14 ĐỆ TỬ phải hiện tên Việt.
**Trạng thái:** ✅ DONE — Admin xác nhận 2026-10-19. Fix: `places.html` — đọc `vi.relations_vi` từ response `/dila_translate` và cập nhật DOM SƯ PHỤ/ĐỆ TỬ. Backup: `docs/sessions/2026-10-19/BUG-043/`. Report: `docs/BUG-043_AI_DICH_TRUYEN_THUA_REPORT.md`.

---

## BUG-045 — Cột Gemini trong namevimap.html chỉ 39K/48K (9K chưa phiên âm) + Cột Claude chưa có dữ liệu (0/48K)

**Route/URL:** `/daoanh/admin/namevimap.html` (Admin panel)
**Task:** `tasks/T418-gemini-translation-incomplete.md`
**Thời gian phát hiện:** 2026-10-19 (Admin báo)
**Expected:** Cột Claude (48.673 tên từ XML import) + Cột Gemini (48.673 tên từ API batch) đều hiện 100%.
**Actual:** Cột Claude chỉ hiện 0 (table `codex_person_name` tạo + import 48.646 matched + 689 orphan, nhưng UI chưa có dữ liệu); Cột Gemini chỉ 39.269/48.673 (85.6%).
**Root cause Part 1:** Script `ai_batch_transliterate.py` chạy 3 lần (2026-10-04/05/08) → 39.269 records. 9.404 ID còn lại bị fail từng batch (quota 429), không auto-retry. Cần chạy lại script để lấy 9.404 ID chưa xử.
**Root cause Part 2:** XML từ GitHub (commit 0d2ea40) có 49.335 tên, 48.646 match với `people` table, 689 ID orphan (không có trong DB). Cần import vào bảng `codex_person_name` + flag 1.637 ID có lệch chữ Hán.
**Scope:** 
- Part 1: Fetch XML từ GitHub (commit 0d2ea40), parse, CREATE TABLE `codex_person_name`, INSERT 48.646 matched + 689 orphan (status='orphan-chưa có ID Dila'), flag 1.637 lệch chữ Hán.
- Part 2: Resume `scripts/ai_batch_transliterate.py` (--limit 500/ngày), fill 9.404 ID còn lại trong `ai_person_name.name_vi_ai`.
- Backup DB trước, manifest INSERT, verify count, screenshot trước/sau, commit script+docs.
**Trạng thái:** ✅ DONE (2026-10-20) — Gemini ai_person_name = 48,673/48,673 (100%), Claude codex_person_name = 49,335 rows. Cả 2 cột hiện đầy đủ trên namevimap.html. QA xác nhận 2026-10-20.

---

## BUG-049 — namevimap.html TAB ETL — button Pass không chạy, hiện nút đỏ X

**Route/URL:** `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → TAB 3 "🔧 TTL ETL"
**Task:** `tasks/T436-bug049-etl-pass-button-error.md`
**Thời gian phát hiện:** 2026-10-20 (Admin báo)
**Expected:** Click `✓ Pass` (hàm `passEtlFlag(this)`) → lưu `name_vi_final` vào DB, ẩn row, network trả 200.
**Actual:** Có lúc nút chuyển đỏ (class `.err`, text `✗`) trong 3s rồi quay lại `✓ Pass`, không lưu DB, không ẩn row.
**Root cause:** KHÔNG phải lỗi ở `passEtlFlag()` (namevimap.html:1840-1871) hay endpoint `POST /api/admin/namevi-map/update` (app.py:15803-15880) — cả hai đã audit và hoạt động đúng (verify nhiều lần: 200 OK, `success:true`). Lỗi thực nằm ở lớp proxy dev local `daoanh/local_gateway.py::proxy()`: chỉ bắt `requests.exceptions.ConnectionError`, KHÔNG bắt `requests.exceptions.Timeout`. Khi backend `app.py` bị chậm tạm thời (ETL tab mở → `loadEtlFlagLiveData()` bắn burst N request `GET /api/admin/namevi-queue/<id>` song song, đã ghi nhận trong T427 "có lúc 7-27s, flag-list tới ~94s khi máy tải nặng"), request proxy vượt `timeout=60` ném `Timeout` không được bắt → Flask trả HTML lỗi 500 mặc định thay vì JSON → `JSON.parse()` phía client crash → `passEtlFlag()` rơi vào catch ngoài cùng → nút hiện `✗`. Bằng chứng trực tiếp: `gateway_local.log` ghi `TimeoutError: timed out` lặp 5 lần (14:30:17–14:32:03) trên endpoint `flag-list` cùng lớp proxy, cùng điều kiện tải với `namevi-map/update` — tính ngẫu nhiên khớp triệu chứng admin báo "không phải lần nào cũng lỗi".
**Scope:** Sửa `daoanh/local_gateway.py::proxy()` — thêm `except requests.exceptions.Timeout` (trả JSON 504) và `except requests.exceptions.RequestException` (trả JSON 502) thay vì để Flask crash ra HTML không parse được. Không sửa `app.py`/`namevimap.html` vì 2 lớp đó không có lỗi. Không thay đổi kiến trúc burst-request của `loadEtlFlagLiveData()` (trade-off đã chấp nhận ở T427, ngoài phạm vi BUG-049).
**Backup:** `daoanh/docs/sessions/2026-10-20/BUG-049/local_gateway.py.bak` (trước khi sửa).
**Test:** Click Pass ngay sau khi mở tab ETL (trong cửa sổ burst) → 200 OK, row ẩn, counter tăng. Double-click Pass liên tiếp → không lỗi, không duplicate-crash. Regression: tab Xác Minh, tab Place vẫn hoạt động bình thường. `python -m py_compile local_gateway.py` OK.
**Trạng thái:** ✅ DONE (2026-10-20) — report chi tiết: `docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md`. Chờ QA xác nhận.
**Verify lại (2026-10-21, T436):** Mở browser thật tại `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → Tab ETL → click `✓ Pass` trên row A046539 (Long Thọ): `POST /api/admin/namevi-map/update` → 200 OK (`success:true`), row ẩn khỏi bảng ngay. Double-click Pass trên row A001003 (Mã Minh): 2 request đều 200 OK, không duplicate/crash, không nút đỏ `✗`. Fix T436 vẫn hoạt động đúng, không cần sửa thêm. Chi tiết: `docs/T436_T437_VERIFY_FIX_REPORT.md`.

---

## BUG-050 — namevimap.html Tab ETL — bảng "Bulk FLAG Queue" kẹt "Đang tải…" vĩnh viễn

**Route/URL:** `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → TAB 3 "🔧 TTL ETL"
**Task:** `tasks/T437-bug050-namevimap-stuck-loading.md`
**Thời gian phát hiện:** 2026-10-20 (Admin báo)
**Expected:** Bảng "Bulk FLAG Queue" load xong, không kẹt "Đang tải…" dù Admin chuyển tab qua lại trong lúc đang tải.
**Actual (audit vòng 2, trước fix):** Rời tab ETL rồi quay lại TRƯỚC KHI lượt tải trước xong → nhánh `else` trong `switchTab()` chỉ gọi `loadEtlFlagLiveData()`, trong khi `_etlNewAbortSignal()` đã abort vĩnh viễn `etlFlagQueueLoad`/`loadAiColStatus`/`loadCodexColStatus` của lượt trước mà không ai gọi lại → bảng kẹt "Đang tải…" mãi mãi (không phải do timeout 45s, mà do request bị huỷ không có request thay thế).
**Root cause xác nhận lại (2026-10-21, T437):** Đã audit code hiện tại — phần sửa `switchTab()` gọi `_etlFullLoad()` ở CẢ 2 nhánh if/else (namevimap.html dòng 1030-1050, comment ghi rõ "T435/BUG-048 vòng 2") **đã được một phiên trước đó áp dụng xong** trước khi phiên này bắt đầu. Verify bằng browser thật: reload trang → chuyển tab đi/về nhiều lần liên tiếp ngay trong lúc đang tải → request cũ bị `net::ERR_ABORTED` nhưng luôn có request thay thế bắn lại ngay, bảng không kẹt, cuối cùng vẫn load đủ 311/311 FLAG. Không cần sửa thêm phần này.
**Việc còn lại đã làm (T437, Hướng A — progressive load):** Theo yêu cầu redesign của Admin, thay cơ chế "1 API per_page=50, chờ cả lượt rồi render 1 lần, lỗi cứng 45s xoá sạch bảng" bằng tải tuần tự theo trang nhỏ, render ngay từng trang:
- `_ETL_FLAG_PER_PAGE`: 50 → 30.
- Hàm mới `etlFlagQueueLoadAll()` + `_etlFlagLoadPageSeq()`: gọi tuần tự `page=1,2,3,...` (không đổi API/backend — `per_page` đã là query param có sẵn), mỗi trang render ngay khi về (`appendChild`, không `innerHTML=''` cả bảng).
- Badge "Đang tải trang N…" hiển thị ở cuối bảng trong lúc chờ trang kế.
- Deadline RIÊNG 15s/trang (so với 45s chung cả lượt trước đây) — hết giờ 1 trang → badge lỗi + nút "Thử lại" CHỈ ở trang đó, các trang đã tải trước vẫn hiển thị nguyên vẹn, không xoá sạch bảng.
- Tất cả điểm gọi "tải lại từ đầu" (nút Load, checkbox Ẩn đã duyệt, tìm kiếm, sort theo Tin cậy, reload sau Bulk Pass, `_etlFullLoad()`) đổi từ `etlFlagQueueLoad(1)` sang `etlFlagQueueLoadAll()`.
**Scope:** Chỉ sửa `daoanh/admin/namevimap.html` (JS trong 1 file, không đổi `app.py`/API/DB/schema). Không đụng Tab Place Claude/Gemini placeholder (ngoài phạm vi, đang chờ Admin quyết định riêng).
**Backup:** `daoanh/docs/sessions/2026-10-21/T437/namevimap.html.bak` (trước phiên này), `namevimap.html.before_progressive_load.bak` (trước khi sửa progressive load).
**Test:** `node --check` script JS trích xuất OK. Browser thật: tải lần đầu → network log xác nhận 11 request `flag-list?page=1..11&per_page=30` tuần tự, đều 200 OK, badge "311/311 FLAG" đúng tổng. Chuyển tab đi/về liên tục nhiều lần ngay trong lúc đang tải (2 vòng) → request cũ `ERR_ABORTED`, request mới luôn chạy tiếp, bảng không kẹt, cuối cùng vẫn 311/311. Cột Claude/Gemini header giữ đúng số (48,646/48,673 · 48,673/48,673) sau nhiều lần chuyển tab. Regression: tab Xác Minh (338 mục), tab Place (59,167 địa danh, Claude/Gemini vẫn placeholder "—" đúng spec), route `/daoanh/places` (map load bình thường, không console error) đều hoạt động bình thường.
**Trạng thái:** ✅ DONE (2026-10-21) — report chi tiết: `docs/T436_T437_VERIFY_FIX_REPORT.md`. Chờ QA + Admin xác nhận.

---
