import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CẤU HÌNH ---
GRAPHDB_URL = "http://158.220.106.183:7200/repositories/buddhist"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'queryResults.csv')

# --- GIAO DIỆN HTML TÍCH HỢP (Cập nhật hiển thị Đời Kép) ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>THIỀN TÔNG ĐỒ THỊ - BẢN ĐỜI KÉP 2026</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>
    <style>
        :root { --p: #4e342e; --a: #bf360c; --bg: #fdf5e6; --gold: #ffd700; }
        body { margin: 0; display: flex; font-family: 'Segoe UI', sans-serif; background: var(--bg); height: 100vh; overflow: hidden; }
        #side { width: 320px; background: #fff; border-right: 3px solid var(--p); display: flex; flex-direction: column; z-index: 10; box-shadow: 2px 0 10px rgba(0,0,0,0.1); }
        .head { padding: 20px; background: var(--p); color: #fff; }
        input { width: 100%; padding: 12px; border-radius: 4px; border: 1px solid #ddd; font-size: 16px; box-sizing: border-box; outline: none; }
        #status { padding: 10px; font-size: 13px; background: #f0f0f0; text-align: center; color: var(--a); font-weight: bold; border-bottom: 1px solid #ddd; }
        #list { flex: 1; overflow-y: auto; }
        .item { padding: 12px 20px; cursor: pointer; border-bottom: 1px solid #eee; transition: 0.2s; }
        .item:hover { background: #fff3e0; color: var(--a); padding-left: 25px; }
        
        #canvas { flex: 1; position: relative; background-image: radial-gradient(#d7ccc8 1px, transparent 1px); background-size: 30px 30px; }
        
        /* Panel thông tin bên phải */
        #info-panel { position: absolute; top: 20px; right: 20px; width: 300px; background: rgba(255,255,255,0.95); border: 2px solid var(--p); border-radius: 8px; padding: 15px; display: none; box-shadow: 0 4px 15px rgba(0,0,0,0.2); z-index: 20; }
        .info-title { color: var(--a); font-weight: bold; font-size: 18px; border-bottom: 1px solid var(--p); margin-bottom: 10px; }
        .lineage-badge { background: var(--p); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-top: 5px; display: inline-block; }
        .generation-box { margin: 10px 0; font-size: 14px; line-height: 1.6; }
        
        .node rect { fill: #fff; stroke: var(--p); stroke-width: 2px; rx: 10; ry: 10; }
        .node.center rect { fill: var(--a); stroke: var(--a); filter: drop-shadow(0 0 5px rgba(191,54,12,0.5)); }
        .node.center text { fill: #fff; }
        .node text { font-size: 14px; font-weight: bold; text-anchor: middle; fill: #333; pointer-events: none; }
        .link { fill: none; stroke: #bc9b82; stroke-width: 2.5px; opacity: 0.6; }
    </style>
</head>
<body>
<div id="side">
    <div class="head"><h3>THIỀN TÔNG ĐỒ THỊ</h3><input type="text" id="inp" placeholder="Tìm tên thiền sư..."></div>
    <div id="status">Đang tải CSV...</div>
    <div id="list"></div>
</div>

<div id="canvas">
    <div id="info-panel">
        <div id="info-content"></div>
    </div>
    <div id="svg-box"></div>
</div>

<script>
let DATA = [];
Papa.parse("/get_csv", {
    download: true,
    complete: (r) => {
        DATA = r.data.map(d => ({
            uri: (d[0]||"").includes("http") ? d[0] : "http://www.phatphaponline.org/ontology/buddhist-kg/monk/" + (d[0]||"").replace("ex:monk/", ""),
            name: d[1]||""
        })).filter(x => x.name && x.name !== "label");
        document.getElementById('status').innerText = "Đã thỉnh: " + DATA.length + " vị thiền sư.";
    }
});

document.getElementById('inp').oninput = (e) => {
    const v = e.target.value.toLowerCase();
    const matches = DATA.filter(x => x.name.toLowerCase().includes(v)).slice(0, 50);
    document.getElementById('list').innerHTML = matches.map(x => `<div class="item" onclick="load('${x.uri}','${x.name}')">${x.name}</div>`).join('');
};

async function load(uri, name) {
    document.getElementById('status').innerText = "Đang thỉnh: " + name;
    
    // TRUY VẤN SPARQL TỐI ƯU CHO ĐỜI KÉP
    const q = `
    PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?c ?n ?g ?ln ?t ?tN ?d ?dN ?isFounder ?founderG WHERE {
        BIND(<${uri}> AS ?c)
        ?c rdfs:label ?n.
        OPTIONAL { ?c bkg:generationOrder ?g }
        OPTIONAL { ?c bkg:dharmaLineageName ?ln }
        OPTIONAL { ?c bkg:isLineageFounder ?isFounder }
        OPTIONAL { ?c bkg:hasTeacher ?t. ?t rdfs:label ?tN. }
        OPTIONAL { ?d bkg:hasTeacher ?c. ?d rdfs:label ?dN. }
        
        # Tra cứu đời của vị Khai Tổ thuộc cùng dòng phái để tính đời nhánh
        OPTIONAL {
            ?f bkg:dharmaLineageName ?ln ;
               bkg:isLineageFounder "true"^^xsd:boolean ;
               bkg:generationOrder ?founderG .
        }
    }`;

    try {
        const res = await fetch(\`/sparql?query=\` + encodeURIComponent(q));
        const json = await res.json();
        const results = json.results.bindings;
        
        if(results.length > 0) {
            updateInfo(results[0]);
            draw(results, uri, name);
        }
        document.getElementById('status').innerText = "Hiện tại: " + name;
    } catch(e) { 
        console.error(e);
        document.getElementById('status').innerText = "Lỗi kết nối GraphDB!"; 
    }
}

function updateInfo(data) {
    const info = document.getElementById('info-panel');
    const content = document.getElementById('info-content');
    
    const name = data.n.value;
    const gVal = data.g ? parseInt(data.g.value) : 0;
    const ln = data.ln ? data.ln.value : "Thiền Tông";
    const isFounder = data.isFounder && data.isFounder.value === "true";
    const founderG = data.founderG ? parseInt(data.founderG.value) : gVal;
    
    // Thuật toán đời nhánh L
    let lVal = isFounder ? 1 : (gVal - founderG + 1);
    if (lVal <= 0) lVal = 1;

    content.innerHTML = `
        <div class="info-title">\${name}</div>
        <div class="lineage-badge">\${ln}</div>
        <div class="generation-box">
            • Đời thứ <b>\${gVal}</b> dòng Lâm Tế<br>
            • Thế hệ thứ <b>\${lVal}</b> pháp phái \${ln}
        </div>
        <p style="font-size: 12px; color: #666; font-style: italic;">*Dữ liệu dựa trên phả hệ 2026</p>
    `;
    info.style.display = 'block';
}

const svg = d3.select("#svg-box").append("svg")
              .attr("width", window.innerWidth-320)
              .attr("height", window.innerHeight)
              .call(d3.zoom().on("zoom", (e) => g.attr("transform", e.transform)));
const g = svg.append("g");

function draw(rows, centerUri, centerName) {
    g.selectAll("*").remove();
    const safeId = (u) => "n_" + btoa(encodeURIComponent(u)).replace(/[^a-z0-9]/gi, "").substr(-10);
    let nodes = [{ id: safeId(centerUri), name: centerName, parent: "", uri: centerUri, isCenter: true }];
    let added = new Set([centerUri]);

    rows.forEach(r => {
        if (r.t && !added.has(r.t.value)) {
            nodes.push({ id: safeId(r.t.value), name: r.tN.value, parent: "", uri: r.t.value });
            nodes[0].parent = safeId(r.t.value); 
            added.add(r.t.value);
        }
        if (r.d && !added.has(r.d.value)) {
            nodes.push({ id: safeId(r.d.value), name: r.dN.value, parent: safeId(centerUri), uri: r.d.value });
            added.add(r.d.value);
        }
    });

    try {
        const root = d3.stratify().id(d => d.id).parentId(d => d.parent)(nodes);
        d3.tree().nodeSize([250, 150])(root);
        
        g.selectAll(".link").data(root.links()).enter().append("path").attr("class", "link")
            .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));
            
        const node = g.selectAll(".node").data(root.descendants()).enter().append("g")
            .attr("class", d => "node" + (d.data.isCenter ? " center" : ""))
            .attr("transform", d => `translate(\${d.x},\${d.y})`)
            .on("click", (e, d) => load(d.data.uri, d.data.name));
            
        node.append("rect").attr("width", 180).attr("height", 45).attr("x", -90).attr("y", -22.5);
        node.append("text").attr("dy", 5).text(d => d.data.name);
        
        svg.transition().duration(500).call(d3.zoom().transform, d3.zoomIdentity.translate((window.innerWidth-320)/2, 150).scale(0.8));
    } catch(e) { console.error("Lỗi Stratify:", e); }
}
</script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    return INDEX_HTML

@app.route('/get_csv')
def get_csv():
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}", 404

@app.route('/sparql')
def sparql_proxy():
    query = request.args.get('query')
    try:
        r = requests.get(GRAPHDB_URL, params={'query': query}, 
                         headers={'Accept': 'application/sparql-results+json'}, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Giải phóng cổng 80 và chạy ứng dụng
    os.system("sudo fuser -k 80/tcp")
    print("Hệ thống khởi động tại http://158.220.106.183/")
    app.run(host='0.0.0.0', port=80, debug=False)