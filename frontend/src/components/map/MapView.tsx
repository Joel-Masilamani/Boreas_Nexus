import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

// Configure MapLibre web worker for Vite ESM bundling
maplibregl.setWorkerUrl(workerUrl);

type MapLibreMap = maplibregl.Map;
type Popup = maplibregl.Popup;
import { useAppStore } from '../../store/useAppStore';
import { MapControls } from './MapControls';
import { MapLegend } from './MapLegend';
import { HotspotDrawer } from './HotspotDrawer';
import { heatDataService } from '../../services/api/heatDataService';

interface MapViewProps {
  className?: string;
  showControls?: boolean;
  showLegend?: boolean;
  showDrawer?: boolean;
}

export const MapView: React.FC<MapViewProps> = ({
  className = 'h-full w-full',
  showControls = true,
  showLegend = true,
  showDrawer = true,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const hoverPopupRef = useRef<Popup | null>(null);

  const {
    activeMapLayer,
    selectedHotspotId,
    setSelectedHotspotId,
    hotspotsGeoJSON,
    isGridPointsVisible,
    mapViewport,
  } = useAppStore();

  // Initialize MapLibre GL
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY || 'cb1_3pba_1_096de1cbf495d7515951abaf';

    const darkStyle: maplibregl.StyleSpecification = {
      version: 8,
      sources: {
        'carto-dark': {
          type: 'raster',
          tiles: [
            `https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=${cartoApiKey}`,
            `https://b.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=${cartoApiKey}`,
            `https://c.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=${cartoApiKey}`,
            `https://d.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=${cartoApiKey}`,
          ],
          tileSize: 256,
          attribution: '© OpenStreetMap contributors, © CARTO',
        },
      },
      layers: [
        {
          id: 'carto-dark-layer',
          type: 'raster',
          source: 'carto-dark',
          minzoom: 0,
          maxzoom: 20,
        },
      ],
    };

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: darkStyle,
      center: mapViewport.center,
      zoom: mapViewport.zoom,
      pitch: mapViewport.pitch,
      bearing: mapViewport.bearing,
      attributionControl: false,
    });

    (window as any).__boreasMap = map;

    map.on('error', (e) => {
      console.error('[MapLibre error]', e);
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right');

    hoverPopupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 15,
    });

    map.on('load', async () => {
      console.log('[MapLibre] Load event fired!');
      try {
        // 1. Add Hotspots GeoJSON Source
        let rawGeo = hotspotsGeoJSON;
        if (!rawGeo || !(rawGeo as any).features) {
          rawGeo = await heatDataService.getHotspotsGeoJSON();
        }
        const cleanGeoJSON: any = (rawGeo as any)?.features ? rawGeo : (rawGeo as any)?.geojson || rawGeo;
        console.log('[MapLibre] Loaded geojson, feature count:', cleanGeoJSON?.features?.length);

        map.addSource('hotspots-source', {
          type: 'geojson',
          data: cleanGeoJSON,
        });


        // 2. Add Hotspots Fill Layer
        map.addLayer({
          id: 'hotspots-fill',
          type: 'fill',
          source: 'hotspots-source',
          paint: {
            'fill-color': getFillColorExpression(activeMapLayer),
            'fill-opacity': [
              'case',
              ['==', ['get', 'hotspot_id'], selectedHotspotId],
              0.9,
              0.65,
            ],
          },
        });

        // 3. Add Hotspots Outline Layer
        map.addLayer({
          id: 'hotspots-stroke',
          type: 'line',
          source: 'hotspots-source',
          paint: {
            'line-color': [
              'case',
              ['==', ['get', 'hotspot_id'], selectedHotspotId],
              '#4DFFDF',
              '#FFFFFF',
            ],
            'line-width': [
              'case',
              ['==', ['get', 'hotspot_id'], selectedHotspotId],
              3.5,
              1.5,
            ],
            'line-opacity': 0.9,
          },
        });

        // 4. Centroid Pin Circles
        const pointFeatures: any = {
          type: 'FeatureCollection',
          features: (cleanGeoJSON.features || []).map((f: any) => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: f.properties?.centroid || [80.25, 13.08],
            },
            properties: f.properties,
          })),
        };

        map.addSource('hotspots-pins-source', {
          type: 'geojson',
          data: pointFeatures,
        });

      map.addLayer({
        id: 'hotspots-pins',
        type: 'circle',
        source: 'hotspots-pins-source',
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'hotspot_id'], selectedHotspotId],
            6,
            4,
          ],
          'circle-color': '#FFFFFF',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#05050F',
        },
      });

      // Trigger resize to ensure full canvas bounds
      setTimeout(() => map.resize(), 100);

      // Hotspot click interaction
      map.on('click', 'hotspots-fill', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        const hid = feature.properties?.hotspot_id;
        if (hid) {
          setSelectedHotspotId(hid);
        }
      });

      // Hover interaction
      map.on('mousemove', 'hotspots-fill', (e) => {
        if (!e.features || e.features.length === 0) return;
        map.getCanvas().style.cursor = 'pointer';
        const p = e.features[0].properties;
        if (!p) return;

        const html = `
          <div style="font-family: 'Open Sans', sans-serif;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px;">
              <strong style="color: #4DFFDF; font-size: 13px;">${p.hotspot_id}</strong>
              <span style="font-size: 10px; background: #25245D; color: #FFA63F; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                ${p.period}
              </span>
            </div>
            <div style="font-size: 11px; color: #E2E8F0; line-height: 1.5;">
              <div>Mean LST: <strong style="color: #FFFFFF;">${p.mean_lst}°C</strong> | Peak: <strong style="color: #FF4D4D;">${p.peak_lst}°C</strong></div>
              <div>SUHII Anomaly: <strong style="color: #FFA63F;">+${p.mean_suhii}°C</strong></div>
              <div>Primary Driver: <strong style="color: #4DFFDF; text-transform: capitalize;">${(p.dominant_driver || '').replace(/_/g, ' ')}</strong></div>
            </div>
          </div>
        `;

        hoverPopupRef.current?.setLngLat(e.lngLat).setHTML(html).addTo(map);
      });

      map.on('mouseleave', 'hotspots-fill', () => {
        map.getCanvas().style.cursor = '';
        hoverPopupRef.current?.remove();
      });
      } catch (err) {
        console.error('[MapLibre] Error in map.on load handler:', err);
      }
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update layer fill colors when activeMapLayer changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('hotspots-fill')) {
      map.setPaintProperty('hotspots-fill', 'fill-color', getFillColorExpression(activeMapLayer));
    }
  }, [activeMapLayer]);

  // Update selection outline when selectedHotspotId changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('hotspots-stroke')) {
      map.setPaintProperty('hotspots-stroke', 'line-color', [
        'case',
        ['==', ['get', 'hotspot_id'], selectedHotspotId],
        '#4DFFDF',
        '#FFFFFF',
      ]);
      map.setPaintProperty('hotspots-stroke', 'line-width', [
        'case',
        ['==', ['get', 'hotspot_id'], selectedHotspotId],
        3.5,
        1.2,
      ]);
    }
    if (map.getLayer('hotspots-fill')) {
      map.setPaintProperty('hotspots-fill', 'fill-opacity', [
        'case',
        ['==', ['get', 'hotspot_id'], selectedHotspotId],
        0.9,
        0.65,
      ]);
    }
  }, [selectedHotspotId]);

  // Toggle thermal grid layer (lazy-loaded on user toggle)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (isGridPointsVisible) {
      if (!map.getSource('thermal-grid-source')) {
        heatDataService.getThermalGrid().then((gridPoints) => {
          if (!mapRef.current || !map.isStyleLoaded()) return;
          if (map.getSource('thermal-grid-source')) return;

          const gridGeoJSON: any = {
            type: 'FeatureCollection',
            features: gridPoints.map(p => ({
              type: 'Feature',
              geometry: {
                type: 'Point',
                coordinates: p.c,
              },
              properties: p,
            })),
          };

          map.addSource('thermal-grid-source', {
            type: 'geojson',
            data: gridGeoJSON,
          });

          map.addLayer({
            id: 'thermal-grid-layer',
            type: 'circle',
            source: 'thermal-grid-source',
            layout: { visibility: 'visible' },
            paint: {
              'circle-radius': 2.5,
              'circle-color': [
                'interpolate',
                ['linear'],
                ['get', 'ld'],
                32, '#3B82F6',
                37, '#5EFF5A',
                41, '#FFA63F',
                44, '#FF7A00',
                48, '#FF0707',
              ],
              'circle-opacity': 0.7,
            },
          });
        }).catch((e) => console.warn('Deferred thermal grid load error:', e));
      } else if (map.getLayer('thermal-grid-layer')) {
        map.setLayoutProperty('thermal-grid-layer', 'visibility', 'visible');
      }
    } else {
      if (map.getLayer('thermal-grid-layer')) {
        map.setLayoutProperty('thermal-grid-layer', 'visibility', 'none');
      }
    }
  }, [isGridPointsVisible]);

  // Smooth camera flyTo when viewport updates
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.flyTo({
      center: mapViewport.center,
      zoom: mapViewport.zoom,
      pitch: mapViewport.pitch,
      bearing: mapViewport.bearing,
      essential: true,
      duration: 1200,
    });
  }, [mapViewport]);

  return (
    <div className={`relative ${className}`}>
      <div ref={mapContainerRef} className="w-full h-full min-h-[500px]" />
      {showControls && <MapControls />}
      {showLegend && <MapLegend />}
      {showDrawer && <HotspotDrawer />}
    </div>
  );
};

// MapLibre expression builder for fill colors
function getFillColorExpression(layer: string): any {
  switch (layer) {
    case 'day_lst':
      return [
        'interpolate',
        ['linear'],
        ['get', 'mean_lst'],
        34, '#3B82F6',
        38, '#5EFF5A',
        41, '#FFA63F',
        43, '#FF7A00',
        47, '#FF0707',
      ];
    case 'night_lst':
      return [
        'interpolate',
        ['linear'],
        ['get', 'mean_lst'],
        21, '#1E3A8A',
        23, '#3B82F6',
        25, '#5EFF5A',
        27, '#FFA63F',
        29, '#EC223B',
      ];
    case 'day_suhii':
      return [
        'interpolate',
        ['linear'],
        ['get', 'mean_suhii'],
        0, '#3B82F6',
        2, '#10B981',
        3.5, '#FFA63F',
        5, '#FF7A00',
        7, '#FF0707',
      ];
    case 'night_suhii':
      return [
        'interpolate',
        ['linear'],
        ['get', 'mean_suhii'],
        1, '#2563EB',
        3, '#06B6D4',
        4.5, '#F59E0B',
        6, '#EF4444',
        8, '#991B1B',
      ];
    case 'persistence':
      return [
        'interpolate',
        ['linear'],
        ['get', 'mean_heat_persistence'],
        0.45, '#312E81',
        0.55, '#6366F1',
        0.65, '#A855F7',
        0.72, '#EC4899',
        0.85, '#F43F5E',
      ];
    case 'dominant_drivers':
      return [
        'match',
        ['get', 'dominant_driver'],
        'land_cover_code', '#FFA63F',
        'building_density', '#EC223B',
        'distance_to_parks_m', '#4DFFDF',
        'distance_to_water_m', '#38BDF8',
        'elevation_m', '#C084FC',
        'ndvi', '#5EFF5A',
        '#176BF8',
      ];
    default:
      return '#FFA63F';
  }
}
