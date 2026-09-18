import { DecisionPreset, HotspotCluster, PlanningActionItem } from '../../types';
import { scenarioService } from './scenarioService';

/**
 * Deterministic Decision Support Service for Module 5 (Decision Center)
 * Translates scenario outputs into multi-criteria planning strategies,
 * Pareto trade-offs (cooling vs cost), and prioritized action plans.
 * 
 * 100% deterministic (NO Math.random()).
 */
class DecisionService {
  getStandardPresets(hotspot: HotspotCluster, budgetCr = 25): DecisionPreset[] {
    const presetsConfig = [
      {
        id: 'cool_roof_strategy',
        name: 'Cool Roof Fast-Track',
        tagline: 'High Albedo Rapid Deployment',
        description: 'Maximizes high-reflectance roof coatings (albedo 0.15 -> 0.70) across dense residential and commercial roofs with minimal capital outlay.',
        interventions: {
          coolRoofCoverage: 65,
          greenRoofCoverage: 10,
          treeCanopyCoverage: 15,
          permeablePavementCoverage: 10,
          waterInfrastructureCoverage: 0,
          budgetCr,
        },
      },
      {
        id: 'green_infrastructure',
        name: 'Ecological Green Corridor',
        tagline: 'Nature-Based Evapotranspiration',
        description: 'Prioritizes intensive tree canopy and green roofs along streets and open spaces to maximize human thermal comfort and biodiversity.',
        interventions: {
          coolRoofCoverage: 20,
          greenRoofCoverage: 35,
          treeCanopyCoverage: 45,
          permeablePavementCoverage: 20,
          waterInfrastructureCoverage: 10,
          budgetCr,
        },
      },
      {
        id: 'hybrid_strategy',
        name: 'Balanced Hybrid Strategy (Recommended)',
        tagline: 'Optimal Cost-Cooling Pareto Front',
        description: 'Combines extensive cool roofs with strategic urban street tree canopy and permeable parking pavements to balance cooling velocity with capital cost.',
        interventions: {
          coolRoofCoverage: 50,
          greenRoofCoverage: 20,
          treeCanopyCoverage: 30,
          permeablePavementCoverage: 25,
          waterInfrastructureCoverage: 5,
          budgetCr,
        },
      },
      {
        id: 'maximum_cooling',
        name: 'Maximum Thermal Abatement',
        tagline: 'Comprehensive Multi-Layer Mitigation',
        description: 'Full-spectrum intervention suite integrating cool surfaces, maximum canopy infill, and blue retention swales for critical persistent heat islands.',
        interventions: {
          coolRoofCoverage: 75,
          greenRoofCoverage: 40,
          treeCanopyCoverage: 55,
          permeablePavementCoverage: 40,
          waterInfrastructureCoverage: 15,
          budgetCr,
        },
      },
    ];

    return presetsConfig.map(p => {
      const res = scenarioService.evaluateScenario(hotspot, p.interventions);
      return {
        id: p.id,
        name: p.name,
        tagline: p.tagline,
        description: p.description,
        coolingImpact: res.lstReduction,
        costCr: res.totalCostCr,
        coveragePct: Math.round(
          (p.interventions.coolRoofCoverage + p.interventions.treeCanopyCoverage + p.interventions.greenRoofCoverage) / 3
        ),
        feasibilityPct: res.feasibilityScore,
        equityPct: res.equityScore,
        interventions: p.interventions,
      };
    });
  }

  getParetoCurve(hotspot: HotspotCluster, budgetCr = 25) {
    // Generate deterministic Pareto points varying budget & intensity
    const points = [];
    const steps = [
      { label: 'Baseline', coolRoof: 0, canopy: 0, greenRoof: 0, perm: 0, water: 0 },
      { label: 'Micro-Intervention', coolRoof: 20, canopy: 5, greenRoof: 0, perm: 5, water: 0 },
      { label: 'Cool Roof Minimal', coolRoof: 40, canopy: 10, greenRoof: 5, perm: 10, water: 0 },
      { label: 'Moderate Hybrid', coolRoof: 50, canopy: 20, greenRoof: 15, perm: 20, water: 5 },
      { label: 'Recommended Hybrid', coolRoof: 55, canopy: 30, greenRoof: 20, perm: 25, water: 5 },
      { label: 'Dense Canopy', coolRoof: 40, canopy: 45, greenRoof: 25, perm: 20, water: 10 },
      { label: 'Comprehensive Max', coolRoof: 75, canopy: 50, greenRoof: 35, perm: 35, water: 15 },
    ];

    for (const step of steps) {
      const interventions = {
        coolRoofCoverage: step.coolRoof,
        greenRoofCoverage: step.greenRoof,
        treeCanopyCoverage: step.canopy,
        permeablePavementCoverage: step.perm,
        waterInfrastructureCoverage: step.water,
        budgetCr,
      };
      const res = scenarioService.evaluateScenario(hotspot, interventions);
      points.push({
        name: step.label,
        costCr: res.totalCostCr,
        coolingLST: res.lstReduction,
        airTempDrop: res.airTempReduction,
        feasibility: res.feasibilityScore,
        withinBudget: res.totalCostCr <= budgetCr,
      });
    }

    return points;
  }

  getPlanningActions(hotspot: HotspotCluster, selectedPreset: DecisionPreset): PlanningActionItem[] {
    const areaHa = Math.max(5, (hotspot.cluster_area_m2 || 50000) / 10000);
    const actions: PlanningActionItem[] = [
      {
        id: 'act-01',
        action: 'Mandate High-Albedo Solar Reflective Coating (SRI > 78) on Municipal & Commercial Roofs',
        type: 'Cool Roof Mandate',
        targetCoverage: `${selectedPreset.interventions.coolRoofCoverage}% of built roof area (${Math.round(areaHa * selectedPreset.interventions.coolRoofCoverage / 100)} ha)`,
        priority: 'Immediate',
        costEstimateCr: Number(((selectedPreset.interventions.coolRoofCoverage / 100) * areaHa * 0.12).toFixed(2)),
        coolingYield: `-${((selectedPreset.interventions.coolRoofCoverage / 100) * 2.6).toFixed(1)}°C LST`,
        status: 'Recommended',
      },
      {
        id: 'act-02',
        action: 'Street Tree Corridor Planting along Primary & Secondary Arterial Roadways',
        type: 'Urban Forestry',
        targetCoverage: `${selectedPreset.interventions.treeCanopyCoverage}% canopy target along ROW (${Math.round(areaHa * selectedPreset.interventions.treeCanopyCoverage / 100)} ha)`,
        priority: 'Phase 1',
        costEstimateCr: Number(((selectedPreset.interventions.treeCanopyCoverage / 100) * areaHa * 0.35).toFixed(2)),
        coolingYield: `-${((selectedPreset.interventions.treeCanopyCoverage / 100) * 3.8).toFixed(1)}°C LST`,
        status: 'Recommended',
      },
      {
        id: 'act-03',
        action: 'Permeable Interlocking Paver Retrofits on Surface Parking & Pedestrian Walkways',
        type: 'Pavement Retrofit',
        targetCoverage: `${selectedPreset.interventions.permeablePavementCoverage}% of public paved surfaces`,
        priority: 'Phase 2',
        costEstimateCr: Number(((selectedPreset.interventions.permeablePavementCoverage / 100) * areaHa * 0.22).toFixed(2)),
        coolingYield: `-${((selectedPreset.interventions.permeablePavementCoverage / 100) * 1.4).toFixed(1)}°C LST`,
        status: 'Evaluating',
      },
    ];

    if (selectedPreset.interventions.waterInfrastructureCoverage > 0) {
      actions.push({
        id: 'act-04',
        action: 'Construct Decentralized Micro-Swales & Rainwater Retention Infiltration Basins',
        type: 'Blue Infrastructure',
        targetCoverage: `${selectedPreset.interventions.waterInfrastructureCoverage}% runoff buffer zone`,
        priority: 'Phase 2',
        costEstimateCr: Number(((selectedPreset.interventions.waterInfrastructureCoverage / 100) * areaHa * 0.65).toFixed(2)),
        coolingYield: `-${((selectedPreset.interventions.waterInfrastructureCoverage / 100) * 3.5).toFixed(1)}°C LST`,
        status: 'Permitting Required',
      });
    }

    return actions;
  }
}

export const decisionService = new DecisionService();
