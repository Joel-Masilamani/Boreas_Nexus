import React from 'react';
import { BrowserRouter, HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { HeatIntelligencePage } from './pages/HeatIntelligencePage';
import { DriverIntelligencePage } from './pages/DriverIntelligencePage';
import { ThermalDynamicsPage } from './pages/ThermalDynamicsPage';
import { ScenarioLabPage } from './pages/ScenarioLabPage';
import { DecisionCenterPage } from './pages/DecisionCenterPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

export const App: React.FC = () => {
  // Using HashRouter for robust client-side routing across dev and preview servers
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="heat-intelligence" element={<HeatIntelligencePage />} />
          <Route path="drivers" element={<DriverIntelligencePage />} />
          <Route path="thermal-dynamics" element={<ThermalDynamicsPage />} />
          <Route path="scenario-lab" element={<ScenarioLabPage />} />
          <Route path="decision-center" element={<DecisionCenterPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  );
};

export default App;
