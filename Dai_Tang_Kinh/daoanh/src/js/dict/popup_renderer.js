/**
 * Popup Renderer - Popup Dictionary
 * Render tooltip popup for dictionary lookups
 * 
 * @version: v4.13c (2026-04-10)
 * @file: src/js/dict/popup_renderer.js
 */

const PopupRenderer = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        maxWidth: 350,
        maxHeight: 300,
        offsetX: 15,
        offsetY: 15,
        animationDuration: 150,
        zIndex: 10000,
        position: 'right'  // right, left, top, bottom
    };

    let popupElement = null;
    let visible = false;
    let currentEntry = null;

    /**
     * Initialize popup renderer
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        // Create popup element
        createPopupElement();

        console.log('[PopupRenderer] Initialized');
    }

    /**
     * Create popup DOM element
     */
    function createPopupElement() {
        if (popupElement) return;

        popupElement = document.createElement('div');
        popupElement.id = 'dict-popup';
        popupElement.className = 'dict-popup';
        
        // Apply styles
        Object.assign(popupElement.style, {
            position: 'fixed',
            display: 'none',
            maxWidth: CONFIG.maxWidth + 'px',
            maxHeight: CONFIG.maxHeight + 'px',
            zIndex: CONFIG.zIndex,
            padding: '12px',
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
            fontSize: '14px',
            lineHeight: '1.5',
            overflow: 'auto',
            transition: `opacity ${CONFIG.animationDuration}ms ease`
        });

        // Apply theme (Amber Gold)
        popupElement.style.background = '#1e293b';  // dark slate
        popupElement.style.color = '#f8fafc';  // white
        popupElement.style.border = '1px solid #d97706';  // amber

        document.body.appendChild(popupElement);
    }

    /**
     * Show popup with dictionary entry
     * @param {object} entry - Dictionary entry
     * @param {number} x - Mouse X position
     * @param {number} y - Mouse Y position
     */
    function show(entry, x, y) {
        if (!popupElement || !entry) return;

        currentEntry = entry;

        // Build HTML content
        const html = buildContent(entry);
        popupElement.innerHTML = html;

        // Calculate position
        const pos = calculatePosition(x, y);
        
        // Apply position
        popupElement.style.left = pos.left + 'px';
        popupElement.style.top = pos.top + 'px';
        popupElement.style.display = 'block';
        popupElement.style.opacity = '1';

        visible = true;

        // Add click-outside handler
        setTimeout(() => {
            document.addEventListener('click', handleClickOutside);
        }, 100);
    }

    /**
     * Hide popup
     */
    function hide() {
        if (!popupElement) return;

        popupElement.style.opacity = '0';
        
        setTimeout(() => {
            popupElement.style.display = 'none';
            currentEntry = null;
        }, CONFIG.animationDuration);

        visible = false;
        
        document.removeEventListener('click', handleClickOutside);
    }

    /**
     * Update position
     */
    function updatePosition(x, y) {
        if (!popupElement || !visible) return;

        const pos = calculatePosition(x, y);
        popupElement.style.left = pos.left + 'px';
        popupElement.style.top = pos.top + 'px';
    }

    /**
     * Check if popup is visible
     */
    function isVisible() {
        return visible;
    }

    /**
     * Build HTML content from entry
     */
    function buildContent(entry) {
        let html = '';

        // Word
        const word = entry.word || entry.term || 'Unknown';
        html += `<div class="dict-word">${escapeHtml(word)}</div>`;

        // Pronunciation
        if (entry.pronunciation || entry.pinyin) {
            html += `<div class="dict-pronunciation">${escapeHtml(entry.pronunciation || entry.pinyin)}</div>`;
        }

        // Meanings
        const meanings = entry.meanings || entry.definitions;
        
        if (meanings && Array.isArray(meanings)) {
            html += '<ul class="dict-meanings">';
            
            for (const meaning of meanings.slice(0, CONFIG.maxDefinitions)) {
                html += '<li>';
                
                // Part of speech
                if (meaning.pos || meaning.part) {
                    html += `<span class="dict-pos">${escapeHtml(meaning.pos || meaning.part)}</span> `;
                }
                
                // Definition
                html += escapeHtml(meaning.def || meaning.meaning || '');
                
                html += '</li>';
            }
            
            html += '</ul>';
        } else if (entry.definition) {
            // Single definition
            html += `<div class="dict-definition">${escapeHtml(entry.definition)}</div>`;
        }

        // Source
        if (entry.source) {
            html += `<div class="dict-source">Nguồn: ${escapeHtml(entry.source)}</div>`;
        }

        return html;
    }

    /**
     * Calculate popup position
     */
    function calculatePosition(x, y) {
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        let left = x + CONFIG.offsetX;
        let top = y + CONFIG.offsetY;

        // Check right edge
        if (left + CONFIG.maxWidth > windowWidth) {
            left = x - CONFIG.maxWidth - CONFIG.offsetX;
        }

        // Check bottom edge
        if (top + CONFIG.maxHeight > windowHeight) {
            top = windowHeight - CONFIG.maxHeight - 10;
        }

        // Ensure not negative
        left = Math.max(10, left);
        top = Math.max(10, top);

        return { left, top };
    }

    /**
     * Handle click outside popup
     */
    function handleClickOutside(event) {
        if (popupElement && !popupElement.contains(event.target)) {
            hide();
        }
    }

    /**
     * Escape HTML
     */
    function escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Destroy renderer
     */
    function destroy() {
        if (popupElement) {
            popupElement.remove();
            popupElement = null;
        }
        
        document.removeEventListener('click', handleClickOutside);
        visible = false;
    }

    // Public API
    return {
        init: init,
        show: show,
        hide: hide,
        updatePosition: updatePosition,
        isVisible: isVisible,
        destroy: destroy
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PopupRenderer;
}
