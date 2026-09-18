import { DiurnalFluxPoint, HotspotCluster, ThermalDynamicsModel } from '../../types';

/**
 * Deterministic Physics Demonstration Service for Module 3 (Thermal Dynamics)
 * Implements surface energy balance partitioning:
 * Rn = H + λE + G
 * Where:
 * Rn = Net radiation flux (W/m²)
 * H  = Sensible heat flux (warming the air)
 * λE = Latent heat flux (evapotranspirative cooling)
 * G  = Ground / storage heat flux (stored in urban fabric)
 *
 * All calculations are 100% deterministic (NO Math.random()).
 */
class PhysicsService {
  calculateThermalDynamics(hotspot: HotspotCluster): ThermalDynamicsModel {
    const baselineMeanLST = hotspot.mean_lst;
    const buildingDensity = hotspot.mean_building_density || 0.45;
    const ndvi = Math.max(0.05, hotspot.mean_ndvi || 0.2);

    // Surface Albedo: inverse relation with built-up imperviousness
    // Higher building density = lower effective albedo due to urban canyon trapping
    const albedo = Number((0.18 - (buildingDensity * 0.08) + (ndvi * 0.04)).toFixed(3));

    // Peak solar radiation for Chennai latitude (13°N) in May peak dry summer
    const peakSolarRadiation = 920; // W/m²
    const netRadiation = Math.round(peakSolarRadiation * (1 - albedo) - 140); // minus net longwave loss (~140 W/m²)

    // Bowen Ratio (β = H / λE): High in dense urban (2.0 - 4.5), low in vegetated (0.4 - 0.8)
    const bowenRatio = Number((1.2 + (buildingDensity * 2.8) - (ndvi * 1.8)).toFixed(2));

    // Ground heat flux G: roughly 15-25% of Rn in built urban environments
    const groundHeatFraction = 0.15 + (buildingDensity * 0.10);
    const groundHeat = Math.round(netRadiation * groundHeatFraction);

    // Remaining available energy for turbulent fluxes (H + λE)
    const availableEnergy = netRadiation - groundHeat;

    // From Bowen ratio: H = β * λE => availableEnergy = λE * (1 + β)
    const latentHeat = Math.round(availableEnergy / (1 + bowenRatio));
    const sensibleHeat = availableEnergy - latentHeat;

    // Approximate 2m air temperature from LST and sensible flux coupling
    const airTemp = Number((baselineMeanLST - 3.8 + (sensibleHeat / 220)).toFixed(1));

    // Generate 24-hour diurnal cycle curve (00:00 to 23:00)
    const diurnalCycle: DiurnalFluxPoint[] = [];

    for (let h = 0; h < 24; h++) {
      const timeLabel = `${h.toString().padStart(2, '0')}:00`;
      
      // Solar elevation factor: peak at solar noon (12:00)
      let solarFactor = 0;
      if (h >= 6 && h <= 18) {
        // Sine wave for daylight hours
        solarFactor = Math.sin(((h - 6) / 12) * Math.PI);
      }

      // Hourly Net Radiation (negative at night due to terrestrial longwave cooling)
      const hNetRad = Math.round(solarFactor > 0 ? (netRadiation * solarFactor) : -55);

      let hSensible = 0;
      let hLatent = 0;
      let hGround = 0;

      if (solarFactor > 0) {
        hGround = Math.round(hNetRad * groundHeatFraction);
        const hAvailable = hNetRad - hGround;
        hLatent = Math.round(hAvailable / (1 + bowenRatio));
        hSensible = hAvailable - hLatent;
      } else {
        // At night, ground heat flux releases upward (G < 0), driving nocturnal canopy warming
        hGround = Math.round(hNetRad * 0.55);
        hSensible = Math.round(hNetRad * 0.40);
        hLatent = Math.round(hNetRad * 0.05);
      }

      // Hourly surface temperature and air temperature
      const tempWave = Math.sin(((h - 9) / 24) * 2 * Math.PI); // Min at 06:00, max at 15:00
      const hSurfTemp = Number((baselineMeanLST + (tempWave * 7.5)).toFixed(1));
      const hAirTemp = Number((airTemp + (tempWave * 5.2)).toFixed(1));

      diurnalCycle.push({
        hour: h,
        timeLabel,
        netRadiation: hNetRad,
        sensibleHeat: hSensible,
        latentHeat: hLatent,
        groundHeat: hGround,
        surfaceTemp: hSurfTemp,
        airTemp: hAirTemp,
      });
    }

    return {
      surfaceTemp: baselineMeanLST,
      airTemp,
      netRadiation,
      sensibleHeat,
      latentHeat,
      groundHeat,
      bowenRatio,
      albedo,
      diurnalCycle,
    };
  }
}

export const physicsService = new PhysicsService();
