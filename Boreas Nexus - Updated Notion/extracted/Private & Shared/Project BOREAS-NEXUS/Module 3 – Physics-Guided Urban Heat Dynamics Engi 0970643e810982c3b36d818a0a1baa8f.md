# Module 3 – Physics-Guided Urban Heat Dynamics Engine

---

Module 3 – Physics-Guided Urban Heat Dynamics Engine

## Objective

**Develop a Physics-Informed AI model that learns the dynamic relationship between Land Surface Temperature (LST) and its contributing factors by integrating urban climate physics with machine learning, enabling scientifically consistent heat prediction and future scenario simulation.**

---

# Stage 1 — Urban Climate Physics Rule Engine

### Goal

Identify and formalize the physical mechanisms governing Urban Heat Island formation.

### Theory

Urban heat is governed by the **Surface Energy Balance (SEB)** rather than temperature alone.

The AI must first understand how energy flows through the urban environment.

### Physical Processes

- Incoming Solar Radiation
- Surface Reflection (Albedo)
- Longwave Radiation
- Sensible Heat Flux
- Latent Heat Flux (Evapotranspiration)
- Ground Heat Storage
- Anthropogenic Heat

### Output

```
Urban Climate Physics Rules

↓

Surface Energy Balance Representation
```

---

# Stage 2 — Physics Feature Construction

### Goal

Transform raw satellite and meteorological data into physics-aware features.

### Input

From Module 2

- NDVI
- NDBI
- LULC
- Impervious Surface
- Building Density
- Road Density
- Urban Morphology

Meteorological Variables

- Air Temperature
- Humidity
- Wind Speed
- Solar Radiation
- Air Pressure

Derived Physical Features

- Albedo
- Vegetation Fraction
- Heat Storage Potential
- Evapotranspiration Proxy
- Surface Roughness
- Urban Canyon Indicators

### Output

```
Physics-Aware Feature Space

↓

Urban Heat Physics Dataset
```

---

# Stage 3 — Hybrid Physics + Machine Learning Model

### Goal

Learn the relationship between urban features and Land Surface Temperature while respecting physical laws.

### Theory

Instead of replacing physics,

Machine Learning augments physics.

The model learns

```
LST

=

f(

Physics Features,

Urban Features,

Meteorological Features

)
```

### Model

Hybrid Physics + ML

Possible implementations

- LightGBM + Physics Constraints
- XGBoost + Physics Features
- Physics-Guided Neural Network

*(Final model selection will depend on implementation benchmarking.)*

### Output

```
Physics-Guided Heat Dynamics Model
```

---

# Stage 4 — Heat Dynamics Learning

### Goal

Learn how changes in urban characteristics affect heat behaviour.

### Examples

```
Increase NDVI

↓

Decrease LST
```

```
Increase Impervious Surface

↓

Increase Heat Storage

↓

Increase LST
```

```
Increase Wind Speed

↓

Increase Convective Cooling

↓

Decrease LST
```

The model learns **continuous relationships**, not simple correlations.

### Output

```
Heat Response Functions

↓

Feature Interaction Graphs
```

---

# Stage 5 — Physics Consistency Validation

### Goal

Verify that AI predictions obey known urban climate principles.

### Theory

High prediction accuracy alone is insufficient.

Predictions must also be physically plausible.

### Validation Rules

Examples

✓ Higher NDVI → Lower LST

✓ Higher Albedo → Lower Absorbed Heat

✓ Water Bodies → Cooling Effect

✓ Dense Built-up Areas → Greater Heat Retention

✓ Higher Wind Speed → Greater Convective Cooling

Predictions violating well-established physics are flagged for review rather than accepted blindly.

### Output

```
Physics-Validated Heat Model
```

---

# Stage 6 — Heat Dynamics Knowledge Layer

### Goal

Create a reusable knowledge layer describing how urban heat evolves under different environmental conditions.

### Output

```
Physics-Guided Heat Model

+

Heat Response Curves

+

Feature Interaction Network

+

Physics Validation Report

↓

Heat Dynamics Knowledge Layer
```

This knowledge layer becomes the direct input for **Module 4 – Cooling Scenario Simulation Engine**.

---

# Final Architecture

```
               MODULE 3

    Physics-Guided Urban Heat Dynamics Engine

──────────────────────────────────────────────

Stage 1
Urban Climate Physics Rule Engine

↓

Stage 2
Physics Feature Construction

↓

Stage 3
Hybrid Physics + Machine Learning

↓

Stage 4
Heat Dynamics Learning

↓

Stage 5
Physics Consistency Validation

↓

Stage 6
Heat Dynamics Knowledge Layer

──────────────────────────────────────────────

Output

Physics-Guided Heat Dynamics Model

+

Heat Response Curves

+

Feature Interaction Network

+

Heat Dynamics Knowledge Layer
```

---

# Why this architecture is strong

| Stage | Scientific Question | Why it exists |
| --- | --- | --- |
| **1. Urban Climate Physics Rule Engine** | *What physical laws govern urban heating?* | Establishes the scientific foundation using Surface Energy Balance and heat transfer principles before any AI modeling. |
| **2. Physics Feature Construction** | *How do we represent these physical processes in data?* | Converts satellite, GIS, and meteorological observations into physics-aware features that the AI can learn from. |
| **3. Hybrid Physics + Machine Learning** | *How do urban and atmospheric factors interact to produce LST?* | Learns nonlinear relationships while remaining guided by established urban climate physics. |
| **4. Heat Dynamics Learning** | *How does LST respond when physical drivers change?* | Models the dynamic response of temperature to variations in vegetation, built-up areas, weather, and urban form, enabling future scenario analysis. |
| **5. Physics Consistency Validation** | *Are the learned relationships scientifically valid?* | Ensures predictions align with known urban climate behavior, preventing physically implausible outputs. |
| **6. Heat Dynamics Knowledge Layer** | *How do we package this knowledge for downstream decision-making?* | Produces a reusable representation of urban heat dynamics that powers cooling simulations and intervention optimization. |

---

## 🔒 Module 3 Status: **Locked**

With this, the system now has a coherent scientific progression:

- **Module 1:** *Where are the Urban Heat Hotspots?*
- **Module 2:** *Why do those hotspots exist?*
- **Module 3:** *How do physical processes and urban features interact to produce and evolve urban heat?*

This positions **Module 4** to answer the next logical question:

> **"If we deliberately change those physical drivers (more trees, cool roofs, higher albedo, water bodies), how will the city's heat dynamics change?"**
> 

That transition is exactly what the official hackathon workflow is aiming for.