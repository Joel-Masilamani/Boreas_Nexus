import React from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, ReferenceLine, ZAxis, Cell } from 'recharts';

interface ParetoPoint {
  name: string;
  costCr: number;
  coolingLST: number;
  airTempDrop: number;
  feasibility: number;
  withinBudget: boolean;
}

interface ParetoTradeoffChartProps {
  points: ParetoPoint[];
  budgetCr?: number;
  onSelectPoint?: (point: ParetoPoint) => void;
  className?: string;
}

export const ParetoTradeoffChart: React.FC<ParetoTradeoffChartProps> = ({
  points,
  budgetCr = 25,
  onSelectPoint,
  className,
}) => {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload as ParetoPoint;
      return (
        <div className="bg-[#191932] border border-[#323273] p-3 rounded-xl shadow-xl text-xs font-sans">
          <div className="font-bold text-white mb-1">{d.name}</div>
          <div className="space-y-1 text-[#A5A5D8]">
            <div className="flex justify-between gap-4">
              <span>Cooling Impact:</span>
              <strong className="text-[#4DFFDF]">-{d.coolingLST.toFixed(2)}°C LST</strong>
            </div>
            <div className="flex justify-between gap-4">
              <span>Est. Cost:</span>
              <strong className={d.withinBudget ? 'text-white' : 'text-[#FF4D4D]'}>
                ₹{d.costCr.toFixed(2)} Cr
              </strong>
            </div>
            <div className="flex justify-between gap-4">
              <span>Feasibility:</span>
              <strong className="text-[#5EFF5A]">{d.feasibility}%</strong>
            </div>
          </div>
          <div className="text-[10px] text-[#6A6A9F] mt-2 pt-1 border-t border-[#242748]">
            {d.withinBudget ? '✓ Compliant with budget constraint' : '⚠ Exceeds allocation limit'}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`p-5 rounded-2xl bg-[#191932] border border-[#323273] ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-bold text-white tracking-wide">
            Cooling vs Cost Trade-off Frontier
          </h4>
          <p className="text-[11px] text-[#6A6A9F]">
            Pareto curve comparing thermal abatement yield vs municipal capital expense
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-semibold text-[#6A6A9F]">
          <span className="w-2.5 h-0.5 bg-[#FF7A00] inline-block" />
          <span>Budget Limit (₹{budgetCr} Cr)</span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 10 }}>
            <XAxis
              type="number"
              dataKey="costCr"
              name="Cost"
              unit=" Cr"
              tick={{ fill: '#6A6A9F', fontSize: 10 }}
              axisLine={{ stroke: '#242748' }}
              tickLine={{ stroke: '#242748' }}
              label={{ value: 'Implementation Cost (₹ Crore)', position: 'insideBottom', offset: -10, fill: '#6A6A9F', fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="coolingLST"
              name="Cooling"
              unit="°C"
              tick={{ fill: '#6A6A9F', fontSize: 10 }}
              axisLine={{ stroke: '#242748' }}
              tickLine={{ stroke: '#242748' }}
              label={{ value: 'Projected Cooling (-°C LST)', angle: -90, position: 'insideLeft', fill: '#6A6A9F', fontSize: 11 }}
            />
            <ZAxis type="number" dataKey="feasibility" range={[70, 220]} name="Feasibility" />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={budgetCr} stroke="#FF7A00" strokeDasharray="4 4" strokeWidth={1.5} />
            <Scatter
              data={points}
              onClick={(e: any) => {
                if (onSelectPoint && e) {
                  onSelectPoint(e.payload || (e as ParetoPoint));
                }
              }}
              cursor="pointer"
            >
              {points.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.withinBudget ? '#4DFFDF' : '#FF4D4D'}
                  stroke="#FFFFFF"
                  strokeWidth={1.5}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
