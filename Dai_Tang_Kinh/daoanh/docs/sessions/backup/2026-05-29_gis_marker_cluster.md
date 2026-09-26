# Session: GIS Marker Cluster for Đạo Ảnh Map

**Date:** 2026-05-29
**Task:** Replace plain L.marker with L.markerClusterGroup + raise backend limit to 50k

## Summary
Backend `api_places_search` limit cap raised from 100 → 50,000. Frontend `places.html` migrated from individual `L.marker` added directly to map, to `L.markerClusterGroup` with `markerMap` for id→marker lookup. `loadInitialPlaces` now fetches all ~58k GPS points without `scope=temple` filter.

## Solution

### Backend (`app.py`)
- `api_places_search`: `limit = min(int(request.args.get('limit', 50)), 100)` → `50000`

### Frontend (`places.html`)
- Added markercluster CSS + JS CDN after Leaflet includes
- Removed `display: none !important` on `.custom-div-icon` (markers should be visible when unclustered)
- Replaced `const markers = {}` with `const clusterGroup = L.markerClusterGroup({chunkedLoading:true, maxClusterRadius:50})` + `const markerMap = {}`
- `map.addLayer(clusterGroup)` after creation
- `addMarker(id, lat, lng)` now does `clusterGroup.addLayer(marker)` instead of `.addTo(map)`
- `clearDynamicMarkers()` uses `clusterGroup.removeLayer()` instead of `map.removeLayer()`
- `highlightMarker()` iterates `markerMap` keys instead of `markers`
- `addMarkerFromResult()` checks `markerMap` instead of `markers`
- `loadInitialPlaces` fetch changed from `?limit=100&scope=temple` to `?limit=50000`

## Files Changed
- `app.py:2026` — limit cap 100 → 50000
- `places.html` lines 8-11 (CDN), 13 (CSS), 168-175 (clusterGroup + markerMap), 180-193 (addMarker cluster), 196 (highlightMarker ref), 240-248 (clearDynamicMarkers ref), 250-254 (addMarkerFromResult ref), 256-260 (loadInitialPlaces params)

## Test Commands
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
bash scripts/lint-check.sh
npm run pipeline
```
