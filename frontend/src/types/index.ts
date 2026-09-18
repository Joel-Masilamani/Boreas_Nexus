export type ActiveMapLayer = 
  | 'day_lst' 
  | 'night_lst' 
  | 'day_suhii' 
  | 'night_suhii' 
  | 'persistence' 
  | 'diurnal' 
  | 'dominant_drivers';

export interface CityKPIs {
  city_name: string;
  analysis_run_id: string;
  provenance: {
    sensor?: string;
    capture_date?: string;
    scene_id?: string;
    processing_version?: string;
  };
  total_sample_points: number;
  hotspots_count: number;
  day_hotspot_count: number;
  night_hotspot_count: number;
  persistent_hotspots: number;
  urban_area_km2: number;
  rural_baseline_area_km2: number;
  validated_hotspot_area_km2: number;
  total_hotspot_clusters: number;
  urban_mean_day_suhii_celsius: number;
  urban_mean_night_suhii_celsius: number;
  status: string;
}

export interface HotspotCluster {
  hotspot_id: string;
  period: 'DAY' | 'NIGHT';
  hotspot_group_id: string | null;
  centroid: [number, number];
  cluster_area_m2: number;
  cluster_perimeter_m: number;
  cluster_size_pixels: number;
  mean_lst: number;
  peak_lst: number;
  mean_suhii: number;
  mean_heat_persistence: number;
  mean_hotspot_confidence_score: number;
  dominant_driver: string;
  secondary_driver: string;
  driver_consensus_pct: number;
  domain_consistency_score: number;
  diurnal_driver_shift: string | null;
  mean_ndvi: number;
  mean_building_density: number;
  mean_distance_to_water_m: number;
  mean_shap_building_density: number;
  mean_shap_ndvi: number;
  mean_shap_ndbi: number;
  mean_shap_distance_to_water_m: number;
  mean_shap_distance_to_parks_m: number;
  dominant_cluster_driver_day?: string;
  secondary_cluster_driver_day?: string;
}

export interface ThermalGridPoint {
  id: string;
  c: [number, number]; // [lon, lat]
  ld: number; // day LST
  ln: number; // night LST
  sd: number; // day SUHII
  sn: number; // night SUHII
  dl: number; // diurnal delta
  p: number;  // persistence index
  cl: string; // hotspot classification
  hid: string | null; // hotspot ID
  gz: number; // Gi* z-score
  gp: number; // Gi* p-value
  cc: string; // confidence class
}

export interface DriverAuditData {
  module: string;
  total_points: number;
  cv_metrics?: Record<string, any>;
  rf_cv_metrics?: Record<string, any>;
  rf_feature_importances?: {
    lst_day_celsius?: Record<string, number>;
    lst_night_celsius?: Record<string, number>;
  };
  expected_values?: {
    lst_day_celsius?: number;
    lst_night_celsius?: number;
  };
  plausibility_audit?: any;
  driver_counts: Record<string, number>;
}

// Module 3: Deterministic Thermal Dynamics (Physics-Informed Energy Balance)
export interface DiurnalFluxPoint {
  hour: number;
  timeLabel: string;
  netRadiation: number;
  sensibleHeat: number;
  latentHeat: number;
  groundHeat: number;
  surfaceTemp: number;
  airTemp: number;
}

export interface ThermalDynamicsModel {
  surfaceTemp: number;
  airTemp: number;
  netRadiation: number;
  sensibleHeat: number;
  latentHeat: number;
  groundHeat: number;
  bowenRatio: number;
  albedo: number;
  diurnalCycle: DiurnalFluxPoint[];
}

// Module 4: Scenario Simulation
export interface ScenarioInterventions {
  coolRoofCoverage: number;       // 0 - 100%
  greenRoofCoverage: number;      // 0 - 100%
  treeCanopyCoverage: number;     // 0 - 100%
  permeablePavementCoverage: number; // 0 - 100%
  waterInfrastructureCoverage: number; // 0 - 100%
  budgetCr: number;               // in ₹ Crore
}

export interface ScenarioResult {
  baselineLST: number;
  projectedLST: number;
  lstReduction: number;
  baselineAirTemp: number;
  projectedAirTemp: number;
  airTempReduction: number;
  baselineSUHII: number;
  projectedSUHII: number;
  suhiiReduction: number;
  totalCostCr: number;
  budgetRemainingCr: number;
  feasibilityScore: number;
  equityScore: number;
  co2OffsetTonsYear: number;
}

// Module 5: Decision Center
export interface DecisionPreset {
  id: string;
  name: string;
  tagline: string;
  description: string;
  coolingImpact: number;
  costCr: number;
  coveragePct: number;
  feasibilityPct: number;
  equityPct: number;
  interventions: ScenarioInterventions;
}

export interface PlanningActionItem {
  id: string;
  action: string;
  type: string;
  targetCoverage: string;
  priority: 'Immediate' | 'Phase 1' | 'Phase 2' | 'Long-term';
  costEstimateCr: number;
  coolingYield: string;
  status: 'Recommended' | 'Evaluating' | 'Permitting Required';
}
