/**
 * Admin Dashboard - System Monitoring & Management
 * Real-time stats, logs, and system management
 * 
 * @version: v4.22 (2026-04-10)
 * @file: src/js/admin/dashboard.js
 */

const AdminDashboard = (function() {
    'use strict';

    // Dashboard elements
    let statsPanel = null;
    let logsPanel = null;
    let consolePanel = null;

    // Configuration
    const CONFIG = {
        refreshInterval: 5000,
        maxLogs: 100,
        showDebug: false
    };

    // Stats storage
    let stats = {
        requests: 0,
        errors: 0,
        cacheHits: 0,
        cacheMisses: 0,
        avgResponseTime: 0,
        uptime: Date.now()
    };

    // Log buffer
    let logs = [];

    /**
     * Initialize dashboard
     * @param {object} options - Configuration options
     */
    function init(options) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        // Create dashboard UI
        createDashboard();

        // Start refresh loop
        startRefreshLoop();

        log('[AdminDashboard] Initialized');

        return {
            log: logMessage,
            updateStats: updateStats,
            getStats: getStats
        };
    }

    /**
     * Create dashboard UI
     */
    function createDashboard() {
        // Create container
        const container = document.createElement('div');
        container.id = 'admin-dashboard';
        container.className = 'admin-dashboard';
        container.style.cssText = `
            position: fixed;
            bottom: 0;
            right: 0;
            width: 350px;
            max-height: 400px;
            background: #1e293b;
            border-top-left-radius: 12px;
            border-top: 2px solid #d97706;
            z-index: 10000;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            color: #f8fafc;
            overflow: hidden;
        `;

        // Header
        const header = document.createElement('div');
        header.className = 'dashboard-header';
        header.style.cssText = `
            padding: 8px 12px;
            background: #0f172a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        `;
        header.innerHTML = `
            <span style="color: #d97706; font-weight: bold;">📊 Admin Dashboard</span>
            <span id="dashboard-toggle">▼</span>
        `;
        header.onclick = toggleDashboard;

        // Content
        const content = document.createElement('div');
        content.id = 'dashboard-content';
        content.style.cssText = `
            padding: 12px;
            display: block;
            max-height: 350px;
            overflow-y: auto;
        `;

        // Stats panel
        statsPanel = document.createElement('div');
        statsPanel.className = 'stats-panel';
        statsPanel.innerHTML = getStatsHTML();

        // Logs panel
        logsPanel = document.createElement('div');
        logsPanel.className = 'logs-panel';
        logsPanel.innerHTML = '<div class="logs-title">Recent Logs</div>';

        content.appendChild(statsPanel);
        content.appendChild(logsPanel);

        container.appendChild(header);
        container.appendChild(content);

        document.body.appendChild(container);
    }

    /**
     * Get stats HTML
     */
    function getStatsHTML() {
        const uptime = Math.floor((Date.now() - stats.uptime) / 1000);
        
        return `
            <div class="stats-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div class="stat-item" style="background: #334155; padding: 8px; border-radius: 4px;">
                    <div style="color: #94a3b8;">Requests</div>
                    <div style="color: #d97706; font-size: 18px; font-weight: bold;">${stats.requests}</div>
                </div>
                <div class="stat-item" style="background: #334155; padding: 8px; border-radius: 4px;">
                    <div style="color: #94a3b8;">Errors</div>
                    <div style="color: #ef4444; font-size: 18px; font-weight: bold;">${stats.errors}</div>
                </div>
                <div class="stat-item" style="background: #334155; padding: 8px; border-radius: 4px;">
                    <div style="color: #94a3b8;">Cache Hits</div>
                    <div style="color: #22c55e; font-size: 18px; font-weight: bold;">${stats.cacheHits}</div>
                </div>
                <div class="stat-item" style="background: #334155; padding: 8px; border-radius: 4px;">
                    <div style="color: #94a3b8;">Uptime</div>
                    <div style="color: #f8fafc; font-size: 18px; font-weight: bold;">${formatUptime(uptime)}</div>
                </div>
            </div>
        `;
    }

    /**
     * Toggle dashboard visibility
     */
    function toggleDashboard() {
        const content = document.getElementById('dashboard-content');
        const toggle = document.getElementById('dashboard-toggle');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.textContent = '▼';
        } else {
            content.style.display = 'none';
            toggle.textContent = '▲';
        }
    }

    /**
     * Update stats
     * @param {object} newStats 
     */
    function updateStats(newStats) {
        stats = { ...stats, ...newStats };
        
        if (statsPanel) {
            statsPanel.innerHTML = getStatsHTML();
        }
    }

    /**
     * Get stats
     */
    function getStats() {
        return { ...stats };
    }

    /**
     * Log message
     * @param {string} message 
     * @param {string} level - info, warn, error
     */
    function logMessage(message, level = 'info') {
        const entry = {
            time: new Date().toISOString(),
            message: message,
            level: level
        };

        logs.unshift(entry);

        // Trim logs
        if (logs.length > CONFIG.maxLogs) {
            logs = logs.slice(0, CONFIG.maxLogs);
        }

        // Update UI
        if (logsPanel) {
            logsPanel.innerHTML = logs.map(log => 
                `<div class="log-entry log-${log.level}" style="padding: 4px 0; border-bottom: 1px solid #334155;">
                    <span style="color: #64748b;">[${log.time.split('T')[1].slice(0,8)}]</span>
                    <span style="color: ${log.level === 'error' ? '#ef4444' : log.level === 'warn' ? '#f59e0b' : '#94a3b8'}">${log.message}</span>
                </div>`
            ).join('');
        }
    }

    /**
     * Start refresh loop
     */
    function startRefreshLoop() {
        setInterval(() => {
            if (statsPanel) {
                statsPanel.innerHTML = getStatsHTML();
            }
        }, CONFIG.refreshInterval);
    }

    /**
     * Format uptime
     */
    function formatUptime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        return `${h}h ${m}m ${s}s`;
    }

    /**
     * Log helper
     */
    function log(...args) {
        if (CONFIG.showDebug) {
            console.log('[AdminDashboard]', ...args);
        }
    }

    // Public API
    return {
        init: init,
        log: logMessage,
        updateStats: updateStats,
        getStats: getStats
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminDashboard;
}
