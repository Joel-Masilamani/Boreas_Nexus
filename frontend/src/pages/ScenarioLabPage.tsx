import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { MapView } from '../components/map/MapView';
import { MetricCard } from '../components/common/MetricCard';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { 
  Sliders, 
  Play, 
  RotateCcw, 
  Sparkles, 
  ShieldCheck, 
  Trees, 
  Building2, 
  Droplets, 
  Coins, 
  CheckCircle2, 
  Loader2,
  TrendingDown,
  Layers
} from 'lucide-react';

export const ScenarioLabPage: React.FC = () => {
  const {
    selectedHotspot,
    scenarioInterventions,
    scenarioResult,
    setScenarioInterventions,
    runScenarioSimulation,
    isSimulating,
  } = useAppStore();

  const [activePreset, setActivePreset] = useState<string>('custom');
  const [simulationLogs, setSimulationLogs] = useState<string[]>([]);

  if (!selectedHotspot || !scenarioResult) {
    return (
      <div className="p-8 text-center text-white">
        <p className="text-sm text-[#6A6A9F]">Please select a hotspot to configure cooling simulation scenarios.</p>
      </div>
    );
  }

  const handleApplyPreset = (preset: string) => {
    setActivePreset(preset);
    if (preset === 'cool_roof') {
      setScenarioInterventions({
        coolRoofCoverage: 65,
        greenRoofCoverage: 10,
        treeCanopyCoverage: 15,
        permeablePavementCoverage: 10,
        waterInfrastructureCoverage: 0,
      });
    } else if (preset === 'green_corridor') {
      setScenarioInterventions({
        coolRoofCoverage: 20,
        greenRoofCoverage: 35,
        treeCanopyCoverage: 45,
        permeablePavementCoverage: 20,
        waterInfrastructureCoverage: 10,
      });
    } else if (preset === 'hybrid') {
      setScenarioInterventions({
        coolRoofCoverage: 50,
        greenRoofCoverage: 20,
        treeCanopyCoverage: 30,
        permeablePavementCoverage: 25,
        waterInfrastructureCoverage: 5,
      });
    } else if (preset === 'max_cooling') {
      setScenarioInterventions({
        coolRoofCoverage: 75,
        greenRoofCoverage: 40,
        treeCanopyCoverage: 55,
        permeablePavementCoverage: 40,
        waterInfrastructureCoverage: 15,
      });
    }
  };

  const handleRunSimulation = async () => {
    setSimulationLogs([
      'Loading baseline observed thermal state (Module 1)...',
      'Applying spatial intervention parameters & material albedos...',
      'Evaluating coupled sensible/latent thermodynamic response...',
      'Computing canopy microclimate cooling yield & budget delta...',
      'SIMULATION COMPLETE: Scenario projected successfully.',
    ]);
    await runScenarioSimulation();
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Demonstration Banner */}
      <div className="p-3.5 rounded-2xl bg-[#942BE6]/10 border border-[#942BE6]/40 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 text-xs text-[#C084FC]">
          <Sparkles className="w-4 h-4 text-[#4DFFDF] shrink-0" />
          <span>
            <strong className="text-white uppercase tracking-wider font-bold">Demonstration Mode:</strong> Scenario Simulation Engine & Microclimate Intervention Modeling
          </span>
        </div>
        <Badge variant="purple">DEMO / SIMULATION</Badge>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#323273]">
        <div>
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
            Module 4 • Cooling Scenario Simulation Lab
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Intervention Testing & Thermal Abatement Modeling
          </h1>
          <p className="text-xs text-[#A5A5D8] mt-0.5">
            Simulate cool roofs, urban forestry, green roofs, permeable surfaces, and blue infrastructure for {selectedHotspot.hotspot_id}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="cyan" dot>Target: {selectedHotspot.hotspot_id}</Badge>
          <Badge variant="warm">Baseline LST {selectedHotspot.mean_lst}°C</Badge>
        </div>
      </div>

      {/* Main 3-Column Layout: Controls | Map | Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Intervention Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Panel title="Intervention Configuration" subtitle="Adjust spatial retrofitting coverage targets">
            {/* Quick Strategy Presets */}
            <div className="mb-4">
              <span className="text-[10px] font-bold tracking-[2px] uppercase text-[#6A6A9F] block mb-2">
                Strategy Presets:
              </span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleApplyPreset('cool_roof')}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold text-left border transition-all cursor-pointer ${
                    activePreset === 'cool_roof'
                      ? 'bg-[#1F1F43] border-[#4DFFDF] text-white'
                      : 'bg-[#14142B] border-[#242748] text-[#A5A5D8] hover:text-white'
                  }`}
                >
                  🏢 Cool Roof Focus
                </button>
                <button
                  onClick={() => handleApplyPreset('green_corridor')}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold text-left border transition-all cursor-pointer ${
                    activePreset === 'green_corridor'
                      ? 'bg-[#1F1F43] border-[#5EFF5A] text-white'
                      : 'bg-[#14142B] border-[#242748] text-[#A5A5D8] hover:text-white'
                  }`}
                >
                  🌳 Green Corridor
                </button>
                <button
                  onClick={() => handleApplyPreset('hybrid')}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold text-left border transition-all cursor-pointer ${
                    activePreset === 'hybrid'
                      ? 'bg-[#1F1F43] border-[#176BF8] text-white shadow-[0_0_10px_rgba(23,107,248,0.3)]'
                      : 'bg-[#14142B] border-[#242748] text-[#A5A5D8] hover:text-white'
                  }`}
                >
                  ⚡ Hybrid (Recommended)
                </button>
                <button
                  onClick={() => handleApplyPreset('max_cooling')}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold text-left border transition-all cursor-pointer ${
                    activePreset === 'max_cooling'
                      ? 'bg-[#1F1F43] border-[#C084FC] text-white'
                      : 'bg-[#14142B] border-[#242748] text-[#A5A5D8] hover:text-white'
                  }`}
                >
                  ❄ Maximum Abatement
                </button>
              </div>
            </div>

            {/* Sliders */}
            <div className="space-y-4 pt-2 border-t border-[#242748]">
              {/* Cool Roof */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-[#38BDF8]" />
                    Cool Roof Coverage
                  </span>
                  <span className="font-bold text-[#4DFFDF] tabular-nums">
                    {scenarioInterventions.coolRoofCoverage}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={scenarioInterventions.coolRoofCoverage}
                  onChange={(e) => {
                    setActivePreset('custom');
                    setScenarioInterventions({ coolRoofCoverage: Number(e.target.value) });
                  }}
                  className="w-full accent-[#4DFFDF] bg-[#05050F] h-1.5 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-[#6A6A9F] mt-0.5">
                  <span>Albedo 0.15 → 0.70</span>
                  <span>Est: -{((scenarioInterventions.coolRoofCoverage / 100) * 2.6).toFixed(1)}°C yield</span>
                </div>
              </div>

              {/* Tree Canopy */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Trees className="w-3.5 h-3.5 text-[#5EFF5A]" />
                    Urban Tree Canopy Infill
                  </span>
                  <span className="font-bold text-[#5EFF5A] tabular-nums">
                    {scenarioInterventions.treeCanopyCoverage}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={scenarioInterventions.treeCanopyCoverage}
                  onChange={(e) => {
                    setActivePreset('custom');
                    setScenarioInterventions({ treeCanopyCoverage: Number(e.target.value) });
                  }}
                  className="w-full accent-[#5EFF5A] bg-[#05050F] h-1.5 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-[#6A6A9F] mt-0.5">
                  <span>Shading & Transpiration</span>
                  <span>Est: -{((scenarioInterventions.treeCanopyCoverage / 100) * 3.8).toFixed(1)}°C yield</span>
                </div>
              </div>

              {/* Green Roof */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#4DFFDF]" />
                    Extensive Green Roofs
                  </span>
                  <span className="font-bold text-white tabular-nums">
                    {scenarioInterventions.greenRoofCoverage}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={scenarioInterventions.greenRoofCoverage}
                  onChange={(e) => {
                    setActivePreset('custom');
                    setScenarioInterventions({ greenRoofCoverage: Number(e.target.value) });
                  }}
                  className="w-full accent-[#38BDF8] bg-[#05050F] h-1.5 rounded-lg cursor-pointer"
                />
              </div>

              {/* Permeable Pavements */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-[#FFA63F]" />
                    Permeable Pavements
                  </span>
                  <span className="font-bold text-white tabular-nums">
                    {scenarioInterventions.permeablePavementCoverage}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={scenarioInterventions.permeablePavementCoverage}
                  onChange={(e) => {
                    setActivePreset('custom');
                    setScenarioInterventions({ permeablePavementCoverage: Number(e.target.value) });
                  }}
                  className="w-full accent-[#FFA63F] bg-[#05050F] h-1.5 rounded-lg cursor-pointer"
                />
              </div>

              {/* Water / Blue Infrastructure */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Droplets className="w-3.5 h-3.5 text-[#38BDF8]" />
                    Blue Infrastructure (Micro-Swales)
                  </span>
                  <span className="font-bold text-[#38BDF8] tabular-nums">
                    {scenarioInterventions.waterInfrastructureCoverage}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={scenarioInterventions.waterInfrastructureCoverage}
                  onChange={(e) => {
                    setActivePreset('custom');
                    setScenarioInterventions({ waterInfrastructureCoverage: Number(e.target.value) });
                  }}
                  className="w-full accent-[#38BDF8] bg-[#05050F] h-1.5 rounded-lg cursor-pointer"
                />
              </div>

              {/* Budget Slider */}
              <div className="pt-2 border-t border-[#242748]">
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-[#FFA63F]" />
                    Budget Allocation Constraint
                  </span>
                  <span className="font-extrabold text-[#FFA63F] tabular-nums">
                    ₹{scenarioInterventions.budgetCr} Crore
                  </span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="50"
                  step="1"
                  value={scenarioInterventions.budgetCr}
                  onChange={(e) => {
                    setScenarioInterventions({ budgetCr: Number(e.target.value) });
                  }}
                  className="w-full accent-[#FFA63F] bg-[#05050F] h-1.5 rounded-lg cursor-pointer"
                />
              </div>
            </div>

            {/* Run Button */}
            <div className="pt-4 border-t border-[#242748] mt-4">
              <button
                onClick={handleRunSimulation}
                disabled={isSimulating}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#176BF8] to-[#942BE6] hover:opacity-95 text-white text-xs font-extrabold tracking-wider uppercase transition-all shadow-[0_0_20px_rgba(23,107,248,0.4)] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isSimulating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing Thermal Simulation...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Run Scenario Simulation</span>
                  </>
                )}
              </button>
            </div>
          </Panel>
        </div>

        {/* Right Column: Results & Telemetry (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Baseline vs Projected Table */}
          <Panel title="Simulation Projected Thermal Response" subtitle="Deterministic physical abatement response">
            <div className="grid grid-cols-3 gap-3 text-center mb-4">
              <div className="p-3.5 rounded-xl bg-[#14142B] border border-[#242748]">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#6A6A9F] block">
                  Baseline LST
                </span>
                <div className="text-xl font-extrabold text-white mt-1 tabular-nums">
                  {scenarioResult.baselineLST}°C
                </div>
                <span className="text-[10px] text-[#A5A5D8]">Observed Satellite</span>
              </div>

              <div className="p-3.5 rounded-xl bg-[#25245D] border border-[#4DFFDF]/40 shadow-[0_0_15px_rgba(77,255,223,0.15)]">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#4DFFDF] block">
                  Projected LST
                </span>
                <div className="text-xl font-extrabold text-[#4DFFDF] mt-1 tabular-nums">
                  {scenarioResult.projectedLST}°C
                </div>
                <span className="text-[10px] text-[#A5A5D8]">Post-Intervention</span>
              </div>

              <div className="p-3.5 rounded-xl bg-[#14142B] border border-[#5EFF5A]/40">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#5EFF5A] block">
                  Net Cooling Drop
                </span>
                <div className="text-xl font-extrabold text-[#5EFF5A] mt-1 tabular-nums flex items-center justify-center gap-1">
                  <TrendingDown className="w-4 h-4 text-[#5EFF5A]" />
                  -{scenarioResult.lstReduction}°C
                </div>
                <span className="text-[10px] text-[#A5A5D8]">Thermal Mitigation</span>
              </div>
            </div>

            {/* Detailed Metric Rows */}
            <div className="space-y-2 text-xs border-t border-[#242748] pt-3">
              <div className="flex justify-between items-center py-1.5 border-b border-[#242748]/50">
                <span className="text-[#A5A5D8]">2m Air Temperature:</span>
                <div className="flex items-center gap-3">
                  <span className="text-[#6A6A9F] line-through">{scenarioResult.baselineAirTemp}°C</span>
                  <span className="font-bold text-white">{scenarioResult.projectedAirTemp}°C</span>
                  <span className="text-[#5EFF5A] font-bold">(-{scenarioResult.airTempReduction}°C)</span>
                </div>
              </div>

              <div className="flex justify-between items-center py-1.5 border-b border-[#242748]/50">
                <span className="text-[#A5A5D8]">SUHII Intensity Anomaly:</span>
                <div className="flex items-center gap-3">
                  <span className="text-[#6A6A9F] line-through">+{scenarioResult.baselineSUHII}°C</span>
                  <span className="font-bold text-white">+{scenarioResult.projectedSUHII}°C</span>
                  <span className="text-[#5EFF5A] font-bold">(-{scenarioResult.suhiiReduction}°C)</span>
                </div>
              </div>

              <div className="flex justify-between items-center py-1.5 border-b border-[#242748]/50">
                <span className="text-[#A5A5D8]">Estimated Implementation Capital:</span>
                <div className="flex items-center gap-2">
                  <strong className={scenarioResult.budgetRemainingCr >= 0 ? 'text-white' : 'text-[#EC223B]'}>
                    ₹{scenarioResult.totalCostCr} Cr
                  </strong>
                  <span className="text-[10px] text-[#6A6A9F]">
                    (₹{scenarioResult.budgetRemainingCr} Cr remaining)
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center py-1.5">
                <span className="text-[#A5A5D8]">Annual Sequestered Carbon Offset:</span>
                <strong className="text-[#5EFF5A]">{scenarioResult.co2OffsetTonsYear} tons CO₂e / yr</strong>
              </div>
            </div>
          </Panel>

          {/* Simulation Telemetry Console */}
          <Panel title="Simulation Execution Telemetry" subtitle="Multi-stage physics propagation sequence">
            <div className="font-mono text-[11px] p-3 rounded-xl bg-[#05050F] border border-[#242748] space-y-1.5 min-h-[110px]">
              {simulationLogs.length > 0 ? (
                simulationLogs.map((log, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-[#4DFFDF]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#5EFF5A] shrink-0" />
                    <span>{log}</span>
                  </div>
                ))
              ) : (
                <div className="text-[#6A6A9F] flex items-center gap-2">
                  <span>● Engine idle. Ready to evaluate scenario.</span>
                </div>
              )}
            </div>
          </Panel>

          {/* Contextual Hotspot Footprint Map Preview */}
          <div className="h-56 rounded-2xl overflow-hidden border border-[#323273] relative shadow-lg">
            <MapView showControls={false} showLegend={false} showDrawer={false} />
          </div>
        </div>
      </div>
    </div>
  );
};
