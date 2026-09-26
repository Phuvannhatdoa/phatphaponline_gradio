/**
 * SPARQL Generator - AI Interpreter
 * Build SPARQL queries từ parsed keywords
 * 
 * @version: v4.3 (2026-04-10)
 * @file: src/js/ai/sparql_generator.js
 */

const SPARQLGenerator = (function() {
    'use strict';

    // SPARQL templates
    const TEMPLATES = {
        // Query thiền sư theo dòng truyền thừa
        byLineage: `
SELECT ?person ?birth ?death ?label
WHERE {
  ?person rdf:type :Monk .
  ?person :lineage :LINEAGE_ID .
  ?person rdfs:label ?label .
  OPTIONAL { ?person :birth ?birth }
  OPTIONAL { ?person :death ?death }
}
ORDER BY ?birth
LIMIT 100
`,
        // Query thiền sư theo thời gian
        byTimeRange: `
SELECT ?person ?birth ?death ?label
WHERE {
  ?person rdf:type :Monk .
  ?person rdfs:label ?label .
  ?person :birth ?birth .
  FILTER (?birth >= MIN_YEAR && ?birth < MAX_YEAR)
}
ORDER BY ?birth
LIMIT 100
`,
        // Query thiền sư theo dòng + thời gian
        byLineageAndTime: `
SELECT ?person ?birth ?death ?label
WHERE {
  ?person rdf:type :Monk .
  ?person :lineage :LINEAGE_ID .
  ?person rdfs:label ?label .
  OPTIONAL { ?person :birth ?birth }
  OPTIONAL { ?person :death ?death }
  FILTER (?birth >= MIN_YEAR && ?birth < MAX_YEAR)
}
ORDER BY ?birth
LIMIT 100
`,
        // Query thầy-trò (teacher-student)
        teacherStudent: `
SELECT ?teacher ?student ?label
WHERE {
  ?student :teacher ?teacher .
  ?student rdfs:label ?label .
}
LIMIT 50
`,
        // Query địa danh
        placeQuery: `
SELECT ?place ?gps ?label
WHERE {
  ?place rdf:type :Place .
  ?place rdfs:label ?label .
  OPTIONAL { ?place :gps ?gps }
}
LIMIT 50
`,
        // Query timeline (nơi ở theo năm)
        timeline: `
SELECT ?person ?place ?year
WHERE {
  ?person :visited ?place .
  ?person :inYear ?year .
}
ORDER BY ?year
LIMIT 100
`
    };

    // Namespace prefix
    const PREFIXES = `
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX : <http://phatphaponline.org/ontology#>
PREFIX dila: <http://dila.edu.tw/ontology#>
`;

    /**
     * Generate SPARQL query từ parsed result
     * @param {object} parsedResult - Kết quả từ SemanticParser
     * @returns {string} - SPARQL query string
     */
    function generate(parsedResult) {
        if (!parsedResult) {
            return { error: 'Invalid parsed result' };
        }

        const { intent, lineage, timeRange, entities, keywords } = parsedResult;

        // Xác định query type
        let queryType = getQueryType(intent, lineage, timeRange, entities);
        
        let query = buildQuery(queryType, {
            lineage: lineage,
            timeRange: timeRange,
            entities: entities,
            keywords: keywords
        });

        return {
            type: queryType,
            query: PREFIXES + '\n' + query,
            parsed: parsedResult
        };
    }

    /**
     * Xác định loại query cần build
     */
    function getQueryType(intent, lineage, timeRange, entities) {
        // Relational query (thầy-trò)
        if (intent === 'relational') {
            if (entities && entities.some(e => e.type === 'person')) {
                return 'teacherStudent';
            }
            return 'byLineage';
        }

        // Có cả lineage và timeRange
        if (lineage && timeRange) {
            return 'byLineageAndTime';
        }

        // Chỉ có lineage
        if (lineage) {
            return 'byLineage';
        }

        // Chỉ có timeRange
        if (timeRange) {
            return 'byTimeRange';
        }

        // Default: byLineage
        return 'byLineage';
    }

    /**
     * Build query từ template
     */
    function buildQuery(queryType, params) {
        let template = TEMPLATES[queryType] || TEMPLATES.byLineage;
        
        // Replace placeholders
        if (params.lineage) {
            template = template.replace(/LINEAGE_ID/g, params.lineage);
        }
        
        if (params.timeRange) {
            template = template.replace(/MIN_YEAR/g, params.timeRange.min);
            template = template.replace(/MAX_YEAR/g, params.timeRange.max);
        }

        return template;
    }

    /**
     * Generate query đơn giản (keyword-based)
     * @param {string} keyword - Từ khóa tìm kiếm
     * @returns {string}
     */
    function generateSimple(keyword) {
        return `${PREFIXES}
SELECT ?person ?label
WHERE {
  ?person rdf:type :Monk .
  ?person rdfs:label ?label .
  FILTER(CONTAINS(LCASE(?label), LCASE("${keyword}")))
}
LIMIT 20`;
    }

    /**
     * Generate query lấy thông tin chi tiết về một person
     * @param {string} personId - Person ID hoặc tên
     * @returns {string}
     */
    function generatePersonDetails(personId) {
        return `${PREFIXES}
SELECT ?prop ?value
WHERE {
  <http://phatphaponline.org/entity/${encodeURIComponent(personId)}> ?prop ?value .
}
LIMIT 50`;
    }

    /**
     * Generate query lấy timeline của một person
     * @param {string} personId - Person ID
     * @returns {string}
     */
    function generateTimeline(personId) {
        return `${PREFIXES}
SELECT ?place ?year ?gps
WHERE {
  <http://phatphaponline.org/entity/${encodeURIComponent(personId)}> :visited ?place .
  <http://phatphaponline.org/entity/${encodeURIComponent(personId)}> :inYear ?year .
  OPTIONAL { ?place :gps ?gps }
}
ORDER BY ?year`;
    }

    /**
     * Validate SPARQL query
     * @param {string} query 
     * @returns {object} - { valid: boolean, error?: string }
     */
    function validate(query) {
        if (!query || typeof query !== 'string') {
            return { valid: false, error: 'Empty query' };
        }

        // Basic validation: check for SELECT keyword
        if (!query.toUpperCase().includes('SELECT')) {
            return { valid: false, error: 'Missing SELECT keyword' };
        }

        // Check for WHERE clause
        if (!query.toUpperCase().includes('WHERE')) {
            return { valid: false, error: 'Missing WHERE clause' };
        }

        return { valid: true };
    }

    // Public API
    return {
        generate: generate,
        generateSimple: generateSimple,
        generatePersonDetails: generatePersonDetails,
        generateTimeline: generateTimeline,
        validate: validate,
        TEMPLATES: TEMPLATES,
        PREFIXES: PREFIXES
    };
})();

// Export for Node.js / ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SPARQLGenerator;
}
