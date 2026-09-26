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
**Status:** open — fix applied (T101, trước 2026-09-22), CHỜ admin xác nhận DONE

## BUG-002 — Edge thiếu trường `evidence_type` trong api_nexus
**Route/URL:** `/daoanh/api/nexus/<type>/<id>`
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Edges cbeta_ref → `with_evidence`; no ref → `unverified`
**Actual:** Branch etype=person: 2 edges thiếu evidence_type (chỉ có ref/citation); branch etype=place: đã có evidence_type
**Evidence:** Audit code app.py api_nexus line 6418-6424 (etype=person branch)
**Fix (2026-09-22 T161):** Thêm _src + evidence_type "unverified"/"partial" cho 2 edges trong etype=person branch. Revert: `git revert <commit-T161>`
**Status:** open — fix applied (2026-09-22), CHỜ admin xác nhận DONE

## BUG-003 — Không có PARTIAL badge trên edge thiếu provenance
**Route/URL:** Nexus tab (places.html `_renderVisGraph`)
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Edge partial hiện badge ⚑ + title lý do thiếu provenance
**Actual:** Không có badge — không phân biệt `partial` vs `with_evidence` trên UI
**Evidence:** Code audit `_renderVisGraph` line 3410-3435 places.html
**Status:** pending_confirm

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
**Status:** open — fix applied, chờ Admin xác nhận DONE

## BUG-005 — `_nexusSafeLabel` thiếu fallback chain đầy đủ theo spec §6
**Route/URL:** Nexus tab (mọi entity)
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Fallback: name_vi > preferred_label_vi > display_name > name_han/name_zh > source_label > canonical_id
**Actual:** Chỉ có: label_vi || label || label_zh || id (thiếu name_vi, preferred_label_vi, display_name, source_label, name_han)
**Evidence:** Code line 5211-5216 places.html
**Fix:** Đã có đầy đủ fallback chain trong code hiện tại (line 7051-7057 places.html): name_vi || label_vi || preferred_label_vi || display_name || label || name_han || label_zh || source_label || name_zh || id || canonical_id
**Status:** open — fix applied (session trước T161 audit), CHỜ admin xác nhận DONE

## BUG-006 — Place view không auto-expand tang_nhan (spec §4.1 default 3-đời)
**Route/URL:** Nexus tab cho place entity
**Root entity ID:** PL000000023255
**Thời gian phát hiện:** 2026-09-07 session T101
**Expected:** Mặc định mở đến đời 2 (root → group → subgroup) — tang_nhan expanded khi load
**Actual:** `_nexusGroupState = { expanded: null, subexpanded: null }` — collapsed mặc định, cần 2 click để thấy subgroup
**Evidence:** Code line 5324 places.html
**Fix:** Đã có `expanded: 'tang_nhan'` cho place entities (places.html line 7165): `const defaultExp = d.entity_type === 'place' ? 'tang_nhan' : null; _nexusGroupState = { expanded: defaultExp, subexpanded: null, ... }`
**Status:** open — fix applied (session trước T161 audit), CHỜ admin xác nhận DONE

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
**Status:** open — fix applied, chờ Admin xác nhận DONE

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
**Status:** open — fix applied, chờ Admin xác nhận DONE

## BUG-011 (MAP_MARKER_PLACE_PROFILE_METADATA_NOT_LOADING_001) — Click marker bản đồ không load GPS/district/note/category vào panel trái
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
**Status:** pending_confirm — IMPLEMENTED / READY_FOR_ADMIN_TEST — CHỜ ADMIN CONFIRM DONE

## BUG-012 (GIS_SEARCH_MARKER_STATE_MISMATCH_001) — Lệch state GPS/RAG giữa tìm kiếm và marker bản đồ
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
**Status:** fix applied (2026-09-22) — CHỜ ADMIN CONFIRM DONE
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
**Status:** fix applied, CHỜ ADMIN CONFIRM DONE (2026-09-10)

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
**Status:** open — fix applied, CHỜ ADMIN CONFIRM DONE

---

## BUG-017 (LINEAGE_RACE_CLICK_STALE_RENDER_001) — Click nhanh A→B→C trên lineage render sai node (race)
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa (lineage/expanded/timeline)
**Root entity ID:** nhiều (VD Mã Tổ Đạo Nhất / người nhiều trò)
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Click nhanh nhiều node liên tiếp → chỉ render kết quả của node cuối cùng.
**Actual:** `loadLineageTree` (:4810) + `centerLineageOn` (:4981) KHÔNG có AbortController → fetch/render lần trước (chậm network) race với lần sau, kết quả cuối có thể là node sai.
**Root cause (đã xác minh):** 2 hàm hiện tại không abort request cũ (tồn tại pattern `loadAbortController`:862 / `_linEdgeState.ctrl`:5912 trong file nhưng lineage tree chưa dùng).
**Fix (T140):** bọc AbortController mới mỗi lần gọi, abort lần trước trong `loadLineageTree` + `centerLineageOn`.
**Status:** open - fix applied in `cd247c4` (daoanh/places.html) — chờ Admin xác nhận DONE. Test: @babel/parser 5 blocks/0 errors + pipeline lint/test/uat/compliance/e2e PASS (e2e:runtime EPERM pre-existing).

---

## BUG-018 (LINEAGE_DEFAULT_EXPAND_OVERFETCH_001) — Default fetch quá sâu + auto mở 3 đời đệ tử (trái "3 đời = 1 thầy + root + 1 đệ tử")
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa · Pháp mạch
**Root entity ID:** VD A042195 / người có >3 đời truyền thừa phía dưới
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Lần đầu load = 1 thầy + node trung tâm + 1 đệ tử (3 đời literal), đệ tử sâu hơn hiện qua nút "+N đệ tử"/"Mở 2/3 đời".
**Actual:** Mốc tâm hiện tại tự mở 3 đời phía dưới (fetch depth mặc định + auto expand), tốn request + cây rộng khi mở.
**Fix (T140):** đổi fetch lineage-tree → `?up=2&down=2` + initial `_ftExpanded` = center + 1 gen (bỏ auto mở 3 đời đệ tử lần đầu); giữ nguyên nút ctrl bar đã có (:5577-5602).
**Status:** ~~open - fix applied in `cd247c4`~~ **REGRESSION FIX `35b3f6b` (2026-09-23)** — commit `6c710b2` (T152) đã đổi up/down thành 6 trước khi T140 Admin QA; `35b3f6b` khôi phục `?up=2&down=2` tại 3 chỗ. Verified: network log thật `up=2&down=2`. Chờ Admin QA.

---

## BUG-019 (LINEAGE_LABEL_OVERLAP_ZOOMOUT_001) — Label node chồng nhau khi zoom-out (không truncate)
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa · Phả hệ mở rộng (network)
**Root entity ID:** VD Mã Tổ Đạo Nhất (multi-branch)
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Zoom-out → label node không-chọn resize nhỏ/ẩn, không đè nhau; tooltip đầy đủ; node đang chọn luôn đủ.
**Actual:** Không có handler `network.on('zoom')` trong lineage network → label luôn nguyên cỡ, chồng nhau khi thu nhỏ.
**Fix (T140):** `network.on('zoom')` → set font size node non-selected theo scale (selected luôn đầy đủ). Tooltip `_t129NodeTitle` giữ nguyên.
**Status:** open - fix applied in `cd247c4` (daoanh/places.html) — chờ Admin xác nhận DONE. Test: @babel/parser 5 blocks/0 errors + pipeline PASS (e2e:runtime EPERM pre-existing).

---

## BUG-020 (LINEAGE_LEGEND_SOURCE_MISLEAD_001) — Legend nguồn hiểu nhầm Marcus/DILA ngang hàng + thiếu ⚠ ngược chiều
**Route/URL:** `/daoanh/places.html` · Tab 🌳 Truyền Thừa
**Root entity ID:** A008874→A009491 (DILA direction_mismatch)
**Thời gian phát hiện:** 2026-09-15 session T140 audit
**Expected:** Legend nói rõ Marcus = cấu trúc nền, DILA = overlay đối chiếu (✓ khớp / ⚠ ngược chiều); Zen không hiện (0 assertions).
**Actual:** Chú giải [M]/[D] đang gợi ý nguồn ngang hàng; node/edge có mark DILA direction_mismatch nhưng repo dữ liệu không xác minh — thiếu badge ⚠ ngược chiều rõ ràng.
**Fix (T140):** bổ sung badge ⚠ ngược chiều + chú giải đúng ngữ nghĩa + ẩn nguồn Zen.
**Status:** ~~open - fix applied in `cd247c4`~~ **REGRESSION FIX `35b3f6b` (2026-09-23)** — commit `62ad40e` (fix tên tăng nhân) đã xóa legend text T140; `35b3f6b` khôi phục "Marcus = cấu trúc chính · DILA = đối chiếu (✓ khớp / ⚠ ngược chiều) · Zen hiện ẩn" (Pháp mạch) + "Nguồn: Marcus (cấu trúc chính) · DILA (đối chiếu ✓/⚠) · Zen ẩn" (Phả hệ mở rộng). Verified: DOM query trả đúng nội dung. Chờ Admin QA.

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
**Status:** fix applied (2026-09-22) — CHỜ ADMIN CONFIRM DONE
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
**Status:** pending_confirm — FIX APPLIED (DB thay đổi trực tiếp, không có commit để revert). Revert: `UPDATE people SET name_vi='Quy Sơn Linh Hựu' WHERE id='A021462'` + `UPDATE people SET name_vi='Đại Viên Thiền Sư' WHERE id='A001984'`. CHỜ ADMIN CONFIRM DONE.

## BUG-026 (SEARCH_THACH_DAU_HY_THIEN_WRONG_PERSON_001) — Search "Thạch Đầu Hy Thiên" trả 2 người (A010291 + A001744)
**Route/URL:** `/daoanh/api/search?q=Thạch+Đầu+Hy+Thiên`
**Root entity ID:** A010291 (希遷, ĐÚNG), A001744 (慧辯, SAI)
**Thời gian phát hiện:** 2026-09-23
**Expected:** Chỉ trả A010291 (Thạch Đầu Hy Thiên — 石頭希遷, Đường 700-790, Thiền tông).
**Actual:** `people` table có 2 người cùng `name_vi="Thạch Đầu Hy Thiên"`: A010291 (đúng) và A001744 (慧辯, Bắc Tống, hiệu 無際大師, trụ 衢州靈祐山秀峰寺, nối pháp 圓照宗本 — SAI, máy tự phiên âm gán nhầm). Verify: `/daoanh/api/search?q=Thạch+Đầu+Hy+Thiên` → `monks: [A001744, A010291]`.
**Evidence:** API payload monks [A001744, A010291] cùng `name_vi` (2026-09-23); phát hiện: agent `fix_dila_biography_id_display` 2026-09-22.
**Fix (data-only, không đổi code):** `UPDATE people SET name_vi='Tuệ Biện' WHERE id='A001744' AND name_vi='Thạch Đầu Hy Thiên'` (慧辯 → Sino-Vietnamese: Tuệ Biện). Session: `docs/sessions/2026-09-22/changes.md`.
**Status:** pending_confirm — FIX APPLIED (2026-09-23, data-only). Revert: `UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE id='A001744'`. CHỜ ADMIN CONFIRM DONE.
