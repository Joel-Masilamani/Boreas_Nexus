# Module 1 - Hybrid Hotspot Identification Engine.

---

> **Module 1 – Urban Heat Hotspot Identification Engine**
> 

Now let's break it into stages.

---

# Module 1 – Urban Heat Hotspot Identification Engine

## Objective

**Identify statistically significant Urban Heat Hotspots using thermal remote sensing while preserving the scientific definition of the Urban Heat Island (UHI).**

---

# Stage 1 — Data Acquisition & Preprocessing

### Goal

Collect and standardize all thermal and spatial datasets required for hotspot identification.

### Input

- Landsat 8 LST
- ECOSTRESS LST (optional validation)
- Sentinel-2 Land Cover / ESA WorldCover
- Administrative Boundary
- OpenStreetMap / GHSL

### Output

```
Study Area

↓

Aligned Raster Layers

↓

Ready for Analysis
```

---

# Stage 2 — Urban–Non-Urban Delineation

### Goal

Separate urban surfaces from surrounding rural landscapes.

### Theory

Urban Heat Island is defined as

> Urban Temperature − Rural Temperature
> 

Therefore we must know

- Urban pixels
- Rural pixels

before any heat analysis.

### Method

Use

- ESA WorldCover
    
    or
    
- Sentinel-2 Land Cover

Generate

```
Urban Mask

+

Rural Mask
```

### Output

```
Urban Pixels

Rural Pixels
```

This follows the methodology used in Dr. Asfa Siddiqui's work.

---

# Stage 3 — Surface Urban Heat Island (SUHII) Computation

### Goal

Establish the physical Urban Heat Island baseline.

### Theory

Compute

```
SUHII

=

Urban Mean LST

-

Rural Mean LST
```

This answers

> Is the city hotter than its surrounding landscape?
> 

### Output

```
City-Level UHI Intensity

↓

Urban Heat Baseline
```

This stage tells us **whether a UHI exists**, not where the hottest neighborhoods are.

---

# Stage 4 — Night-Time Thermal Behaviour Analysis

### Goal

Capture persistent urban heat retention.

### Theory

Cities store heat during the day and release it after sunset.

Night-time LST is therefore a stronger indicator of urbanization effects than daytime LST, as highlighted in Dr. Asfa Siddiqui's study.

### Method

Compare

- Day LST
- Night LST

Generate

```
Night-Time Heat Persistence Map
```

### Output

```
Persistent Heat Zones
```

This removes locations that become hot only temporarily during the day.

---

# Stage 5 — Spatial Hotspot Validation

### Goal

Identify statistically significant hotspot clusters.

### Theory

A hotspot is **not** a single hot pixel.

It is

> a spatial cluster of consistently high temperatures.
> 

### Method

Apply

**Getis–Ord Gi***

The algorithm evaluates

- pixel temperature
- neighboring temperatures

and computes

- Z-score
- P-value

### Decision

Only clusters with statistically significant Z-scores are retained.

### Output

```
Validated Urban Heat Hotspots
```

This removes isolated noisy pixels.

---

# Stage 6 —**Urban Heat Hotspot Knowledge Layer**

Merge the outputs from previous stages.

```
Urban Mask

+

SUHII

+

Night-Time Heat

+

Gi* Clusters

↓

Final Urban Heat Hotspot Map
```

This becomes the official input for Module 2.

---

# Final Architecture

```
                 MODULE 1

     Urban Heat Hotspot Identification Engine

──────────────────────────────────────────────

Stage 1
Data Acquisition & Preprocessing

↓

Stage 2
Urban–Non-Urban Delineation

↓

Stage 3
Surface Urban Heat Island (SUHII)

↓

Stage 4
Night-Time Thermal Behaviour Analysis

↓

Stage 5
Spatial Hotspot Validation
(Getis-Ord Gi*)

↓

Stage 6
**Urban Heat Hotspot Knowledge Layer**
──────────────────────────────────────────────
Output

Validated Urban Heat Hotspot Regions
```

---

# Why this architecture is strong

Each stage has a distinct scientific purpose:

| Stage | Scientific Question | Why it exists |
| --- | --- | --- |
| **1. Data Acquisition & Preprocessing** | *Do we have clean, aligned geospatial data?* | Ensures all datasets share the same projection, resolution, and study area. |
| **2. Urban–Non-Urban Delineation** | *What is urban and what is rural?* | Establishes the physical basis for UHI analysis. |
| **3. SUHII Computation** | *Does this city exhibit an Urban Heat Island effect?* | Provides the city-level thermal baseline. |
| **4. Night-Time Thermal Behaviour** | *Which areas retain heat after sunset?* | Identifies persistent urban heating rather than temporary daytime warming. |
| **5. Spatial Hotspot Validation (Gi*)** | *Which hot areas are statistically significant clusters?* | Filters noise and confirms neighborhood-scale hotspots. |
| **6. Hotspot Map Generation** | *Where are the validated Urban Heat Hotspots?* | Produces the final hotspot layer for downstream AI analysis. |

---

## One refinement I recommend

Instead of calling Stage 6 simply **"Urban Heat Hotspot Map,"** call it:

> **Urban Heat Hotspot Knowledge Layer**
> 

Why?

Because Module 2 will consume it as **knowledge**, not just as an image. It becomes a geospatial layer containing validated hotspot regions that the next module can explain, analyze, and ultimately use to recommend interventions. This framing also reinforces that your system is building a **decision-support pipeline**, not just generating maps.