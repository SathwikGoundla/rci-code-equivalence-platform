import React from 'react';
import type { CompilerInfo } from '../../types';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

interface CompilerStatusProps {
  language: 'C' | 'Fortran';
  compilers: CompilerInfo[];
  loading?: boolean;
}

const StatusIcon: React.FC<{ status: CompilerInfo['status'] }> = ({ status }) => {
  if (status === 'detected')  return <CheckCircle2 size={14} color="var(--status-detected)" />;
  if (status === 'not_found') return <AlertCircle  size={14} color="var(--status-not-found)" />;
  return <XCircle size={14} color="var(--status-error)" />;
};

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
