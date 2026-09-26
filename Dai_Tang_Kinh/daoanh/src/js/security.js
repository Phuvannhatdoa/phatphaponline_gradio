/**
 * P15: Security Utilities
 * - SPARQL sanitization
 * - Rate limiting helper
 * - Input validation
 */

const Security = {
    /**
     * Sanitize SPARQL query to prevent injection
     */
    sanitizeSparql: function(query) {
        if (!query || typeof query !== 'string') {
            return '';
        }

        // Remove potentially dangerous characters
        let sanitized = query
            .replace(/;/g, ' ; ')  // Split semicolons
            .replace(/--/g, '')    // Remove comments
            .replace(/\/\*/g, '')  // Remove block comment start
            .replace(/\*\//g, '')  // Remove block comment end
            .trim();

        // Check for suspicious patterns
        const dangerous = [
            /DROP\s+GRAPH/i,
            /DELETE\s+ALL/i,
            /CLEAR\s+GRAPH/i,
            /INSERT\s+DATA.*DROP/i,
            /LOAD\s+FILE/i
        ];

        for (const pattern of dangerous) {
            if (pattern.test(sanitized)) {
                console.warn("⚠️ Blocked potentially dangerous SPARQL:", pattern);
                throw new Error("Forbidden SPARQL pattern detected");
            }
        }

        return sanitized;
    },

    /**
     * Validate place ID format
     */
    validatePlaceId: function(id) {
        // DILA ID format: PL + 12 digits
        const dilaPattern = /^PL\d{12}$/;
        // CBETA ref format: T + number + n + number
        const cbetaPattern = /^T\d+n\d+$/;

        return dilaPattern.test(id) || cbetaPattern.test(id);
    },

    /**
     * Validate coordinates
     */
    validateCoordinates: function(lat, lon) {
        const latNum = parseFloat(lat);
        const lonNum = parseFloat(lon);

        return !isNaN(latNum) && !isNaN(lonNum) &&
               latNum >= -90 && latNum <= 90 &&
               lonNum >= -180 && lonNum <= 180;
    },

    /**
     * Rate limiting check (client-side)
     */
    rateLimit: {
        requests: {},
        
        check: function(key, maxRequests = 60, windowMs = 60000) {
            const now = Date.now();
            
            if (!this.requests[key]) {
                this.requests[key] = [];
            }

            // Remove old requests outside window
            this.requests[key] = this.requests[key].filter(time => now - time < windowMs);

            if (this.requests[key].length >= maxRequests) {
                console.warn("⚠️ Rate limit exceeded for:", key);
                return false;
            }

            this.requests[key].push(now);
            return true;
        }
    },

    /**
     * Generate CSP header
     */
    getCspHeader: function() {
        return "default-src 'self'; " +
               "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; " +
               "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; " +
               "img-src 'self' data: https:; " +
               "connect-src 'self' https://unpkg.com https://cdn.jsdelivr.net; " +
               "font-src 'self' https://fonts.gstatic.com;";
    },

    /**
     * Sanitize HTML output
     */
    sanitizeHtml: function(html) {
        if (!html) return '';
        
        return html
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    /**
     * Validate user input length
     */
    validateLength: function(str, min = 1, max = 1000) {
        if (!str || typeof str !== 'string') return false;
        return str.length >= min && str.length <= max;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Security;
}