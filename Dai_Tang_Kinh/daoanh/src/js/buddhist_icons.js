/**
 * A3: Buddhist Map Icons
 * Custom marker icons for different place types
 */

const BuddhistIcons = {
    // Default icons from Leaflet
    defaultIcon: L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        shadowSize: [41, 41],
        shadowAnchor: [12, 41]
    }),

    // Buddhist-themed custom icons
    icons: {
        // Sacred sites
        'stupa': {
            html: '<div class="buddhist-icon stupa" title="Bảo tháp">⛩️</div>',
            className: 'buddhist-marker stupa-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        'temple': {
            html: '<div class="buddhist-icon temple" title="Chùa">🏛️</div>',
            className: 'buddhist-marker temple-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        'monastery': {
            html: '<div class="buddhist-icon monastery" title="Tự/Tàng">🕉️</div>',
            className: 'buddhist-marker monastery-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Dharma wheel
        'dharmachakra': {
            html: '<div class="buddhist-icon dharmachakra" title="Pháp luân">☸️</div>',
            className: 'buddhist-marker dharma-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Footprint
        'footprint': {
            html: '<div class="buddhist-icon footprint" title="Dấu chân">👣</div>',
            className: 'buddhist-marker footprint-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Pagoda
        'pagoda': {
            html: '<div class="buddhist-icon pagoda" title="Tháp">🗼</div>',
            className: 'buddhist-marker pagoda-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Mountain/Temple
        'mountain': {
            html: '<div class="buddhist-icon mountain" title="Sơn Tự">⛰️</div>',
            className: 'buddhist-marker mountain-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Cave
        'cave': {
            html: '<div class="buddhist-icon cave" title="Động">🕳️</div>',
            className: 'buddhist-marker cave-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Monk location
        'monk': {
            html: '<div class="buddhist-icon monk" title="Thiền sư">👨‍�️</div>',
            className: 'buddhist-marker monk-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        },
        
        // Default fallback
        'default': {
            html: '<div class="buddhist-icon default" title="Địa danh">📍</div>',
            className: 'buddhist-marker default-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        }
    },

    /**
     * Get icon for place type
     */
    getIcon: function(type) {
        const iconConfig = this.icons[type] || this.icons['default'];
        return L.divIcon(iconConfig);
    },

    /**
     * Get icon by place properties
     */
    getIconForPlace: function(place) {
        const type = this.determineType(place);
        return this.getIcon(type);
    },

    /**
     * Determine place type from properties
     */
    determineType: function(place) {
        const name = (place.nameVietnamese || place.nameChinese || '').toLowerCase();
        const type = place.type || '';
        
        // Check name keywords
        if (name.includes('tháp') || name.includes('塔')) return 'pagoda';
        if (name.includes('chùa') || name.includes('寺')) return 'temple';
        if (name.includes('tự') || name.includes('寺')) return 'monastery';
        if (name.includes('động') || name.includes('洞')) return 'cave';
        if (name.includes('sơn') || name.includes('山')) return 'mountain';
        if (name.includes('pháp luân') || name.includes('法輪')) return 'dharmachakra';
        if (name.includes('dấu chân') || name.includes('脚印')) return 'footprint';
        if (name.includes('bảo tháp') || name.includes('塔')) return 'stupa';
        
        // Check type field
        if (type === 'pagoda') return 'pagoda';
        if (type === 'temple') return 'temple';
        if (type === 'monastery') return 'monastery';
        if (type === 'cave') return 'cave';
        if (type === 'mountain') return 'mountain';
        
        // Check country/region
        if (place.region === 'India') return 'stupa';
        if (place.region === 'China') return 'pagoda';
        if (place.region === 'Vietnam') return 'temple';
        
        return 'default';
    },

    /**
     * Create custom marker with type
     */
    createMarker: function(lat, lon, place, options = {}) {
        const icon = this.getIconForPlace(place);
        return L.marker([lat, lon], { ...options, icon });
    },

    /**
     * Register custom icons with Leaflet
     */
    registerIcons: function() {
        // Add CSS for custom icons
        const style = document.createElement('style');
        style.textContent = `
            .buddhist-marker {
                background: transparent;
                border: none;
            }
            .buddhist-icon {
                font-size: 24px;
                line-height: 32px;
                text-align: center;
                filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.5));
                cursor: pointer;
                transition: transform 0.2s;
            }
            .buddhist-icon:hover {
                transform: scale(1.2);
            }
            .stupa-marker .buddhist-icon { color: #FFD700; }
            .temple-marker .buddhist-icon { color: #FF6B6B; }
            .monastery-marker .buddhist-icon { color: #4ECDC4; }
            .pagoda-marker .buddhist-icon { color: #9B59B6; }
            .mountain-marker .buddhist-icon { color: #27AE60; }
            .cave-marker .buddhist-icon { color: #3498DB; }
            .dharma-marker .buddhist-icon { color: #E67E22; }
            .footprint-marker .buddhist-icon { color: #1ABC9C; }
            .monk-marker .buddhist-icon { color: #E74C3C; }
            .default-marker .buddhist-icon { color: #95A5A6; }
            
            /* Popup styling */
            .leaflet-popup-content-wrapper {
                border-radius: 8px;
                box-shadow: 0 3px 14px rgba(0,0,0,0.4);
            }
            .leaflet-popup-content {
                margin: 12px;
            }
            .popup-content h3 {
                margin: 0 0 8px 0;
                color: #2C3E50;
                font-size: 16px;
            }
            .popup-content .names {
                font-size: 12px;
                color: #7F8C8D;
                margin-bottom: 8px;
            }
            .popup-content .name-zh {
                font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
            }
            .popup-content .info {
                font-size: 13px;
            }
            .popup-content .info-row {
                display: flex;
                justify-content: space-between;
                margin: 4px 0;
            }
            .popup-content .info-label {
                color: #95A5A6;
            }
            .popup-content .period-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
            }
            .period-india { background: #FFEBEE; color: #C62828; }
            .period-china { background: #E0F7FA; color: #006064; }
            .period-vietnam { background: #E8F5E9; color: #2E7D32; }
        `;
        document.head.appendChild(style);
    }
};

// Auto-register when loaded
if (typeof document !== 'undefined') {
    BuddhistIcons.registerIcons();
}

// Export for use
if (typeof window !== 'undefined') {
    window.BuddhistIcons = BuddhistIcons;
}
