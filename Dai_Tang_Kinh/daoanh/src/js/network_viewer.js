// Lineage & Network Viewer - Vis.js integration
const NetworkViewer = {
    container: null,
    network: null,
    currentNode: null,
    nodes: [],
    edges: [],
    
    init: function() {
        this.createModal();
    },
    
    createModal: function() {
        this.container = document.createElement('div');
        this.container.id = 'network-modal';
        this.container.className = 'network-modal hidden';
        this.container.innerHTML = `
            <div class="network-modal-content">
                <div class="network-header">
                    <h3>🔗 Sơ đồ quan hệ truyền thừa</h3>
                    <button class="network-close" onclick="NetworkViewer.close()">✕</button>
                </div>
                <div class="network-info">
                    <span class="network-node-label">Node trung tâm:</span>
                    <span id="network-center-name" class="network-center-name">-</span>
                </div>
                <div id="network-graph" class="network-graph"></div>
                <div class="network-legend">
                    <span class="legend-node teacher">⬤ Thầy</span>
                    <span class="legend-node student">◯ Trò</span>
                    <span class="legend-node center">★ Trung tâm</span>
                </div>
            </div>
        `;
        document.body.appendChild(this.container);
        
        // Load Vis.js from CDN
        this.loadVisJS();
    },
    
    loadVisJS: function() {
        if (window.vis) return;
        
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/vis-network/standalone/umd/vis-network.min.js';
        script.onload = () => console.log('✅ Vis.js loaded');
        document.head.appendChild(script);
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/vis-network/styles/vis-network.min.css';
        document.head.appendChild(link);
    },
    
    show: function(centerName) {
        this.currentNode = centerName;
        this.buildNetwork(centerName);
        
        document.getElementById('network-center-name').textContent = centerName;
        this.container.classList.remove('hidden');
        
        // Initialize network after modal is shown
        setTimeout(() => this.initNetwork(), 100);
    },
    
    close: function() {
        this.container.classList.add('hidden');
        if (this.network) {
            this.network.destroy();
            this.network = null;
        }
    },
    
    buildNetwork: function(centerName) {
        // Build nodes and edges based on critical places/monks data
        this.nodes = [];
        this.edges = [];
        
        // Center node
        this.nodes.push({
            id: centerName,
            label: centerName,
            color: '#fbbf24',
            size: 30,
            font: { size: 16, color: '#020617' },
            shape: 'star'
        });
        
        // Find related monks/places
        if (SearchApp && SearchApp.criticalPlaces) {
            const centerEntity = SearchApp.criticalPlaces.find(p => 
                p.vietnamese === centerName || p.searchKey === centerName
            );
            
            if (centerEntity && centerEntity.relatedMonks) {
                centerEntity.relatedMonks.forEach((monk, index) => {
                    // Add related monk as node
                    this.nodes.push({
                        id: monk,
                        label: monk,
                        color: '#22c55e',
                        size: 20,
                        font: { size: 14 }
                    });
                    
                    // Add edge (teacher relationship)
                    this.edges.push({
                        from: monk,
                        to: centerName,
                        arrows: 'to',
                        color: '#64748b',
                        width: 2
                    });
                });
            }
        }
        
        // If no related monks found, add sample data for demo
        if (this.nodes.length === 1) {
            this.addSampleNetwork(centerName);
        }
    },
    
    addSampleNetwork: function(centerName) {
        // Sample lineage for demo
        const sampleLineages = {
            'Lục Tổ': ['Hoằng Nhẫn', 'Trung Quang', 'Pháp Loa'],
            'Huệ Năng': ['Hoằng Nhẫn', 'Nam Tông'],
            'Thiếu Lâm Tự': ['Bồ Đề Đạt Ma', 'Huệ Khả'],
            'Bồ Đề Đạt Ma': ['Huệ Khả'],
            'Trần Nhân Tông': ['Khip', 'Pháp Loa'],
            'Yên Tử': ['Trần Nhân Tông', 'Quảng Nghiêm']
        };
        
        const related = sampleLineages[centerName] || ['Hoằng Nhẫn', 'Nam Tông'];
        
        related.forEach(monk => {
            this.nodes.push({
                id: monk,
                label: monk,
                color: '#22c55e',
                size: 20,
                font: { size: 14 }
            });
            
            this.edges.push({
                from: monk,
                to: centerName,
                arrows: 'to',
                color: '#64748b',
                width: 2
            });
        });
    },
    
    initNetwork: function() {
        const graphDiv = document.getElementById('network-graph');
        if (!graphDiv || !window.vis) return;
        
        const data = {
            nodes: new window.vis.DataSet(this.nodes),
            edges: new window.vis.DataSet(this.edges)
        };
        
        const options = {
            nodes: {
                shape: 'dot',
                font: { face: 'Noto Serif TC, sans-serif' }
            },
            edges: {
                smooth: { type: 'continuous' }
            },
            physics: {
                stabilization: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    springLength: 150
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200
            }
        };
        
        this.network = new window.vis.Network(graphDiv, data, options);
        
        // Click handler to navigate
        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                this.navigateTo(nodeId);
            }
        });
    },
    
    navigateTo: function(nodeId) {
        // Move center to clicked node
        this.close();
        
        // Trigger search for this monk
        if (SearchApp) {
            SearchApp.handleMonkClick({ name: nodeId });
        }
        
        // Or show network for new node
        this.show(nodeId);
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => NetworkViewer.init(), 1000);
});

console.log("🔗 NetworkViewer module loaded");