// Text Comparison - Dual panel + TEI lb alignment + Source tracking
const TextComparison = {
    leftPanel: null,
    rightPanel: null,
    currentSource: null,
    
    init: function() {
        this.leftPanel = document.getElementById('text-panel-left');
        this.rightPanel = document.getElementById('text-panel-right');
        
        if (this.leftPanel && this.rightPanel) {
            this.setupPanelContent();
            this.addSyncScroll();
        }
    },
    
    setupPanelContent: function() {
        // Sample data - in production would come from CBETA/DILA
        const hanText = `初，達磨大師至少林寺，面壁九年，終日默坐，人莫之測，謂之壁觀婆羅門。`;
        const vietText = `Thuở ban đầu, Đại sư Đạt Ma đến chùa Thiếu Lâm, diện bích chín năm, suốt ngày ngồi lặng yên, người đời không ai lường được, gọi Ngài là vị Bà-la-môn quán vách.`;

        // Check if panels have content, if not add default
        if (this.leftPanel && !this.leftPanel.innerHTML.trim()) {
            this.leftPanel.innerHTML = `<h5>Hán Văn (CBETA)</h5><p class="han-text">${hanText}</p>`;
        }
        
        if (this.rightPanel && !this.rightPanel.innerHTML.trim()) {
            this.rightPanel.innerHTML = `<h5>Bản dịch Việt ngữ</h5><p class="viet-text">${vietText}</p>`;
        }
    },
    
    addSyncScroll: function() {
        if (!this.leftPanel || !this.rightPanel) return;
        
        this.leftPanel.addEventListener('scroll', () => {
            this.rightPanel.scrollTop = this.leftPanel.scrollTop;
        });
        
        this.rightPanel.addEventListener('scroll', () => {
            this.leftPanel.scrollTop = this.rightPanel.scrollTop;
        });
    },
    
    loadSource: function(sourceId) {
        this.currentSource = sourceId;
        
        // Simulate loading text from CBETA/DILA
        const sources = {
            'T51n2076': {
                han: '初，達磨大師至少林寺，面壁九年...',
                viet: 'Thuở ban đầu, Đại sư Đạt Ma...'
            },
            'X1234': {
                han: '爾時世尊在給孤獨園...',
                viet: 'Bấy giờ Đức Thế Tôn tại vườn Cấp Cô Độc...'
            }
        };
        
        const data = sources[sourceId];
        if (data) {
            if (this.leftPanel) {
                this.leftPanel.innerHTML = `<h5>Hán Văn (${sourceId})</h5><p class="han-text">${data.han}</p>`;
            }
            if (this.rightPanel) {
                this.rightPanel.innerHTML = `<h5>Bản dịch Việt ngữ</h5><p class="viet-text">${data.viet}</p>`;
            }
        }
    },
    
    alignLines: function() {
        // TEI lb alignment - split text by line breaks
        const leftText = this.leftPanel?.querySelector('.han-text');
        const rightText = this.rightPanel?.querySelector('.viet-text');
        
        if (leftText && rightText) {
            const leftLines = leftText.innerText.split('\n');
            const rightLines = rightText.innerText.split('\n');
            
            // Display with alignment markers
            leftText.innerHTML = leftLines.map((line, i) => 
                `<div class="text-line" data-line="${i}">${line}</div>`
            ).join('');
            
            rightText.innerHTML = rightLines.map((line, i) => 
                `<div class="text-line" data-line="${i}">${line}</div>`
            ).join('');
            
            // Add line number sync on click
            this.leftPanel?.querySelectorAll('.text-line').forEach(line => {
                line.addEventListener('click', (e) => {
                    const lineNum = e.target.dataset.line;
                    this.highlightLine(lineNum, 'left');
                });
            });
            
            this.rightPanel?.querySelectorAll('.text-line').forEach(line => {
                line.addEventListener('click', (e) => {
                    const lineNum = e.target.dataset.line;
                    this.highlightLine(lineNum, 'right');
                });
            });
        }
    },
    
    highlightLine: function(lineNum, panel) {
        // Remove previous highlights
        document.querySelectorAll('.text-line.active').forEach(el => {
            el.classList.remove('active');
        });
        
        // Add highlight to both panels
        if (panel === 'left' || panel === 'both') {
            this.leftPanel?.querySelector(`.text-line[data-line="${lineNum}"]`)?.classList.add('active');
        }
        if (panel === 'right' || panel === 'both') {
            this.rightPanel?.querySelector(`.text-line[data-line="${lineNum}"]`)?.classList.add('active');
        }
    },
    
    showSourceInfo: function() {
        // Show DILA/CBETA source information
        const sourceInfo = {
            'T51n2076': {
                cbeta: 'T51n2076_p0217',
                dila: 'A000123',
                title: 'Tứ Thư Thiền',
                taisho: '大正藏 No.2076'
            }
        };
        
        // Dispatch event for UI to display
        console.log('📚 Source loaded:', this.currentSource);
    }
};

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => TextComparison.init(), 500);
});

console.log("📚 TextComparison module loaded");