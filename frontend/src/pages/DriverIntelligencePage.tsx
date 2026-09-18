import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { ShapAttributionBar } from '../components/visual/ShapAttributionBar';
import { MetricCard } from '../components/common/MetricCard';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { 
  Network, 
  Cpu, 
  ShieldCheck, 
  Building2, 
  TreePine, 
  Droplets, 
  Compass,
  Layers,
  Sparkles
} from 'lucide-react';

export const DriverIntelligencePage: React.FC = () => {
  const { selectedHotspot, driverAudit } = useAppStore();

  const driverCountsData = [
    { name: 'Land Cover Code', count: 97, color: '#FFA63F' },
    { name: 'Building Density', count: 39, color: '#EC223B' },
    { name: 'Distance to Parks', count: 19, color: '#4DFFDF' },
    { name: 'Distance to Water', count: 5, color: '#38BDF8' },
    { name: 'Elevation & Slope', count: 5, color: '#C084FC' },
    { name: 'NDVI Vegetation', count: 2, color: '#5EFF5A' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#323273]">
        <div>
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
            Module 2 • Urban Heat Driver Intelligence Engine
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Biophysical Drivers & Explainable AI (SHAP) Attribution
          </h1>
          <p className="text-xs text-[#A5A5D8] mt-0.5">
            Machine learning decomposition (LightGBM & Random Forest) explaining environmental causality
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="cyan" dot>
            REAL ML ATTRIBUTIONS
          </Badge>
          <Badge variant="purple">
            R² = 0.946 (Day)
          </Badge>
        </div>
      </div>

      {/* Context Banner for Selected Hotspot */}
      {selectedHotspot && (
        <div className="p-4 rounded-2xl bg-[#1F1F43] border border-[#4DFFDF]/40 shadow-[0_0_20px_rgba(77,255,223,0.1)] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-[#25245D] border border-[#4DFFDF] flex items-center justify-center text-[#4DFFDF] shadow-[0_0_15px_rgba(77,255,223,0.3)]">
              <Network className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-widest text-[#6A6A9F]">Target Hotspot:</span>
                <span className="text-base font-extrabold text-white">{selectedHotspot.hotspot_id}</span>
                <Badge variant={selectedHotspot.period === 'DAY' ? 'warm' : 'purple'}>
                  {selectedHotspot.period} Hotspot
                </Badge>
              </div>
              <div className="text-xs text-[#A5A5D8] mt-0.5">
                Mean LST: <strong className="text-white">{selectedHotspot.mean_lst}°C</strong> • Peak: <strong className="text-[#EC223B]">{selectedHotspot.peak_lst}°C</strong> • SUHII: <strong className="text-[#FFA63F]">+{selectedHotspot.mean_suhii}°C</strong>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-[#323273] pt-3 md:pt-0 md:pl-6">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#6A6A9F]">Primary Driver</span>
              <div className="text-sm font-extrabold text-[#4DFFDF] capitalize">
                {selectedHotspot.dominant_driver.replace(/_/g, ' ')}
              </div>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#6A6A9F]">Consensus</span>
              <div className="text-sm font-extrabold text-white">
                {selectedHotspot.driver_consensus_pct}%
              </div>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#6A6A9F]">Plausibility</span>
              <div className="text-sm font-extrabold text-[#5EFF5A]">
                {selectedHotspot.domain_consistency_score}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Benchmark Performance Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="LightGBM Day R²"
          value="0.946"
          subtext="RMSE: 0.55°C (5-fold CV)"
          icon={<Cpu className="w-4 h-4 text-[#4DFFDF]" />}
          highlightColor="cyan"
        />
        <MetricCard
          label="LightGBM Night R²"
          value="0.937"
          subtext="RMSE: 0.31°C (5-fold CV)"
          icon={<Cpu className="w-4 h-4 text-[#C084FC]" />}
          highlightColor="purple"
        />
        <MetricCard
          label="Random Forest Baseline"
          value="0.930"
          subtext="Day R² Baseline (12 Features)"
          icon={<Layers className="w-4 h-4 text-[#A5A5D8]" />}
        />
        <MetricCard
          label="Physics Plausibility"
          value="70.3%"
          subtext="City-wide directional validity"
          icon={<ShieldCheck className="w-4 h-4 text-[#5EFF5A]" />}
          highlightColor="cyan"
        />
      </div>

      {/* Real SHAP Feature Attribution Chart */}
      {selectedHotspot && (
        <ShapAttributionBar hotspot={selectedHotspot} />
      )}

      {/* City-Wide Driver Breakdown & GWR Local Relationships */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dominant Driver Distribution Chart */}
        <Panel title="Dominant Drivers Across 167 Hotspot Clusters">
          <div className="flex flex-col sm:flex-row items-center gap-6 mt-2">
            <div className="w-44 h-44 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={driverCountsData}
                    dataKey="count"
                    nameKey="name"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={3}
                  >
                    {driverCountsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#191932', borderColor: '#323273', borderRadius: '12px', fontSize: '11px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="flex-1 space-y-2 text-xs w-full">
              {driverCountsData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-white font-medium">{item.name}</span>
                  </div>
                  <div className="font-bold text-white tabular-nums">
                    {item.count} <span className="text-[#6A6A9F] font-normal text-[10px]">({Math.round((item.count / 167) * 100)}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        {/* Spatial GWR Metrics & Local Interpretability */}
        <Panel title="Spatial GWR (Geographically Weighted Regression)">
          <div className="space-y-3 mt-2 text-xs">
            <p className="text-[#A5A5D8] leading-relaxed">
              Spatial heterogeneity in Chennai creates varying thermal sensitivities across neighborhoods:
            </p>

            <div className="p-3 rounded-xl bg-[#14142B] border border-[#242748] space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-[#6A6A9F] font-semibold">Building Density Sensitivity (β):</span>
                <span className="font-bold text-[#EC223B]">+0.880 relative importance</span>
              </div>
              <div className="w-full h-1 rounded-full bg-[#05050F]">
                <div className="h-full bg-[#EC223B] rounded-full w-[88%]" />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#14142B] border border-[#242748] space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-[#6A6A9F] font-semibold">Vegetation Deficit (NDVI β):</span>
                <span className="font-bold text-[#5EFF5A]">-0.143 cooling impact</span>
              </div>
              <div className="w-full h-1 rounded-full bg-[#05050F]">
                <div className="h-full bg-[#5EFF5A] rounded-full w-[14%]" />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#14142B] border border-[#242748] space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-[#6A6A9F] font-semibold">Bay of Bengal Coastal Buffer:</span>
                <span className="font-bold text-[#38BDF8]">Cooling effect within 800m</span>
              </div>
              <div className="w-full h-1 rounded-full bg-[#05050F]">
                <div className="h-full bg-[#38BDF8] rounded-full w-[35%]" />
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
};
