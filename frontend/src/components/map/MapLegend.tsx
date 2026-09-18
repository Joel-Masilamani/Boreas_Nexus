import React from 'react';
import { useAppStore } from '../../store/useAppStore';

export const MapLegend: React.FC = () => {
  const { activeMapLayer } = useAppStore();

  const getLegendConfig = () => {
    switch (activeMapLayer) {
      case 'day_lst':
        return {
          title: 'DAY LST (°C)',
          subtitle: 'Landsat-8/9 Thermal Band',
          gradient: 'linear-gradient(to right, #3B82F6 0%, #5EFF5A 25%, #FFA63F 50%, #FF7A00 75%, #FF0707 100%)',
          ticks: ['30°C', '35°C', '40°C', '45°C', '50°C+'],
        };
      case 'night_lst':
        return {
          title: 'NIGHT LST (°C)',
          subtitle: 'Nocturnal Thermal Retention',
          gradient: 'linear-gradient(to right, #1E3A8A 0%, #3B82F6 30%, #5EFF5A 60%, #FFA63F 85%, #EC223B 100%)',
          ticks: ['20°C', '22°C', '24°C', '26°C', '29°C+'],
        };
      case 'day_suhii':
        return {
          title: 'DAY SUHII ANOMALY (°C)',
          subtitle: 'Urban Surface Heat Intensity vs Rural Baseline',
          gradient: 'linear-gradient(to right, #3B82F6 0%, #10B981 30%, #FFA63F 60%, #FF7A00 80%, #FF0707 100%)',
          ticks: ['-2°C', '0°C', '+2°C', '+4°C', '+8°C+'],
        };
      case 'night_suhii':
        return {
          title: 'NIGHT SUHII ANOMALY (°C)',
          subtitle: 'Nocturnal Canopy Heat Retention',
          gradient: 'linear-gradient(to right, #2563EB 0%, #06B6D4 25%, #F59E0B 55%, #EF4444 80%, #991B1B 100%)',
          ticks: ['0°C', '+2°C', '+4°C', '+6°C', '+8°C+'],
        };
      case 'persistence':
        return {
          title: 'HEAT PERSISTENCE INDEX',
          subtitle: 'Diurnal Heat Retention Score (0 to 1)',
          gradient: 'linear-gradient(to right, #312E81 0%, #6366F1 30%, #A855F7 60%, #EC4899 85%, #F43F5E 100%)',
          ticks: ['0.4', '0.5', '0.6', '0.7', '0.9'],
        };
      case 'dominant_drivers':
        return {
          title: 'DOMINANT HEAT DRIVER (MODULE 2)',
          subtitle: 'XAI SHAP Feature Attribution',
          isCategorical: true,
          categories: [
            { label: 'Land Cover', color: '#FFA63F', count: '97 clusters' },
            { label: 'Building Density', color: '#EC223B', count: '39 clusters' },
            { label: 'Distance to Parks', color: '#4DFFDF', count: '19 clusters' },
            { label: 'Water Proximity', color: '#38BDF8', count: '5 clusters' },
            { label: 'Elevation/Terrain', color: '#C084FC', count: '5 clusters' },
            { label: 'NDVI Vegetation', color: '#5EFF5A', count: '2 clusters' },
          ],
        };
      default:
        return {
          title: 'THERMAL LST (°C)',
          subtitle: 'Observed Temperature',
          gradient: 'linear-gradient(to right, #3B82F6, #5EFF5A, #FFA63F, #FF7A00, #FF0707)',
          ticks: ['30°C', '35°C', '40°C', '45°C', '50°C'],
        };
    }
  };

  const legend = getLegendConfig();

  return (
    <div className="absolute bottom-6 left-4 z-20 bg-[#0B0B19]/90 backdrop-blur-md border border-[#323273] rounded-2xl p-3.5 shadow-[0_10px_25px_rgba(0,0,0,0.5)] min-w-[280px] max-w-[340px]">
      <div className="text-[10px] font-bold tracking-[2px] uppercase text-[#6A6A9F] mb-0.5">
        {legend.title}
      </div>
      <div className="text-[10px] text-[#A5A5D8] mb-2.5">
        {legend.subtitle}
      </div>

      {legend.isCategorical ? (
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          {legend.categories?.map((cat) => (
            <div key={cat.label} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: cat.color }}
              />
              <div className="truncate">
                <span className="text-white font-semibold">{cat.label}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <div
            className="h-2.5 w-full rounded-full border border-[#323273]"
            style={{ background: legend.gradient }}
          />
          <div className="flex justify-between text-[10px] font-bold text-[#6A6A9F] mt-1.5 tabular-nums">
            {legend.ticks?.map((tick, i) => (
              <span key={i}>{tick}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
