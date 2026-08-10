import React from 'react';
import { Header } from '../components/layout/Header';
import { FileText } from 'lucide-react';

export const Reports: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
    <Header title="Reports" subtitle="Generate and export offline verification reports" />
    <div className="page-content">
      <div className="stub-page">
        <FileText size={48} style={{ opacity: 0.2 }} />
        <span className="stub-phase-badge">Phase 12</span>
        <h2>Report Generation Engine</h2>
        <p>
          Export to PDF, HTML, JSON, and CSV. Reports include source summaries, IR comparison,
          gap classification, test results, numerical error analysis, and visualizations.
          All generated offline with no external dependencies. Implemented in Phase 12.
        </p>
      </div>
    </div>
  </div>
);
