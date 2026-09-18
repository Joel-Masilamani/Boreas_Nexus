import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { MapView } from '../components/map/MapView';
import { MetricCard } from '../components/common/MetricCard';
import { Badge } from '../components/common/Badge';
import { 
  Flame, 
  Grid, 
  Moon, 
  Sun, 
  TrendingUp, 
  ShieldCheck, 
  Search,
  SlidersHorizontal,
  ChevronRight,
  Maximize2
} from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const { 
    cityKPIs, 
    hotspotsRegistry, 
    selectedHotspotId, 
    setSelectedHotspotId,
    setDrawerOpen 
  } = useAppStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [periodFilter, setPeriodFilter] = useState<'ALL' | 'DAY' | 'NIGHT'>('ALL');
  const [sortBy, setSortBy] = useState<'peak_lst' | 'cluster_area_m2' | 'mean_suhii' | 'mean_heat_persistence'>('peak_lst');

  // Filter and sort hotspots
  const filteredHotspots = hotspotsRegistry
    .filter((h) => {
      const matchesSearch = h.hotspot_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            h.dominant_driver.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesPeriod = periodFilter === 'ALL' || h.period === periodFilter;
      return matchesSearch && matchesPeriod;
    })
    .sort((a, b) => (b[sortBy] || 0) - (a[sortBy] || 0));

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top KPI Strip - Calculated directly from real Module 1 metadata */}
      <section className="px-6 py-4 border-b border-[#323273] bg-[#090915] shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
              Chennai Metropolitan Region • Observed Baseline (Module 1)
            </div>
            <h1 className="text-xl font-extrabold text-white tracking-tight">
              Urban Heat Island & Thermal Vulnerability Command
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="cyan" dot>
              Landsat-8/9 & Sentinel-2 L2SP
            </Badge>
            <Badge variant="purple">
              100m Spatial Grid
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricCard
            label="Total Cells"
            value={(cityKPIs?.total_sample_points || 44298).toLocaleString()}
            subtext="100m Grid Ingestion"
            icon={<Grid className="w-4 h-4" />}
          />
          <MetricCard
            label="Day Hotspots"
            value={(cityKPIs?.day_hotspot_count || 7451).toLocaleString()}
            subtext="95% & 99% Conf Cells"
            highlightColor="warm"
            icon={<Sun className="w-4 h-4" />}
          />
          <MetricCard
            label="Night Hotspots"
            value={(cityKPIs?.night_hotspot_count || 13895).toLocaleString()}
            subtext="Nocturnal Heat Islands"
            highlightColor="purple"
            icon={<Moon className="w-4 h-4" />}
          />
          <MetricCard
            label="Persistent Heat"
            value={(cityKPIs?.persistent_hotspots || 1403).toLocaleString()}
            subtext="Diurnal Heat Retention"
            highlightColor="extreme"
            icon={<Flame className="w-4 h-4" />}
          />
          <MetricCard
            label="Mean Day SUHII"
            value={`+${cityKPIs?.urban_mean_day_suhii_celsius || 1.23}°C`}
            subtext="Urban vs Rural Delta"
            highlightColor="warm"
            icon={<TrendingUp className="w-4 h-4" />}
          />
          <MetricCard
            label="Mean Night SUHII"
            value={`+${cityKPIs?.urban_mean_night_suhii_celsius || 4.31}°C`}
            subtext="Canopy Heat Retention"
            highlightColor="hot"
            icon={<ShieldCheck className="w-4 h-4" />}
          />
        </div>
      </section>

      {/* Main Map & Hotspot Explorer Split */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
        {/* Dominant GIS Map Container */}
        <div className="flex-1 h-full relative">
          <MapView />
        </div>

        {/* Right Hotspot Quick-List Panel */}
        <aside className="w-full lg:w-96 border-t lg:border-t-0 lg:border-l border-[#323273] bg-[#090915] flex flex-col h-64 lg:h-full shrink-0 z-10">
          <div className="p-4 border-b border-[#242748]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold tracking-[2px] uppercase text-[#6A6A9F]">
                Hotspot Clusters ({filteredHotspots.length})
              </span>
              <div className="flex items-center gap-1 text-xs">
                {(['ALL', 'DAY', 'NIGHT'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriodFilter(p)}
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase transition-colors cursor-pointer ${
                      periodFilter === p
                        ? 'bg-[#176BF8] text-white'
                        : 'text-[#6A6A9F] hover:text-white bg-[#191932]'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#6A6A9F]" />
              <input
                type="text"
                placeholder="Search by ID or driver..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#191932] border border-[#323273] text-xs text-white placeholder-[#6A6A9F] focus:outline-none focus:border-[#4DFFDF]"
              />
            </div>

            {/* Sort Selector */}
            <div className="flex items-center justify-between text-[11px] text-[#6A6A9F] mt-2">
              <span>Sort by:</span>
              <select
                value={sortBy}
                onChange={(e: any) => setSortBy(e.target.value)}
                className="bg-[#191932] border border-[#323273] text-white rounded px-2 py-0.5 text-[11px] focus:outline-none cursor-pointer"
              >
                <option value="peak_lst">Peak LST (°C)</option>
                <option value="mean_suhii">Mean SUHII</option>
                <option value="cluster_area_m2">Cluster Area</option>
                <option value="mean_heat_persistence">Persistence</option>
              </select>
            </div>
          </div>

          {/* Scrollable Hotspot Cards */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {filteredHotspots.map((h) => {
              const isSelected = selectedHotspotId === h.hotspot_id;
              const areaHa = (h.cluster_area_m2 / 10000).toFixed(1);
              return (
                <div
                  key={h.hotspot_id}
                  onClick={() => {
                    setSelectedHotspotId(h.hotspot_id);
                    setDrawerOpen(true);
                  }}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#25245D] border-[#4DFFDF] shadow-[0_0_15px_rgba(77,255,223,0.2)]'
                      : 'bg-[#191932] border-[#242748] hover:border-[#323273] hover:bg-[#1F1F43]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white tracking-wide">
                        {h.hotspot_id}
                      </span>
                      <Badge variant={h.period === 'DAY' ? 'warm' : 'purple'}>
                        {h.period}
                      </Badge>
                    </div>
                    <span className="text-xs font-extrabold text-[#EC223B] tabular-nums">
                      {h.peak_lst}°C
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-1 text-[11px] text-[#A5A5D8] mb-2">
                    <div>
                      <span className="text-[#6A6A9F] text-[9px] uppercase block">Mean</span>
                      <strong className="text-white">{h.mean_lst}°C</strong>
                    </div>
                    <div>
                      <span className="text-[#6A6A9F] text-[9px] uppercase block">SUHII</span>
                      <strong className="text-[#FFA63F]">+{h.mean_suhii}°C</strong>
                    </div>
                    <div>
                      <span className="text-[#6A6A9F] text-[9px] uppercase block">Area</span>
                      <strong className="text-white">{areaHa} ha</strong>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1.5 border-t border-[#242748]/60 text-[10px]">
                    <span className="text-[#6A6A9F] capitalize truncate max-w-[170px]">
                      Driver: <span className="text-[#4DFFDF]">{h.dominant_driver.replace(/_/g, ' ')}</span>
                    </span>
                    <span className="text-[#A5A5D8] flex items-center gap-0.5">
                      Details <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>
      </div>
    </div>
  );
};
