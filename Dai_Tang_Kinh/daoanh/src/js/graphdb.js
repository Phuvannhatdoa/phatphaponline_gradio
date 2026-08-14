// GraphDB SPARQL operations
const GraphDB = {
    /**
     * Execute SPARQL SELECT query
     */
    query: async function(sparql, format = "json") {
        const credentials = Auth.getCredentials();
        if (!credentials) throw new Error("Not authenticated");
        
        const url = CONFIG.GRAPHDB.sparqlUrl + "?query=" + encodeURIComponent(sparql);
        
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Authorization": `Basic ${credentials}`,
                "Accept": format === "json" ? "application/sparql-results+json" : "application/xml"
            }
        });
        
        if (!response.ok) {
            throw new Error(`Query failed: ${response.status}`);
        }
        
        return response.json();
    },
    
    /**
     * Execute SPARQL UPDATE (INSERT/DELETE)
     */
    update: async function(sparql) {
        const credentials = Auth.getCredentials();
        if (!credentials) throw new Error("Not authenticated");
        
        const response = await fetch(CONFIG.GRAPHDB.updateUrl, {
            method: "POST",
            headers: {
                "Authorization": `Basic ${credentials}`,
                "Content-Type": "application/sparql-update; charset=utf-8"
            },
            body: sparql
        });
        
        if (!response.ok) {
            throw new Error(`Update failed: ${response.status}`);
        }
        
        return true;
    },
    
    /**
     * Get all places with Vietnamese data
     */
    getAllPlaces: async function() {
        const sparql = `
            SELECT ?id ?nameZh ?nameVi ?lat ?lon ?country ?desc ?source
            WHERE {
                ?s a <http://www.phatphaponline.org/ontology/buddhist-kg#BuddhistPlace> .
                OPTIONAL { ?s <http://www.phatphaponline.org/ontology/buddhist-kg#cbetaId> ?id }
                OPTIONAL { ?s <http://www.phatphaponline.org/ontology/buddhist-kg#nameChinese> ?nameZh }
                OPTIONAL { ?s <http://www.phatphaponline.org/ontology/buddhist-kg#nameVietnamese> ?nameVi }
                OPTIONAL { ?s <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat }
                OPTIONAL { ?s <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?lon }
                OPTIONAL { ?s <http://www.phatphaponline.org/ontology/buddhist-kg#countryCode> ?country }
                OPTIONAL { ?s <http://schema.org/description> ?desc }
                OPTIONAL { ?s <http://www.phatphaponline.org/ontology/buddhist-kg#source> ?source }
            }
            LIMIT 10000
        `;
        
        return this.query(sparql);
    },
    
    /**
     * Update Vietnamese name for a place
     */
    updateVietnameseName: async function(placeId, nameVi) {
        const sparql = `
            DELETE {
                ?s <http://www.phatphaponline.org/ontology/buddhist-kg#nameVietnamese> ?old
            }
            INSERT {
                ?s <http://www.phatphaponline.org/ontology/buddhist-kg#nameVietnamese> "${nameVi}"@vi
            }
            WHERE {
                ?s <http://www.phatphaponline.org/ontology/buddhist-kg#cbetaId> "${placeId}" .
                OPTIONAL { ?s <http://www.phatphaponline.org/ontology/buddhist-kg#nameVietnamese> ?old }
            }
        `;
        
        return this.update(sparql);
    },
    
    /**
     * Update Vietnamese description for a place
     */
    updateVietnameseDesc: async function(placeId, descVi) {
        const sparql = `
            DELETE {
                ?s <http://schema.org/description> ?old
            }
            INSERT {
                ?s <http://schema.org/description> "${descVi}"@vi
            }
            WHERE {
                ?s <http://www.phatphaponline.org/ontology/buddhist-kg#cbetaId> "${placeId}" .
                OPTIONAL { ?s <http://schema.org/description> ?old }
            }
        `;
        
        return this.update(sparql);
    },
    
    /**
     * Update GPS coordinates
     */
    updateGPS: async function(placeId, lat, lon) {
        const sparql = `
            DELETE {
                ?s <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?oldLat .
                ?s <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?oldLon
            }
            INSERT {
                ?s <http://www.w3.org/2003/01/geo/wgs84_pos#lat> "${lat}" .
                ?s <http://www.w3.org/2003/01/geo/wgs84_pos#long> "${lon}"
            }
            WHERE {
                ?s <http://www.phatphaponline.org/ontology/buddhist-kg#cbetaId> "${placeId}" .
                OPTIONAL { ?s <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?oldLat }
                OPTIONAL { ?s <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?oldLon }
            }
        `;
        
        return this.update(sparql);
    }
};