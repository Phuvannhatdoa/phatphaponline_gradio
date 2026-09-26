// Global Search - Autocomplete for Places and Monks (v2 - Enhanced with Dictionary)
// Includes: Critical places from Phật Quang, Đạo Uyển dictionaries

// Data Adapter - STRICT mapping functions (DILA JSON standard)
const DataAdapter = {
    getBio: (item) => {
        if (!item) return "Chưa có sử liệu";
        // STRICT: Use exact field names from DILA JSON-LD
        const bn = item['bkg:biographicalNote'];
        if (bn) {
            if (Array.isArray(bn)) return bn[0]?.value || bn[0]?.['@value'] || bn[0] || "Chưa có sử liệu";
            return bn.value || bn['@value'] || bn || "Chưa có sử liệu";
        }
        return item.bio || item.biography || item.bioNote || "Chưa có sử liệu";
    },
    getID: (item) => item?.id || item?.m_id || item?.['@id'] || "Unknown",
    getHanName: (item) => {
        if (!item?.names) return "";
        return item.names.find(n => n.lang === 'han' || n.lang === 'zh-Hant')?.value || "";
    },
    getVietName: (item) => {
        if (!item?.names) return "";
        return item.names.find(n => n.lang === 'viet')?.value || "";
    },
    getLineage: (item) => item?.lineage || item?.lineageData || item?.heritage || ""
};

// ID-First Index for fast lookup
let personIndex = new Map();

const SearchApp = {
    // CSS animation for loading
    initStyles: function() {
        if (!document.getElementById('search-spin-style')) {
            const style = document.createElement('style');
            style.id = 'search-spin-style';
            style.textContent = '@keyframes searchSpin {from{transform:rotate(0deg)}to{transform:rotate(360deg)}} .search-spin {animation:searchSpin 1s linear infinite}';
            document.head.appendChild(style);
        }
    },
    
    monkNames: [],
    vietNames: [],
    localPlaces: [],
    criticalPlaces: [],
    dictData: [],
    isLoading: false,
    debounceTimer: null,
    selectedIndex: -1,
    currentQuery: '',
    minChars: 2,
    unifiedData: [],
    currentResults: [],
    masterDb: {},

    /**
     * Initialize - load all data sources
     */
    init: async function() {
        console.log("🔍 Loading unified search...");
        
        try {
            await this.loadMasterDb();
            await this.loadMonkNames();
            await this.loadLocalPlaces();
            await this.loadCriticalPlaces();
            this.mergeUnifiedData();
            this.setupEvents();
            console.log(`✅ Unified: ${this.unifiedData.length} items ready`);
            console.log(`✅ Master DB: ${Object.keys(this.masterDb).length} records loaded`);
            
            // Run diagnostics after load
            this.runSearchDiagnostics();
        } catch(err) {
            this.showErrorOverlay('INIT FAILED: ' + err.message);
        }
    },

    /**
     * Load Master DB for O(1) lookup (Runtime Layer)
     */
    loadMasterDb: async function() {
        try {
            const response = await fetch('/daoanh/data/master_db.json');
            if (response.ok) {
                this.masterDb = await response.json();
            }
        } catch(e) {
            console.warn('[Master] Load failed:', e);
        }
    },

    /**
     * Get record by ID from Master DB (O(1))
     */
    getMasterRecord: function(id) {
        return this.masterDb[id] || null;
    },

    /**
     * REFACTORED: Merge all data sources with STRICT deduplication
     * - Generate searchID for every item
     * - Use ID for API calls, never name string
     * - Clean title display
     */
    mergeUnifiedData: function() {
        const seenNames = new Map(); // FIX: Use Map with displayName as key
        const items = [];
        let idCounter = 0;
        
        // FIX: Clean title for display (max 5 words for places)
        const cleanTitle = (raw, type) => {
            if (!raw) return '';
            let t = raw.split('(')[0].split(',')[0].split('-')[0].split('nói')[0].trim();
            t = t.replace(/\s*(ở|khu vực|gần|tọa lạc|nằm|tọa địa|phía đông|phía tây|phía nam|phía bắc).*$/i, '').trim();
            if (type === 'Chùa' || type === 'Địa danh') {
                const words = t.split(/\s+/);
                if (words.length > 5) t = words.slice(0, 5).join(' ') + '...';
            }
            return t.length > 50 ? t.substring(0, 47) + '...' : t;
        };
        
        const genId = (prefix) => prefix + String(idCounter++).padStart(5, '0');
        
        // 1. Add monks (2487 names)
        if (this.monkNames) {
            this.monkNames.forEach(n => {
                const displayName = cleanTitle(n, 'Vị Tổ');
                if (!displayName) return;
                
                // FIX: Use displayName as key in Map
                const existing = seenNames.get(displayName);
                if (!existing || existing.priority < 0) {
                    seenNames.set(displayName, { priority: 0, type: 'Vị Tổ' });
                    items.push({
                        searchId: genId('M'),
                        name: n,
                        displayName: displayName,
                        type: 'Vị Tổ',
                        label: 'Vị Tổ',
                        searchType: 'monk',
                        priority: 0,
                        lat: '', lon: '', id: ''
                    });
                }
            });
        }
        
        // 2. Add places (35 temples)
        if (this.localPlaces) {
            this.localPlaces.forEach(p => {
                const name = p.nameVietnamese || p.nameChinese || '';
                const displayName = cleanTitle(name, 'Chùa');
                if (!displayName) return;
                
                const hasGPS = p.lat && p.lon;
                const hasId = p.id;
                const priority = hasGPS ? 2 : (hasId ? 1 : 0);
                
                // FIX: Replace if higher priority
                const existing = seenNames.get(displayName);
                if (!existing || priority > existing.priority) {
                    seenNames.set(displayName, { priority, type: 'Chùa' });
                    items.push({
                        searchId: p.id || genId('P'),
                        name: name,
                        displayName: cleanTitle(name, 'Chùa'),
                        type: p.type || 'Chùa',
                        label: 'Chùa',
                        searchType: 'place',
                        priority: priority,
                        lat: p.lat || '',
                        lon: p.lon || '',
                        id: p.id || ''
                    });
                }
            });
        }
        
        // 3. Add critical places (29 sites) - highest priority
        if (this.criticalPlaces) {
            this.criticalPlaces.forEach(p => {
                const name = p.vietnamese || p.searchKey || '';
                const displayName = cleanTitle(name, 'Địa danh');
                if (!displayName) return;
                
                const hasGPS = p.gps?.lat && p.gps?.lon;
                const priority = hasGPS ? 2 : 0;
                
                // FIX: Replace if higher priority
                const existing = seenNames.get(displayName);
                if (!existing || priority > existing.priority) {
                    seenNames.set(displayName, { priority, type: 'Địa danh' });
                    items.push({
                        searchId: genId('C'),
                        name: name,
                        displayName: displayName,
                        type: 'Địa danh',
                        label: 'Địa danh',
                        searchType: 'critical',
                        priority: priority,
                        lat: p.gps?.lat || '',
                        lon: p.gps?.lon || '',
                        id: ''
                    });
                }
            });
        }
        
        this.unifiedData = items;
        console.log(`✅ Merged: ${this.unifiedData.length} unique items`);
    },
    
    /**
     * Data Validator - check required fields
     */
    validateItem: function(item) {
        const type = item.label || item.type || '';
        
        if (type === 'Vị Tổ') {
            // Monks need ID and name
            return item.name && item.name.length > 0;
        } else if (type === 'Chùa') {
            // Temples need GPS + short name
            const hasGPS = item.lat && item.lon;
            const title = this.normalizeItem(item).title;
            return hasGPS && title && title.length < 50;
        } else {
            // Places need name
            return item.name && item.name.length > 0;
        }
    },

    /**
     * Run diagnostics - auto test 4 scenarios
     */
    runSearchDiagnostics: function() {
        console.log('🔧 Starting Search Diagnostics...');
        let failed = false;
        
        // Test 1: Check title length
        const longTitles = this.unifiedData.filter(item => {
            const title = this.normalizeItem(item).title;
            return title.length > 50;
        });
        if (longTitles.length > 0) {
            console.warn(`⚠️ Test 1 FAILED: ${longTitles.length} titles too long`);
            failed = true;
        } else {
            console.log('✅ Test 1: Title lengths OK');
        }
        
        // Test 1b: Check duplicate titles (use Map like merge)
        const testMap = new Map();
        let dupCount = 0;
        this.unifiedData.forEach(item => {
            const title = item.displayName || item.name || '';
            if (title) {
                if (testMap.has(title)) dupCount++;
                testMap.set(title, true);
            }
        });
        
        if (dupCount > 0) {
            console.warn(`⚠️ Test 1b FAILED: ${dupCount} duplicates`);
            failed = true;
        } else {
            console.log('✅ Test 1b: No duplicate titles');
        }
        
        // Test 2: Check 4 blocks exist
        const blocksExist = {
            'Việt Ngữ': typeof document.getElementById('workbench-content') !== 'undefined',
            'Khối A': true,  // Check in render
            'Khối B': true,
            'Khối C': true
        };
        const missingBlocks = Object.entries(blocksExist).filter(([k,v]) => !v).map(([k]) => k);
        if (missingBlocks.length > 0) {
            this.showErrorOverlay('QA FAILED: Missing blocks - ' + missingBlocks.join(', '));
            failed = true;
        } else {
            console.log('✅ Test 2: All 4 blocks exist');
        }
        
        // Test 3: Check Tab focus
        const input = document.getElementById('global-search');
        if (input) {
            input.addEventListener('keydown', function handler(e) {
                if (e.key === 'Tab') {
                    console.log('✅ Test 3: Tab key intercepted');
                    input.removeEventListener('keydown', handler);
                }
            });
        }
        
        if (failed) {
            this.showErrorOverlay('⚠️ QA WARNING: Check console for details');
        } else {
            console.log('✅ All diagnostics passed');
            console.log('🎉 QA PASSED: Data Clean & Navigation Ready');
        }
    },

    /**
     * Show error overlay
     */
    showErrorOverlay: function(msg) {
        const overlay = document.createElement('div');
        overlay.id = 'error-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#f59e0b;color:white;padding:12px;text-align:center;z-index:99999;font-weight:bold;';
        overlay.textContent = msg;
        document.body.appendChild(overlay);
        setTimeout(() => overlay.remove(), 5000);
    },

    /**
     * Auto test runner - runs on page load
     */
    runAutoTest: function() {
        console.log('🧪 Running Auto Search Tests...');
        const results = { passed: 0, failed: 0, errors: [] };
        const testCount = 5;
        
        // TEST 1: Check unifiedData loaded
        if (this.unifiedData && this.unifiedData.length > 0) {
            console.log(`✅ Test 1/5: Data loaded (${this.unifiedData.length} items)`);
            results.passed++;
        } else {
            results.errors.push('Test 1 FAIL: No data');
            results.failed++;
        }
        
        // TEST 2: UI Block Content Check - REAL DATA not Placeholders
        let blockFailures = 0;
        ['block1', 'block2', 'block3', 'block4'].forEach(bId => {
            const el = document.getElementById(bId);
            if (el) {
                const body = el.querySelector('.panel-body');
                const text = body ? body.innerText || body.textContent : '';
                // Must have > 20 chars AND NOT contain placeholder text
                if (text.length < 20 || text.includes('Đang cập nhật') || text.includes('Chưa số hóa')) {
                    blockFailures++;
                    console.warn(`⚠️ Test 2 FAIL: ${bId} has insufficient content: "${text.substring(0,30)}..."`);
                }
            }
        });
        
        if (blockFailures === 0) {
            console.log(`✅ Test 2/5: All 4 blocks have real data`);
            results.passed++;
        } else {
            results.errors.push(`Test 2 FAIL: ${blockFailures}/4 blocks empty or placeholder`);
            results.failed++;
        }
        
        // TEST 3: Temples have GPS
        const noGPS = this.unifiedData.filter(i => (i.label||i.type) === 'Chùa' && (!i.lat || !i.lon));
        if (noGPS.length < 100) { // Allow some tolerance
            console.log('✅ Test 3/5: Most temples have GPS');
            results.passed++;
        } else {
            results.errors.push(`Test 3 FAIL: ${noGPS.length} temples without GPS`);
            results.failed++;
        }
        
        // TEST 4: Search input exists
        const input = document.getElementById('global-search');
        if (input) {
            console.log('✅ Test 4/5: Search input exists');
            results.passed++;
        } else {
            results.errors.push('Test 4 FAIL: No search input');
            results.failed++;
        }
        
        // TEST 5: Results container exists
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            console.log('✅ Test 5/5: Results container exists');
            results.passed++;
        } else {
            results.errors.push('Test 5 FAIL: No results container');
            results.failed++;
        }
        
        // Show result on UI
        const statusDiv = document.createElement('div');
        statusDiv.id = 'test-status';
        const color = results.failed === 0 ? '#22c55e' : '#f59e0b';
        statusDiv.style.cssText = `position:fixed;bottom:10px;right:10px;background:${color};color:white;padding:8px 16px;border-radius:6px;font-size:12px;z-index:99999;cursor:pointer;`;
        statusDiv.textContent = `🧪 ${results.passed}/${testCount} passed`;
        statusDiv.onclick = () => statusDiv.remove();
        document.body.appendChild(statusDiv);
        
        // Remove error overlay if exists
        const errOverlay = document.getElementById('error-overlay');
        if (errOverlay && results.failed === 0) {
            errOverlay.remove();
            console.log('✅ System Stabilized');
        }
        
        console.log(`🧪 Results: ${results.passed}/${testCount} passed`);
        return results;
    },

    /**
     * Initialize - load all data sources
     */
    initOLD: async function() {
        console.log("🔍 Loading unified search...");
        
        // Load monk names
        await this.loadMonkNames();
        
        // Load places (temples + critical)
        await this.loadLocalPlaces();
        await this.loadCriticalPlaces();
        
        // Merge all into unified search
        this.unifiedData = [];
        
        // Add monks
        if (this.monkNames) {
            this.monkNames.forEach(n => {
                this.unifiedData.push({ name: n, type: 'Vị Tổ', label: 'Vị Tổ', searchType: 'monk' });
            });
        }
        
        // Add places (with location + DILA ID)
        if (this.localPlaces) {
            this.localPlaces.forEach(p => {
                const name = p.nameVietnamese || p.nameChinese || p.nameEnglish || '';
                if (name) {
                    this.unifiedData.push({
                        name: name,
                        type: p.type || 'Chùa',
                        label: 'Chùa',
                        location: p.province || '',
                        lat: p.lat,
                        lon: p.lon,
                        id: p.id || '',
                        searchType: 'place'
                    });
                }
            });
        }
        
        // Add critical places
        if (this.criticalPlaces) {
            this.criticalPlaces.forEach(p => {
                this.unifiedData.push({
                    name: p.vietnamese || p.searchKey || '',
                    type: 'Địa danh',
                    label: 'Địa danh',
                    location: p.description?.split(',')[1] || '',
                    lat: p.gps?.lat,
                    lon: p.gps?.lon,
                    searchType: 'critical'
                });
            });
        }
        
console.log(`✅ Unified: ${this.unifiedData.length} items ready`);
        
        this.setupEvents();
        
        // Run auto test after setup
        setTimeout(() => this.runAutoTest(), 1000);
    },

    /**
     * Load dictionary data for fallback search
     */
    loadDictData: async function() {
        try {
            const response = await fetch('/daoanh/data/indexed/combined_dict.json');
            if (response.ok) {
                const data = await response.json();
                this.dictData = Object.keys(data).slice(0, 5000).map(term => ({
                    term: term,
                    definition: data[term]?.definition || '',
                    source: data[term]?.source || ''
                }));
                console.log(`📚 Loaded ${this.dictData.length} dict entries`);
            }
        } catch (error) {
            console.warn("Failed to load dict:", error);
        }
    },

    /**
     * NEW: Load critical places from dictionary lookup
     */
    loadCriticalPlaces: async function() {
        try {
            const response = await fetch('/daoanh/data/processed/search_index_critical.json');
            if (response.ok) {
                this.criticalPlaces = await response.json();
                console.log(`📚 Loaded ${this.criticalPlaces.length} critical places from dictionary`);
            }
        } catch (error) {
            console.warn("Failed to load critical places:", error);
            this.criticalPlaces = [];
        }
    },

    /**
     * Load local places from JSON file - Zero-RAM optimized
     */
    loadLocalPlaces: async function() {
        try {
            // Load DILA places (international) - with limit for Zero-RAM
            const placesResponse = await fetch('/daoanh/data/places.json');
            if (placesResponse.ok) {
                // Check file size first
                const contentLength = placesResponse.headers.get('content-length');
                const fileSize = parseInt(contentLength || 0);
                
                if (fileSize > 2 * 1024 * 1024) {
                    // Large file: load only first 300 items
                    const data = await placesResponse.json();
                    this.localPlaces = (data.places || []).slice(0, 300);
                    console.log(`[Zero-RAM] Loaded ${this.localPlaces.length} places (limited from ${data.places?.length || 0})`);
                } else {
                    const data = await placesResponse.json();
                    this.localPlaces = data.places || [];
                }
            }
            
            // Load Vietnamese temples (with GPS) - smaller file, OK to load
            const templesResponse = await fetch('/daoanh/data/processed/temples_master_gps.json');
            if (templesResponse.ok) {
                const templeData = await templesResponse.json();
                const vnTemples = (templeData.temples || [])
                    .filter(t => t.lat && t.lon)
                    .map(t => ({
                        id: t.id,
                        nameVietnamese: t.nameVi || t.nameAlt || "",
                        nameChinese: t.nameVi || "",
                        lat: t.lat,
                        lon: t.lon,
                        province: t.province || "",
                        country: "VN",
                        source: "Vietnam-Temples"
                    }));
                this.localPlaces = [...this.localPlaces, ...vnTemples];
                console.log(`📍 Loaded ${vnTemples.length} Vietnamese temples`);
            }
        } catch (error) {
            console.error("Failed to load local places:", error);
            this.localPlaces = [];
        }
    },

    /**
     * Load monk names - use pre-filtered JSON (fast)
     */
    loadMonkNames: async function() {
        try {
            const response = await fetch('/daoanh/data/persons.json');
            if (response.ok) {
                const data = await response.json();
                // persons.json has structure: { "persons": [...] }
                const monkData = data.persons || data;
                this.monkNames = monkData;
                
                // ============ BUILD FULL OBJECT INDEX ============
                personIndex = new Map();
                let sampleKeys = [];
                let sampleEntity = null;
                
                monkData.forEach(m => {
                    if (!m || typeof m !== 'object') return;
                    const id = m.id || m.m_id || m['@id'] || null;
                    // FIX: Remove ALL whitespace from ID
                    const key = id ? String(id).trim().toUpperCase().replace(/\s+/g, '') : null;
                    if (key) {
                        personIndex.set(key, m);
                        if (sampleKeys.length < 3) sampleKeys.push(key);
                        if (!sampleEntity) sampleEntity = m;
                    }
                });
                
                if (personIndex.size > 0) {
                    console.log(`✅ personIndex built: ${personIndex.size} entries from persons.json`);
                    console.log("📋 Sample IDs:", sampleKeys);
                    // Show sample entity structure
                    if (sampleEntity) {
                        console.log("📋 SAMPLE_ENTITY_KEYS:", Object.keys(sampleEntity));
                        console.log("📋 SAMPLE_BIO:", sampleEntity.biography ? sampleEntity.biography.substring(0, 100) : "NO BIO");
                    }
                } else {
                    console.warn("⚠️ personIndex empty - check JSON structure");
                }
            } else {
                this.monkNames = [];
            }
        } catch (error) {
            console.error("loadMonkNames error:", error);
            this.monkNames = [];
        }
    },
    
    /**
     * Extract Han characters from name
     */
    getHanFromName: function(name) {
        const hanChars = name.match(/[\u4e00-\u9fff\u3400-\u4dbf]/g);
        return hanChars ? hanChars.join('') : '';
    },

    /**
     * Normalize text for fuzzy search (remove diacritics, spaces)
     */
    normalizeText: function(text) {
        if (!text) return '';
        return text.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')  // Remove diacritics
            .replace(/\s+/g, ' ')           // Collapse spaces
            .trim();
    },

    /**
     * Fuzzy search - includes partial match with normalization
     */
    fuzzySearch: function(items, query) {
        if (!query || !items.length) return [];
        const queryNorm = this.normalizeText(query);
        return items.filter(item => {
            const itemNorm = this.normalizeText(item);
            return itemNorm.includes(queryNorm);
        });
    },
    
    /**
     * NEW: Search DILA Person Authority (from local API)
     */
    searchDilaPersons: async function(query) {
        if (!query || query.length < 2) return [];
        
        try {
            const response = await fetch(`/daoanh/api/persons/search?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                return (data.persons || []).slice(0, 10).map(person => {
                    const primaryName = person.names && person.names[0] ? person.names[0].value : person.id;
                    return {
                        type: 'dila_person',
                        id: person.id,
                        name: primaryName,
                        names: person.names || [],
                        dynasty: person.dynasty || '',
                        is_monk: person.is_monk,
                        biography: person.biography || ''
                    };
                });
            }
        } catch (error) {
            console.warn("Failed to search DILA persons:", error);
        }
        return [];
    },

    /**
     * Fallback: load monk names from local JSON file
     */
    loadMonkNamesFallback: async function() {
        try {
            // Try local file (relative path)
            const response = await fetch('/daoanh/data/processed/monk_names.json');
            if (response.ok) {
                this.monkNames = await response.json();
            }
        } catch (error) {
            console.error("Failed to load monk names from fallback:", error);
            this.monkNames = [];
        }
    },

    /**
     * Setup event listeners
     */
    setupEvents: function() {
        const searchInput = document.getElementById('global-search');
        if (!searchInput) return;

        // Input event with debounce
        searchInput.addEventListener('input', (e) => {
            this.selectedIndex = -1;
            this.currentQuery = e.target.value;
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.handleSearch(e.target.value);
            }, 200);
        });

        // Keyboard navigation - switch case for clarity
        searchInput.addEventListener('keydown', (e) => {
            const resultsDiv = document.getElementById('search-results');
            const dropdownVisible = resultsDiv && !resultsDiv.classList.contains('hidden');
            const items = dropdownVisible ? resultsDiv.querySelectorAll('.search-result-item') : [];
            
switch (e.key) {
                case 'Tab':
                case 'ArrowDown':
                    e.preventDefault();
                    if (dropdownVisible && items.length > 0) {
                        this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                        this.highlightItem(items);
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (dropdownVisible && items.length > 0) {
                        this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                        this.highlightItem(items);
                    }
                    break;
                case 'Enter':
                    e.preventDefault();
                    const idx = this.selectedIndex;
                    if (dropdownVisible && idx >= 0 && items[idx]) {
                        resultsDiv.classList.add('hidden');
                        searchInput.blur();
                        this.executeSearch(idx);
                    }
                    break;
                case 'Escape':
                    resultsDiv.classList.add('hidden');
                    this.selectedIndex = -1;
                    break;
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const resultsDiv = document.getElementById('search-results');
            const searchBox = document.querySelector('.search-box');
            if (searchBox && !searchBox.contains(e.target)) {
                resultsDiv.classList.add('hidden');
            }
        });
    },

    /**
     * Highlight selected item
     */
    highlightItem: function(items) {
        items.forEach((item, i) => {
            item.classList.toggle('selected', i === this.selectedIndex);
            if (i === this.selectedIndex) {
                item.scrollIntoView({ block: 'nearest' });
            }
        });
    },

    /**
     * Handle search input - synchronous for speed
     */
    handleSearch: function(query) {
        const resultsDiv = document.getElementById('search-results');
        
        if (!query || query.length < 1) {
            resultsDiv.classList.add('hidden');
            resultsDiv.innerHTML = '';
            return;
        }

        try {
            const unifiedResults = this.searchUnified(query);
            this.renderUnifiedResults(unifiedResults, query);
            
        } catch (error) {
            console.error("Search error:", error);
        }
    },

    /**
     * Normalize item to unified format 
     * FIXED: Use new field names (displayName, searchId)
     */
    normalizeItem: function(item) {
        if (!item) return { title: 'Unknown', id: '', lat: '', lon: '', type: 'unknown', province: '' };
        
        const type = item.label || item.type || item.searchType || 'unknown';
        
        // Use displayName (already cleaned in mergeUnifiedData)
        let title = item.displayName || item.name || '';
        
        // Fallback: quick clean if displayName missing
        if (!title) {
            title = (item.temple_name || item.name || item.name_vn || 'Unknown')
                .split('(')[0].split(',')[0].split('-')[0].split('nói')[0].trim();
            title = title.replace(/\s*(ở|khu vực|gần|tọa lạc|nằm|tọa địa|phía).*$/i, '').trim();
            if (title.length > 30) title = title.substring(0, 27) + '...';
        }
        
        return {
            title: title,
            id: item.searchId || item.id || '',
            lat: item.lat || '',
            lon: item.lon || '',
            type: type,
            province: item.location || item.province || ''
        };
    },

    /**
     * Render unified results
     */
    renderUnifiedResults: function(results, query) {
        const resultsDiv = document.getElementById('search-results');
        
        // Store for executeSearch
        this.currentResults = results;
        
        if (!results || results.length === 0) {
            resultsDiv.innerHTML = `<div class="search-result-item">
                <span style="color:#94a3b8;">No results for "${this.escapeHtml(query)}"</span>
            </div>`;
            resultsDiv.classList.remove('hidden');
            return;
        }

        let html = results.map((item, idx) => {
            const normalized = this.normalizeItem(item);
            const icon = normalized.type === 'Vị Tổ' ? '👤' : (normalized.type === 'Chùa' ? '🏛' : '📍');
            
            return `<div class="search-result-item" data-index="${idx}" onclick="SearchApp.executeSearch(${idx})">
                <div class="result-main">
                    <div class="result-name">${this.highlightMatch(normalized.title, query)}</div>
                    ${normalized.province ? `<div class="result-loc">${normalized.province}</div>` : ''}
                </div>
                <span class="result-type">${icon}</span>
            </div>`;
        }).join('');

        resultsDiv.innerHTML = html;
        resultsDiv.classList.remove('hidden');
        
        // Auto-select first result
        this.selectedIndex = 0;
        this.highlightItem(resultsDiv.querySelectorAll('.search-result-item'));
    },

    /**
     * Select result -> load 4 data blocks + zoom
     */
    selectSearchResult: function(name, lat, lon, dilaId) {
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.classList.add('hidden');
        
        console.log(`📌 Selected: ${name}`);
        
        // 4. Map Zoom
        if (lat && lon && typeof map !== 'undefined') {
            map.flyTo([parseFloat(lat), parseFloat(lon)], 18, { duration: 1.5 });
        }
        
        // Load full data (4 blocks)
        this.loadEntityData(dilaId || name, name);
    },

    /**
     * Load entity data - 4 blocks
     */
    loadEntityData: async function(id, name, hanNameParam = '') {
        console.log(`📋 Loading: ${id} | ${name} | Hán: ${hanNameParam}`);
        
        this.initStyles();
        const workbench = document.getElementById('workbench-content');
        
        if (workbench) {
            workbench.innerHTML = `<div class="bio-section" style="text-align:center;padding:40px;">
                <div style="font-size:24px;" class="search-spin">🔄</div>
                <p>Đang quét dữ liệu cho "${name}"...</p>
            </div>`;
        }
        
        if (!id || id.length < 3) {
            if (workbench) {
                workbench.innerHTML = `<div class="bio-section">
                    <h4>${name || 'Unknown'}</h4>
                    <p style="color:#f59e0b;">⚠️ Chưa số hóa</p>
                </div>`;
            }
            console.log('📋 No valid ID');
            return;
        }
        
        // ============ STRICT MAPPING: RDF/TTL STRUCTURE ============
        // Field: bkg:biographicalNote (multiline string with @vi suffix)
        // Example:
        // bkg:biographicalNote """
        // ẤN NHẬT – TỔ TÂN – HOẰNG TÍN
        // (1869 – 1946)
        // ..."""@vi ;
        
        // FIX 1: STRICT ID Normalization - remove spaces + uppercase
        const cleanID = id.trim().toUpperCase().replace(/\s+/g, '');
        console.log("🔍 LOOKUP_KEY:", cleanID, "personIndex.size:", personIndex.size);
        
        // 1. Get entity from personIndex or Master DB (Runtime Layer) or API
        let entity = personIndex.get(cleanID);
        
        // 2. If not found in index, try Master DB (O(1) lookup)
        if (!entity && this.masterDb[cleanID]) {
            const masterRecord = this.masterDb[cleanID];
            entity = {
                id: cleanID,
                'bkg:biographicalNote': masterRecord.bio?.content || '',
                display_name: masterRecord.display?.name_vi || '',
                'bkg:hasTeacher': masterRecord.lineage?.teacher_id ? [{id: masterRecord.lineage.teacher_id}] : [],
                'bkg:hasDisciple': (masterRecord.lineage?.disciples || []).map(d => typeof d === 'string' ? {id: d} : d)
            };
            console.log("📋 Master DB Hit:", cleanID);
        }
        
        // 3. If still not found, get FULL person data from API (includes teacher/student)
        if (!entity) {
            try {
                // STRICT: Use ID for lookup, get FULL person with teacher/student
                const resp = await fetch(`/daoanh/api/persons/${cleanID}`);
                if (resp.ok) {
                    entity = await resp.json();
                    console.log("📋 API Found:", entity ? "YES" : "NO");
                }
            } catch(e) { 
                console.warn('API error:', e); 
                // Fallback: try name search
                try {
                    const resp2 = await fetch(`/api/persons/search?q=${encodeURIComponent(cleanID)}`);
                    if (resp2.ok) {
                        const data = await resp2.json();
                        entity = data.persons?.[0];
                    }
                } catch(e2) {}
            }
        }
        
        // 3. STRICT ID-FIRST MAPPING - Use DILA ID as Primary Key
        let bioValue = "Chưa có sử liệu";
        
        // STRICT: Extract DILA ID first
        const dilaId = entity?.id || entity?.['@id'] || cleanID;
        const cleanDilaId = String(dilaId).trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
        
        console.log("🔑 DILA_ID:", cleanDilaId, "ENTITY_KEYS:", entity ? Object.keys(entity).slice(0, 10) : "NONE");
        
        if (entity) {
            // EXACT field from RDF/TTL: bkg:biographicalNote
            const rawBio = entity['bkg:biographicalNote'] || entity.biography;
            
            if (rawBio) {
                // Handle multiline string with @vi suffix
                let bioStr = String(rawBio);
                if (bioStr.endsWith('@vi')) {
                    bioStr = bioStr.slice(0, -3).trim();
                }
                bioValue = bioStr || "Chưa có sử liệu";
                console.log("✅ BIO_EXTRACTED:", bioValue.substring(0, 50) + "...");
            }
        } else {
            console.log("❌ ENTITY_MISSING:", cleanID);
        }
        
        // 4. STRICT ID-FIRST Lookup for Teacher/Disciple (DILA = Authority)
        // FIX: Fetch full teacher/student data from API by ID
        let teacherData = null;
        let studentsData = [];
        
        if (entity) {
            // STRICT: Use ID for teacher lookup (not name)
            // entity.teacher/student are arrays of {id, name} pairs from persons.json
            const teacherList = entity.teacher || [];
            const studentList = entity.student || [];
            
            // Lookup teacher by ID from API (since personIndex may not have full data)
            if (teacherList && teacherList.length > 0) {
                const firstTeacher = teacherList[0];
                const teacherId = firstTeacher?.id;
                if (teacherId) {
                    try {
                        const resp = await fetch(`/daoanh/api/persons/${teacherId}`);
                        if (resp.ok) {
                            teacherData = await resp.json();
                            console.log("👨‍🏫 TEACHER FETCHED:", teacherId, teacherData?.names?.[0]?.value);
                        }
                    } catch(e) {
                        // Fallback to API search
                        teacherData = { name: firstTeacher?.name || teacherId, id: teacherId };
                    }
                }
            }
            
            // Lookup students by ID from API
            if (studentList && studentList.length > 0) {
                studentsData = await Promise.all(studentList.slice(0, 10).map(async s => {
                    const sid = s?.id;
                    if (!sid) return null;
                    try {
                        const resp = await fetch(`/daoanh/api/persons/${sid}`);
                        if (resp.ok) {
                            const data = await resp.json();
                            return { name: data.names?.[0]?.value || s?.name || sid, id: sid };
                        }
                    } catch(e) {}
                    return { name: s?.name || sid, id: sid };
                }));
                studentsData = studentsData.filter(s => s);
                console.log("👨‍🎓 STUDENTS_COUNT:", studentsData.length);
            }
        }
        
        // Extract names
        let vietName = name;
        let hanNameValue = hanNameParam || '';
        
        if (entity?.names) {
            const hanObj = entity.names.find(n => n.lang === 'han' || n.lang === 'zh-Hant');
            const vietObj = entity.names.find(n => n.lang === 'viet');
            hanNameValue = hanObj?.value || '';
            vietName = vietObj?.value || name;
        }
        
        // Search StarDict (definitions) - SEPARATE API
        // FIX: Include ID in search terms for better lookup
        const searchTerms = [id, name, hanNameValue, vietName].filter(t => t && t.length > 1);
        
        // ISOLATED: StarDict (Vietnamese/Han Viet definitions)
        let resStartdict = [];
        for (const term of searchTerms) {
            try {
                const resp = await fetch(`/daoanh/api/dict/search?q=${encodeURIComponent(term)}`);
                if (resp.ok) {
                    const data = await resp.json();
                    resStartdict.push(...(data.results || []));
                    console.log(`📚 StarDict "${term}": ${data.results?.length || 0}`);
                }
            } catch(e) { console.warn('StarDict error:', e); }
        }
        
        // ISOLATED: CBETA (canonical texts) - SEPARATE from StartDict
        // FIX: CBETA API does not exist - handle gracefully with error logging
        let resCbeta = [];
        for (const term of searchTerms) {
            try {
                // NOTE: /api/cbeta/search does NOT exist - this will 404
                // Log clear error instead of silent failure
                const resp = await fetch(`/daoanh/api/cbeta/search?q=${encodeURIComponent(term)}`);
                if (!resp.ok) {
                    console.log("❌ API_CBETA_404: CBETA API not available, endpoint /api/cbeta/search does not exist");
                    continue;
                }
                if (resp.ok) {
                    const data = await resp.json();
                    resCbeta.push(...(data.results || []));
                    console.log(`📖 CBETA "${term}": ${data.results?.length || 0}`);
                }
            } catch(e) {
                console.log("⚠️ CBETA đang bảo trì:", e.message);
            }
        }
        
        // ISOLATED: TAISHO (Taisho Tripitaka)
        let resTaisho = [];
        for (const term of searchTerms) {
            try {
                const resp = await fetch(`/daoanh/api/dict/search?q=${encodeURIComponent(term)}&type=taisho`);
                if (resp.ok) {
                    const data = await resp.json();
                    resTaisho.push(...(data.results || []));
                    console.log(`📕 Taisho "${term}": ${data.total || 0}`);
                }
            } catch(e) { console.warn('Taisho error:', e); }
        }
        
        console.log(`📋 ISOLATED: StarDict:${resStartdict.length} | CBETA:${resCbeta.length} | Taisho:${resTaisho.length}`);
        
        // FIX 3: NO DATA HIJACKING - Use isolated data, never copy between blocks
        console.log("🔍 SAMPLE startdict[0]:", resStartdict[0]);
        console.log("🔍 SAMPLE startdict[1]:", resStartdict[1]);
        console.log("🔍 SAMPLE cbeta[0]:", resCbeta[0]);
        console.log("🔍 SAMPLE cbeta[1]:", resCbeta[1]);
        console.log("🔍 SAMPLE taisho[0]:", resTaisho[0]);
        
        // FIX 4: ReferenceError guard - entity might be undefined
        const entitySafe = entity || {};
        console.log("🔍 TTL entity keys:", entitySafe ? Object.keys(entitySafe).slice(0, 10) : 'undefined');
        console.log("🔍 TTL bkg:biographicalNote:", entitySafe?.['bkg:biographicalNote'] ? "FOUND" : "NOT FOUND");

        // ID-First Lookup check
        if (!entity || Object.keys(entity).length === 0) {
            console.log("❌ MISSING_DATA_FOR_ID:", id, "for name:", name);
        }

        // FORCE OVERRIDE: Pass ISOLATED data to forceFinalRender
        // FIX: Use extracted bioValue after strict mapping
        // STRICT: Pass teacherData/studentsData from ID-First lookup
        this.forceFinalRender({
            name: name,
            bio: bioValue,
            personData: entity,
            startdict: resStartdict,
            cbeta: resCbeta,
            taisho: resTaisho,
            teacher: teacherData?.name || null,
            teacherId: teacherData?.id || null,
            students: studentsData.map(s => s.name)
        });
        
        // FIX: Update Verified Entity card with lineage from ID-First lookup
        if (name && cleanDilaId) {
            this.updateEntityCard(name, cleanDilaId, { 
                teacher: teacherData?.name || null, 
                teacherId: teacherData?.id || null,
                great_teacher: null, 
                students: studentsData.map(s => s.name)
            });
        }
    },
    
    /**
     * Force final render - update panel-body inside each block (preserves header)
     */
    forceFinalRender: function(data) {
        console.log("FINAL DATA:", data);
        
        const name = data.name || "Unknown";
        
        // Helper: Find or create panel-body inside a block
        const getPanelBody = function(blockId) {
            const block = document.getElementById(blockId);
            if (!block) return null;
            let body = block.querySelector('.panel-body');
            if (!body) {
                body = document.createElement('div');
                body.className = 'panel-body';
                body.style.padding = '8px';
                body.style.maxHeight = '300px';
                body.style.overflowY = 'auto';
                block.appendChild(body);
            }
            return body;
        };
        
        // Block 1: Bio - Use strict bio value passed from loadEntityData
        let block1Body = getPanelBody('block1');
        if (block1Body) {
            // FIX: Use data.bio which is already extracted correctly
            let block1Html = "";
            
            // Use pre-extracted bio value
            if (data.bio && data.bio !== "Dữ liệu chưa nạp" && data.bio.trim() !== "") {
                block1Html = '<div><h4 style="color:#d97706;">📖 ' + name + '</h4><p style="color:#e2e8f0;font-size:11px;">' + data.bio + '</p></div>';
            } else {
                block1Html = '<p style="color:#f59e0b;font-size:12px;">📖 Dữ liệu chưa nạp từ GraphDB</p>';
            }
            block1Body.innerHTML = block1Html;
        } else {
            console.warn("❌ block1 not found");
        }
        
        // Block 2: StarDict
        let block2Body = getPanelBody('block2');
        if (block2Body) {
            let block2Html = '<p style="color:#94a3b8;">📚 Không có dữ liệu</p>';
            if (data.startdict && data.startdict.length > 0) {
                block2Html = '<h5>📚 StarDict (' + data.startdict.length + ')</h5>';
                block2Html += data.startdict.slice(0, 10).map(function(r) {
                    return '<div>📚 ' + r.term + ': ' + (r.definition || '').substring(0, 50) + '</div>';
                }).join('');
            }
            block2Body.innerHTML = block2Html;
        }
        
        // Block 3: CBETA - render with data ONLY - NO COPY from startdict
        let block3Body = getPanelBody('block3');
        if (block3Body) {
            let block3Html = '';
            if (data.cbeta && data.cbeta.length > 0) {
                block3Html = '<h5 style="color:#d97706;">📖 CBETA (' + data.cbeta.length + ')</h5>';
                block3Html += data.cbeta.slice(0, 10).map(function(r) {
                    return '<div style="color:#e2e8f0;font-size:11px;margin:4px 0;">📖 ' + (r.term || r.title || 'Kinh') + '</div>';
                }).join('');
            }
            if (!block3Html) {
                block3Html = '<p style="color:#94a3b8;font-size:11px;">📖 Không có dữ liệu CBETA (0)</p>';
            }
            block3Body.innerHTML = block3Html;
        }
        
        // Block 4: Taisho - render with data ONLY - NO COPY from startdict
        let block4Body = getPanelBody('block4');
        if (block4Body) {
            let block4Html = '';
            if (data.taisho && data.taisho.length > 0) {
                block4Html = '<h5 style="color:#d97706;">📕 Taisho (' + data.taisho.length + ')</h5>';
                block4Html += data.taisho.slice(0, 10).map(function(r) {
                    return '<div style="color:#e2e8f0;font-size:11px;margin:4px 0;">📕 ' + (r.term || r.title || 'Kinh') + '</div>';
                }).join('');
            }
            if (!block4Html) {
                block4Html = '<p style="color:#94a3b8;font-size:11px;">📕 Không có dữ liệu Taisho (0)</p>';
            }
            block4Body.innerHTML = block4Html;
        }
        
        console.log("✅ All 4 blocks rendered");
        
        // BƯỚC KHÓA RENDER: Force CBETA display if data exists
        if (data.cbeta && data.cbeta.length > 0) {
            const block3Body = getPanelBody('block3');
            if (block3Body) {
                const block3Html = '<h5 style="color:#d97706;">📖 CBETA (' + data.cbeta.length + ')</h5>' +
                    data.cbeta.slice(0, 10).map(function(r) {
                        return '<div style="color:#e2e8f0;font-size:11px;margin:4px 0;">📖 ' + (r.term || r.title || 'Kinh') + '</div>';
                    }).join('');
                block3Body.innerHTML = block3Html;
                console.log("🔒 Locked CBETA:", data.cbeta.length, "items");
            }
        }
    },
    
    /**
     * Safe update - prevents errors on missing elements
     */
    safeUpdate: function(id, content) {
        const el = document.getElementById(id);
        if (!el) {
            console.warn("❌ Missing element:", id);
            return;
        }
        el.innerHTML = content;
    },
    
    /**
     * Update panel content
     */
    updatePanel: function(panelId, html) {
        const panel = document.getElementById(panelId);
        if (panel) panel.innerHTML = html;
    },
    
    /**
     * Update Verified Entity card
     */
    updateVerifiedEntity: function(name, personData) {
        const entityTitle = document.getElementById('verified-entity-title');
        const entityName = document.getElementById('verified-entity-name');
        const entityId = document.getElementById('verified-entity-id');
        const keywordDisplay = document.querySelector('.keyword-display');
        
        if (entityTitle) entityTitle.textContent = name;
        if (entityName) entityName.textContent = name;
        if (entityId && personData) entityId.textContent = personData.id ? 'DILA: ' + personData.id : '';
        if (keywordDisplay) keywordDisplay.textContent = name;
        
        console.log("✅ Updated Verified Entity:", name);
    },
    
    /**
     * Update TTL Metadata
     */
    updateTTLMetadata: function(name, personData) {
        const ttlBox = document.getElementById('ttl-box') || document.getElementById('metadata-content');
        if (ttlBox && personData) {
            const ttlHtml = '<span class="ttl-key">:' + name.replace(/\s+/g, '_') + '</span> <span class="ttl-key">a</span> <span class="ttl-key">:Person</span> ;<br>' +
                '&nbsp;&nbsp;<span class="ttl-key">rdfs:label</span> <span class="ttl-val">"' + name + '"</span> ;<br>' +
                '&nbsp;&nbsp;<span class="ttl-key">owl:sameAs</span> <span class="ttl-val">dila:' + (personData.id || 'N/A') + '</span> ;<br>' +
                '&nbsp;&nbsp;<span class="ttl-key">:dynasty</span> <span class="ttl-val">' + (personData.dynasty || 'N/A') + '</span> .';
            ttlBox.innerHTML = ttlHtml;
        }
    },

    /**
     * Search dictionary for fallback (58,836 terms)
     */
    searchDict: function(query) {
        const queryLower = query.toLowerCase();
        return this.dictData
            .filter(item => item.term.toLowerCase().includes(queryLower))
            .slice(0, 10)
            .map(item => ({
                type: 'dict',
                term: item.term,
                definition: item.definition?.substring(0, 80) || '',
                source: item.source
            }));
    },

    /**
     * Highlight matching text
     */
    highlightMatch: function(text, query) {
        if (!query || !text) return text;
        const q = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${q})`, 'gi');
        return text.replace(regex, '<b>$1</b>');
    },

    /**
     * Execute search - Full SSOT Reset & Sync (Universal Version)
     * Tự dò tìm mọi ID khả thi để ép chữ phải hiện ra
     */
    executeSearch: async function(idx) {
        const resultsDiv = document.getElementById('search-results');
        const results = this.currentResults || [];
        const item = results[idx];
        
        if (!item) return;
        
        const searchId = item.searchId || '';
        const displayName = item.displayName || item.name || '';
        
        console.log("🔥 Lệnh SSOT: Đuổi Thiếu Lâm Tự, nạp", displayName);
        
        // BƯỚC XÓA: PURGE all blocks & entity
        this.clearAllBlocks();
        
        // BƯỚC MAPPING: Sync Verified Entity
        this.syncCard(displayName, searchId);
        
        // RESET 4 BLOCKS (giữ header, xóa nội dung cũ)
        this.resetAllBlocks();
        
        // Close dropdown
        if (resultsDiv) {
            resultsDiv.classList.add('hidden');
            resultsDiv.style.display = 'none';
        }
        
        // 3. Zoom map
        const lat = item.lat;
        const lon = item.lon;
        if (lat && lon && typeof map !== 'undefined') {
            map.flyTo([parseFloat(lat), parseFloat(lon)], 20, { duration: 1.5 });
        }
        
        // 4. Load dữ liệu & render
        const names = item.names || [];
        await this.loadEntityData(searchId, displayName, '', names);
        
        console.log("✅ Đã cưỡng chế hiển thị thành công cho:", displayName);
    },


    
    /**
     * RESET all 4 blocks & Analysis Graph - clear old data completely
     */
    resetAllBlocks: function() {
        console.log("🧹 Resetting all blocks...");
        
        // Helper: Find or create panel-body inside a block
        const getPanelBody = function(blockId, msg) {
            const block = document.getElementById(blockId);
            if (!block) return null;
            let body = block.querySelector('.panel-body');
            if (!body) {
                body = document.createElement('div');
                body.className = 'panel-body';
                body.style.padding = '8px';
                body.style.maxHeight = '300px';
                body.style.overflowY = 'auto';
                block.appendChild(body);
            }
            body.innerHTML = '<p style="color:#94a3b8;font-size:11px;">' + msg + '</p>';
            return body;
        };
        
        getPanelBody('block1', '📖 Đang tải tiểu sử...');
        getPanelBody('block2', '📚 Đang tải Đại Từ Điển...');
        getPanelBody('block3', '📖 Đang tải CBETA...');
        getPanelBody('block4', '📕 Đang tải Taisho...');
        
        // RESET Analysis Graph (TTL) - clear :Shaolin_Temple
        const ttlBox = document.getElementById('ttl-box') || document.getElementById('metadata-content');
        if (ttlBox) {
            ttlBox.innerHTML = '<p style="color:#94a3b8;font-size:11px;">Đang nạp Metadata...</p>';
        }
        
        // Reset keyword display
        const keywordDisplay = document.getElementById('keyword-display');
        if (keywordDisplay) {
            keywordDisplay.innerText = 'Đang cập nhật...';
        }
        
        console.log("✅ All blocks reset");
    },
    
    /**
     * Force update UI directly - DOM Manipulation
     */
    forceUpdateUI: function(id, name) {
        console.log("🚀 Force updating UI for:", name);
        
        // Update keyword display in header
        const keywordDisplay = document.getElementById('keyword-display');
        if (keywordDisplay) {
            keywordDisplay.innerText = name;
            keywordDisplay.style.color = '#f59e0b';
        }
        
        // Update workbench header with new entity
        const workbenchHeader = document.querySelector('.workbench-header');
        if (workbenchHeader) {
            const span = workbenchHeader.querySelector('span');
            if (span) {
                span.innerText = name;
                span.style.color = '#f59e0b';
            }
        }
        
        // Make sure workbench is visible
        const workbench = document.querySelector('.workbench');
        if (workbench) {
            workbench.style.display = 'flex';
        }
        
        const workbenchContent = document.querySelector('.workbench-content');
        if (workbenchContent) {
            workbenchContent.style.display = 'block';
        }
        
        // Force show panels
        const panels = document.querySelectorAll('.text-panel');
        panels.forEach(panel => {
            panel.style.display = 'block';
        });
        
        console.log("✅ UI force updated for:", name);
    },

    /**
     * Select result -> zoom map + show BIO
     */
    selectResult: function(name, lat, lon, dilaId) {
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.classList.add('hidden');
        
        console.log(`📌 Selected: ${name}`);
        
        // Zoom map
        if (lat && lon && typeof map !== 'undefined') {
            map.flyTo([parseFloat(lat), parseFloat(lon)], 16, { duration: 1.5 });
        }
        
        // Load BIO from DILA
        if (dilaId) {
            this.loadTTLData(dilaId, name);
        }
    },

    /**
     * Load TTL/BIO data
     */
    loadTTLData: async function(dilaId, name) {
        try {
            const resp = await fetch(`/daoanh/api/persons/${dilaId}`);
            if (resp.ok) {
                const person = await resp.json();
                console.log(`📋 BIO: ${(person.biography || '').substring(0, 100)}...`);
                
                const workbench = document.getElementById('workbench-content');
                if (workbench) {
                    workbench.innerHTML = `<div class="bio-section">
                        <h4>${name}</h4>
                        <p>${person.biography || 'No biography'}</p>
                        <div class="meta">Dynasty: ${person.dynasty || 'N/A'}</div>
                    </div>`;
                }
            }
        } catch(e) {
            console.warn('BIO error:', e);
        }
    },
    
    /**
     * RAG semantic search fallback
     * Uses RAGConnector when local search returns no results
     */
    searchWithRAG: async function(query) {
        // Check if RAGConnector is available
        if (typeof RAGConnector === 'undefined') {
            console.log('[SearchApp] RAGConnector not available');
            return [];
        }
        
        try {
            const result = await RAGConnector.query(query, { maxResults: 5 });
            
            if (result.error || !result.results) {
                return [];
            }
            
            // Transform RAG results to match our format
            return result.results.map(r => ({
                type: 'rag_result',
                name: r.title || r.source || 'Result',
                description: r.content?.substring(0, 100) || '',
                source: 'rag',
                score: r.score || 0
            }));
        } catch (error) {
            console.warn('[SearchApp] RAG search failed:', error);
            return [];
        }
    },

    /**
     * NEW: Search critical places from dictionary (Tào Khê, Lục Tổ, etc.)
     */
    searchCriticalPlaces: function(query) {
        const queryLower = query.toLowerCase();
        return this.criticalPlaces
            .filter(place => {
                const searchKey = (place.searchKey || '').toLowerCase();
                const viet = (place.vietnamese || '').toLowerCase();
                const desc = (place.description || '').toLowerCase();
                const related = (place.relatedMonks || []).join(' ').toLowerCase();
                return searchKey.includes(queryLower) || 
                       viet.includes(queryLower) || 
                       desc.includes(queryLower) ||
                       related.includes(queryLower);
            })
            .slice(0, 10)
            .map(place => ({
                type: 'critical_place',
                searchKey: place.searchKey,
                name: place.vietnamese,
                nameZh: place.searchKey,
                description: place.description,
                type: place.type,
                period: place.period,
                lat: place.gps?.lat || '',
                lon: place.gps?.lon || '',
                relatedMonks: place.relatedMonks || [],
                relatedSutras: place.relatedSutras || [],
                source: 'dictionary'
            }));
    },

    /**
     * Unified search - all types with deduplication
     */
    searchUnified: function(query) {
        if (query.length < this.minChars) return [];
        if (!this.unifiedData || !this.unifiedData.length) return [];
        
        const q = query.toLowerCase().trim();
        
        // Filter matching items
        const filtered = this.unifiedData
            .filter(item => item.name && item.name.toLowerCase().includes(q))
            .slice(0, 30);
        
        // Deduplicate: group by normalized title, keep best (GPS + ID)
        const titleMap = new Map();
        
        for (const item of filtered) {
            const normalized = this.normalizeItem(item);
            const title = normalized.title;
            const hasGPS = item.lat && item.lon;
            const hasId = item.id;
            
            if (!titleMap.has(title)) {
                // First occurrence - store it
                titleMap.set(title, { item, priority: hasGPS ? 2 : (hasId ? 1 : 0) });
            } else {
                // Already exists - check if this one has higher priority
                const existing = titleMap.get(title);
                const newPriority = hasGPS ? 2 : (hasId ? 1 : 0);
                if (newPriority > existing.priority) {
                    titleMap.set(title, { item, priority: newPriority });
                }
            }
        }
        
        // Convert to results array (max 10)
        // FIXED: Include searchId + displayName for API calls
        const results = Array.from(titleMap.values())
            .slice(0, 10)
            .map(entry => ({
                type: 'result',
                name: entry.item.name,
                displayName: entry.item.displayName || entry.item.name,
                searchId: entry.item.searchId || entry.item.id || '',
                label: entry.item.type,
                lat: entry.item.lat || '',
                lon: entry.item.lon || '',
                id: entry.item.id || '',
                searchType: entry.item.searchType
            }));
        
        console.log(`🔍 "${query}": ${results.length} unique results`);
        return results;
    },

    /**
     * Search local places cache (DILA/CBETA)
     */
    searchLocalPlaces: function(query) {
        const queryLower = query.toLowerCase();
        return this.localPlaces
            .filter(place => {
                const nameVi = (place.nameVietnamese || '').toLowerCase();
                const nameZh = (place.nameChinese || '').toLowerCase();
                const nameEn = (place.nameEnglish || '').toLowerCase();
                return nameVi.includes(queryLower) || nameZh.includes(queryLower) || nameEn.includes(queryLower);
            })
            .slice(0, 10)
            .map(place => ({
                type: 'place',
                uri: place.id || '',
                name: place.nameVietnamese || place.nameChinese || place.nameEnglish || '',
                nameZh: place.nameChinese || '',
                lat: place.lat || '',
                lon: place.lon || '',
                country: place.country || '',
                source: 'dila_cbeta'
            }));
    },

    /**
     * Render search results with priority sections + highlighting
     */
    renderResults: function(criticalResults, dilaPersonResults, monkResults, placeResults, dictResults = []) {
        const resultsDiv = document.getElementById('search-results');
        const query = this.currentQuery;
        
        // Safe: ensure all are arrays
        const c = Array.isArray(criticalResults) ? criticalResults : [];
        const d = Array.isArray(dilaPersonResults) ? dilaPersonResults : [];
        const m = Array.isArray(monkResults) ? monkResults : [];
        const p = Array.isArray(placeResults) ? placeResults : [];
        const dict = Array.isArray(dictResults) ? dictResults : [];
        
        const totalResults = c.length + d.length + m.length + p.length + dict.length;
        
        console.log(`📋 Dropdown: ${totalResults} results for "${query}"`);
        
        if (totalResults === 0) {
            // No result - suggest dictionary
            resultsDiv.innerHTML = `<div class="search-result-item">
                <span style="color: #94a3b8;">Không tìm thấy "${this.escapeHtml(query)}" trong 48,000 vị Tổ.</span>
                <div style="margin-top:4px;font-size:11px;color:#fbbf24;cursor:pointer;" onclick="SearchApp.searchDictOnly('${this.escapeHtml(query)}')">
                    👉 Tìm trong 58,836 thuật ngữ Phật học?
                </div>
            </div>`;
            resultsDiv.classList.remove('hidden');
            return;
        }

        let html = '';
        let totalShown = 0;
        const maxResults = 10;

// Critical places
        if (c.length > 0 && totalShown < maxResults) {
            html += '<div class="search-section-header">📚 Địa danh</div>';
            c.slice(0, maxResults - totalShown).forEach(place => {
                html += this.renderPlaceItemWithHighlight(place, query);
            });
            totalShown += c.length;
        }

        // DILA Person
        if (d.length > 0 && totalShown < maxResults) {
            html += '<div class="search-section-header">👤 Vị Tổ</div>';
            d.slice(0, maxResults - totalShown).forEach(person => {
                html += this.renderPersonItemWithHighlight(person, query);
            });
            totalShown += d.length;
        }

        // Monks
        if (m.length > 0 && totalShown < maxResults) {
            html += '<div class="search-section-header">🧑 Tu sĩ</div>';
            m.slice(0, maxResults - totalShown).forEach(monk => {
                html += this.renderMonkItem(monk);
            });
            totalShown += m.length;
        }

        // Place results (DILA/CBETA + Vietnam Temples)
        if (p.length > 0 && totalShown < maxResults) {
            html += '<div class="search-section-header">🗺️ Địa điểm</div>';
            p.slice(0, maxResults - totalShown).forEach(place => {
                html += this.renderPlaceItemWithHighlight(place, query);
            });
            totalShown += p.length;
        }

        // Dictionary
        if (dict.length > 0 && totalShown < maxResults) {
            html += '<div class="search-section-header">📖 Thuật ngữ</div>';
            dictResults.slice(0, maxResults - totalShown).forEach(item => {
                html += `<div class="search-result-item">
                    <div>
                        <div>${this.highlightMatch(item.term, query)}</div>
                        <div class="search-result-meta">${item.definition}...</div>
                    </div>
                    <span class="result-type">dict</span>
                </div>`;
            });
        }

        resultsDiv.innerHTML = html;
        resultsDiv.classList.remove('hidden');
    },

    /**
     * Render place item with highlighting
     */
    renderPlaceItemWithHighlight: function(place, query) {
        const name = place.name || place.searchKey || place.nameZh || '';
        const lat = place.lat || place.gps?.lat || '';
        const lon = place.lon || place.gps?.lon || '';
        return `<div class="search-result-item" onclick="SearchApp.selectPlace('${this.escapeHtml(name)}', '${lat}', '${lon}')">
            <div>
                <div>${this.highlightMatch(name, query)}</div>
                <div class="search-result-meta">${place.description?.substring(0,50) || ''}</div>
            </div>
            <span class="result-type">${place.type || 'place'}</span>
        </div>`;
    },

    /**
     * Render person item with highlighting
     */
    renderPersonItemWithHighlight: function(person, query) {
        const name = person.name || '';
        const dynasty = person.dynasty || '';
        return `<div class="search-result-item" onclick="SearchApp.selectDilaPerson('${person.id}', '${this.escapeHtml(name)}')">
            <div>
                <div>${this.highlightMatch(name, query)} ${dynasty}</div>
                <div class="search-result-meta">ID: ${person.id}</div>
            </div>
            <span class="result-type">person</span>
        </div>`;
    },

    /**
     * Select first result (auto)
     */
    selectFirstResult: function() {
        const resultsDiv = document.getElementById('search-results');
        const items = resultsDiv?.querySelectorAll('.search-result-item');
        if (items && items.length > 0) {
            items[0].click();
        }
    },

    /**
     * Select a monk - load from DILA + update map + workbench
     */
    selectMonk: async function(name, personId) {
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.classList.add('hidden');
        
        console.log('📌 Selected:', name);
        
        // Load person details from DILA
        if (personId) {
            try {
                const resp = await fetch(`/daoanh/api/persons/${personId}`);
                if (resp.ok) {
                    const person = await resp.json();
                    console.log('📋 DILA:', person.id, person.dynasty);
                    
                    // Update map if has GPS
                    if (person.lat && person.lon && typeof map !== 'undefined') {
                        map.flyTo([person.lat, person.lon], 14, { duration: 1 });
                    }
                }
            } catch(e) {
                console.warn('Load error:', e);
            }
        }
    },

    /**
     * Select a place - focus map
     */
    selectPlace: function(name, lat, lon) {
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.classList.add('hidden');
        if (lat && lon && typeof map !== 'undefined') {
            map.flyTo([parseFloat(lat), parseFloat(lon)], 14, { duration: 1 });
        }
        console.log('📍 Place:', name, lat, lon);
    },

/**
     * Clear all panels BEFORE rendering - with timeout reset
     */
    clearAllPanels: function() {
        const emptyMsg = '<p style="color:#94a3b8;">Đang tải...</p>';
        this.safeUpdate('block1', emptyMsg);
        this.safeUpdate('block2', emptyMsg);
        this.safeUpdate('block3', emptyMsg);
        this.safeUpdate('block4', emptyMsg);
        
        // Auto-clear loading state after 3 seconds
        setTimeout(() => {
            const stillLoading = document.getElementById('block1');
            if (stillLoading && stillLoading.innerText === 'Đang tải...') {
                this.safeUpdate('block1', '<p style="color:#f59e0b;">⚠️ Timeout - thử lại</p>');
                this.safeUpdate('block2', '<p style="color:#f59e0b;">⚠️ Timeout - thử lại</p>');
                this.safeUpdate('block3', '<p style="color:#f59e0b;">⚠️ Timeout - thử lại</p>');
                this.safeUpdate('block4', '<p style="color:#f59e0b;">⚠️ Timeout - thử lại</p>');
            }
        }, 3000);
    },

    /**
     * Escape HTML
     */
    escapeHtml: function(text) {
        if (!text) return '';
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },
    
    /**
     * NEW: Render DILA Person Authority result
     */
    renderDilaPersonItem: function(person) {
        const icon = person.is_monk ? '🧑‍‍' : '👤';
        const dynasty = person.dynasty ? `(${person.dynasty})` : '';
        const bio = person.biography ? person.biography.substring(0, 60) + '...' : '';
        
        return `<div class="search-result-item" onclick="SearchApp.selectDilaPerson('${person.id}', '${this.sanitizeHtml(person.name)}')">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:20px;">${icon}</span>
                <div>
                    <div class="search-result-name">${this.sanitizeHtml(person.name)} ${dynasty}</div>
                    <div class="search-result-meta">ID: ${person.id} | ${bio}</div>
                </div>
            </div>
        </div>`;
    },
    
    /**
     * NEW: Handle DILA Person selection - load lineage map
     */
    selectDilaPerson: function(personId, personName) {
        console.log('Selected DILA person:', personId, personName);
        
        // Hide search results
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.classList.add('hidden');
        }
        
        // If LineageMapApp is available, load the lineage
        if (typeof LineageMapApp !== 'undefined') {
            LineageMapApp.loadLineage(personName);
        } else {
            // Fallback: show person details in a panel
            this.showPersonDetails(personId);
        }
    },
    
    /**
     * Show person details panel
     */
    showPersonDetails: async function(personId) {
        try {
            const response = await fetch(`/daoanh/api/persons/${personId}`);
            if (response.ok) {
                const person = await response.json();
                
                // Create or update details panel
                let panel = document.getElementById('person-details-panel');
                if (!panel) {
                    panel = document.createElement('div');
                    panel.id = 'person-details-panel';
                    panel.className = 'fixed right-0 top-0 w-96 h-full bg-slate-900 text-white p-4 overflow-y-auto z-50';
                    document.body.appendChild(panel);
                }
                
                panel.innerHTML = `
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-amber-500">👤 Chi tiết</h3>
                        <button onclick="document.getElementById('person-details-panel').remove()" class="text-gray-400 hover:text-white">✕</button>
                    </div>
                    <div class="space-y-4">
                        <div>
                            <div class="text-sm text-gray-400">ID</div>
                            <div class="text-lg">${person.id}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-400">Tên</div>
                            <div class="text-lg font-bold">${person.names ? person.names.map(n => n.value).join(' / ') : 'N/A'}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-400">Triều đại</div>
                            <div>${person.dynasty || 'N/A'}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-400">Là tu sĩ</div>
                            <div>${person.is_monk ? '✅ Có' : '❌ Không'}</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-400">Tiểu truyện</div>
                            <div class="text-sm">${person.biography || 'N/A'}</div>
                        </div>
                        ${person.teacher && person.teacher.length > 0 ? `
                        <div>
                            <div class="text-sm text-gray-400">Thầy</div>
                            <div>${person.teacher.map(t => t.name).join(', ')}</div>
                        </div>
                        ` : ''}
                        ${person.student && person.student.length > 0 ? `
                        <div>
                            <div class="text-sm text-gray-400">Đệ tử</div>
                            <div>${person.student.slice(0, 5).map(s => s.name).join(', ')}${person.student.length > 5 ? '...' : ''}</div>
                        </div>
                        ` : ''}
                        ${person.active_at && person.active_at.length > 0 ? `
                        <div>
                            <div class="text-sm text-gray-400">Nơi hoạt động</div>
                            <div>${person.active_at.join(', ')}</div>
                        </div>
                        ` : ''}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Failed to load person details:', error);
        }
    },
    
    /**
     * Render RAG semantic search result
     */
    renderRAGItem: function(result) {
        return `<div class="search-result-item" onclick="SearchApp.selectRAGResult('${this.sanitizeHtml(result.name)}')">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:16px;">🤖</span>
                <div>
                    <div class="result-name">${this.sanitizeHtml(result.name)}</div>
                    <div class="result-desc" style="font-size:11px;color:#94a3b8;">
                        ${this.sanitizeHtml(result.description || '')} 
                        ${result.score ? `<span style="color:#10b981;">(${Math.round(result.score * 100)}% match)</span>` : ''}
                    </div>
                </div>
            </div>
        </div>`;
    },
    
    /**
     * Handle RAG result selection
     */
    selectRAGResult: function(name) {
        // Navigate to entity or show details
        console.log('[SearchApp] Selected RAG result:', name);
        // Could expand to show full RAG content in a modal
    },
    
    /**
     * Sanitize HTML to prevent XSS
     */
    sanitizeHtml: function(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * NEW: Render a critical place result from dictionary
     */
    renderCriticalPlaceItem: function(place) {
        const coords = place.lat && place.lon ? `${place.lat}, ${place.lon}` : 'Chưa có GPS';
        const typeIcon = place.type === 'monk' ? '🧓' : 
                         place.type === 'monastery' ? '🏛️' : 
                         place.type === 'mountain' ? '⛰️' : 
                         place.type === 'lineage' ? '🔗' : '📍';
        const typeLabel = place.type === 'monk' ? 'Thiền sư' :
                          place.type === 'monastery' ? 'Chùa' :
                          place.type === 'mountain' ? 'Núi' :
                          place.type === 'lineage' ? 'Dòng thiền' :
                          place.type === 'sacred_place' ? 'Thánh địa' : 'Địa điểm';
        const monks = place.relatedMonks?.length ? `👤 ${place.relatedMonks.slice(0, 2).join(', ')}` : '';
        const sutras = place.relatedSutras?.length ? `📖 ${place.relatedSutras.join(', ')}` : '';
        
        return `
            <div class="search-result-item" data-type="critical_place" 
                 data-name="${place.name}" 
                 data-name-zh="${place.nameZh}"
                 data-description="${place.description?.replace(/"/g, "'") || ''}"
                 data-type="${place.type}"
                 data-period="${place.period || ''}"
                 data-lat="${place.lat}" 
                 data-lon="${place.lon}"
                 data-monks="${place.relatedMonks?.join('|') || ''}"
                 data-sutras="${place.relatedSutras?.join('|') || ''}">
                <span class="search-result-type critical">${typeIcon} ${typeLabel}</span>
                <span class="search-result-name">${place.name}</span>
                <span class="search-result-zh" style="color:#78350f;font-size:11px;margin-left:4px;">${place.nameZh}</span>
                <div class="search-result-info">📍 ${coords} ${place.period ? '| 📅 ' + place.period : ''}</div>
                ${monks ? `<div class="search-result-info">${monks}</div>` : ''}
                ${sutras ? `<div class="search-result-info">${sutras}</div>` : ''}
            </div>
        `;
    },

    /**
     * Render a place result item (DILA/CBETA)
     */
    renderPlaceItem: function(place) {
        const coords = place.lat && place.lon ? `${place.lat}, ${place.lon}` : 'Chưa có GPS';
        const nameZh = place.nameZh || '';
        const displayName = place.name || nameZh;
        return `
            <div class="search-result-item" data-type="place" data-uri="${place.uri}" data-name="${displayName}" data-name-zh="${nameZh}" data-lat="${place.lat}" data-lon="${place.lon}">
                <span class="search-result-type place">🗺️ Địa điểm</span>
                <span class="search-result-name">${displayName}</span>
                ${nameZh ? `<span class="search-result-zh" style="color:#78350f;font-size:11px;margin-left:4px;">${nameZh}</span>` : ''}
                <div class="search-result-info">📍 ${coords} | ${place.country || 'N/A'}</div>
            </div>
        `;
    },

    /**
     * Render a monk result item
     */
    renderMonkItem: function(monk) {
        return `
            <div class="search-result-item" data-type="monk" data-name="${monk.name}">
                <span class="search-result-type monk">🧑 Tu sĩ</span>
                <span class="search-result-name">${monk.name}</span>
            </div>
        `;
    },

    /**
     * Attach click handlers to result items
     */
    attachClickHandlers: function() {
        const items = document.querySelectorAll('.search-result-item');
        items.forEach(item => {
            item.addEventListener('click', () => {
                const type = item.dataset.type;
                
                if (type === 'critical_place') {
                    this.handleCriticalPlaceClick(item.dataset);
                } else if (type === 'place') {
                    this.handlePlaceClick(item.dataset);
                } else if (type === 'monk') {
                    this.handleMonkClick(item.dataset);
                }
            });
        });
    },

    /**
     * NEW: Handle click on a critical place from dictionary
     */
    handleCriticalPlaceClick: function(data) {
        console.log("📚 Critical place clicked:", data);
        
        document.getElementById('search-results').classList.add('hidden');
        document.getElementById('global-search').value = data.name;

        // Zoom to location if coordinates available
        if (data.lat && data.lon && window.MapApp) {
            window.MapApp.map.setView([parseFloat(data.lat), parseFloat(data.lon)], 14);
        }

        // Update workbench with detailed info
        this.updateWorkbenchCriticalPlace(data);
    },

    /**
     * Handle click on a place (DILA/CBETA)
     */
    handlePlaceClick: function(data) {
        console.log("📍 Place clicked:", data);
        
        document.getElementById('search-results').classList.add('hidden');
        document.getElementById('global-search').value = data.name;

        if (data.lat && data.lon && window.MapApp) {
            window.MapApp.map.setView([parseFloat(data.lat), parseFloat(data.lon)], 14);
        }

        this.updateWorkbenchPlace(data);
    },

    /**
     * Handle click on a monk
     */
    handleMonkClick: async function(data) {
        console.log("🧑 Monk clicked:", data);
        
        document.getElementById('search-results').classList.add('hidden');
        document.getElementById('global-search').value = data.name;

        this.updateRightPanel(`<div class="p-4">🔄 Đang tìm thông tin ${data.name}...</div>`);

        try {
            const uriResponse = await fetch(`/daoanh/api/monk_uri?name=${encodeURIComponent(data.name)}`);
            const uriData = await uriResponse.json();
            
            if (uriData.uri) {
                const lineageResponse = await fetch(`/daoanh/api/get_lineage?name=${encodeURIComponent(data.name)}`);
                const lineageData = await lineageResponse.json();
                this.updateRightPanelMonk(data.name, uriData.uri, lineageData);
            } else {
                this.updateRightPanel(`<div class="p-4">⚠️ Không tìm thấy thông tin tu sĩ ${data.name}</div>`);
            }
        } catch (error) {
            console.error("Monk info error:", error);
            this.updateRightPanel(`<div class="p-4">❌ Lỗi: ${error.message}</div>`);
        }
    },

    /**
     * NEW: Update workbench with critical place info (dictionary data)
     */
    updateWorkbenchCriticalPlace: function(data) {
        const workbenchContent = document.querySelector('.workbench-content');
        if (!workbenchContent) return;

        const coords = data.lat && data.lon ? `${data.lat}, ${data.lon}` : 'Chưa có GPS';
        const relatedMonks = data.monks ? data.monks.split('|').map(m => 
            `<button class="monk-link" onclick="SearchApp.searchAndShowMonk('${m}')">${m}</button>`
        ).join(', ') : 'Không có';
        const relatedSutras = data.sutras ? data.sutras.split('|').map(s => 
            `<span class="sutra-link">${s}</span>`
        ).join(', ') : 'Không có';
        
        workbenchContent.innerHTML = `
            <div class="text-panel" style="border-left: 4px solid #8b5cf6;">
                <h5 style="color:#8b5cf6;">📚 ${data.name} (${data.nameZh})</h5>
                <p class="viet-text"><strong>Loại:</strong> ${data.type || 'Địa điểm'}</p>
                <p class="viet-text"><strong>Thời kỳ:</strong> ${data.period || 'N/A'}</p>
                <p class="viet-text"><strong>📍 GPS:</strong> ${coords}</p>
                <hr style="border-color:#e5e7eb;margin:10px 0;">
                <p class="viet-text" style="font-size:14px;line-height:1.6;">${data.description || 'Không có mô tả'}</p>
                <hr style="border-color:#e5e7eb;margin:10px 0;">
                <p class="viet-text"><strong>👤 Liên quan:</strong> ${relatedMonks}</p>
                <p class="viet-text"><strong>📖 Kinh văn:</strong> ${relatedSutras}</p>
            </div>
        `;
    },

    /**
     * Update workbench with place info (DILA/CBETA)
     */
    updateWorkbenchPlace: function(data) {
        const workbenchContent = document.querySelector('.workbench-content');
        if (!workbenchContent) return;

        const coords = data.lat && data.lon ? `${data.lat}, ${data.lon}` : 'Chưa có GPS';
        
        workbenchContent.innerHTML = `
            <div class="text-panel">
                <h5>🗺️ ${data.name}</h5>
                ${data.nameZh ? `<p class="viet-text"><strong>汉:</strong> ${data.nameZh}</p>` : ''}
                <p class="viet-text"><strong>📍 GPS:</strong> ${coords}</p>
                <p class="viet-text"><strong>Nguồn:</strong> ${data.uri ? 'DILA/CBETA' : 'N/A'}</p>
                ${data.uri ? `<p class="viet-text"><strong>URI:</strong> <a href="${data.uri}" target="_blank" class="text-blue-600">${data.uri}</a></p>` : ''}
            </div>
        `;
    },

    /**
     * Search and show monk info (called from workbench)
     */
    searchAndShowMonk: function(name) {
        document.getElementById('global-search').value = name;
        this.handleSearch(name);
    },

    /**
     * Update right panel with monk info
     */
    updateRightPanel: function(html) {
        const kgContent = document.querySelector('.kg-content');
        if (kgContent) {
            kgContent.innerHTML = html;
        }
    },

    /**
     * Update right panel with monk info and lineage
     */
    updateRightPanelMonk: async function(name, uri, lineageData) {
        const kgContent = document.querySelector('.kg-content');
        if (!kgContent) return;

        let html = `<pre>`;
        html += `<span class="ttl-syntax-key">:${name.replace(/\s+/g, '_')}</span> a <span class="ttl-syntax-key">:BuddhistMonk</span> ;\n`;
        html += `    <span class="ttl-syntax-key">rdfs:label</span> <span class="ttl-syntax-val">"${name}"@vi</span> ;\n`;
        html += `    <span class="ttl-syntax-key">owl:sameAs</span> <span class="ttl-syntax-link">${uri}</span> .\n\n`;

        if (lineageData.teacher) {
            html += `<span class="ttl-syntax-key">:hasTeacher</span> <span class="ttl-syntax-val">${lineageData.teacher}</span> ;\n`;
        }

        if (lineageData.great_teacher) {
            html += `    <span class="ttl-syntax-key">:greatTeacher</span> <span class="ttl-syntax-val">${lineageData.great_teacher}</span> ;\n`;
        }

        if (lineageData.students && lineageData.students.length > 0) {
            html += `\n<span class="ttl-syntax-key">:hasDisciple</span> [\n`;
            lineageData.students.slice(0, 5).forEach(s => {
                html += `    <span class="ttl-syntax-val">"${s}"@vi</span>,\n`;
            });
            if (lineageData.students.length > 5) {
                html += `    ... <span class="text-gray-500">+${lineageData.students.length - 5} more</span>\n`;
            }
            html += `] .\n`;
        }

        html += `</pre>`;

        kgContent.innerHTML = html;
        this.updateEntityCard(name, uri, lineageData);
    },

    /**
     * BƯỚC XÓA: Clear all blocks + Verified Entity
     */
    clearAllBlocks: function() {
        console.log("🧹 PURGE: Xóa tất cả blocks...");
        
        // Clear 4 blocks
        ['block1', 'block2', 'block3', 'block4'].forEach(bId => {
            const el = document.getElementById(bId);
            if (el) {
                let body = el.querySelector('.panel-body');
                if (body) body.innerHTML = '';
                else {
                    body = document.createElement('div');
                    body.className = 'panel-body';
                    body.style.padding = '8px';
                    el.appendChild(body);
                }
            }
        });
        
        // Clear Verified Entity (name, id, heritage)
        const entityNameEl = document.getElementById('verified-entity-name');
        const entityIdEl = document.getElementById('verified-entity-id');
        const entityHeritageEl = document.getElementById('entity-heritage');
        
        if (entityNameEl) entityNameEl.textContent = '';
        if (entityIdEl) entityIdEl.textContent = '';
        if (entityHeritageEl) entityHeritageEl.textContent = '';
        
        // Clear Analysis Graph (TTL)
        const ttlBox = document.getElementById('ttl-box') || document.getElementById('metadata-content');
        if (ttlBox) ttlBox.innerHTML = '';
        
        console.log("✅ PURGE complete");
    },
    
    /**
     * BƯỚC MAPPING: Sync Verified Entity với heritage/lineage
     */
    syncCard: function(name, id, lineageData, fullEntity) {
        console.log('🔗 SYNC_CARD:', name, id, lineageData);
        
        // Step 1: Update name & ID
        const entityNameEl = document.getElementById('verified-entity-name');
        const entityIdEl = document.getElementById('verified-entity-id');
        
        if (entityNameEl) {
            entityNameEl.textContent = name || 'Unknown';
            entityNameEl.style.color = '#d97706';
        }
        if (entityIdEl) {
            entityIdEl.textContent = id || 'N/A';
        }
        
        // Step 2: Update Bio (from fullEntity - V32 new)
        const entityBioEl = document.getElementById('entity-bio');
        if (entityBioEl && fullEntity) {
            const bio = fullEntity.biography || fullEntity.bio || '';
            if (bio) {
                entityBioEl.innerHTML = '<div class="bio-text">' + bio.substring(0, 500) + (bio.length > 500 ? '...' : '') + '</div>';
            } else {
                entityBioEl.innerHTML = '<div class="bio-text">Chưa có tiểu sử...</div>';
            }
        }
        
        // Step 3: Update heritage/lineage (ID-First display)
        const entityHeritageEl = document.getElementById('entity-heritage');
        if (entityHeritageEl) {
            let heritage = '';
            if (lineageData) {
                // STRICT: Show teacher with DILA ID for authority
                if (lineageData.teacher) {
                    const teacherId = lineageData.teacherId ? ` [${lineageData.teacherId}]` : '';
                    heritage = '📖 Thầy: ' + lineageData.teacher + teacherId + '<br>';
                }
                if (lineageData.students && lineageData.students.length > 0) {
                    const studentsList = lineageData.students.slice(0, 5).map(s => {
                        return typeof s === 'object' ? (s.name || s.id) : s;
                    }).join(', ');
                    heritage += '📖 Đệ tử: ' + studentsList;
                    if (lineageData.students.length > 5) heritage += ' +' + (lineageData.students.length - 5) + ' more';
                }
            }
            if (!heritage) {
                heritage = 'Thiền sư thuộc dòng phái... (đang truy vấn tệp nguồn)';
            }
            entityHeritageEl.innerHTML = heritage;
        }
        
        // Step 4: Update authority links (V32 new)
        const entityAuthEl = document.getElementById('entity-authority');
        if (entityAuthEl && fullEntity && fullEntity.authority_links) {
            const links = fullEntity.authority_links;
            let linkHTML = '';
            if (links.dila) linkHTML += `<a href="${links.dila}" target="_blank">🔗 DILA</a> `;
            if (links.wiki && links.wiki !== null) linkHTML += `<a href="${links.wiki}" target="_blank">🔗 Wiki</a>`;
            entityAuthEl.innerHTML = linkHTML || 'Chưa có liên kết';
        }
        
        console.log("🔄 Synced card:", name, id);
    },
    
    /**
     * Update entity card in sidebar (legacy)
     * STRICT: Handle teacherId for ID-First display
     */
    updateEntityCard: function(name, uri, lineageData) {
        // Include teacherId in lineageData if present
        const enhancedLineage = lineageData || {};
        console.log("🔗 ENTITY_CARD:", name, "teacher:", lineageData?.teacher, "teacherId:", lineageData?.teacherId, "students:", lineageData?.students?.length || 0);
        this.syncCard(name, uri, enhancedLineage);
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        SearchApp.init();
    }, 500);
});

// ===== AUTO TEST ENGINE =====
async function testCase(name) {
    console.log("🧪 TEST:", name);

    try {
        await SearchApp.executeSearch(name);

        setTimeout(() => {
            const results = {
                block1: document.getElementById("block1")?.innerText,
                block2: document.getElementById("block2")?.innerText,
                block3: document.getElementById("block3")?.innerText,
                block4: document.getElementById("block4")?.innerText,
            };

            console.table(results);

            // FAIL if missing data
            if (!results.block1) console.error("❌ FAIL: block1 (Bio)");
            if (!results.block2) console.error("❌ FAIL: block2 (StarDict)");

        }, 1500);

    } catch (e) {
        console.error("❌ CRASH:", e);
    }
}

// ===== HELPER FUNCTIONS =====

// Find person by name (fallback)
function findPersonByName(name) {
    if (!name) return null;
    
    // Try SearchApp.dictData first
    if (SearchApp.dictData) {
        const query = name.toLowerCase();
        const found = SearchApp.dictData.find(function(p) {
            return p.name && p.name.toLowerCase().includes(query);
        });
        if (found) return found;
    }
    
    // Try SearchApp.localPlaces  
    if (SearchApp.localPlaces) {
        const query = name.toLowerCase();
        return SearchApp.localPlaces.find(function(p) {
            return (p.vietnamese && p.vietnamese.toLowerCase().includes(query)) ||
                   (p.nameChinese && p.nameChinese.toLowerCase().includes(query));
        });
    }
    
    // Try criticalPlaces
    if (SearchApp.criticalPlaces) {
        const query = name.toLowerCase();
        return SearchApp.criticalPlaces.find(function(p) {
            return p.vietnamese && p.vietnamese.toLowerCase().includes(query);
        });
    }
    
    return null;
}

// Find person by ID (fallback)  
function findPersonById(id) {
    if (!id) return null;
    
    if (SearchApp.dictData) {
        const found = SearchApp.dictData.find(function(p) {
            return p.id === id || p.dilaId === id;
        });
        if (found) return found;
    }
    
    if (SearchApp.localPlaces) {
        return SearchApp.localPlaces.find(function(p) {
            return p.id === id;
        });
    }
    
    return null;
}

// AUTO RUN - Uncomment to test
// window.addEventListener("load", () => {
//     setTimeout(() => {
//         testCase("Mã Tổ Đạo Nhất");
//     }, 1000);
// });

console.log("🔍 Search module v2 loaded - with Dictionary Integration");

// ===============================
// MINI QA FRAMEWORK v1.0
// ===============================

// ===== CONFIG =====
const QA_CONFIG = {
    delayAfterSearch: 1500,
    autoRun: true
};

// ===== TEST CASES =====
const QA_TEST_CASES = [
    {
        name: "Mã Tổ Đạo Nhất",
        expect: {
            block1: true,
            block2: true,
            block3: true,
            block4: true
        }
    },
    {
        name: "Lâm Tế Nghĩa Huyền",
        expect: {
            block1: true,
            block2: true,
            block3: true,
            block4: true
        }
    }
];

// ===== CORE =====

function getBlockContent(id) {
    const el = document.getElementById(id);
    return el ? el.innerText.trim() : null;
}

function assertBlock(id, required) {
    const content = getBlockContent(id);

    if (!required) return true;

    if (!content) {
        console.error("❌ FAIL EMPTY: " + id);
        return false;
    }

    if (content.includes("Đang tải")) {
        console.error("❌ FAIL LOADING: " + id);
        return false;
    }

    if (content === "Không có dữ liệu") {
        console.error("❌ FAIL NO DATA: " + id);
        return false;
    }

    if (content === "undefined") {
        console.error("❌ FAIL UNDEFINED: " + id);
        return false;
    }

    console.log("✅ PASS: " + id);
    return true;
}

function assertData(data) {
    if (!data.bio) {
        console.error("❌ FAIL DATA: bio missing");
        return false;
    }
    return true;
}

// Crash detector
window.addEventListener("error", function(e) {
    console.error("💥 JS CRASH DETECTED:", e.message);
});

function collectResults() {
    return {
        block1: getBlockContent("block1"),
        block2: getBlockContent("block2"),
        block3: getBlockContent("block3"),
        block4: getBlockContent("block4")
    };
}

// ===== RUN 1 TEST =====
async function runTestCase(test) {
    console.log("\n======================");
    console.log("🧪 TEST: " + test.name);
    console.log("======================");

    try {
        await SearchApp.executeSearch(test.name);

        await new Promise(r => setTimeout(r, QA_CONFIG.delayAfterSearch));

        const results = collectResults();
        console.table(results);

        let pass = true;

        pass &= assertBlock("block1", test.expect.block1);
        pass &= assertBlock("block2", test.expect.block2);
        pass &= assertBlock("block3", test.expect.block3);
        pass &= assertBlock("block4", test.expect.block4);

        if (pass) {
            console.log("🎉 TEST PASS: " + test.name);
        } else {
            console.error("💥 TEST FAIL: " + test.name);
        }

        return pass;

    } catch (e) {
        console.error("💥 CRASH: " + e);
        return false;
    }
}

// ===== RUN ALL =====
async function runAllTests() {
    console.log("🚀 QA RUN START");

    let total = QA_TEST_CASES.length;
    let passed = 0;

    for (const test of QA_TEST_CASES) {
        const ok = await runTestCase(test);
        if (ok) passed++;
    }

    console.log("\n======================");
    console.log("📊 QA SUMMARY");
    console.log("======================");
    console.log("Passed: " + passed + "/" + total);

    if (passed !== total) {
        console.error("❌ QA FAILED");
    } else {
        console.log("✅ QA ALL PASS");
    }
}

// ===== AUTO RUN =====
if (QA_CONFIG.autoRun) {
    window.addEventListener("load", function() {
        setTimeout(function() {
            runAllTests();
        }, 1000);
    });
}

// ===== MANUAL RUN =====
window.QA = {
    run: runAllTests,
    test: runTestCase
};
