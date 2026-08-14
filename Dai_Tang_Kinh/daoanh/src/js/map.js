// Map Interface for Buddhist Heritage Mapping
const MapApp = {
    map: null,
    markers: {},
    layers: {
        india: null,
        china: null,
        vietnam: null
    },
    markerClusterGroup: null,
    allPlaces: [],
    timelineEntities: [],  // V32: Spatial timeline data
    filters: {
        layers: ['india', 'china', 'vietnam'],
        types: ['all'],
        yearRange: [-600, 2026],
        dynasty: '',
        entityType: '',
        region: ''
    },
    filteredCache: null,
    timeline: {
        playing: false,
        currentYear: 2026,
        interval: null
    },

    /**
     * Load entity timeline data for spatial visualization
     */
    loadEntityTimeline: async function() {
        try {
            const response = await fetch('/daoanh/ontology/json/entity_export_enriched.json');
            if (response.ok) {
                const data = await response.json();
                // Extract entities with GPS coordinates
                const entities = data.entities || [];
                const withGPS = entities.filter(e => {
                    const tl = e.spatial_timeline;
                    if (!tl || !tl.length) return false;
                    return tl.some(t => t.location && t.location.lat && t.location.lng);
                }).map(e => {
                    const tl = e.spatial_timeline.find(t => t.location && t.location.lat);
                    return {
                        id: e.id,
                        name: e.name,
                        hanName: e.han_name,
                        dynasty: e.dynasty,
                        bio: e.biography,
                        year: tl?.year || null,
                        lat: tl?.location?.lat,
                        lng: tl?.location?.lng,
                        locationName: tl?.location?.name,
                        graphConnections: e.graph_connections || []
                    };
                });
                this.timelineEntities = withGPS;
                console.log(`📍 Timeline entities with GPS: ${withGPS.length}`);
                return withGPS;
            }
        } catch(err) {
            console.warn('Failed to load entity timeline:', err);
        }
        return [];
    },

    /**
     * Initialize the map
     */
    init: function() {
        this.initMap();
        this.initLayers();
        this.initControls();
        this.initTimeline();
        this.loadPlaces();
        // V32: Load entity timeline data
        this.loadEntityTimeline();
    },

    /**
     * Initialize Leaflet map
     */
    initMap: function() {
        // Center on Vietnam (Hà Nội) with default zoom 11
        this.map = L.map('map', {
            center: [21.0285, 105.8342],  // Hà Nội
            zoom: 11,                       // Zoom 10-12 for VN detail
            minZoom: 2,
            maxZoom: 18,
            zoomControl: false
        });

        // Esri World Imagery - stable, good for Vietnam
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© Esri',
            maxZoom: 18
        }).addTo(this.map);

        // Initialize marker cluster group
        if (typeof L.markerClusterGroup !== 'undefined') {
            this.markerClusterGroup = L.markerClusterGroup({
                chunkedLoading: true,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                maxClusterRadius: 50,
                disableClusteringAtZoom: 16
            });
            this.markerClusterGroup.addTo(this.map);
        }
    },

    /**
     * Initialize layer groups
     */
    initLayers: function() {
        this.layers.india = L.layerGroup();
        this.layers.china = L.layerGroup();
        this.layers.vietnam = L.layerGroup();

        this.layers.india.addTo(this.map);
        this.layers.china.addTo(this.map);
        this.layers.vietnam.addTo(this.map);

        // Initialize marker cluster group
        this.markerClusterGroup = L.markerClusterGroup({
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            iconCreateFunction: function(cluster) {
                const count = cluster.getChildCount();
                let size = 'small';
                if (count > 100) size = 'large';
                else if (count > 10) size = 'medium';

                return L.divIcon({
                    html: `<div><span>${count}</span></div>`,
                    className: `marker-cluster marker-cluster-${size}`,
                    iconSize: L.point(40, 40)
                });
            }
        });
        this.markerClusterGroup.addTo(this.map);
    },

    /**
     * Initialize map controls
     */
    initControls: function() {
        // Zoom controls
        document.getElementById('zoom-in').addEventListener('click', () => this.map.zoomIn());
        document.getElementById('zoom-out').addEventListener('click', () => this.map.zoomOut());
        document.getElementById('reset-view').addEventListener('click', () => this.resetView());
        document.getElementById('locate-me').addEventListener('click', () => this.locateMe());

        // Layer toggles
        document.querySelectorAll('.layer-toggle input').forEach(input => {
            input.addEventListener('change', (e) => {
                this.toggleLayer(e.target.closest('.layer-toggle').dataset.layer, e.target.checked);
            });
        });

        // Filter chips
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
                e.target.classList.add('active');
                this.filters.types = [e.target.dataset.type];
                this.applyFilters();
            });
        });
    },

    /**
     * Initialize timeline
     */
    initTimeline: function() {
        const slider = document.getElementById('timeline-slider');
        const playBtn = document.getElementById('play-btn');

        if (!slider || !playBtn) return;  // Elements may not exist

        slider.addEventListener('input', (e) => {
            this.timeline.currentYear = parseInt(e.target.value);
            const yearDisplay = document.getElementById('year-display');
            if (yearDisplay) yearDisplay.textContent = this.formatYear(this.timeline.currentYear);
            this.filters.yearRange[1] = this.timeline.currentYear;
            this.applyFilters();
            
            // Update JDN for precision
            if (window.DilaAuthority) {
                this.timeline.currentJDN = DilaAuthority.lunarYearToJDN(this.timeline.currentYear);
                console.log(`📅 Year ${this.timeline.currentYear} → JDN ${this.timeline.currentJDN}`);
            }
        });

        playBtn.addEventListener('click', () => this.toggleTimeline());

        // Presets with JDN
        document.querySelectorAll('.timeline-preset').forEach(preset => {
            preset.addEventListener('click', (e) => {
                const range = e.target.dataset.range.split(',').map(Number);
                this.filters.yearRange = range;
                slider.value = range[1];
                const yearDisplay = document.getElementById('year-display');
                if (yearDisplay) yearDisplay.textContent = this.formatYear(range[1]);
                this.applyFilters();
                
                // Store JDN range
                if (window.DilaAuthority) {
                    this.timeline.jdnRange = [
                        DilaAuthority.lunarYearToJDN(range[0]),
                        DilaAuthority.lunarYearToJDN(range[1])
                    ];
                }
            });
        });
    },

    /**
     * Link DILA and geocoded Vietnam places via owl:sameAs
     * Matches by Chinese name
     */
    linkSameAs: function(allPlaces) {
        // Find places with same Chinese name but different sources
        const nameGroups = {};
        
        allPlaces.forEach(p => {
            const key = (p.nameChinese || "").toLowerCase().trim();
            if (key && key.length > 2) {
                if (!nameGroups[key]) nameGroups[key] = [];
                nameGroups[key].push(p);
            }
        });
        
        // Add sameAs links
        Object.values(nameGroups).forEach(group => {
            if (group.length > 1) {
                const primary = group[0];
                group.slice(1).forEach(secondary => {
                    if (!primary.sameAs) primary.sameAs = [];
                    // Avoid duplicates
                    if (!primary.sameAs.includes(secondary.id)) {
                        primary.sameAs.push(secondary.id);
                    }
                    // Mark secondary with reference to primary
                    secondary.sameAsLink = primary.id;
                });
            }
        });
        
        // Count linked
        const linked = allPlaces.filter(p => p.sameAs && p.sameAs.length > 0).length;
        console.log(`🔗 owl:sameAs links created: ${linked}`);
        
        return allPlaces;
    },

    /**
     * Load places from pre-generated map_data.json
     */
    loadPlaces: function() {
        // Load the preprocessed map data with monks linked
        fetch('/daoanh/data/indexed/map_data.json')
            .then(response => response.json())
            .then(data => {
                if (data && data.features) {
                    this.allPlaces = data.features;
                    console.log(`📍 Loaded ${this.allPlaces.length} places from map_data.json`);
                    this.renderMarkers();
                }
            })
            .catch(error => {
                console.warn('Failed to load map_data.json:', error);
                // Fallback to original loading
                this.loadCriticalPlaces().then(() => {
                    this.loadDilaPlacesChunked(0, 500);
                });
            });
    },
    
    /**
     * Load critical places only (small dataset - ~30 items)
     * Zero-RAM: This is intentional - small dataset needed for UI
     */
    loadCriticalPlaces: async function() {
        try {
            const response = await fetch('/daoanh/data/processed/search_index_critical.json');
            if (response.ok) {
                const data = await response.json();
                const criticalPlaces = data.map(c => ({
                    id: 'CRITICAL_' + c.searchKey,
                    nameVietnamese: c.vietnamese,
                    nameChinese: c.searchKey,
                    lat: c.gps?.lat,
                    lon: c.gps?.lon,
                    province: c.description?.split(',')[1] || "",
                    description: c.description || "",
                    source: 'Critical-Places',
                    type: c.type,
                    period: c.period,
                    relatedMonks: c.relatedMonks
                })).filter(p => p.lat && p.lon);
                
                this.allPlaces = [...this.allPlaces, ...criticalPlaces];
                console.log(`📍 Critical places loaded: ${criticalPlaces.length}`);
                this.renderMarkers();
            }
        } catch (error) {
            console.warn('Failed to load critical places:', error);
        }
    },
    
    /**
     * Load DILA places in chunks - Zero-RAM approach
     * Only load first N items, load more on demand
     */
    loadDilaPlacesChunked: function(offset, limit) {
        var self = this;
        fetch('/daoanh/data/places.json')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var places = (data.places || []).slice(offset, offset + limit);
                console.log('📍 DILA places (chunk ' + offset + '-' + (offset+limit) + '): ' + places.length);
                
                // Add to existing places
                if (places.length > 0) {
                    self.allPlaces = self.allPlaces.concat(places);
                    self.renderMarkers();
                }
                
                // Only update stats if elements exist
                if (document.getElementById('total-places')) {
                    self.updateStats();
                }
                self.hideLoading();
            })
            .catch(error => {
                console.warn('Failed to load DILA places:', error);
                this.hideLoading();
            });
    },
    
    /**
     * Setup lazy loading on map move
     * Only loads more data when user pans/zooms
     */
    setupLazyLoad: function() {
        if (!this.map) return;
        
        let loadTimeout;
        this.map.on('moveend', () => {
            clearTimeout(loadTimeout);
            loadTimeout = setTimeout(() => {
                // Check if we need more data
                this.checkLoadMoreData();
            }, 1000);
        });
    },
    
    /**
     * Check if we need to load more data based on viewport
     */
    checkLoadMoreData: function() {
        const bounds = this.map.getBounds();
        const visibleCount = this.allPlaces.filter(p => {
            return p.lat && p.lon && 
                   bounds.contains([p.lat, p.lon]);
        }).length;
        
        console.log(`📍 Visible places in viewport: ${visibleCount}`);
        // Could implement dynamic loading here if needed
    },

    /**
     * Render markers on map
     */
    renderMarkers: function() {
        this.markerClusterGroup.clearLayers();
        this.layers.india.clearLayers();
        this.layers.china.clearLayers();
        this.layers.vietnam.clearLayers();

        const filtered = this.getFilteredPlaces();

        filtered.forEach(place => {
            if (!place.lat || !place.lon) return;

            const period = this.getPeriod(place);
            const layer = this.getLayerGroup(period);
            
            const marker = this.createMarker(place, period);
            
            if (layer) {
                layer.addLayer(marker);
            }
        });

        this.updateVisibleCount(filtered.length);
    },

    /**
     * Create marker with custom icon
     */
    createMarker: function(place, period) {
        const color = this.getPeriodColor(period);
        
        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background:${color};width:20px;height:20px;border-radius:50%;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });

        // Use Buddhist Icons (A3) if available, otherwise fallback
        let marker;
        if (typeof BuddhistIcons !== 'undefined') {
            marker = BuddhistIcons.createMarker(place.lat, place.lon, place);
        } else {
            marker = L.marker([place.lat, place.lon], { icon });
        }

        marker.bindPopup(this.createPopupContent(place, period));
        // Add tooltip showing Vietnamese name first, fallback to Chinese
        const tooltipText = place.name_vi || place.name_zh || (place.properties && (place.properties.name_vi || place.properties.name_zh || place.properties.name)) || '';
        marker.bindTooltip(tooltipText, { permanent: true, direction: 'top' });

        return marker;
    },

    /**
     * Create popup content
     */
    createPopupContent: function(place, period) {
        const periodClass = `period-${period}`;
        
        // Build monks list
        let monksHtml = '';
        const monks = place.properties && place.properties.monks ? place.properties.monks : [];
        if (monks.length > 0) {
            monksHtml = `
                <div class="popup-section">
                    <div class="popup-title">Vị Tổ Trụ Trì:</div>
                    <div class="monks-list">
                        ${monks.map(monk => `
                            <div class="monk-item">
                                <div class="monk-name">${monk.name || 'Unknown'}</div>
                                ${monk.relationship ? `<div class="monk-relationship">${monk.relationship}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="popup-content">
                <h3>${place.properties.name_vi || place.properties.name || 'Unknown Temple'}</h3>
                ${monksHtml}
                <div class="popup-actions">
                    <button class="popup-btn" onclick="MapApp.showPlaceDetails('${place.properties.id}')">Chi tiết</button>
                    <button class="popup-btn sutra-btn" onclick="MapApp.showSutraReferences('${place.properties.id}')">Kinh văn</button>
                </div>
            </div>
        `;
    },

    /**
     * Get period for a place
     */
    getPeriod: function(place) {
        // Determine period based on country and other factors
        if (place.country === 'IN') return 'india';
        if (place.country === 'CN' || place.country === 'JP' || place.country === 'KR') return 'china';
        if (place.country === 'VN') return 'vietnam';
        
        // Fallback based on lat/lon
        if (place.lat > 20 && place.lon < 100) return 'india';
        if (place.lat > 20 && place.lon >= 100) return 'china';
        return 'vietnam';
    },

    /**
     * Get layer group for period
     */
    getLayerGroup: function(period) {
        switch (period) {
            case 'india': return this.layers.india;
            case 'china': return this.layers.china;
            case 'vietnam': return this.layers.vietnam;
            default: return this.layers.vietnam;
        }
    },

    /**
     * Get period color
     */
    getPeriodColor: function(period) {
        switch (period) {
            case 'india': return '#FF6B6B';
            case 'china': return '#4ECDC4';
            case 'vietnam': return '#95E1D3';
            default: return '#95E1D3';
        }
    },

    /**
     * Get period label
     */
    getPeriodLabel: function(period) {
        switch (period) {
            case 'india': return 'Ấn Độ';
            case 'china': return 'Trung Hoa';
            case 'vietnam': return 'Việt Nam';
            default: return 'Khác';
        }
    },

    /**
     * Get country name
     */
    getCountryName: function(code) {
        const countries = {
            'IN': 'Ấn Độ',
            'CN': 'Trung Quốc',
            'JP': 'Nhật Bản',
            'KR': 'Hàn Quốc',
            'VN': 'Việt Nam',
            'TH': 'Thái Lan',
            'MM': 'Myanmar',
            'NP': 'Nepal',
            'LK': 'Sri Lanka'
        };
        return countries[code] || code;
    },

    /**
     * Toggle layer visibility
     */
    toggleLayer: function(layer, visible) {
        if (visible) {
            this.layers[layer].addTo(this.map);
            this.filters.layers.push(layer);
        } else {
            this.map.removeLayer(this.layers[layer]);
            this.filters.layers = this.filters.layers.filter(l => l !== layer);
        }
        this.applyFilters();
    },

    /**
     * Apply entity filters from dropdown (dynasty, type, region)
     */
    applyEntityFilters: function(filters) {
        this.filters.dynasty = filters.dynasty;
        this.filters.entityType = filters.type;
        this.filters.region = filters.region;
        
        this.applyFilters();
        console.log('🏷️ Entity filters applied:', filters);
    },

    /**
     * Get filtered places
     */
    getFilteredPlaces: function() {
        return this.allPlaces.filter(place => {
            // Layer filter
            const period = this.getPeriod(place);
            if (!this.filters.layers.includes(period)) return false;

            // Type filter
            if (!this.filters.types.includes('all')) {
                // Place type filtering (can be expanded)
            }

            // Dynasty filter from entity filter
            if (this.filters.dynasty && this.filters.dynasty !== '') {
                const placeDynasty = place.period || '';
                if (!placeDynasty.toLowerCase().includes(this.filters.dynasty.toLowerCase())) {
                    return false;
                }
            }

            // Entity type filter
            if (this.filters.entityType && this.filters.entityType !== '') {
                const placeType = place.type || '';
                if (this.filters.entityType === 'Tự' && placeType !== 'monastery') return false;
                if (this.filters.entityType === 'Pháp' && placeType !== 'lineage') return false;
                if (this.filters.entityType === 'Tháp' && placeType !== 'stupa') return false;
            }

            // Region filter
            if (this.filters.region && this.filters.region !== '') {
                const gps = place.gps || {};
                const lat = gps.lat;
                // Simple region detection
                if (this.filters.region === 'Việt Nam' && lat && lat > 22) return true; // North Vietnam
                if (this.filters.region === 'Trung Quốc' && lat && lat > 20 && lat < 45) return true;
                if (this.filters.region === 'Ấn Độ' && lat && lat < 30) return true;
                // For other cases, check description
                const desc = place.description || '';
                if (this.filters.region === 'Việt Nam' && !desc.includes('Việt Nam')) return false;
                if (this.filters.region === 'Trung Quốc' && !desc.includes('Trung Quốc')) return false;
            }

            // Timeline filter - JDN based
            const currentYear = this.timeline.currentYear || this.filters.yearRange[1];
            if (window.DilaAuthority && currentYear) {
                const currentJDN = DilaAuthority.lunarYearToJDN(currentYear);
                const jdnStart = place.jdnStart;
                const jdnEnd = place.jdnEnd;
                
                // Show place if it was active in the selected year
                // If no JDN data, show all places (backward compatibility)
                if (jdnStart && jdnEnd) {
                    if (currentJDN < jdnStart || currentJDN > jdnEnd) {
                        return false;
                    }
                } else if (jdnStart) {
                    // If only start exists, show from that year onwards
                    if (currentJDN < jdnStart) return false;
                }
            }

            return true;
        });
    },

    /**
     * Apply filters with caching
     */
    applyFilters: function() {
        // Invalidate cache when filters change
        this.filteredCache = null;
        this.renderMarkers();
    },

    /**
     * Get cached filtered places (performance optimization)
     */
    getFilteredPlacesCached: function() {
        if (this.filteredCache) {
            return this.filteredCache;
        }
        
        this.filteredCache = this.getFilteredPlaces();
        return this.filteredCache;
    },

    /**
     * Update statistics
     */
    updateStats: function() {
        var total = this.allPlaces.length;
        var india = this.allPlaces.filter(function(p) { return this.getPeriod(p) === 'india'; }.bind(this)).length;
        var china = this.allPlaces.filter(function(p) { return this.getPeriod(p) === 'china'; }.bind(this)).length;
        var vietnam = this.allPlaces.filter(function(p) { return this.getPeriod(p) === 'vietnam'; }.bind(this)).length;

        var el = document.getElementById('total-places');
        if (el) el.textContent = total;
        var elIndia = document.getElementById('count-india');
        if (elIndia) elIndia.textContent = india;
        var elChina = document.getElementById('count-china');
        if (elChina) elChina.textContent = china;
        var elVietnam = document.getElementById('count-vietnam');
        if (elVietnam) elVietnam.textContent = vietnam;
    },

    /**
     * Update visible count
     */
    updateVisibleCount: function(count) {
        var el = document.getElementById('visible-places');
        if (el) el.textContent = count;
    },

    /**
     * Format year for display
     */
    formatYear: function(year) {
        if (year < 0) return `${Math.abs(year)} TCN`;
        return year;
    },

    /**
     * Toggle timeline play/pause
     */
    toggleTimeline: function() {
        this.timeline.playing = !this.timeline.playing;
        const btn = document.getElementById('play-btn');
        
        if (this.timeline.playing) {
            btn.textContent = '⏸ Dừng';
            this.timeline.interval = setInterval(() => {
                if (this.timeline.currentYear > -600) {
                    this.timeline.currentYear--;
                    document.getElementById('timeline-slider').value = this.timeline.currentYear;
                    document.getElementById('year-display').textContent = this.formatYear(this.timeline.currentYear);
                    this.filters.yearRange[1] = this.timeline.currentYear;
                    this.applyFilters();
                } else {
                    this.toggleTimeline();
                }
            }, 100);
        } else {
            btn.textContent = '▶ Chạy';
            clearInterval(this.timeline.interval);
        }
    },

    /**
     * Reset view to default
     */
    resetView: function() {
        this.map.setView([25, 100], 4);
    },

    /**
     * Locate user position
     */
    locateMe: function() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.map.setView([position.coords.latitude, position.coords.longitude], 10);
                },
                (error) => {
                    alert('Không thể xác định vị trí: ' + error.message);
                }
            );
        } else {
            alert('Trình duyệt không hỗ trợ định vị');
        }
    },

    /**
     * Show place details
     */
    showPlaceDetails: function(placeId) {
        console.log('Show details for:', placeId);
    },

    /**
     * A4: Show sutra references for a place
     */
    showSutraReferences: function(placeId) {
        const place = this.allPlaces.find(p => p.id === placeId || p.nameChinese === placeId || p.nameVietnamese === placeId);
        if (!place) {
            console.warn('Place not found:', placeId);
            return;
        }
        
        // Dispatch event for SutraSync
        const event = new CustomEvent('marker-click', { detail: place });
        document.dispatchEvent(event);
    },

    /**
     * Hide loading overlay
     */
    hideLoading: function() {
        document.getElementById('loading-overlay').classList.add('hidden');
    },

    /**
     * Search places
     */
    search: function(query) {
        if (!query || query.length < 2) {
            document.getElementById('search-results').classList.remove('active');
            return;
        }

        const results = this.allPlaces.filter(place => {
            const nameVi = place.nameVietnamese || '';
            const nameZh = place.nameChinese || '';
            const nameEn = place.nameEnglish || '';
            
            return nameVi.toLowerCase().includes(query.toLowerCase()) ||
                   nameZh.toLowerCase().includes(query.toLowerCase()) ||
                   nameEn.toLowerCase().includes(query.toLowerCase());
        }).slice(0, 10);

        this.renderSearchResults(results);
    },

    /**
     * Render search results
     */
    renderSearchResults: function(results) {
        const container = document.getElementById('search-results');
        
        if (results.length === 0) {
            container.classList.remove('active');
            return;
        }

        container.innerHTML = results.map(place => `
            <div class="search-result-item" onclick="MapApp.selectPlace('${place.id}')">
                <div class="name-vi">${place.nameVietnamese || place.nameChinese || 'Unknown'}</div>
                ${place.nameChinese ? `<div class="name-zh">${place.nameChinese}</div>` : ''}
            </div>
        `).join('');
        
        container.classList.add('active');
    },

    /**
     * Select place from search
     */
    selectPlace: function(placeId) {
        const place = this.allPlaces.find(p => p.id === placeId);
        if (!place || !place.lat || !place.lon) return;

        this.map.setView([place.lat, place.lon], 10);
        document.getElementById('search-results').classList.remove('active');
        document.getElementById('search-input').value = '';
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    MapApp.init();
});

// Setup search input
document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var searchTimeout;
    
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                MapApp.search(e.target.value);
            }, 300);
        });
    }

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            document.getElementById('search-results').classList.remove('active');
        }
    });

    // Handle URL parameters (AI Dispatcher from Portal)
    const urlParams = new URLSearchParams(window.location.search);
    const lat = urlParams.get('lat');
    const lon = urlParams.get('lon');
    const zoom = urlParams.get('zoom');
    const placeName = urlParams.get('place');
    const layer = urlParams.get('layer');

    if (lat && lon) {
        this.map.setView([parseFloat(lat), parseFloat(lon)], zoom ? parseInt(zoom) : 15);
        console.log(`AI Dispatcher: Centered to ${lat}, ${lon} at zoom ${zoom}`);
    }

    if (layer === 'terrain') {
        MapApp.filters.types = ['religion', 'natural', 'historical'];
        MapApp.applyFilters();
        console.log('Layer terrain mode: filters set to religion, natural, historical (excludes business/shopping)');
    }

    if (placeName) {
        // Find and highlight the place
        const place = this.allPlaces.find(p => 
            (p.nameVietnamese && p.nameVietnamese.toLowerCase().includes(placeName.toLowerCase())) ||
            (p.nameChinese && p.nameChinese.toLowerCase().includes(placeName.toLowerCase()))
        );
        if (place) {
            console.log(`AI Dispatcher: Found place ${place.nameVietnamese}`);
        }
    }
});