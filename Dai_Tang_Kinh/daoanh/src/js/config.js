// Config for Buddhist Heritage Mapping (Phật Tổ Đạo Ảnh)
const CONFIG = {
    // Base URL for all API calls
    BASE_URL: "/daoanh",

    // GraphDB Repositories:
    // - dao_anh: Địa điểm Phật giáo (DILA/CBETA places)
    // - buddhist: Phả hệ Thiền sư (lineage tree - 2000+ monks)
    // 
    // Domain: https://phatphaponline.org/daoanh/ (via nginx proxy)
    // GraphDB: http://158.220.106.183:7200 (internal, direct access)
    get API_BASE() { return this.BASE_URL + "/api"; },
    get DATA_BASE() { return this.BASE_URL + "/data"; },

    GRAPHDB: {
        baseUrl: "http://158.220.106.183:7200",
        repository: "dao_anh",  // ⭐ PRIMARY - Địa điểm Đạo Ảnh
        get sparqlUrl() { return `${this.baseUrl}/repositories/${this.repository}/sparql`; },
        get updateUrl() { return `${this.baseUrl}/repositories/${this.repository}/statements`; },
        get importUrl() { return `${this.baseUrl}/import#user`; }
    },
    
    // GraphDB lineage (buddhist repo - for P11 pathfinding)
    GRAPHDB_LINEAGE: {
        baseUrl: "http://158.220.106.183:7200",
        repository: "buddhist",  // Phả hệ Thiền sư
        get sparqlUrl() { return `${this.baseUrl}/repositories/${this.repository}/sparql`; }
    },
    
    // Local JSON file
    JSON_FILE: "../data/places.json",
    
    // Auth
    AUTH_KEY: "buddhist_admin_auth",
    
    // GPS threshold (meters)
    GPS_THRESHOLD_METERS: 100,
    
    // UI
    ITEMS_PER_PAGE: 50
};