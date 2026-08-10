import React from 'react';
import { Header } from '../components/layout/Header';
import { GitCompareArrows } from 'lucide-react';

export const GapDetection: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
    <Header title="Gap Detection" subtitle="Classify and manage detected implementation gaps" />
    <div className="page-content">
      <div className="stub-page">
        <GitCompareArrows size={48} style={{ opacity: 0.2 }} />
        <span className="stub-phase-badge">Phase 6</span>
        <h2>Gap Detection Console</h2>
        <p>
          The full gap management console — with diff viewer, patch generation, and human approval
          workflow — is implemented in Phase 6 and 7. Upload files in <strong>Code Analysis</strong>
          to see gap results now.
        </p>
      </div>
    </div>
  </div>
);
