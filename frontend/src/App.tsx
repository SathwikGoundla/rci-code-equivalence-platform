import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Analysis } from './pages/Analysis';
import { GapDetection } from './pages/GapDetection';
import { TestExecution } from './pages/TestExecution';
import { Visualization } from './pages/Visualization';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { SystemDiagnostics } from './pages/SystemDiagnostics';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/"              element={<Dashboard />} />
            <Route path="/analysis"      element={<Analysis />} />
            <Route path="/gaps"          element={<GapDetection />} />
            <Route path="/tests"         element={<TestExecution />} />
            <Route path="/visualization" element={<Visualization />} />
            <Route path="/reports"       element={<Reports />} />
            <Route path="/settings"      element={<Settings />} />
            <Route path="/diagnostics"   element={<SystemDiagnostics />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
