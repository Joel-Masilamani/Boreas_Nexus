import { HotspotCluster, ScenarioInterventions, ScenarioResult } from '../../types';

/**
 * Deterministic Cooling Scenario Simulation Service for Module 4 (Scenario Lab)
 * Calculates cooling responses to cool roofs, tree canopy, green roofs,
 * permeable pavements, and urban water infrastructure.
 * 
 * Based on empirical urban climatology mitigation models.
 * Strictly 100% deterministic (NO Math.random()).
 */
class ScenarioService {
  /**
   * Run simulation model
   */
  evaluateScenario(hotspot: HotspotCluster, interventions: ScenarioInterventions): ScenarioResult {
    const baselineLST = hotspot.mean_lst;
    const baselineSUHII = hotspot.mean_suhii;
    const baselineAirTemp = Number((baselineLST - 3.5).toFixed(1));

    // Area of hotspot in hectares (1 hectare = 10,000 m²)
    const areaHa = Math.max(5, (hotspot.cluster_area_m2 || 50000) / 10000);

    // Unit implementation costs per hectare (in ₹ Crore):
    // Cool roof coating: ~₹0.12 Cr / ha of roof
    // Green roof extensive: ~₹0.48 Cr / ha
    // Mature urban tree planting & maintenance: ~₹0.35 Cr / ha
    // Permeable pavement retrofitting: ~₹0.22 Cr / ha
    // Micro-water bodies / swales: ~₹0.65 Cr / ha
    const costCoolRoof = (interventions.coolRoofCoverage / 100) * areaHa * 0.12;
    const costGreenRoof = (interventions.greenRoofCoverage / 100) * areaHa * 0.48;
    const costTreeCanopy = (interventions.treeCanopyCoverage / 100) * areaHa * 0.35;
    const costPermPavement = (interventions.permeablePavementCoverage / 100) * areaHa * 0.22;
    const costWater = (interventions.waterInfrastructureCoverage / 100) * areaHa * 0.65;

    const totalCostCr = Number((costCoolRoof + costGreenRoof + costTreeCanopy + costPermPavement + costWater).toFixed(2));
    const budgetRemainingCr = Number((interventions.budgetCr - totalCostCr).toFixed(2));

    // Cooling Yield Coefficients (Degrees Celsius drop per 100% coverage):
    // Tree canopy has highest cooling through combined shading + latent transpiration: ~3.8°C
    // Water infrastructure: ~3.5°C
    // Cool roof (albedo shift 0.15 -> 0.70): ~2.6°C
    // Green roof: ~2.1°C
    // Permeable pavement: ~1.4°C
    const deltaLST_Tree = (interventions.treeCanopyCoverage / 100) * 3.8;
    const deltaLST_Water = (interventions.waterInfrastructureCoverage / 100) * 3.5;
    const deltaLST_CoolRoof = (interventions.coolRoofCoverage / 100) * 2.6;
    const deltaLST_GreenRoof = (interventions.greenRoofCoverage / 100) * 2.1;
    const deltaLST_PermPavement = (interventions.permeablePavementCoverage / 100) * 1.4;

    // Combined cooling with diminishing return factor for overlapping infrastructure
    const rawCooling = deltaLST_Tree + deltaLST_Water + deltaLST_CoolRoof + deltaLST_GreenRoof + deltaLST_PermPavement;
    // Saturation curve: maximum thermal cooling cap of ~6.5°C for localized urban microclimate
    const totalCoolingLST = Number((6.5 * (1 - Math.exp(-rawCooling / 5.2))).toFixed(2));

    const projectedLST = Number((baselineLST - totalCoolingLST).toFixed(2));
    const suhiiReduction = Number(Math.min(baselineSUHII, totalCoolingLST).toFixed(2));
    const projectedSUHII = Number(Math.max(0, baselineSUHII - suhiiReduction).toFixed(2));

    // 2m Air Temperature reduction is coupled to LST cooling (~65% efficiency transfer)
    const airTempReduction = Number((totalCoolingLST * 0.65).toFixed(2));
    const projectedAirTemp = Number((baselineAirTemp - airTempReduction).toFixed(1));

    // Feasibility score (penalized if budget exceeded or unrealistic canopy coverage)
    let feasibility = 100;
    if (totalCostCr > interventions.budgetCr) {
      const overspendRatio = (totalCostCr - interventions.budgetCr) / interventions.budgetCr;
      feasibility -= Math.min(60, Math.round(overspendRatio * 80));
    }
    if (interventions.treeCanopyCoverage > 60) {
      feasibility -= Math.round((interventions.treeCanopyCoverage - 60) * 0.8);
    }
    const feasibilityScore = Math.max(15, Math.min(98, feasibility));

    // Social & Ecological Equity score
    const equityScore = Math.round(
      Math.min(95, 30 + (interventions.treeCanopyCoverage * 0.35) + (interventions.waterInfrastructureCoverage * 0.25) + (interventions.coolRoofCoverage * 0.15))
    );

    // Estimated annual CO2 offset tons
    const co2OffsetTonsYear = Math.round(
      (interventions.treeCanopyCoverage * areaHa * 0.45) + (interventions.greenRoofCoverage * areaHa * 0.22)
    );

    return {
      baselineLST,
      projectedLST,
      lstReduction: totalCoolingLST,
      baselineAirTemp,
      projectedAirTemp,
      airTempReduction,
      baselineSUHII,
      projectedSUHII,
      suhiiReduction,
      totalCostCr,
      budgetRemainingCr,
      feasibilityScore,
      equityScore,
      co2OffsetTonsYear,
    };
  }
}

export const scenarioService = new ScenarioService();
