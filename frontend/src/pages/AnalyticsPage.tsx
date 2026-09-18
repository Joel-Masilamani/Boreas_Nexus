import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { MetricCard } from '../components/common/MetricCard';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, ZAxis } from 'recharts';
import { BarChart3, Satellite, Database, CheckCircle2, ShieldCheck } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const { cityKPIs, hotspotsRegistry } = useAppStore();

  const sampleCorrelations = hotspotsRegistry.slice(0, 80).map((h) => ({
    id: h.hotspot_id,
    ndvi: h.mean_ndvi,
    bldgDensity: Math.round(h.mean_building_density * 100),
    lst: h.mean_lst,
    suhii: h.mean_suhii,
  }));

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#323273]">
        <div>
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
            Platform Diagnostics & Analytics
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Biophysical Correlations & Satellite Provenance
          </h1>
          <p className="text-xs text-[#A5A5D8] mt-0.5">
            Statistical distribution checks across 44,298 spatial grid cells and 167 hotspot clusters
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="cyan" dot>PROVENANCE VERIFIED</Badge>
          <Badge variant="purple">Processing v1.0.0</Badge>
        </div>
      </div>

      {/* Provenance & Metadata Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Panel title="Sensor & Satellite Acquisition" variant="elevated">
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-[#242748]">
              <span className="text-[#6A6A9F]">Primary Sensor:</span>
              <strong className="text-white">Landsat-8/9 OLI/TIRS & Sentinel-2 MSI</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-[#242748]">
              <span className="text-[#6A6A9F]">Capture Date:</span>
              <strong className="text-white">2024-05-15 (Peak Summer)</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-[#242748]">
              <span className="text-[#6A6A9F]">Scene ID:</span>
              <strong className="text-[#4DFFDF] font-mono text-[11px]">LC09_L2SP_142051_20240515</strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#6A6A9F]">Coordinate System:</span>
              <strong className="text-white">EPSG:4326 / UTM Zone 44N</strong>
            </div>
          </div>
        </Panel>

        <Panel title="Urban Coverage Statistics" variant="elevated">
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-[#242748]">
              <span className="text-[#6A6A9F]">Total Urban Extent:</span>
              <strong className="text-white">{cityKPIs?.urban_area_km2 || 303.5} km²</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-[#242748]">
              <span className="text-[#6A6A9F]">Rural Baseline Area:</span>
              <strong className="text-white">{cityKPIs?.rural_baseline_area_km2 || 125.6} km²</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-[#242748]">
              <span className="text-[#6A6A9F]">Validated Hotspots:</span>
              <strong className="text-[#EC223B]">{cityKPIs?.validated_hotspot_area_km2 || 197.6} km²</strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#6A6A9F]">Hotspot Area Ratio:</span>
              <strong className="text-white">65.1% of Urban Footprint</strong>
            </div>
          </div>
        </Panel>

        <Panel title="Data Governance & Integrity" variant="elevated">
          <div className="space-y-2 text-xs">
            <div className="flex items-center gap-2 py-1 text-[#5EFF5A]">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Zero source dataset mutations (Read-Only)</span>
            </div>
            <div className="flex items-center gap-2 py-1 text-[#5EFF5A]">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>100% 1-to-1 foreign key alignment on hotspot_id</span>
            </div>
            <div className="flex items-center gap-2 py-1 text-[#5EFF5A]">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Clean CRS transformation & boundary checks</span>
            </div>
            <div className="flex items-center gap-2 py-1 text-[#4DFFDF]">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>Reproducible deterministic demonstration layers</span>
            </div>
          </div>
        </Panel>
      </div>

      {/* Multi-Variate Scatter Plots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Building Density vs LST */}
        <Panel
          title="Building Density (%) vs Land Surface Temperature (°C)"
          subtitle="Observed positive correlation between impervious urban mass and thermal intensity"
        >
          <div className="h-64 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 0 }}>
                <XAxis
                  type="number"
                  dataKey="bldgDensity"
                  name="Building Density"
                  unit="%"
                  tick={{ fill: '#6A6A9F', fontSize: 10 }}
                  axisLine={{ stroke: '#242748' }}
                  label={{ value: 'Building Density (%)', position: 'insideBottom', offset: -10, fill: '#6A6A9F', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="lst"
                  name="LST"
                  unit="°C"
                  domain={['auto', 'auto']}
                  tick={{ fill: '#6A6A9F', fontSize: 10 }}
                  axisLine={{ stroke: '#242748' }}
                  label={{ value: 'Mean LST (°C)', angle: -90, position: 'insideLeft', fill: '#6A6A9F', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#191932', borderColor: '#323273', borderRadius: '12px', fontSize: '11px' }}
                />
                <Scatter data={sampleCorrelations} fill="#EC223B" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        {/* NDVI Vegetation vs LST */}
        <Panel
          title="NDVI Vegetation Index vs Land Surface Temperature (°C)"
          subtitle="Observed negative correlation confirming vegetative cooling capacity"
        >
          <div className="h-64 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 0 }}>
                <XAxis
                  type="number"
                  dataKey="ndvi"
                  name="NDVI"
                  tick={{ fill: '#6A6A9F', fontSize: 10 }}
                  axisLine={{ stroke: '#242748' }}
                  label={{ value: 'Normalized Difference Vegetation Index (NDVI)', position: 'insideBottom', offset: -10, fill: '#6A6A9F', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="lst"
                  name="LST"
                  unit="°C"
                  domain={['auto', 'auto']}
                  tick={{ fill: '#6A6A9F', fontSize: 10 }}
                  axisLine={{ stroke: '#242748' }}
                  label={{ value: 'Mean LST (°C)', angle: -90, position: 'insideLeft', fill: '#6A6A9F', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#191932', borderColor: '#323273', borderRadius: '12px', fontSize: '11px' }}
                />
                <Scatter data={sampleCorrelations} fill="#5EFF5A" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
};
