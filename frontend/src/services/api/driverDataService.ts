import { DriverAuditData, HotspotCluster } from '../../types';
import { heatDataService } from './heatDataService';

class DriverDataService {
  private auditCache: DriverAuditData | null = null;

  async getDriverAudit(): Promise<DriverAuditData> {
    if (this.auditCache) return this.auditCache;
    try {
      const res = await fetch('/data/driver_audit.json');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      this.auditCache = await res.json();
      return this.auditCache!;
    } catch (err) {
      console.error('DriverDataService: Failed to fetch driver_audit.json', err);
      throw new Error('Unable to load driver model validation audits.');
    }
  }

  async getDriverProfileForHotspot(hotspotId: string): Promise<HotspotCluster | null> {
    return await heatDataService.getHotspotById(hotspotId);
  }
}

export const driverDataService = new DriverDataService();
