// Main application logic
var app = (function() {
    // Auth placeholder - check if defined before use
    var Auth = window.Auth || { isLoggedIn: function() { return false; }, getUsername: function() { return ''; }, login: function() {}, logout: function() {} };
    
    return {
        data: [],
        filteredData: [],
        table: null,
        
        /**
         * Initialize the application
         */
        init: function() {
            // Check authentication (Auth may not be defined in non-admin views)
            try {
                var auth = Auth.isLoggedIn();
                if (!auth) {
                    this.showLogin();
                } else {
                    this.showDashboard();
                    this.loadData();
                }
            } catch(e) {
                // Auth not available, skip auth check
                console.log('[app] Auth not available');
            }
        },
    
    /**
     * Setup event listeners
     */
    setupEvents: function() {
        // Login form
        document.getElementById("login-form").addEventListener("submit", (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // Edit form
        document.getElementById("edit-form").addEventListener("submit", (e) => {
            e.preventDefault();
            this.handleEdit();
        });
    },
    
    /**
     * Show login section
     */
    showLogin: function() {
        document.getElementById("login-section").classList.remove("hidden");
        document.getElementById("dashboard-section").classList.add("hidden");
    },
    
    /**
     * Show dashboard section
     */
    showDashboard: function() {
        document.getElementById("login-section").classList.add("hidden");
        document.getElementById("dashboard-section").classList.remove("hidden");
        document.getElementById("user-info").textContent = '👤 ' + Auth.getUsername();
    },
    
    /**
     * Handle login
     */
    handleLogin: async function() {
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        
        const btn = document.querySelector("#login-form button");
        btn.textContent = "⏳ Đang đăng nhập...";
        btn.disabled = true;
        
        try {
            await Auth.login(username, password);
            this.showDashboard();
            this.loadData();
        } catch (error) {
            alert("❌ Đăng nhập thất bại. Kiểm tra username/password.");
        } finally {
            btn.textContent = "Login";
            btn.disabled = false;
        }
    },
    
    /**
     * Handle logout
     */
    logout: function() {
        Auth.logout();
    },
    
    /**
     * Load data from local JSON file - Zero-RAM optimized
     */
    loadData: function() {
        // Check file size first - use streaming for large files
        fetch(CONFIG.JSON_FILE, { method: 'HEAD' })
            .then(response => {
                const contentLength = response.headers.get('content-length');
                const fileSize = parseInt(contentLength || 0);
                
                // If file > 5MB, use streaming/pagination
                if (fileSize > 5 * 1024 * 1024) {
                    console.log(`[Zero-RAM] Large file detected: ${(fileSize/1024/1024).toFixed(2)}MB - Using pagination`);
                    return this.loadDataPaginated();
                }
                
                // Smaller file: OK to load with limit
                return this.loadDataDirect();
            })
            .catch(error => {
                console.error("Error checking file size:", error);
                this.loadDataDirect();
            });
    },
    
    /**
     * Direct load for small files (<5MB)
     */
    loadDataDirect: function() {
        fetch(CONFIG.JSON_FILE)
            .then(response => {
                if (!response.ok) throw new Error("Cannot load JSON file");
                return response.json();
            })
            .then(data => {
                // Limit initial load to 500 items
                this.data = (data.places || []).slice(0, 500);
                this.filteredData = [...this.data];
                this.renderTable();
                this.updateStats();
                console.log(`[Zero-RAM] Loaded ${this.data.length} places (limited)`);
            })
            .catch(error => {
                console.error("Error loading data:", error);
                this.loadFromGraphDB();
            });
    },
    
    /**
     * Paginated load for large files - Zero-RAM pattern
     */
    loadDataPaginated: async function() {
        try {
            const LIMIT = 300;
            let offset = 0;
            let hasMore = true;
            
            this.data = [];
            
            while (hasMore && offset < 1500) { // Max 5 pages
                const response = await fetch(`${CONFIG.JSON_FILE}?offset=${offset}&limit=${LIMIT}`);
                if (!response.ok) break;
                
                const chunk = await response.json();
                const items = chunk.places || [];
                
                if (items.length > 0) {
                    this.data.push(...items);
                    offset += LIMIT;
                    console.log(`[Zero-RAM] Loaded page ${offset/LIMIT}: ${items.length} items`);
                }
                
                if (items.length < LIMIT) hasMore = false;
            }
            
            this.filteredData = [...this.data];
            this.renderTable();
            this.updateStats();
            console.log(`[Zero-RAM] Total loaded: ${this.data.length} places`);
            
        } catch (error) {
            console.error("Error loading paginated data:", error);
            this.loadFromGraphDB();
        }
    },
    
    /**
     * Load data from GraphDB (fallback)
     */
    loadFromGraphDB: async function() {
        try {
            const result = await GraphDB.getAllPlaces();
            this.data = this.parseGraphDBResult(result);
            this.filteredData = [...this.data];
            this.renderTable();
            this.updateStats();
        } catch (error) {
            console.error("Error loading from GraphDB:", error);
            alert("Không thể tải dữ liệu. Vui lòng kiểm tra kết nối.");
        }
    },
    
    /**
     * Parse GraphDB result to app format
     */
    parseGraphDBResult: function(result) {
        if (!result.results || !result.results.bindings) return [];
        
        return result.results.bindings.map(binding => ({
            id: binding.id?.value || "",
            nameChinese: binding.nameZh?.value || "",
            nameVietnamese: binding.nameVi?.value || "",
            lat: binding.lat?.value || "",
            lon: binding.lon?.value || "",
            country: binding.country?.value || "",
            description: binding.desc?.value || "",
            source: binding.source?.value || "DILA"
        }));
    },
    
    /**
     * Render DataTable
     */
    renderTable: function() {
        const tbody = document.querySelector("#places-table tbody");
        tbody.innerHTML = "";
        
        // Show first 100 items for performance
        const displayData = this.filteredData.slice(0, 100);
        
        displayData.forEach(place => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${place.id || "-"}</td>
                <td>${place.nameChinese || "-"}</td>
                <td>${place.nameVietnamese || "<em style='color:#999'>Chưa có</em>"}</td>
                <td><span class="badge badge-${place.source}">${place.source}</span></td>
                <td>${place.lat && place.lon ? `${place.lat}, ${place.lon}` : "<em>Chưa có</em>"}</td>
                <td>${place.country || "-"}</td>
                <td>
                    <button onclick="app.editPlace('${place.id}')" class="btn-small">✏️ Edit</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Initialize DataTables
        if (this.table) this.table.destroy();
        this.table = $("#places-table").DataTable({
            pageLength: 50,
            language: {
                url: "lib/datatables/i18n/Vietnamese.json"
            }
        });
    },
    
    /**
     * Update statistics
     */
    updateStats: function() {
        const total = this.data.length;
        const cbeta = this.data.filter(p => p.source === "CBETA").length;
        const dila = this.data.filter(p => p.source === "DILA").length;
        const vietnamese = this.data.filter(p => p.nameVietnamese).length;
        
        document.getElementById("total-places").textContent = total;
        document.getElementById("cbeta-places").textContent = cbeta;
        document.getElementById("dila-places").textContent = dila;
        document.getElementById("vietnamese-places").textContent = vietnamese;
    },
    
    /**
     * Search
     */
    search: function() {
        const query = document.getElementById("search").value.toLowerCase();
        this.filterData();
    },
    
    /**
     * Filter data
     */
    filter: function() {
        this.filterData();
    },
    
    /**
     * Filter data based on search and filters
     */
    filterData: function() {
        const query = document.getElementById("search").value.toLowerCase();
        const sourceFilter = document.getElementById("filter-source").value;
        const countryFilter = document.getElementById("filter-country").value;
        
        this.filteredData = this.data.filter(place => {
            // Search
            if (query && 
                !place.nameChinese?.toLowerCase().includes(query) && 
                !place.nameVietnamese?.toLowerCase().includes(query) &&
                !place.id?.toLowerCase().includes(query)) {
                return false;
            }
            
            // Source filter
            if (sourceFilter !== "all" && place.source !== sourceFilter) {
                return false;
            }
            
            // Country filter
            if (countryFilter !== "all" && place.country !== countryFilter) {
                return false;
            }
            
            return true;
        });
        
        this.renderTable();
    },
    
    /**
     * Edit place
     */
    editPlace: function(placeId) {
        const place = this.data.find(p => p.id === placeId);
        if (!place) return;
        
        document.getElementById("edit-id").value = place.id;
        document.getElementById("edit-name-zh").value = place.nameChinese || "";
        document.getElementById("edit-name-vi").value = place.nameVietnamese || "";
        document.getElementById("edit-desc-vi").value = place.description || "";
        document.getElementById("edit-gps").textContent = place.lat && place.lon ? 
            `${place.lat}, ${place.lon}` : "Chưa có GPS";
        
        document.getElementById("edit-modal").classList.remove("hidden");
    },
    
    /**
     * Close edit modal
     */
    closeEditModal: function() {
        document.getElementById("edit-modal").classList.add("hidden");
    },
    
    /**
     * Handle edit save
     */
    handleEdit: async function() {
        const placeId = document.getElementById("edit-id").value;
        const nameVi = document.getElementById("edit-name-vi").value;
        const descVi = document.getElementById("edit-desc-vi").value;
        
        try {
            // Update GraphDB
            if (nameVi) {
                await GraphDB.updateVietnameseName(placeId, nameVi);
            }
            if (descVi) {
                await GraphDB.updateVietnameseDesc(placeId, descVi);
            }
            
            alert("✅ Đã lưu vào GraphDB!");
            this.closeEditModal();
            this.loadData(); // Refresh
            
        } catch (error) {
            console.error("Error saving:", error);
            alert("❌ Lỗi khi lưu: " + error.message);
        }
    },
    
    /**
     * Export CSV
     */
    exportCSV: function() {
        const headers = ["ID", "Tên Hán", "Tên Việt", "GPS", "Quốc gia", "Mô tả"];
        const rows = this.data.map(p => [
            p.id,
            p.nameChinese,
            p.nameVietnamese,
            `${p.lat},${p.lon}`,
            p.country,
            p.description
        ]);
        
        const csv = [headers.join(","), ...rows.map(r => r.map(v => `"${v || ""}"`).join(","))].join("\n");
        
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "places_vietnamese.csv";
        a.click();
    },
    
    /**
     * Refresh JSON data
     */
    refreshData: function() {
        alert("🔄 Để refresh JSON, chạy script: python src/python/export_json.py");
    },
    
    /**
     * Show GPS compare modal
     */
    showCompare: function() {
        document.getElementById("compare-modal").classList.remove("hidden");
        document.getElementById("compare-results").innerHTML = "<p>⚠️ Chức năng GPS Compare đang được phát triển.</p><p>Sử dụng script: python src/python/compare_gps.py</p>";
    },
    
    /**
     * Close compare modal
     */
    closeCompareModal: function() {
        document.getElementById("compare-modal").classList.add("hidden");
    }
};

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    app.init();
});