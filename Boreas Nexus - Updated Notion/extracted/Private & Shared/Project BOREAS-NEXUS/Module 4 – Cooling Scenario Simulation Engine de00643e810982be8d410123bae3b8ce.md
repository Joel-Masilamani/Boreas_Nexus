# Module 4 – Cooling Scenario Simulation Engine

---

Module 4 – Cooling Scenario Simulation Engine

## Objective

**Generate, simulate, and scientifically validate multiple urban cooling intervention scenarios by combining search-driven optimization, a Physics-Guided AI surrogate model, and high-fidelity urban climate simulation models to estimate their impact on urban heat.**

---

# Stage 1 — Search-Driven Scenario Generation

### Goal

Intelligently explore thousands of possible urban cooling interventions instead of relying on manual or random scenario creation.

### Theory

The intervention search space is extremely large and cannot be explored exhaustively.

Use optimization-driven search to generate promising intervention combinations.

### Search Methods

- Genetic Algorithm (GA)
- Bayesian Optimization (BO)

### Example Interventions

- Increase Tree Canopy
- Green Roofs
- Cool Roofs
- Reflective Pavements
- Water Bodies
- Urban Greening

### Optimization Loop

The search operates iteratively:

```
Generate Candidates

↓

Evaluate Candidates

↓

Select Best Candidates

↓

Generate Improved Candidates

↓

Repeat until Convergence
```

### Termination Criteria

- Maximum generations
- Convergence threshold
- Computational budget

### Output

```
Candidate Cooling Scenarios
```

---

# Stage 2 — Scenario Translator

### Goal

Convert urban planning interventions into model-specific physical representations.

### Theory

Different models require different representations of the same intervention.

Example

Planner Input

```
Increase Tree Cover by 20%
```

Module 3 Requires

- NDVI Increase
- Vegetation Fraction
- Heat Storage Reduction

InVEST Requires

- Updated Land Use/Land Cover
- Biophysical Parameters

SOLWEIG Requires

- Updated Tree Geometry
- Canopy Height
- DSM / Shadow Geometry

### Output

```
Model-Ready Scenario Representations
```

---

# Stage 3 — Fast Scenario Evaluation

### Goal

Rapidly evaluate thousands of candidate scenarios using the Physics-Guided Heat Dynamics Model developed in Module 3.

### Theory

Module 3 acts as a surrogate model.

Instead of running expensive physical simulations for every candidate,

use AI to estimate

```
Scenario

↓

Predicted ΔLST
```

### Output

```
Predicted Cooling Performance

(ΔLST)
```

---

# Stage 4 — Feasibility Filtering & Thermal Ranking

### Goal

Filter unrealistic scenarios and identify the most thermally effective candidates.

### Feasibility Constraints

- Available Land
- Urban Planning Regulations
- Maximum Intervention Limits
- Physical Constraints

### Ranking Metric

Primary Metric

- Predicted Cooling (ΔLST)

Only the highest-ranked scenarios proceed to detailed physics validation.

### Output

```
Top-N Candidate Scenarios
```

---

# Stage 5 — City-Scale Physics Validation (InVEST)

### Goal

Validate promising scenarios using a physics-based urban cooling model.

### Theory

Module 3 predicts

Land Surface Temperature.

InVEST estimates

Near-Surface Air Temperature (ΔTair)

and urban cooling capacity.

### Purpose

- Validate large-scale cooling behaviour
- Capture air temperature response
- Evaluate spatial cooling diffusion

### Output

```
Validated ΔTair

City-Scale Cooling Assessment
```

---

# Stage 6 — Pedestrian-Scale Physics Validation (SOLWEIG)

### Goal

Evaluate thermal comfort at the pedestrian level.

### Theory

SOLWEIG estimates

Mean Radiant Temperature (Tmrt)

using

- 3D Urban Geometry
- Building Shadows
- Solar Radiation
- Reflected Radiation

### Purpose

Assess

Human Thermal Comfort

rather than surface temperature alone.

### Output

```
Validated Tmrt

Pedestrian Thermal Comfort Assessment
```

---

# Stage 7 — Unified Scenario Evaluation Report

### Goal

Combine AI predictions, physics validation, and planning intelligence into a single decision-ready report.

### Thermal Metrics

- ΔLST (Module 3)
- ΔTair (InVEST)
- ΔTmrt (SOLWEIG)

### Agreement Analysis

- Directional Agreement
- Scenario Ranking Agreement
- Physics Consistency Flags

### Auxiliary Data Layer

Integrate

- Intervention Cost
- Population Exposure
- Vulnerability Maps
- Energy Impact
- Land Availability

### Output

```
Comprehensive Scenario Evaluation Report

↓

Scenario Knowledge Layer
```

---

# Stage 8 — Disagreement Logging & Active Learning

### Goal

Continuously improve Module 3 using disagreements between AI predictions and physics-based simulations.

### Theory

Physics validation acts as a teacher for the surrogate model.

Significant disagreements are stored for future model improvement.

### Active Learning Strategy

- Log disagreement cases
- Build validation dataset
- Periodic offline retraining
- Redeploy improved Module 3

*(Retraining is batched, not performed after every simulation.)*

### Output

```
Validated Training Dataset

↓

Continuous Improvement Pipeline
```

---

# Final Architecture

```
                    MODULE 4

         Cooling Scenario Simulation Engine

────────────────────────────────────────────────

Stage 1
Search-Driven Scenario Generation
(GA / Bayesian Optimization)

        │
        ▼

Stage 2
Scenario Translator
(Planning Actions → Model Inputs)

        │
        ▼

Stage 3
Fast Scenario Evaluation
(Module 3 Surrogate)

        ▲
        │
Fitness Feedback Loop
(Search Optimization)

        ▼

Stage 4
Feasibility Filtering &
Thermal Ranking

        ▼

Stage 5
City-Scale Physics Validation
(InVEST)

        ▼

Stage 6
Pedestrian-Scale Physics Validation
(SOLWEIG)

        ▼

Stage 7
Unified Scenario Evaluation Report

        ▲
        │
Auxiliary Data Layer
(Cost, Population,
Energy, Land Availability)

        ▼

Stage 8
Disagreement Logging &
Active Learning

────────────────────────────────────────────────

Output

Validated Cooling Scenario Knowledge Layer

+

Scenario Evaluation Reports

+

Physics-Validated Cooling Predictions
```

---

# Why this architecture is strong

| Stage | Scientific Question | Why it exists |
| --- | --- | --- |
| **1. Search-Driven Scenario Generation** | *Which intervention combinations should we explore?* | Efficiently searches a vast intervention space using optimization algorithms instead of random sampling. |
| **2. Scenario Translator** | *How do planning interventions become model inputs?* | Converts urban planning actions into the physical representations required by AI and physics models. |
| **3. Fast Scenario Evaluation** | *How can thousands of scenarios be evaluated quickly?* | Uses the Physics-Guided Heat Dynamics Model as a fast surrogate to estimate cooling without expensive simulations. |
| **4. Feasibility Filtering & Thermal Ranking** | *Which scenarios are physically and operationally realistic?* | Removes infeasible interventions and identifies the most promising candidates for detailed validation. |
| **5. City-Scale Physics Validation (InVEST)** | *How do interventions affect near-surface air temperature across the city?* | Validates large-scale cooling behaviour and captures air temperature changes and spatial diffusion effects. |
| **6. Pedestrian-Scale Physics Validation (SOLWEIG)** | *How will people actually experience the intervention?* | Evaluates human thermal comfort by modeling radiation, shading, and urban geometry. |
| **7. Unified Scenario Evaluation Report** | *How do we integrate thermal performance with planning intelligence?* | Combines AI predictions, physics validation, and socio-economic indicators into a decision-ready assessment. |
| **8. Disagreement Logging & Active Learning** | *How can the surrogate model improve over time?* | Uses discrepancies between AI and physics models to periodically retrain and strengthen Module 3. |

---

# 🔒 Module 4 Status: **LOCKED**

The project now follows a scientifically coherent progression:

- **Module 1:** **Where** are the Urban Heat Hotspots?
- **Module 2:** **Why** do those hotspots exist?
- **Module 3:** **How** do physical processes govern urban heat?
- **Module 4:** **What happens if** we redesign the city using different cooling interventions?

The remaining **Module 5** now has a single responsibility:

> **Given multiple validated cooling scenarios, which intervention (or combination of interventions) should be implemented to maximize cooling while balancing cost, feasibility, population impact, and long-term sustainability?**
> 

This clean separation of responsibilities is what gives the overall system a research-grade architecture rather than a collection of disconnected AI models.