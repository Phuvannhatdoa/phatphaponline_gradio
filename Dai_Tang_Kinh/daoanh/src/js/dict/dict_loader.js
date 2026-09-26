/**
 * Dictionary Loader - Popup Dictionary
 * Load StarDict dictionary files
 * 
 * @version: v4.13a (2026-04-10)
 * @file: src/js/dict/dict_loader.js
 */

const DictLoader = (function() {
    'use strict';

    const DEFAULT_DICT_PATH = '/data/dictionaries/';
    
    let dictionary = new Map();
    let index = new Map();
    let loaded = false;
    let loading = false;

    /**
     * Load dictionary from JSON file
     * @param {string} url - URL to dictionary JSON
     * @returns {Promise<boolean>}
     */
    async function load(url = null) {
        if (loaded || loading) {
            return loaded;
        }

        loading = true;
        const dictUrl = url || DEFAULT_DICT_PATH + 'dict_index.json';

        try {
            console.log('[DictLoader] Loading dictionary from', dictUrl);
            
            const response = await fetch(dictUrl);
            if (!response.ok) {
                throw new Error('Failed to load dictionary');
            }

            const data = await response.json();
            
            // Build lookup map
            for (const entry of data) {
                const word = entry.word || entry.term;
                if (word) {
                    dictionary.set(word.toLowerCase(), entry);
                    
                    // Also index by normalized form
                    const normalized = normalizeWord(word);
                    if (normalized !== word.toLowerCase()) {
                        index.set(normalized, entry);
                    }
                }
            }

            loaded = true;
            console.log('[DictLoader] ✓ Loaded', dictionary.size, 'entries');
            
            return true;

        } catch (error) {
            console.error('[DictLoader] Error:', error);
            loading = false;
            return false;
        }
    }

    /**
     * Load multiple dictionary files
     */
    async function loadMultiple(urls) {
        const results = [];
        
        for (const url of urls) {
            results.push(await load(url));
        }
        
        return results.every(r => r);
    }

    /**
     * Lookup a word
     * @param {string} word - Word to lookup
     * @returns {object|null}
     */
    function lookup(word) {
        if (!word) return null;

        const lower = word.toLowerCase();
        
        // Direct lookup
        if (dictionary.has(lower)) {
            return dictionary.get(lower);
        }
        
        // Normalized lookup
        const normalized = normalizeWord(lower);
        if (index.has(normalized)) {
            return index.get(normalized);
        }
        
        // Partial match (prefix)
        for (const [key, value] of dictionary) {
            if (key.startsWith(lower) || key.includes(lower)) {
                return value;
            }
        }
        
        return null;
    }

    /**
     * Search suggestions
     * @param {string} prefix - Search prefix
     * @param {number} limit - Max results
     * @returns {array}
     */
    function search(prefix, limit = 10) {
        if (!prefix || prefix.length < 2) return [];

        const lower = prefix.toLowerCase();
        const results = [];

        for (const [key, value] of dictionary) {
            if (key.startsWith(lower)) {
                results.push({
                    word: key,
                    definition: value.definition || value.meanings?.[0]?.def
                });
                
                if (results.length >= limit) break;
            }
        }

        return results;
    }

    /**
     * Normalize word (remove diacritics)
     */
    function normalizeWord(word) {
        const DIACRITICS = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd'
        };

        return word.split('').map(c => DIACRITICS[c] || c).join('');
    }

    /**
     * Get dictionary statistics
     */
    function getStats() {
        return {
            entries: dictionary.size,
            indexed: index.size,
            loaded: loaded
        };
    }

    /**
     * Clear dictionary
     */
    function clear() {
        dictionary.clear();
        index.clear();
        loaded = false;
        loading = false;
    }

    // Public API
    return {
        load: load,
        loadMultiple: loadMultiple,
        lookup: lookup,
        search: search,
        getStats: getStats,
        clear: clear,
        isLoaded: () => loaded
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DictLoader;
}
