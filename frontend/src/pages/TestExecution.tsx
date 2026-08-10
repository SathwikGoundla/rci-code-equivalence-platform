import React from 'react';
import { Header } from '../components/layout/Header';
import { FlaskConical } from 'lucide-react';

export const TestExecution: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
    <Header title="Test Execution" subtitle="Run identical inputs against both C and Fortran implementations" />
    <div className="page-content">
      <div className="stub-page">
        <FlaskConical size={48} style={{ opacity: 0.2 }} />
        <span className="stub-phase-badge">Phase 8–10</span>
        <h2>Test Execution Engine</h2>
        <p>
          Compiler detection, safe subprocess execution, test-input generation, and same-input
          guarantee are implemented in Phases 8–10. Requires GCC and GFortran to be installed.
        </p>
      </div>
    </div>
  </div>
);
