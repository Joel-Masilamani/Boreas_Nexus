import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { StatusIndicator } from '../common/StatusIndicator';
import { Badge } from '../common/Badge';
import { Flame, Layers, MapPin, Sparkles } from 'lucide-react';

export const TopBar: React.FC = () => {
  const {
    city,
    analysisRun,
    spatialResolution,
    selectedHotspotId,
    selectedHotspot,
    hotspotsRegistry,
    setSelectedHotspotId,
    setDrawerOpen,
  } = useAppStore();

  return (
    <header className="h-16 bg-[#0B0B19]/90 backdrop-blur-md border-b border-[#323273] px-4 md:px-6 flex items-center justify-between z-30 sticky top-0">
      {/* Geographic Context */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#176BF8]/15 border border-[#176BF8]/40 flex items-center justify-center text-[#4DFFDF]">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm md:text-base font-bold text-white tracking-wide">
                {city}
              </span>
              <span className="hidden sm:inline-block text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-[#1F1F43] border border-[#323273] text-[#A5A5D8]">
                {spatialResolution}
              </span>
            </div>
            <div className="text-[11px] text-[#6A6A9F] tracking-wider flex items-center gap-2">
              <span>Run: <span className="text-[#C084FC] font-semibold">{analysisRun}</span></span>
              <span className="hidden md:inline text-[#323273]">|</span>
              <span className="hidden md:inline">Landsat-8/9 & Sentinel-2 L2SP</span>
            </div>
          </div>
        </div>
      </div>

      {/* Center / Active Hotspot Target Jumper */}
      <div className="hidden lg:flex items-center gap-2 bg-[#191932] border border-[#323273] px-3 py-1.5 rounded-xl shadow-inner">
        <div className="flex items-center gap-1.5 text-xs text-[#6A6A9F]">
          <Flame className="w-3.5 h-3.5 text-[#FF7A00]" />
          <span className="text-[10px] font-bold tracking-[2px] uppercase">Active Target:</span>
        </div>

        <select
          value={selectedHotspotId}
          onChange={(e) => setSelectedHotspotId(e.target.value)}
          className="bg-[#05050F] text-xs font-bold text-[#4DFFDF] border border-[#323273] rounded-lg px-2.5 py-1 focus:outline-none focus:border-[#4DFFDF] cursor-pointer"
        >
          {hotspotsRegistry.slice(0, 30).map((h) => (
            <option key={h.hotspot_id} value={h.hotspot_id}>
              {h.hotspot_id} ({h.period} • {h.peak_lst}°C)
            </option>
          ))}
        </select>

        {selectedHotspot && (
          <div className="flex items-center gap-2 pl-1">
            <Badge variant={selectedHotspot.period === 'DAY' ? 'warm' : 'purple'}>
              {selectedHotspot.period}
            </Badge>
            <button
              onClick={() => setDrawerOpen(true)}
              className="text-[11px] text-[#4DFFDF] hover:text-white transition-colors underline underline-offset-2 font-semibold"
            >
              Inspect Profile →
            </button>
          </div>
        )}
      </div>

      {/* Right System Telemetry */}
      <div className="flex items-center gap-3 md:gap-4">
        <StatusIndicator status="READY" />
        
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#1F1F43] border border-[#323273] text-[11px] text-[#A5A5D8]">
          <Layers className="w-3 h-3 text-[#4DFFDF]" />
          <span className="font-semibold text-white">167</span> Clusters / <span className="font-semibold text-white">44,298</span> Cells
        </div>
      </div>
    </header>
  );
};
