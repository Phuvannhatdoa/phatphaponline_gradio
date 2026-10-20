/* Search input for home.html - Identity Hub search */
document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('.da-header');
    if (!header) return;
    
    // Add search box to header
    const searchContainer = document.createElement('div');
    searchContainer.className = 'da-search-container';
    searchContainer.innerHTML = `
        <div class="da-search-box">
            <input type="text" id="homeSearchInput" placeholder="Tìm kiếm địa danh, tăng nhân..." 
                   autocomplete="off" 
                   onkeyup="homeSearch this.value">
            <button type="button" onclick="homeSearch(document.getElementById('homeSearchInput').value)" class="da-search-btn">🔍</button>
        </div>
    `;
    
    // Insert after logo
    const logo = header.querySelector('.da-header-logo');
    if (logo) {
        logo.parentNode.insertBefore(searchContainer, logo.nextSibling);
    }
});

function homeSearch(query) {
    if (!query || query.trim().length < 2) return;
    
    const input = document.getElementById('homeSearchInput');
    input.style.display = 'none';
    const btn = document.querySelector('.da-search-btn');
    btn.style.display = 'none';
    
    // Show loading state
    const resultDiv = document.createElement('div');
    resultDiv.className = 'da-welcome-message';
    resultDiv.innerHTML = '<div class="da-loading">Đang tìm kiếm...</div>';
    document.getElementById('contentArea').innerHTML = '';
    document.getElementById('contentArea').appendChild(resultDiv);
    
    // Call API
    fetch('/daoanh/api/places/search?q=' + encodeURIComponent(query) + '&limit=10')
        .then(r => r.json())
        .then(data => {
            const results = data.results || data || [];
            let html = '<h4>Kết quả tìm kiếm cho: ' + query + '</h4>';
            if (results && results.length > 0) {
                html += '<ul class="da-search-results">';
                results.forEach(item => {
                    const name = item.name_vi || item.name_zh || item.name || '';
                    const dilaId = item.dila_id || '';
                    html += '<li><a href="/daoanh/places/' + dilaId + '">' + name + '</a></li>';
                });
                html += '</ul>';
            } else {
                html += '<p class="da-warn">Không tìm thấy kết quả</p>';
            }
            document.getElementById('contentArea').innerHTML = html;
        })
        .catch(() => {
            document.getElementById('contentArea').innerHTML = '<p class="da-error">Lỗi kết nối</p>';
        });
}