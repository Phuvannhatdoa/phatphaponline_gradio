// Popup Context Cards - Hover detection + Card display + Entity Linking
const PopupCards = {
    cardContainer: null,
    cardData: {},
    
    init: function() {
        this.createCardContainer();
        this.setupHoverDetection();
    },
    
    createCardContainer: function() {
        this.cardContainer = document.createElement('div');
        this.cardContainer.id = 'popup-card';
        this.cardContainer.className = 'popup-card hidden';
        document.body.appendChild(this.cardContainer);
    },
    
    // XSS Protection: Sanitize string for HTML
    sanitizeHtml: function(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
    
    // Escape special regex characters
    escapeRegex: function(str) {
        if (!str) return '';
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },
    
    setupHoverDetection: function() {
        // Monitor workbench content for entity mentions
        const workbenchContent = document.querySelector('.workbench-content');
        if (workbenchContent) {
            // Use MutationObserver to detect content changes
            const observer = new MutationObserver(() => {
                this.addEntityLinks(workbenchContent);
            });
            observer.observe(workbenchContent, { childList: true, subtree: true });
        }
        
        // Also scan text panels periodically
        setInterval(() => {
            document.querySelectorAll('.text-panel').forEach(panel => {
                this.addEntityLinks(panel);
            });
        }, 2000);
    },
    
    addEntityLinks: function(container) {
        if (!container || container.dataset.scanned === 'true') return;
        container.dataset.scanned = 'true';
        
        // Get monk names from SearchApp
        const monkNames = SearchApp?.monkNames || [];
        const criticalPlaces = SearchApp?.criticalPlaces || [];
        
        // Combine all entities
        const entities = [
            ...monkNames.map(n => ({ name: n, type: 'monk' })),
            ...criticalPlaces.map(p => ({ name: p.vietnamese, nameZh: p.searchKey, type: 'place' }))
        ];
        
        // Find and wrap entity mentions
        const walker = document.createTreeWalker(
            container, 
            NodeFilter.SHOW_TEXT, 
            null, 
            false
        );
        
        const textNodes = [];
        while (walker.nextNode()) textNodes.push(walker.currentNode);
        
        textNodes.forEach(node => {
            const text = node.textContent;
            entities.forEach(entity => {
                const safeName = this.sanitizeHtml(entity.name);
                const safeType = this.sanitizeHtml(entity.type);
                const regex = new RegExp(`(${this.escapeRegex(entity.name)})`, 'g');
                if (regex.test(text) && text.length > 2) {
                    const span = document.createElement('span');
                    span.innerHTML = text.replace(regex, 
                        `<span class="entity-link" data-entity-name="${safeName}" data-entity-type="${safeType}">${safeName}</span>`
                    );
                    if (node.parentNode) {
                        node.parentNode.replaceChild(span, node);
                    }
                }
            });
        });
        
        // Add hover listeners
        container.querySelectorAll('.entity-link').forEach(link => {
            link.addEventListener('mouseenter', (e) => this.showCard(e));
            link.addEventListener('mouseleave', () => this.hideCard());
        });
    },
    
    showCard: async function(e) {
        const name = e.target.dataset.entityName;
        const type = e.target.dataset.entityType;
        
        // Get entity data
        const data = await this.fetchEntityData(name, type);
        this.renderCard(data, e.target);
    },
    
    fetchEntityData: async function(name, type) {
        // Try to get from critical places first
        if (SearchApp && SearchApp.criticalPlaces) {
            const place = SearchApp.criticalPlaces.find(p => 
                p.vietnamese === name || p.searchKey === name
            );
            if (place) {
                return {
                    name: place.vietnamese,
                    nameZh: place.searchKey,
                    type: place.type,
                    period: place.period,
                    description: place.description,
                    relatedMonks: place.relatedMonks || [],
                    relatedSutras: place.relatedSutras || [],
                    gps: place.gps
                };
            }
        }
        
        // Default data for monks
        if (type === 'monk') {
            return {
                name: name,
                type: 'thiền sư',
                period: 'Unknown',
                description: 'Thiền sư trong hệ thống truyền thừa Phật giáo.',
                relatedMonks: [],
                relatedSutras: []
            };
        }
        
        return null;
    },
    
    renderCard: function(data, targetElement) {
        if (!data) {
            this.hideCard();
            return;
        }
        
        // Sanitize all data fields to prevent XSS
        const safeName = this.sanitizeHtml(data.name);
        const safeNameZh = this.sanitizeHtml(data.nameZh || '');
        const safeType = this.sanitizeHtml(data.type || 'unknown');
        const safePeriod = this.sanitizeHtml(data.period || 'N/A');
        const safeDesc = this.sanitizeHtml(data.description ? data.description.substring(0, 100) + '...' : '');
        const safeGps = this.sanitizeHtml(gps);
        const safeRelatedMonks = this.sanitizeHtml(relatedMonks);
        const safeRelatedSutras = this.sanitizeHtml(relatedSutras);
        
        const icon = data.type === 'monk' ? '🧑' : 
                    data.type === 'monastery' ? '🏛️' : 
                    data.type === 'mountain' ? '⛰️' : '📍';
        
        const relatedMonks = data.relatedMonks?.slice(0, 3).join(', ') || 'Không có';
        const relatedSutras = data.relatedSutras?.slice(0, 2).join(', ') || 'Không có';
        const gps = data.gps?.lat ? `${data.gps.lat}, ${data.gps.lon}` : 'Chưa có GPS';
        
        this.cardContainer.innerHTML = `
            <div class="card-header">
                <span class="card-icon">${icon}</span>
                <span class="card-name">${safeName}</span>
                ${safeNameZh ? `<span class="card-name-zh">${safeNameZh}</span>` : ''}
            </div>
            <div class="card-body">
                <div class="card-field">
                    <span class="field-label">Loại:</span>
                    <span class="field-value">${safeType}</span>
                </div>
                <div class="card-field">
                    <span class="field-label">Thời kỳ:</span>
                    <span class="field-value">${safePeriod}</span>
                </div>
                <div class="card-field">
                    <span class="field-label">GPS:</span>
                    <span class="field-value">${safeGps}</span>
                </div>
                ${safeDesc ? `
                <div class="card-desc">${safeDesc}</div>
                ` : ''}
                <div class="card-field">
                    <span class="field-label">Liên quan:</span>
                    <span class="field-value">${safeRelatedMonks}</span>
                </div>
                <div class="card-field">
                    <span class="field-label">Kinh văn:</span>
                    <span class="field-value">${safeRelatedSutras}</span>
                </div>
            </div>
            <div class="card-footer">
                <button class="card-btn view-network" data-mon="${safeName}" onclick="NetworkViewer.show(this.dataset.mon)">
                    🔗 Xem sơ đồ
                </button>
            </div>
        `;
        
        // Position card near target element
        const rect = targetElement.getBoundingClientRect();
        this.cardContainer.style.left = `${rect.left}px`;
        this.cardContainer.style.top = `${rect.bottom + 10}px`;
        
        this.cardContainer.classList.remove('hidden');
    },
    
    hideCard: function() {
        this.cardContainer.classList.add('hidden');
    }
};

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => PopupCards.init(), 1000);
});

console.log("🔍 PopupCards module loaded");