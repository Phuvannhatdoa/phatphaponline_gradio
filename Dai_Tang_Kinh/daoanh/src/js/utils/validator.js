/**
 * Data Validator - Validation utilities
 * Validate entity data, GPS coordinates, dates
 * 
 * @version: v4.24 (2026-04-10)
 * @file: src/js/utils/validator.js
 */

const DataValidator = (function() {
    'use strict';

    // Validation rules
    const RULES = {
        // GPS coordinate ranges
        gps: {
            lat: { min: -90, max: 90 },
            lng: { min: -180, max: 180 }
        },
        
        // Year range
        year: {
            min: -2000,
            max: 2100
        },
        
        // Required fields for entities
        person: ['name', 'id'],
        place: ['name', 'id', 'gps'],
        lineage: ['name', 'id']
    };

    /**
     * Validate entity data
     * @param {object} entity - Entity to validate
     * @param {string} entityType - Type of entity
     * @returns {object} - Validation result
     */
    function validateEntity(entity, entityType) {
        const errors = [];
        const warnings = [];

        // Check required fields
        const required = RULES[entityType];
        if (required) {
            for (const field of required) {
                if (!entity[field]) {
                    errors.push(`Missing required field: ${field}`);
                }
            }
        }

        // Validate GPS
        if (entity.gps) {
            const gpsValidation = validateGPS(entity.gps);
            if (!gpsValidation.valid) {
                errors.push(...gpsValidation.errors);
            }
        }

        // Validate dates
        if (entity.birth || entity.death) {
            const dateValidation = validateDates(entity.birth, entity.death);
            if (!dateValidation.valid) {
                errors.push(...dateValidation.errors);
            }
        }

        // Validate name
        if (entity.name && entity.name.length < 2) {
            warnings.push('Name is too short');
        }

        // Validate ID format
        if (entity.id) {
            const idValidation = validateID(entity.id);
            if (!idValidation.valid) {
                errors.push(...idValidation.errors);
            }
        }

        return {
            valid: errors.length === 0,
            errors: errors,
            warnings: warnings
        };
    }

    /**
     * Validate GPS coordinates
     * @param {string|object} gps - GPS string or object
     * @returns {object}
     */
    function validateGPS(gps) {
        const errors = [];
        
        let lat, lng;
        
        if (typeof gps === 'string') {
            const parts = gps.split(/[,\s]+/);
            if (parts.length >= 2) {
                lat = parseFloat(parts[0]);
                lng = parseFloat(parts[1]);
            } else {
                errors.push('Invalid GPS format');
                return { valid: false, errors };
            }
        } else if (typeof gps === 'object') {
            lat = gps.lat || gps.latitude;
            lng = gps.lng || gps.longitude || gps.lng;
        } else {
            errors.push('GPS must be string or object');
            return { valid: false, errors };
        }

        if (isNaN(lat) || isNaN(lng)) {
            errors.push('Invalid GPS values');
        }

        if (lat < RULES.gps.lat.min || lat > RULES.gps.lat.max) {
            errors.push(`Latitude must be between ${RULES.gps.lat.min} and ${RULES.gps.lat.max}`);
        }

        if (lng < RULES.gps.lng.min || lng > RULES.gps.lng.max) {
            errors.push(`Longitude must be between ${RULES.gps.lng.min} and ${RULES.gps.lng.max}`);
        }

        return {
            valid: errors.length === 0,
            errors: errors,
            lat: lat,
            lng: lng
        };
    }

    /**
     * Validate birth/death dates
     * @param {number} birth 
     * @param {number} death 
     * @returns {object}
     */
    function validateDates(birth, death) {
        const errors = [];

        // Check year ranges
        if (birth !== undefined && birth !== null) {
            if (birth < RULES.year.min || birth > RULES.year.max) {
                errors.push(`Birth year ${birth} out of range`);
            }
        }

        if (death !== undefined && death !== null) {
            if (death < RULES.year.min || death > RULES.year.max) {
                errors.push(`Death year ${death} out of range`);
            }
        }

        // Check birth < death
        if (birth !== undefined && death !== undefined) {
            if (birth > death) {
                errors.push('Birth year cannot be after death year');
            }
        }

        // Check reasonable lifespan
        if (birth !== undefined && death !== undefined) {
            const lifespan = death - birth;
            if (lifespan > 150) {
                errors.push(`Lifespan of ${lifespan} years seems unrealistic`);
            }
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate ID format
     * @param {string} id 
     * @returns {object}
     */
    function validateID(id) {
        const errors = [];
        
        if (!id || typeof id !== 'string') {
            errors.push('ID must be a non-empty string');
            return { valid: false, errors };
        }

        // Check for valid characters
        if (!/^[a-zA-Z0-9_:.-]+$/.test(id)) {
            errors.push('ID contains invalid characters');
        }

        // Check length
        if (id.length < 2 || id.length > 100) {
            errors.push('ID length must be between 2 and 100 characters');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate entire dataset
     * @param {array} entities 
     * @param {string} entityType 
     * @returns {object}
     */
    function validateDataset(entities, entityType) {
        const results = {
            total: entities.length,
            valid: 0,
            invalid: 0,
            errors: [],
            warnings: []
        };

        for (let i = 0; i < entities.length; i++) {
            const validation = validateEntity(entities[i], entityType);
            
            if (validation.valid) {
                results.valid++;
            } else {
                results.invalid++;
                results.errors.push({
                    index: i,
                    id: entities[i].id,
                    errors: validation.errors
                });
            }

            results.warnings.push(...validation.warnings.map(w => ({
                index: i,
                warning: w
            })));
        }

        return results;
    }

    /**
     * Sanitize input
     * @param {string} input 
     * @returns {string}
     */
    function sanitize(input) {
        if (typeof input !== 'string') return '';
        
        return input
            .replace(/[<>]/g, '')  // Remove angle brackets
            .trim();
    }

    // Public API
    return {
        validateEntity: validateEntity,
        validateGPS: validateGPS,
        validateDates: validateDates,
        validateID: validateID,
        validateDataset: validateDataset,
        sanitize: sanitize
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataValidator;
}
