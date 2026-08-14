/**
 * P11: Pathfinding - Nối điểm dựa trên quan hệ Thầy-Trò
 * Query GraphDB (buddhist repo) để lấy teacher-student relationships
 * Vẽ đường đi trên map
 */

const Pathfinding = {
    graphdbUrl: "http://158.220.106.183:7200/repositories/buddhist",
    auth: null,
    pathsLayer: null,
    pathData: [],

    /**
     * Initialize pathfinding
     */
    init: function() {
        this.pathsLayer = L.layerGroup().addTo(MapApp.map);
        console.log("🛤️ Pathfinding initialized");
    },

    /**
     * Set authentication
     */
    setAuth: function(username, password) {
        this.auth = btoa(`${username}:${password}`);
    },

    /**
     * Query GraphDB for lineage relationships
     */
    queryLineage: async function(limit = 100) {
        const sparql = `
            PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?student ?studentName ?teacher ?teacherName ?studentPlace ?teacherPlace
            WHERE {
                ?student a bkg:Monk .
                ?student rdfs:label ?studentName .
                ?student bkg:hasTeacher ?teacher .
                ?teacher rdfs:label ?teacherName .
                OPTIONAL { ?student bkg:place ?studentPlace }
                OPTIONAL { ?teacher bkg:place ?teacherPlace }
            }
            LIMIT ${limit}
        `;

        try {
            const response = await fetch(this.graphdbUrl + "/sparql?query=" + encodeURIComponent(sparql), {
                headers: {
                    "Authorization": "Basic " + this.auth,
                    "Accept": "application/sparql-results+json"
                }
            });
            const data = await response.json();
            return data.results.bindings;
        } catch (e) {
            console.error("❌ GraphDB query error:", e);
            return [];
        }
    },

    /**
     * Get place coordinates for a monk
     */
    getMonkPlace: function(monkUri) {
        var sparql = "PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> SELECT ?place ?lat ?lon WHERE {"
            PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
            SELECT ?place ?lat ?lon
            WHERE {
                <${monkUri}> bkg:place ?place .
                ?place geo:lat ?lat .
                ?place geo:long ?lon .
            }
        `;

        try {
            const response = await fetch(this.graphdbUrl + "/sparql?query=" + encodeURIComponent(sparql), {
                headers: {
                    "Authorization": "Basic " + this.auth,
                    "Accept": "application/sparql-results+json"
                }
            });
            const data = await response.json();
            const bindings = data.results.bindings;
            if (bindings.length > 0) {
                return {
                    lat: parseFloat(bindings[0].lat.value),
                    lon: parseFloat(bindings[0].lon.value),
                    name: bindings[0].place.value
                };
            }
        } catch (e) {
            console.error("Place query error:", e);
        }
        return null;
    },

    /**
     * Draw path between two places
     */
    drawPath: function(lat1, lon1, lat2, lon2, label) {
        if (!lat1 || !lon1 || !lat2 || !lon2) return;

        const polyline = L.polyline([
            [lat1, lon1],
            [lat2, lon2]
        ], {
            color: '#d97706',
            weight: 2,
            opacity: 0.7,
            dashArray: '5, 10',
            lineCap: 'round'
        }).bindPopup(`
            <div class="text-sm">
                <strong>🔗 ${label}</strong>
            </div>
        `);

        this.pathsLayer.addLayer(polyline);
    },

    /**
     * Clear all paths
     */
    clearPaths: function() {
        this.pathsLayer.clearLayers();
        this.pathData = [];
    },

    /**
     * Load and draw lineage paths
     */
    loadLineagePaths: async function() {
        console.log("🛤️ Loading lineage paths...");
        
        // Get lineage data from GraphDB
        const lineages = await this.queryLineage(50);
        
        if (lineages.length === 0) {
            console.log("⚠️ No lineage data found");
            return;
        }

        // For demo, we'll use sample coordinates
        // In production, would query place coordinates
        const samplePaths = [
            { from: [21.0285, 105.8342], to: [21.0285, 105.8342], label: "Mã Tổ Đạo Nhất → Đạt Ma" },
            { from: [34.3, 108.9], to: [34.2, 108.95], label: "Lục Tổ → Mã Tổ" },
            { from: [25.1, 83.0], to: [34.3, 108.9], label: "Bồ Đề Đạt Ma → Lục Tổ" }
        ];

        samplePaths.forEach(path => {
            this.drawPath(
                path.from[0], path.from[1],
                path.to[0], path.to[1],
                path.label
            );
        });

        console.log(`✅ Drew ${samplePaths.length} lineage paths`);
    },

    /**
     * Toggle path visibility
     */
    togglePaths: function(visible) {
        if (visible) {
            if (!MapApp.map.hasLayer(this.pathsLayer)) {
                this.pathsLayer.addTo(MapApp.map);
            }
        } else {
            MapApp.map.removeLayer(this.pathsLayer);
        }
    }
};

// Initialize on MapApp ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof MapApp !== 'undefined') {
        Pathfinding.init();
    }
});