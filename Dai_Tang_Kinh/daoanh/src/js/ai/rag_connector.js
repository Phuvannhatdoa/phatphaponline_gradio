/**
 * RAG Engine Connector - Semantic Search
 * Connect to RAG backend for semantic search
 * 
 * @version: v4.20 (2026-04-10)
 * @file: src/js/ai/rag_connector.js
 */

const RAGConnector = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        endpoint: '/api/rag/query',
        timeout: 10000,
        maxResults: 10,
        similarityThreshold: 0.5,
        cacheResults: true,
        cacheExpiry: 3600000 // 1 hour
    };

    // Cache
    const cache = new Map();

    /**
     * Initialize RAG connector
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }
        console.log('[RAGConnector] Initialized with config:', CONFIG);
    }

    /**
     * Query the RAG system
     * @param {string} query - Query string
     * @param {object} params - Query parameters
     * @returns {Promise<object>}
     */
    async function query(query, params = {}) {
        if (!query) {
            return { error: 'Empty query' };
        }

        const cacheKey = `query:${query}:${JSON.stringify(params)}`;
        
        // Check cache
        if (CONFIG.cacheResults && cache.has(cacheKey)) {
            const cached = cache.get(cacheKey);
            if (Date.now() - cached.timestamp < CONFIG.cacheExpiry) {
                console.log('[RAGConnector] Cache hit for:', query);
                return cached.data;
            }
        }

        try {
            const response = await Promise.race([
                fetch(CONFIG.endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        query: query,
                        max_results: params.maxResults || CONFIG.maxResults,
                        similarity_threshold: params.similarityThreshold || CONFIG.similarityThreshold,
                        ...params
                    })
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout')), CONFIG.timeout)
                )
            ]);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Cache result
            if (CONFIG.cacheResults && data) {
                cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
            }

            return data;

        } catch (error) {
            console.error('[RAGConnector] Query error:', error);
            return { error: error.message, results: [] };
        }
    }

    /**
     * Search with context
     * @param {string} query - Query string
     * @param {string} context - Context for RAG (e.g., "lineage", "biography")
     * @returns {Promise<object>}
     */
    async function searchWithContext(query, context) {
        return query(query, { context: context });
    }

    /**
     * Search by entity
     * @param {string} entityId - Entity ID
     * @param {string} entityType - Entity type (person, place, etc.)
     * @returns {Promise<object>}
     */
    async function searchByEntity(entityId, entityType = 'person') {
        return query(`Info about ${entityType} ${entityId}`, {
            filters: { entity_type: entityType, entity_id: entityId }
        });
    }

    /**
     * Search in specific documents
     * @param {string} query - Query string
     * @param {array} docIds - Document IDs to search in
     * @returns {Promise<object>}
     */
    async function searchInDocuments(query, docIds) {
        return query(query, { filters: { doc_ids: docIds } });
    }

    /**
     * Get suggestions based on partial query
     * @param {string} partial - Partial query
     * @returns {Promise<array>}
     */
    async function getSuggestions(partial) {
        const result = await query(partial, { maxResults: 5 });
        
        if (result.error || !result.suggestions) {
            return [];
        }
        
        return result.suggestions;
    }

    /**
     * Get cached results
     * @returns {object}
     */
    function getCacheStats() {
        const stats = {
            size: cache.size,
            entries: []
        };

        for (const [key, value] of cache.entries()) {
            stats.entries.push({
                query: key.substring(0, 50),
                age: Date.now() - value.timestamp
            });
        }

        return stats;
    }

    /**
     * Clear cache
     */
    function clearCache() {
        cache.clear();
        console.log('[RAGConnector] Cache cleared');
    }

    /**
     * Check RAG service availability
     * @returns {Promise<boolean>}
     */
    async function checkHealth() {
        try {
            const response = await fetch('/daoanh/api/rag/health', {
                method: 'GET',
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // Public API
    return {
        init: init,
        query: query,
        searchWithContext: searchWithContext,
        searchByEntity: searchByEntity,
        searchInDocuments: searchInDocuments,
        getSuggestions: getSuggestions,
        getCacheStats: getCacheStats,
        clearCache: clearCache,
        checkHealth: checkHealth,
        CONFIG: CONFIG
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RAGConnector;
}
