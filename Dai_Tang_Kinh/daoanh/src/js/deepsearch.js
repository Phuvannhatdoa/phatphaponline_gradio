/**
 * P13: Deep-Sync Integration
 * Click Marker → Query CBETA → Display Sutra References
 * Integration with Deepsearch API
 */

const DeepSync = {
    cache: {},
    apiEndpoint: '/api/search',
    cbetaBaseUrl: 'https://cbetaonline.cnr.tw/',

    /**
     * Initialize Deep-Sync
     */
    init: function() {
        console.log("🔗 Deep-Sync initialized");
    },

    /**
     * Search CBETA for sutras mentioning a place
     */
    searchSutras: async function(placeName, placeId) {
        const cacheKey = `place_${placeId}`;
        
        // Check cache first
        if (this.cache[cacheKey]) {
            console.log("📦 Using cached results for", placeName);
            return this.cache[cacheKey];
        }

        console.log("🔍 Searching CBETA for:", placeName);

        // Simulated CBETA results (in production, would call actual API)
        const results = this.getSimulatedResults(placeName, placeId);
        
        // Cache results
        this.cache[cacheKey] = results;
        
        return results;
    },

    /**
     * Get simulated CBETA results (for demo)
     */
    getSimulatedResults: function(placeName, placeId) {
        const placeSutraMap = {
            'Thiếu Lâm Tự': [
                { title: 'Cảnh Đức Truyền Đăng Lục', ref: 'T51n2076', vol: '51', page: '217', text: '初，達磨大師至少林寺，面壁九年，終日默坐...' },
                { title: 'Tứ Thánh Truyện', ref: 'T49n2023', vol: '49', page: '56', text: '達磨祖師度慧可，面壁少林九年...' }
            ],
            'Lộc Uyển': [
                { title: 'Đại Phương Đãm Phổ Ngữ', ref: 'T01n0001', vol: '1', page: '1', text: '一時佛在舍衛國祇樹給孤獨園，與大比丘眾千二百五十人俱...' },
                { title: 'Xá Lợi Phất Vấn', ref: 'T04n0125', vol: '4', page: '125', text: '時阿難在拘薩羅國遊行...' }
            ],
            'Kỳ Viên': [
                { title: 'Đại Phương Đãm Phổ Ngữ', ref: 'T01n0001', vol: '1', page: '1', text: '一時佛在舍衛國祇樹給孤獨園...' }
            ],
            'Xá Vệ': [
                { title: 'Nhiếp Chánh Luận', ref: 'T48n2010', vol: '48', page: '365', text: '舍衛國中有逝心...' }
            ]
        };

        // Find matches
        for (const [key, sutras] of Object.entries(placeSutraMap)) {
            if (placeName.includes(key) || key.includes(placeName)) {
                return {
                    placeName: placeName,
                    placeId: placeId,
                    sutras: sutras,
                    count: sutras.length
                };
            }
        }

        // Default - no results
        return {
            placeName: placeName,
            placeId: placeId,
            sutras: [],
            count: 0,
            message: "Chưa có dữ liệu kinh văn cho địa điểm này"
        };
    },

    /**
     * Display sutra results in workbench
     */
    displayResults: function(results) {
        const workbenchContent = document.querySelector('.workbench-content');
        if (!workbenchContent) {
            console.error("Workbench content not found");
            return;
        }

        if (results.count === 0) {
            workbenchContent.innerHTML = `
                <div class="text-panel" style="grid-column: 1/-1;">
                    <h5>Kết quả CBETA</h5>
                    <p class="viet-text">${results.message || 'Không tìm thấy kinh văn liên quan'}</p>
                </div>
            `;
            return;
        }

        // Generate HTML for sutras
        let html = '';
        results.sutras.forEach((sutra, index) => {
            html += `
                <div class="sutra-item" style="margin-bottom: 20px; padding: 16px; background: white; border-radius: 12px; border: 1px solid #e2e8f0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 10px; font-weight: 700; background: #78350f; color: white; padding: 2px 8px; border-radius: 4px;">${sutra.ref}</span>
                        <span style="font-size: 9px; color: #94a3b8;">Vol.${sutra.vol} P.${sutra.page}</span>
                    </div>
                    <h5 style="font-size: 14px; font-weight: bold; color: #78350f; margin-bottom: 8px;">${sutra.title}</h5>
                    <p class="han-nom" style="font-size: 14px; color: #475569; margin-bottom: 8px;">${sutra.text}</p>
                    <a href="${this.cbetaBaseUrl}${sutra.ref}" target="_blank" style="font-size: 10px; color: #2563eb; text-decoration: none;">
                        <i class="fa-solid fa-external-link-alt"></i> Xem trên CBETA Online
                    </a>
                </div>
            `;
        });

        workbenchContent.innerHTML = html;
    },

    /**
     * Handle marker click - trigger deep sync
     */
    onMarkerClick: function(place) {
        console.log("🔗 Deep-Sync: Marker clicked for", place.nameVietnamese || place.nameChinese);
        
        // Show loading in workbench
        const workbenchContent = document.querySelector('.workbench-content');
        if (workbenchContent) {
            workbenchContent.innerHTML = `
                <div class="text-panel" style="grid-column: 1/-1; text-align: center; padding: 40px;">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size: 24px; color: #78350f;"></i>
                    <p style="margin-top: 12px; color: #94a3b8; font-size: 12px;">Đang truy vết CBETA...</p>
                </div>
            `;
        }

        // Search sutras
        const placeName = place.nameVietnamese || place.nameChinese || place.nameEnglish;
        const placeId = place.id || 'unknown';
        
        this.searchSutras(placeName, placeId).then(results => {
            this.displayResults(results);
        });
    },

    /**
     * Clear cache
     */
    clearCache: function() {
        this.cache = {};
        console.log("📦 Cache cleared");
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    DeepSync.init();
});