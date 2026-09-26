/**
 * DILA API Connector - Multi-source RAG
 * Connect to DILA Web Services for real-time data
 * 
 * @version: v4.15 (2026-04-10)
 * @file: src/js/ai/dila_connector.js
 */

const DILAConnector = (function() {
    'use strict';

    // DILA API endpoints
    const API_BASE = 'https://authority.dila.edu.tw';
    const ENDPOINTS = {
        person: '/authority/Person',
        place: '/authority/Place', 
        time: '/authority/Time',
        search: '/search'
    };

    // Configuration
    const CONFIG = {
        timeout: 3000,
        retry: 3,
        cache: true,
        cacheExpiry: 24 * 60 * 60 * 1000 // 24 hours
    };

    // Cache storage
    const cache = new Map();

    /**
     * Initialize connector
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }
        console.log('[DILAConnector] Initialized with config:', CONFIG);
    }

    /**
     * Lookup person by ID
     * @param {string} personId - DILA Person ID (e.g., "A000001")
     * @returns {Promise<object>}
     */
    async function lookupPerson(personId) {
        const cacheKey = `person:${personId}`;
        
        // Check cache
        if (CONFIG.cache && cache.has(cacheKey)) {
            const cached = cache.get(cacheKey);
            if (Date.now() - cached.timestamp < CONFIG.cacheExpiry) {
                return cached.data;
            }
        }

        // Build URL
        const url = `${API_BASE}${ENDPOINTS.person}/${personId}.json`;

        try {
            const data = await fetchWithRetry(url, CONFIG.retry);
            
            // Cache result
            if (CONFIG.cache && data) {
                cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
            }
            
            return data;
            
        } catch (error) {
            console.error('[DILAConnector] Error fetching person:', error);
            return { error: error.message };
        }
    }

    /**
     * Search for persons
     * @param {string} query - Search query
     * @param {object} params - Search parameters
     * @returns {Promise<object>}
     */
    async function searchPersons(query, params = {}) {
        const url = `${API_BASE}${ENDPOINTS.search}`;
        
        const queryParams = new URLSearchParams({
            q: query,
            ...params
        });

        try {
            const response = await fetch(`${url}?${queryParams}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('[DILAConnector] Search error:', error);
            return { error: error.message, results: [] };
        }
    }

    /**
     * Get place information
     * @param {string} placeId - DILA Place ID
     * @returns {Promise<object>}
     */
    async function lookupPlace(placeId) {
        const cacheKey = `place:${placeId}`;
        
        if (CONFIG.cache && cache.has(cacheKey)) {
            const cached = cache.get(cacheKey);
            if (Date.now() - cached.timestamp < CONFIG.cacheExpiry) {
                return cached.data;
            }
        }

        const url = `${API_BASE}${ENDPOINTS.place}/${placeId}.json`;

        try {
            const data = await fetchWithRetry(url, CONFIG.retry);
            
            if (CONFIG.cache && data) {
                cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
            }
            
            return data;

        } catch (error) {
            console.error('[DILAConnector] Error fetching place:', error);
            return { error: error.message };
        }
    }

    /**
     * Get time/date information
     * @param {string} timeId - DILA Time ID
     * @returns {Promise<object>}
     */
    async function lookupTime(timeId) {
        const cacheKey = `time:${timeId}`;
        
        if (CONFIG.cache && cache.has(cacheKey)) {
            const cached = cache.get(cacheKey);
            if (Date.now() - cached.timestamp < CONFIG.cacheExpiry) {
                return cached.data;
            }
        }

        const url = `${API_BASE}${ENDPOINTS.time}/${timeId}.json`;

        try {
            const data = await fetchWithRetry(url, CONFIG.retry);
            
            if (CONFIG.cache && data) {
                cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
            }
            
            return data;

        } catch (error) {
            console.error('[DILAConnector] Error fetching time:', error);
            return { error: error.message };
        }
    }

    /**
     * Fetch with retry logic
     * @param {string} url - URL to fetch
     * @param {number} maxRetries - Max retry attempts
     * @returns {Promise<object>}
     */
    async function fetchWithRetry(url, maxRetries = 3) {
        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);

                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    },
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return await response.json();

            } catch (error) {
                lastError = error;
                console.warn(`[DILAConnector] Attempt ${attempt} failed:`, error.message);
                
                if (attempt < maxRetries) {
                    await new Promise(r => setTimeout(r, 500 * attempt));
                }
            }
        }

        throw lastError;
    }

    /**
     * Clear cache
     */
    function clearCache() {
        cache.clear();
        console.log('[DILAConnector] Cache cleared');
    }

    /**
     * Get cache stats
     */
    function getCacheStats() {
        return {
            size: cache.size,
            entries: Array.from(cache.keys())
        };
    }

    /**
     * Check if DILA is accessible
     * @returns {Promise<boolean>}
     */
    async function checkConnection() {
        try {
            const response = await fetch(API_BASE, {
                method: 'HEAD',
                mode: 'no-cors'
            });
            return true;
        } catch (error) {
            return false;
        }
    }

    // Public API
    return {
        init: init,
        lookupPerson: lookupPerson,
        lookupPlace: lookupPlace,
        lookupTime: lookupTime,
        searchPersons: searchPersons,
        clearCache: clearCache,
        getCacheStats: getCacheStats,
        checkConnection: checkConnection,
        CONFIG: CONFIG
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DILAConnector;
}
