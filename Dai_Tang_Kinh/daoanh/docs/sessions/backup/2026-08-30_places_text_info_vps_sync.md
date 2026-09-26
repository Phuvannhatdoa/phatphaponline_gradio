# 2026-08-30 — Fix places text_info + Kế hoạch rsync local → VPS

## Mô tả ngắn task

Session này gồm 2 phần: (1) fix bug `places/index.html` trên VPS không hiển thị `text_info` trong
panel bên trái địa danh; (2) phê chuẩn và ghi chép kế hoạch đồng bộ toàn bộ code local Windows
lên VPS bằng `rsync`.

---

## Phần 1 — Fix places/index.html: hiển thị VĂN BẢN LIÊN QUAN

### Vấn đề

Panel bên trái địa danh (ví dụ Thiếu Lâm Tự `PL000000023255`) luôn hiển thị "Chưa có ghi chú
Việt ngữ cho địa danh này." dù API đã trả về trường `text_info` đầy đủ (title_vi, dynasty_vi,
sh_number, juans...). HTML chưa có section render `text_info` và JS chưa có code xử lý.

### Fix

Patch file `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/places/index.html`
trên VPS bằng Python script upload qua `scp` (tránh lỗi heredoc shell quoting):

**HTML thêm** (trước section "LIÊN QUAN NIÊN ĐẠI"):
```html
<div class="pp-card p-6 bg-white/[0.02]" id="textInfoCard" style="display:none">
    <h4 class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
        <span class="w-5 h-[1px] bg-amber-500"></span> VĂN BẢN LIÊN QUAN
    </h4>
    <div id="textInfoContent" class="space-y-2 text-[12px] text-slate-300"></div>
</div>
```

**JS thêm** (sau dòng render `itemBio`):
```js
const ti = d.text_info;
const tiCard = document.getElementById('textInfoCard');
const tiContent = document.getElementById('textInfoContent');
if (ti && tiCard && tiContent) {
    tiCard.style.display = '';
    tiContent.innerHTML = [
        ti.title_vi   ? `<p><span class="text-amber-500 font-bold">Tiêu đề:</span> ${ti.title_vi}</p>` : '',
        ti.title_zh   ? `<p class="serif italic text-slate-400">${ti.title_zh}</p>` : '',
        ti.dynasty_vi ? `<p><span class="text-amber-500 font-bold">Triều đại:</span> ${ti.dynasty_vi}</p>` : '',
        ti.juans      ? `<p><span class="text-amber-500 font-bold">Số quyển:</span> ${ti.juans}</p>` : '',
        ti.sh_number  ? `<p class="text-slate-500 text-[10px]">SH: ${ti.sh_number}${ti.q_number ? ' · Q: '+ti.q_number : ''}${ti.page ? ' · Tr. '+ti.page : ''}</p>` : '',
        ti.source_note ? `<p class="text-slate-500 text-[11px] italic mt-2">${ti.source_note}</p>` : '',
        ti.license_name ? `<p class="text-slate-600 text-[10px] mt-1">${ti.license_name}</p>` : ''
    ].join('');
} else if (tiCard) {
    tiCard.style.display = 'none';
}
```

### Kỹ thuật đáng ghi

- **Heredoc SSH lỗi**: Python script inline qua heredoc bị lỗi do nháy đơn xung đột shell. Fix:
  tạo file `.py` riêng → `scp` upload → SSH chạy `python3`.
- **Browser cache**: sau khi patch VPS, browser vẫn dùng HTML cũ → `textInfoCard` NOT FOUND IN DOM.
  Fix: hard reload `window.location.reload(true)`.
- **`await` top-level trong `javascript_tool`**: lỗi "await is only valid in async functions".
  Fix: dùng `new Promise(resolve => setTimeout(...))`.

### Kết quả verify

Chọn Thiếu Lâm Tự trên production `https://phatphaponline.org/daoanh/places/` → panel bên trái
hiển thị đúng section "VĂN BẢN LIÊN QUAN" với: Tiêu đề "Thiếu Lâm Vô Khổng Địch", 少林無孔笛
(六卷), Triều đại Nhật Bản, Số quyển 6, SH: 2571 · Q: 81 · Tr. 347. ✅

---

## Phần 2 — Kế hoạch rsync: đồng bộ local Windows → VPS (đã phê chuẩn)

### Vấn đề

Code local và VPS còn khác nhau sau nhiều lần patch thủ công. User muốn đồng bộ **100%** local
source lên VPS mà không sửa từng file một.

### Kế hoạch rsync (đã phê chuẩn)

```bash
# Chạy trong Git Bash trên Windows
rsync -avz --delete \
  --exclude='*.db' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  -e "ssh -i ~/.ssh/vps_phatphap" \
  "/e/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/" \
  root@158.220.106.183:/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/
```

**Sau khi rsync xong**, restart Flask trên VPS:
```bash
# SSH vào VPS, tìm PID Flask
ssh -i ~/.ssh/vps_phatphap root@158.220.106.183
screen -ls          # xem session
# hoặc
pkill -f "python.*app.py" && sleep 2
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
screen -dmS flask python app.py
```

### Lưu ý quan trọng

- `--delete`: xóa trên VPS các file không còn tồn tại local — dùng cẩn thận, không rsync vào
  nhầm thư mục.
- Exclude `*.db`: database `lineage.db` + `cbeta.db` **KHÔNG** đồng bộ từ local (db production
  trên VPS là bản thật, có dữ liệu user; db local có thể khác).
- SSH key: `~/.ssh/vps_phatphap` (ed25519, đã setup từ các session trước).
- Source path phải kết thúc bằng `/` (rsync sync NỘI DUNG thư mục, không phải chính thư mục).

### Trạng thái

Kế hoạch đã phê chuẩn, **chưa chạy rsync** — ghi lại để admin thực hiện (xem tasks T23–T26).

---

## File đã sửa

- `places/index.html` (VPS, patch trực tiếp) — thêm section VĂN BẢN LIÊN QUAN

## Liên hệ ROADMAP

- Sau khi rsync xong: verify production khớp local, tiếp tục T11 (RAG Việt chat) hoặc T12.
- Disk VPS: đã dọn từ session trước (cleanup.sh đã update). Cần theo dõi nếu log tăng lại.
