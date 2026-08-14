// Multi-layer Entity Filter + Auto-complete
const EntityFilter = {
    dynastyFilter: null,
    typeFilter: null,
    regionFilter: null,
    searchInput: null,
    applyButton: null,
    suggestions: [],
    initialized: false,
    
    init: function() {
        this.dynastyFilter = document.getElementById('filter-dynasty');
        this.typeFilter = document.getElementById('filter-type');
        this.regionFilter = document.getElementById('filter-region');
        this.searchInput = document.getElementById('entity-search');
        this.applyButton = document.getElementById('apply-filters');
        
        console.log('🏷️ EntityFilter: Initializing...');
        
        this.setupEventListeners();
        this.initialized = true;
        
        console.log('🏷️ EntityFilter: Ready');
    },
    
    setupEventListeners: function() {
        // Dynasty filter
        if (this.dynastyFilter) {
            this.dynastyFilter.addEventListener('change', (e) => this.applyFilters());
        }
        
        // Type filter
        if (this.typeFilter) {
            this.typeFilter.addEventListener('change', (e) => this.applyFilters());
        }
        
        // Region filter
        if (this.regionFilter) {
            this.regionFilter.addEventListener('change', (e) => this.applyFilters());
        }
        
        // Apply button click
        if (this.applyButton) {
            this.applyButton.addEventListener('click', () => this.applyFilters());
        }
        
        // Search with auto-complete
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
            this.searchInput.addEventListener('focus', () => this.showSuggestions());
            
            // Hide suggestions on blur
            this.searchInput.addEventListener('blur', () => {
                setTimeout(() => this.hideSuggestions(), 200);
            });
        }
    },
    
    handleSearch: function(query) {
        if (!query || query.length < 1) {
            this.hideSuggestions();
            return;
        }
        
        // Search in critical places + monk names
        const results = this.searchEntities(query);
        this.displaySuggestions(results);
    },
    
    searchEntities: function(query) {
        const queryLower = query.toLowerCase();
        let results = [];
        
        // Search in critical places - with null check
        if (window.SearchApp && Array.isArray(window.SearchApp.criticalPlaces)) {
            const placeResults = window.SearchApp.criticalPlaces.filter(p => {
                const name = (p.vietnamese || '').toLowerCase();
                const zh = (p.searchKey || '').toLowerCase();
                return name.includes(queryLower) || zh.includes(queryLower);
            }).slice(0, 5).map(p => ({
                type: 'place',
                name: p.vietnamese,
                nameZh: p.searchKey,
                subtype: p.type
            }));
            results = [...results, ...placeResults];
        }
        
        // Search in monk names - with null check
        if (window.SearchApp && Array.isArray(window.SearchApp.monkNames)) {
            const monkResults = window.SearchApp.monkNames
                .filter(name => name.toLowerCase().includes(queryLower))
                .slice(0, 5)
                .map(name => ({
                    type: 'monk',
                    name: name,
                    subtype: 'thiền sư'
                }));
            results = [...results, ...monkResults];
        }
        
        return results;
    },
    
    displaySuggestions: function(results) {
        let container = document.getElementById('entity-suggestions');
        if (!container) {
            container = document.createElement('div');
            container.id = 'entity-suggestions';
            container.className = 'entity-suggestions';
            this.searchInput.parentNode.appendChild(container);
        }
        
        if (results.length === 0) {
            container.innerHTML = '<div class="suggestion-item no-results">Không tìm thấy</div>';
        } else {
            container.innerHTML = results.map(r => `
                <div class="suggestion-item" data-type="${r.type}" data-name="${r.name}">
                    <span class="suggestion-icon">${r.type === 'place' ? '🏛️' : '🧑'}</span>
                    <span class="suggestion-name">${r.name}</span>
                    <span class="suggestion-subtype">${r.subtype || ''}</span>
                </div>
            `).join('');
            
            // Add click handlers
            container.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', () => {
                    const name = item.dataset.name;
                    const type = item.dataset.type;
                    this.selectEntity(name, type);
                });
            });
        }
        
        container.classList.add('active');
    },
    
    hideSuggestions: function() {
        const container = document.getElementById('entity-suggestions');
        if (container) container.classList.remove('active');
    },
    
    selectEntity: function(name, type) {
        this.searchInput.value = name;
        this.hideSuggestions();
        
        if (window.SearchApp) {
            if (type === 'place') {
                window.SearchApp.handleSearch(name);
            } else if (type === 'monk') {
                window.SearchApp.handleMonkClick({ name: name });
            }
        }
    },
    
    applyFilters: function() {
        const dynasty = this.dynastyFilter?.value || '';
        const type = this.typeFilter?.value || '';
        const region = this.regionFilter?.value || '';
        
        // Apply filters to map markers
        if (window.MapApp) {
            window.MapApp.applyEntityFilters({ dynasty, type, region });
        }
        
        console.log(`🔍 Filters applied: dynasty=${dynasty}, type=${type}, region=${region}`);
    }
};

// Auto-initialize with retry
document.addEventListener('DOMContentLoaded', () => {
    let attempts = 0;
    const maxAttempts = 10;
    
    const tryInit = () => {
        attempts++;
        const filterDynasty = document.getElementById('filter-dynasty');
        
        if (filterDynasty && !EntityFilter.initialized) {
            EntityFilter.init();
        } else if (attempts < maxAttempts) {
            setTimeout(tryInit, 200);
        }
    };
    
    setTimeout(tryInit, 500);
});

console.log("🔍 EntityFilter module loaded");