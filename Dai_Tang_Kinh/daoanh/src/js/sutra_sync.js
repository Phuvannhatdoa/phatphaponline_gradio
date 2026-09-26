/**
 * A4: Sutra-to-Map Sync
 * Click marker to show sutra text, deep search integration
 */

const SutraSync = {
    // API endpoints
    apiBase: '/daoanh/',
    
    // Cache for loaded sutras
    sutraCache: {},
    
    // Current selection
    currentPlace: null,
    currentSutra: null,
    
    /**
     * Initialize Sutra Sync
     */
    init: function() {
        this.bindEvents();
        console.log('✅ Sutra-to-Map Sync initialized');
    },
    
    /**
     * Bind click events from map markers
     */
    bindEvents: function() {
        // Listen for marker clicks from MapApp
        document.addEventListener('marker-click', (e) => {
            this.onMarkerClick(e.detail);
        });
        
        // Listen for sutra reference clicks
        document.addEventListener('sutra-ref-click', (e) => {
            this.loadSutraById(e.detail.sutraId);
        });
    },
    
    /**
     * Handle marker click - show sutra panel
     */
    onMarkerClick: async function(place) {
        this.currentPlace = place;
        
        // Find sutras referencing this place
        const sutras = await this.findSutrasForPlace(place);
        
        if (sutras.length > 0) {
            this.showSutraPanel(place, sutras);
        } else {
            this.showPlaceInfo(place);
        }
    },
    
    /**
     * Find sutras that reference a place
     */
    findSutrasForPlace: async function(place) {
        const placeName = place.nameChinese || place.nameVietnamese || '';
        if (!placeName) return [];
        
        try {
            // Call deep search API
            const response = await fetch(`${this.apiBase}api/deepsearch?q=${encodeURIComponent(placeName)}`);
            if (response.ok) {
                const data = await response.json();
                return data.results || [];
            }
        } catch (e) {
            console.warn('Deep search not available:', e);
        }
        
        // Fallback: check if place has sutra references
        return place.referenced_in || [];
    },
    
    /**
     * Load sutra by ID
     */
    async loadSutraById(sutraId) {
        // Check cache first
        if (this.sutraCache[sutraId]) {
            this.showSutraText(sutraId, this.sutraCache[sutraId]);
            return;
        }
        
        // Try to load from API
        try {
            const response = await fetch(`${this.apiBase}api/sutra/${sutraId}`);
            if (response.ok) {
                const data = await response.json();
                this.sutraCache[sutraId] = data;
                this.showSutraText(sutraId, data);
            }
        } catch (e) {
            console.error('Failed to load sutra:', e);
        }
    },
    
    /**
     * Show sutra panel with place info
     */
    showSutraPanel: function(place, sutras) {
        const panel = this.getPanel();
        panel.innerHTML = `
            <div class="sutra-panel">
                <div class="panel-header">
                    <h3>${place.nameVietnamese || place.nameChinese || 'Unknown'}</h3>
                    <button class="close-btn" onclick="SutraSync.closePanel()">×</button>
                </div>
                <div class="panel-body">
                    <div class="place-info">
                        ${place.nameChinese ? `<div class="name-zh">${place.nameChinese}</div>` : ''}
                        ${place.province ? `<div class="province">${place.province}</div>` : ''}
                        ${place.description ? `<div class="description">${place.description}</div>` : ''}
                    </div>
                    <div class="sutra-list">
                        <h4>Kinh văn tham chiếu (${sutras.length})</h4>
                        ${sutras.map(s => `
                            <div class="sutra-item" onclick="SutraSync.loadSutraById('${s.id || s}')">
                                <span class="sutra-id">${s.id || s}</span>
                                <span class="sutra-title">${s.title || ''}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        this.openPanel();
    },
    
    /**
     * Show place info without sutras
     */
    showPlaceInfo: function(place) {
        const panel = this.getPanel();
        panel.innerHTML = `
            <div class="sutra-panel">
                <div class="panel-header">
                    <h3>${place.nameVietnamese || place.nameChinese || 'Unknown'}</h3>
                    <button class="close-btn" onclick="SutraSync.closePanel()">×</button>
                </div>
                <div class="panel-body">
                    <div class="place-info">
                        ${place.nameChinese ? `<div class="name-zh">${place.nameChinese}</div>` : ''}
                        ${place.province ? `<div class="province">${place.province}</div>` : ''}
                        ${place.country ? `<div class="country">${place.country}</div>` : ''}
                        ${place.description ? `<div class="description">${place.description}</div>` : ''}
                        ${place.lat && place.lon ? `<div class="coords">📍 ${place.lat}, ${place.lon}</div>` : ''}
                    </div>
                    <div class="no-sutra">
                        <p>Chưa có kinh văn tham chiếu cho địa điểm này.</p>
                        <button onclick="SutraSync.searchDeep('${place.nameVietnamese || place.nameChinese}')">
                            Tìm kiếm sâu
                        </button>
                    </div>
                </div>
            </div>
        `;
        this.openPanel();
    },
    
    /**
     * Show sutra text
     */
    showSutraText: function(sutraId, sutraData) {
        const panel = this.getPanel();
        panel.innerHTML = `
            <div class="sutra-panel">
                <div class="panel-header">
                    <h3>${sutraData.title || sutraId}</h3>
                    <button class="close-btn" onclick="SutraSync.closePanel()">×</button>
                </div>
                <div class="panel-body">
                    <div class="sutra-meta">
                        ${sutraData.author ? `<div>Tác giả: ${sutraData.author}</div>` : ''}
                        ${sutraData.period ? `<div>Thời kỳ: ${sutraData.period}</div>` : ''}
                    </div>
                    <div class="sutra-content">
                        ${sutraData.content || 'Nội dung không có sẵn.'}
                    </div>
                    <div class="sutra-actions">
                        <button onclick="SutraSync.highlightPlaces('${sutraId}')">
                            Hiển thị trên bản đồ
                        </button>
                    </div>
                </div>
            </div>
        `;
        this.openPanel();
    },
    
    /**
     * Deep search for place references
     */
    async searchDeep(placeName) {
        try {
            const response = await fetch(`${this.apiBase}api/deepsearch?q=${encodeURIComponent(placeName)}`);
            if (response.ok) {
                const data = await response.json();
                this.showDeepSearchResults(placeName, data.results);
            }
        } catch (e) {
            console.error('Deep search failed:', e);
        }
    },
    
    /**
     * Show deep search results
     */
    showDeepSearchResults: function(query, results) {
        const panel = this.getPanel();
        panel.innerHTML = `
            <div class="sutra-panel">
                <div class="panel-header">
                    <h3>Tìm kiếm: ${query}</h3>
                    <button class="close-btn" onclick="SutraSync.closePanel()">×</button>
                </div>
                <div class="panel-body">
                    <div class="results-count">Tìm thấy ${results.length} kết quả</div>
                    <div class="search-results">
                        ${results.map(r => `
                            <div class="result-item" onclick="SutraSync.loadSutraById('${r.id}')">
                                <div class="result-title">${r.title || r.id}</div>
                                <div class="result-snippet">${r.snippet || ''}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        this.openPanel();
    },
    
    /**
     * Highlight places mentioned in sutra
     */
    highlightPlaces: function(sutraId) {
        // Emit event for map to highlight places
        const event = new CustomEvent('highlight-sutra-places', {
            detail: { sutraId }
        });
        document.dispatchEvent(event);
    },
    
    /**
     * Get panel element
     */
    getPanel: function() {
        let panel = document.getElementById('sutra-panel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'sutra-panel';
            panel.className = 'sutra-panel-container';
            document.body.appendChild(panel);
        }
        return panel;
    },
    
    /**
     * Open panel
     */
    openPanel: function() {
        const panel = this.getPanel();
        panel.classList.add('active');
    },
    
    /**
     * Close panel
     */
    closePanel: function() {
        const panel = this.getPanel();
        panel.classList.remove('active');
    }
};

// Auto-initialize when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => SutraSync.init());
} else {
    SutraSync.init();
}

// Export
if (typeof window !== 'undefined') {
    window.SutraSync = SutraSync;
}
