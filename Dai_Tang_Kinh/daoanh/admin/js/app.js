/**
 * Admin Panel - Main Application
 * Version: v2.5-Admin
 * Extended: v6.0-Heritage-TổĐình
 */

const API_BASE = '/daoanh/api';

// ========================================
// Heritage Handlers (v6.0)
// ========================================

const HeritageApp = {
    HERITAGE_LEVELS: [
        { value: 'UNESCO', label: '🏆 Di sản UNESCO', color: '#ffd700' },
        { value: 'Quốc Gia', label: '🏛️ Di sản Quốc Gia', color: '#f97316' },
        { value: 'Tỉnh', label: '📜 Di sản Tỉnh', color: '#3b82f6' },
        { value: 'Tân Tự', label: '🏗️ Tân Tự (Mới)', color: '#6b7280' }
    ],

    /**
     * Detect heritage from wiki text
     */
    detectFromText: async function(wikiText) {
        try {
            const response = await fetch(API_BASE + '/admin/heritage/detect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({wiki_text: wikiText})
            });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[Heritage] Detect failed:', error);
            return {detected: 'Tân Tự'};
        }
    },

    /**
     * Verify/update heritage status
     */
    verifyHeritage: async function(placeId, heritageStatus) {
        try {
            const response = await fetch(API_BASE + '/admin/heritage/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    place_id: placeId,
                    heritage_status: heritageStatus
                })
            });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[Heritage] Verify failed:', error);
            return {error: error.message};
        }
    },

    /**
     * Run cron detection on all places
     */
    runCron: async function() {
        try {
            const response = await fetch(API_BASE + '/admin/heritage/run-cron', {
                method: 'POST'
            });
            const data = await response.json();
            console.log('[Heritage] Cron result:', data);
            return data;
        } catch (error) {
            console.error('[Heritage] Cron failed:', error);
            return {error: error.message};
        }
    },

    /**
     * Get heritage stats
     */
    getStats: async function() {
        try {
            const response = await fetch(API_BASE + '/admin/heritage/stats');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[Heritage] Stats failed:', error);
            return {total: 0};
        }
    },

    /**
     * Get icon by level
     */
    getIcon: function(level) {
        const icons = {
            'UNESCO': '🏆',
            'Quốc Gia': '🏛️',
            'Tỉnh': '📜',
            'Tân Tự': '🏗️'
        };
        return icons[level] || '🏗️';
    }
};

// Legacy exports
window.HeritageApp = HeritageApp;
window.detectHeritage = HeritageApp.detectFromText;
window.verifyHeritage = HeritageApp.verifyHeritage;
window.runHeritageCron = HeritageApp.runCron;

// ========================================
// Staging & Verification Handlers (v5.9)
// ========================================

const StagingApp = {
    currentView: 'verification',
    currentItem: null,

    /**
     * Load staging queue
     */
    loadStagingQueue: async function() {
        try {
            const response = await fetch(API_BASE + '/admin/staging/list');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[Staging] Load failed:', error);
            return {items: [], total: 0};
        }
    },

    /**
     * Load verification queue
     */
    loadVerificationQueue: async function() {
        try {
            const response = await fetch(API_BASE + '/admin/verification/list');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[Verification] Load failed:', error);
            return {items: [], total: 0};
        }
    },

    /**
     * Publish to Gmaps Vietnam (Local)
     */
    publishLocal: async function(placeId, gps) {
        try {
            const response = await fetch(API_BASE + '/admin/publish-local', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({place_id: placeId, gps: gps})
            });
            const data = await response.json();
            console.log('[Staging] Published:', data);
            return data;
        } catch (error) {
            console.error('[Staging] Publish failed:', error);
            return {error: error.message};
        }
    },

    /**
     * Map to DILA Global Authority
     */
    mapGlobal: async function(placeId, dilaId) {
        try {
            const response = await fetch(API_BASE + '/admin/map-global', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({place_id: placeId, dila_id: dilaId})
            });
            const data = await response.json();
            console.log('[Verification] Mapped:', data);
            return data;
        } catch (error) {
            console.error('[Verification] Map failed:', error);
            return {error: error.message};
        }
    },

    /**
     * Check sync status
     */
    checkSyncStatus: async function() {
        try {
            const response = await fetch(API_BASE + '/admin/sync-check');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[Sync] Check failed:', error);
            return {sync_status: 'error', error: error.message};
        }
    }
};

// Legacy exports for inline JS
window.StagingApp = StagingApp;
window.loadStagingQueue = StagingApp.loadStagingQueue;
window.loadVerificationQueue = StagingApp.loadVerificationQueue;
window.publishLocal = StagingApp.publishLocal;
window.mapGlobal = StagingApp.mapGlobal;
window.checkSyncStatus = StagingApp.checkSyncStatus;

const AdminApp = {
    // State
    data: {
        places: [],
        stats: {},
        logs: [],
        gpsChanges: []
    },
    pagination: {
        page: 1,
        perPage: 20,
        total: 0
    },
    currentSection: 'dashboard',

    /**
     * Initialize admin app
     */
init: function() {
        console.log('🚀 Admin Panel v2.5 initializing...');
        
        // Load dashboard stats
        this.loadDashboard();
        
        // Also load places
        this.loadPlaces();
        this.hideLoading();
    },

    /**
     * Bridge: Load DILA queue (places pending without Vietnamese names)
     */
    loadDilaQueue: async function() {
        try {
            const res = await fetch(API_BASE + '/admin/places_pending?no_vi=true');
            const data = await res.json();
            const container = document.getElementById('mapping-form-content');
            if (!container) {
                console.warn('mapping-form-content not found');
                return;
            }
            let html = '<h3>🗺️ DILA Places chưa có tên tiếng Việt (' + (data.total || 0) + ')</h3>';
            if (data.places && data.places.length) {
                html += '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
                html += '<tr style="background:#334155"><th>ID</th><th>Hán</th><th>Tỉnh</th><th>Thao tác</th></tr>';
                data.places.forEach(p => {
                    html += `<tr>
                        <td>${p.id || ''}</td>
                        <td style="color:#fbbf24;">${p.name_zh || ''}</td>
                        <td>${p.province || ''}</td>
                        <td><button class="btn-edit-mapping" data-id="${p.id}" style="background:#3b82f6;color:white;padding:4px 8px;border:none;border-radius:4px;cursor:pointer;font-size:10px;">Dịch</button></td>
                    </tr>`;
                });
                html += '</table>';
            } else {
                html += '<p>Không có dữ liệu</p>';
            }
            container.innerHTML = html;
        } catch (err) {
            console.error('loadDilaQueue error:', err);
        }
    },

    /**
     * Hide loading overlay
     */
    hideLoading: function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    /**
     * Setup navigation handlers
     */
    setupNavigation: function() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.navigateTo(section);
            });
        });
    },

    /**
     * Navigate to section
     */
    navigateTo: function(section) {
        // Update nav active
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.section === section) {
                item.classList.add('active');
            }
        });

        // Update section title
        const titles = {
            dashboard: 'Dashboard',
            places: 'Places Management',
            gps: 'GPS Compare Tool',
            translation: 'Vietnamese Translation',
            logs: 'Activity Logs'
        };
        document.getElementById('section-title').textContent = titles[section] || section;

        // Show correct section
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        this.currentSection = section;

        // Load section data
        switch(section) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'places':
                this.loadPlaces();
                break;
            case 'gps':
                this.loadGPSCompare();
                break;
            case 'translation':
                this.loadTranslation();
                break;
            case 'logs':
                this.loadLogs();
                break;
        }
    },

    /**
     * Load Dashboard data
     */
    loadDashboard: async function() {
        try {
            // Load basic stats - use correct path for nginx
            var response = await fetch('/daoanh/api/stats');
            if (!response.ok) {
                console.error('[Admin] Stats API failed:', response.status);
                throw new Error('Stats API: ' + response.status);
            }
            var stats = await response.json();
            
            // Update stats with null checks
            var el = document.getElementById('stat-total-places');
            if (el) el.textContent = stats.total || 0;
            
            el = document.getElementById('stat-vietnamese');
            if (el) el.textContent = stats.vietnamese || 0;
            
            el = document.getElementById('stat-gps');
            if (el) el.textContent = stats.with_gps || 0;
            
            // verified = DILA (trusted source)
            el = document.getElementById('stat-verified');
            if (el) el.textContent = stats.dila || 0;

            // Load detailed DILA stats
            var dilaResponse = await fetch('/daoanh/api/admin/dila-stats');
            if (!dilaResponse.ok) {
                console.error('[Admin] DILA Stats API failed:', dilaResponse.status);
                throw new Error('DILA Stats API: ' + dilaResponse.status);
            }
            var dilaStats = await dilaResponse.json();
            
            // Update DILA breakdown
            el = document.getElementById('stat-temples');
            if (el) el.textContent = dilaStats.temples || 0;
            
            el = document.getElementById('stat-stupas');
            if (el) el.textContent = dilaStats.stupas || 0;
            
            el = document.getElementById('stat-caves');
            if (el) el.textContent = dilaStats.caves || 0;
            
            el = document.getElementById('stat-sites');
            if (el) el.textContent = dilaStats.sites || 0;
            
            // Update GPS accuracy
            el = document.getElementById('stat-gps-accuracy');
            if (el) el.textContent = dilaStats.gps_accuracy + '%';
            
            var bar = document.getElementById('gps-accuracy-bar');
            if (bar) bar.style.width = dilaStats.gps_accuracy + '%';
            
            console.log('[Admin] DILA Stats loaded:', dilaStats);
            
            // NEW: Load Person Authority stats
            try {
                var personResponse = await fetch('/daoanh/api/admin/person-stats');
                if (!personResponse.ok) {
                    console.error('[Admin] Person Stats API failed:', personResponse.status);
                    throw new Error('Person Stats API: ' + personResponse.status);
                }
                var personStats = await personResponse.json();
                
                console.log('[Admin] Person Stats loaded:', personStats);
                
                // Update Person Authority stats
                el = document.getElementById('stat-persons-total');
                if (el) el.textContent = personStats.total ? personStats.total.toLocaleString() : 0;
                
                el = document.getElementById('stat-persons-monks');
                if (el) el.textContent = personStats.monks ? personStats.monks.toLocaleString() : 0;
                
                el = document.getElementById('stat-persons-teachers');
                if (el) el.textContent = personStats.with_teacher ? personStats.with_teacher.toLocaleString() : 0;
                
                el = document.getElementById('stat-persons-students');
                if (el) el.textContent = personStats.with_student ? personStats.with_student.toLocaleString() : 0;
                
                // Update lotus index
                el = document.getElementById('stat-persons-lotus');
                if (el) el.textContent = (personStats.lotus_index || 0) + '%';
                
                var personBar = document.getElementById('person-lotus-bar');
                if (personBar) personBar.style.width = (personStats.lotus_index || 0) + '%';
                
            } catch (personError) {
                console.warn('[Admin] Person stats loading failed:', personError);
            }
            
            // NEW: Load Time Authority (dynasty distribution)
            try {
                var timelineResponse = await fetch('/daoanh/api/persons/timeline');
                var timelineData = await timelineResponse.json();
                
                console.log('[Admin] Timeline loaded:', timelineData);
                
                // Update timeline stats
                var timelineEl = document.getElementById('stat-timeline-total');
                if (timelineEl) timelineEl.textContent = timelineData.total ? timelineData.total.toLocaleString() : 0;
                
                // Render dynasty chart
                var dynastyChart = document.getElementById('dynasty-chart');
                if (dynastyChart && timelineData.timeline) {
                    var maxCount = Math.max(...timelineData.timeline.map(t => t.count));
                    dynastyChart.innerHTML = timelineData.timeline.slice(0, 10).map(t => {
                        var percent = (t.count / maxCount) * 100;
                        return `<div class="dynasty-bar" style="width:${percent}%">
                            <span class="dynasty-label">${t.dynasty}</span>
                            <span class="dynasty-count">${t.count}</span>
                        </div>`;
                    }).join('');
                }
                
            } catch (timelineError) {
                console.warn('[Admin] Timeline loading failed:', timelineError);
            }
            
            // Load source breakdown
            this.loadSourceBreakdown();
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    },

    /**
     * Load source breakdown
     */
    loadSourceBreakdown: async function() {
        try {
            const response = await fetch('/daoanh/api/admin/sources');
            if (!response.ok) {
                console.error('[Admin] Sources API failed:', response.status);
                return;
            }
            const data = await response.json();
            
            const tbody = document.getElementById('source-table-body');
            if (tbody && data.sources) {
                tbody.innerHTML = data.sources.map(s => `
                    <tr>
                        <td>${s.name}</td>
                        <td>${s.count}</td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load sources:', error);
        }
    },

    /**
     * Load Places data
     */
    loadPlaces: async function() {
        try {
            const page = this.pagination.page;
            const perPage = this.pagination.perPage;
            const search = document.getElementById('place-search')?.value || '';
            
            const response = await fetch(`/daoanh/api/admin/places?page=${page}&per_page=${perPage}&search=${encodeURIComponent(search)}`);
            const data = await response.json();
            
            this.data.places = data.places || [];
            this.pagination.total = data.total || 0;
            
            this.renderPlacesTable();
            this.renderPagination();
        } catch (error) {
            console.error('Failed to load places:', error);
        }
    },

    /**
     * Render places table
     */
    renderPlacesTable: function() {
        const tbody = document.getElementById('places-table-body');
        if (!tbody) return;

        if (this.data.places.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No places found</td></tr>';
            return;
        }

        tbody.innerHTML = this.data.places.map(place => `
            <tr>
                <td><code>${place.id || '-'}</code></td>
                <td>${place.nameVietnamese || '-'}</td>
                <td class="han-nom">${place.nameChinese || '-'}</td>
                <td>${place.province || '-'}</td>
                <td>${place.lat && place.lon ? `${place.lat}, ${place.lon}` : '<span style="color:var(--text-muted)">No GPS</span>'}</td>
                <td>${place.source || '-'}</td>
                <td>
                    <button class="btn btn-secondary" onclick="AdminApp.editPlace('${place.id}')">Edit</button>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Render pagination
     */
    renderPagination: function() {
        const container = document.getElementById('places-pagination');
        if (!container) return;

        const totalPages = Math.ceil(this.pagination.total / this.pagination.perPage);
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '';
        for (let i = 1; i <= totalPages; i++) {
            html += `<button onclick="AdminApp.goToPage(${i})" ${i === this.pagination.page ? 'style="background:var(--primary);color:var(--bg-dark)"' : ''}>${i}</button>`;
        }
        container.innerHTML = html;
    },

    /**
     * Go to page
     */
    goToPage: function(page) {
        this.pagination.page = page;
        this.loadPlaces();
    },

    /**
     * Load GPS Compare data
     */
    loadGPSCompare: async function() {
        try {
            const response = await fetch('/daoanh/api/admin/gps-compare');
            const data = await response.json();
            
            this.data.gpsChanges = data.changes || [];
            
            // Update stats
            const approved = this.data.gpsChanges.filter(c => c.status === 'approved').length;
            const pending = this.data.gpsChanges.filter(c => c.status === 'pending').length;
            const rejected = this.data.gpsChanges.filter(c => c.status === 'rejected').length;
            
            document.getElementById('gps-total').textContent = this.data.gpsChanges.length;
            document.getElementById('gps-approved').textContent = approved;
            document.getElementById('gps-pending').textContent = pending;
            document.getElementById('gps-rejected').textContent = rejected;
            
            this.renderGPSCompareTable();
        } catch (error) {
            console.error('Failed to load GPS compare:', error);
        }
    },

    /**
     * Render GPS compare table
     */
    renderGPSCompareTable: function() {
        const tbody = document.getElementById('gps-compare-body');
        if (!tbody) return;

        if (this.data.gpsChanges.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No GPS changes to review</td></tr>';
            return;
        }

        tbody.innerHTML = this.data.gpsChanges.map(change => `
            <tr>
                <td>${change.name}</td>
                <td>${change.old_lat}, ${change.old_lon}</td>
                <td>${change.new_lat}, ${change.new_lon}</td>
                <td>${change.distance}m</td>
                <td><span class="status-${change.status}">${change.status}</span></td>
                <td>
                    ${change.status === 'pending' ? `
                        <button class="btn btn-success" onclick="AdminApp.approveGPS('${change.id}')">✓</button>
                        <button class="btn btn-danger" onclick="AdminApp.rejectGPS('${change.id}')">✗</button>
                    ` : '-'}
                </td>
            </tr>
        `).join('');
    },

    /**
     * Approve GPS change
     */
    approveGPS: async function(id) {
        try {
            await fetch(`/daoanh/api/admin/gps-compare/${id}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'approve'})
            });
            this.loadGPSCompare();
        } catch (error) {
            console.error('Failed to approve GPS:', error);
        }
    },

    /**
     * Reject GPS change
     */
    rejectGPS: async function(id) {
        try {
            await fetch(`/daoanh/api/admin/gps-compare/${id}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'reject'})
            });
            this.loadGPSCompare();
        } catch (error) {
            console.error('Failed to reject GPS:', error);
        }
    },

    /**
     * Load Translation data
     */
    loadTranslation: async function() {
        try {
            const response = await fetch('/daoanh/api/admin/translation-needed');
            const data = await response.json();
            
            const tbody = document.getElementById('translation-body');
            if (tbody) {
                tbody.innerHTML = (data.places || []).map(place => `
                    <tr>
                        <td class="han-nom">${place.nameChinese || '-'}</td>
                        <td>${place.nameVietnamese || '<span style="color:var(--warning)">Pending</span>'}</td>
                        <td>${place.nameVietnamese ? '✓ Translated' : '<span style="color:var(--warning)">Need Translation</span>'}</td>
                        <td>
                            <button class="btn btn-primary" onclick="AdminApp.editTranslation('${place.id}')">Edit</button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load translation:', error);
        }
    },

    /**
     * Edit translation
     */
    editTranslation: function(id) {
        const place = this.data.places.find(p => p.id === id) || {};
        
        document.getElementById('translation-form').style.display = 'block';
        document.getElementById('trans-id').value = id;
        document.getElementById('trans-name-zh').value = place.nameChinese || '';
        document.getElementById('trans-name-vi').value = place.nameVietnamese || '';
        document.getElementById('trans-desc-vi').value = place.descriptionVi || '';
    },

    /**
     * Save translation
     */
    saveTranslation: async function() {
        const id = document.getElementById('trans-id').value;
        const nameVi = document.getElementById('trans-name-vi').value;
        const descVi = document.getElementById('trans-desc-vi').value;
        
        try {
            await fetch(`/daoanh/api/admin/places/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    nameVietnamese: nameVi,
                    descriptionVi: descVi
                })
            });
            
            document.getElementById('translation-form').style.display = 'none';
            this.loadTranslation();
        } catch (error) {
            console.error('Failed to save translation:', error);
        }
    },

    /**
     * Load Logs
     */
    loadLogs: async function() {
        try {
            const response = await fetch('/daoanh/api/admin/logs');
            const data = await response.json();
            
            const tbody = document.getElementById('logs-body');
            if (tbody) {
                tbody.innerHTML = (data.logs || []).map(log => `
                    <tr>
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                        <td><span class="log-type-${log.type}">${log.type}</span></td>
                        <td>${log.user || 'System'}</td>
                        <td>${log.action}</td>
                        <td>${log.details || '-'}</td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    },

    /**
     * Edit place
     */
    editPlace: function(id) {
        console.log('Edit place:', id);
        alert('Edit functionality coming soon!');
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    AdminApp.init();
});

// Setup event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Search input
    const searchInput = document.getElementById('place-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            AdminApp.pagination.page = 1;
            AdminApp.loadPlaces();
        }, 300));
    }
    
    // Add place button
    const addBtn = document.getElementById('add-place-btn');
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            alert('Add place functionality coming soon!');
        });
    }
    
    // Translation buttons
    const saveTransBtn = document.getElementById('save-translation');
    if (saveTransBtn) {
        saveTransBtn.addEventListener('click', () => AdminApp.saveTranslation());
    }
    
    const cancelTransBtn = document.getElementById('cancel-translation');
    if (cancelTransBtn) {
        cancelTransBtn.addEventListener('click', () => {
            document.getElementById('translation-form').style.display = 'none';
        });
    }
});

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ========================================
// CSV Multi-Source Import Handlers
// ========================================

var CSVData = [];

/**
 * Handle CSV file upload
 */
function handleCSVUpload(input) {
    var file = input.files[0];
    if (!file) return;
    
    console.log('[CSV] Processing:', file.name);
    
    var reader = new FileReader();
    reader.onload = function(e) {
        var content = e.target.result;
        parseCSV(content);
    };
    reader.readAsText(file, 'UTF-8');
}

/**
 * Parse CSV content (pipe delimiter)
 */
function parseCSV(content) {
    var lines = content.split('\n');
    var headers = lines[0].split('|').map(h => h.trim());
    
    CSVData = [];
    for (var i = 1; i < lines.length; i++) {
        var line = lines[i].trim();
        if (!line || line.startsWith('#')) continue;
        
        var values = line.split('|');
        var row = {};
        for (var j = 0; j < headers.length; j++) {
            row[headers[j]] = values[j] ? values[j].trim() : '';
        }
        
        if (row.id) {
            CSVData.push(row);
        }
    }
    
    console.log('[CSV] Parsed:', CSVData.length, 'places');
    showCSVPreview();
}

/**
 * Show CSV preview table
 */
function showCSVPreview() {
    var preview = document.getElementById('csv-preview');
    var tbody = document.getElementById('csv-preview-body');
    
    if (!tbody) return;
    
    // Show preview section
    if (preview) preview.classList.remove('hidden');
    
    // Build preview (first 5 rows)
    var html = '';
    for (var i = 0; i < Math.min(CSVData.length, 5); i++) {
        var row = CSVData[i];
        html += '<tr>';
        html += '<td>' + (row.id || '-') + '</td>';
        html += '<td>' + (row.nameVietnamese || '-') + '</td>';
        html += '<td>' + (row.nameJapanese || '-') + '</td>';
        html += '<td>' + (row.nameChinese || '-') + '</td>';
        html += '<td>' + (row.lat || '-') + ',' + (row.lon || '-') + '</td>';
        
        // Show sources
        var sources = [];
        if (row.dila_id) sources.push('DILA');
        if (row.wikidata_id) sources.push('Wiki');
        if (row.stardict_id) sources.push('StarDict');
        if (row.bkg_id) sources.push('Phả Hệ');
        html += '<td>' + (sources.length ? sources.join(', ') : '-') + '</td>';
        
        html += '</tr>';
    }
    
    tbody.innerHTML = html;
    console.log('[CSV] Preview shown');
}

/**
 * Validate CSV data
 */
function validateCSV() {
    console.log('[CSV] Validating...');
    
    var errors = [];
    for (var i = 0; i < CSVData.length; i++) {
        var row = CSVData[i];
        
        // Required fields
        if (!row.id) errors.push('Row ' + (i+1) + ': Missing ID');
        if (!row.nameVietnamese) errors.push('Row ' + (i+1) + ': Missing Vietnamese name');
        
        // GPS validation
        if (row.lat && isNaN(parseFloat(row.lat))) errors.push('Row ' + (i+1) + ': Invalid lat');
        if (row.lon && isNaN(parseFloat(row.lon))) errors.push('Row ' + (i+1) + ': Invalid lon');
    }
    
    if (errors.length > 0) {
        alert('[CSV] Validation errors:\n' + errors.join('\n'));
    } else {
        alert('[CSV] Validation passed! ' + CSVData.length + ' places ready to import.');
    }
    
    console.log('[CSV] Validation:', errors.length ? 'FAILED' : 'PASSED');
    return errors.length === 0;
}

/**
 * Import CSV to GraphDB
 */
function importCSV() {
    if (!validateCSV()) return;
    
    console.log('[CSV] Importing to GraphDB...');
    
    // Convert to TTL format (simplified - send as JSON to server)
    var payload = {
        places: CSVData,
        source: 'CSV Import',
        date: new Date().toISOString()
    };
    
    fetch('/daoanh/api/admin/import-csv', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        console.log('[CSV] Import result:', data);
        alert('[CSV] Import complete! ' + data.imported + ' places.');
        
        // Reload dashboard
        AdminApp.loadDashboard();
    })
    .catch(function(err) {
        console.error('[CSV] Import error:', err);
        alert('[CSV] Import failed: ' + err.message);
    });
}