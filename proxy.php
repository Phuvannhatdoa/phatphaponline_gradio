<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// Lấy truy vấn SPARQL từ tham số GET
$sparql_query = $_GET['query'] ?? '';

if (empty($sparql_query)) {
    echo json_encode(['error' => 'No SPARQL query provided.']);
    exit;
}

$sparql_endpoint = 'https://phatphaponline.org/query';
$query_url = $sparql_endpoint . '?' . http_build_query(['query' => $sparql_query]);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $query_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Accept: application/sparql-results+json'
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if ($http_code !== 200) {
    echo json_encode(['error' => 'Failed to fetch data from remote server.', 'http_code' => $http_code]);
} else {
    echo $response;
}

curl_close($ch);
?>