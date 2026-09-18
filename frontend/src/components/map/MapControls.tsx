import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { ActiveMapLayer } from '../../types';
import clsx from 'clsx';
import { Sun, Moon, Flame, Clock, Network, Grid, Layers } from 'lucide-react';

export const MapControls: React.FC = () => {
  const {
    activeMapLayer,
    setActiveMapLayer,
    isGridPointsVisible,
    setGridPointsVisible,
  } = useAppStore();

  const layers: { id: ActiveMapLayer; label: string; icon: React.ReactNode; group: string }[] = [
    { id: 'day_lst', label: 'Day LST', icon: <Sun className="w-3.5 h-3.5 text-[#FFA63F]" />, group: 'Thermal' },
    { id: 'night_lst', label: 'Night LST', icon: <Moon className="w-3.5 h-3.5 text-[#93C5FD]" />, group: 'Thermal' },
    { id: 'day_suhii', label: 'Day SUHII', icon: <Flame className="w-3.5 h-3.5 text-[#FF7A00]" />, group: 'SUHII' },
    { id: 'night_suhii', label: 'Night SUHII', icon: <Flame className="w-3.5 h-3.5 text-[#EC223B]" />, group: 'SUHII' },
    { id: 'persistence', label: 'Persistence', icon: <Clock className="w-3.5 h-3.5 text-[#C084FC]" />, group: 'Dynamics' },
    { id: 'dominant_drivers', label: 'Drivers (M2)', icon: <Network className="w-3.5 h-3.5 text-[#4DFFDF]" />, group: 'Attribution' },
  ];

  return (
    <div className="absolute top-4 left-4 z-20 flex flex-col gap-2">
      {/* Layer Selector Bar */}
      <div className="bg-[#0B0B19]/90 backdrop-blur-md border border-[#323273] rounded-2xl p-1.5 shadow-[0_10px_25px_rgba(0,0,0,0.5)] flex flex-wrap items-center gap-1">
        <div className="px-2.5 py-1 text-[10px] font-bold tracking-[2px] uppercase text-[#6A6A9F] flex items-center gap-1.5 border-r border-[#242748]">
          <Layers className="w-3 h-3 text-[#4DFFDF]" />
          <span>Layers</span>
        </div>

        {layers.map((layer) => {
          const isActive = activeMapLayer === layer.id;
          return (
            <button
              key={layer.id}
              onClick={() => setActiveMapLayer(layer.id)}
              className={clsx(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer',
                isActive
                  ? 'bg-[#1F1F43] text-white border border-[#4DFFDF]/50 shadow-[0_0_12px_rgba(77,255,223,0.3)]'
                  : 'text-[#A5A5D8] hover:text-white hover:bg-[#191932]'
              )}
            >
              {layer.icon}
              <span>{layer.label}</span>
            </button>
          );
        })}

        {/* High-density grid toggle */}
        <div className="pl-1 border-l border-[#242748]">
          <button
            onClick={() => setGridPointsVisible(!isGridPointsVisible)}
            className={clsx(
              'flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer',
              isGridPointsVisible
                ? 'bg-[#942BE6]/30 text-[#C084FC] border border-[#942BE6]/60 shadow-[0_0_12px_rgba(148,43,230,0.4)]'
                : 'text-[#6A6A9F] hover:text-white hover:bg-[#191932]'
            )}
            title="Toggle 44,298 sample grid point WebGL layer"
          >
            <Grid className="w-3.5 h-3.5" />
            <span>44k Grid</span>
          </button>
        </div>
      </div>
    </div>
  );
};
