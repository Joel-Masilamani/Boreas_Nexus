import { create } from 'zustand';
import { 
  ActiveMapLayer, 
  CityKPIs, 
  DriverAuditData, 
  HotspotCluster, 
  ScenarioInterventions, 
  ScenarioResult 
} from '../types';
import { heatDataService } from '../services/api/heatDataService';
import { driverDataService } from '../services/api/driverDataService';
import { scenarioService } from '../services/mock/scenarioService';

interface AppState {
  // Analytical & Context State
  city: string;
  analysisRun: string;
  spatialResolution: string;
  dateRange: string;
  
  // Real Selection & Persistence across routes
  selectedHotspotId: string;
  selectedHotspot: HotspotCluster | null;
  activeMapLayer: ActiveMapLayer;
  isDrawerOpen: boolean;
  isGridPointsVisible: boolean;
  
  // Data Cache
  cityKPIs: CityKPIs | null;
  hotspotsRegistry: HotspotCluster[];
  hotspotsGeoJSON: GeoJSON.FeatureCollection | null;
  driverAudit: DriverAuditData | null;
  isLoading: boolean;
  error: string | null;

  // Scenario Simulation State (Module 4)
  scenarioInterventions: ScenarioInterventions;
  scenarioResult: ScenarioResult | null;
  isSimulating: boolean;

  // Decision State (Module 5)
  selectedPresetId: string;

  // Viewport State
  mapViewport: {
    center: [number, number];
    zoom: number;
    pitch: number;
    bearing: number;
  };

  // Actions
  setSelectedHotspotId: (id: string) => void;
  setActiveMapLayer: (layer: ActiveMapLayer) => void;
  setDrawerOpen: (open: boolean) => void;
  setGridPointsVisible: (visible: boolean) => void;
  setScenarioInterventions: (interventions: Partial<ScenarioInterventions>) => void;
  runScenarioSimulation: () => Promise<void>;
  setSelectedPresetId: (presetId: string) => void;
  setMapViewport: (viewport: { center: [number, number]; zoom: number; pitch?: number; bearing?: number }) => void;
  loadInitialData: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  city: 'Chennai Metropolitan Region',
  analysisRun: 'BNX-2024-05-15-001',
  spatialResolution: '100 m Spatial Grid',
  dateRange: 'May 2024 Dry Season',

  selectedHotspotId: 'DAY_HOT_0001',
  selectedHotspot: null,
  activeMapLayer: 'day_lst',
  isDrawerOpen: false,
  isGridPointsVisible: false,

  cityKPIs: null,
  hotspotsRegistry: [],
  hotspotsGeoJSON: null,
  driverAudit: null,
  isLoading: true,
  error: null,

  scenarioInterventions: {
    coolRoofCoverage: 50,
    greenRoofCoverage: 20,
    treeCanopyCoverage: 30,
    permeablePavementCoverage: 25,
    waterInfrastructureCoverage: 5,
    budgetCr: 25,
  },
  scenarioResult: null,
  isSimulating: false,

  selectedPresetId: 'hybrid_strategy',

  mapViewport: {
    center: [80.25, 13.08], // Chennai center [lon, lat]
    zoom: 11,
    pitch: 0,
    bearing: 0,
  },

  setSelectedHotspotId: (id: string) => {
    const { hotspotsRegistry, scenarioInterventions } = get();
    const hotspot = hotspotsRegistry.find(h => h.hotspot_id === id) || null;
    
    // Evaluate scenario result for this new hotspot immediately so Module 4 is ready
    let result = null;
    if (hotspot) {
      result = scenarioService.evaluateScenario(hotspot, scenarioInterventions);
    }

    set({
      selectedHotspotId: id,
      selectedHotspot: hotspot,
      scenarioResult: result,
      isDrawerOpen: true,
      ...(hotspot ? {
        mapViewport: {
          center: hotspot.centroid,
          zoom: 13.5,
          pitch: 25,
          bearing: 0,
        }
      } : {})
    });
  },

  setActiveMapLayer: (layer: ActiveMapLayer) => set({ activeMapLayer: layer }),
  setDrawerOpen: (open: boolean) => set({ isDrawerOpen: open }),
  setGridPointsVisible: (visible: boolean) => set({ isGridPointsVisible: visible }),

  setScenarioInterventions: (partial) => {
    const updated = { ...get().scenarioInterventions, ...partial };
    const { selectedHotspot } = get();
    let result = null;
    if (selectedHotspot) {
      result = scenarioService.evaluateScenario(selectedHotspot, updated);
    }
    set({ scenarioInterventions: updated, scenarioResult: result });
  },

  runScenarioSimulation: async () => {
    const { selectedHotspot, scenarioInterventions } = get();
    if (!selectedHotspot) return;

    set({ isSimulating: true });
    // Simulate brief 1.5s execution progression
    await new Promise(resolve => setTimeout(resolve, 1500));
    const result = scenarioService.evaluateScenario(selectedHotspot, scenarioInterventions);
    set({ scenarioResult: result, isSimulating: false });
  },

  setSelectedPresetId: (presetId: string) => set({ selectedPresetId: presetId }),

  setMapViewport: (viewport) => set((state) => ({
    mapViewport: {
      ...state.mapViewport,
      ...viewport,
    }
  })),

  loadInitialData: async () => {
    set({ isLoading: true, error: null });
    try {
      const [kpis, geojson, registry, audit] = await Promise.all([
        heatDataService.getCityKPIs(),
        heatDataService.getHotspotsGeoJSON(),
        heatDataService.getHotspotRegistry(),
        driverDataService.getDriverAudit(),
      ]);

      const initialHotspot = registry.find(h => h.hotspot_id === 'DAY_HOT_0001') || registry[0] || null;
      const initialScenarioResult = initialHotspot 
        ? scenarioService.evaluateScenario(initialHotspot, get().scenarioInterventions)
        : null;

      set({
        cityKPIs: kpis,
        hotspotsGeoJSON: geojson,
        hotspotsRegistry: registry,
        driverAudit: audit,
        selectedHotspotId: initialHotspot ? initialHotspot.hotspot_id : 'DAY_HOT_0001',
        selectedHotspot: initialHotspot,
        scenarioResult: initialScenarioResult,
        isLoading: false,
      });
    } catch (err: any) {
      console.error('Failed to load initial data:', err);
      set({
        isLoading: false,
        error: err.message || 'Error loading analytical knowledge layers',
      });
    }
  },
}));
