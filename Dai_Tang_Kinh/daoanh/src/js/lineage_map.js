/**
 * Lineage Map - Genealogy + Geography Integration
 * 
 * This module combines:
 * - Phả hệ (Genealogy): Teacher-Student relationships from DILA Person Authority
 * - Địa lý (Geography): GPS coordinates from places.json/GraphDB
 * 
 * Features:
 * - View lineage tree with map markers
 * - Draw paths between related places
 * - Filter by dynasty/period
 * 
 * Usage:
 *   <script src="src/js/lineage_map.js"></script>
 *   LineageMapApp.init('map-container', 'lineage-container');
 */

const LineageMapApp = (function() {
    'use strict';
    
    // State
    let map = null;
    let lineageData = null;
    let markers = [];
    let paths = [];
    let currentMonk = null;
    
    // Configuration
    const CONFIG = {
        apiBase: '/api',
        mapContainer: 'map',
        lineageContainer: 'lineage-panel',
        defaultCenter: [21.0, 105.8],  // Vietnam
        defaultZoom: 5,
        pathColor: '#d97706',  // Amber gold
        pathWeight: 3,
        markerIcon: '📍'
    };
    
    /**
     * Initialize the Lineage Map application
     */
    function init(mapContainer, lineageContainer) {
        CONFIG.mapContainer = mapContainer || CONFIG.mapContainer;
        CONFIG.lineageContainer = lineageContainer || CONFIG.lineageContainer;
        
        // Check if Leaflet is available
        if (typeof L === 'undefined') {
            console.error('Leaflet not loaded. Please include Leaflet.js first.');
            return;
        }
        
        // Initialize map
        initMap();
        
        console.log('✅ LineageMapApp initialized');
    }
    
    /**
     * Initialize Leaflet map
     */
    function initMap() {
        const container = document.getElementById(CONFIG.mapContainer);
        if (!container) {
            console.warn('Map container not found');
            return;
        }
        
        map = L.map(CONFIG.mapContainer).setView(CONFIG.defaultCenter, CONFIG.defaultZoom);
        
        // Add tile layer (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);
    }
    
    /**
     * Load lineage data for a monk
     */
    async function loadLineage(monkName) {
        if (!monkName) {
            console.error('Monk name required');
            return;
        }
        
        try {
            const encodedName = encodeURIComponent(monkName);
            const response = await fetch(`${CONFIG.apiBase}/lineage-map/${encodedName}`);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            lineageData = await response.json();
            currentMonk = monkName;
            
            // Render lineage and map
            renderLineageTree(lineageData.lineage);
            renderMapMarkers(lineageData.places);
            
            // If we have GPS paths, draw them
            if (lineageData.paths && lineageData.paths.length > 0) {
                renderPaths(lineageData.paths);
            }
            
            console.log('✅ Loaded lineage for:', monkName);
            
            return lineageData;
            
        } catch (error) {
            console.error('Failed to load lineage:', error);
            return null;
        }
    }
    
    /**
     * Render lineage tree in the side panel
     */
    function renderLineageTree(lineage) {
        const container = document.getElementById(CONFIG.lineageContainer);
        if (!container) {
            console.warn('Lineage container not found');
            return;
        }
        
        if (!lineage) {
            container.innerHTML = '<p class="text-gray-500">No lineage data</p>';
            return;
        }
        
        let html = `
            <div class="lineage-tree p-4 bg-slate-900 text-white rounded-lg">
                <h3 class="text-lg font-bold text-amber-500 mb-4">📜 Phả hệ (Genealogy)</h3>
                
                <div class="lineage-item mb-4">
                    <div class="text-sm text-gray-400">Sư</div>
                    <div class="text-xl font-bold text-white">${lineage.name || 'Unknown'}</div>
                    <div class="text-sm text-gray-400">${lineage.dynasty || ''}</div>
                    <div class="text-xs text-gray-500">ID: ${lineage.monk}</div>
                </div>
        `;
        
        // Grand Teacher
        if (lineage.grand_teacher) {
            html += `
                <div class="lineage-item mb-2 ml-4">
                    <div class="text-sm text-gray-400">▲ Sư đời trước</div>
                    <div class="text-lg font-semibold text-amber-400">${lineage.grand_teacher.name}</div>
                    <div class="text-xs text-gray-500">${lineage.grand_teacher.dynasty}</div>
                </div>
            `;
        }
        
        // Teacher
        if (lineage.teacher) {
            html += `
                <div class="lineage-item mb-2 ml-4">
                    <div class="text-sm text-gray-400">▲ Thầy</div>
                    <div class="text-lg font-semibold text-amber-400">${lineage.teacher.name}</div>
                    <div class="text-xs text-gray-500">${lineage.teacher.dynasty}</div>
                </div>
            `;
        }
        
        // Current monk (repeated)
        html += `
            <div class="lineage-item mb-4 ml-2 border-l-2 border-amber-500 pl-2">
                <div class="text-sm text-amber-500">● Hiện tại</div>
                <div class="text-xl font-bold text-white">${lineage.name || 'Unknown'}</div>
            </div>
        `;
        
        // Students
        if (lineage.students && lineage.students.length > 0) {
            html += `<div class="text-sm text-gray-400 mb-2">▼ Đệ tử (${lineage.students.length})</div>`;
            
            lineage.students.forEach(student => {
                html += `
                    <div class="lineage-item mb-2 ml-4 cursor-pointer hover:text-amber-400" 
                         onclick="LineageMapApp.loadLineage('${student.name}')">
                        <div class="text-base">${student.name}</div>
                        <div class="text-xs text-gray-500">${student.dynasty}</div>
                    </div>
                `;
            });
        }
        
        // Grand students
        if (lineage.grand_students && lineage.grand_students.length > 0) {
            html += `<div class="text-sm text-gray-400 mb-2 mt-4">▼▼ Đệ tử thế hệ sau (${lineage.grand_students.length})</div>`;
            
            lineage.grand_students.forEach(student => {
                html += `
                    <div class="lineage-item mb-2 ml-6 cursor-pointer hover:text-amber-400 text-sm"
                         onclick="LineageMapApp.loadLineage('${student.name}')">
                        <div class="text-gray-400">${student.name}</div>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        
        container.innerHTML = html;
    }
    
    /**
     * Render map markers for places
     */
    function renderMapMarkers(places) {
        if (!map || !places) return;
        
        // Clear existing markers
        clearMarkers();
        
        // Add new markers
        places.forEach(place => {
            if (place.lat && place.lon) {
                const marker = L.marker([place.lat, place.lon], {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: `<div class="text-2xl">${CONFIG.markerIcon}</div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    })
                });
                
                marker.bindPopup(`
                    <div class="text-center">
                        <div class="font-bold">${place.monk}</div>
                        <div class="text-sm">${place.place}</div>
                        <div class="text-xs text-gray-500">${place.type}</div>
                    </div>
                `);
                
                marker.addTo(map);
                markers.push(marker);
            }
        });
        
        // Fit bounds if we have markers
        if (markers.length > 0) {
            const group = L.featureGroup(markers);
            map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }
    }
    
    /**
     * Draw paths between places
     */
    function renderPaths(pathsData) {
        if (!map || !pathsData || pathsData.length === 0) return;
        
        // Clear existing paths
        clearPaths();
        
        pathsData.forEach(path => {
            if (path.from && path.to) {
                const polyline = L.polyline([path.from, path.to], {
                    color: CONFIG.pathColor,
                    weight: CONFIG.pathWeight,
                    opacity: 0.7,
                    dashArray: '5, 10'
                });
                
                polyline.bindPopup(path.label || 'Phả hệ path');
                polyline.addTo(map);
                paths.push(polyline);
            }
        });
    }
    
    /**
     * Clear all markers
     */
    function clearMarkers() {
        markers.forEach(m => map.removeLayer(m));
        markers = [];
    }
    
    /**
     * Clear all paths
     */
    function clearPaths() {
        paths.forEach(p => map.removeLayer(p));
        paths = [];
    }
    
    /**
     * Search for a monk by name
     */
    async function searchMonk(query) {
        if (!query || query.length < 2) return [];
        
        try {
            const response = await fetch(`${CONFIG.apiBase}/persons/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            return data.persons || [];
        } catch (error) {
            console.error('Search failed:', error);
            return [];
        }
    }
    
    /**
     * Get person details
     */
    async function getPerson(personId) {
        try {
            const response = await fetch(`${CONFIG.apiBase}/persons/${personId}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to get person:', error);
            return null;
        }
    }
    
    /**
     * Get statistics
     */
    async function getStats() {
        try {
            const response = await fetch(`${CONFIG.apiBase}/persons/stats`);
            return await response.json();
        } catch (error) {
            console.error('Failed to get stats:', error);
            return null;
        }
    }
    
    // Public API
    return {
        init,
        loadLineage,
        renderLineageTree,
        renderMapMarkers,
        renderPaths,
        searchMonk,
        getPerson,
        getStats,
        clearMarkers,
        clearPaths
    };
})();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LineageMapApp;
}