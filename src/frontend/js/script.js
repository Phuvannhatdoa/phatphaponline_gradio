// script.js
// =========================================================================================================
// Cấu hình chung
// =========================================================================================================
// Thay thế 'your_vps_ip' bằng địa chỉ IP thực của VPS của bạn
// Oxigraph lắng nghe trực tiếp trên cổng 7878
const OXIGRAPH_SPARQL_ENDPOINT = window.location.origin + '/sparql';
// Namespace ontology của bạn. Hãy đảm bảo khớp với namespace trong file TTL của bạn.
// Ví dụ: PREFIX ex: <http://example.org/ontology/phatphap_truyen_thua#>
const MY_ONTOLOGY_NAMESPACE = 'http://example.org/ontology/phatphap_truyen_thua#'; 

// =========================================================================================================
// Các biến toàn cục cho Vis.js Network
// =========================================================================================================
let network;
let nodes;
let edges;
let nodeIdCounter = 0;
const uriToNodeId = {}; // Map URI to Vis.js node ID for efficient lookup

// =========================================================================================================
// Hàm khởi tạo Vis.js Network
// =========================================================================================================
function initializeNetwork() {
    const container = document.getElementById('mynetwork');
    nodes = new vis.DataSet();
    edges = new vis.DataSet();
    const data = { nodes: nodes, edges: edges };

    // Tùy chọn cấu hình cho Vis.js Network
    const options = {
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.1,
                springLength: 200,
                springConstant: 0.001,
                damping: 0.09,
                avoidOverlap: 1
            },
            solver: 'barnesHut'
        },
        edges: {
            arrows: 'to',
            color: { inherit: 'from' },
            smooth: { type: 'continuous' }
        },
        nodes: {
            shape: 'dot',
            size: 15,
            font: { size: 12, color: '#333' },
            borderWidth: 2,
            shadow: true // Thêm bóng cho node để nhìn rõ hơn
        },
        layout: {
            improvedLayout: false // Tắt để đồ thị ổn định hơn với dữ liệu lớn
        },
        interaction: {
            navigationButtons: true, // Thêm các nút điều hướng (zoom, pan)
            keyboard: true // Bật điều khiển bằng bàn phím
        }
    };
    network = new vis.Network(container, data, options);

    // Xử lý sự kiện click vào node/edge (tùy chọn)
    network.on("selectNode", function (params) {
        if (params.nodes.length === 1) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            // alert(`Bạn đã click vào: ${node.label}\nURI: ${node.title}`);
            console.log("Thông tin node:", node);
        }
    });
}

// =========================================================================================================
// Hàm gửi truy vấn SPARQL đến Oxigraph
// =========================================================================================================
async function executeSparqlQuery(query) {
    try {
        const response = await fetch(OXIGRAPH_SPARQL_ENDPOINT, {
            method: 'POST', // ĐẢM BẢO LÀ 'POST'
            headers: {
                'Content-Type': 'application/sparql-query',
                'Accept': 'application/sparql-results+json' // Quan trọng để Oxigraph trả về JSON
            },
            body: query
        });

        if (!response.ok) {
            const errorText = await response.text();
            // Đây là dòng in lỗi ra console
            console.error("Lỗi HTTP:", response.status, errorText);
            throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
        }

        const jsonResponse = await response.json(); // Phân tích phản hồi thành JSON
        // Oxigraph trả về dữ liệu trong results.bindings
        return jsonResponse.results.bindings;
    } catch (error) {
        console.error("Lỗi khi thực hiện truy vấn SPARQL:", error);
        alert("Lỗi khi truy vấn dữ liệu. Vui lòng kiểm tra console để biết chi tiết.");
        return [];
    }
}S

// =========================================================================================================
// Hàm xử lý kết quả SPARQL và cập nhật Vis.js Network
// =========================================================================================================
async function processSparqlResults(bindings) {
    // Xóa dữ liệu cũ và reset map
    nodes.clear();
    edges.clear();
    nodeIdCounter = 0;
    for (const key in uriToNodeId) {
        delete uriToNodeId[key];
    }

    // Hàm trợ giúp để lấy hoặc tạo node ID và thêm vào DataSet
    function getVisNodeId(uri, label = null) {
        if (!uriToNodeId[uri]) {
            nodeIdCounter++;
            uriToNodeId[uri] = nodeIdCounter;
            // Cố gắng làm sạch label: lấy phần sau dấu '#' hoặc '/' cuối cùng
            const cleanedLabel = label || uri.split('#').pop() || uri.split('/').pop();
            nodes.add({
                id: nodeIdCounter,
                label: cleanedLabel,
                title: uri, // Hiển thị đầy đủ URI khi hover
                color: { background: '#ADD8E6', border: '#1E90FF' } // Màu sắc mặc định
            });
        }
        return uriToNodeId[uri];
    }

    bindings.forEach(binding => {
        const subjectUri = binding.s.value;
        const predicateUri = binding.p.value;
        const objectValue = binding.o.value;
        const objectType = binding.o.type; // 'uri' or 'literal'

        // Lấy hoặc tạo node cho Subject
        const subjectLabel = binding.sLabel ? binding.sLabel.value : null;
        const sId = getVisNodeId(subjectUri, subjectLabel);

        if (objectType === 'uri') {
            // Nếu Object là một URI (là một node khác)
            const objectLabel = binding.oLabel ? binding.oLabel.value : null;
            const oId = getVisNodeId(objectValue, objectLabel);

            // Thêm edge
            edges.add({
                from: sId,
                to: oId,
                label: predicateUri.split('#').pop() || predicateUri.split('/').pop(), // Lấy phần cuối URI làm label cạnh
                title: predicateUri // Hiển thị đầy đủ URI predicate khi hover
            });
        } else if (objectType === 'literal') {
            // Nếu Object là một literal (giá trị data, không phải node khác trong đồ thị)
            // Ta có thể tạo một node riêng cho literal hoặc hiển thị thông tin bằng cách khác
            // Ở đây, tạo một node riêng với màu khác để dễ phân biệt
            const literalNodeId = getVisNodeId(`literal:${objectValue}`, objectValue); // Dùng prefix để đảm bảo ID duy nhất cho literal
            nodes.update({
                id: literalNodeId,
                color: { background: '#D3D3D3', border: '#808080' }, // Màu xám cho literal nodes
                shape: 'box' // Hình hộp cho literal nodes
            });
            edges.add({
                from: sId,
                to: literalNodeId,
                label: predicateUri.split('#').pop() || predicateUri.split('/').pop(),
                title: predicateUri,
                dashes: true // Nét đứt cho cạnh đến literal
            });
        }
    });

    network.fit(); // Tự động điều chỉnh khung nhìn để vừa toàn bộ đồ thị
}

// =========================================================================================================
// Hàm tải toàn bộ dữ liệu Phật sử truyền thừa
// =========================================================================================================
async function loadAllData() {
    // Truy vấn SPARQL để lấy tất cả các bộ ba thuộc ontology của bạn
    // OPTIONAL để lấy rdfs:label nếu có
    const query = `
        PREFIX ex: <${MY_ONTOLOGY_NAMESPACE}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?s ?p ?o ?sLabel ?oLabel
        WHERE {
          ?s ?p ?o .
          OPTIONAL { ?s rdfs:label ?sLabel . }
          OPTIONAL { ?o rdfs:label ?oLabel . }
          FILTER (
            STRSTARTS(STR(?s), STR(ex:)) &&
            STRSTARTS(STR(?o), STR(ex:)) &&
            STRSTARTS(STR(?p), STR(ex:)) # Chỉ lấy các mối quan hệ và thực thể thuộc ontology của bạn
          )
        }
    `;
    const bindings = await executeSparqlQuery(query);
    await processSparqlResults(bindings);
    alert(`Đã tải ${nodes.length} nút và ${edges.length} cạnh.`);
}

// =========================================================================================================
// Hàm thực hiện tìm kiếm theo tên Thiền sư
// =========================================================================================================
async function performSearch() {
    const searchText = document.getElementById('searchQuery').value.trim();
    if (!searchText) {
        alert("Vui lòng nhập từ khóa tìm kiếm.");
        return;
    }

    // Truy vấn SPARQL để tìm kiếm các thực thể có rdfs:label hoặc vcard:fn chứa searchText
    // và lấy các mối quan hệ liên quan
    const query = `
        PREFIX ex: <${MY_ONTOLOGY_NAMESPACE}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>

        SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel
        WHERE {
          {
            ?s rdfs:label|vcard:fn ?sLabel . # Tìm kiếm theo rdfs:label hoặc vcard:fn
            FILTER (regex(?sLabel, "${searchText}", "i")) # "i" cho tìm kiếm không phân biệt chữ hoa/thường
            ?s ?p ?o .
            OPTIONAL { ?o rdfs:label ?oLabel . }
          }
          UNION # Kết hợp kết quả tìm kiếm trong chủ thể và đối tượng
          {
            ?o rdfs:label|vcard:fn ?oLabel . # Tìm kiếm cả trong object
            FILTER (regex(?oLabel, "${searchText}", "i"))
            ?s ?p ?o .
            OPTIONAL { ?s rdfs:label ?sLabel . }
          }
          FILTER (
            STRSTARTS(STR(?s), STR(ex:)) && # Đảm bảo chỉ lấy dữ liệu từ ontology của bạn
            STRSTARTS(STR(?o), STR(ex:)) &&
            STRSTARTS(STR(?p), STR(ex:))
          )
        }
    `;
    const bindings = await executeSparqlQuery(query);
    if (bindings.length === 0) {
        alert(`Không tìm thấy kết quả nào cho "${searchText}".`);
        return;
    }
    await processSparqlResults(bindings);
    alert(`Tìm thấy ${nodes.length} nút và ${edges.length} cạnh liên quan đến "${searchText}".`);
}

// =========================================================================================================
// Gắn sự kiện (Event Listeners) khi DOM đã tải xong
// =========================================================================================================
document.addEventListener('DOMContentLoaded', () => {
    initializeNetwork(); // Khởi tạo Vis.js network

    // Gắn sự kiện cho nút "Tìm kiếm"
    const searchButton = document.querySelector('.controls button[onclick="performSearch()"]');
    if (searchButton) {
        searchButton.onclick = performSearch; // Gắn hàm performSearch
    }

    // Gắn sự kiện cho nút "Tải toàn bộ cây"
    const loadAllButton = document.querySelector('.controls button[onclick="loadAllData()"]');
    if (loadAllButton) {
        loadAllButton.onclick = loadAllData; // Gắn hàm loadAllData
    }

    // Gắn sự kiện "Enter" vào ô tìm kiếm
    const searchQueryInput = document.getElementById('searchQuery');
    if (searchQueryInput) {
        searchQueryInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                performSearch();
            }
        });
    }

    // Tùy chọn: Tải toàn bộ dữ liệu khi trang vừa load xong
    // loadAllData(); 
});