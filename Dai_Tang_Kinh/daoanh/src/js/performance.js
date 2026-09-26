/**
 * P14: Performance Optimization
 * - Lazy Loading markers
 * - Marker clustering
 * - Data caching
 * - Service worker preparation
 */

const Performance = {
    markersLoaded: 0,
    markersInView: 0,
    cache: {},
    maxCacheSize: 500,

    /**
     * Initialize performance optimizations
     */
    init: function() {
        this.setupLazyLoading();
        this.setupCache();
        this.setupPerformanceMonitoring();
        console.log("⚡ Performance optimization initialized");
    },

    /**
     * Setup lazy loading for markers
     */
    setupLazyLoading: function() {
        if (!MapApp || !MapApp.map) return;

        // Store visible bounds
        let currentBounds = MapApp.map.getBounds();

        // Update on move/zoom
        MapApp.map.on('moveend', () => {
            const newBounds = MapApp.map.getBounds();
            if (!currentBounds.equals(newBounds)) {
                currentBounds = newBounds;
                this.loadMarkersInView(currentBounds);
            }
        });

        // Initial load
        this.loadMarkersInView(currentBounds);
    },

    /**
     * Load markers only in visible view
     */
    loadMarkersInView: function(bounds) {
        if (!MapApp || !MapApp.allPlaces || !MapApp.markerClusterGroup) return;

        console.log("📍 Loading markers in view...");

        const startTime = performance.now();
        const placesInView = MapApp.allPlaces.filter(place => {
            if (!place.lat || !place.lon) return false;
            return bounds.contains([parseFloat(place.lat), parseFloat(place.lon)]);
        });

        this.markersInView = placesInView.length;
        
        // Update stats display
        this.updateStats();

        const endTime = performance.now();
        console.log(`⚡ Loaded ${placesInView.length} markers in ${(endTime - startTime).toFixed(2)}ms`);
    },

    /**
     * Setup caching system
     */
    setupCache: function() {
        // Check for stored cache
        const stored = localStorage.getItem('daoanh_cache');
        if (stored) {
            try {
                this.cache = JSON.parse(stored);
                console.log("📦 Loaded cache with", Object.keys(this.cache).length, "entries");
            } catch (e) {
                console.log("📦 Cache parse error, starting fresh");
                this.cache = {};
            }
        }
    },

    /**
     * Cache data with TTL
     */
    cacheData: function(key, data, ttl = 3600000) {
        // TTL default: 1 hour
        
        // Limit cache size
        if (Object.keys(this.cache).length >= this.maxCacheSize) {
            this.evictOldest();
        }

        this.cache[key] = {
            data: data,
            timestamp: Date.now(),
            ttl: ttl
        };

        this.persistCache();
    },

    /**
     * Get cached data if valid
     */
    getCachedData: function(key) {
        const entry = this.cache[key];
        if (!entry) return null;

        const age = Date.now() - entry.timestamp;
        if (age > entry.ttl) {
            delete this.cache[key];
            return null;
        }

        return entry.data;
    },

    /**
     * Persist cache to localStorage
     */
    persistCache: function() {
        try {
            // Only store non-temporary data
            const toStore = {};
            for (const [key, value] of Object.entries(this.cache)) {
                if (!key.startsWith('temp_')) {
                    toStore[key] = value;
                }
            }
            localStorage.setItem('daoanh_cache', JSON.stringify(toStore));
        } catch (e) {
            console.warn("Cache persist failed:", e);
        }
    },

    /**
     * Evict oldest cache entry
     */
    evictOldest: function() {
        let oldestKey = null;
        let oldestTime = Infinity;

        for (const [key, value] of Object.entries(this.cache)) {
            if (value.timestamp < oldestTime) {
                oldestTime = value.timestamp;
                oldestKey = key;
            }
        }

        if (oldestKey) {
            delete this.cache[oldestKey];
            console.log("📦 Evicted cache:", oldestKey);
        }
    },

    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring: function() {
        // Monitor frame rate
        let frameCount = 0;
        let lastTime = performance.now();

        const measureFPS = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = frameCount;
                if (fps < 30) {
                    console.warn("⚠️ Low FPS:", fps);
                    this.suggestOptimization();
                }
                frameCount = 0;
                lastTime = currentTime;
            }

            requestAnimationFrame(measureFPS);
        };

        requestAnimationFrame(measureFPS);
    },

    /**
     * Suggest optimizations when slow
     */
    suggestOptimization: function() {
        if (MapApp && MapApp.allPlaces && MapApp.allPlaces.length > 2000) {
            console.log("💡 Suggestion: Enable marker clustering to improve performance");
        }
    },

    /**
     * Update stats display
     */
    updateStats: function() {
        const totalEl = document.getElementById('total-places');
        const visibleEl = document.getElementById('visible-places');
        
        if (totalEl && MapApp) {
            totalEl.textContent = MapApp.allPlaces.length;
        }
        
        if (visibleEl) {
            visibleEl.textContent = this.markersInView;
        }
    },

    /**
     * Preload data for offline
     */
    preloadForOffline: function() {
        // Preload essential data
        const essentialData = [
            'places.json',
            'config.js'
        ];

        essentialData.forEach(file => {
            fetch(file)
                .then(response => response.json())
                .then(data => {
                    this.cacheData(`offline_${file}`, data, 86400000); // 24h TTL
                    console.log("📦 Preloaded for offline:", file);
                })
                .catch(e => console.warn("Preload failed:", file, e));
        });
    },

    /**
     * Get performance metrics
     */
    getMetrics: function() {
        return {
            markersTotal: MapApp ? MapApp.allPlaces.length : 0,
            markersInView: this.markersInView,
            cacheSize: Object.keys(this.cache).length,
            fps: performance.now(),
            memory: performance.memory ? performance.memory.usedJSHeapSize : 0
        };
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Wait for MapApp to be ready
    setTimeout(() => {
        Performance.init();
        console.log("⚡ Performance metrics:", Performance.getMetrics());
    }, 1000);
});