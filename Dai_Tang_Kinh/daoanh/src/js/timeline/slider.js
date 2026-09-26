/**
 * Timeline Slider - GIS Timeline Component
 * Time slider for filtering entities by year/century
 * 
 * @version: v4.1a (2026-04-10)
 * @file: src/js/timeline/slider.js
 */

const TimelineSlider = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        minYear: -600,     // Earliest Buddhist year
        maxYear: 2026,     // Current year
        defaultYear: 1000,  // Default starting year
        step: 1,           // Year step
        centuryStep: 100,   // Century step for large ranges
        animationDuration: 300,
        presets: [
            { label: 'Thời Đức Phật', start: -600, end: -400 },
            { label: 'Truyền sang Trung Hoa', start: 67, end: 500 },
            { label: 'Thời Lý Trần', start: 1009, end: 1400 },
            { label: 'Truyền sang Việt Nam', start: 580, end: 700 },
            { label: 'Thời Nguyễn', start: 1802, end: 1945 }
        ]
    };

    let container = null;
    let currentYear = CONFIG.defaultYear;
    let onChangeCallback = null;
    let isPlaying = false;
    let playInterval = null;

    /**
     * Initialize timeline slider
     * @param {string} containerId - DOM container ID
     * @param {object} options - Configuration options
     */
    function init(containerId, options = {}) {
        if (options) {
            Object.assign(CONFIG, options);
        }

        container = document.getElementById(containerId);
        if (!container) {
            console.error('[TimelineSlider] Container not found:', containerId);
            return;
        }

        render();
        setYear(CONFIG.defaultYear);

        console.log('[TimelineSlider] Initialized');
    }

    /**
     * Render the slider UI
     */
    function render() {
        if (!container) return;

        container.innerHTML = `
            <div class="timeline-slider">
                <div class="timeline-header">
                    <span class="timeline-label">Năm:</span>
                    <span class="timeline-year" id="timeline-current-year">${currentYear}</span>
                    <span class="timeline-century" id="timeline-century"></span>
                </div>
                
                <div class="timeline-track-container">
                    <input type="range" 
                           class="timeline-range" 
                           id="timeline-range"
                           min="${CONFIG.minYear}"
                           max="${CONFIG.maxYear}"
                           value="${currentYear}"
                           step="${CONFIG.step}">
                    
                    <div class="timeline-markers" id="timeline-markers"></div>
                </div>
                
                <div class="timeline-controls">
                    <button class="timeline-btn" id="timeline-prev" title="Thế kỷ trước">◀◀</button>
                    <button class="timeline-btn" id="timeline-play" title="Chạy timeline">▶</button>
                    <button class="timeline-btn" id="timeline-next" title="Thế kỷ sau">▶▶</button>
                    <button class="timeline-btn" id="timeline-reset" title="Reset">↺</button>
                </div>
                
                <div class="timeline-presets" id="timeline-presets"></div>
            </div>
        `;

        // Add styles
        addStyles();

        // Bind events
        bindEvents();

        // Render presets
        renderPresets();

        // Render markers
        renderMarkers();
    }

    /**
     * Add CSS styles
     */
    function addStyles() {
        if (document.getElementById('timeline-styles')) return;

        const style = document.createElement('style');
        style.id = 'timeline-styles';
        style.textContent = `
            .timeline-slider {
                padding: 12px;
                background: #1e293b;
                border-radius: 8px;
                color: #f8fafc;
                font-family: 'Inter', sans-serif;
            }
            
            .timeline-header {
                display: flex;
                align-items: baseline;
                gap: 8px;
                margin-bottom: 12px;
            }
            
            .timeline-label {
                font-size: 12px;
                color: #94a3b8;
            }
            
            .timeline-year {
                font-size: 24px;
                font-weight: bold;
                color: #d97706;
            }
            
            .timeline-century {
                font-size: 14px;
                color: #94a3b8;
            }
            
            .timeline-track-container {
                position: relative;
                margin: 16px 0;
            }
            
            .timeline-range {
                width: 100%;
                height: 8px;
                -webkit-appearance: none;
                background: linear-gradient(to right, #d97706 0%, #d97706 var(--progress), #334155 var(--progress), #334155 100%);
                border-radius: 4px;
                outline: none;
            }
            
            .timeline-range::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 20px;
                height: 20px;
                background: #d97706;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            }
            
            .timeline-controls {
                display: flex;
                justify-content: center;
                gap: 8px;
                margin-top: 12px;
            }
            
            .timeline-btn {
                padding: 8px 12px;
                background: #334155;
                border: none;
                border-radius: 4px;
                color: #f8fafc;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .timeline-btn:hover {
                background: #475569;
            }
            
            .timeline-btn.active {
                background: #d97706;
            }
            
            .timeline-presets {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 16px;
                padding-top: 12px;
                border-top: 1px solid #334155;
            }
            
            .timeline-preset {
                padding: 6px 12px;
                background: #334155;
                border: none;
                border-radius: 4px;
                color: #f8fafc;
                font-size: 12px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .timeline-preset:hover {
                background: #475569;
            }
            
            .timeline-preset.active {
                background: #d97706;
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Bind event listeners
     */
    function bindEvents() {
        const range = document.getElementById('timeline-range');
        if (range) {
            range.addEventListener('input', (e) => {
                setYear(parseInt(e.target.value));
            });
        }

        const playBtn = document.getElementById('timeline-play');
        if (playBtn) {
            playBtn.addEventListener('click', togglePlay);
        }

        const prevBtn = document.getElementById('timeline-prev');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => jumpCentury(-1));
        }

        const nextBtn = document.getElementById('timeline-next');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => jumpCentury(1));
        }

        const resetBtn = document.getElementById('timeline-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', reset);
        }
    }

    /**
     * Render preset buttons
     */
    function renderPresets() {
        const presetsContainer = document.getElementById('timeline-presets');
        if (!presetsContainer) return;

        presetsContainer.innerHTML = CONFIG.presets.map((preset, i) => 
            `<button class="timeline-preset" data-index="${i}">${preset.label}</button>`
        ).join('');

        presetsContainer.querySelectorAll('.timeline-preset').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                const preset = CONFIG.presets[index];
                setYear(preset.start);
            });
        });
    }

    /**
     * Render timeline markers
     */
    function renderMarkers() {
        const markersContainer = document.getElementById('timeline-markers');
        if (!markersContainer) return;

        // Add century markers
        const markers = [];
        for (let year = CONFIG.minYear; year <= CONFIG.maxYear; year += 100) {
            markers.push({
                year: year,
                label: year < 0 ? `TCN ${Math.abs(year)}` : year
            });
        }

        markersContainer.innerHTML = markers.map(m => 
            `<span class="marker" style="left: ${((m.year - CONFIG.minYear) / (CONFIG.maxYear - CONFIG.minYear)) * 100}%">${m.label}</span>`
        ).join('');
    }

    /**
     * Set current year
     * @param {number} year 
     */
    function setYear(year) {
        currentYear = Math.max(CONFIG.minYear, Math.min(CONFIG.maxYear, year));
        
        // Update display
        const yearDisplay = document.getElementById('timeline-current-year');
        const centuryDisplay = document.getElementById('timeline-century');
        const rangeInput = document.getElementById('timeline-range');
        
        if (yearDisplay) {
            yearDisplay.textContent = currentYear < 0 ? `TCN ${Math.abs(currentYear)}` : currentYear;
        }
        
        if (centuryDisplay) {
            const century = Math.floor((currentYear - 1) / 100) + 1;
            centuryDisplay.textContent = ` (thế kỷ ${century})`;
        }
        
        if (rangeInput) {
            rangeInput.value = currentYear;
            // Update progress bar
            const progress = ((currentYear - CONFIG.minYear) / (CONFIG.maxYear - CONFIG.minYear)) * 100;
            rangeInput.style.setProperty('--progress', `${progress}%`);
        }
        
        // Callback
        if (onChangeCallback) {
            onChangeCallback(currentYear);
        }
    }

    /**
     * Get current year
     * @returns {number}
     */
    function getYear() {
        return currentYear;
    }

    /**
     * Set year change callback
     * @param {function} callback 
     */
    function onChange(callback) {
        onChangeCallback = callback;
    }

    /**
     * Toggle play/pause
     */
    function togglePlay() {
        if (isPlaying) {
            pause();
        } else {
            play();
        }
    }

    /**
     * Start playing
     */
    function play() {
        if (isPlaying) return;
        
        isPlaying = true;
        
        const playBtn = document.getElementById('timeline-play');
        if (playBtn) {
            playBtn.textContent = '⏸';
            playBtn.classList.add('active');
        }

        playInterval = setInterval(() => {
            if (currentYear >= CONFIG.maxYear) {
                pause();
                return;
            }
            setYear(currentYear + 10); // Advance 10 years per tick
        }, 500);
    }

    /**
     * Pause playing
     */
    function pause() {
        isPlaying = false;
        
        if (playInterval) {
            clearInterval(playInterval);
            playInterval = null;
        }

        const playBtn = document.getElementById('timeline-play');
        if (playBtn) {
            playBtn.textContent = '▶';
            playBtn.classList.remove('active');
        }
    }

    /**
     * Jump by centuries
     * @param {number} direction - -1 or 1
     */
    function jumpCentury(direction) {
        const newYear = currentYear + (direction * 100);
        setYear(newYear);
    }

    /**
     * Reset to default
     */
    function reset() {
        pause();
        setYear(CONFIG.defaultYear);
    }

    /**
     * Get configuration
     */
    function getConfig() {
        return { ...CONFIG };
    }

    // Public API
    return {
        init: init,
        setYear: setYear,
        getYear: getYear,
        onChange: onChange,
        play: play,
        pause: pause,
        togglePlay: togglePlay,
        reset: reset,
        getConfig: getConfig
    };
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimelineSlider;
}
