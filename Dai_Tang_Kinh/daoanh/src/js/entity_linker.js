var EntityLinker = {
    cache: {
        persons: new Map(),
        places: new Map()
    },
    
    init: function() {
        console.log('[EntityLinker] Initializing...');
        this.loadEntityIndex();
    },
    
    loadEntityIndex: async function() {
        try {
            var personResponse = await fetch('/daoanh/api/persons?limit=100');
            var personData = await personResponse.json();
            
            if (personData.persons) {
                personData.persons.forEach(function(p) {
                    p.names.forEach(function(n) {
                        EntityLinker.cache.persons.set(n.value, {
                            id: p.id,
                            type: 'person'
                        });
                    });
                });
            }
            
            console.log('[EntityLinker] Loaded:', EntityLinker.cache.persons.size, 'persons');
        } catch (error) {
            console.error('[EntityLinker] Load error:', error);
        }
    },
    
    linkText: async function(text) {
        if (!text) return { html: text, entities: [] };
        
        try {
            var response = await fetch('/daoanh/api/entity/link', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            return await response.json();
        } catch (error) {
            console.error('[EntityLinker] Link error:', error);
            return { html: text, entities: [] };
        }
    },
    
    resolveEntity: async function(id, type) {
        try {
            var url = '/api/entity/resolve?id=' + encodeURIComponent(id) + '&type=' + (type || '');
            var response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('[EntityLinker] Resolve error:', error);
            return null;
        }
    },
    
    setupClickHandlers: function(container) {
        if (!container) container = document;
        
        container.querySelectorAll('.entity-link').forEach(function(link) {
            link.addEventListener('click', async function(e) {
                e.preventDefault();
                
                var id = link.dataset.id;
                var type = link.dataset.type;
                
                var entity = await EntityLinker.resolveEntity(id, type);
                if (entity) {
                    EntityLinker.showEntityPopup(entity, link);
                }
            });
        });
    },
    
    showEntityPopup: function(entity, targetElement) {
        var popup = document.getElementById('entity-popup');
        if (!popup) {
            popup = document.createElement('div');
            popup.id = 'entity-popup';
            popup.className = 'entity-popup';
            document.body.appendChild(popup);
        }
        
        var content = '<strong>' + (entity.names ? entity.names[0] : entity.nameChinese) + '</strong>';
        
        if (entity.type === 'person') {
            content += '<br><span class="dynasty">' + (entity.dynasty || '') + '</span>';
            if (entity.biography) {
                content += '<p class="bio">' + entity.biography.substring(0, 100) + '...</p>';
            }
        } else {
            content += '<br>' + (entity.nameVietnamese || '');
            if (entity.lat && entity.lon) {
                content += '<br><small>GPS: ' + entity.lat + ', ' + entity.lon + '</small>';
            }
        }
        
        popup.innerHTML = content;
        popup.style.display = 'block';
        
        var rect = targetElement.getBoundingClientRect();
        popup.style.left = rect.left + 'px';
        popup.style.top = (rect.bottom + 5) + 'px';
    }
};

document.addEventListener('DOMContentLoaded', function() {
    EntityLinker.init();
});