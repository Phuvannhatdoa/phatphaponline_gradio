/**
 * Hover Detector - Popup Dictionary
 * Detect and handle hover events for dictionary lookups
 * 
 * @version: v4.13b (2026-04-10)
 * @file: src/js/dict/hover_detector.js
 */

const HoverDetector = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        enabled: true,
        delay: 300,           // ms before showing popup
        dismissDelay: 2000,   // ms before hiding popup
        maxDefinitions: 3,    // Max definitions to show
        minWordLength: 2,    // Minimum word length to lookup
        excludeTags: ['script', 'style', 'noscript', 'pre', 'code'],
        includeTags: ['p', 'div', 'span', 'td', 'th', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    };

    // Word patterns for Buddhist terms
    const PATTERNS = {
        // Vietnamese Buddhist terms
        vietnamese: /\b([A-Za-zÀ-ỹ\s]{2,30})\b/g,
        
        // Chinese characters (Hán tự)
        chinese: /[\u4e00-\u9fff]+/g,
        
        // Pali/Sanskrit (Romanized)
        pali: /\b([A-Za-z]{3,20})\b/g
    };

    let dictLoader = null;
    let popupRenderer = null;
    let timer = null;
    let currentWord = null;

    /**
     * Initialize hover detector
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        // Get dictionary and popup modules
        if (typeof DictLoader !== 'undefined') {
            dictLoader = DictLoader;
        }
        if (typeof PopupRenderer !== 'undefined') {
            popupRenderer = PopupRenderer;
        }

        // Bind events
        document.addEventListener('mouseover', handleMouseOver, true);
        document.addEventListener('mouseout', handleMouseOut, true);
        document.addEventListener('mousemove', handleMouseMove, true);

        console.log('[HoverDetector] Initialized');
    }

    /**
     * Handle mouse over
     */
    function handleMouseOver(event) {
        if (!CONFIG.enabled) return;

        const target = event.target;
        
        // Skip excluded tags
        if (CONFIG.excludeTags.includes(target.tagName.toLowerCase())) {
            return;
        }

        // Check if we should process this element
        if (!shouldProcess(target)) {
            return;
        }

        // Get word under cursor
        const word = getWordAtPosition(event.clientX, event.clientY);

        if (word && word.length >= CONFIG.minWordLength) {
            // Clear previous timer
            if (timer) {
                clearTimeout(timer);
            }

            // Set new timer to show popup
            timer = setTimeout(() => {
                showPopup(word, event.clientX, event.clientY);
            }, CONFIG.delay);
        }
    }

    /**
     * Handle mouse out
     */
    function handleMouseOut(event) {
        // Clear timer
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }

        // Dismiss popup after delay
        if (popupRenderer && popupRenderer.isVisible()) {
            setTimeout(() => {
                popupRenderer.hide();
            }, CONFIG.dismissDelay);
        }
    }

    /**
     * Handle mouse move (update position)
     */
    function handleMouseMove(event) {
        if (popupRenderer && popupRenderer.isVisible()) {
            // Optionally update position
            // popupRenderer.updatePosition(event.clientX, event.clientY);
        }
    }

    /**
     * Check if element should be processed
     */
    function shouldProcess(element) {
        const tag = element.tagName.toLowerCase();
        
        // Check include list
        if (CONFIG.includeTags.includes(tag)) {
            return true;
        }
        
        // Check for contenteditable
        if (element.isContentEditable) {
            return true;
        }
        
        return false;
    }

    /**
     * Get word at cursor position
     */
    function getWordAtPosition(x, y) {
        if (!document.caretPositionFromPoint) {
            // Fallback for browsers without caretPositionFromPoint
            return null;
        }

        try {
            const pos = document.caretPositionFromPoint(x, y);
            if (!pos) return null;

            const node = pos.offsetNode;
            const text = node.textContent || '';
            const offset = pos.offset;

            // Find word boundaries
            let start = offset;
            let end = offset;

            while (start > 0 && /[\wÀ-ỹ]/.test(text[start - 1])) {
                start--;
            }

            while (end < text.length && /[\wÀ-ỹ]/.test(text[end])) {
                end++;
            }

            return text.substring(start, end).trim();

        } catch (e) {
            return null;
        }
    }

    /**
     * Show popup with definition
     */
    function showPopup(word, x, y) {
        if (!dictLoader || !popupRenderer) {
            console.warn('[HoverDetector] Missing dependencies');
            return;
        }

        // Lookup word
        const entry = dictLoader.lookup(word);

        if (entry) {
            currentWord = word;
            popupRenderer.show(entry, x, y);
        }
    }

    /**
     * Enable/disable detector
     */
    function setEnabled(enabled) {
        CONFIG.enabled = enabled;
        
        if (!enabled) {
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            if (popupRenderer) {
                popupRenderer.hide();
            }
        }
    }

    /**
     * Get configuration
     */
    function getConfig() {
        return { ...CONFIG };
    }

    /**
     * Destroy detector
     */
    function destroy() {
        document.removeEventListener('mouseover', handleMouseOver, true);
        document.removeEventListener('mouseout', handleMouseOut, true);
        document.removeEventListener('mousemove', handleMouseMove, true);
        
        if (timer) {
            clearTimeout(timer);
        }
        
        if (popupRenderer) {
            popupRenderer.hide();
        }
    }

    // Public API
    return {
        init: init,
        showPopup: showPopup,
        setEnabled: setEnabled,
        getConfig: getConfig,
        destroy: destroy
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HoverDetector;
}
