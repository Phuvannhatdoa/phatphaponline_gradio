// DILA Authority ID Normalization + JDN Time Conversion + Entity Linking
var DilaAuthority = {
    dilaBaseUrl: 'https://authority.dila.edu.tw/',
    
    // Generate DILA-style IDs
    generatePersonId: function(index) {
        return 'A' + String(index).padStart(6, '0');
    },
    
    generatePlaceId: function(index) {
        return 'PL' + String(index).padStart(9, '0');
    },
    
    // Convert lunar year to JDN (Julian Day Number)
    lunarYearToJDN: function(year, month, day) {
        month = month || 1;
        day = day || 1;
        var is BCE = year < 0;
        var absYear = Math.abs(year);
        
        let jdn;
        if (absYear <= 0) {
            jdn = 1721424.5; // 1 Jan 1 CE (Julian)
        } else {
            const a = Math.floor((14 - month) / 12);
            const y = absYear + 4800 - a;
            const m = month + 12 * a - 3;
            jdn = day + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
            
            if (is BCE) {
                jdn = 1721424.5 - (365 * (absYear - 1) + Math.floor((absYear - 1) / 4));
            }
        }
        
        return jdn;
    },
    
    // Parse period string to year range
    parsePeriod: function(periodStr) {
        const periodMap = {
            'Ancient India': { start: -600, end: -400 },
            'Eastern Jin': { start: 317, end: 420 },
            'Liang Dynasty': { start: 502, end: 557 },
            'Wei-North Dynasty': { start: 386, end: 534 },
            'Early Tang': { start: 618, end: 700 },
            'Tang Dynasty': { start: 618, end: 907 },
            'Late Ancient China': { start: 400, end: 500 },
            'Trần Dynasty (Vietnam)': { start: 1225, end: 1400 },
            'Trần Dynasty onwards': { start: 1225, end: 2026 },
            'Tang Dynasty onwards': { start: 618, end: 2026 },
            'Various': { start: -600, end: 2026 }
        };
        
        return periodMap[periodStr] || { start: 0, end: 2026 };
    },
    
    // Process all entities and add DILA fields
    normalizeEntities: function(entities) {
        let monkIndex = 1;
        let placeIndex = 1;
        
        return entities.map(entity => {
            const normalized = { ...entity };
            const periodData = this.parsePeriod(entity.period);
            
            // Assign DILA ID based on type
            if (entity.type === 'monk' || entity.type === 'bodhisattva') {
                normalized.dilaId = this.generatePersonId(monkIndex);
                normalized.dilaUrl = `${this.dilaBaseUrl}person/${normalized.dilaId}`;
                monkIndex++;
            } else {
                normalized.dilaId = this.generatePlaceId(placeIndex);
                normalized.dilaUrl = `${this.dilaBaseUrl}place/${normalized.dilaId}`;
                placeIndex++;
            }
            
            // Add JDN for timeline
            normalized.jdnStart = this.lunarYearToJDN(periodData.start);
            normalized.jdnEnd = this.lunarYearToJDN(periodData.end);
            normalized.yearStart = periodData.start;
            normalized.yearEnd = periodData.end;
            
            // Add entity links for description
            normalized.linkedEntities = this.extractEntities(entity.description, entities);
            
            return normalized;
        });
    },
    
    // Extract and link entities in description
    extractEntities: function(description, allEntities) {
        const links = [];
        
        allEntities.forEach(entity => {
            if (description.includes(entity.vietnamese) || description.includes(entity.searchKey)) {
                links.push({
                    name: entity.vietnamese,
                    nameZh: entity.searchKey,
                    type: entity.type,
                    dilaId: entity.dilaId || 'pending'
                });
            }
        });
        
        return links;
    },
    
    // Generate TTL RDF output
    generateTTL: function(entities) {
        let ttl = '';
        
        entities.forEach(entity => {
            if (!entity.dilaId) return;
            
            const type = entity.type === 'monk' || entity.type === 'bodhisattva' ? ':BuddhistMonk' : ':BuddhistPlace';
            
            ttl += `<${entity.dilaId}> a ${type} ;\n`;
            ttl += `    owl:sameAs <${entity.dilaUrl}> ;\n`;
            ttl += `    rdfs:label "${entity.vietnamese}"@vi ;\n`;
            
            if (entity.gps?.lat) {
                ttl += `    geo:lat ${entity.gps.lat} ;\n`;
                ttl += `    geo:long ${entity.gps.lon} ;\n`;
            }
            
            if (entity.jdnStart) {
                ttl += `    time:hasDateStart "${entity.jdnStart}"^^xsd:integer ;\n`;
                ttl += `    time:hasDateEnd "${entity.jdnEnd}"^^xsd:integer ;\n`;
            }
            
            ttl += '.\n\n';
        });
        
        return ttl;
    }
};

// Initialize and process
document.addEventListener('DOMContentLoaded', async () => {
    if (typeof SearchApp !== 'undefined' && SearchApp.criticalPlaces) {
        const normalized = DilaAuthority.normalizeEntities(SearchApp.criticalPlaces);
        
        // Expose normalized data globally
        window.normalizedEntities = normalized;
        
        // Log for verification
        console.log('✅ DILA Authority IDs normalized:', normalized.length);
        console.log('🔗 Sample:', normalized[0]);
        
        // Update SearchApp with normalized data
        SearchApp.criticalPlaces = normalized;
        
        // Generate TTL for knowledge graph
        const ttl = DilaAuthority.generateTTL(normalized);
        console.log('📝 TTL generated:', ttl.length, 'chars');
    }
});

console.log("🏛️ DilaAuthority module loaded");