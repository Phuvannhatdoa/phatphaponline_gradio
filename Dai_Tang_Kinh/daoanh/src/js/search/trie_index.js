/**
 * Trie Index - Zero-RAM Search Structure
 * JavaScript Trie implementation cho autocomplete
 * 
 * @version: v4.6 (2026-04-10)
 * @file: src/js/search/trie_index.js
 */

const TrieIndex = (function() {
    'use strict';

    class TrieNode {
        constructor() {
            this.children = new Map();
            this.items = new Set(); // Store item IDs at leaf
            this.isEnd = false;
        }
    }

    class Trie {
        constructor() {
            this.root = new TrieNode();
            this.itemMap = new Map(); // ID -> full item data
        }

        /**
         * Insert một item vào trie
         * @param {string} text - Text để insert (sẽ được normalize)
         * @param {object} item - Full item data
         */
        insert(text, item) {
            if (!text || !item) return;

            const normalized = normalizeText(text);
            let node = this.root;

            for (const char of normalized) {
                if (!node.children.has(char)) {
                    node.children.set(char, new TrieNode());
                }
                node = node.children.get(char);
                node.items.add(item.id);
            }

            node.isEnd = true;
            this.itemMap.set(item.id, item);
        }

        /**
         * Tìm kiếm prefix
         * @param {string} prefix - Prefix cần tìm
         * @param {number} limit - Số kết quả tối đa
         * @returns {array} - Danh sách items
         */
        searchPrefix(prefix, limit = 20) {
            if (!prefix) return [];

            const normalized = normalizeText(prefix);
            let node = this.root;

            // Navigate to prefix node
            for (const char of normalized) {
                if (!node.children.has(char)) {
                    return [];
                }
                node = node.children.get(char);
            }

            // Collect all items under this node
            const results = [];
            const visited = new Set();

            const dfs = (n, depth = 0) => {
                if (results.length >= limit) return;

                for (const id of n.items) {
                    if (!visited.has(id) && results.length < limit) {
                        const item = this.itemMap.get(id);
                        if (item) {
                            results.push(item);
                            visited.add(id);
                        }
                    }
                }

                for (const child of n.children.values()) {
                    dfs(child, depth + 1);
                    if (results.length >= limit) break;
                }
            };

            dfs(node);
            return results;
        }

        /**
         * Tìm kiếm chính xác
         * @param {string} text 
         * @returns {object|null}
         */
        exactMatch(text) {
            const normalized = normalizeText(text);
            let node = this.root;

            for (const char of normalized) {
                if (!node.children.has(char)) {
                    return null;
                }
                node = node.children.get(char);
            }

            if (node.isEnd && node.items.size > 0) {
                const id = node.items.values().next().value;
                return this.itemMap.get(id);
            }

            return null;
        }

        /**
         * Xóa một item
         * @param {string} text 
         * @param {string} itemId 
         */
        remove(text, itemId) {
            const normalized = normalizeText(text);
            let node = this.root;
            const path = [node];

            for (const char of normalized) {
                if (!node.children.has(char)) return;
                node = node.children.get(char);
                path.push(node);
            }

            node.items.delete(itemId);

            // Clean up empty nodes
            for (let i = path.length - 1; i > 0; i--) {
                const current = path[i];
                const parent = path[i - 1];
                const char = normalized[i - 1];

                if (current.items.size === 0 && current.children.size === 0) {
                    parent.children.delete(char);
                }
            }
        }

        /**
         * Load data từ JSON array
         * @param {array} items - Array of items
         * @param {string} textField - Field name cho text
         */
        loadFromArray(items, textField = 'name') {
            this.root = new TrieNode();
            this.itemMap.clear();

            for (const item of items) {
                const text = item[textField];
                if (text) {
                    this.insert(text, item);
                }
            }

            console.log(`[TrieIndex] Loaded ${items.length} items`);
        }

        /**
         * Get statistics
         */
        getStats() {
            let nodeCount = 0;
            let edgeCount = 0;

            const dfs = (node) => {
                nodeCount++;
                edgeCount += node.children.size;

                for (const child of node.children.values()) {
                    dfs(child);
                }
            };

            dfs(this.root);

            return {
                nodes: nodeCount,
                edges: edgeCount,
                items: this.itemMap.size
            };
        }
    }

    /**
     * Normalize text (lowercase + remove diacritics)
     */
    function normalizeText(text) {
        if (!text) return '';
        
        // Vietnamese diacritics removal
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

        return text.toLowerCase()
            .split('')
            .map(char => DIACRITICS[char] || char)
            .join('');
    }

    // Singleton instance
    let _instance = null;

    /**
     * Get/create singleton instance
     */
    function getInstance() {
        if (!_instance) {
            _instance = new Trie();
        }
        return _instance;
    }

    /**
     * Initialize với data
     */
    async function init(dataUrl, textField = 'name') {
        try {
            const response = await fetch(dataUrl);
            const data = await response.json();
            
            const trie = getInstance();
            trie.loadFromArray(Array.isArray(data) ? data : data.items || [], textField);
            
            return trie;
        } catch (error) {
            console.error('[TrieIndex] Init error:', error);
            return null;
        }
    }

    // Public API
    return {
        Trie: Trie,
        getInstance: getInstance,
        init: init,
        normalizeText: normalizeText
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TrieIndex;
}
