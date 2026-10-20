import os, requests, json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ========================================================
# 1. DANH SÁCH 22 DÒNG THIỀN (NIÊM ẤN GỐC)
# ========================================================
GRAPHDB_URL = "http://localhost:7200/repositories/buddhist"

LINEAGE_DATA = [
    { "id": "AnDo", "label": "Thiền Tông Ấn Độ", "parent": "", "founder": "Ma Ha Ca Diếp" },
    { "id": "TrungHoa", "label": "Thiền Tông Trung Hoa", "parent": "AnDo", "founder": "Bồ Đề Đạt Ma" },
    { "id": "NamTong", "label": "Thiền Tông Nam Tông", "parent": "TrungHoa", "founder": "Lục Tổ Huệ Năng" },
    { "id": "HongChau", "label": "Tông Hồng Châu", "parent": "NamTong", "founder": "Mã Tổ Đạo Nhất" },
    { "id": "ThachDau", "label": "Tông Thạch Đầu", "parent": "NamTong", "founder": "Thạch Đầu Hy Thiên" },
    { "id": "LamTe", "label": "Tông Lâm Tế", "parent": "HongChau", "founder": "Lâm Tế Nghĩa Huyền" },
    { "id": "TaoDong", "label": "Tông Tào Động", "parent": "ThachDau", "founder": "Động Sơn Lương Giới" },
    { "id": "QuyNguong", "label": "Tông Quy Ngưỡng", "parent": "HongChau", "founder": "Quy Sơn Linh Hựu" },
    { "id": "VanMon", "label": "Tông Vân Môn", "parent": "ThachDau", "founder": "Vân Môn Văn Yển" },
    { "id": "PhapNhan", "label": "Tông Pháp Nhãn", "parent": "ThachDau", "founder": "Pháp Nhãn Văn Ích" },
    { "id": "DuongKy", "label": "Phái Dương Kỳ", "parent": "LamTe", "founder": "Dương Kỳ Phương Hội" },
    { "id": "HoangLong", "label": "Phái Hoàng Long", "parent": "LamTe", "founder": "Hoàng Long Huệ Nam" },
    { "id": "ChucThanh", "label": "Dòng Lâm Tế Chúc Thánh", "parent": "DuongKy", "founder": "Minh Hải Pháp Bảo" },
    { "id": "LieuQuan", "label": "Dòng Lâm Tế Liễu Quán", "parent": "DuongKy", "founder": "Thiệt Diệu Liễu Quán" },
    { "id": "NguyenThieu", "label": "Dòng Lâm Tế Nguyên Thiều", "parent": "DuongKy", "founder": "Nguyên Thiều Siêu Bạch" },
    { "id": "GiaPho", "label": "Dòng Lâm Tế Gia Phổ", "parent": "DuongKy", "founder": "Phật Ý Linh Nhạc" },
    { "id": "TrucLam", "label": "Thiền Phái Trúc Lâm", "parent": "DuongKy", "founder": "Trần Nhân Tông" },
    { "id": "TyNi", "label": "Tỳ Ni Đa Lưu Chi", "parent": "TrungHoa", "founder": "Tỳ Ni Đa Lưu Chi" },
    { "id": "VoNgon", "label": "Vô Ngôn Thông", "parent": "NamTong", "founder": "Vô Ngôn Thông" },
    { "id": "ThaoDuong", "label": "Thảo Đường", "parent": "TrungHoa", "founder": "Thảo Đường" },
    { "id": "LamTeDT", "label": "Lâm Tế Đàng Trong", "parent": "DuongKy", "founder": "Lương Thân Chủy Ngôn" },
    { "id": "TaoDongVN", "label": "Tào Động Việt Nam", "parent": "TaoDong", "founder": "Thông Giác Thủy Nguyệt" }
]

@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    sparql = f"PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?l WHERE {{ ?s rdfs:label ?l . FILTER(lang(?l)='vi' && regex(str(?l),'{q}','i')) }} LIMIT 10"
    try:
        r = requests.get(GRAPHDB_URL, params={'query': sparql}, headers={'Accept': 'application/sparql-results+json'})
        return jsonify([{"l": i['l']['value']} for i in r.json()['results']['bindings']])
    except: return jsonify([])

@app.route('/api/get_by_label')
def get_by_label():
    name = request.args.get('name', '').strip()
    PREFIXES = "PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
    query = f'''{PREFIXES} SELECT ?note ?g ?ln ?parentName ?childName WHERE {{ 
        ?s rdfs:label "{name}"@vi .
        OPTIONAL {{ ?s bkg:biographicalNote ?note }}
        OPTIONAL {{ ?s bkg:generationOrder ?g }}
        OPTIONAL {{ ?s bkg:dharmaLineageName ?ln }}
        OPTIONAL {{ ?s bkg:hasTeacher ?p . ?p rdfs:label ?parentName . FILTER(lang(?parentName)="vi") }}
        OPTIONAL {{ ?c bkg:hasTeacher ?s . ?c rdfs:label ?childName . FILTER(lang(?childName)="vi") }}
    }}'''
    try:
        r = requests.get(GRAPHDB_URL, params={'query': query}, headers={'Accept': 'application/sparql-results+json'})
        bindings = r.json()['results']['bindings']
        if not bindings: return jsonify({"error": "notfound"})
        f = bindings[0]
        g = int(f['g']['value']) if 'g' in f else 0
        ln = f['ln']['value'] if 'ln' in f else "Chưa rõ pháp phái"
        
        res_gens = {
            "line1": f"Thiền Tông Thế Giới: Đời thứ {g}",
            "line2": f"Tông Lâm Tế Trung Hoa: Đời thứ {g - 38 + 1}" if g >= 38 else "",
            "line3": f"Pháp phái : {ln}: Đời thứ {g - 71 + 1}" if g >= 71 else f"Pháp phái : {ln}: Đời thứ {g}"
        }
        parents = list(set(b['parentName']['value'] for b in bindings if 'parentName' in b))
        children = list(set(b['childName']['value'] for b in bindings if 'childName' in b))
        return jsonify({"name": name, "note": f['note']['value'] if 'note' in f else "", "gens": res_gens, "tree": {"name": name, "parents": parents, "children": children}})
    except Exception as e: return jsonify({"error": str(e)})

@app.route('/')
def index():
    return r'''
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Thiền Phái Niêm Ấn</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
    :root { --p: #4e342e; --a: #bf360c; --bg: #fdf5e6; }
    body { margin: 0; display: flex; font-family: 'Times New Roman', serif; background: var(--bg); height: 100vh; overflow: hidden; }
    #sidebar { width: 320px; background: white; padding: 25px; border-right: 3px solid var(--p); z-index: 100; box-shadow: 2px 0 10px rgba(0,0,0,0.1); }
    #tree-area { flex-grow: 1; position: relative; background: #fff; }
    #bio-panel { position: fixed; top: 0; right: -500px; width: 450px; height: 100vh; background: white; border-left: 8px solid var(--p); transition: 0.4s; padding: 40px 30px; box-sizing: border-box; overflow-y: auto; z-index: 1000; }
    #bio-panel.open { right: 0; }
    .badge-container { background: #fdf2f0; padding: 20px; border: 1px double var(--a); margin-bottom: 25px; }
    .badge-line { display: block; color: var(--p); font-weight: bold; font-size: 16px; margin-bottom: 8px; border-bottom: 1px solid #eee; }
    .bio-text { line-height: 1.8; font-size: 17px; text-align: justify; white-space: pre-wrap; }
    .node rect { fill: white; stroke: var(--p); stroke-width: 2px; rx: 4; cursor: pointer; }
    .node.active rect { fill: #fff3e0; stroke: var(--a); stroke-width: 3px; }
    .node text { font-size: 13px; font-weight: bold; text-anchor: middle; }
    .link { fill: none; stroke: #bc9b82; stroke-width: 1.5px; opacity: 0.6; }
    .btn { width: 100%; padding: 12px; background: var(--p); color: #fff; border: none; cursor: pointer; font-weight: bold; margin-bottom: 15px; }
    #sug { position: absolute; background: white; border: 1px solid #ccc; width: 100%; max-height: 300px; overflow-y: auto; z-index: 110; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .s-item { padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; font-size: 14px; }
    .s-item:hover { background: #fdf5e6; color: var(--a); }
</style></head>
<body>
<div id="sidebar">
    <h2 style="color:var(--p); text-align:center; border-bottom: 2px solid var(--p);">THIỀN SỬ</h2>
    <button class="btn" onclick="drawMain()">22 DÒNG THIỀN GỐC</button>
    <div style="position:relative;">
        <input type="text" id="search" placeholder="Gõ tên Tổ sư..." style="width:100%; padding:12px; box-sizing:border-box; border:1px solid var(--p);">
        <div id="sug"></div>
    </div>
</div>
<div id="tree-area"><svg id="canvas" style="width:100%; height:100%;"><g id="viewport"></g></svg></div>
<div id="bio-panel">
    <span style="float:right; cursor:pointer; font-size:30px;" onclick="document.getElementById('bio-panel').classList.remove('open')">&times;</span>
    <h2 id="bio-title" style="color:var(--a); border-bottom: 2px solid var(--a); padding-bottom:10px;"></h2>
    <div id="bio-content"></div>
</div>
<script>
    const mainData = JSON_DATA;
    const svg = d3.select("#canvas"), container = d3.select("#viewport");
    svg.call(d3.zoom().on("zoom", (e) => container.attr("transform", e.transform)));

    // SEARCH "MỚM" Ô TÌM KIẾM
    const sInp = document.getElementById('search'), sDiv = document.getElementById('sug');
    sInp.addEventListener('input', async () => {
        if(sInp.value.length < 2) { sDiv.innerHTML = ''; return; }
        const res = await fetch(`/api/search?q=${encodeURIComponent(sInp.value)}`).then(r => r.json());
        sDiv.innerHTML = res.map(i => `<div class="s-item" onclick="selectS('${i.l}')">${i.l}</div>`).join('');
    });
    function selectS(name) { sInp.value = name; sDiv.innerHTML = ''; loadBio(name); }

    function drawMain() {
        container.selectAll("*").remove();
        const root = d3.stratify().id(d => d.id).parentId(d => d.parent)(mainData);
        d3.tree().nodeSize([220, 160])(root);
        container.selectAll(".link").data(root.links()).enter().append("path").attr("class", "link")
                 .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));
        const node = container.selectAll(".node").data(root.descendants()).enter().append("g")
                 .attr("class", "node").attr("transform", d => `translate(${d.x},${d.y})`)
                 .on("click", (e, d) => loadBio(d.data.founder));
        node.append("rect").attr("width", 175).attr("height", 50).attr("x", -87.5).attr("y", -25);
        node.append("text").attr("dy", -2).text(d => d.data.label);
        node.append("text").attr("dy", 15).style("font-size","11px").style("fill","#666").text(d => d.data.founder);
        svg.call(d3.zoom().transform, d3.zoomIdentity.translate(window.innerWidth/2-160, 80).scale(0.6));
    }

    function draw3Gen(data) {
        container.selectAll("*").remove();
        const nodes = [{id: data.name, x: 0, y: 0, type: 'mid'}];
        const links = [];
        data.parents.forEach((p, i) => {
            nodes.push({id: p, x: (i - (data.parents.length-1)/2)*280, y: -160, type: 'top'});
            links.push({source: [nodes[nodes.length-1].x, -160], target: [0, 0]});
        });
        data.children.forEach((c, i) => {
            nodes.push({id: c, x: (i - (data.children.length-1)/2)*280, y: 160, type: 'bot'});
            links.push({source: [0, 0], target: [nodes[nodes.length-1].x, 160]});
        });
        container.selectAll(".link").data(links).enter().append("line")
                 .attr("class", "link").attr("x1", d=>d.source[0]).attr("y1", d=>d.source[1])
                 .attr("x2", d=>d.target[0]).attr("y2", d=>d.target[1]);
        const node = container.selectAll(".node").data(nodes).enter().append("g")
                 .attr("class", d => "node " + (d.type==='mid'?'active':''))
                 .attr("transform", d => `translate(${d.x},${d.y})`)
                 .on("click", (e, d) => loadBio(d.id));
        node.append("rect").attr("width", 210).attr("height", 45).attr("x", -105).attr("y", -22.5);
        node.append("text").attr("dy", 5).text(d => d.id);
        svg.call(d3.zoom().transform, d3.zoomIdentity.translate(window.innerWidth/2-160, window.innerHeight/2).scale(0.8));
    }

    async function loadBio(name) {
        const res = await fetch(`/api/get_by_label?name=${encodeURIComponent(name)}`).then(r => r.json());
        if(res.error) return;
        document.getElementById('bio-title').innerText = "Tổ sư " + res.name;
        document.getElementById('bio-content').innerHTML = `
            <div class="badge-container">
                <span class="badge-line">${res.gens.line1}</span>
                ${res.gens.line2 ? `<span class="badge-line">${res.gens.line2}</span>` : ''}
                <span class="badge-line" style="color:var(--a); border:none;">${res.gens.line3}</span>
            </div>
            <div class="bio-text">${res.note}</div>`;
        document.getElementById('bio-panel').classList.add('open');
        draw3Gen(res.tree);
    }
    window.onload = drawMain;
</script></body></html>'''.replace('JSON_DATA', json.dumps(LINEAGE_DATA))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)