/**
 * Response Formatter - AI Interpreter
 * Convert SPARQL results → text dễ hiểu
 * 
 * @version: v4.4 (2026-04-10)
 * @file: src/js/ai/response_formatter.js
 */

const ResponseFormatter = (function() {
    'use strict';

    /**
     * Format kết quả SPARQL → text tiếng Việt
     * @param {object} sparqlResult - Kết quả từ SPARQL endpoint
     * @param {object} originalQuery - Query gốc từ SemanticParser
     * @returns {object} - { text, html, data }
     */
    function format(sparqlResult, originalQuery) {
        if (!sparqlResult) {
            return { 
                text: 'Không có kết quả trả về.', 
                html: '<p>Không có kết quả trả về.</p>',
                data: [] 
            };
        }

        if (sparqlResult.error) {
            return {
                text: `Lỗi: ${sparqlResult.error}`,
                html: `<p class="error">Lỗi: ${sparqlResult.error}</p>`,
                data: []
            };
        }

        const bindings = sparqlResult.results?.bindings || [];
        
        if (bindings.length === 0) {
            return {
                text: 'Không tìm thấy kết quả phù hợp.',
                html: '<p>Không tìm thấy kết quả phù hợp.</p>',
                data: []
            };
        }

        // Format theo loại query
        const queryType = originalQuery?.type || 'default';
        
        switch (queryType) {
            case 'byLineage':
            case 'byLineageAndTime':
                return formatMonks(bindings, originalQuery);
            case 'byTimeRange':
                return formatMonksByTime(bindings, originalQuery);
            case 'teacherStudent':
                return formatTeacherStudent(bindings, originalQuery);
            case 'placeQuery':
                return formatPlaces(bindings, originalQuery);
            case 'timeline':
                return formatTimeline(bindings, originalQuery);
            default:
                return formatDefault(bindings, originalQuery);
        }
    }

    /**
     * Format danh sách thiền sư
     */
    function formatMonks(bindings, query) {
        const monks = bindings.map(b => ({
            name: b.label?.value || b.person?.value || 'Unknown',
            birth: b.birth?.value || '?',
            death: b.death?.value || '?'
        }));

        let text = `Tìm thấy ${monks.length} thiền sư:\n`;
        
        monks.forEach((m, i) => {
            const lifeSpan = m.birth !== '?' && m.death !== '?' 
                ? `(${m.birth} - ${m.death})` 
                : m.birth !== '?' ? `(sinh năm ${m.birth})` : '';
            text += `${i + 1}. ${m.name} ${lifeSpan}\n`;
        });

        const html = `
<h3>Tìm thấy ${monks.length} thiền sư</h3>
<ul class="monk-list">
${monks.map((m, i) => {
    const lifeSpan = m.birth !== '?' && m.death !== '?' 
        ? `<span class="lifespan">(${m.birth} - ${m.death})</span>` 
        : m.birth !== '?' ? `<span class="lifespan">(sinh năm ${m.birth})</span>` : '';
    return `<li><a href="/monk/${encodeURIComponent(m.name)}">${m.name}</a> ${lifeSpan}</li>`;
}).join('\n')}
</ul>`;

        return { text, html, data: monks };
    }

    /**
     * Format danh sách thiền sư theo thời gian
     */
    function formatMonksByTime(bindings, query) {
        const timeRange = query?.parsed?.timeRange;
        const timeStr = timeRange 
            ? `thế kỷ ${Math.floor(timeRange.min / 100) + 1}` 
            : 'thời gian yêu cầu';

        const monks = bindings.map(b => ({
            name: b.label?.value || b.person?.value || 'Unknown',
            birth: b.birth?.value || '?',
            death: b.death?.value || '?'
        }));

        let text = `Danh sách thiền sư trong ${timeStr} (${monks.length} vị):\n`;
        monks.forEach((m, i) => {
            text += `${i + 1}. ${m.name} (${m.birth} - ${m.death})\n`;
        });

        const html = `
<h3>Thiền sư ${timeStr}</h3>
<p>Tìm thấy ${monks.length} vị</p>
<ul>
${monks.map((m, i) => `<li>${m.name} (${m.birth} - ${m.death})</li>`).join('\n')}
</ul>`;

        return { text, html, data: monks };
    }

    /**
     * Format quan hệ thầy-trò
     */
    function formatTeacherStudent(bindings, query) {
        const pairs = bindings.map(b => ({
            teacher: b.teacher?.value || 'Unknown',
            student: b.student?.value || b.label?.value || 'Unknown'
        }));

        let text = `Tìm thấy ${pairs.length} cặp quan hệ thầy-trò:\n`;
        pairs.forEach((p, i) => {
            text += `${i + 1}. ${p.student} ← ${p.teacher}\n`;
        });

        const html = `
<h3>Quan hệ thầy-trò</h3>
<ul>
${pairs.map(p => `<li><strong>${p.student}</strong> là đệ tử của <strong>${p.teacher}</strong></li>`).join('\n')}
</ul>`;

        return { text, html, data: pairs };
    }

    /**
     * Format địa danh
     */
    function formatPlaces(bindings, query) {
        const places = bindings.map(b => ({
            name: b.label?.value || b.place?.value || 'Unknown',
            gps: b.gps?.value || null
        }));

        let text = `Tìm thấy ${places.length} địa danh:\n`;
        places.forEach((p, i) => {
            text += `${i + 1}. ${p.name}${p.gps ? ` (GPS: ${p.gps})` : ''}\n`;
        });

        const html = `
<h3>Địa danh</h3>
<ul>
${places.map(p => `<li>${p.name}${p.gps ? ` <small>(${p.gps})</small>` : ''}</li>`).join('\n')}
</ul>`;

        return { text, html, data: places };
    }

    /**
     * Format timeline
     */
    function formatTimeline(bindings, query) {
        const events = bindings.map(b => ({
            place: b.place?.value || 'Unknown',
            year: b.year?.value || '?',
            gps: b.gps?.value || null
        }));

        let text = `Timeline của ${query?.parsed?.entities?.[0]?.value || 'nhân vật'}:\n`;
        events.forEach((e, i) => {
            text += `- Năm ${e.year}: ${e.place}\n`;
        });

        const html = `
<h3>Timeline</h3>
<ul class="timeline">
${events.map(e => `
<li><span class="year">${e.year}</span> - ${e.place}</li>
`.trim()).join('\n')}
</ul>`;

        return { text, html, data: events };
    }

    /**
     * Format mặc định
     */
    function formatDefault(bindings, query) {
        const items = bindings.map(b => {
            const keys = Object.keys(b);
            return keys.reduce((obj, key) => {
                obj[key] = b[key].value;
                return obj;
            }, {});
        });

        let text = `Tìm thấy ${items.length} kết quả:\n`;
        items.forEach((item, i) => {
            text += `${i + 1}. ${JSON.stringify(item)}\n`;
        });

        const html = `
<h3>Kết quả</h3>
<pre>${JSON.stringify(items, null, 2)}</pre>`;

        return { text, html, data: items };
    }

    /**
     * Format error response
     * @param {string} message 
     * @returns {object}
     */
    function formatError(message) {
        return {
            text: `Lỗi: ${message}`,
            html: `<div class="error"><strong>Lỗi:</strong> ${message}</div>`,
            data: []
        };
    }

    /**
     * Format loading state
     * @returns {object}
     */
    function formatLoading() {
        return {
            text: 'Đang tìm kiếm...',
            html: '<div class="loading">Đang tìm kiếm...</div>',
            data: []
        };
    }

    // Public API
    return {
        format: format,
        formatError: formatError,
        formatLoading: formatLoading
    };
})();

// Export for Node.js / ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResponseFormatter;
}
