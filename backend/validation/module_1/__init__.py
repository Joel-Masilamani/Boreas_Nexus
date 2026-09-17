"""
Module 1 Validation Layer: Urban Heat Island & Hotspot Delineation

Standalone validation engines for independently verifying SUHII urban-rural baselines,
Getis-Ord Gi* z-scores, Moran's I spatial autocorrelation, DBSCAN cluster topology,
diurnal thermal persistence, and GeoParquet schema contracts.
"""

from validation.module_1.pipeline import Module1ValidationPipeline

__all__ = ["Module1ValidationPipeline"]
