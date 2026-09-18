import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { decisionService } from '../services/mock/decisionService';
import { ParetoTradeoffChart } from '../components/visual/ParetoTradeoffChart';
import { MetricCard } from '../components/common/MetricCard';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { 
  Compass, 
  Sparkles, 
  Coins, 
  ShieldCheck, 
  Award, 
  ArrowRight, 
  CheckCircle, 
  FileText,
  Clock,
  Layers
} from 'lucide-react';

export const DecisionCenterPage: React.FC = () => {
  const { selectedHotspot } = useAppStore();
  const [selectedPresetId, setSelectedPresetId] = useState<string>('hybrid_strategy');

  if (!selectedHotspot) {
    return (
      <div className="p-8 text-center text-white">
        <p className="text-sm text-[#6A6A9F]">Please select a hotspot to view its decision-support strategy.</p>
      </div>
    );
  }

  const presets = decisionService.getStandardPresets(selectedHotspot, 25);
  const activePreset = presets.find((p) => p.id === selectedPresetId) || presets[2];
  const paretoPoints = decisionService.getParetoCurve(selectedHotspot, 25);
  const actions = decisionService.getPlanningActions(selectedHotspot, activePreset);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Demonstration Banner */}
      <div className="p-3.5 rounded-2xl bg-[#942BE6]/10 border border-[#942BE6]/40 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 text-xs text-[#C084FC]">
          <Sparkles className="w-4 h-4 text-[#4DFFDF] shrink-0" />
          <span>
            <strong className="text-white uppercase tracking-wider font-bold">Demonstration Output:</strong> Urban Climate Decision Intelligence & Multi-Criteria Planning Optimization
          </span>
        </div>
        <Badge variant="purple">DEMO / DECISION SUPPORT</Badge>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#323273]">
        <div>
          <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
            Module 5 • Urban Climate Decision Intelligence Engine
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Prioritized Mitigation Strategy & Actionable Urban Zoning
          </h1>
          <p className="text-xs text-[#A5A5D8] mt-0.5">
            Pareto-optimal allocation of cool infrastructure, capital constraints, and implementation roadmaps for {selectedHotspot.hotspot_id}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="cyan" dot>Target: {selectedHotspot.hotspot_id}</Badge>
          <Badge variant="moderate">Budget ≤ ₹25 Crore</Badge>
        </div>
      </div>

      {/* Strategic Presets Grid */}
      <div>
        <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F] mb-3">
          Evaluated Strategy Options (Ranked by Multi-Criteria Pareto Scoring):
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {presets.map((preset) => {
            const isSelected = selectedPresetId === preset.id;
            return (
              <div
                key={preset.id}
                onClick={() => setSelectedPresetId(preset.id)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? 'bg-[#25245D] border-[#4DFFDF] shadow-[0_0_20px_rgba(77,255,223,0.2)]'
                    : 'bg-[#191932] border-[#242748] hover:border-[#323273] hover:bg-[#1F1F43]'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-xs font-bold text-white tracking-wide">
                      {preset.name}
                    </span>
                    {isSelected && (
                      <span className="w-2 h-2 rounded-full bg-[#4DFFDF] shadow-[0_0_8px_#4DFFDF]" />
                    )}
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#4DFFDF] mb-2">
                    {preset.tagline}
                  </div>
                  <p className="text-[11px] text-[#A5A5D8] leading-relaxed mb-3">
                    {preset.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-[#242748] space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[#6A6A9F]">Cooling Drop:</span>
                    <strong className="text-[#5EFF5A]">-{preset.coolingImpact}°C LST</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#6A6A9F]">Est. Cost:</span>
                    <strong className="text-white">₹{preset.costCr} Cr</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#6A6A9F]">Feasibility:</span>
                    <strong className="text-[#4DFFDF]">{preset.feasibilityPct}%</strong>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pareto Trade-off Frontier Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7">
          <ParetoTradeoffChart
            points={paretoPoints}
            budgetCr={25}
            onSelectPoint={(p) => console.log('Selected Pareto point:', p)}
          />
        </div>

        {/* Selected Strategy Summary */}
        <div className="lg:col-span-5 space-y-4">
          <Panel
            title="Selected Strategy Summary"
            subtitle={activePreset.name}
            variant="elevated"
          >
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="p-3 rounded-xl bg-[#14142B] border border-[#242748]">
                <span className="text-[10px] text-[#6A6A9F] uppercase font-bold tracking-wider">Projected Cooling</span>
                <div className="text-xl font-extrabold text-[#5EFF5A] mt-1">
                  -{activePreset.coolingImpact}°C
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#14142B] border border-[#242748]">
                <span className="text-[10px] text-[#6A6A9F] uppercase font-bold tracking-wider">Implementation Cost</span>
                <div className="text-xl font-extrabold text-white mt-1">
                  ₹{activePreset.costCr} Cr
                </div>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-[#242748]">
                <span className="text-[#A5A5D8]">Cool Roof Target:</span>
                <strong className="text-[#4DFFDF]">{activePreset.interventions.coolRoofCoverage}% coverage</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#242748]">
                <span className="text-[#A5A5D8]">Urban Tree Canopy:</span>
                <strong className="text-[#5EFF5A]">{activePreset.interventions.treeCanopyCoverage}% coverage</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#242748]">
                <span className="text-[#A5A5D8]">Green Roof Target:</span>
                <strong className="text-white">{activePreset.interventions.greenRoofCoverage}% coverage</strong>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#A5A5D8]">Permeable Pavement:</span>
                <strong className="text-white">{activePreset.interventions.permeablePavementCoverage}% coverage</strong>
              </div>
            </div>
          </Panel>
        </div>
      </div>

      {/* Prioritized Planning Action Items Table */}
      <Panel
        title="Prioritized Urban Planning Action Items"
        subtitle="Operational roadmap for municipal engineering & zoning implementation"
      >
        <div className="overflow-x-auto mt-2">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-[#323273] text-[#6A6A9F] uppercase text-[10px] tracking-wider">
                <th className="pb-3 font-bold">Priority</th>
                <th className="pb-3 font-bold">Intervention Policy</th>
                <th className="pb-3 font-bold">Target Extent</th>
                <th className="pb-3 font-bold">Capital Est.</th>
                <th className="pb-3 font-bold">Cooling Yield</th>
                <th className="pb-3 font-bold">Regulatory Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#242748]">
              {actions.map((act) => (
                <tr key={act.id} className="hover:bg-[#1F1F43]/40 transition-colors">
                  <td className="py-3 font-bold">
                    <Badge variant={act.priority === 'Immediate' ? 'hot' : act.priority === 'Phase 1' ? 'cyan' : 'purple'}>
                      {act.priority}
                    </Badge>
                  </td>
                  <td className="py-3 font-semibold text-white max-w-xs">
                    {act.action}
                  </td>
                  <td className="py-3 text-[#A5A5D8]">
                    {act.targetCoverage}
                  </td>
                  <td className="py-3 font-bold text-white tabular-nums">
                    ₹{act.costEstimateCr} Cr
                  </td>
                  <td className="py-3 font-bold text-[#5EFF5A] tabular-nums">
                    {act.coolingYield}
                  </td>
                  <td className="py-3">
                    <span className="text-[11px] font-semibold text-[#4DFFDF]">
                      {act.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
};
