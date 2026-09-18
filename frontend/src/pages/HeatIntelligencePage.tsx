import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { MapView } from '../components/map/MapView';
import { MetricCard } from '../components/common/MetricCard';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { RadarScannerDial } from '../components/visual/RadarScannerDial';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { Flame, Sun, Moon, Clock, ShieldCheck, Activity } from 'lucide-react';

export const HeatIntelligencePage: React.FC = () => {
  const { selectedHotspot, cityKPIs } = useAppStore();

  const thermalDistribution = [
    { range: '< 34°C', dayCells: 820, nightCells: 38400, label: 'Cool / Water' },
    { range: '34 - 38°C', dayCells: 14200, nightCells: 5898, label: 'Moderate' },
    { range: '38 - 41°C', dayCells: 19827, nightCells: 0, label: 'Warm Urban' },
    { range: '41 - 44°C', dayCells: 7451, nightCells: 0, label: 'Hotspot' },
    { range: '> 44°C', dayCells: 2000, nightCells: 0, label: 'Extreme Hotspot' },
  ];

  const persistenceClassification = [
    { name: 'Moderate Retention', count: 21802, pct: '49.2%', color: '#38BDF8' },
    { name: 'High Nocturnal Retention', count: 16857, pct: '38.1%', color: '#EC223B' },
    { name: 'Rapid Cooling Surface', count: 5639, pct: '12.7%', color: '#5EFF5A' },
  ];

  const significanceBreakdown = [
    { name: '99% Conf Hotspot', count: 4654, period: 'Day', color: '#FF0707' },
    { name: '95% Conf Hotspot', count: 2797, period: 'Day', color: '#FF7A00' },
    { name: '99% Conf Nocturnal', count: 10366, period: 'Night', color: '#942BE6' },
    { name: '95% Conf Nocturnal', count: 3529, period: 'Night', color: '#383DCA' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#323273]">
        <div>
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
            Module 1 • Physical Urban Heat Intelligence
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Diurnal Surface Temperature & Spatial Hotspot Dynamics
          </h1>
          <p className="text-xs text-[#A5A5D8] mt-0.5">
            Empirical Getis-Ord Gi* statistics, surface urban heat island intensity, and thermal persistence
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="cyan" dot>
            REAL OBSERVATIONS
          </Badge>
          <Badge variant="purple">
            44,298 Cells
          </Badge>
        </div>
      </div>

      {/* Hero Analytics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          label="Day LST Range"
          value="29.7° - 49.7°C"
          subtext="Mean: 39.09°C (σ = 2.34)"
          icon={<Sun className="w-4 h-4 text-[#FFA63F]" />}
          highlightColor="warm"
        />
        <MetricCard
          label="Night LST Range"
          value="20.3° - 29.2°C"
          subtext="Mean: 24.50°C (σ = 2.43)"
          icon={<Moon className="w-4 h-4 text-[#60A5FA]" />}
          highlightColor="blue"
        />
        <MetricCard
          label="Diurnal ΔLST Mean"
          value="14.6°C"
          subtext="Thermal range up to 26.5°C"
          icon={<Activity className="w-4 h-4 text-[#4DFFDF]" />}
          highlightColor="cyan"
        />
        <MetricCard
          label="Validated Hotspot Area"
          value={`${cityKPIs?.validated_hotspot_area_km2 || 197.6} km²`}
          subtext="65.1% of Urban Extent"
          icon={<Flame className="w-4 h-4 text-[#EC223B]" />}
          highlightColor="extreme"
        />
      </div>

      {/* Map & Orbital Radar Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map View */}
        <div className="lg:col-span-2 h-[460px] rounded-3xl overflow-hidden border border-[#323273] relative shadow-2xl">
          <MapView showDrawer={false} />
        </div>

        {/* Selected Hotspot Radar Dial */}
        <div className="space-y-4">
          {selectedHotspot ? (
            <RadarScannerDial hotspot={selectedHotspot} />
          ) : (
            <Panel title="Hotspot Selection Required">
              <p className="text-xs text-[#6A6A9F]">Select a hotspot on the map to inspect its persistence radar.</p>
            </Panel>
          )}

          {/* Thermal Retention Class Breakdown */}
          <Panel title="Thermal Retention Classes">
            <div className="space-y-2.5">
              {persistenceClassification.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-white font-medium">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-white tabular-nums">{item.count.toLocaleString()}</span>
                    <span className="text-[10px] text-[#6A6A9F] ml-1.5 font-semibold">({item.pct})</span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>

      {/* Bottom Visualizations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Thermal Distribution Bar Chart */}
        <Panel title="City-Wide Thermal Distribution (Cell Counts)">
          <div className="h-56 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={thermalDistribution} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <XAxis dataKey="range" tick={{ fill: '#6A6A9F', fontSize: 11 }} axisLine={{ stroke: '#242748' }} />
                <YAxis tick={{ fill: '#6A6A9F', fontSize: 10 }} axisLine={{ stroke: '#242748' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#191932', borderColor: '#323273', borderRadius: '12px', fontSize: '11px' }}
                />
                <Bar dataKey="dayCells" name="Day Cells" fill="#FFA63F" radius={[4, 4, 0, 0]} />
                <Bar dataKey="nightCells" name="Night Cells" fill="#176BF8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        {/* Spatial Significance Breakdown */}
        <Panel title="Getis-Ord Gi* Hotspot Confidence Distribution">
          <div className="grid grid-cols-2 gap-3 mt-2">
            {significanceBreakdown.map((item) => (
              <div key={item.name} className="p-3.5 rounded-xl bg-[#14142B] border border-[#242748]">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#6A6A9F] block">
                  {item.period} Hotspots
                </span>
                <div className="text-lg font-extrabold text-white mt-1" style={{ color: item.color }}>
                  {item.count.toLocaleString()}
                </div>
                <span className="text-[10px] text-[#A5A5D8]">{item.name}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
};
