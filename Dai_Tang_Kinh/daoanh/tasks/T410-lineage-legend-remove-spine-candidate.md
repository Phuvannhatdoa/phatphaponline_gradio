---
id: T410
bug_id: BUG-035
title: "Bug verify: BUG-035: Panel Pháp hệ — gỡ chú thích + nét 'cam đậm (trục tổ sư)'/'xám đứt (candidate)', chuyển sang MÀU THEO NGUỒN (DILA xanh · Marcus vàng · TTL đỏ · nhiều nguồn khớp bạc · xám đứt = chưa rõ chiều)"
status: in_progress
created: 2026-10-15
updated: 2026-10-19
owner: code (Hermes giao)
module: Nexus Visualization
priority: medium
depends_on: []
depends_note: >
  Admin chốt 2026-10-19: T410 làm TRƯỚC, KHÔNG chờ T414. Quy tắc tạm trong lúc chưa có nhãn nối pháp:
  nét ĐỨT = "chưa rõ chiều" (0 nguồn), nét LIỀN = mọi cạnh có chiều rõ (kể cả 1 nguồn). Trục tổ sư chính
  chỉ phân biệt bằng ĐỘ DÀY nét. T414/T425 sẽ tự đúng dần khi có cột relation_kind.
dispatch: approved
plan_approved_at: "2026-10-15 (Admin: 'Hãy tìm và remove các code liên quan tới thông tin \"Nét liền cam đậm — Trục tổ sư chính (ancestor spine) / Nét đứt xám — Candidate (cần khảo cứu)\" để remove đi vì ko còn giá trị nữa')"
done_when: >
  (1) Panel trái "Pháp hệ" không còn mục "Chú thích màu nét" với 2 dòng "Nét liền cam đậm — Trục tổ sư chính" và
  "Nét đứt xám — Candidate (cần khảo cứu)" (places.html ~dòng 565–577). Chú thích "Y-fork · 3 nguồn" thay bằng chú thích
  "Cách đọc cây truyền thừa" theo **QUY TẮC MÀU MỚI — MÀU THEO NGUỒN (2026-10-19)** bên dưới: Xanh = chỉ DILA · Vàng = chỉ
  Marcus · Đỏ = chỉ TTL · Nhiều nguồn khớp = trắng/bạc (nền tối) / đen (nền sáng) · Xám chấm = chưa rõ chiều; + 3 dòng nét.
  (2) Trên cây truyền thừa KHÔNG còn cạnh vẽ màu cam (#e8941a trục chính, #e07820 single-source cũ), vàng amber cũ
  (#d4a030), xám đứt (#6b7a8a candidate), tím (#a855f7) hay xanh dương (#3b82f6). Mọi cạnh dùng đúng bảng màu theo nguồn 2026-10-19 (biến `--edge-agree` cho "nhiều nguồn khớp"); trục tổ sư chính (nếu còn
  cần nhấn) chỉ được phân biệt bằng độ dày nét, không bằng màu riêng. Cạnh đỏ "conflict" (#ff7b72) giữ nguyên (không
  thuộc phạm vi) — ghi rõ trong session log nếu Admin cần bàn.
  (3) Cạnh chưa có `edge_color` từ API (ví dụ cạnh từ ancestor-spine): hoặc backend trả thêm `edge_color` cho các cạnh
  này (hàm `calculate_edge_color_and_divergence()` trong app.py), hoặc frontend suy ra từ trường nguồn sẵn có
  (`source_badge`/`consensus_status`/`agreeing_source_count`) theo đúng bảng 3 màu. Không bịa nguồn khi thiếu dữ liệu:
  cạnh thật sự không có thông tin nguồn → ghi danh sách trong session log và hỏi Admin cách hiển thị.
  (3b) Chú thích đúng bảng "CHÚ THÍCH MỚI" (6 dòng), không còn chữ "Y-fork", hiện ở **2 chỗ** (Admin chốt 04:13):
  (i) **trực tiếp trên giao diện cây** — hộp chú thích nhỏ nổi ở một góc khung vẽ cây (thu gọn/mở được, không che nút);
  (ii) **panel trái**, đặt ngay cạnh khối tính số đời "Pháp mạch · theo từng hệ truyền thừa" (`#lineage-gen-v2-inline`).
  (4) Bằng chứng trình duyệt thật (127.0.0.1) trên route Admin báo + 1 route khác (vd A001719 Huệ Năng, A010081):
  ảnh trước/sau; grep places.html không còn chuỗi "Nét liền cam đậm", "Nét đứt xám".
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T410>, hoặc chép lại bản sao docs/sessions/<ngày>/places.html.bak-before-T410
  (+ app.py.bak-before-T410 nếu sửa backend).
outcome: >
  2026-10-15: RC kiểm hiện trạng (chỉ đọc), tạo task. Chưa sửa.
  2026-10-19: Admin đổi quy tắc màu sang màu theo nguồn (DILA xanh, Marcus vàng, TTL đỏ, 3 nguồn đen, chưa rõ chiều xám chấm).
  Tạm giữ dispatch (hold) chờ 2 câu: màu 2 nguồn, màu đen trên nền tối.
  07:17: Admin chốt ≥2 nguồn khớp = đen, khác nhau = màu từng nguồn. Còn chờ câu (b) nền tối.
  07:25: Admin chốt nền tối = trắng/bạc, nền sáng = đen; chú thích ghi "Nhiều nguồn khớp" (không ghi chữ "Đen"). Trả dispatch về approved.
  07:30: Admin duyệt bảng màu token chính thức (đã dùng đúng mã này trong code):
    --edge-dila #38bdf8 (sáng) / #0284c7 (tối) · --edge-marcus #facc15 / #ca8a04 ·
    --edge-ttl #dc2626 / #b91c1c · --edge-agree #f1f5f9 / #0f172a · --edge-unknown #94a3b8 / #64748b ·
    xung đột #ff7b72 giữ nguyên cả 2 nền.
  2026-10-19 BUILD (steps A–H hoàn tất, chờ daoanh-qa + Admin DONE):
    A. places.html: thêm 6 token --edge-* vào :root và :root[data-theme="light"] (dòng ~20–24).
    B. Panel trái: xoá cả 2 khối legend cũ ("Chú thích màu nét" 2 dòng + "Y-fork · 3 nguồn" 4 dòng) và thay bằng
       6 dòng "Cách đọc cây truyền thừa", đặt ngay sau #lineage-gen-v2-inline. Khối nổi trên canvas thêm mới
       #lineage-edge-legend-float (nút thu gọn/mở). ĐÃ PHÁT HIỆN legend THỨ BA: #lineage-legend-row (dòng tóm tắt
       đầu tab, trước đây ghi "≥2 nguồn / 1 nguồn (chưa đủ)" với #d4a030 + #e07820) — đã đổi sang màu theo nguồn.
    C. app.py calculate_edge_color_and_divergence() viết lại: trả edge_color_token + edge_sources + n_sources
       (giữ edge_color hex nền tối làm fallback). 2 call site (BFS lên + BFS xuống) đã truyền thêm 3 trường mới.
    D. places.html _t127EdgeStyle() viết lại dùng _t410EdgeColor(token) (đọc CSS var, tự đổi theo nền) +
       _t410TokenForEdge(e). Bỏ hẳn nhánh fallback single_source/candidate với #e07820/#6b7a8a/#d4a030.
    E. afterDrawing: col = theo token nguồn; isMain + isSpine chỉ đổi ĐỘ DÀY nét và kích thước đầu mũi tên.
       Nét đứt CHỈ khi unknownDir (0 nguồn); marker ⚠ (#ff7b72) giữ nguyên.
    F. 3 visEdges builder đều gắn _edgeToken/_nSources/_isSpine/_edgeDashed/_isDivergence (trước đây builder
       thứ 2 thiếu hẳn các trường này).
    G. Task file này đổi tiêu đề + depends_note theo 3 quyết định của Admin.
    H. Kiểm chứng: py_compile OK; 3/3 script block của places.html syntax OK; lint + e2e exit 0; 6 ảnh
       dark/light × A004980/A009460/A047924; audit pixel xác nhận màu mới vẽ ra và màu cũ = 0 nét.
  BUG PHÁT HIỆN KHI BUILD: #lineage-canvas bị gán innerHTML = '' ở 6 chỗ mỗi lần render (6326/6340/6794/7887/
    8417/8426) ⇒ chú thích nổi đặt TRONG canvas sẽ bị xoá. Đã chuyển #lineage-edge-legend-float ra làm sibling
    của canvas, trong wrapper có position:relative. Ghi chú này để task sau không tái phạm.
---

# T410 / BUG-035 — Gỡ chú thích + màu "trục tổ sư cam" và "candidate xám"

## Mục tiêu

Admin muốn panel Pháp hệ chỉ còn thể hiện nguồn truyền thừa bằng **màu (nay là 3 màu theo số nguồn, xem Quy tắc MÀU)**:
xanh lá liền (3 nguồn đồng thuận hoặc TTL + 1 nguồn), tím liền (Marcus + DILA, chưa có TTL), vàng đứt (chỉ Marcus),
xanh dương đứt (chỉ DILA). Hai chú thích "cam đậm trục tổ sư" và "xám đứt candidate" không còn giá trị. *(Bảng 4 màu này đã được thay bằng "Quy tắc MÀU" 3 màu theo số nguồn, mọi nét liền — xem bên dưới.)*

## Hiện trạng (RC kiểm 2026-10-15, chỉ đọc)

Route Admin báo: `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A004980&lm=tree&chain=A004981%2CA006575%2CA020370%2CA020434%2CA020435%2CA026996%2CA026997`
— vẫn thấy "Nét liền cam đậm" và "Nét đứt xám" ở panel trái (ảnh `docs/sessions/2026-10-15/BUG-035-036/before-A004980.jpg`).

| Chỗ | Vị trí (places.html) | Ghi chú |
|---|---|---|
| Chú thích 2 dòng cần gỡ | ~565–577 (khối "Chú thích màu nét — T7 legend") | Gỡ cả tiêu đề "Chú thích màu nét" nếu khối trống |
| Chú thích Y-fork 4 màu (thay bằng 3 màu theo số nguồn) | ~579–600 `#lineage-yfork-legend` | Giữ; có thể đổi tiêu đề cho dễ hiểu (vd "Màu nét = nguồn ghi nhận") |
| Vẽ cạnh vis-network | `_t127EdgeStyle()` ~6647–6710 | Nhánh fallback khi thiếu `edge_color`: cam #e07820 (single_source), xám #6b7a8a (candidate L3), amber #d4a030 (≥2 nguồn) |
| Vẽ cạnh canvas (layout cây) | ~6805–6835 | `col = isMain ? '#e8941a' : (hasYFork ? edge._edgeColor : (isSingle ? '#e07820' : '#d4a030'))` — trục chính LUÔN cam, đè màu Y-fork |
| Nguồn edge_color | app.py `calculate_edge_color_and_divergence()` (T381) | Một số cạnh (ancestor-spine) chưa được gắn |

**Cảnh báo:** chỉ xoá chú thích mà giữ code vẽ thì trên cây vẫn còn nét cam/xám không có giải thích. Task phải xử lý cả hai.

## Admin chốt (2026-10-15 03:45)

Admin: *"chốt T410"* — đặc tả trên là bản cuối, Hermes làm theo.

**[ĐÃ THAY — xem mục 04:00 bên dưới] Quy tắc nét (Admin chốt 2026-10-15 03:49):** *"nếu là 1 nguồn thì dùng nét đứt, 2 nguồn trở lên thì nét liền màu, trục
chính thì màu và to đậm gấp đôi các trục phụ"*.

**[ĐÃ THAY bởi QUY TẮC MÀU MỚI 2026-10-19] Quy tắc MÀU (Admin chốt 2026-10-15 03:59 — THAY bảng 4 màu cũ xanh lá/tím/vàng/xanh dương):** *"3 nguồn: Xanh, 2 nguồn:
vàng, 1 nguồn: đỏ"*. Màu chỉ phụ thuộc **số nguồn** ghi nhận quan hệ (DILA, Marcus, TTL), không phụ thuộc nguồn nào.

| Số nguồn ghi nhận | Màu | Kiểu nét | Độ dày |
|---|---|---|---|
| 3 nguồn (DILA + Marcus + TTL) | **xanh** | liền | chuẩn |
| 2 nguồn (bất kỳ 2 trong 3) | **vàng** | liền | chuẩn |
| 1 nguồn (chỉ DILA / chỉ Marcus / chỉ TTL) | **đỏ** | **liền** | chuẩn |
| Trục chính (pháp hệ trực tiếp) | theo số nguồn như trên | theo số nguồn | **gấp đôi** cạnh phụ |

Hệ quả cho code: bỏ hẳn tím (#a855f7) và xanh dương (#3b82f6); thay chú thích "Y-fork · 3 nguồn" ở panel trái bằng 3 dòng
mới (Xanh = 3 nguồn · Vàng = 2 nguồn · Đỏ = 1 nguồn). `edge_color` từ backend
(`calculate_edge_color_and_divergence()` trong app.py) phải đổi theo bảng này, hoặc frontend tính từ số nguồn
(`source_badge` dạng "n/4: …" / cờ dila/marcus/ttl_asserted). Trường hợp "chỉ TTL" không còn chờ màu riêng — là đỏ.

**[ĐÃ THAY — xem mục 04:04] Nét đứt: BỎ HẲN (Admin chốt 2026-10-15 04:00):** *"đỏ cũng liền vì nó là thông tin chỉ 1 nguồn chứ ko phải thông tin ko
chính xác"*. Thay cho quy tắc 03:49 "1 nguồn dùng nét đứt". Mọi cạnh đều nét liền; độ tin cậy chỉ thể hiện bằng màu theo số
nguồn. Bỏ mọi `dashes`/`setLineDash` theo số nguồn trong `_t127EdgeStyle` và đoạn vẽ canvas.

**QUY TẮC CUỐI (Admin chốt 2026-10-15 04:04) — MÀU = số nguồn, KIỂU NÉT = loại quan hệ:**
*"Nét đứt là dùng để hiển thị trên Tree nhưng ko phải truyền pháp cho Maintree: vd Đơn Hà Thiên Nhiên nối pháp từ Hy Thiên
là line liền; có 1 line truyền từ Dila, Marcus là Mã Tổ thì từ Mã Tổ nối tới Đơn Hà là nét đứt. Nhìn qua ta biết ngay vị
thiền sư thọ pháp của thầy nào, và y chỉ pháp, hoặc thầy giáo thọ là vị nào (căn theo nét đứt)."*

| Thuộc tính | Ý nghĩa |
|---|---|
| Màu | số nguồn ghi nhận quan hệ: **3 = xanh · 2 = vàng · 1 = đỏ** (đỏ = chỉ 1 nguồn, KHÔNG có nghĩa là sai) |
| Nét **liền** | quan hệ **nối pháp / thọ pháp** (truyền pháp) — tạo thành Main tree |
| Nét **đứt** | quan hệ thầy khác: **y chỉ, tham học, giáo thọ, giới sư, thế độ…** — vẫn hiện trên cây nhưng không thuộc Main tree |
| Độ dày | Main tree (chuỗi nối pháp trực tiếp tới nhân vật đang xem) dày **gấp đôi** |

Ví dụ kiểm bằng dữ liệu thật (A009460 Đơn Hà Thiên Nhiên, 2026-10-15):
- Thạch Đầu Hy Thiên (A010291) → Đơn Hà: DILA + Marcus + TTL (3) · TTL `hasTeacher` ⇒ **liền, xanh, dày (Main tree)**.
- Kính Sơn Đạo Khâm (A004218) → Đơn Hà: DILA + Marcus (2), tham học ⇒ **đứt, vàng**.
- Luật sư Hy Thao 希操 (A010470, thầy truyền giới) → Đơn Hà: DILA + Marcus (2) ⇒ **đứt, vàng**. (Tên Việt DILA đang sai "Hơi Táng".)
- Mã Tổ (A003623) → Đơn Hà: **KHÔNG có cạnh nào trong DB** (DILA chỉ nhắc trong tiểu sử "尋謁江西馬大師，受天然之法號") ⇒ cạnh
  này sẽ chưa hiện cho tới khi được bổ sung (thuộc T414).

**BỔ SUNG QUY TẮC NÉT ĐỨT (Admin chốt 2026-10-15 04:06–04:07, "đúng, sửa theo quy tắc này"):**
*"Nét đứt là để nhìn ra dòng pháp phụ mà vị thiền sư đó đã từng tham học qua nhưng chưa đắc pháp, chỉ tham khảo. Nên chỉ
có hiện trên đời của vị đó. Còn ngang hàng sư huynh đệ đồng môn hoặc học trò thì là nét liền."*

- Nét **đứt** CHỈ vẽ cho **nhân vật đang xem (focus)**: các thầy mà vị đó từng tham học / y chỉ / thọ giới nhưng không đắc
  pháp. Không vẽ nét đứt cho thầy phụ của các nút khác trên cây (ẩn đi, để cây gọn).
- Sư huynh đệ đồng môn (cùng thầy nối pháp) và học trò của nhân vật đang xem: **nét liền** (màu theo số nguồn).
- Khi người dùng chuyển sang xem nhân vật khác, nét đứt của nhân vật cũ biến mất, nét đứt của nhân vật mới hiện ra.
- Nhân vật đang xem có nhiều thầy mà chưa có nhãn nối pháp (T414 chưa xong): giữ hành vi hiện tại (nét liền) cho tới khi có
  nhãn — không đoán.

**Admin xác nhận 2026-10-15 04:10:** dùng quy tắc Xanh = 3 nguồn · Vàng = 2 · Đỏ = 1 và **hiện hướng dẫn đọc (bảng dưới) trên panel Pháp hệ**.

**Admin chốt 2026-10-15 04:13:** "phải thêm legend/chú thích trực tiếp trên giao diện tree và trên thanh Menu Panel trái đó. Thanh tính số đời đó. Chốt" ⇒ chú thích hiện ở cả 2 chỗ (xem done_when (3b)).

**CHÚ THÍCH MỚI (Admin 2026-10-15 04:08: "quy tắc mã màu này cũng re-edit lại")** — thay TOÀN BỘ khối
"Y-fork · 3 nguồn (DILA / Marcus / TTL)" (4 dòng Xanh lá liền / Tím liền / Vàng đứt / Xanh dương đứt) và dòng cảnh báo
`#lineage-yfork-warning` ở panel trái bằng đúng nội dung sau (tiêu đề: **"Cách đọc cây truyền thừa"**):

| Mẫu | Chữ hiển thị |
|---|---|
| ━ xanh | **Xanh** — 3 nguồn ghi nhận (DILA, Marcus, TTL) |
| ━ vàng | **Vàng** — 2 nguồn ghi nhận |
| ━ đỏ | **Đỏ** — 1 nguồn ghi nhận (chưa có nguồn thứ hai đối chiếu, không có nghĩa là sai) |
| ━━ dày | **Nét dày** — dòng pháp chính (Main tree) dẫn tới vị đang xem |
| ━ liền | **Nét liền** — nối pháp; sư huynh đệ đồng môn; học trò |
| ┄ đứt | **Nét đứt** — thầy từng tham học / y chỉ / thọ giới nhưng chưa đắc pháp (chỉ hiện quanh vị đang xem, để tham khảo) |

Cũng đổi theo: tooltip cạnh (bỏ chữ "Y-fork", "Trục đồng thuận", "◆ Candidate"; dùng câu như "Nối pháp · 3 nguồn: DILA,
Marcus, TTL" hoặc "Tham học (chưa đắc pháp) · 2 nguồn: DILA, Marcus"); bảng `COLOR_NAME` và mọi chữ "Tím (Marcus+DILA)",
"Xanh dương (chỉ DILA)" trong places.html. grep places.html không còn "Y-fork", "Tím liền", "Xanh dương đứt".

**QUY TẮC MÀU MỚI — MÀU THEO NGUỒN (Admin chốt 2026-10-19 07:02–07:03) — THAY bảng "3 xanh · 2 vàng · 1 đỏ theo SỐ nguồn" ở trên:**
*"Mỗi nguồn 1 màu khác nhau, Nếu 3 nguồn nhập chung cho cùng 1 kết quả thì dùng 1 Màu đen duy nhất nếu thông tin có cả 3 nguồn : Cạnh chưa rõ xám nét chấm"* · *"Dila Xanh: Marcus: Vàng , TTL Đỏ"*.

| Cạnh được ghi nhận bởi | Màu | Ghi chú |
|---|---|---|
| Chỉ DILA | **xanh** | 1 nguồn, không có nghĩa là sai |
| Chỉ Marcus | **vàng** | 1 nguồn |
| Chỉ TTL | **đỏ** | 1 nguồn |
| ≥ 2 nguồn ghi CÙNG cặp thầy→trò (cùng ID thầy, cùng ID trò) | **đen** (duy nhất) | dữ liệu khớp nhau; tooltip ghi rõ các nguồn (2 hay 3) |
| Cạnh chưa rõ chiều thầy→trò | **xám, nét CHẤM** (khác nét đứt) | |

Giữ nguyên (không đổi): nét liền = nối pháp / đồng môn / học trò; nét đứt = tham học chưa đắc pháp, chỉ quanh vị đang xem;
Main tree dày gấp đôi; chú thích hiện 2 chỗ (khung cây + panel trái cạnh khối tính số đời).

Chú thích "Cách đọc cây truyền thừa" đổi 3 dòng màu thành: **Xanh — DILA** · **Vàng — Marcus** · **Đỏ — TTL** ·
**Nhiều nguồn khớp** (mẫu màu theo nền: trắng/bạc trên nền tối, đen trên nền sáng) — từ 2 nguồn trở lên ghi giống nhau (khớp ID thầy và trò) · **Xám chấm — chưa rõ chiều thầy→trò**; giữ 3 dòng nét dày / liền / đứt.
done_when (1)(2) đọc "3 màu theo số nguồn" ⇒ hiểu là bảng màu theo nguồn này.

**Admin chốt câu (a) 2026-10-19 07:17:** *"Nếu cùng 1 thông tin giống nhau thì ta ghi thành 1 màu đen tượng trưng cho data
đều chính xác về ID thầy và trò, nếu có kết quả khác thì dùng màu của từng cây riêng."* ⇒ Cạnh 2 hoặc 3 nguồn khớp nhau = **đen**.
Nguồn nào ghi một quan hệ khác (thầy khác, chỉ nguồn đó có) thì cạnh đó vẽ **màu của nguồn đó** (xanh/vàng/đỏ).
Ví dụ Đơn Hà: Thạch Đầu → Đơn Hà (3 nguồn) đen; Kính Sơn Đạo Khâm → Đơn Hà (DILA + Marcus) đen, nét đứt (tham học).

**Admin chốt câu (b) 2026-10-19 07:25:** nền tối dùng **trắng/bạc** thay cho "đen"; nền sáng dùng **đen** (thích ứng nền).
Chống nhầm "trắng ≠ đen" (Admin lưu ý): chú thích và tooltip KHÔNG ghi chữ "Đen"; ghi theo ý nghĩa và mẫu màu đúng như
đang vẽ — ví dụ "━ (mẫu trắng/bạc) **Nhiều nguồn khớp** — từ 2 nguồn trở lên ghi giống nhau". Dùng 1 biến CSS
(ví dụ `--edge-agree`: #e5e7eb trên nền tối, #111 trên nền sáng) cho cả nét vẽ lẫn mẫu chú thích.

**[ĐÃ CHỐT — giữ để tham khảo] Câu hỏi mở cũ:**
- (b) Khung vẽ cây đang nền tối ⇒ nét đen gần như không thấy. Chọn: ① đổi nền cây sang sáng; ② nét đen có viền sáng;
  ③ nền tối dùng trắng/bạc thay đen (nền sáng vẫn đen).

**Phụ thuộc:** để biết cạnh nào là "nối pháp" cần nhãn loại quan hệ — hiện `lineage_primary_teacher` chỉ ~3.200 cạnh
`dharma_transmission` (Marcus) + 569 TTL, ~19.600 cạnh "unknown" (kể cả Hy Thiên → Đơn Hà). Việc gắn nhãn tách thành
**T414 / BUG-039**. Trong lúc chưa có nhãn: cạnh "unknown" vẽ theo quy tắc tạm do Admin chốt (xem T414, câu hỏi mở).

**Điểm chờ Admin:** đỏ trước đây còn dùng cho cạnh **xung đột** (#ff7b72, hai nguồn chỉ ra hai thầy khác nhau). Đề xuất
đổi xung đột sang ký hiệu riêng (ví dụ nét đỏ + biểu tượng ⚠ trên cạnh, hoặc màu tím đậm) để không lẫn với "1 nguồn".
Hermes chưa đổi màu xung đột cho tới khi Admin chốt.

## Phạm vi

Được sửa: `places.html` (khối legend + `_t127EdgeStyle` + đoạn vẽ canvas), và nếu cần `app.py` (chỉ để trả thêm
`edge_color` cho cạnh ancestor-spine, đọc-only, không ghi DB). Cấm: ghi DB, đổi schema, đổi bảng màu 4 nguồn, deploy, push.
Sao lưu trước khi sửa vào `docs/sessions/<ngày>/*.bak-before-T410`. Tránh sửa cùng lúc với T411 (cùng file places.html).

## Các bước

- [x] RC kiểm hiện trạng + chụp ảnh trước (2026-10-15)
- [x] Sao lưu places.html + app.py → docs/sessions/2026-10-19/*.bak-before-T410 (2026-10-19)
- [x] Gỡ 2 dòng chú thích + khối Y-fork 4 dòng + đổi #lineage-legend-row (legend thứ ba)
- [x] Bỏ màu cam/amber/xám/tím/xanh dương trong _t127EdgeStyle và afterDrawing; trục chính/spine chỉ nhấn bằng độ dày
- [x] Mọi cạnh có token nguồn (backend edge_color_token hoặc frontend _t410TokenForEdge); spine = 'agree' khi API
      không trả trường consensus (không bịa nguồn)
- [x] Ảnh sau + grep chuỗi cũ = 0 (xem "Kết quả đo được")
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE

## Kết quả đo được (2026-10-19)

**Grep places.html — 0 chuỗi cũ:** `#e8941a` `#e07820` `#d4a030` `#6b7a8a` `#3b82f6` `#eab308` = 0 ·
"Chú thích màu nét" = 0 · "Nét liền cam đậm" = 0 · "Nét đứt xám" = 0 · "Y-fork · 3 nguồn" = 0.
(`#a855f7` còn 1 lần nhưng là màu category `dynasty_region` trên bản đồ — KHÔNG phải nét truyền thừa.)

**Grep app.py — 0 hex cũ** trong calculate_edge_color_and_divergence; `edge_color_token` xuất hiện 8 lần; `py_compile` OK.

**Bằng chứng trình duyệt (Playwright + Edge headless, 127.0.0.1:8080):**

| Đường dẫn | Theme | Nét vẽ | Ghi chú |
|---|---|---|---|
| `?mode=lineage&focus=A004980&lm=tree` | dark | agree 691 · unknown 763 · ttl 64 · dila 28 | legend 6 dòng + cảnh báo "⚠ 2 cạnh chỉ 1 nguồn" |
| `?mode=lineage&focus=A004980&lm=tree` | light | ttl 392 · unknown 997 | token sáng: dila #0284c7, agree #0f172a |
| `?mode=lineage&focus=A009460&lm=tree` | dark | agree 769 · ttl 36 · unknown 141 | |
| `?mode=lineage&focus=A047924&lm=tree` | dark | **ttl 1435** · agree 612 | A047924 có 33 cạnh TTL ⇒ đỏ Dominant, đúng kỳ vọng |

**Nét cũ = 0 (audit pixel trong vùng canvas, dung sai 24):** `#e07820` 0 · `#a855f7` 0 · `#3b82f6` 0 · `#22c55e` 0 ở cả 6 ảnh.
`#e8941a` 6 px và `#eab308` 17 px có bbox GIỐNG HỆT nhau ở cả 6 ảnh (1,47,137,142) và (3,441,2,142) ⇒ là phần tử UI cố định
(chữ/viền), KHÔNG phải nét cây. `#d4a030` ~204–267 px cùng bbox mọi ảnh ⇒ chữ vàng `--da-gold`. `#6b7a8a` bị đếm nhầm do
nằm trong tolerance của `--edge-unknown` light (#64748b, khoảng cách 14 ≤ 24).

**Ảnh:** `docs/sessions/2026-10-19/t410_{A004980,A009460,A047924}_{dark,light}.png` +
`t410-screenshot-probe.json` (giá trị CSS var thực tế + nội dung legend).
