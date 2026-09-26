/**
 * Fusion Engine - Multi-source RAG
 * Merge data from DILA API, GraphDB, and RAG
 * 
 * @version: v4.16 (2026-04-10)
 * @file: src/js/ai/fusion_engine.js
 */

const FusionEngine = (function() {
    'use strict';

    // Priority order: DILA > GraphDB > RAG
    const PRIORITY = ['DILA', 'GraphDB', 'RAG'];

    // Merge configuration
    const CONFIG = {
        priority: PRIORITY,
        dedupe: true,
        conflictResolution: 'highest_priority',  // highest_priority, latest, manual
        timeout: 10000
    };

    /**
     * Initialize fusion engine
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }
        console.log('[FusionEngine] Initialized with priority:', CONFIG.priority);
    }

    /**
     * Fuse data from multiple sources
     * @param {object} sources - Object with keys: DILA, GraphDB, RAG
     * @returns {Promise<object>} - Merged result
     */
    async function fuse(sources) {
        if (!sources || typeof sources !== 'object') {
            return { error: 'Invalid sources object' };
        }

        console.log('[FusionEngine] Fusing data from:', Object.keys(sources));

        const results = {
            DILA: null,
            GraphDB: null,
            RAG: null,
            merged: null,
            source: null,
            timestamp: Date.now()
        };

        // Collect valid results
        for (const sourceName of CONFIG.priority) {
            const sourceData = sources[sourceName];
            
            if (sourceData && !sourceData.error) {
                results[sourceName] = sourceData;
                
                // Use first valid source
                if (!results.merged) {
                    results.merged = sourceData;
                    results.source = sourceName;
                }
            }
        }

        // Deduplicate if enabled
        if (CONFIG.dedupe && results.merged) {
            results.merged = deduplicate(results.merged, sources);
        }

        // Add metadata
        results.sources = Object.keys(sources).filter(k => sources[k] && !sources[k].error);
        results.priority = CONFIG.priority;

        console.log('[FusionEngine] Fusion complete. Primary source:', results.source);

        return results;
    }

    /**
     * Deduplicate merged data
     * @param {object} merged - Merged data
     * @param {object} sources - Original sources
     * @returns {object} - Deduplicated data
     */
    function deduplicate(merged, sources) {
        const seen = new Set();
        const uniqueItems = [];

        const items = merged.results?.bindings || merged.items || merged.data || [];

        for (const item of items) {
            // Create unique key from item
            const key = JSON.stringify(item);
            
            if (!seen.has(key)) {
                seen.add(key);
                uniqueItems.push(item);
            }
        }

        // Return with unique items
        return {
            ...merged,
            results: { bindings: uniqueItems },
            itemCount: uniqueItems.length,
            deduplicated: true
        };
    }

    /**
     * Resolve conflicts between sources
     * @param {object} sources - Data from multiple sources
     * @returns {object} - Resolved data
     */
    function resolveConflicts(sources) {
        const resolved = {};
        
        // Track field conflicts
        const fieldConflicts = {};

        // Check each priority source
        for (const sourceName of CONFIG.priority) {
            const sourceData = sources[sourceName];
            
            if (!sourceData || sourceData.error) continue;

            // For each field in data
            for (const [field, value] of Object.entries(sourceData)) {
                if (field in resolved) {
                    // Conflict detected
                    if (!fieldConflicts[field]) {
                        fieldConflicts[field] = [];
                    }
                    fieldConflicts[field].push({
                        source: sourceName,
                        value: resolved[field]
                    });
                    
                    // Use priority to resolve
                    if (CONFIG.conflictResolution === 'highest_priority') {
                        resolved[field] = value;
                    }
                } else {
                    resolved[field] = value;
                }
            }
        }

        resolved._conflicts = fieldConflicts;
        resolved._resolvedBy = CONFIG.conflictResolution;

        return resolved;
    }

    /**
     * Get data from specific source with fallback
     * @param {string} primarySource - Primary source name
     * @param {object} sources - All sources
     * @returns {Promise<object>}
     */
    async function getWithFallback(primarySource, sources) {
        const primary = sources[primarySource];
        
        // Return primary if available and valid
        if (primary && !primary.error) {
            return {
                data: primary,
                source: primarySource
            };
        }

        // Try fallbacks in priority order
        for (const sourceName of CONFIG.priority) {
            if (sourceName === primarySource) continue;
            
            const fallback = sources[sourceName];
            if (fallback && !fallback.error) {
                console.log(`[FusionEngine] Falling back to ${sourceName}`);
                return {
                    data: fallback,
                    source: sourceName,
                    fallback: true
                };
            }
        }

        // All sources failed
        return {
            error: 'All sources failed',
            data: null,
            source: null
        };
    }

    /**
     * Compare sources
     * @param {object} sources - Data from multiple sources
     * @returns {object} - Comparison report
     */
    function compare(sources) {
        const report = {
            sources: {},
            agreement: [],
            conflicts: []
        };

        for (const sourceName of CONFIG.priority) {
            const sourceData = sources[sourceName];
            
            if (sourceData && !sourceData.error) {
                report.sources[sourceName] = {
                    itemCount: sourceData.results?.bindings?.length || 
                               sourceData.items?.length || 0,
                    hasData: true
                };
            } else {
                report.sources[sourceName] = {
                    hasData: false,
                    error: sourceData?.error
                };
            }
        }

        return report;
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
        fuse: fuse,
        resolveConflicts: resolveConflicts,
        getWithFallback: getWithFallback,
        compare: compare,
        getConfig: getConfig
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FusionEngine;
}
