import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { physicsService } from '../services/mock/physicsService';
import { EnergyFluxDiagram } from '../components/visual/EnergyFluxDiagram';
import { MetricCard } from '../components/common/MetricCard';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { StatusIndicator } from '../components/common/StatusIndicator';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { Activity, Sun, Wind, Droplets, Mountain, Sparkles, AlertCircle } from 'lucide-react';

export const ThermalDynamicsPage: React.FC = () => {
  const { selectedHotspot } = useAppStore();

  if (!selectedHotspot) {
    return (
      <div className="p-8 text-center text-white">
        <p className="text-sm text-[#6A6A9F]">Please select a hotspot to view its physics-informed thermal dynamics.</p>
      </div>
    );
  }

  const model = physicsService.calculateThermalDynamics(selectedHotspot);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Demonstration Model Disclaimer Banner */}
      <div className="p-3.5 rounded-2xl bg-[#942BE6]/10 border border-[#942BE6]/40 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 text-xs text-[#C084FC]">
          <Sparkles className="w-4 h-4 text-[#4DFFDF] shrink-0" />
          <span>
            <strong className="text-white uppercase tracking-wider font-bold">Demonstration Model:</strong> Physics-Guided Microclimate Energy Balance & Projected Thermal Dynamics
          </span>
        </div>
        <Badge variant="purple">DEMO / PROJECTED</Badge>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#323273]">
        <div>
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
            Module 3 • Physics-Guided Urban Heat Dynamics
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Surface Energy Balance & Diurnal Thermal Progression
          </h1>
          <p className="text-xs text-[#A5A5D8] mt-0.5">
            Thermodynamic coupling of net solar radiation, sensible convection, and latent cooling for {selectedHotspot.hotspot_id}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="cyan" dot>Target: {selectedHotspot.hotspot_id}</Badge>
          <Badge variant="warm">LST {selectedHotspot.mean_lst}°C</Badge>
        </div>
      </div>

      {/* Thermodynamic KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          label="Net Radiation (Rₙ)"
          value={model.netRadiation}
          unit="W/m²"
          subtext="Peak solar radiative forcing"
          icon={<Sun className="w-4 h-4 text-[#FFA63F]" />}
          highlightColor="warm"
        />
        <MetricCard
          label="Sensible Heat (H)"
          value={model.sensibleHeat}
          unit="W/m²"
          subtext="Direct canopy air warming"
          icon={<Wind className="w-4 h-4 text-[#EC223B]" />}
          highlightColor="hot"
        />
        <MetricCard
          label="Latent Heat (λE)"
          value={model.latentHeat}
          unit="W/m²"
          subtext="Evapotranspirative flux"
          icon={<Droplets className="w-4 h-4 text-[#4DFFDF]" />}
          highlightColor="cyan"
        />
        <MetricCard
          label="Storage Heat (G)"
          value={model.groundHeat}
          unit="W/m²"
          subtext="Fabric thermal inertia"
          icon={<Mountain className="w-4 h-4 text-[#FFA63F]" />}
        />
        <MetricCard
          label="Coupled 2m Air Temp"
          value={`${model.airTemp}°C`}
          subtext={`LST - ${(model.surfaceTemp - model.airTemp).toFixed(1)}°C gradient`}
          icon={<Activity className="w-4 h-4 text-[#C084FC]" />}
          highlightColor="purple"
        />
      </div>

      {/* Visual Energy Flux Partitioning Diagram */}
      <EnergyFluxDiagram model={model} />

      {/* 24-Hour Diurnal Progression Chart */}
      <Panel
        title="24-Hour Diurnal Energy Flux & Temperature Cycle"
        subtitle="Hourly progression from nocturnal terrestrial cooling to peak solar noon"
      >
        <div className="h-72 w-full mt-3">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={model.diurnalCycle} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
              <XAxis dataKey="timeLabel" tick={{ fill: '#6A6A9F', fontSize: 10 }} axisLine={{ stroke: '#242748' }} />
              <YAxis yAxisId="left" tick={{ fill: '#6A6A9F', fontSize: 10 }} axisLine={{ stroke: '#242748' }} label={{ value: 'Energy Flux (W/m²)', angle: -90, position: 'insideLeft', fill: '#6A6A9F', fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6A6A9F', fontSize: 10 }} axisLine={{ stroke: '#242748' }} label={{ value: 'Temperature (°C)', angle: 90, position: 'insideRight', fill: '#6A6A9F', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#191932', borderColor: '#323273', borderRadius: '12px', fontSize: '11px' }} />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Line yAxisId="left" type="monotone" dataKey="netRadiation" name="Net Radiation (Rn)" stroke="#FFA63F" strokeWidth={2.5} dot={false} />
              <Line yAxisId="left" type="monotone" dataKey="sensibleHeat" name="Sensible Heat (H)" stroke="#EC223B" strokeWidth={2} dot={false} />
              <Line yAxisId="left" type="monotone" dataKey="latentHeat" name="Latent Heat (λE)" stroke="#4DFFDF" strokeWidth={2} dot={false} />
              <Line yAxisId="right" type="monotone" dataKey="surfaceTemp" name="Surface LST (°C)" stroke="#FF7A00" strokeWidth={2} strokeDasharray="3 3" dot={false} />
              <Line yAxisId="right" type="monotone" dataKey="airTemp" name="Air Temp (°C)" stroke="#38BDF8" strokeWidth={2} strokeDasharray="3 3" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
};
