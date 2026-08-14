/**
 * Agent Orchestrator - 9-Agent System
 * Central controller for all AI agents
 * 
 * @version: v4.12 (2026-04-10)
 * @file: src/js/ai/orchestrator.js
 */

const AgentOrchestrator = (function() {
    'use strict';

    // Agent registry
    const AGENTS = {
        semanticParser: null,
        intentRouter: null,
        sparqlGenerator: null,
        responseFormatter: null,
        graphDB: null,
        ragEngine: null,
        fusionEngine: null,
        visualization: null,
        storage: null
    };

    // Configuration
    const CONFIG = {
        timeout: 30000,
        retry: 2,
        parallel: true,
        debug: true
    };

    // Agent definitions
    const AGENT_DEFINITIONS = {
        Orchestrator: {
            role: 'central_controller',
            input: ['parsed_query', 'detected_entities'],
            output: ['execution_plan', 'routing_decisions'],
            logic: ['detect_intent', 'parallel_execution']
        },
        SemanticParser: {
            module: 'SemanticParser',
            file: 'ai/semantic_parser.js',
            input: 'natural_language_query',
            output: ['entities', 'intent', 'sparql_template']
        },
        IntentRouter: {
            module: 'IntentRouter', 
            file: 'ai/intent_router.js',
            input: 'parsed_result',
            output: 'routed_result'
        },
        SPARQLGenerator: {
            module: 'SPARQLGenerator',
            file: 'ai/sparql_generator.js',
            input: 'parsed_result',
            output: 'sparql_query'
        },
        ResponseFormatter: {
            module: 'ResponseFormatter',
            file: 'ai/response_formatter.js',
            input: 'sparql_result',
            output: ['text', 'html', 'data']
        },
        GraphDBAgent: {
            file: 'graphdb.js',
            endpoint: '/api/graphdb/sparql',
            input: 'sparql_query',
            output: 'triples'
        },
        RAGEngine: {
            endpoint: '/api/rag/query',
            input: 'query',
            output: 'enriched_answer'
        },
        FusionEngine: {
            input: ['api_data', 'graph_data', 'rag_data'],
            output: 'unified_response',
            priority: ['DILA', 'GraphDB', 'RAG']
        },
        VisualizationEngine: {
            file: 'map.js',
            input: ['entity', 'location', 'time'],
            output: ['gis_layers', 'timeline_data']
        },
        StorageOptimizer: {
            file: 'search/trie_index.js',
            input: 'search_query',
            output: 'index_results'
        }
    };

    /**
     * Initialize all agents
     */
    async function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        log('[Orchestrator] Initializing 9-Agent System...');

        // Load agent modules (if not already loaded)
        await loadAgents();

        // Initialize each agent
        if (AGENTS.intentRouter && AGENTS.intentRouter.init) {
            AGENTS.intentRouter.init(CONFIG);
        }

        log('[Orchestrator] ✓ System initialized');
        
        return {
            agents: Object.keys(AGENTS),
            config: CONFIG
        };
    }

    /**
     * Load agent modules
     */
    async function loadAgents() {
        // Semantic Parser (already loaded as global)
        if (typeof SemanticParser !== 'undefined') {
            AGENTS.semanticParser = SemanticParser;
        }

        // Intent Router
        if (typeof IntentRouter !== 'undefined') {
            AGENTS.intentRouter = IntentRouter;
        }

        // SPARQL Generator
        if (typeof SPARQLGenerator !== 'undefined') {
            AGENTS.sparqlGenerator = SPARQLGenerator;
        }

        // Response Formatter
        if (typeof ResponseFormatter !== 'undefined') {
            AGENTS.responseFormatter = ResponseFormatter;
        }

        log('[Orchestrator] Loaded', Object.keys(AGENTS).filter(k => AGENTS[k]).length, 'agents');
    }

    /**
     * Process a user query through the agent pipeline
     * @param {string} query - Natural language query
     * @returns {Promise<object>} - Final response
     */
    async function processQuery(query) {
        if (!query) {
            return { error: 'Empty query' };
        }

        log('[Orchestrator] Processing query:', query);

        const startTime = Date.now();
        const pipeline = {
            query: query,
            stages: [],
            result: null
        };

        try {
            // Stage 1: Parse (Semantic Parser)
            const parseResult = AGENTS.semanticParser 
                ? AGENTS.semanticParser.parse(query)
                : { error: 'SemanticParser not loaded' };
            
            pipeline.stages.push({
                name: 'SemanticParser',
                result: parseResult,
                time: Date.now() - startTime
            });

            if (parseResult.error) {
                throw new Error(parseResult.error);
            }

            // Stage 2: Route (Intent Router)
            let routedResult;
            if (AGENTS.intentRouter) {
                routedResult = await AGENTS.intentRouter.route(parseResult);
            } else {
                routedResult = await routeFallback(parseResult);
            }

            pipeline.stages.push({
                name: 'IntentRouter',
                result: routedResult,
                time: Date.now() - startTime
            });

            // Stage 3: Generate SPARQL
            let sparqlQuery;
            if (AGENTS.sparqlGenerator) {
                sparqlQuery = AGENTS.sparqlGenerator.generate(parseResult);
            } else {
                sparqlQuery = { query: generateSimpleSPARQL(parseResult) };
            }

            pipeline.stages.push({
                name: 'SPARQLGenerator',
                result: sparqlQuery,
                time: Date.now() - startTime
            });

            // Stage 4: Execute query (via fetch)
            let queryResult;
            if (routedResult.data) {
                queryResult = routedResult.data;
            } else {
                queryResult = await executeSPARQL(sparqlQuery.query);
            }

            pipeline.stages.push({
                name: 'GraphDB',
                result: queryResult,
                time: Date.now() - startTime
            });

            // Stage 5: Format response
            let formatted;
            if (AGENTS.responseFormatter) {
                formatted = AGENTS.responseFormatter.format(queryResult, parseResult);
            } else {
                formatted = formatFallback(queryResult, parseResult);
            }

            pipeline.stages.push({
                name: 'ResponseFormatter',
                result: formatted,
                time: Date.now() - startTime
            });

            // Final result
            pipeline.result = formatted;
            pipeline.totalTime = Date.now() - startTime;

            log('[Orchestrator] ✓ Query processed in', pipeline.totalTime, 'ms');

            return pipeline;

        } catch (error) {
            log('[Orchestrator] Error:', error.message);
            return {
                error: error.message,
                pipeline: pipeline,
                totalTime: Date.now() - startTime
            };
        }
    }

    /**
     * Fallback routing when IntentRouter not available
     */
    async function routeFallback(parseResult) {
        const intent = parseResult.intent || 'semantic';
        
        return {
            intent: intent,
            source: 'fallback',
            data: null
        };
    }

    /**
     * Execute SPARQL query via API
     */
    async function executeSPARQL(sparql) {
        try {
            const response = await fetch('/daoanh/api/graphdb/sparql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: sparql })
            });
            
            return await response.json();
        } catch (error) {
            return { error: error.message };
        }
    }

    /**
     * Generate simple SPARQL fallback
     */
    function generateSimpleSPARQL(parseResult) {
        const { entities, lineage, timeRange } = parseResult;
        
        let where = '?person rdf:type :Monk . ?person rdfs:label ?label .';
        
        if (lineage) {
            where += ` ?person :lineage :${lineage} .`;
        }
        
        if (timeRange) {
            where += ` ?person :birth ?birth . FILTER(?birth >= ${timeRange.min} && ?birth < ${timeRange.max})`;
        }
        
        return `SELECT ?person ?label WHERE { ${where} } LIMIT 20`;
    }

    /**
     * Fallback formatter
     */
    function formatFallback(result, parseResult) {
        if (result.error) {
            return { text: 'Lỗi: ' + result.error, html: '<p>Lỗi: ' + result.error + '</p>', data: [] };
        }
        
        const bindings = result.results?.bindings || [];
        
        if (bindings.length === 0) {
            return { text: 'Không tìm thấy kết quả', html: '<p>Không tìm thấy kết quả</p>', data: [] };
        }
        
        const items = bindings.map(b => b.label?.value || b.person?.value);
        return {
            text: 'Tìm thấy ' + items.length + ' kết quả: ' + items.join(', '),
            html: '<ul>' + items.map(i => '<li>' + i + '</li>').join('') + '</ul>',
            data: items
        };
    }

    /**
     * Get agent by name
     */
    function getAgent(name) {
        return AGENTS[name];
    }

    /**
     * Get system status
     */
    function getStatus() {
        return {
            agents: Object.keys(AGENTS).map(k => ({
                name: k,
                loaded: AGENTS[k] !== null
            })),
            config: CONFIG,
            definitions: AGENT_DEFINITIONS
        };
    }

    /**
     * Log helper
     */
    function log(...args) {
        if (CONFIG.debug) {
            console.log('[Orchestrator]', ...args);
        }
    }

    // Public API
    return {
        init: init,
        processQuery: processQuery,
        getAgent: getAgent,
        getStatus: getStatus,
        AGENT_DEFINITIONS: AGENT_DEFINITIONS
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AgentOrchestrator;
}
