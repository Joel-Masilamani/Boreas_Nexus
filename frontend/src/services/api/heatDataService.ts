import { CityKPIs, HotspotCluster, ThermalGridPoint } from '../../types';

class HeatDataService {
  private cityKPIsCache: CityKPIs | null = null;
  private hotspotsGeoJSONCache: GeoJSON.FeatureCollection | null = null;
  private hotspotRegistryCache: HotspotCluster[] | null = null;
  private thermalGridCache: ThermalGridPoint[] | null = null;

  async getCityKPIs(): Promise<CityKPIs> {
    if (this.cityKPIsCache) return this.cityKPIsCache;
    try {
      const res = await fetch('/data/city_kpis.json');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      this.cityKPIsCache = await res.json();
      return this.cityKPIsCache!;
    } catch (err) {
      console.error('HeatDataService: Failed to fetch city_kpis.json', err);
      throw new Error('Unable to load observed city thermal metadata.');
    }
  }

  async getHotspotsGeoJSON(): Promise<GeoJSON.FeatureCollection> {
    if (this.hotspotsGeoJSONCache) return this.hotspotsGeoJSONCache;
    try {
      const res = await fetch('/data/hotspots.geojson');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      this.hotspotsGeoJSONCache = await res.json();
      return this.hotspotsGeoJSONCache!;
    } catch (err) {
      console.error('HeatDataService: Failed to fetch hotspots.geojson', err);
      throw new Error('Unable to load observed hotspot cluster boundaries.');
    }
  }

  async getHotspotRegistry(): Promise<HotspotCluster[]> {
    if (this.hotspotRegistryCache) return this.hotspotRegistryCache;
    try {
      const res = await fetch('/data/hotspot_registry.json');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      this.hotspotRegistryCache = await res.json();
      return this.hotspotRegistryCache!;
    } catch (err) {
      console.error('HeatDataService: Failed to fetch hotspot_registry.json', err);
      throw new Error('Unable to load observed hotspot registry.');
    }
  }

  async getThermalGrid(): Promise<ThermalGridPoint[]> {
    if (this.thermalGridCache) return this.thermalGridCache;
    try {
      const res = await fetch('/data/thermal_grid.json');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      this.thermalGridCache = await res.json();
      return this.thermalGridCache!;
    } catch (err) {
      console.error('HeatDataService: Failed to fetch thermal_grid.json', err);
      throw new Error('Unable to load observed thermal grid points.');
    }
  }

  async getHotspotById(hotspotId: string): Promise<HotspotCluster | null> {
    const registry = await this.getHotspotRegistry();
    return registry.find(h => h.hotspot_id === hotspotId) || null;
  }
}

export const heatDataService = new HeatDataService();
