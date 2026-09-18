import React from 'react';
import { ThermalDynamicsModel } from '../../types';
import { Sun, Wind, Droplets, Mountain, ArrowRight } from 'lucide-react';

interface EnergyFluxDiagramProps {
  model: ThermalDynamicsModel;
  className?: string;
}

export const EnergyFluxDiagram: React.FC<EnergyFluxDiagramProps> = ({ model, className }) => {
  const { netRadiation, sensibleHeat, latentHeat, groundHeat, bowenRatio } = model;

  const sensiblePct = Math.round((sensibleHeat / netRadiation) * 100);
  const latentPct = Math.round((latentHeat / netRadiation) * 100);
  const groundPct = Math.round((groundHeat / netRadiation) * 100);

  return (
    <div className={`p-5 rounded-2xl bg-[#191932] border border-[#323273] ${className}`}>
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-[#242748]">
        <div>
          <h4 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
            Surface Energy Balance Flow
            <span className="text-[10px] text-[#C084FC] bg-[#942BE6]/20 border border-[#942BE6]/30 px-2 py-0.5 rounded-full font-bold">
              Rₙ = H + λE + G
            </span>
          </h4>
          <p className="text-[11px] text-[#6A6A9F]">
            Physics partitioning of incoming net radiation flux (W/m²)
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-[#6A6A9F] uppercase font-bold tracking-wider">Bowen Ratio (β = H/λE)</span>
          <div className="text-sm font-extrabold text-[#4DFFDF] tabular-nums">{bowenRatio}</div>
        </div>
      </div>

      {/* Ribbon Flow Visualization */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center my-4">
        {/* Source: Net Radiation */}
        <div className="md:col-span-2 p-4 rounded-2xl bg-[#25245D] border border-[#FFA63F]/50 shadow-[0_0_20px_rgba(255,166,63,0.15)] flex flex-col justify-between h-44">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold tracking-[2px] uppercase text-[#FFA63F]">
              Net Radiation (Rₙ)
            </span>
            <div className="w-8 h-8 rounded-xl bg-[#FFA63F]/20 flex items-center justify-center text-[#FFA63F]">
              <Sun className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-white tabular-nums">
              {netRadiation} <span className="text-sm font-semibold text-[#A5A5D8]">W/m²</span>
            </div>
            <p className="text-[11px] text-[#A5A5D8] mt-1">
              Peak summer insolation minus surface albedo & longwave emission.
            </p>
          </div>
          <div className="text-[10px] text-[#6A6A9F] uppercase font-semibold flex items-center gap-1">
            <span>Partitioned into 3 turbulent fluxes</span>
            <ArrowRight className="w-3 h-3 text-[#4DFFDF]" />
          </div>
        </div>

        {/* Partitioned Sinks */}
        <div className="md:col-span-3 flex flex-col gap-2.5">
          {/* Sensible Heat Flux H */}
          <div className="p-3 rounded-xl bg-[#1F1F43] border border-[#EC223B]/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#EC223B]/20 text-[#EC223B] flex items-center justify-center">
                <Wind className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-white">Sensible Heat (H)</div>
                <div className="text-[10px] text-[#A5A5D8]">Direct air heating & canopy warming</div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-base font-extrabold text-[#EC223B] tabular-nums">{sensibleHeat} W/m²</span>
              <div className="text-[10px] font-semibold text-[#6A6A9F]">{sensiblePct}% of Rₙ</div>
            </div>
          </div>

          {/* Latent Heat Flux λE */}
          <div className="p-3 rounded-xl bg-[#1F1F43] border border-[#4DFFDF]/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#4DFFDF]/20 text-[#4DFFDF] flex items-center justify-center">
                <Droplets className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-white">Latent Heat (λE)</div>
                <div className="text-[10px] text-[#A5A5D8]">Evapotranspirative cooling from vegetation</div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-base font-extrabold text-[#4DFFDF] tabular-nums">{latentHeat} W/m²</span>
              <div className="text-[10px] font-semibold text-[#6A6A9F]">{latentPct}% of Rₙ</div>
            </div>
          </div>

          {/* Ground Heat Flux G */}
          <div className="p-3 rounded-xl bg-[#1F1F43] border border-[#FFA63F]/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#FFA63F]/20 text-[#FFA63F] flex items-center justify-center">
                <Mountain className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-white">Ground / Storage Heat (G)</div>
                <div className="text-[10px] text-[#A5A5D8]">Thermal absorption in concrete & masonry</div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-base font-extrabold text-[#FFA63F] tabular-nums">{groundHeat} W/m²</span>
              <div className="text-[10px] font-semibold text-[#6A6A9F]">{groundPct}% of Rₙ</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
