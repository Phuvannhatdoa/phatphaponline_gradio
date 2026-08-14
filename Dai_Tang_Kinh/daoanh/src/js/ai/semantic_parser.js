/**
 * Semantic Parser - AI Interpreter
 * Nhận diện intent từ câu hỏi tiếng Việt
 * 
 * @version: v4.1 (2026-04-10)
 * @file: src/js/ai/semantic_parser.js
 */

const SemanticParser = (function() {
    'use strict';

    // Vietnamese patterns cho entities
    const PATTERNS = {
        // Loại thực thể (entity types)
        entityTypes: {
            person: /(thiền sư|pháp sư|đại sư|tổ sư|sư|cụ|dịch giả|nghĩa giả|nhà sư)/i,
            place: /(chùa|tự|thiền viện|tịnh xá|am|cốc|quán|trai|viện|núi|thắng)/i,
            lineage: /(dòng|phái|tông|lạt ma|lam tế|vân môn|thiền tông|trúc lâm|yên tử|quỳnh lâm)/i,
            time: /(thế kỷ|năm|thời|triều|đời|chính|phục)/i,
            text: /(kinh|văn|bài|luận|ngữ lục|truyện|triều)/i
        },

        // Keywords cho lineage
        lineages: {
            'lam tế': 'LamTe',
            'lâm tế': 'LamTe',
            'van mon': 'VanMon',
            'vân môn': 'VanMon',
            'truong tu': 'TruongTu',
            'trường tồn': 'TruongTu',
            'thien': 'Thien',
            'thiền': 'Thien',
            'yen tu': 'YenTu',
            'yên tử': 'YenTu',
            'quynh lam': 'QuynhLam',
            'quỳnh lâm': 'QuynhLam',
            'truc lam': 'TrucLam',
            'trúc lâm': 'TrucLam'
        },

        // Keywords cho thời gian (century mapping)
        centuries: {
            'thế kỷ 1': { min: 1, max: 100 },
            'thế kỷ 2': { min: 100, max: 200 },
            'thế kỷ 3': { min: 200, max: 300 },
            'thế kỷ 4': { min: 300, max: 400 },
            'thế kỷ 5': { min: 400, max: 500 },
            'thế kỷ 6': { min: 500, max: 600 },
            'thế kỷ 7': { min: 600, max: 700 },
            'thế kỷ 8': { min: 700, max: 800 },
            'thế kỷ 9': { min: 800, max: 900 },
            'thế kỷ 10': { min: 900, max: 1000 },
            'thế kỷ 11': { min: 1000, max: 1100 },
            'thế kỷ 12': { min: 1100, max: 1200 },
            'thế kỷ 13': { min: 1200, max: 1300 },
            'thế kỷ 14': { min: 1300, max: 1400 },
            'thế kỷ 15': { min: 1400, max: 1500 },
            'thế kỷ 16': { min: 1500, max: 1600 },
            'thế kỷ 17': { min: 1600, max: 1700 },
            'thế kỷ 18': { min: 1700, max: 1800 },
            'thế kỷ 19': { min: 1800, max: 1900 },
            'thế kỷ 20': { min: 1900, max: 2000 }
        },

        // Keywords cho intent detection
        intents: {
            factual: /ai|là ai|tên gì|ở đâu|năm sinh|năm mất|bao nhiêu tuổi/i,
            relational: /đệ tử|thầy|truyền thừa|dòng|phái|người học|sư phụ|học trò/i,
            semantic: /hỏi|tra cứu|tìm kiếm|tìm|cho biết|nói về|giải thích/i
        }
    };

    /**
     * Parse một câu hỏi tiếng Việt
     * @param {string} query - Câu hỏi cần parse
     * @returns {object} - Kết quả parse
     */
    function parse(query) {
        if (!query || typeof query !== 'string') {
            return { error: 'Invalid query' };
        }

        query = query.trim();
        
        const result = {
            original: query,
            entities: extractEntities(query),
            intent: detectIntent(query),
            lineage: extractLineage(query),
            timeRange: extractTimeRange(query),
            keywords: extractKeywords(query)
        };

        return result;
    }

    /**
     * Trích xuất các thực thể từ câu hỏi
     * @param {string} query 
     * @returns {array} - Danh sách entities
     */
    function extractEntities(query) {
        const entities = [];
        
        // Tìm person entities
        const personMatch = query.match(/([A-Za-zÀ-ỹ\s]+?)(?:\s+(?:thiền sư|pháp sư|đại sư|tổ sư|sư))/i);
        if (personMatch) {
            entities.push({
                type: 'person',
                value: personMatch[1].trim(),
                position: personMatch.index
            });
        }

        // Tìm place entities  
        const placePatterns = /(?:ở|đặt|tại)\s+([A-Za-zÀ-ỹ\s]+?)(?:\s|$)/gi;
        let match;
        while ((match = placePatterns.exec(query)) !== null) {
            const placeValue = match[1].trim();
            if (PATTERNS.entityTypes.place.test(placeValue) || 
                placeValue.includes('chùa') || placeValue.includes('núi')) {
                entities.push({
                    type: 'place',
                    value: placeValue,
                    position: match.index
                });
            }
        }

        return entities;
    }

    /**
     * Phát hiện loại intent
     * @param {string} query 
     * @returns {string} - Intent type
     */
    function detectIntent(query) {
        if (PATTERNS.intents.relational.test(query)) {
            return 'relational';
        }
        if (PATTERNS.intents.factual.test(query)) {
            return 'factual';
        }
        if (PATTERNS.intents.semantic.test(query)) {
            return 'semantic';
        }
        return 'semantic'; // default
    }

    /**
     * Trích xuất dòng truyền thừa
     * @param {string} query 
     * @returns {string|null} - Lineage ID
     */
    function extractLineage(query) {
        const lowerQuery = query.toLowerCase();
        
        for (const [keyword, lineageId] of Object.entries(PATTERNS.lineages)) {
            if (lowerQuery.includes(keyword)) {
                return lineageId;
            }
        }
        
        return null;
    }

    /**
     * Trích xuất khoảng thời gian
     * @param {string} query 
     * @returns {object|null} - Time range
     */
    function extractTimeRange(query) {
        const lowerQuery = query.toLowerCase();
        
        for (const [centuryStr, range] of Object.entries(PATTERNS.centuries)) {
            if (lowerQuery.includes(centuryStr)) {
                return range;
            }
        }

        // Thử parse năm cụ thể
        const yearMatch = query.match(/năm\s*(\d{3,4})/i);
        if (yearMatch) {
            const year = parseInt(yearMatch[1]);
            return { min: year, max: year + 1 };
        }

        return null;
    }

    /**
     * Trích xuất keywords còn lại
     * @param {string} query 
     * @returns {array}
     */
    function extractKeywords(query) {
        const keywords = [];
        const lowerQuery = query.toLowerCase();
        
        // Loại bỏ các từ đã dùng
        const stopWords = [
            'tìm', 'kiếm', 'hỏi', 'cho', 'biết', 'nói', 'về', 'các', 'những',
            'thiền sư', 'pháp sư', 'đại sư', 'tổ sư', 'sư', 'vị'
        ];
        
        // Simple keyword extraction
        const words = query.split(/\s+/).filter(w => w.length > 2);
        
        for (const word of words) {
            const lower = word.toLowerCase();
            if (!stopWords.some(sw => lower.includes(sw)) && 
                !Object.values(PATTERNS.lineages).some(l => lower.includes(l.toLowerCase()))) {
                keywords.push(word);
            }
        }
        
        return keywords;
    }

    // Public API
    return {
        parse: parse,
        extractEntities: extractEntities,
        detectIntent: detectIntent,
        extractLineage: extractLineage,
        extractTimeRange: extractTimeRange,
        
        // Export patterns for testing
        PATTERNS: PATTERNS
    };
})();

// Export for Node.js / ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SemanticParser;
}
