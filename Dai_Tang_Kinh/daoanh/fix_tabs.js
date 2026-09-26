/* Fix 15 TABs tab bar - replace 6 tabs with 15 tabs in scrollable strip */
document.addEventListener('DOMContentLoaded', function() {
    const tabBar = document.getElementById('da-stabs');
    if (!tabBar) return;
    
    // Replace with 15 tabs (scrollable horizontal strip)
    tabBar.innerHTML = `
        <button class="da-stab active" data-t="entity">地 Thực Thể</button>
        <button class="da-stab" data-t="daitang">📜 Đại Tạng</button>
        <button class="da-stab" data-t="graph">🕸 Đồ Thị</button>
        <button class="da-stab" data-t="persons">🧑 Nhân Vật</button>
        <button class="da-stab" data-t="lineage">🌳 Truyền Thừa</button>
        <button class="da-stab" data-t="timeline">⏱ Niên Đại</button>
        <button class="da-stab" data-t="giaoly">🔍 Giáo Lý</button>
        <button class="da-stab" data-t="thuvien">📚 Thư Viện</button>
        <button class="da-stab" data-t="nghile">🙏 Nghi Lễ</button>
        <button class="da-stab" data-t="giaoduc">🎓 Giáo Dục</button>
        <button class="da-stab" data-t="sukien">⚡ Sự Kiện</button>
        <button class="da-stab" data-t="bandoo">🗺 Bản Đồ</button>
        <button class="da-stab" data-t="dulieu">📊 Dữ Liệu</button>
        <button class="da-stab" data-t="hinhanh">🖼 Hình Ảnh</button>
        <button class="da-stab" data-t="nghethuat">🎨 Nghệ Thuật</button>
    `;
});