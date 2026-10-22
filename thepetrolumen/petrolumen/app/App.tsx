import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ReservoirSimulation from './pages/ReservoirSimulation';
import ProductionAnalysis from './pages/ProductionAnalysis';
import Optimization from './pages/Optimization';
import Modeling from './pages/Modeling';
import Uncertainty from './pages/Uncertainty';
import WellTesting from './pages/WellTesting';
import EconomicAnalysis from './pages/EconomicAnalysis';
import Visualization from './pages/Visualization';
import AdvancedAnalytics from './pages/AdvancedAnalytics';
import Integration from './pages/Integration';

const App: React.FC = () => {
  return (
    <Router>
      <div className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/reservoir-simulation" element={<ReservoirSimulation />} />
            <Route path="/production-analysis" element={<ProductionAnalysis />} />
            <Route path="/optimization" element={<Optimization />} />
            <Route path="/modeling" element={<Modeling />} />
            <Route path="/uncertainty" element={<Uncertainty />} />
            <Route path="/well-testing" element={<WellTesting />} />
            <Route path="/economic-analysis" element={<EconomicAnalysis />} />
            <Route path="/visualization" element={<Visualization />} />
            <Route path="/advanced-analytics" element={<AdvancedAnalytics />} />
            <Route path="/integration" element={<Integration />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App; 