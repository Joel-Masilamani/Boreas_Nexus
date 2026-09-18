import React from 'react';
import { HotspotCluster } from '../../types';

interface RadarScannerDialProps {
  hotspot: HotspotCluster;
  className?: string;
}

export const RadarScannerDial: React.FC<RadarScannerDialProps> = ({ hotspot, className }) => {
  const persistencePct = Math.round((hotspot.mean_heat_persistence || 0.6) * 100);
  const confidenceScore = Math.round(hotspot.mean_hotspot_confidence_score || 65);
  const suhiiSeverityPct = Math.min(100, Math.round((hotspot.mean_suhii / 8.0) * 100));

  return (
    <div className={`relative flex flex-col items-center justify-center p-5 rounded-2xl bg-[#191932] border border-[#323273] ${className}`}>
      <div className="w-full flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold tracking-[2px] uppercase text-[#6A6A9F]">
          Thermal Radar Scanner
        </span>
        <span className="text-[10px] font-bold text-[#4DFFDF] bg-[#4DFFDF]/10 border border-[#4DFFDF]/30 px-2 py-0.5 rounded-full">
          {hotspot.period} PERSISTENCE
        </span>
      </div>

      {/* Concentric Radar Graphic */}
      <div className="relative w-56 h-56 flex items-center justify-center my-2">
        {/* Outer Ring */}
        <div className="absolute inset-0 rounded-full border border-[#323273] border-dashed animate-[spin_60s_linear_infinite]" />
        
        {/* Middle Ring */}
        <div className="absolute inset-5 rounded-full border border-[#242748]" />

        {/* Inner Luminous Ring */}
        <div className="absolute inset-10 rounded-full border-2 border-[#176BF8]/30 shadow-[0_0_20px_rgba(23,107,248,0.2)]" />

        {/* Central Core Pulse */}
        <div className="absolute w-24 h-24 rounded-full bg-[#25245D] border-2 border-[#4DFFDF] shadow-[0_0_25px_rgba(77,255,223,0.3)] flex flex-col items-center justify-center text-center p-2 z-10">
          <span className="text-2xl font-extrabold text-white leading-none tabular-nums">
            {persistencePct}%
          </span>
          <span className="text-[9px] text-[#6A6A9F] uppercase font-bold tracking-wider mt-1">
            Persistence
          </span>
        </div>

        {/* Orbital Badges */}
        <div className="absolute top-1 left-3 bg-[#191932] border border-[#FF7A00]/50 px-2 py-1 rounded-lg text-[10px] font-bold text-[#FF7A00] shadow-[0_0_8px_rgba(255,122,0,0.3)]">
          +{hotspot.mean_suhii}°C SUHII
        </div>

        <div className="absolute bottom-2 right-2 bg-[#191932] border border-[#5EFF5A]/50 px-2 py-1 rounded-lg text-[10px] font-bold text-[#5EFF5A] shadow-[0_0_8px_rgba(94,255,90,0.3)]">
          {confidenceScore}% Conf
        </div>

        <div className="absolute top-3 right-2 bg-[#191932] border border-[#C084FC]/50 px-2 py-1 rounded-lg text-[10px] font-bold text-[#C084FC]">
          {hotspot.peak_lst}°C Peak
        </div>
      </div>

      {/* Telemetry Readout Bars */}
      <div className="w-full space-y-2 mt-2 pt-3 border-t border-[#242748] text-xs">
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#A5A5D8]">Heat Persistence Index</span>
            <span className="font-bold text-white">{hotspot.mean_heat_persistence}</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-[#05050F] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#176BF8] via-[#942BE6] to-[#EC223B] rounded-full"
              style={{ width: `${persistencePct}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#A5A5D8]">Thermal Anomaly Severity</span>
            <span className="font-bold text-[#FFA63F]">+{hotspot.mean_suhii}°C</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-[#05050F] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#5EFF5A] via-[#FFA63F] to-[#FF0707] rounded-full"
              style={{ width: `${suhiiSeverityPct}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
