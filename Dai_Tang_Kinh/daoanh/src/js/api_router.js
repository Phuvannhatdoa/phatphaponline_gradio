/**
 * API Router - Central API Router
 * Connect all components: AI, RAG, GraphDB, DILA, Timeline
 * 
 * @version: v4.21 (2026-04-10)
 * @file: src/js/api_router.js
 */

const APIRouter = (function() {
    'use strict';

    // Components
    let orchestrator = null;
    let ragConnector = null;
    let dilaConnector = null;
    let fusionEngine = null;
    let gistimeline = null;

    // Configuration
    const CONFIG = {
        defaultSource: 'orchestrator',
        timeout: 30000,
        debug: true
    };

    /**
     * Initialize API Router
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        // Initialize components
        if (typeof AgentOrchestrator !== 'undefined') {
            orchestrator = AgentOrchestrator;
        }

        if (typeof RAGConnector !== 'undefined') {
            ragConnector = RAGConnector;
            ragConnector.init();
        }

        if (typeof DILAConnector !== 'undefined') {
            dilaConnector = DILAConnector;
        }

        if (typeof FusionEngine !== 'undefined') {
            fusionEngine = FusionEngine;
            fusionEngine.init();
        }

        if (typeof GISTimeline !== 'undefined') {
            gistimeline = GISTimeline;
            gistimeline.init();
        }

        log('[APIRouter] All components initialized');
    }

    /**
     * Handle incoming API request
     * @param {object} request - API request object
     * @returns {Promise<object>}
     */
    async function handleRequest(request) {
        const startTime = Date.now();
        
        try {
            const { type, action, data } = request;

            log('[APIRouter] Request:', type, action);

            switch (type) {
                case 'query':
                    return await handleQuery(action, data);
                
                case 'entity':
                    return await handleEntity(action, data);
                
                case 'timeline':
                    return await handleTimeline(action, data);
                
                case 'search':
                    return await handleSearch(action, data);
                
                case 'system':
                    return await handleSystem(action, data);
                
                default:
                    return { error: 'Unknown request type: ' + type };
            }

        } catch (error) {
            log('[APIRouter] Error:', error);
            return { error: error.message };
        } finally {
            log('[APIRouter] Request handled in', Date.now() - startTime, 'ms');
        }
    }

    /**
     * Handle query requests (AI → SPARQL)
     */
    async function handleQuery(action, data) {
        if (action === 'natural_language') {
            // Use orchestrator for NL queries
            if (orchestrator) {
                return await orchestrator.processQuery(data.query);
            }
            return { error: 'Orchestrator not initialized' };
        }

        if (action === 'sparql') {
            // Direct SPARQL query
            return await executeSPARQL(data.query);
        }

        return { error: 'Unknown query action' };
    }

    /**
     * Handle entity requests (DILA, GraphDB)
     */
    async function handleEntity(action, data) {
        const { entityId, entityType } = data;

        if (action === 'lookup') {
            // Multi-source lookup with fusion
            return await multiSourceLookup(entityId, entityType);
        }

        if (action === 'details') {
            return await getEntityDetails(entityId, entityType);
        }

        if (action === 'lineage') {
            return await getEntityLineage(entityId);
        }

        return { error: 'Unknown entity action' };
    }

    /**
     * Handle timeline requests
     */
    async function handleTimeline(action, data) {
        if (action === 'set_year') {
            if (gistimeline) {
                gistimeline.setYear(data.year);
                return { success: true, year: data.year };
            }
            return { error: 'GISTimeline not initialized' };
        }

        if (action === 'get_year') {
            if (gistimeline) {
                return { year: gistimeline.getCurrentYear() };
            }
            return { year: 1000 };
        }

        if (action === 'load_data') {
            if (gistimeline) {
                gistimeline.loadData(data.entities);
                return { success: true, count: data.entities.length };
            }
            return { error: 'GISTimeline not initialized' };
        }

        return { error: 'Unknown timeline action' };
    }

    /**
     * Handle search requests
     */
    async function handleSearch(action, data) {
        if (action === 'semantic') {
            // RAG semantic search
            if (ragConnector) {
                return await ragConnector.query(data.query, data.params);
            }
            return { error: 'RAG not initialized' };
        }

        if (action === 'entity') {
            // Entity search (GraphDB)
            return await searchEntities(data.query);
        }

        if (action === 'dila') {
            // DILA search
            if (dilaConnector) {
                return await dilaConnector.searchPersons(data.query);
            }
            return { error: 'DILA not initialized' };
        }

        return { error: 'Unknown search action' };
    }

    /**
     * Handle system requests
     */
    async function handleSystem(action, data) {
        if (action === 'status') {
            return getSystemStatus();
        }

        if (action === 'health') {
            return await checkHealth();
        }

        return { error: 'Unknown system action' };
    }

    /**
     * Multi-source entity lookup with fusion
     */
    async function multiSourceLookup(entityId, entityType) {
        const sources = {};

        // Try DILA first
        if (dilaConnector) {
            try {
                if (entityType === 'person') {
                    sources.DILA = await dilaConnector.lookupPerson(entityId);
                } else if (entityType === 'place') {
                    sources.DILA = await dilaConnector.lookupPlace(entityId);
                }
            } catch (e) {
                log('[APIRouter] DILA lookup failed:', e);
            }
        }

        // Try GraphDB
        try {
            sources.GraphDB = await getEntityDetails(entityId, entityType);
        } catch (e) {
            log('[APIRouter] GraphDB lookup failed:', e);
        }

        // Try RAG
        if (ragConnector) {
            try {
                sources.RAG = await ragConnector.searchByEntity(entityId, entityType);
            } catch (e) {
                log('[APIRouter] RAG lookup failed:', e);
            }
        }

        // Fuse results
        if (fusionEngine) {
            return await fusionEngine.fuse(sources);
        }

        // Return first available
        return sources.DILA || sources.GraphDB || sources.RAG || { error: 'No data found' };
    }

    /**
     * Get entity details from GraphDB
     */
    async function getEntityDetails(entityId, entityType) {
        const query = `
            SELECT ?prop ?value
            WHERE {
                <http://phatphaponline.org/entity/${entityId}> ?prop ?value .
            }
            LIMIT 50
        `;
        return await executeSPARQL(query);
    }

    /**
     * Get entity lineage
     */
    async function getEntityLineage(entityId) {
        const query = `
            SELECT ?teacher ?student
            WHERE {
                ?student :teacher ?teacher .
                FILTER(?student = <http://phatphaponline.org/entity/${entityId}>)
            }
        `;
        return await executeSPARQL(query);
    }

    /**
     * Execute SPARQL query
     */
    async function executeSPARQL(query) {
        try {
            const response = await fetch('/daoanh/api/graphdb/sparql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            return await response.json();
        } catch (error) {
            return { error: error.message };
        }
    }

    /**
     * Search entities
     */
    async function searchEntities(searchQuery) {
        const query = `
            SELECT ?entity ?label
            WHERE {
                ?entity rdfs:label ?label .
                FILTER(CONTAINS(LCASE(?label), LCASE("${searchQuery}")))
            }
            LIMIT 20
        `;
        return await executeSPARQL(query);
    }

    /**
     * Get system status
     */
    function getSystemStatus() {
        return {
            components: {
                orchestrator: orchestrator !== null,
                ragConnector: ragConnector !== null,
                dilaConnector: dilaConnector !== null,
                fusionEngine: fusionEngine !== null,
                gistimeline: gistimeline !== null
            },
            config: CONFIG,
            uptime: Date.now()
        };
    }

    /**
     * Check system health
     */
    async function checkHealth() {
        const health = {
            status: 'ok',
            components: {}
        };

        // Check RAG
        if (ragConnector) {
            health.components.rag = await ragConnector.checkHealth();
        }

        // Check DILA
        if (dilaConnector) {
            health.components.dila = await dilaConnector.checkConnection();
        }

        health.status = Object.values(health.components).every(v => v) ? 'ok' : 'degraded';

        return health;
    }

    /**
     * Log helper
     */
    function log(...args) {
        if (CONFIG.debug) {
            console.log('[APIRouter]', ...args);
        }
    }

    // Public API
    return {
        init: init,
        handleRequest: handleRequest,
        getSystemStatus: getSystemStatus,
        checkHealth: checkHealth
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIRouter;
}
