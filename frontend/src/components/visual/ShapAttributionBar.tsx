import React from 'react';
import { HotspotCluster } from '../../types';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ReferenceLine } from 'recharts';

interface ShapAttributionBarProps {
  hotspot: HotspotCluster;
  className?: string;
}

export const ShapAttributionBar: React.FC<ShapAttributionBarProps> = ({ hotspot, className }) => {
  const shapData = [
    {
      feature: 'Building Density',
      shapValue: hotspot.mean_shap_building_density || 0.42,
      rawMetric: `${Math.round(hotspot.mean_building_density * 100)}% density`,
      type: 'Built Environment',
    },
    {
      feature: 'Distance to Water',
      shapValue: hotspot.mean_shap_distance_to_water_m || 0.18,
      rawMetric: `${Math.round(hotspot.mean_distance_to_water_m)}m away`,
      type: 'Proximity',
    },
    {
      feature: 'Distance to Parks',
      shapValue: hotspot.mean_shap_distance_to_parks_m || 0.12,
      rawMetric: `Park buffer`,
      type: 'Proximity',
    },
    {
      feature: 'NDBI Built Index',
      shapValue: hotspot.mean_shap_ndbi || 0.05,
      rawMetric: `Impervious surface`,
      type: 'Spectral',
    },
    {
      feature: 'NDVI Vegetation',
      shapValue: hotspot.mean_shap_ndvi || -0.28,
      rawMetric: `NDVI: ${hotspot.mean_ndvi}`,
      type: 'Biophysical',
    },
  ].sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      const isHeating = d.shapValue >= 0;
      return (
        <div className="bg-[#191932] border border-[#323273] p-3 rounded-xl shadow-xl text-xs font-sans">
          <div className="font-bold text-white mb-1">{d.feature}</div>
          <div className="text-[#A5A5D8] mb-1.5">Domain: <span className="text-white">{d.rawMetric}</span></div>
          <div className="flex items-center gap-1.5">
            <span className="text-[#6A6A9F]">SHAP Attribution:</span>
            <span className={`font-bold ${isHeating ? 'text-[#EC223B]' : 'text-[#5EFF5A]'}`}>
              {isHeating ? `+${d.shapValue.toFixed(4)}°C` : `${d.shapValue.toFixed(4)}°C`}
            </span>
          </div>
          <div className="text-[10px] text-[#6A6A9F] mt-1">
            {isHeating ? 'Contributes to local heating' : 'Provides microclimate cooling effect'}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`p-4 rounded-2xl bg-[#191932] border border-[#323273] ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-bold text-white tracking-wide">
            SHAP Local Feature Attribution
          </h4>
          <p className="text-[11px] text-[#6A6A9F]">
            Marginal temperature contribution (°C) to {hotspot.hotspot_id}
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-semibold">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#EC223B]" />
            <span className="text-[#E2E8F0]">Warming (+°C)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#5EFF5A]" />
            <span className="text-[#E2E8F0]">Cooling (-°C)</span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={shapData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
          >
            <XAxis
              type="number"
              domain={['auto', 'auto']}
              tick={{ fill: '#6A6A9F', fontSize: 10 }}
              axisLine={{ stroke: '#242748' }}
              tickLine={{ stroke: '#242748' }}
              tickFormatter={(v) => `${v > 0 ? '+' : ''}${v.toFixed(2)}°C`}
            />
            <YAxis
              type="category"
              dataKey="feature"
              tick={{ fill: '#FFFFFF', fontSize: 11, fontWeight: 600 }}
              axisLine={{ stroke: '#242748' }}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={0} stroke="#4DFFDF" strokeDasharray="3 3" />
            <Bar dataKey="shapValue" radius={[0, 4, 4, 0]}>
              {shapData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.shapValue >= 0 ? '#EC223B' : '#5EFF5A'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
