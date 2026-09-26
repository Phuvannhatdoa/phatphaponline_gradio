/**
 * Timeline Manager - GIS Timeline Component
 * Manage entities based on time filtering
 * 
 * @version: v4.1b (2026-04-10)
 * @file: src/js/timeline/manager.js
 */

const TimelineManager = (function() {
    'use strict';

    // Entity storage
    let entities = [];
    let filteredEntities = [];
    let currentYear = 1000;

    // Configuration
    const CONFIG = {
        showBirth: true,      // Show entities born in current year
        showDeath: true,     // Show entities died in current year
        showActive: true,    // Show entities active in current year
        showFloruit: true,   // Show entities in floruit period
        tolerance: 0         // Year tolerance for filtering
    };

    /**
     * Initialize manager
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }
        console.log('[TimelineManager] Initialized');
    }

    /**
     * Load entities from data source
     * @param {array} data - Array of entity objects
     */
    function loadEntities(data) {
        if (!Array.isArray(data)) {
            console.error('[TimelineManager] Invalid data:', data);
            return;
        }

        entities = data.map(normalizeEntity);
        console.log('[TimelineManager] Loaded', entities.length, 'entities');

        // Apply current filter
        filterByYear(currentYear);
    }

    /**
     * Normalize entity format
     * @param {object} entity 
     * @returns {object}
     */
    function normalizeEntity(entity) {
        return {
            id: entity.id || entity['@id'] || '',
            name: entity.name || entity.label || entity['rdfs:label'] || '',
            birth: parseYear(entity.birth || entity.birthYear),
            death: parseYear(entity.death || entity.deathYear),
            floruitStart: parseYear(entity.floruitStart || entity['floruit:notBefore']),
            floruitEnd: parseYear(entity.floruitEnd || entity['floruit:notAfter']),
            location: entity.location || entity.place || null,
            lineage: entity.lineage || entity.dong || null,
            gps: entity.gps || entity.coordinates || null
        };
    }

    /**
     * Parse year from various formats
     * @param {any} year 
     * @returns {number|null}
     */
    function parseYear(year) {
        if (year === null || year === undefined || year === '') {
            return null;
        }
        
        if (typeof year === 'number') {
            return year;
        }
        
        if (typeof year === 'string') {
            // Handle TCN format
            if (year.toLowerCase().includes('tcn') || year.startsWith('-')) {
                return parseInt(year.replace(/[^\d-]/g, ''));
            }
            return parseInt(year);
        }
        
        return null;
    }

    /**
     * Filter entities by year
     * @param {number} year 
     * @returns {array}
     */
    function filterByYear(year) {
        currentYear = year;
        
        filteredEntities = entities.filter(entity => {
            // Check birth year
            if (CONFIG.showBirth && entity.birth !== null) {
                if (Math.abs(entity.birth - year) <= CONFIG.tolerance) {
                    return true;
                }
            }
            
            // Check death year
            if (CONFIG.showDeath && entity.death !== null) {
                if (Math.abs(entity.death - year) <= CONFIG.tolerance) {
                    return true;
                }
            }
            
            // Check floruit period
            if (CONFIG.showFloruit) {
                if (entity.floruitStart !== null && entity.floruitEnd !== null) {
                    if (year >= entity.floruitStart && year <= entity.floruitEnd) {
                        return true;
                    }
                }
            }
            
            // Check if active (between birth and death)
            if (CONFIG.showActive) {
                const activeStart = entity.birth !== null ? entity.birth : -9999;
                const activeEnd = entity.death !== null ? entity.death : 9999;
                
                if (year >= activeStart && year <= activeEnd) {
                    return true;
                }
            }
            
            return false;
        });

        console.log('[TimelineManager] Filtered:', filteredEntities.length, 'entities for year', year);

        return filteredEntities;
    }

    /**
     * Get entities for a year range
     * @param {number} startYear 
     * @param {number} endYear 
     * @returns {array}
     */
    function getEntitiesInRange(startYear, endYear) {
        return entities.filter(entity => {
            const birth = entity.birth;
            const death = entity.death;
            
            if (birth !== null && death !== null) {
                // Entity existed during this period
                return !(death < startYear || birth > endYear);
            }
            
            if (birth !== null) {
                return birth <= endYear;
            }
            
            if (death !== null) {
                return death >= startYear;
            }
            
            return false;
        });
    }

    /**
     * Get timeline data (year -> entities)
     * @returns {object}
     */
    function getTimelineData() {
        const timeline = {};
        
        for (const entity of entities) {
            // Add birth
            if (entity.birth !== null) {
                if (!timeline[entity.birth]) {
                    timeline[entity.birth] = { born: [], died: [], active: [] };
                }
                timeline[entity.birth].born.push(entity);
            }
            
            // Add death
            if (entity.death !== null) {
                if (!timeline[entity.death]) {
                    timeline[entity.death] = { born: [], died: [], active: [] };
                }
                timeline[entity.death].died.push(entity);
            }
            
            // Add active years
            if (entity.birth !== null && entity.death !== null) {
                for (let year = entity.birth; year <= entity.death; year++) {
                    if (!timeline[year]) {
                        timeline[year] = { born: [], died: [], active: [] };
                    }
                    timeline[year].active.push(entity);
                }
            }
        }
        
        return timeline;
    }

    /**
     * Get current filtered entities
     * @returns {array}
     */
    function getFilteredEntities() {
        return filteredEntities;
    }

    /**
     * Get all entities
     * @returns {array}
     */
    function getAllEntities() {
        return entities;
    }

    /**
     * Get entities with GPS coordinates
     * @returns {array}
     */
    function getEntitiesWithGPS() {
        return filteredEntities.filter(e => e.gps !== null);
    }

    /**
     * Get configuration
     */
    function getConfig() {
        return { ...CONFIG };
    }

    /**
     * Set configuration
     * @param {object} config 
     */
    function setConfig(config) {
        Object.assign(CONFIG, config);
    }

    // Public API
    return {
        init: init,
        loadEntities: loadEntities,
        filterByYear: filterByYear,
        getEntitiesInRange: getEntitiesInRange,
        getTimelineData: getTimelineData,
        getFilteredEntities: getFilteredEntities,
        getAllEntities: getAllEntities,
        getEntitiesWithGPS: getEntitiesWithGPS,
        getConfig: getConfig,
        setConfig: setConfig
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimelineManager;
}
