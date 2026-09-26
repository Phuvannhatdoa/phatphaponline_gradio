/**
 * Intent Router - AI Interpreter
 * Phân loại intent và định tuyến đến data source phù hợp
 * 
 * @version: v4.2 (2026-04-10)
 * @file: src/js/ai/intent_router.js
 */

const IntentRouter = (function() {
    'use strict';

    // Router configuration
    const CONFIG = {
        sources: {
            factual: {
                primary: 'DILA_API',
                fallback: 'GraphDB',
                endpoint: '/api/dila/lookup'
            },
            relational: {
                primary: 'GraphDB',
                fallback: 'RAG',
                endpoint: '/api/graphdb/sparql'
            },
            semantic: {
                primary: 'RAG',
                fallback: 'GraphDB',
                endpoint: '/api/rag/query'
            }
        },
        
        // Timeout settings (ms)
        timeouts: {
            DILA_API: 3000,
            GraphDB: 5000,
            RAG: 10000
        },

        // Retry settings
        retries: {
            DILA_API: 3,
            GraphDB: 2,
            RAG: 1
        }
    };

    /**
     * Khởi tạo IntentRouter
     * @param {object} options - Cấu hình tùy chọn
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }
        console.log('[IntentRouter] Initialized with config:', CONFIG);
    }

    /**
     * Route intent đến source phù hợp
     * @param {object} parsedResult - Kết quả từ SemanticParser
     * @returns {Promise<object>} - Kết quả từ data source
     */
    async function route(parsedResult) {
        if (!parsedResult || !parsedResult.intent) {
            return { error: 'Invalid parsed result' };
        }

        const intent = parsedResult.intent;
        const sourceConfig = CONFIG.sources[intent];

        if (!sourceConfig) {
            return { error: `Unknown intent: ${intent}` };
        }

        console.log(`[IntentRouter] Routing ${intent} intent to ${sourceConfig.primary}`);

        try {
            // Try primary source
            const result = await executeQuery(sourceConfig.primary, sourceConfig.endpoint, parsedResult);
            if (result && !result.error) {
                return {
                    intent: intent,
                    source: sourceConfig.primary,
                    data: result,
                    fallback: null
                };
            }
            
            // Fallback nếu primary fail
            if (sourceConfig.fallback) {
                console.log(`[IntentRouter] Primary failed, trying fallback: ${sourceConfig.fallback}`);
                const fallbackResult = await executeQuery(
                    sourceConfig.fallback, 
                    CONFIG.sources[sourceConfig.fallback].endpoint, 
                    parsedResult
                );
                
                return {
                    intent: intent,
                    source: sourceConfig.primary,
                    data: result, // Primary error
                    fallback: {
                        source: sourceConfig.fallback,
                        data: fallbackResult
                    }
                };
            }
            
            return {
                intent: intent,
                source: sourceConfig.primary,
                error: result.error || 'Unknown error',
                data: null
            };
            
        } catch (error) {
            console.error('[IntentRouter] Error:', error);
            return {
                intent: intent,
                error: error.message,
                source: sourceConfig.primary
            };
        }
    }

    /**
     * Thực thi query đến data source
     * @param {string} source - Tên source (DILA_API, GraphDB, RAG)
     * @param {string} endpoint - API endpoint
     * @param {object} params - Parameters
     * @returns {Promise<object>}
     */
    async function executeQuery(source, endpoint, params) {
        const timeout = CONFIG.timeouts[source] || 5000;
        const maxRetries = CONFIG.retries[source] || 1;
        
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const response = await Promise.race([
                    fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(params)
                    }),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout')), timeout)
                    )
                ]);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                return await response.json();
                
            } catch (error) {
                lastError = error;
                console.warn(`[IntentRouter] Attempt ${attempt} failed:`, error.message);
                
                if (attempt < maxRetries) {
                    await new Promise(r => setTimeout(r, 500)); // Wait before retry
                }
            }
        }
        
        return { error: lastError.message };
    }

    /**
     * Route nhiều intent cùng lúc (parallel)
     * @param {array} parsedResults - Mảng kết quả từ SemanticParser
     * @returns {Promise<array>}
     */
    async function routeParallel(parsedResults) {
        const promises = parsedResults.map(pr => route(pr));
        return Promise.all(promises);
    }

    /**
     * Get router configuration
     * @returns {object}
     */
    function getConfig() {
        return { ...CONFIG };
    }

    // Public API
    return {
        init: init,
        route: route,
        routeParallel: routeParallel,
        getConfig: getConfig,
        CONFIG: CONFIG
    };
})();

// Export for Node.js / ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IntentRouter;
}
