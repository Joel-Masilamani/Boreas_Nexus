import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';
import { Badge } from '../common/Badge';
import { RadialProgress } from '../common/RadialProgress';
import { 
  X, 
  Flame, 
  Activity, 
  Network, 
  Sliders, 
  MapPin, 
  Maximize2, 
  ShieldCheck,
  TrendingUp,
  Layers
} from 'lucide-react';

export const HotspotDrawer: React.FC = () => {
  const navigate = useNavigate();
  const { 
    selectedHotspot, 
    isDrawerOpen, 
    setDrawerOpen 
  } = useAppStore();

  if (!isDrawerOpen || !selectedHotspot) return null;

  const h = selectedHotspot;
  const areaHa = (h.cluster_area_m2 / 10000).toFixed(1);
  const areaKm2 = (h.cluster_area_m2 / 1000000).toFixed(2);

  return (
    <aside className="fixed right-4 top-20 bottom-6 w-96 bg-[#0B0B19]/95 backdrop-blur-xl border border-[#323273] rounded-3xl p-5 shadow-[0_20px_50px_rgba(0,0,0,0.7)] z-30 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-300">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-[#242748]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#FF7A00]/15 border border-[#FF7A00]/40 flex items-center justify-center text-[#FF7A00] shadow-[0_0_15px_rgba(255,122,0,0.3)]">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-extrabold text-white tracking-wide">
                  {h.hotspot_id}
                </h2>
                <Badge variant={h.period === 'DAY' ? 'warm' : 'purple'}>
                  {h.period}
                </Badge>
              </div>
              <p className="text-[11px] text-[#6A6A9F] tracking-wide mt-0.5">
                Cluster Group: {h.hotspot_group_id || 'Isolated'} • {h.cluster_size_pixels} Pixels
              </p>
            </div>
          </div>

          <button
            onClick={() => setDrawerOpen(false)}
            className="w-8 h-8 rounded-xl bg-[#191932] border border-[#323273] text-[#A5A5D8] hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section 1: Real Thermal Profile (Module 1) */}
        <div className="mt-4">
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F] mb-2.5 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[#4DFFDF]" />
            <span>Observed Thermal Profile (Module 1)</span>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-2xl bg-[#191932] border border-[#323273]">
              <span className="text-[9px] font-bold tracking-[2px] uppercase text-[#6A6A9F]">Mean LST</span>
              <div className="text-xl font-extrabold text-white mt-1 tabular-nums">
                {h.mean_lst}°C
              </div>
              <span className="text-[10px] text-[#A5A5D8]">Surface temperature</span>
            </div>

            <div className="p-3 rounded-2xl bg-[#191932] border border-[#EC223B]/40 shadow-[0_0_10px_rgba(236,34,59,0.15)]">
              <span className="text-[9px] font-bold tracking-[2px] uppercase text-[#FF7A00]">Peak LST</span>
              <div className="text-xl font-extrabold text-[#EC223B] mt-1 tabular-nums">
                {h.peak_lst}°C
              </div>
              <span className="text-[10px] text-[#A5A5D8]">Cluster maximum</span>
            </div>

            <div className="p-3 rounded-2xl bg-[#191932] border border-[#323273]">
              <span className="text-[9px] font-bold tracking-[2px] uppercase text-[#6A6A9F]">Mean SUHII</span>
              <div className="text-xl font-extrabold text-[#FFA63F] mt-1 tabular-nums">
                +{h.mean_suhii}°C
              </div>
              <span className="text-[10px] text-[#A5A5D8]">Above rural baseline</span>
            </div>

            <div className="p-3 rounded-2xl bg-[#191932] border border-[#323273]">
              <span className="text-[9px] font-bold tracking-[2px] uppercase text-[#6A6A9F]">Persistence</span>
              <div className="text-xl font-extrabold text-[#C084FC] mt-1 tabular-nums">
                {Math.round(h.mean_heat_persistence * 100)}%
              </div>
              <span className="text-[10px] text-[#A5A5D8]">Retention index: {h.mean_heat_persistence}</span>
            </div>
          </div>

          {/* Spatial Metrics & Confidence */}
          <div className="mt-3 p-3 rounded-2xl bg-[#14142B] border border-[#242748] flex items-center justify-between text-xs">
            <div>
              <div className="text-[10px] text-[#6A6A9F] uppercase tracking-wider font-semibold">
                Cluster Footprint
              </div>
              <div className="font-bold text-white mt-0.5">
                {areaHa} ha <span className="text-[#6A6A9F] font-normal">({areaKm2} km²)</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-[#6A6A9F] uppercase tracking-wider font-semibold">
                Confidence Score
              </div>
              <div className="font-bold text-[#5EFF5A] mt-0.5 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-[#5EFF5A]" />
                {h.mean_hotspot_confidence_score} / 100
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Real Driver Intelligence (Module 2) */}
        <div className="mt-5">
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F] mb-2.5 flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-[#C084FC]" />
            <span>Driver Intelligence (Module 2)</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#191932] border border-[#323273] space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] text-[#6A6A9F] uppercase tracking-wider font-semibold">
                  Dominant Driver
                </span>
                <div className="text-sm font-bold text-[#4DFFDF] mt-0.5 capitalize">
                  {h.dominant_driver.replace(/_/g, ' ')}
                </div>
              </div>
              <Badge variant="cyan" dot>
                {h.driver_consensus_pct}% Consensus
              </Badge>
            </div>

            <div className="flex items-center justify-between text-xs pt-2 border-t border-[#242748]">
              <span className="text-[#A5A5D8]">Secondary Driver:</span>
              <span className="font-semibold text-white capitalize">
                {h.secondary_driver.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-[#A5A5D8]">Domain Consistency:</span>
              <span className="font-bold text-[#5EFF5A]">
                {h.domain_consistency_score}%
              </span>
            </div>

            {h.diurnal_driver_shift && (
              <div className="text-[11px] p-2 rounded-xl bg-[#0B0B19] border border-[#242748] text-[#FFA63F]">
                <span className="font-bold text-white">Diurnal Shift:</span> {h.diurnal_driver_shift}
              </div>
            )}

            {/* Micro Feature Readout */}
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#242748] text-center">
              <div>
                <span className="text-[9px] text-[#6A6A9F] uppercase">Bldg Density</span>
                <div className="font-bold text-white text-xs mt-0.5">
                  {Math.round(h.mean_building_density * 100)}%
                </div>
              </div>
              <div>
                <span className="text-[9px] text-[#6A6A9F] uppercase">NDVI Veg</span>
                <div className="font-bold text-white text-xs mt-0.5">
                  {h.mean_ndvi}
                </div>
              </div>
              <div>
                <span className="text-[9px] text-[#6A6A9F] uppercase">Water Dist</span>
                <div className="font-bold text-white text-xs mt-0.5">
                  {Math.round(h.mean_distance_to_water_m)}m
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Downstream Actions */}
      <div className="pt-4 border-t border-[#242748] flex flex-col gap-2 mt-4">
        <button
          onClick={() => {
            navigate('/drivers');
          }}
          className="w-full py-2.5 px-4 rounded-xl bg-[#176BF8] hover:bg-[#176BF8]/80 text-white text-xs font-bold tracking-wider uppercase transition-all shadow-[0_0_15px_rgba(23,107,248,0.4)] flex items-center justify-center gap-2 cursor-pointer"
        >
          <Network className="w-4 h-4" />
          <span>Analyze Drivers (Module 2) →</span>
        </button>

        <button
          onClick={() => {
            navigate('/scenario-lab');
          }}
          className="w-full py-2.5 px-4 rounded-xl bg-[#1F1F43] hover:bg-[#25245D] text-[#4DFFDF] border border-[#323273] text-xs font-bold tracking-wider uppercase transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <Sliders className="w-4 h-4" />
          <span>Simulate Mitigation Scenarios →</span>
        </button>
      </div>
    </aside>
  );
};
