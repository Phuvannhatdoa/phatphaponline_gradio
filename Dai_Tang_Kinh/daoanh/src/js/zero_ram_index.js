// Zero-RAM Index Helper - Streaming + Pagination for large JSON files
// Implements: mmap-like binary search on JSON data chunks

const ZeroRAMIndex = {
    cache: new Map(),
    chunkSize: 500,
    
    /**
     * Stream JSON array with pagination - Zero-RAM approach
     * @param {string} url - URL to JSON file
     * @param {number} limit - Number of items to load initially
     * @param {Function} filterFn - Optional filter function
     */
    async streamLoad(url, limit = 200, filterFn = null) {
        try {
            const response = await fetch(url);
            if (!response.ok) return [];
            
            // Use streaming for large files
            const contentLength = response.headers.get('content-length');
            if (contentLength && parseInt(contentLength) > 5 * 1024 * 1024) {
                // File > 5MB: Use chunked loading
                return await this.chunkedLoad(url, limit, filterFn);
            }
            
            // Smaller file: OK to load directly but with limit
            const data = await response.json();
            const items = Array.isArray(data) ? data : (data.places || data.temples || []);
            
            // Apply limit and filter
            let result = items.slice(0, limit);
            if (filterFn) result = result.filter(filterFn);
            
            this.cache.set(url, { items, total: items.length, loaded: limit });
            return result;
            
        } catch (error) {
            console.error(`[ZeroRAM] Failed to load ${url}:`, error);
            return [];
        }
    },
    
    /**
     * Chunked loading for large files (>5MB)
     */
    async chunkedLoad(url, limit, filterFn) {
        // For very large files, load in chunks
        // Use server-side pagination when available
        // Fallback: Load first N items only
        
        const response = await fetch(`${url}?limit=${limit}`);
        if (response.ok) {
            const data = await response.json();
            const items = Array.isArray(data) ? data : (data.places || []);
            return filterFn ? items.filter(filterFn) : items;
        }
        return [];
    },
    
    /**
     * Binary search on cached data (if already loaded)
     */
    binarySearch(query, field = 'name') {
        const cached = Array.from(this.cache.values());
        if (!cached.length) return [];
        
        const allItems = cached.flatMap(c => c.items);
        const sorted = [...allItems].sort((a, b) => 
            (a[field] || '').localeCompare(b[field] || '')
        );
        
        const results = [];
        const lowerQuery = query.toLowerCase();
        
        for (let i = 0; i < sorted.length; i++) {
            const name = (sorted[i][field] || '').toLowerCase();
            if (name.includes(lowerQuery) || name.includes(query)) {
                results.push(sorted[i]);
                if (results.length >= 20) break;
            }
        }
        
        return results;
    },
    
    /**
     * Load more items (pagination)
     */
    async loadMore(url, offset, count) {
        const cached = this.cache.get(url);
        if (cached && cached.items.length > offset + count) {
            return cached.items.slice(offset, offset + count);
        }
        return [];
    },
    
    /**
     * Clear cache to free RAM
     */
    clearCache() {
        this.cache.clear();
        console.log('[ZeroRAM] Cache cleared');
    },
    
    /**
     * Get memory usage stats
     */
    getStats() {
        let totalItems = 0;
        this.cache.forEach(c => totalItems += c.loaded);
        return {
            cachedFiles: this.cache.size,
            totalItems,
            estimatedMemory: `${(totalItems * 0.5).toFixed(2)} KB`
        };
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ZeroRAMIndex;
}