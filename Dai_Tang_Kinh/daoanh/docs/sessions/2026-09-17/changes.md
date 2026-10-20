# Session Changes 2026-09-17

## Files modified

### daoanh/places.html

**Task 1 — NHÂN VẬT tab: hiển thị bio_vi thay vì bio_snippet Hán**
- Curated persons (ĐÃ XÁC MINH): `p.bio_vi || p.note || ''` thay vì `if (p.note)`
- directBio: `p.bio_vi || p.note || ''` với style italic khi dùng note fallback
- indirectBio: `p.bio_vi || p.note || ''` với style italic khi dùng note fallback

**Task 2 — Fix SEARCH ERROR: Invalid LatLng object: (NaN, NaN)**
- `doSearch` line ~1536: guard `isFinite(parseFloat())` trước `map.flyTo`
- `selectItem` line ~1113: guard `isFinite` trước `map.flyTo`
- `window.onload` flyParam handler: guard `isFinite` trước `map.flyTo`
- `selectResult` line ~1682: guard `isFinite` trước `map.flyTo`
- DILA GPS handler line ~1181: guard `isFinite` trước `map.flyTo`

**Task 3 — Fix Tailwind CDN production warning**
- Thay `<script src="https://cdn.tailwindcss.com">` bằng `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.16/dist/tailwind.min.css">`
- Chuyển 5 arbitrary class sang inline style:
  - `w-[420px]` → `style="width:420px"` trên `<aside>`
  - `tracking-[0.3em]` → `style="letter-spacing:0.3em"` trên `<h3>`
  - `text-[11px]` → `style="font-size:11px"` trên `<p>`
  - `text-[10px]` trong JS autocomplete string → `style="font-size:10px"` (2 chỗ)
  - `text-[9px]` trong JS autocomplete string → `style="font-size:9px"` (2 chỗ)

### daoanh/app.py

**Task 1 — Thêm bio_vi vào API response của api_places_persons**
- Curated persons SQL: thêm `p.bio_vi` vào SELECT và dict
- bio_cache SQL: thêm `p.bio_vi` JOIN người → dict
- Fallback LIKE query: thêm `bio_vi` vào SELECT và dict

**Task D — doSearch (Enter) tự động chuyển sang Nhân Vật khi tìm thấy tăng nhân**
- `doSearch` tại line ~1523: refactor dùng `Promise.allSettled` gọi cả `/api/places/search` lẫn `/api/monk-resolve` song song
- Nếu monk-resolve trả về kết quả: `searchInput.value` cập nhật tên, gọi `selectPerson(p.id, ...)` → tự động switch tab lineage
- Nếu chỉ có place results: giữ nguyên logic cũ
- Test: "Đơn Hà Thiên Nhiên" → Enter → `itemId=A009460`, `sourceOrigin=· TĂNG NHÂN · DILA`, activeTab=lineage

**Task E — Lineage inspector "Chi tiết tăng nhân" có thể scroll khi nội dung dài**
- Root cause: `inspector.style.display = ''` xóa property → browser fallback `display:block` → sections mất flex constraint → `overflow-y:auto` vô hiệu
- Fix 1 (line ~4934): `inspector.style.display = 'flex'` (show khi lineage tree load)
- Fix 2 (line ~6824): `insp.style.display = hidden ? 'flex' : 'none'` (toggle button)
- Test: `display:flex` ✅, section1=`336px` ✅, `scrollHeight=1018 > clientHeight=336` → scrollbar xuất hiện ✅

**Task F — Nút AI Dịch trong "Tiểu sử (nguồn DILA)" ở panel Nguồn & chứng cứ**
- `_renderBioViEditor` (line ~5735): khi `bioVi` falsy, thêm `<button id="lin-bv-ai-btn" onclick="_linDichAI(pid,this)">` sau "Chưa có bản dịch" message
- Thêm hàm `_linDichAI(pid, btn)`: POST `/api/person/<pid>/translate` → nếu OK cập nhật `lin-bv-view`, xóa nút wrapper; nếu lỗi hiện text lỗi trong button, re-enable
- Logic cache: khi đã có `bio_vi` trong DB → `_renderBioViEditor` hiển thị bản dịch, không có nút
- Test: A003881 (Huệ Khả, chưa dịch) → nút xuất hiện ✅; API rate limit → button hiện "⚠ Dịch thất bại", re-enable ✅; A001361 (Bồ Đề Đạt Ma, đã có bio_vi) → không có nút, hiển thị bản dịch ✅

## Verified

- ✅ Tailwind CDN warning biến mất (chỉ còn vis-data dev warning, không thể fix)
- ✅ SEARCH ERROR không xuất hiện khi search "Thiếu Lâm"
- ✅ Sidebar width 420px đúng sau khi bỏ Tailwind CDN
- ✅ Tab NHÂN VẬT hiển thị bio tiếng Việt cho person cards
- ✅ Không có console errors

## Known unfixed

- vis-data.mjs "You're running a development build." — từ vis-network.min.js bundle, không thể suppress từ places.html
- A000003, A000005: `bio_vi` trống → fallback note/snippet hiển thị (cần admin save bio_concise_vi trong person.html)
