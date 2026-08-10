import React, { useState } from 'react';
import { Header } from '../components/layout/Header';
import { Settings as SettingsIcon, Save } from 'lucide-react';

export const Settings: React.FC = () => {
  const [atol, setAtol] = useState('1e-6');
  const [rtol, setRtol] = useState('1e-9');
  const [timeout, setTimeout_] = useState('30');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // Phase 2+: persist to backend config
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  };

  const fieldStyle: React.CSSProperties = {
    background: 'var(--bg-primary)',
    border: '1px solid var(--border-normal)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    padding: '8px 12px',
    width: '100%',
    outline: 'none',
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 12,
    color: 'var(--text-secondary)',
    marginBottom: 6,
    display: 'block',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header title="Settings" subtitle="Configure tolerances, compiler paths, and execution parameters" />
      <div className="page-content" style={{ maxWidth: 640 }}>
        <div className="page-section">
          <div className="section-title">Numerical Comparison Tolerances</div>
          <div className="card">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <label style={labelStyle}>Absolute Tolerance (atol)</label>
                <input style={fieldStyle} value={atol} onChange={e => setAtol(e.target.value)} id="input-atol" />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>|a - b| ≤ atol + rtol·|b|</div>
              </div>
              <div>
                <label style={labelStyle}>Relative Tolerance (rtol)</label>
                <input style={fieldStyle} value={rtol} onChange={e => setRtol(e.target.value)} id="input-rtol" />
              </div>
            </div>
          </div>
        </div>

        <div className="page-section">
          <div className="section-title">Execution Engine</div>
          <div className="card">
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Execution Timeout (seconds)</label>
              <input style={{ ...fieldStyle, width: 120 }} value={timeout} onChange={e => setTimeout_(e.target.value)} id="input-timeout" />
            </div>
            <div>
              <label style={labelStyle}>C Compiler Path (leave blank to auto-detect)</label>
              <input style={fieldStyle} placeholder="e.g. C:/msys64/mingw64/bin/gcc.exe" id="input-c-compiler-path" />
            </div>
            <div style={{ marginTop: 16 }}>
              <label style={labelStyle}>Fortran Compiler Path (leave blank to auto-detect)</label>
              <input style={fieldStyle} placeholder="e.g. C:/msys64/mingw64/bin/gfortran.exe" id="input-fortran-compiler-path" />
            </div>
          </div>
        </div>

        <button className="btn btn-primary" onClick={handleSave} id="btn-save-settings">
          <Save size={14} /> {saved ? 'Saved!' : 'Save Settings'}
        </button>
        <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
          Note: Settings persistence to backend config is implemented in Phase 2.
        </div>
      </div>
    </div>
  );
};
