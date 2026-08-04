"""
Boreas-Nexus Module 1 - Hotspot Cluster Generator (Part 1 Extension)

Purpose: Perform Connected Component Analysis on Getis-Ord Gi* validated hotspot pixels
to identify contiguous spatial hotspot clusters, assign unique identifiers (e.g. HOT_0001),
compute cluster-level morphological/thermal metadata, and generate derived GIS export polygons.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import yaml
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.ndimage import label
from shapely.geometry import Polygon
from shapely.ops import unary_union

from utils.logger import logger
from utils.config_loader import ConfigLoader
from storage.storage_manager import StorageManager


class HotspotClusterGenerator:
    """
    Identifies contiguous spatial hotspot regions using connected component analysis
    and builds cluster-level metadata and visualization vector polygons.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/city.yaml"),
        scoring_config_path: Path | str = Path("config/hotspot_scoring.yaml"),
        input_hotspot_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.config_path = Path(config_path)
        self.scoring_config_path = Path(scoring_config_path)
        self.storage_manager = StorageManager()

        if input_hotspot_path is not None:
            self.input_hotspot_path = Path(input_hotspot_path)
        else:
            self.input_hotspot_path = self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_hotspots.parquet")

        if output_dir is not None:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.storage_manager.get_debug_dir("module_1")

        self.connectivity = self._load_connectivity()
        self.grid_res = self._load_grid_res()

    def _load_connectivity(self) -> int:
        """Loads connectivity parameter (4 or 8) from scoring configuration."""
        p = Path(self.scoring_config_path)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return data.get("hotspot_scoring", {}).get("connectivity", 8)
            except Exception as e:
                logger.warning(f"Failed to read connectivity from {p}: {e}")
                return 8
        return 8

    def _load_grid_res(self) -> float:
        """Loads grid resolution in meters from city configuration."""
        p = Path(self.config_path)
        if p.exists():
            try:
                cfg = ConfigLoader.load_config(p)
                return float(getattr(cfg.preprocessing, "grid_resolution_meters", 100.0))
            except Exception:
                return 100.0
        return 100.0

    def load_stage5_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 5 validated hotspot dataset."""
        candidates = [
            self.input_hotspot_path,
            self.output_dir / "module_1_stage5_hotspots.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_hotspots.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading Stage 5 dataset from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf

        raise FileNotFoundError(f"Stage 5 dataset not found at {self.input_hotspot_path}.")

    def label_clusters(self, gdf: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, pd.DataFrame, gpd.GeoDataFrame]:
        """Runs connected component analysis on validated hotspot pixels."""
        result_gdf = gdf.copy()
        logger.info(f"Running Connected Component Analysis (connectivity={self.connectivity}-neighbour)...")

        if "utm_x_m" not in result_gdf.columns or "utm_y_m" not in result_gdf.columns:
            gdf_utm = result_gdf.to_crs("EPSG:32644")
            result_gdf["utm_x_m"] = gdf_utm.geometry.x
            result_gdf["utm_y_m"] = gdf_utm.geometry.y

        xs = result_gdf["utm_x_m"].values
        ys = result_gdf["utm_y_m"].values
        is_hotspot = result_gdf.get("is_validated_hotspot", pd.Series(False, index=result_gdf.index)).values.astype(bool)

        dx = self.grid_res if self.grid_res > 0 else 100.0
        dy = dx

        min_x = xs.min()
        max_y = ys.max()

        col_indices = np.round((xs - min_x) / dx).astype(int)
        row_indices = np.round((max_y - ys) / dy).astype(int)

        nrows = row_indices.max() + 1
        ncols = col_indices.max() + 1

        grid = np.zeros((nrows, ncols), dtype=bool)
        for r, c, flag in zip(row_indices, col_indices, is_hotspot):
            if flag:
                grid[r, c] = True

        if self.connectivity == 4:
            structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=int)
        else:
            structure = np.ones((3, 3), dtype=int)

        labeled_grid, num_clusters = label(grid, structure=structure)
        logger.info(f"Identified {num_clusters} distinct hotspot clusters.")

        hotspot_ids: List[Optional[str]] = []
        for r, c, flag in zip(row_indices, col_indices, is_hotspot):
            if flag and labeled_grid[r, c] > 0:
                hotspot_ids.append(f"HOT_{labeled_grid[r, c]:04d}")
            else:
                hotspot_ids.append(None)

        result_gdf["hotspot_id"] = hotspot_ids

        cluster_records = []
        cluster_polygons = []

        for cid in range(1, num_clusters + 1):
            hid = f"HOT_{cid:04d}"
            member_mask = (result_gdf["hotspot_id"] == hid)
            members = result_gdf[member_mask]

            if len(members) == 0:
                continue

            cell_boxes = []
            for _, row in members.iterrows():
                x_c = row["utm_x_m"]
                y_c = row["utm_y_m"]
                poly = Polygon([
                    (x_c - dx / 2, y_c - dy / 2),
                    (x_c + dx / 2, y_c - dy / 2),
                    (x_c + dx / 2, y_c + dy / 2),
                    (x_c - dx / 2, y_c + dy / 2)
                ])
                cell_boxes.append(poly)

            cluster_geom = unary_union(cell_boxes)
            area_m2 = float(cluster_geom.area)
            perimeter_m = float(cluster_geom.length)
            size_px = len(members)
            centroid_str = cluster_geom.centroid.wkt
            bbox_str = str(list(cluster_geom.bounds))

            mean_lst = float(members["lst_day_celsius"].mean())
            peak_lst = float(members["lst_day_celsius"].max())
            mean_suhii = float(members["suhii_day_celsius"].mean()) if "suhii_day_celsius" in members.columns else 0.0
            mean_hp = float(members["heat_persistence_index"].mean()) if "heat_persistence_index" in members.columns else 0.0

            rec = {
                "hotspot_id": hid,
                "cluster_area_m2": round(area_m2, 2),
                "cluster_perimeter_m": round(perimeter_m, 2),
                "cluster_size_pixels": size_px,
                "cluster_centroid": centroid_str,
                "cluster_bbox": bbox_str,
                "mean_lst": round(mean_lst, 2),
                "peak_lst": round(peak_lst, 2),
                "mean_suhii": round(mean_suhii, 2),
                "mean_heat_persistence": round(mean_hp, 3),
                "mean_hotspot_confidence_score": 0.0
            }
            cluster_records.append(rec)

            cluster_polygons.append({
                "hotspot_id": hid,
                "cluster_area_m2": round(area_m2, 2),
                "cluster_perimeter_m": round(perimeter_m, 2),
                "cluster_size_pixels": size_px,
                "mean_lst": round(mean_lst, 2),
                "peak_lst": round(peak_lst, 2),
                "geometry": cluster_geom
            })

        df_registry = pd.DataFrame(cluster_records)
        gdf_clusters = gpd.GeoDataFrame(cluster_polygons, crs="EPSG:32644").to_crs("EPSG:4326")

        return result_gdf, df_registry, gdf_clusters

    def run(self) -> Dict[str, Any]:
        """Executes Cluster Generator and exports derived visualization products into exports/."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - EXTENSION 1: HOTSPOT CLUSTER GENERATOR")
        logger.info("=================================================================")

        gdf = self.load_stage5_data()
        gdf_labeled, df_registry, gdf_clusters = self.label_clusters(gdf)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        geojson_out = self.output_dir / "hotspot_clusters.geojson"
        gpkg_out = self.output_dir / "hotspot_clusters.gpkg"

        if len(gdf_clusters) > 0:
            logger.info(f"Exporting derived cluster polygons GeoJSON to {geojson_out}...")
            gdf_clusters.to_file(geojson_out, driver="GeoJSON")
            logger.info(f"Exporting derived cluster polygons GeoPackage to {gpkg_out}...")
            gdf_clusters.to_file(gpkg_out, driver="GPKG")

            export_geojson = self.storage_manager.get_export_filepath("geojson", "hotspot_clusters.geojson")
            export_gpkg = self.storage_manager.get_export_filepath("gpkg", "hotspot_clusters.gpkg")
            gdf_clusters.to_file(export_geojson, driver="GeoJSON")
            gdf_clusters.to_file(export_gpkg, driver="GPKG")

        parquet_out = self.output_dir / "module_1_stage5_labeled.parquet"
        logger.info(f"Saving labeled dataset to {parquet_out}...")
        df_export = pd.DataFrame(gdf_labeled.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        metrics = {
            "status": "SUCCESS",
            "total_clusters_found": len(df_registry),
            "total_hotspot_pixels": int((gdf_labeled["hotspot_id"].notnull()).sum()),
            "connectivity": self.connectivity,
            "clusters_geojson": str(geojson_out),
            "clusters_gpkg": str(gpkg_out),
            "output_parquet": str(parquet_out)
        }

        logger.info(f"Hotspot Cluster Generator complete! Identified {len(df_registry)} clusters.")
        logger.info("=================================================================")
        return metrics
