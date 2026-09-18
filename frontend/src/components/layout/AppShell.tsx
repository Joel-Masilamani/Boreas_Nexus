import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { HotspotDrawer } from '../map/HotspotDrawer';
import { useAppStore } from '../../store/useAppStore';
import { Loader2, AlertTriangle } from 'lucide-react';

export const AppShell: React.FC = () => {
  const { loadInitialData, isLoading, error } = useAppStore();

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[#05050F] flex flex-col items-center justify-center text-white">
        <div className="relative flex items-center justify-center mb-4">
          <div className="w-16 h-16 rounded-full border-2 border-[#176BF8]/20 border-t-[#4DFFDF] animate-spin" />
          <Loader2 className="w-6 h-6 text-[#4DFFDF] absolute animate-pulse" />
        </div>
        <div className="text-sm font-bold tracking-[3px] uppercase text-[#A5A5D8] mb-1">
          Boreas-Nexus
        </div>
        <p className="text-xs text-[#6A6A9F]">Loading Chennai Urban Heat Knowledge Layers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen w-screen bg-[#05050F] flex flex-col items-center justify-center text-white p-6 text-center">
        <div className="w-14 h-14 rounded-2xl bg-[#EC223B]/20 border border-[#EC223B]/50 flex items-center justify-center text-[#EC223B] mb-4">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Thermal Knowledge Layer Unavailable</h2>
        <p className="text-sm text-[#6A6A9F] max-w-md mb-6">{error}</p>
        <button
          onClick={() => loadInitialData()}
          className="px-5 py-2.5 rounded-xl bg-[#176BF8] hover:bg-[#176BF8]/80 text-white font-bold text-xs uppercase tracking-wider transition-all"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-[#05050F] text-white overflow-hidden">
      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Persistent Top Bar */}
        <TopBar />

        {/* Dynamic Route Viewport */}
        <main className="flex-1 overflow-y-auto relative bg-[#05050F]">
          <Outlet />
        </main>
      </div>

      {/* Persistent Hotspot Detail Drawer */}
      <HotspotDrawer />
    </div>
  );
};
