# Session 2026-09-25 — Task 5 + Task 6: A009460 DB Audit + Ancestor Chain Quicklist

## Tóm tắt
Audit toàn bộ dữ liệu A009460 (Đơn Hà Thiên Nhiên) trong DB để đảm bảo không sót
thông tin nào, rồi bổ sung tất cả vào layout inspector.

## 1. DB Audit — Kết quả

**Đã hiển thị đúng trước phiên này:**
- Alt names (Hán + Việt dịch) ✓
- Giới tính "Nam" ✓
- Năm sinh/mất (DILA: ~739–824) ✓
- death_note, birth_death_quote ✓
- Truyền Thừa relations (Thạch Đầu Hy Thiên → Đơn Hà → 5 đệ tử) ✓
- listbibl CBETA ✓, mentioned_in ✓

**Thiếu trước phiên này (đã fix):**
1. `dynasty="唐"` — trong center node từ lineage-tree API, CHƯA render trong inspector
2. `vn_person_authority.generation_order=NULL` — trong TTL bkg:generationOrder=36, chưa import
3. `vn_person_authority.dharma_lineage=NULL` — trong TTL bkg:dharmaLineageName, chưa import
4. `vn_person_authority.biographical_note_vi=NULL` — TTL biographicalNote 8787 chars, chưa import

## 2. DB Import (Python 1-shot)

Đọc từ `data/ttl/TS-Don-Ha-Thien-Nhien.ttl`:
```
generationOrder: 36
dharmaLineageName: "Thiền Tông Trung Hoa - Nam Tông"
biographicalNote: 8787 chars (đầy đủ từ THIỀN SƯ THIÊN NHIÊN ĐAN HÀ...)
```

Cập nhật SQL:
```sql
UPDATE vn_person_authority
SET generation_order=36, dharma_lineage='Thiền Tông Trung Hoa - Nam Tông',
    biographical_note_vi='...(8787 chars)...'
WHERE dila_id='A009460';
```

## 3. API Change — app.py

`_t86_resolve_display_name()` lines 5782–5800:
- Mở rộng SELECT để lấy `generation_order, dharma_lineage, biographical_note_vi`
- Thêm 3 keys vào returned dict khi resolve từ `vn_person_authority`
- Áp dụng cho mọi monk có TTL data (không chỉ A009460)

## 4. UI Change — places.html

`_renderLineageInspector()` lines 6921–6942:
Thêm 3 section mới trước DILA bio:
1. **Meta gold line**: `"Nhà Đường (唐) · Pháp tự đời thứ 36"` (dynasty + generation_order)
2. **Pháp mạch**: `"Pháp mạch: Thiền Tông Trung Hoa - Nam Tông"` (dharma_lineage)
3. **TTL bio `<details>`**: collapsible với toàn văn biographical_note_vi

## 5. Verify

Browser QA (loadLineageTree('A009460')):
- DOM: evHTML[0:400] = "Nhà Đường (唐) · Pháp tự đời thứ 36...Pháp mạch: Thiền Tông Trung Hoa - Nam Tông...<details>..."
- evContentLen: 21532 chars
- evWrapFlex: "1 1 50%" (expanded)
- TTL bio expand: "THIỀN SƯ THIÊN NHIÊN ĐAN HÀ\n\nPHÁP TỰ ĐỜI THỨ HAI..." ✓
- 0 JS error ✓
- Screenshot: right panel hiển thị đầy đủ các section mới

## 6. Commit

`22a5cf7` feat: T5 — A009460 TTL metadata load + inspector render

## Files changed
- `daoanh/app.py` — _t86_resolve_display_name: include TTL meta fields
- `daoanh/places.html` — _renderLineageInspector: render dynasty/generationOrder/dharmaLineage/bio
- `daoanh/data/lineage.db` — vn_person_authority A009460: 3 fields updated (không track trong git)
- Backup: `docs/sessions/2026-09-25/places.html.bak-t5-ttl-bio-pre`

---

# Task 6 — Quicklist Ancestor Chain (BFS từ Huệ Năng)

## Yêu cầu
Hiển thị chuỗi pháp hệ dọc từ Root Tổ sư Huệ Năng A001719 đến monk đang xem.

## Cơ chế consensus (Task 6b)
`lineage_edge_consensus WHERE is_default_visible=1` = ≥2 nguồn đồng thuận.
- Cột `agreeing_source_count`: số nguồn xác nhận (DILA, Marcus, TTL, Lineage)
- Cột `consensus_status`: 'multi_source' (≥2) hoặc 'single_source' (ẩn mặc định)
- API ancestor-path dùng `is_default_visible=1` → tự động chỉ đi qua cạnh đã đồng thuận ≥2 nguồn

## API mới — app.py
`GET /daoanh/api/monk/<dila_id>/ancestor-path?root=A001719`
- BFS ngược: từ dila_id đi lên qua teacher_id (lineage_edge_consensus, is_default_visible=1)
- Dừng khi gặp root_id (A001719) hoặc hết đường
- Trả về: `{ok, found, path: [node_info,...], start, root, depth}`

## UI — places.html
`_renderLineageSidebar()` → async, gọi API, render chuỗi dọc:
- 🔱 Root (style: background mờ trắng, font 600)
- · Ancestor giữa (style: panel border)
- ◈ Center = monk đang xem (style: vàng gold, border vàng, font 700)
- ↓ arrow giữa các node
- Fallback sang flat chips nếu API lỗi hoặc path rỗng

## Bằng chứng Verify (A009460)
API: GET /daoanh/api/monk/A009460/ancestor-path?root=A001719 → 200 OK
Chain: 🔱 Tôn Giả Đại Giám Huệ Năng (A001719)
       → · Thanh Nguyên Hành Tư (A003666)
       → · Thạch Đầu Hy Thiên (A010291)
       → ◈ Đơn Hà Thiên Nhiên (A009460)
DOM: qlChildCount=7 (4 row divs + 3 arrow divs) ✓

## Commit
`a059601` feat: T6 — quicklist ancestor chain BFS từ Huệ Năng A001719

---

# Task 7 — Nét liền/đứt phân biệt nguồn xác nhận

## Yêu cầu
- Nét liền vàng cho ≥2 nguồn, nét đứt cam cho 1 nguồn chưa đủ
- Thêm legend màu nét vào panel trái để user hiểu ý nghĩa
- Fix tooltip sai "cần khảo cứu" khi hover cạnh chánh mạch

## Các commit (phiên trước + phiên này)

### `fa7bb5e` feat: T7 — net dut cam cho truyen thua 1 nguon
- `include_single=1` thêm vào 3 API calls
- `_t127EdgeStyle` thêm case `consensus_status==='single_source'`
- Legend bar cập nhật
- Footer text cải thiện

### `8fb883f` fix: edge color - confirmed luon vang, single-source cam sang
- `_t127EdgeStyle` tách 3 trường hợp rõ ràng
- confirmed_2plus LUÔN vàng #d4a030, nét liền — kể cả khi không có CBETA ref

### `a17326e` fix: T7b — legend màu nét + isCandidate guard + canvas isSingle fix
**3 thay đổi:**

1. **Legend màu nét trong panel trái** (#lineage-sidebar):
   - Section "CHÚ THÍCH MÀU NÉT" với 4 dòng indicator
   - Hiển thị visual dòng (CSS border/background) + text giải thích

2. **isCandidate defensive fix** trong `_t127EdgeStyle`:
   - Cũ: `isCandidate = trust_level === 'L3'`
   - Mới: `isCandidate = L3 && !isConfirmed && !isSingleSource`
   - Guard: confirmed_2plus edges KHÔNG bao giờ hiện "cần khảo cứu"
   - Verify: A000237(Hoằng Nhẫn)→A001719(Huệ Năng) L1+confirmed_2plus
     → tooltip "● Truyền pháp đã xác nhận (≥2 nguồn)" ✓
     → 0 edges có "cần khảo cứu" trong tree A001719 ✓

3. **Canvas `afterDrawing` isSingle flag** (fix core từ phiên trước):
   - `var isSingle = edge._isSingle || edge._consensus_status === 'single_source'`
   - `col = isSingle ? '#e07820' : '#d4a030'`
   - `setLineDash([3/sc, 5/sc])` cho single-source edges
   - `_isSingle` flag set trong visEdges build cả 2 mode

## DB xác nhận
- A001719 (Huệ Năng): 4 single-source edges (is_default_visible=0)
- 98 edges total trong lineage-tree (khi include_single=1)
- 0 L3 edges trong tree hoặc spine của A001719, A009460

## Verify
- API `/lineage-tree?include_single=1`: 98 edges, 4 single_source ✓
- Tooltip A000237→A001719: "● Truyền pháp đã xác nhận" (không phải "cần khảo cứu") ✓
- Legend hiển thị trong panel trái với 4 loại nét ✓

---

# Task 8 — Breadcrumb header cập nhật khi click node

## Yêu cầu
Click vào vị nào trong tree thì breadcrumb "Pháp hệ ·" phải cập nhật tên nhân vật đó.

## Phân tích
- Element visible: `#lineage-header` (full-width breadcrumb bar)
- Element ban đầu T8 target: `lineage-sidebar-title` (trong sidebar `display:none` → INVISIBLE)
- Fix: cập nhật `#lineage-header > strong` và DILA ID span thay vì sidebar-title

## Code (places.html ~line 5725)

```javascript
// T8: Cập nhật breadcrumb #lineage-header khi click node trong lineage mode
if (options.mode === 'lineage') {
    const _hdr = document.getElementById('lineage-header');
    if (_hdr && _lineageState) {
        const _n = (_lineageState.nodes || {})[pid];
        const _vi = _n ? ((_t86NodeLabel && _t86NodeLabel(_n)) || _n.name_vi || pid) : pid;
        const _zh = _n && _n.name_zh ? ' (' + _escHtml(_n.name_zh) + ')' : '';
        const _s = _hdr.querySelector('strong');
        if (_s) { _s.innerHTML = _escHtml(_vi) + _zh; }
        const _ns = _s && _s.nextElementSibling;
        if (_ns && _ns.tagName === 'SPAN' && pid) { _ns.innerHTML = '– DILA ID: ' + _escHtml(pid); }
    }
}
```

## Verify

- Click A000237 (Hoằng Nhẫn): header → "Tôn Giả Hoàng Mai Hoằng Nhẫn (弘忍) – DILA ID: A000237" ✓
- Click A001719 (center Huệ Năng): header reset → "Tôn Giả Đại Giám Huệ Năng (慧能) – DILA ID: A001719" ✓
- Screenshot: breadcrumb hiển thị đúng sau khi emit click event ✓
- Left sidebar title vẫn giữ center monk (Huệ Năng) — không bị ảnh hưởng ✓
