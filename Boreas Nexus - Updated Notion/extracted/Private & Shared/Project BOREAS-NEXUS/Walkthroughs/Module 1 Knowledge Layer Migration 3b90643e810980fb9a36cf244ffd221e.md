# Module 1 Knowledge Layer Migration

The Module 1 Knowledge Layer in **Boreas-Nexus** has been cleanly migrated to the authoritative schema and storage architecture, eliminating redundant attributes, incorporating dynamic UTM projection, integrating upstream environmental feature engineering variables, and producing normalized cluster registry artifacts.

---

## 1. Summary of Changes

### Schema & Data Migration

1. **Removed Redundant Surface Class**: Eliminated `surface_class` across all stages and final outputs. Surface state is represented authoritatively by `is_urban`, `is_rural`, `is_water`, and `land_cover_code`.
2. **Removed Duplicate LST Field**: Omitted redundant `lst_celsius` from Knowledge Layer outputs, keeping `lst_day_celsius` and `lst_night_celsius`.
3. **Replaced Legacy Hotspot Booleans**: Replaced `is_hotspot_day_95`, `is_hotspot_day_99`, `is_hotspot_night_95`, and `is_hotspot_night_99` with `day_hotspot_significance` and `night_hotspot_significance` (allowed values: `99`, `95`, `None`).
4. **Integrated Environmental Features**: Directly consumed upstream `features.geoparquet` variables (`ndvi`, `ndbi`, `ndwi`, `building_density`, `distance_to_water_m`, `distance_to_roads_m`, `distance_to_parks_m`, `elevation_m`, `slope_deg`, `aspect_deg`).
5. **City Temperature Percentiles**: Computed daytime LST relative percentile ranking (`city_temperature_percentile`) strictly across valid land pixels (excluding water and NoData), along with `temperature_rank` and `temperature_total_pixels`.
6. **Hotspot Clustering**: Connected component analysis (4/8 connectivity) groups significant hotspot pixels into clusters, assigning `hotspot_id` (`HOT_0001`, `HOT_0002`, ...); non-hotspot points receive `null`.
7. **Normalized Hotspot Registry**: Created `hotspot_registry.parquet` with `cluster_centroid_x`, `cluster_centroid_y`, `cluster_bbox`, `cluster_area_m2`, `cluster_perimeter_m`, and `mean_hotspot_confidence_score`.
8. **Hotspot Confidence Scoring**: Computed deterministic 0–100 weighted score (`hotspot_confidence_score`) and assigned `confidence_class` using configurable weights from `config/hotspot_scoring.yaml`; non-hotspots are cleanly set to `null`.
9. **Dynamic UTM Projection & Validation**: Created `utils/crs_utils.py` to dynamically compute UTM zone from longitude (e.g. EPSG:32644 for Chennai) using `pyproj.Transformer(always_xy=True)` with coordinate range validation ($100,000 \le X \le 900,000$, $0 \le Y \le 10,000,000$).
10. **Data Provenance**: Populated `sensor`, `capture_date`, `scene_id`, and `processing_version` metadata.
11. **Storage Optimization**: GeoParquet is the authoritative internal format; intermediate debug outputs are suppressed unless `debug.enabled` or `debug.save_intermediate_outputs` is `true`.

---

## 2. Authoritative Knowledge Layer Schema (43 Fields + Geometry)

| Category | Field Name | Type | Example / Description |
| --- | --- | --- | --- |
| **Identity** | `point_id` | `str`/`int` | `pt_000001` |
|  | `latitude` | `float` | `13.097923` |
|  | `longitude` | `float` | `80.141088` |
|  | `utm_x_m` | `float` | `406891.96` (Projected meters) |
|  | `utm_y_m` | `float` | `1448122.86` (Projected meters) |
| **Surface** | `land_cover_code` | `int` | `50` (Built-up) |
|  | `is_urban` | `bool` | `True` |
|  | `is_rural` | `bool` | `False` |
|  | `is_water` | `bool` | `False` |
| **Thermal** | `lst_day_celsius` | `float` | `40.22` |
|  | `lst_night_celsius` | `float` | `25.79` |
|  | `suhii_day_celsius` | `float` | `1.81` |
|  | `suhii_night_celsius` | `float` | `4.28` |
|  | `delta_lst_diurnal` | `float` | `14.42` |
|  | `heat_persistence_index` | `float` | `0.641` |
| **Statistics** | `gi_zscore_day` | `float` | `-1.02` |
|  | `gi_pvalue_day` | `float` | `0.85` |
|  | `gi_zscore_night` | `float` | `0.72` |
|  | `gi_pvalue_night` | `float` | `0.24` |
|  | `day_hotspot_significance` | `Int64`/`None` | `95`, `99`, or `None` |
|  | `night_hotspot_significance` | `Int64`/`None` | `95`, `99`, or `None` |
|  | `hotspot_id` | `str`/`None` | `HOT_0001` or `None` |
|  | `city_temperature_percentile` | `float` | `70.42` (0-100, NaN for water) |
|  | `temperature_rank` | `int`/`float` | `30199` |
|  | `temperature_total_pixels` | `int` | `42913` (Valid land pixels) |
|  | `hotspot_confidence_score` | `float` | `49.03` (0-100 for hotspots) |
| **Environment** | `ndvi` | `float` | `0.35` |
|  | `ndbi` | `float` | `0.15` |
|  | `ndwi` | `float` | `-0.10` |
|  | `building_density` | `float` | `0.50` |
|  | `distance_to_water_m` | `float` | `154.02` |
|  | `distance_to_roads_m` | `float` | `17.36` |
|  | `distance_to_parks_m` | `float` | `1335.98` |
|  | `elevation_m` | `float` | `19.51` |
|  | `slope_deg` | `float` | `42.59` |
|  | `aspect_deg` | `float` | `135.00` |
| **Classification** | `thermal_retention_class` | `str` | `Moderate Retention` |
|  | `confidence_class` | `str`/`None` | `Moderate` / `High` / `Very High` / `Critical` |
|  | `hotspot_classification` | `str` | `95% Confidence Hotspot` |
| **Provenance** | `sensor` | `str` | `Landsat-8/9 & Sentinel-2` |
|  | `capture_date` | `str` | `2024-05-15` |
|  | `scene_id` | `str` | `LC09_L2SP_142051_20240515` |
|  | `processing_version` | `str` | `1.0.0` |
| **Geometry** | `geometry` | `Point` | `POINT (80.14109 13.09792)` (EPSG:4326) |

---

## 3. Verification & Validation Results

### 20-Point Automated Validation Matrix

All 20 validation rules passed in `cluster_validation.json`:

- `required_columns_exist`: `True` (all 43 authoritative columns + geometry)
- `no_forbidden_duplicate_fields`: `True` (zero occurrences of `surface_class`, `lst_celsius`, `is_hotspot_day_95`, etc.)
- `coordinates_valid`: `True` (valid latitude/longitude bounds)
- `utm_coordinates_projected_valid`: `True` (easting ~406,892 to ~427,637 m; northing ~1,420,990 to ~1,463,206 m)
- `crs_valid`: `True` (EPSG:4326)
- `surface_masks_consistent`: `True` (no overlapping masks)
- `water_excluded_from_temperature_percentiles`: `True` (1,385 water pixels set to `NaN`)
- `temperature_percentiles_within_0_100`: `True` (evaluated over 42,913 valid land pixels)
- `temperature_rank_valid`: `True` ($1 \le \text{rank} \le 42,913$)
- `temperature_total_pixels_consistent`: `True` (42,913 across all rows)
- `hotspot_ids_unique_in_registry`: `True` (158 unique cluster rows in registry)
- `single_hotspot_membership_per_point`: `True`
- `cluster_areas_positive`: `True`
- `cluster_perimeters_positive`: `True`
- `confidence_scores_within_0_100`: `True`
- `confidence_classes_valid`: `True`
- `no_redundant_cluster_metadata_in_points`: `True`
- `geometries_valid`: `True`
- `mandatory_fields_complete`: `True`
- `spatial_alignment_compatible`: `True`

### Full Test Suite Results

```bash
python -m pytest
======================= 26 passed, 3 warnings in 37.16s =======================
```

---

## 4. Final Storage Structure

```
data/
├── processed/
│   ├── feature_engineering/
│   │   └── features.geoparquet
│   └── module_1/
│       ├── urban_heat_hotspot_knowledge_layer.geoparquet  (Authoritative GeoParquet)
│       ├── hotspot_registry.parquet                      (Normalized Cluster Registry)
│       ├── cluster_validation.json                        (20-Point Validation Report)
│       └── metadata.json                                  (Dataset Metadata Manifest)
└── exports/
    ├── geojson/
    │   ├── urban_heat_hotspot_knowledge_layer.geojson
    │   └── hotspot_clusters.geojson
    ├── gpkg/
    │   ├── urban_heat_hotspot_knowledge_layer.gpkg
    │   └── hotspot_clusters.gpkg
    └── reports/
        └── module_1_manifest.json
```

---

## 5. Summary of Files Changed & Created

### Files Created

- [`utils/crs_utils.py`](file:///d:/Projects/Boreas_Nexus/utils/crs_utils.py): Dynamic UTM zone detection and PyProj coordinate transformations.
- [`tests/test_knowledge_layer_schema.py`](file:///d:/Projects/Boreas_Nexus/tests/test_knowledge_layer_schema.py): Authoritative schema and validation regression suite.

### Files Modified

- [`config/hotspot_scoring.yaml`](file:///d:/Projects/Boreas_Nexus/config/hotspot_scoring.yaml): Updated confidence classification threshold tiers.
- [`module_1_thermal/stage1_data_aligner.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/stage1_data_aligner.py): Dynamic UTM projection and memory-passing support.
- [`module_1_thermal/stage2_urban_delineation.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/stage2_urban_delineation.py): Removed `surface_class`.
- [`module_1_thermal/stage3_suhii_calculator.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/stage3_suhii_calculator.py): SUHII anomaly computation with memory passing.
- [`module_1_thermal/stage4_nighttime_thermal.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/stage4_nighttime_thermal.py): Diurnal range and HPI metrics with memory passing.
- [`module_1_thermal/stage5_hotspot_validator.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/stage5_hotspot_validator.py): Replaced boolean flags with `day_hotspot_significance` and `night_hotspot_significance`.
- [`module_1_thermal/hotspot_cluster_generator.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/hotspot_cluster_generator.py): Hotspot clustering with `cluster_centroid_x`, `cluster_centroid_y`, and `cluster_bbox`.
- [`module_1_thermal/city_temperature_percentile.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/city_temperature_percentile.py): Land-only percentile calculation.
- [`module_1_thermal/hotspot_confidence_scorer.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/hotspot_confidence_scorer.py): Deterministic 0-100 scoring for hotspots.
- [`module_1_thermal/stage6_knowledge_export.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/stage6_knowledge_export.py): Authoritative 43-column schema export and 20-point validation.
- [`module_1_thermal/pipeline.py`](file:///d:/Projects/Boreas_Nexus/module_1_thermal/pipeline.py): End-to-end pipeline orchestrator with in-memory GeoDataFrame transfer.
- Unit test suites: [`tests/test_module_1_stage2.py`](file:///d:/Projects/Boreas_Nexus/tests/test_module_1_stage2.py), [`tests/test_module_1_stage3.py`](file:///d:/Projects/Boreas_Nexus/tests/test_module_1_stage3.py), [`tests/test_module_1_stage5.py`](file:///d:/Projects/Boreas_Nexus/tests/test_module_1_stage5.py), [`tests/test_module_1_stage6.py`](file:///d:/Projects/Boreas_Nexus/tests/test_module_1_stage6.py), [`tests/test_module_1_extensions.py`](file:///d:/Projects/Boreas_Nexus/tests/test_module_1_extensions.py).