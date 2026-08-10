import React from 'react';
import type { CompilerInfo } from '../../types';

interface CompilerStatusProps {
  language: 'C' | 'Fortran';
  compilers: CompilerInfo[];
  loading?: boolean;
}

export const CompilerStatusCard: React.FC<CompilerStatusProps> = ({
  language,
  compilers,
  loading = false,
}) => {
  const detected = compilers.find((c) => c.status === 'detected');
  const primary = detected || compilers[0];

  return (
    <div className="compiler-card">
      <div
        className={`compiler-indicator ${loading ? 'loading' : primary?.status ?? 'not_found'}`}
      />
      <div className="compiler-info">
        <div className="compiler-name">
          {loading ? 'Detecting...' : primary ? primary.name.toUpperCase() : 'Not Found'}
        </div>
        <div className="compiler-detail">
          {loading
            ? 'Searching PATH...'
            : primary?.version
            ? `v${primary.version} — ${primary.path ?? ''}`
            : primary?.error ?? 'Compiler not detected on this system'}
        </div>
      </div>
      <span className={`compiler-lang-badge ${language.toLowerCase()}`}>{language}</span>
    </div>
  );
};
