// Global Search - Autocomplete for Places and Monks (v2 - Enhanced with Dictionary)
// Includes: Critical places from Phật Quang, Đạo Uyển dictionaries
const SearchApp = {
    monkNames: [],
    vietNames: [],  // Priority: Vietnamese/Han characters
    localPlaces: [],
    criticalPlaces: [],
    dictData: [],
    isLoading: false,
    debounceTimer: null,
    selectedIndex: -1,
    currentQuery: '',
    minChars: 2,  // Start search after 2 chars

    /**
     * Initialize - load all data sources
     */
    init: async function() {
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
                    lon: p.gps?.lon,
                    searchType: 'critical'
                });
            });
        }
        
        console.log(`✅ Unified: ${this.unifiedData.length} items ready`);
        
        this.setupEvents();
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
            // Use pre-filtered: 2487 VN/Han names
            const response = await fetch('/daoanh/data/processed/monk_names_vn.json');
            if (response.ok) {
                this.monkNames = await response.json();
                console.log(`👤 Loaded: ${this.monkNames.length} VN/Han names`);
            } else {
                this.monkNames = [];
            }
        } catch (error) {
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

        // Keyboard navigation - arrow keys + Enter (Tab jumps to list)
        searchInput.addEventListener('keydown', (e) => {
            const resultsDiv = document.getElementById('search-results');
            const dropdownVisible = resultsDiv && !resultsDiv.classList.contains('hidden');
            const items = dropdownVisible ? resultsDiv.querySelectorAll('.search-result-item') : [];
            
            // Down/Up arrows - navigate dropdown
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                if (dropdownVisible && items.length > 0) {
                    e.preventDefault();
                    if (e.key === 'ArrowDown') {
                        this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                    } else {
                        this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                    }
                    this.highlightItem(items);
                }
            } 
            // Enter - select current
            else if (e.key === 'Enter') {
                e.preventDefault();
                if (dropdownVisible && this.selectedIndex >= 0 && items[this.selectedIndex]) {
                    items[this.selectedIndex].click();
                } else if (this.currentQuery) {
                    this.selectFirstResult();
                }
            } 
            // Tab - move to first result
            else if (e.key === 'Tab' && dropdownVisible && items.length > 0) {
                e.preventDefault();
                this.selectedIndex = 0;
                this.highlightItem(items);
            }
            // Escape - close dropdown
            else if (e.key === 'Escape') {
                resultsDiv.classList.add('hidden');
                this.selectedIndex = -1;
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
     * Render unified results with labels
     */
    renderUnifiedResults: function(results, query) {
        const resultsDiv = document.getElementById('search-results');
        
        if (!results || results.length === 0) {
            resultsDiv.innerHTML = `<div class="search-result-item">
                <span style="color:#94a3b8;">No results for "${this.escapeHtml(query)}"</span>
            </div>`;
            resultsDiv.classList.remove('hidden');
            return;
        }

        let html = results.map((item, idx) => {
            const icon = (item.label || item.type || '') === 'Vị Tổ' ? '👤' : ((item.label || item.type || '') === 'Chùa' ? '🏛' : '📍');
            const locText = item.location || item.province || '';
            const nameText = item.name || 'Unknown';
            
            return `<div class="search-result-item" data-index="${idx}" onclick="SearchApp.selectSearchResult('${this.escapeHtml(nameText)}', '${item.lat || ''}', '${item.lon || ''}', '${item.id || ''}')">
                <div class="result-main">
                    <div class="result-name">${this.highlightMatch(nameText, query)}</div>
                    ${locText ? `<div class="result-loc">${locText}</div>` : ''}
                </div>
                <span class="result-type">${icon} ${item.label || item.type || ''}</span>
            </div>`;
        }).join('');

        resultsDiv.innerHTML = html;
        resultsDiv.classList.remove('hidden');
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
    loadEntityData: async function(id, name) {
        console.log(`📋 Loading full data for: ${id}`);
        
        // 1. VIET NGU - BIO
        try {
            const resp = await fetch(`/daoanh/api/persons/${id}`);
            if (resp.ok) {
                const person = await resp.json();
                const bio = person.biography || '';
                console.log(`📋 Block 1 (Việt Ngữ): ${bio.substring(0, 50)}...`);
            }
        } catch(e) { console.warn('BIO load error:', e); }
        
        // 2. CBETA
        try {
            const resp = await fetch(`/daoanh/api/dict/search?q=${name}`);
            if (resp.ok) {
                const data = await resp.json();
                console.log(`📋 Block 2 (CBETA): ${data.results?.dict?.length || 0} terms`);
            }
        } catch(e) { console.warn('CBETA error:', e); }
        
        // 3. TAISHO
        try {
            const resp = await fetch(`/daoanh/api/dict/search?q=${name}&type=taisho`);
            if (resp.ok) {
                const data = await resp.json();
                console.log(`📋 Block 3 (Taisho): ${data.total || 0} results`);
            }
        } catch(e) { console.warn('Taisho error:', e); }
        
        // 4. DILA Metadata
        try {
            // Already loaded via persons API
            console.log(`📋 Block 4 (DILA): ✓`);
        } catch(e) { console.warn('DILA error:', e); }
        
        console.log(`✅ Full Data Loaded for ID: ${id}`);
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
     * Load TTL/BIO data — T73: hiển thị bio DILA + nút Tạm Dịch + Báo lỗi
     */
    loadTTLData: async function(dilaId, name) {
        const workbench = document.getElementById('workbench-content');
        if (workbench) {
            workbench.innerHTML = `<div class="bio-loading" style="padding:12px;color:#888;">Đang tải hồ sơ…</div>`;
        }
        try {
            const resp = await fetch(`/daoanh/api/persons/${dilaId}`);
            if (!resp.ok) throw new Error('404');
            const person = await resp.json();
            console.log(`📋 BIO: ${(person.bio_zh || '').substring(0, 80)}…`);
            if (workbench) {
                workbench.innerHTML = this._renderPersonBio(person, dilaId);
            }
        } catch(e) {
            console.warn('BIO error:', e);
            if (workbench) workbench.innerHTML = `<p style="color:#888;padding:12px">Không tìm thấy hồ sơ DILA.</p>`;
        }
    },

    _renderPersonBio: function(person, dilaId) {
        const bioZh = person.bio_zh || '';
        const bioVi = person.bio_vi || '';
        const tid   = person.translation_id || '';
        const status = person.bio_vi_status || '';
        const hasBio = bioZh.length > 0;

        const metaHtml = `
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;font-size:12px;color:#888;">
                ${person.dynasty ? `<span>Triều đại: <b>${person.dynasty}</b></span>` : ''}
                ${person.sect ? `<span>Tông: <b>${person.sect}</b></span>` : ''}
                ${person.birth_year ? `<span>(${person.birth_year}–${person.death_year || '?'})</span>` : ''}
            </div>`;

        const sourceTag = `<span style="font-size:11px;background:#1a3a5c;color:#6ab4ff;padding:2px 6px;border-radius:3px;margin-left:6px;">DILA Authority</span>`;

        // Tiểu sử Hán văn (gốc)
        const bioZhHtml = hasBio ? `
            <details style="margin-top:8px;">
                <summary style="cursor:pointer;color:#aaa;font-size:12px;user-select:none;">
                    Nguyên bản Hán văn ${sourceTag}
                </summary>
                <p style="margin:6px 0 0;font-size:13px;line-height:1.7;color:#ccc;font-family:'Noto Serif SC',serif;">${bioZh}</p>
            </details>` : '<p style="color:#666;font-size:13px;">Chưa có tiểu sử DILA.</p>';

        // Panel bản dịch
        let translatePanel = '';
        if (hasBio) {
            if (bioVi) {
                const statusBadge = status === 'reported'
                    ? `<span style="font-size:11px;color:#f87;margin-left:6px;">⚠ Đã báo lỗi</span>`
                    : (status === 'auto'
                        ? `<span style="font-size:11px;color:#fa3;margin-left:6px;">Tạm dịch AI</span>`
                        : `<span style="font-size:11px;color:#6f6;margin-left:6px;">✓ Đã xét duyệt</span>`);
                translatePanel = `
                    <div style="margin-top:10px;border-top:1px solid #2a2a2a;padding-top:10px;">
                        <div style="font-size:12px;color:#888;margin-bottom:4px;">Bản dịch tiếng Việt ${statusBadge}</div>
                        <p id="bio-vi-text" style="font-size:14px;line-height:1.8;color:#ddd;">${bioVi}</p>
                        <div style="display:flex;gap:8px;margin-top:8px;">
                            <button onclick="SearchApp.retranslateBio('${dilaId}')"
                                style="font-size:12px;padding:4px 10px;background:#1e3a2a;border:1px solid #3a6;color:#6d6;border-radius:4px;cursor:pointer;">
                                Dịch lại
                            </button>
                            <button onclick="SearchApp.reportBioTranslation('${dilaId}','${tid}')"
                                style="font-size:12px;padding:4px 10px;background:#2a1a1a;border:1px solid #633;color:#c66;border-radius:4px;cursor:pointer;">
                                Báo lỗi dịch
                            </button>
                        </div>
                    </div>`;
            } else {
                translatePanel = `
                    <div style="margin-top:10px;border-top:1px solid #2a2a2a;padding-top:10px;">
                        <button id="btn-tam-dich-${dilaId}" onclick="SearchApp.translateBio('${dilaId}')"
                            style="font-size:13px;padding:6px 16px;background:#1a2a3a;border:1px solid #46a;color:#8af;border-radius:5px;cursor:pointer;">
                            Tạm Dịch (AI)
                        </button>
                        <span style="font-size:11px;color:#666;margin-left:8px;">Dịch tiểu sử DILA sang tiếng Việt</span>
                    </div>`;
            }
        }

        return `<div style="padding:12px;">
            <h4 style="margin:0 0 4px;font-size:16px;">${person.name_vi || person.name_zh || ''}
                <span style="font-size:13px;color:#888;font-weight:normal;margin-left:6px;">${person.name_zh || ''}</span>
            </h4>
            ${metaHtml}
            ${bioZhHtml}
            <div id="bio-translate-panel-${dilaId}">${translatePanel}</div>
        </div>`;
    },

    translateBio: async function(dilaId) {
        const btn = document.getElementById(`btn-tam-dich-${dilaId}`);
        const panel = document.getElementById(`bio-translate-panel-${dilaId}`);
        if (btn) { btn.disabled = true; btn.textContent = 'Đang dịch…'; }
        try {
            const resp = await fetch(`/daoanh/api/person/${dilaId}/translate`, {method:'POST'});
            const data = await resp.json();
            if (data.ok && data.bio_vi && panel) {
                panel.innerHTML = `
                    <div style="margin-top:10px;border-top:1px solid #2a2a2a;padding-top:10px;">
                        <div style="font-size:12px;color:#fa3;margin-bottom:4px;">Tạm dịch AI</div>
                        <p id="bio-vi-text" style="font-size:14px;line-height:1.8;color:#ddd;">${data.bio_vi}</p>
                        <div style="display:flex;gap:8px;margin-top:8px;">
                            <button onclick="SearchApp.retranslateBio('${dilaId}')"
                                style="font-size:12px;padding:4px 10px;background:#1e3a2a;border:1px solid #3a6;color:#6d6;border-radius:4px;cursor:pointer;">
                                Dịch lại
                            </button>
                            <button onclick="SearchApp.reportBioTranslation('${dilaId}','${data.translation_id}')"
                                style="font-size:12px;padding:4px 10px;background:#2a1a1a;border:1px solid #633;color:#c66;border-radius:4px;cursor:pointer;">
                                Báo lỗi dịch
                            </button>
                        </div>
                    </div>`;
            } else if (panel) {
                panel.innerHTML += `<p style="color:#f66;font-size:12px;">Dịch thất bại. Thử lại sau.</p>`;
                if (btn) { btn.disabled = false; btn.textContent = 'Tạm Dịch (AI)'; }
            }
        } catch(e) {
            console.warn('translate error:', e);
            if (btn) { btn.disabled = false; btn.textContent = 'Tạm Dịch (AI)'; }
        }
    },

    retranslateBio: async function(dilaId) {
        const panel = document.getElementById(`bio-translate-panel-${dilaId}`);
        if (panel) panel.innerHTML = `<div style="font-size:12px;color:#aaa;margin-top:10px;">Đang dịch lại…</div>`;
        await this.translateBio(dilaId);
    },

    reportBioTranslation: async function(dilaId, translationId) {
        if (!translationId) return;
        const note = prompt('Mô tả vấn đề bản dịch (tùy chọn):') || '';
        try {
            const resp = await fetch(`/daoanh/api/person/${dilaId}/translate/report`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({translation_id: parseInt(translationId), note})
            });
            const data = await resp.json();
            if (data.ok) {
                alert(`Đã báo cáo. Cảm ơn! (Tổng báo cáo: ${data.report_count})`);
            }
        } catch(e) { console.warn('report error:', e); }
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
     * Unified search - all types
     */
    searchUnified: function(query) {
        if (query.length < this.minChars) return [];
        if (!this.unifiedData || !this.unifiedData.length) return [];
        
        const q = query.toLowerCase().trim();
        const results = this.unifiedData
            .filter(item => item.name && item.name.toLowerCase().includes(q))
            .slice(0, 10)
            .map(item => ({
                type: 'result',
                name: item.name,
                label: item.type,
                lat: item.lat,
                lon: item.lon,
                searchType: item.searchType
            }));
        
        console.log(`🔍 "${query}": ${results.length} results`);
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
     * Search dictionary only
     */
    searchDictOnly: function(query) {
        const dictResults = this.searchDict(query);
        this.renderResults([], [], [], [], dictResults);
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
     * Update entity card in sidebar
     */
    updateEntityCard: function(name, uri, lineageData) {
        const entityNameEl = document.querySelector('.entity-name');
        const entityZhEl = document.querySelector('.entity-name-zh');
        const entityDescEl = document.querySelector('.entity-desc');
        const entityIdEl = document.querySelector('.entity-id');

        if (entityNameEl) entityNameEl.textContent = name;
        if (entityIdEl) entityIdEl.textContent = uri;

        let desc = '';
        if (lineageData.teacher) {
            desc += `📖 Thầy: ${lineageData.teacher}<br>`;
        }
        if (lineageData.great_teacher) {
            desc += `📖 Sư phụ: ${lineageData.great_teacher}<br>`;
        }
        if (lineageData.students && lineageData.students.length > 0) {
            desc += `📖 Đệ tử: ${lineageData.students.slice(0, 3).join(', ')}${lineageData.students.length > 3 ? '...' : ''}`;
        }

        if (entityDescEl) entityDescEl.innerHTML = desc || 'Thiền sư';
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        SearchApp.init();
    }, 500);
});

console.log("🔍 Search module v2 loaded - with Dictionary Integration");
