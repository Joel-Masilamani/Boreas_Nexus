import React from 'react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import {
  LayoutDashboard,
  Flame,
  Network,
  Activity,
  Sliders,
  Compass,
  BarChart3,
  Globe2,
  Info,
} from 'lucide-react';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  badge?: string;
  isProjected?: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, badge, isProjected }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      clsx(
        'group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 relative',
        isActive
          ? 'bg-[#1F1F43] text-white border border-[#323273] shadow-[0_0_15px_rgba(23,107,248,0.2)]'
          : 'text-[#A5A5D8] hover:text-white hover:bg-[#191932]/70'
      )
    }
  >
    {({ isActive }) => (
      <>
        <div className="flex items-center gap-3">
          <div
            className={clsx(
              'w-7 h-7 rounded-lg flex items-center justify-center transition-colors',
              isActive
                ? 'bg-[#176BF8] text-white shadow-[0_0_10px_#176BF8]'
                : 'text-[#6A6A9F] group-hover:text-[#4DFFDF] group-hover:bg-[#191932]'
            )}
          >
            {icon}
          </div>
          <span className="truncate">{label}</span>
        </div>

        <div className="flex items-center gap-1.5">
          {badge && (
            <span className="text-[9px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-[#25245D] text-[#4DFFDF] border border-[#323273]">
              {badge}
            </span>
          )}
          {isProjected && (
            <span className="text-[8px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#942BE6]/20 text-[#C084FC] border border-[#942BE6]/30">
              DEMO
            </span>
          )}
          {isActive && (
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-[#4DFFDF] rounded-l-full shadow-[0_0_8px_#4DFFDF]" />
          )}
        </div>
      </>
    )}
  </NavLink>
);

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#05050F] border-r border-[#323273] flex flex-col justify-between h-screen shrink-0 sticky top-0 z-40">
      {/* Brand Header */}
      <div>
        <div className="h-16 px-5 flex items-center gap-3 border-b border-[#323273]">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#176BF8] to-[#942BE6] p-0.5 shadow-[0_0_15px_rgba(23,107,248,0.5)]">
            <div className="w-full h-full bg-[#05050F] rounded-[10px] flex items-center justify-center">
              <Globe2 className="w-5 h-5 text-[#4DFFDF]" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-extrabold tracking-wider text-white">BOREAS</span>
              <span className="text-sm font-extrabold tracking-wider text-[#4DFFDF]">NEXUS</span>
            </div>
            <p className="text-[9px] uppercase tracking-[3px] text-[#6A6A9F] font-bold">
              Urban Heat Command
            </p>
          </div>
        </div>

        {/* Navigation Groups */}
        <div className="p-3 space-y-5 overflow-y-auto max-h-[calc(100vh-140px)]">
          {/* Overview */}
          <div>
            <NavItem
              to="/overview"
              icon={<LayoutDashboard className="w-4 h-4" />}
              label="Overview"
              badge="M1"
            />
          </div>

          {/* Thermal Intelligence */}
          <div className="space-y-1">
            <div className="px-3 pb-1 text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
              Thermal Intelligence
            </div>
            <NavItem
              to="/heat-intelligence"
              icon={<Flame className="w-4 h-4" />}
              label="Heat Intelligence"
              badge="Real"
            />
            <NavItem
              to="/drivers"
              icon={<Network className="w-4 h-4" />}
              label="Driver Intelligence"
              badge="Real"
            />
            <NavItem
              to="/thermal-dynamics"
              icon={<Activity className="w-4 h-4" />}
              label="Thermal Dynamics"
              isProjected
            />
          </div>

          {/* Decision Support */}
          <div className="space-y-1">
            <div className="px-3 pb-1 text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
              Decision Support
            </div>
            <NavItem
              to="/scenario-lab"
              icon={<Sliders className="w-4 h-4" />}
              label="Scenario Lab"
              isProjected
            />
            <NavItem
              to="/decision-center"
              icon={<Compass className="w-4 h-4" />}
              label="Decision Center"
              isProjected
            />
          </div>

          {/* Analytics */}
          <div className="space-y-1">
            <div className="px-3 pb-1 text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
              Analytics
            </div>
            <NavItem
              to="/analytics"
              icon={<BarChart3 className="w-4 h-4" />}
              label="Urban Analytics"
            />
          </div>
        </div>
      </div>

      {/* System Run Footer */}
      <div className="p-3 border-t border-[#323273] bg-[#090915]">
        <div className="p-2.5 rounded-xl bg-[#191932] border border-[#242748] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#5EFF5A] shadow-[0_0_6px_#5EFF5A]" />
            <div>
              <div className="text-[10px] font-bold text-white uppercase tracking-wider">
                Pipeline v1.0.0
              </div>
              <div className="text-[9px] text-[#6A6A9F]">
                Chennai 100m Grid
              </div>
            </div>
          </div>
          <Info className="w-3.5 h-3.5 text-[#6A6A9F]" />
        </div>
      </div>
    </aside>
  );
};
