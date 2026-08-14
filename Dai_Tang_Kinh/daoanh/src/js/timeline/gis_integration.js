/**
 * GIS Timeline Integration - Map + Timeline Connector
 * Connect Leaflet map with Timeline components for synchronized display
 * 
 * @version: v4.19 (2026-04-10)
 * @file: src/js/timeline/gis_integration.js
 */

const GISTimeline = (function() {
    'use strict';

    // Components
    let map = null;
    let timelineSlider = null;
    let timelineManager = null;
    let markersLayer = null;

    // Configuration
    const CONFIG = {
        mapContainer: 'map',
        timelineContainer: 'timeline-container',
        markerColor: '#d97706',
        activeMarkerColor: '#22c55e',
        showLabels: true,
        clusterMarkers: true,
        animationEnabled: true
    };

    /**
     * Initialize GIS Timeline integration
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        // Wait for map to be ready
        if (typeof L !== 'undefined' && document.getElementById(CONFIG.mapContainer)) {
            initializeMap();
        } else {
            // Retry after delay
            setTimeout(initializeMap, 1000);
        }

        // Initialize timeline components
        if (typeof TimelineSlider !== 'undefined') {
            timelineSlider = TimelineSlider;
            timelineSlider.init(CONFIG.timelineContainer, {
                defaultYear: 1000
            });
            timelineSlider.onChange(handleYearChange);
        }

        if (typeof TimelineManager !== 'undefined') {
            timelineManager = TimelineManager;
            timelineManager.init();
        }

        console.log('[GISTimeline] Initialized');
    }

/**
     * Initialize map - only if map is ready
     */
    function initializeMap() {
        // Check if Leaflet is loaded
        if (typeof L === 'undefined') {
            console.warn('[GISTimeline] Leaflet not loaded yet');
            return;
        }
        
        // Check if map container exists
        var container = document.getElementById(CONFIG.mapContainer);
        if (!container) {
            console.warn('[GISTimeline] Map container not found');
            return;
        }

        // Check if map already exists in MapApp
        if (typeof MapApp !== 'undefined' && MapApp.map) {
            map = MapApp.map;
            markersLayer = L.layerGroup().addTo(map);
            console.log('[GISTimeline] Using MapApp.map');
        } else {
            console.log('[GISTimeline] MapApp not ready, skipping');
        }
    }

        // Check if map already exists
        if (typeof window.map !== 'undefined') {
            map = window.map;
            markersLayer = L.layerGroup().addTo(map);
            console.log('[GISTimeline] Using existing map');
        } else {
            // Create new map
            map = L.map(CONFIG.mapContainer).setView([21.0285, 105.8542], 6);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(map);
            
            markersLayer = L.layerGroup().addTo(map);
        }

        // Listen for map ready
        map.whenReady(() => {
            console.log('[GISTimeline] Map ready');
        });
    }

    /**
     * Handle year change from slider
     * @param {number} year 
     */
    function handleYearChange(year) {
        if (!timelineManager) return;

        // Filter entities by year
        const entities = timelineManager.filterByYear(year);

        // Update map markers
        updateMarkers(entities, year);
    }

    /**
     * Update map markers
     * @param {array} entities 
     * @param {number} year 
     */
    function updateMarkers(entities, year) {
        if (!markersLayer) return;

        // Clear existing markers
        markersLayer.clearLayers();

        // Add new markers
        const markers = [];

        for (const entity of entities) {
            if (!entity.gps) continue;

            const [lat, lng] = parseGPS(entity.gps);
            if (lat === null || lng === null) continue;

            // Determine marker color based on entity status
            let color = CONFIG.markerColor;
            
            if (entity.birth === year) {
                color = '#22c55e'; // Green for birth
            } else if (entity.death === year) {
                color = '#ef4444'; // Red for death
            }

            const marker = L.circleMarker([lat, lng], {
                radius: 8,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            });

            // Add popup
            const popupContent = buildPopupContent(entity, year);
            marker.bindPopup(popupContent);

            markers.push(marker);
        }

        // Add markers to layer
        for (const marker of markers) {
            markersLayer.addLayer(marker);
        }

        // Fit bounds if we have markers
        if (markers.length > 0 && map) {
            const group = L.featureGroup(markers);
            map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }

        console.log('[GISTimeline] Updated', markers.length, 'markers for year', year);
    }

    /**
     * Parse GPS string to coordinates
     * @param {string} gps - GPS string like "21.0285,105.8542"
     * @returns {array} [lat, lng] or [null, null]
     */
    function parseGPS(gps) {
        if (!gps) return [null, null];

        // Handle various formats
        const parts = gps.toString().split(/[,\s]+/);
        
        if (parts.length >= 2) {
            const lat = parseFloat(parts[0]);
            const lng = parseFloat(parts[1]);
            
            if (!isNaN(lat) && !isNaN(lng)) {
                return [lat, lng];
            }
        }

        return [null, null];
    }

    /**
     * Build popup content
     * @param {object} entity 
     * @param {number} year 
     * @returns {string}
     */
    function buildPopupContent(entity, year) {
        let status = '';
        
        if (entity.birth === year) {
            status = '<span class="status-birth">Sinh năm này</span>';
        } else if (entity.death === year) {
            status = '<span class="status-death">Mất năm này</span>';
        } else {
            status = '<span class="status-active">Hoạt động</span>';
        }

        return `
            <div class="gis-popup">
                <h4>${entity.name || 'Unknown'}</h4>
                <p class="status">${status}</p>
                <p class="years">
                    ${entity.birth ? 'Sinh: ' + entity.birth : ''}
                    ${entity.death ? ' - Mất: ' + entity.death : ''}
                </p>
                ${entity.lineage ? '<p class="lineage">Dòng: ' + entity.lineage + '</p>' : ''}
            </div>
        `;
    }

    /**
     * Load entities data
     * @param {array} data - Entity data array
     */
    function loadData(data) {
        if (!timelineManager) {
            console.error('[GISTimeline] TimelineManager not initialized');
            return;
        }

        timelineManager.loadEntities(data);
        console.log('[GISTimeline] Loaded', data.length, 'entities');
    }

    /**
     * Add entity to timeline
     * @param {object} entity 
     */
    function addEntity(entity) {
        if (!timelineManager) return;

        const entities = timelineManager.getAllEntities();
        entities.push(entity);
        timelineManager.loadEntities(entities);
    }

    /**
     * Set year programmatically
     * @param {number} year 
     */
    function setYear(year) {
        if (timelineSlider) {
            timelineSlider.setYear(year);
        }
    }

    /**
     * Get current year
     * @returns {number}
     */
    function getCurrentYear() {
        if (timelineSlider) {
            return timelineSlider.getYear();
        }
        return 1000;
    }

    /**
     * Play timeline animation
     */
    function play() {
        if (timelineSlider) {
            timelineSlider.play();
        }
    }

    /**
     * Pause timeline animation
     */
    function pause() {
        if (timelineSlider) {
            timelineSlider.pause();
        }
    }

    /**
     * Get configuration
     */
    function getConfig() {
        return { ...CONFIG };
    }

    // Public API
    return {
        init: init,
        loadData: loadData,
        addEntity: addEntity,
        setYear: setYear,
        getCurrentYear: getCurrentYear,
        play: play,
        pause: pause,
        getConfig: getConfig,
        handleYearChange: handleYearChange
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GISTimeline;
}
